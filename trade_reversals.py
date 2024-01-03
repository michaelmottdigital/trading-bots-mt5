import argparse
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib as ta
import time
import win32com.client


from trade_utils import get_symbol_data, create_opening_trade



def open_position(symbol, data):
    # look for a trade
    current_cdl = data.iloc[0]

    print(data.head(5)[["ptn_bullish_engulfing", "ptn_bearish_engulfing", "ind_rsi"]])

    number_of_lots = .01
    
    # convert to numpy array so it easier to access previous rsi values
    ind_rsi = data.ind_rsi.to_numpy()

    rsi_overbought_threshold = 65
    rsi_oversold_threshold = 35

    is_down_trend = (
        True if ind_rsi[1] < rsi_oversold_threshold or ind_rsi[2] < rsi_oversold_threshold or ind_rsi[3] < rsi_oversold_threshold
        else False
    )

    is_up_trend = (
        True if ind_rsi[1] > rsi_overbought_threshold or ind_rsi[2] > rsi_overbought_threshold or ind_rsi[3] > rsi_overbought_threshold
        else False
    )

    if ( 
            (current_cdl.ptn_bullish_engulfing or current_cdl.ptn_morningstar) and
            current_cdl.ind_rsi > rsi_oversold_threshold and
            is_down_trend
        ):
        if IS_SPEECH_ENABLED:
            speaker.Speak('alert BUY')
        print("Buy")
        current_price = mt5.symbol_info_tick(symbol).ask
        ts_amount = current_cdl.ind_atr * 2
        position = create_opening_trade(symbol, "buy", number_of_lots, ts_amount)
        return position

    if (
        (current_cdl.ptn_bearish_engulfing or current_cdl.ptn_eveningstar) and 
        current_cdl.ind_rsi < rsi_oversold_threshold and
        is_up_trend
        ):
        if IS_SPEECH_ENABLED:
            speaker.Speak('alert SELL')
        print("Sell")
        current_price = mt5.symbol_info_tick(symbol).bid
        ts_amount = current_cdl.ind_atr * 2
        position = create_opening_trade(symbol, "sell", number_of_lots, ts_amount)
        return position

    return None



def manage_position(position, data):
    print("manage position")

    # is position still open
    is_position_open = (
        True if len(mt5.positions_get(symbol=position["symbol"])) > 0
        else False)
     
    if not is_position_open:
        print( "no open positions")
        return None
    
    ts_amount = position["ts_amount"]
    #print(position["symbol"], ts_amount)

    old_sl = position["sl"]
    move_sl = False

    # get current price
    if position["long_or_short"] == "long":
        current_price = mt5.symbol_info_tick(symbol).ask

        new_sl = current_price - ts_amount
        if new_sl > old_sl:
            move_sl = True
            
    else: 
        current_price = mt5.symbol_info_tick(symbol).bid

        new_sl = current_price + ts_amount
        if new_sl < old_sl:
            move_sl = True

    if move_sl:
        if IS_SPEECH_ENABLED:
            speaker.Speak('moving stop loss')

        #print("** moving stop loss", old_sl, new_sl)      
        
        request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": position["ticket_id"],
                "sl": new_sl
            }
        
        result = mt5.order_send(request)
        
        position["sl"] = new_sl
    
    # return updated postion with new sl or other changes
    return position
    

IS_SPEECH_ENABLED = True

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")
if IS_SPEECH_ENABLED:
    speaker.Speak('connected to Meta trader')

symbol = "ETHUSD"

current_time = 0
previous_time = 0
position = None 

while True:
    data = get_symbol_data(symbol, closed_candles_only=True, timeframe=mt5.TIMEFRAME_M5)
    current_time = data.iloc[0].local_time
    print("checking for new data", current_time)
    if current_time != previous_time:
        # we have a new candle
        print("new data has arrived: ", current_time)
        #if IS_SPEECH_ENABLED:
            #speaker.Speak('new data has arrived')

        if position == None:
            position = open_position(symbol, data)
        else: 
            position = manage_position(position, data)

        previous_time = current_time
    
    #print(position)
    time.sleep(30)
