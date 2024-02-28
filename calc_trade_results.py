import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas_ta as pta
import numpy as np
import csv, os

if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


file_name = "logs/tradelog.csv"
    
if not os.path.isfile(file_name):
    print("file does not exist")    

result = []

with open(file_name, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(
        f,fieldnames=["time", "symbol", "ticket_id", "order_type", "direction", "price_open", "sl", "timeframe", "strategy", "position_id"]   
    )
    #skip header row
    next(reader)
    
    for row in reader:
        print(row)
        position_id = int(row["position_id"])
        #print(position_id)
        positions = mt5.history_deals_get(position=position_id)

        #print(positions)
        
        profit = 0
        for position in positions:
            p = position._asdict()
            print(p)            
            if p["type"] == mt5.ORDER_TYPE_BUY:
                print("buy")
            else:
                profit = p["profit"]
                print("sell")
                print(profit)

        #print("# of trades: ", len(positions))
        #trade_history=pd.DataFrame(list(postitions),columns=postitions[0]._asdict().keys())
        result.append(
            { 
                "time": row["time"],
                "symbol": row["symbol"],
                "position_id": row["position_id"],
                "ticket_id": row["ticket_id"],
                "direction": row["direction"],
                #"open_price": float(row["price_open"]),
                #"close_price": close_price,
                "profit": profit,
                "timeframe": row["timeframe"],
                "strategy": row["strategy"]
            }
        )



keys = result[0].keys()
with open("logs/trade_results.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, keys)
    writer.writeheader()
    writer.writerows(result)