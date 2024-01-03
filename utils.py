import pandas as pd
import MetaTrader5 as mt5
import datetime 
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import numpy as np
import csv
import os

RSI_OVER_BOUGHT_THRESHOLD = 60
RSI_OVER_SOLD_THRESHOLD = 40

def get_symbol_history(symbol, closed_candles_only=True, periods=300):
    print("get symbol history")

    data = pd.DataFrame(mt5.copy_rates_from_pos(
        symbol,
        mt5.TIMEFRAME_M5,
        0,
        periods
    ))


    # convert time to date time
    data["time"] = pd.to_datetime(data["time"], unit="s")


    # add a local time colimn
    seven_hours = datetime.timedelta(hours=7)
    #data["Date"] = data["time"] - seven_hours
    data["local_time"] = data["time"] - seven_hours


    # Add technical indicators
    rsi_indicator = RSIIndicator(
        close=data["close"],
        window=14,                   # 14 is default, 9 will give more signals
        )
    data["rsi"] = rsi_indicator.rsi()


    atr_indicator = AverageTrueRange(
            high=data["high"],
            low=data["low"],
            close=data["close"],
            window=14
        )
        
    data["atr"] = round(atr_indicator.average_true_range(), 2)

    # most recent bar is incomplete, we need to remove it
    # we only want to use completed candles
    if closed_candles_only:
        data.drop(index=len(data)-1, inplace=True)

    # make sure first row is the most current time
    data.sort_index(ascending=False, inplace=True)
    data.reset_index(inplace=True)

    return data





def append_cdl_patterns(data):
    data = (data
        .assign(cdl_size = abs(data.high - data.low))
        .assign(cdl_body_size = abs(data.close - data.open))
        .assign(cdl_up = np.where(data.open < data.close, True, False))
        .assign(cdl_down = np.where(data.open > data.close, True, False))
       )

    data = (data 
        .assign(cdl_body_perc = data.cdl_body_size / data.cdl_size )
       )

    previous_cdl = data.shift(-1)


    data["ptn_bullish_engulfing"] = np.where(
            (data.open <= previous_cdl.close) &
            (data.close >= previous_cdl.open) &
            (data.cdl_up & previous_cdl.cdl_down),
            True, False
        )

    data["ptn_bearish_engulfing"] = np.where(
            (data.open >= previous_cdl.close) &
            (data.close <= previous_cdl.open) &
            (data.cdl_up == False & previous_cdl.cdl_up), 
            True, False
        )
    
    return data


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
        "sl_moved": 0
    }

    file_name = "logs/tradelog.csv"
    
    if not os.path.isfile(file_name):
        with open(file_name, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter( f, ["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl_moved"])
            writer.writeheader()


    with open(file_name, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter( f,["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl_moved"])
        writer.writerow(data)

