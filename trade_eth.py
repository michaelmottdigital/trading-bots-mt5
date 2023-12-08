from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
from win11toast import toast
import win32com.client
import math
from ta import add_all_ta_features
from ta.momentum import RSIIndicator
from ta.utils import dropna 

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


def open_position_on_signal(symbol, number_of_lots, sl_percent, sl_amount):

    currentTime = time.localtime()
    minutesToSleep = 2

    trade_active = False
    # currentTime.tm_hour <= 20 
    while not trade_active:
        print('Checking Prices ', time.strftime('%I:%M:%S', currentTime))

        data = pd.DataFrame(mt5.copy_rates_from_pos(
            symbol,
            mt5.TIMEFRAME_M5,
            0,
            200
        ))

        data["time"] = pd.to_datetime(data["time"], unit="s")

        #sprint(data)
        

        rsi_indicator = RSIIndicator(
            close=data["close"],
            window=14,
            )
        
        data["rsi"] = rsi_indicator.rsi()

        # check indicator    
        last_row = data.iloc[-1]
        

        rsi_value = last_row["rsi"]

        rsi_value_2bars_back = data.iloc[-3]["rsi"]

        print("RSI ", rsi_value)

        # --------------------  TESTING ------------------------
        #position = create_opening_trade(symbol, "buy", number_of_lots, sl_percent, sl_amount)
        #trade_active = True
        #speaker.Speak('alert, BUY ' + symbol)
        #return position
        # --------------------  TESTING ------------------------
    
        if rsi_value < 70 and rsi_value_2bars_back > 70:
            print('SELL ')
            speaker.Speak('alert, sell ')
            trade_active = True
            position = create_opening_trade(symbol, "sell", number_of_lots, sl_percent, sl_amount)
            return position

        elif  rsi_value > 30 and rsi_value_2bars_back < 30 :
            print('BUY ', symbol)
            speaker.Speak('alert, BUY ' + symbol)
            #create_opening_trade(symbol, "buy", number_of_lots, sl_percent)
            trade_active = True
            position = create_opening_trade(symbol, "buy", number_of_lots, sl_percent, sl_amount)
            return position

        # if we open a trade then exit right aways
        if not trade_active:
            time.sleep(20)
            currentTime = time.localtime()


def create_opening_trade(symbol, order_type, number_of_lots, sl_percent, sl_amount):

    if order_type == "buy":
        type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        sl = price - sl_amount
        long_or_short = "long"
    else:
        type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        sl = price + sl_amount
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

   # long_or_short = "long" if order_type == "buy" else "short"
    
    return { 
        "ticket_id": new_ticket.order,
        "long_or_short": long_or_short
    }

    #return new_ticket.order   # return the ticket id

def adjust_trailing_stop(position, ts_amount):

    
    open_position = True
    while open_position:
        print("checking trailing stop", position["ticket_id"])
        # trailing stop can only go in one direction
        #  if long, the new trailing stop can not be less than the old trailing stop


        # get old stop loss from ticket 
        open_position = mt5.positions_get(
            ticket=position["ticket_id"]
        )[0]

        #print(open_position)

        if open_position == None:
            print("no positions open")

        #print(open_position)
        old_ts = open_position.sl
        #print("old trailing stop: ", old_ts)

        move_stop_loss = False

        # get current price so we can adjust the stop loss
        if position["long_or_short"] == "long":
            price = mt5.symbol_info_tick(symbol).ask
            new_ts = price - ts_amount
            if new_ts > old_ts and new_ts - old_ts > 2: 
                # move the stop loss
                move_stop_loss = True
        else: 
            price = mt5.symbol_info_tick(symbol).bid
            new_ts = price + ts_amount
            if new_ts < old_ts and new_ts - old_ts > 2: 
                # move the stop loss
                move_stop_loss = True

        if move_stop_loss:
            speaker.Speak('moving stop loss')
            print("** moving stop loss", old_ts, new_ts)      
            request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": position["ticket_id"],
                    "sl": new_ts
                }
            
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("2. order_send failed, retcode={}".format(result.retcode), result)
                print("shutdown() and quit")
                mt5.shutdown()
                quit()
        else:
            print("leave stop loss")

        time.sleep(60)



# -------------------------------------------------------
#   Main
#
# -------------------------------------------------------
    
# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Speak('connected to Meta trader')

#listAvailableSymbols()
  
#listSymbolInfo('NAS100')
# symbolsToCheck = ['ETHUSD']  #, 'SP500', 'NAS100', 'EURUSD'

symbol = "ETHUSD"
number_of_lots = .01   # .01 lots
sl_percent = .05 
sl_amount = 20.0   # doallars for stop loss - total dollars at risk is .20 cents
ts_amount = 7.0


position = open_position_on_signal(symbol, number_of_lots, sl_percent, sl_amount)


#position = { 
#        "ticket_id": 97569201,
#        "long_or_short": "long"
#}

#{'ticket_id': 97582331, 'long_or_short': 'long'}

#print(position)


adjust_trailing_stop(position, ts_amount)


mt5.shutdown()
