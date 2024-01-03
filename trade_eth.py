import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
import win32com.client
import math
import random
from ta import add_all_ta_features
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.utils import dropna 
import numpy as np
import argparse
import os
import csv
from utils import get_symbol_history, write_trade_log, append_cdl_patterns


def listAvailableSymbols():
    symbols = mt5.symbols_get()
    print('Symbold: ', symbols[0])

    for symbol in symbols:
        print(symbol.name)

def listSymbolInfo(symbolName):
    print(symbolName)
    info = mt5.symbol_info(symbolName)._asdict()
    for prop in info:
        print(prop, ': ',  info[prop])
  

def truncate(number, digits):
    x = number * (10**digits)
    return math.trunc(x) / (10**digits)


def open_position_on_signal(symbol, number_of_lots):


    trade_active = False
    while not trade_active:
        currentTime = time.localtime()

        print("\r\n------------------------------------------------")
        print('Checking Prices ', time.strftime('%I:%M:%S', currentTime))
        print("------------------------------------------------\r\n")

        data = get_symbol_history(symbol, closed_candles_only=True)

        # trailing stop is 2x atr
        ts_amount = data.iloc[0].atr * 1.5
        
        print("--- initial ts_amount", ts_amount)
        data = append_cdl_patterns(data)

        print(data.head(10)[["local_time", "ptn_bullish_engulfing", "ptn_bearish_engulfing", "atr", "cdl_up", "open", "close"]])
        

        is_bullish_engulfing_pattern = data.iloc[0]["ptn_bullish_engulfing"]
        is_bearish_engulfing_pattern = data.iloc[0]["ptn_bearish_engulfing"]
        
        #testing
        #is_bullish_engulfing_pattern = True
      
        if is_bullish_engulfing_pattern:
            print('BUY ', symbol)
            if IS_SPEECH_ENABLED:
                speaker.Speak('alert, BUY ' + symbol)

            trade_active = True
            position = create_opening_trade(symbol, "buy", number_of_lots, ts_amount)
            return position
        
        if is_bearish_engulfing_pattern:
            print('SELL ', symbol)
            if IS_SPEECH_ENABLED:
                speaker.Speak('alert, SELL ' + symbol)

            trade_active = True
            position = create_opening_trade(symbol, "sell", number_of_lots, ts_amount)
            return position



        # if we open a trade then exit right aways
        if not trade_active:
            time.sleep(60)
            #currentTime = time.localtime()

def create_opening_trade(symbol, order_type, number_of_lots,ts_amount):
    if order_type == "buy":
        type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        sl = price - ts_amount
        long_or_short = "long"
    else:
        type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        sl = price + ts_amount
        long_or_short = "short"

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": number_of_lots,
        "type": type,
        "sl": sl,
        "comment": order_type + symbol,
        "type_time": mt5.ORDER_TIME_GTC
    }

    new_ticket = mt5.order_send(request)
    if new_ticket.retcode != mt5.TRADE_RETCODE_DONE:
        print("2. order_send failed, retcode={}".format(new_ticket.retcode), new_ticket)
        print("shutdown() and quit")
        mt5.shutdown()
        quit()

    print("opened position with POSITION_TICKET={}".format(new_ticket.order))
    #print(new_ticket)
   # long_or_short = "long" if order_type == "buy" else "short"
    
    result = { 
        "symbol": symbol,
        "ticket_id": new_ticket.order,
        "long_or_short": long_or_short,
        "price": new_ticket.price,
        "lots": new_ticket.volume,
        "ts_amount": ts_amount
    }

    write_trade_log(result, "create_position")
    print("---- result: ", result)
    return result



def countdown_timer(minutes, seconds):
    t = (minutes * 60) + seconds
    
    while t: 
        mins, secs = divmod(t, 60) 
        status = '{:02d}:{:02d}'.format(mins, secs) 
        print(status, end="\r") 
        time.sleep(1) 
        t -= 1

def manage_position(position):

    start_time = time.time()

    print("start_ime:" , start_time)
    ts_amount = position["ts_amount"]

    open_position = mt5.positions_get(
            ticket=position["ticket_id"]
        )

    if len(open_position) == 0:
        print("No positions are open")
        return
    
    open_position = open_position[0]

    ts_adjusted_count = 0

    
    is_at_breakeven = False
    while open_position:
        
        print("checking trailing stop", position["ticket_id"])
        print("at Breakeven: ", is_at_breakeven)
        # trailing stop can only go in one direction
        #  if long, the new trailing stop can not be less than the old trailing stop


        # get old stop loss from ticket 
        #   why do we need the [0] -- mt5 is returning a namedtuple structure - not sure how to use it
        open_position = mt5.positions_get(
            ticket=position["ticket_id"]
        )                 

        if len(open_position) == 0:
            if IS_SPEECH_ENABLED:
                speaker.Speak('no positions open')
    
            print("no positions open")
            break

        open_position = open_position[0]

        data = get_symbol_history(symbol, closed_candles_only=True)

        append_cdl_patterns(data)

        old_ts = open_position.sl

        # see if we can move to breakeven

        current_cdl = data.iloc[0]
        previous_cdl = data.iloc[1]
           

        #print("old trailing stop: ", old_ts)

        move_stop_loss = False

        if position["long_or_short"] == "long" :
            current_price = mt5.symbol_info_tick(symbol).ask
            
            proposed_ts = current_price - position["ts_amount"] 

            if (
                proposed_ts > old_ts and      # trailing stops can never go back
                current_price >= current_cdl.close   
            ):
                new_ts = proposed_ts 
                move_stop_loss = True

        else:
            print("checking stop loss short")  

            proposed_ts = current_price + position["ts_amount"] 

            if (
                proposed_ts < old_ts and      # trailing stops can never go back
                current_price <= current_cdl.close   
            ):
                new_ts = proposed_ts 
                move_stop_loss = True

          
        if move_stop_loss:
            if IS_SPEECH_ENABLED:
                speaker.Speak('moving stop loss')
            
            print("** moving stop loss", old_ts, new_ts)      
            request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": position["ticket_id"],
                    "sl": new_ts
                }
            
            result = mt5.order_send(request)

            print("------- Move Stop Loss -------------------")
            print(result)
            print("------- Move Stop Loss -------------------")

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("2. order_send failed, retcode={}".format(result.retcode), result)
                print("shutdown() and quit")
                mt5.shutdown()
                quit()
        else:
            print("leave stop loss")

        
        elapsed_time = math.floor((time.time() - start_time)/60)

        #print("-- elapsed time - minutes: ", elapsed_time)
        
        is_price_beyond_open_price = ( 
            True if (position["long_or_short"] == "long" and current_price > open_position.price_open) or 
            (position["long_or_short"] == "short" and current_price < open_position.price_open) 
            else False
        )        

        minutes_to_check = 5
        is_time_to_adjust_ts_amount = ( 
            True if (ts_adjusted_count +1) * minutes_to_check == elapsed_time
            else False
        ) 
          
        max_number_of_adjustments = 3

        if is_time_to_adjust_ts_amount and is_price_beyond_open_price and ts_adjusted_count < max_number_of_adjustments:
            print("ADJUST TS SIZE  ")
            ts_amount = ts_amount * 1
            ts_adjusted_count += 1
            #print("adjusted: ", ts_amount, "  ", ts_adjusted_count)    

        sleep_seconds = random.randrange(20, 30)
        print("sleeping: ", sleep_seconds)

        time.sleep(30)



# -------------------------------------------------------
#   Main
#
# -------------------------------------------------------


IS_SPEECH_ENABLED = True
RSI_OVER_BOUGHT_THRESHOLD = 60
RSI_OVER_SOLD_THRESHOLD = 40

argParser = argparse.ArgumentParser()
argParser.add_argument("-s", "--symbol", help="symbol")

args = argParser.parse_args()
print(args.symbol)

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")
if IS_SPEECH_ENABLED:
    speaker.Speak('connected to Meta trader')

#listAvailableSymbols()
  
#listSymbolInfo('NAS100')
# symbolsToCheck = ['ETHUSD']  #, 'SP500', 'NAS100', 'EURUSD'

symbol = args.symbol
number_of_lots = .01   # .01 lots

# set parameters based on symbol
symbol_config = [
    {
        "symbol": "ETHUSD",
        "initial_sl": 8.0,
        "after_breakeven_sl": 5.00,
        "breakeven_threshold" : 5.00,
        "breakeven_offset": 1.00,
        "rsi_oversold_threshold": 60,
        "rsi_overbought_threshold": 40
    },
    {
        "symbol": "SP500",
        "initial_sl": 5.0,
        "after_breakeven_sl": 3.00,
        "breakeven_threshold" : 3.00,
        "breakeven_offset": .50,
        "rsi_oversold_threshold": 70,
        "rsi_overbought_threshold": 30
    }
]






while True:

    # do not trade between midning at 5am
    #   24 hour time. 0 to 5
    current_time  = time.localtime()
    print("local time: ", current_time)
    #if current_time.tm_hour >= 0 and current_time.tm_hour < 5:
    #    time.sleep(60*10)
    #    continue

    
    position = open_position_on_signal(symbol, number_of_lots)


    manage_position(position)

    

    print("waiting to make a new trade")
    countdown_timer(5,30)

mt5.shutdown()
