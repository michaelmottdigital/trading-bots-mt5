import argparse
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib as ta
import time
import win32com.client
import argparse
import datetime

from trade_utils import get_symbol_data, create_opening_trade, is_ny_trading_hours, is_daytime, get_MT5_Timeframe

def open_position(symbol, data, timeframe):
    # look for a trade
    current_cdl = data.iloc[0]
    previous_cdl = data.iloc[1]

    #print(data.head(5)[["close", "ind_ma_cross", "ind_sma9", "ind_sma21"]])
    print("current", current_cdl[["ptn_bullish_engulfing_1", "is_prev_trend_down"]])
    print("previous", previous_cdl[["ind_rsi"]])

    number_of_lots = .01
    if symbol == "ETHUSD":
        number_of_lots = .02
    elif symbol == "SP500":
        number_of_lots = .01
    

    # 1 hour chart
    # 20, 50 ma cross 
    # follow 35 sma 
    # buy only 
    strategy_ma_cross = False
    if strategy_ma_cross:
        is_test_buy = False
        is_test_sell = False
        if is_test_buy or (current_cdl.ind_ma_cross == 1 
                        #and current_cdl.cdl_up
                        ):
            # buy
            if is_daytime():
                    speaker.Speak('alert BUY')

            print("Buy")
            current_price = mt5.symbol_info_tick(symbol).ask
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "buy", number_of_lots, sl_amount, timeframe)
            return position

        elif is_test_sell or (current_cdl.ind_ma_cross == -1
                            # and current_cdl.cdl_down
                            ):
            # sell
            if is_daytime():
                    speaker.Speak('alert SELL')
            print("Sell")
            current_price = mt5.symbol_info_tick(symbol).bid
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "sell", number_of_lots, sl_amount, timeframe)
            return position


    strategy_engulfing = True 
    if strategy_engulfing: 
        # convert to numpy array so it easier to access previous rsi values
        ind_rsi = data.ind_rsi.to_numpy()

        rsi_overbought_threshold = 65
        rsi_oversold_threshold = 35

#        is_down_trend = (
#            True if ind_rsi[1] < rsi_oversold_threshold or ind_rsi[2] < rsi_oversold_threshold or ind_rsi[3] < rsi_oversold_threshold
#            else False
#        )

#        is_up_trend = (
#            True if ind_rsi[1] > rsi_overbought_threshold or ind_rsi[2] > rsi_overbought_threshold or ind_rsi[3] > rsi_overbought_threshold
#            else False
#        )
        if ( current_cdl.ptn_bullish_engulfing_1 and
            current_cdl.is_prev_trend_down #and
            #previous_cdl.ind_rsi <= rsi_oversold_threshold
            ):
            if is_daytime():
                speaker.Speak('alert BUY')
            print("Buy")
            current_price = mt5.symbol_info_tick(symbol).ask
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "buy", number_of_lots, sl_amount, timeframe)
            return position

        if (current_cdl.ptn_bearish_engulfing_1 
            and current_cdl.is_prev_trend_up
            #and previous_cdl.ind_rsi >= rsi_overbought_threshold
            ):
            if is_daytime():
                speaker.Speak('alert SELL')
            print("Sell")
            current_price = mt5.symbol_info_tick(symbol).bid
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "sell", number_of_lots, sl_amount, timeframe)
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


    old_sl = position["detail"].sl
    move_sl = False

    current_cdl = data.iloc[0]

    # get current price
    if position["long_or_short"] == "long":
        current_price = mt5.symbol_info_tick(symbol).ask
        
        # standard trailing stop
        # new_sl = current_price - sl_amount
        
        if (
            current_cdl.low > position["detail"].price_open
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
            current_cdl.high < position["detail"].price_open 
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
        if is_daytime():
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
        position["detail"] = position_detail
            

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

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")
if is_daytime():
    speaker.Speak('connected to Meta trader')

current_time = 0
previous_time = 0
position = None 


while True:
    data = get_symbol_data(symbol, closed_candles_only=True, timeframe=args.timeframe)
    current_time = data.iloc[0].local_time
    print("checking for new data ", current_time, " " , symbol)
    if current_time != previous_time:
        # we have a new candle
        print("new data has arrived: ", current_time)
        #if is_daytime():
            #speaker.Speak('new data has arrived')  
        
        now = datetime.datetime.now()
        if position == None:
            if now.hour >= 4 and now.hour <= 16:
                position = open_position(symbol, data, args.timeframe)
        else: 
            position = manage_position(position, data)

        previous_time = current_time
    
    #print(position)
    time.sleep(30)
