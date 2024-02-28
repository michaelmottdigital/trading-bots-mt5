import argparse
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib as ta
import time
import win32com.client
import argparse
import datetime

from trade_utils import get_symbol_data, create_opening_trade, is_ny_trading_hours, is_daytime, get_MT5_Timeframe, is_trading_hours

from strategies import check_rsi_signal, check_engulfing_candle
from countdown_timer import countdown_timer

def open_position(symbol, data, timeframe):
    # look for a trade
    current_cdl = data.iloc[0]
    previous_cdl = data.iloc[1]

    number_of_lots = .01
    if symbol == "ETHUSD":
        number_of_lots = .01
    elif symbol == "SP500":
        number_of_lots = .01
    

    if symbol == "SP500":
        trade_signal = check_rsi_signal(data)
        if trade_signal == "buy" or trade_signal == "sell":
            position = create_opening_trade(symbol, trade_signal, number_of_lots, current_cdl, timeframe, "rsi",is_speech_enabled)
            return position
        
    trade_signal = check_engulfing_candle(data)
    if trade_signal == "buy" or trade_signal == "sell":
        position = create_opening_trade(symbol, trade_signal, number_of_lots, current_cdl, timeframe, "engulfing_candle", is_speech_enabled)
        return position
    
   
    return None



def manage_position(position, data):
    print("manage position")

    position["num_candles_since_open"] += 1

    print(position)
    
    # is position still open
    is_position_open = (
        True if len(mt5.positions_get(ticket=position["ticket_id"])) > 0
        else False)
     
    if not is_position_open:
        print( "no open positions")
        return None
    
    sl_amount = position["sl_amount"]


    old_sl = position["sl"]
    move_sl = False

    current_cdl = data.iloc[0]

    # get current price
    if position["long_or_short"] == "long":
        current_price = mt5.symbol_info_tick(symbol).ask
        
        # standard trailing stop
        # new_sl = current_price - sl_amount
        
        if (
            current_cdl.low > position["price_open"]
            ):

            if current_cdl.low > current_cdl.ind_sma9:
                new_sl= current_cdl.ind_sma9
            elif current_cdl.low > current_cdl.ind_sma15:
                new_sl = current_cdl.ind_sma15 
            else:
                new_sl = old_sl

            if new_sl > old_sl:
                move_sl = True
            
    else: 
        current_price = mt5.symbol_info_tick(symbol).bid

        # standard trailing stop
        # new_sl = current_price + sl_amount
        
        if (
            current_cdl.high < position["price_open"] 
            ):

            if current_cdl.high < current_cdl.ind_sma9:
                new_sl= current_cdl.ind_sma9
            elif current_cdl.high < current_cdl.ind_sma9:
                new_sl = current_cdl.ind_sma15
            else:
                new_sl = old_sl

            if new_sl < old_sl:
                move_sl = True

    if move_sl:
        if is_daytime() and is_speech_enabled:
            speaker.Speak('moving stop loss')

        #print("** moving stop loss", old_sl, new_sl)      
        
        request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": position["ticket_id"],
                "sl": new_sl
            }
        
        result = mt5.order_send(request)

        # updsate position and position details
        position_detail = mt5.positions_get(ticket=position["ticket_id"])[0]  # 0 because it is a named tuple
        #position["detail"] = position_detail
        print("\n\n-----------------------------")
        print(position_detail)
        print("-----------------------------\n\n")
        
        position["sl"] = position_detail.sl
            

    # return updated postion with new sl or other changes


    return position
    




# ---------------------------------------------------------
#  Main 
# ---------------------------------------------------------


argParser = argparse.ArgumentParser()
argParser.add_argument("-s", "--symbol", help="symbol")
argParser.add_argument("-tf", "--timeframe", help="timeframe", default="5M")

args = argParser.parse_args()

symbol = args.symbol
timeframe = args.timeframe

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")

is_speech_enabled = False

if is_daytime() and is_speech_enabled:
    speaker.Speak('connected to Meta trader')

current_time = 0
previous_time = 0
position = None 


while True:
    #print("is trading_hours: ", is_trading_hours())
    if not is_trading_hours(symbol, timeframe) and position == None:
        countdown_timer(5,0)
        continue

    data = get_symbol_data(symbol, closed_candles_only=True, timeframe=timeframe)
    current_time = data.iloc[0].local_time
    print("checking for new data ", current_time, " " , symbol)
    if current_time != previous_time:
        # we have a new candle
        print("new data has arrived: ", current_time)
        #if is_daytime():
            #speaker.Speak('new data has arrived')  
        
        #now = datetime.datetime.now()
        if position == None:
            if is_trading_hours(symbol, timeframe):
                position = open_position(symbol, data, timeframe)

        else: 
            position = manage_position(position, data)

        previous_time = current_time
    
    time.sleep(30)
