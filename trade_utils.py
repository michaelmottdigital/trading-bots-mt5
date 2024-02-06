import MetaTrader5 as mt5
import datetime
import talib as ta
import pandas as pd
import numpy as np
import os
import csv

import win32com.client

def is_daytime():
    # is the current time between 7:00am and 10:00pm
    now = datetime.datetime.now()
    if now.hour >= 7 and now.hour <= 22:
        return True
    else:
        return False

def is_ny_trading_hours():
    # is the current time between 9:30am and 4:00pm
    open_time = datetime.time(9,30)
    close_time = datetime.time(16,0)
    now = datetime.datetime.now()

    if now.time() >= open_time and now.time() <= close_time and now.weekday in [0,1,2,3,4]:
        return True
    else:
        return False 


def get_symbol_data(symbol, closed_candles_only=True, periods=300, timeframe=mt5.TIMEFRAME_M5):
    print("get symbol history")

    
    data = pd.DataFrame(mt5.copy_rates_from_pos(
        symbol,
        get_MT5_Timeframe(timeframe),
        0,
        periods
    ))
    
    # create a field converting to local date and time
    seven_hours = datetime.timedelta(hours=7)
    data = (data
        .assign(server_time = pd.to_datetime(data.time, unit="s").astype(str))
        .assign(time = pd.to_datetime( data.time, unit="s") - seven_hours)
        .assign(local_time = pd.to_datetime( data.time, unit="s") - seven_hours)
        .set_index("time")
        .sort_index(ascending=True)

       )
    
    # basic candle statistics
    data = (data
        .assign(cdl_size = abs(data.high - data.low))
        .assign(cdl_body_size = abs(data.close - data.open))
        .assign(cdl_up = np.where(data.open < data.close, True, False))
        .assign(cdl_down = np.where(data.open > data.close, True, False))
       )

    data = (data 
        .assign(cdl_body_perc = data.cdl_body_size / data.cdl_size )
       )

    #data.rename(columns={"open": "Open", "close": "Close", "low": "Low", "high": "High", "volume": "Volume"}, inplace=True)

    # Add technical indicators
    data  = (data
             .assign(ind_rsi = ta.RSI(data.close, 14),
                    ind_adx = ta.ADX(data.high, data.low, data.close, timeperiod=14),
                    ind_atr = ta.ATR(data.high, data.low, data.close, timeperiod=14),
                    ind_sma9 = data.close.rolling(9).mean(),
                    ind_sma15 = data.close.rolling(15).mean(),
                    ind_sma21 = data.close.rolling(21).mean(),
                    ind_sma20 = data.close.rolling(20).mean(),
                    ind_sma35 = data.close.rolling(35).mean(),
                    ind_sma50 = data.close.rolling(50).mean()
                )
           
            .assign(
                ptn_bullish_engulfing = np.where(ta.CDLENGULFING(data.open, data.high, data.low, data.close) == 100, True, False),
                ptn_bearish_engulfing = np.where(ta.CDLENGULFING(data.open, data.high, data.low, data.close) == -100, True, False),
                ptn_morningstar = np.where(ta.CDLMORNINGSTAR(data.open, data.high, data.low, data.close, penetration=0) == 100, True, False),
                ptn_eveningstar = np.where(ta.CDLEVENINGSTAR(data.open, data.high, data.low, data.close, penetration=0) == 100, True, False),

                )
            )
    
    data = data.assign( ind_ma_bullish = np.where(data.ind_sma9 > data.ind_sma21, 1.0, 0.0))

    data = data.assign( ind_ma_cross = data.ind_ma_bullish.diff())
            
    # rsi signal
    rsi_overbought = 72
    rsi_oversold = 28
    data["tmp_is_below_threshold"] = np.where(data.ind_rsi <= rsi_oversold, 1, 0) 
    data = data.assign( tmp_is_oversold = data.tmp_is_below_threshold.diff() )
    data["signal_rsi_buy"] = np.where(data.tmp_is_oversold == -1, True, False)

    data["tmp_is_above_threshold"] = np.where(data.ind_rsi >=  rsi_overbought, 1, 0) 
    data = data.assign( tmp_is_overbought = data.tmp_is_above_threshold.diff() )
    data["signal_rsi_sell"] = np.where(data.tmp_is_overbought == -1, True, False)


    data.drop(
        ["tmp_is_below_threshold",  "tmp_is_oversold", "tmp_is_above_threshold", "tmp_is_overbought"], 
        axis=1,
        inplace=True
    )



    # most recent bar is incomplete, we need to remove it
    # we only want to use completed candles
    if closed_candles_only:
        data.drop(data.tail(1).index, inplace=True)
       

    # make sure first row is the most current time
    data.sort_index(ascending=False, inplace=True)
    
    #print(data.loc[:, data.columns.str.startswith( ('ind_', 'ptn_') )].query("ptn_bullish_engulfing or ptn_bearish_engulfing"))
   

    previous_cdl = data.shift(-1)
    data["ptn_bullish_engulfing_1"] = np.where(
            (data.open <= previous_cdl.close) &
            (data.close >= previous_cdl.open) &
            (data.cdl_up & previous_cdl.cdl_down),
            True, False
        )

    data["ptn_bearish_engulfing_1"] = np.where(
            (data.open >= previous_cdl.close) &
            (data.close <= previous_cdl.open) &
            (data.cdl_down & previous_cdl.cdl_up), 
            True, False
        )
    

    # is rsi overbougth or oversold

    data["is_prev_trend_down"] = np.where(
        ( data.shift(-1).cdl_down == True ) &
        ( data.shift(-2).cdl_down == True ) &
        ( data.shift(-3).cdl_down == True ),
        True, False
    )

    data["is_prev_trend_up"] = np.where(
        ( data.shift(-1).cdl_up == True ) &
        ( data.shift(-2).cdl_up == True ) &
        ( data.shift(-3).cdl_up == True ),
        True, False
    )

    #data.to_csv("./notebooks/test_data.csv")
    return data


def create_opening_trade(symbol, order_type, number_of_lots,current_cdl,timeframe, strategy):
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    
    if order_type == "buy":
        current_price = mt5.symbol_info_tick(symbol).ask
    else: 
        current_price = mt5.symbol_info_tick(symbol).bid

    sl_amount = current_cdl.ind_atr * 1.5
    
    if is_daytime():
        speaker.Speak('alert ' + order_type)
        print(order_type)
           
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

    #print("--------------------")
    #print("order result")
    #print(new_ticket)
    #print("--------------------")
    
    
    position_detail = mt5.positions_get(ticket=new_ticket.order)[0]  # 0 because it is a named tuple
    
    result = { 
        "symbol": symbol,
        "ticket_id": new_ticket.order,
        "long_or_short": long_or_short,
        "sl_amount": sl_amount,
        "strategy": strategy,
        "timeframe": timeframe,
        "num_candles_since_open": 1,
        "detail": position_detail
       
    }



    write_trade_log(result, "create_position")
    print("---- result: ", result)
    return result



def write_trade_log(trade, order_type):
    # order_type = move stop loss, open position

    time = datetime.datetime.now()

    data = {
        "time": time,
        "symbol": trade["symbol"],
        "ticket_id": trade["ticket_id"],
        "order_type": order_type,
        "direction": trade["long_or_short"],
        "price_open": trade["detail"].price_open,
        "sl": trade["detail"].sl,
        "timeframe": trade["timeframe"],
        "strategy": trade["strategy"]
    }

    file_name = "logs/tradelog.csv"
    
    if not os.path.isfile(file_name):
        with open(file_name, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter( f, ["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl", "timeframe", "strategy"])
            writer.writeheader()


    with open(file_name, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter( f,["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl", "timeframe", "strategy"])
        writer.writerow(data)


def get_MT5_Timeframe(tf):
    match(tf):
        case "30M":
            timeframe = mt5.TIMEFRAME_M30
        case "15M":
            timeframe = mt5.TIMEFRAME_M15
        case "5M":
            timeframe = mt5.TIMEFRAME_M5
        case "1M":
            timeframe = mt5.TIMEFRAME_M1
        case "1H":
            timeframe = mt5.TIMEFRAME_H1
        case "4H":
            timeframe = mt5.TIMEFRAME_H4
        case _:
            timeframe = None

    return timeframe



def is_trading_hours():
    # trading hours are 4:00am to 3:30pm
    now = datetime.datetime.now().time()

    start_time = datetime.time(4,0,0)
    end_time = datetime.time(20,30,0)   #15

    return now >= start_time and now <= end_time
    
