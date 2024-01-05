import MetaTrader5 as mt5
import datetime
import talib as ta
import pandas as pd
import numpy as np
import os
import csv

def get_symbol_data(symbol, closed_candles_only=True, periods=300, timeframe=mt5.TIMEFRAME_M5):
    #print("get symbol history")

    data = pd.DataFrame(mt5.copy_rates_from_pos(
        symbol,
        timeframe,
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
    


    return data


def create_opening_trade(symbol, order_type, number_of_lots,sl_amount):
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
    #print(new_ticket)
   # long_or_short = "long" if order_type == "buy" else "short"
    
    result = { 
        "symbol": symbol,
        "ticket_id": new_ticket.order,
        "long_or_short": long_or_short,
        "price": new_ticket.price,
        "lots": new_ticket.volume,
        "sl_amount": sl_amount,
        "sl": sl
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
        "price_open": trade["price"],
        "sl_moved": 0,
        "sl": trade["sl"]
    }

    file_name = "logs/tradelog.csv"
    
    if not os.path.isfile(file_name):
        with open(file_name, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter( f, ["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl_moved", "sl"])
            writer.writeheader()


    with open(file_name, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter( f,["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl_moved", "sl"])
        writer.writerow(data)
