import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
from win11toast import toast
import win32com.client
import math
import random
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


def open_position_on_signal(symbol, number_of_lots, ts_amount):

    currentTime = time.localtime()

    trade_active = False
    while not trade_active:
        print('Checking Prices ', time.strftime('%I:%M:%S', currentTime))

        data = pd.DataFrame(mt5.copy_rates_from_pos(
            symbol,
            mt5.TIMEFRAME_M5,
            0,
            500
        ))

        # convert time to date time
        data["time"] = pd.to_datetime(data["time"], unit="s")


        # add a local time colimn
        seven_hours = datetime.timedelta(hours=7)
        data["Date"] = data["time"] - seven_hours

        # create index
        data = data.set_index("Date")

        #print(data.tail())
        
        # add RSI to our data
        rsi_indicator = RSIIndicator(
            close=data["close"],
            window=14,                   # 14 is default, 9 will give more signals
            )
        data["rsi"] = rsi_indicator.rsi()


        # check for bullish/bearish engulfing candle
        #  look for an up bar preceded by 4 - 6 down candles
        #result = check_engulfing_pattern(data)

        # check rsi indicator
        #  short - rsi is under threshold after being over threshold    
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
        enabled = False
        if enabled: 
            if rsi_value < 70 and rsi_value_2bars_back > 70:
                print('SELL ')
                if IS_SPEECH_ENABLED:
                    speaker.Speak('alert, sell ')
                
                trade_active = True
                position = create_opening_trade(symbol, "sell", number_of_lots, ts_amount)
                return position

            elif rsi_value > 30 and rsi_value_2bars_back < 30 :
                print('BUY ', symbol)
                if IS_SPEECH_ENABLED:
                    speaker.Speak('alert, BUY ' + symbol)
                
                #create_opening_trade(symbol, "buy", number_of_lots, sl_percent)
                trade_active = True
                position = create_opening_trade(symbol, "buy", number_of_lots, ts_amount)
                return position



        is_engulfing_pattern = check_engulfing_pattern(data)

        if is_engulfing_pattern == "bullish engulfing":
            print('BUY ', symbol)
            if IS_SPEECH_ENABLED:
                speaker.Speak('alert, BUY ' + symbol)

            trade_active = True
            position = create_opening_trade(symbol, "buy", number_of_lots, ts_amount)
            return position
        elif is_engulfing_pattern == "bearish engulfing":
            print('SELL ', symbol)
            if IS_SPEECH_ENABLED:
                speaker.Speak('alert, SELL ' + symbol)

            trade_active = True
            position = create_opening_trade(symbol, "sell", number_of_lots, ts_amount)
            return position



        # if we open a trade then exit right aways
        if not trade_active:
            time.sleep(30)
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

   # long_or_short = "long" if order_type == "buy" else "short"
    
    return { 
        "ticket_id": new_ticket.order,
        "long_or_short": long_or_short
    }

def countdown_timer(minutes, seconds):
    t = (minutes * 60) + seconds
    
    while t: 
        mins, secs = divmod(t, 60) 
        status = '{:02d}:{:02d}'.format(mins, secs) 
        print(status, end="\r") 
        time.sleep(1) 
        t -= 1

def manage_position(position, initial_ts_amount):
    # right ofer the position is opened, wait 5 minutes
    

    countdown_timer(5, 0)


    start_time = time.time()

    print("start_time:" , start_time)
    ts_amount = initial_ts_amount

    open_position = mt5.positions_get(
            ticket=position["ticket_id"]
        )

    if len(open_position) == 0:
        print("No positions are open")
        return
    
    open_position = open_position[0]

    ts_adjusted_count = 0

    first_ts_adjustment_done = False
    second_ts_adjustment_done = False
    while open_position:
        print("checking trailing stop", position["ticket_id"])
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

        old_ts = open_position.sl
        #print("old trailing stop: ", old_ts)

        move_stop_loss = False

        # get current price so we can adjust the stop loss
        # only move stop loss if 
        #   1. the current_price is greater than (long) or less than (short) the price at which we opened the trade
        #   2. the gap between the old and new ts is big enough
        #
        if position["long_or_short"] == "long":
            price = mt5.symbol_info_tick(symbol).ask
            new_ts = price - ts_amount
            if new_ts > old_ts and new_ts - old_ts > 2 and price > open_position.price_open: 
                # move the stop loss
                move_stop_loss = True
        else: 
            price = mt5.symbol_info_tick(symbol).bid
            new_ts = price + ts_amount
            
            if new_ts < old_ts and old_ts - new_ts > 2 and price < open_position.price_open: 
                # move the stop loss
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
            True if (position["long_or_short"] == "long" and price > open_position.price_open) or 
            (position["long_or_short"] == "short" and price < open_position.price_open) 
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
            ts_amount = ts_amount *.90
            ts_adjusted_count += 1
            #print("adjusted: ", ts_amount, "  ", ts_adjusted_count)    

        sleep_seconds = random.randrange(30, 90)
        print("sleeping: ", sleep_seconds)

        time.sleep(sleep_seconds)



def set_cndl_up_or_down(row):
    if row["cndl_body_size"] > 0:
        return "up"
    else:
        return "down"


def check_engulfing_pattern(data):
    print("check engulfing pattern")

    data["cndl_body_size"] = data["close"] - data["open"]
    data["cndl_direction"] = data.apply(set_cndl_up_or_down, axis=1)

    current_bar = data.iloc[-1]
    previous_bar = data.iloc[-2]


    # lets make sure we were in an up or down trend before the change in direction
    sorted_data = data.sort_index( ascending=False)
    down_days = len(sorted_data.iloc[1:8].query("cndl_direction == 'down'"))
    up_days = len(sorted_data.iloc[1:8].query("cndl_direction == 'up'"))

    is_bullish_engulfing = (
        True if current_bar.cndl_direction == "up" and previous_bar.cndl_direction == "down" and 
        abs(current_bar.cndl_body_size) > abs(previous_bar.cndl_body_size) and
        current_bar.close > previous_bar.open and
        current_bar.open <= previous_bar.close and
        down_days >= 4
        else False
)

    is_bearish_engulfing = (
        True if current_bar.cndl_direction == "down" and previous_bar.cndl_direction == "up" and
        abs(current_bar.cndl_body_size) > abs(previous_bar.cndl_body_size) and 
        current_bar.close < previous_bar.open and
        current_bar.open <= previous_bar.close and
        up_days >= 4
        else False
    )

    
    if is_bullish_engulfing:
        print("Bullish Engulfing")
        return("bulling engulfing")
    elif is_bearish_engulfing:
        print("Bearish Engulfing")
        return("bearish engulfing")
    else: 
        return False


# -------------------------------------------------------
#   Main
#
# -------------------------------------------------------


IS_SPEECH_ENABLED = True


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

symbol = "ETHUSD"
number_of_lots = .01   # .01 lots


while True:

    # do not trade between midning at 5am
    #   24 hour time. 0 to 5
    current_time  = time.localtime()
    print("local time: ", current_time)
    if current_time.tm_hour >= 0 and current_time.tm_hour < 5:
        time.sleep(60*10)
        continue

    
    initial_ts_amount = random.uniform(7, 10)
    print("initial ts: ", initial_ts_amount)
    position = open_position_on_signal(symbol, number_of_lots, initial_ts_amount)

    #position = { 
    #        "ticket_id": 97884929,
    #        "long_or_short": "long"
    #}

    manage_position(position, initial_ts_amount)

    print("waiting to make a new trade")
    #countdown_timer(5,0)

mt5.shutdown()
