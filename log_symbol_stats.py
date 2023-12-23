# ----------------------------------------------------------------- #
# Log stats about particular symbol
# Stats include:
#   1. Bid Ask spread
# ----------------------------------------------------------------- #
import MetaTrader5 as mt5
import win32com.client
import argparse
import time
import datetime
import csv
import os


argParser = argparse.ArgumentParser()
argParser.add_argument("-s", "--symbol", help="symbol")

args = argParser.parse_args()
print(args.symbol)
symbol = args.symbol



IS_SPEECH_ENABLED = False

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")
if IS_SPEECH_ENABLED:
    speaker.Speak('connected to Meta trader')

file_name = "logs/stats_" + symbol + ".csv"
if not os.path.isfile(file_name):
    with open(file_name, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter( f, ["time", "bid_ask"])
        writer.writeheader()


while True:
    last_tick = mt5.symbol_info_tick(symbol)

    date_and_time = datetime.datetime.now()

    print(date_and_time, last_tick.bid)
    
    data = {
        "time": date_and_time,
        "bid_ask": round(last_tick.ask - last_tick.bid, 3)

    }

    with open(file_name, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter( f, ["time", "bid_ask"])
        writer.writerow(data)
    
    time.sleep(60)

