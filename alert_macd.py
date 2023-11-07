from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
from win11toast import toast
import win32com.client
import math

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


def calc_macd(data, macd_fast=12, macd_slow=26, macd_signal=9):
    data['macd_fast'] = data['close'].ewm(span=macd_fast).mean()
    data['macd_slow'] = data['close'].ewm(span=macd_slow).mean()
    data['macd'] = data['macd_fast'] - data['macd_slow']

    # simple moving average for macd_signal
    data['macd_signal'] = data['macd'].rolling(macd_signal).mean()
    
    # distance between the macd and the signal line
    data['macd_histogram'] = data['macd'] - data['macd_signal']

    return data


# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Speak('connected to Meta trader')
#listAvailableSymbols()
  
#listSymbolInfo('NAS100')


symbolsToCheck = ['SP500', 'NAS100', 'EURUSD']

currentTime = time.localtime()
minutesToSleep = 10

while currentTime.tm_hour <= 20:
    print('Checking Prices ', time.strftime('%I:%M:%S', currentTime))

    for symbol in symbolsToCheck:

        data = pd.DataFrame(mt5.copy_rates_from_pos(
            symbol,
            mt5.TIMEFRAME_M5,
            0,
            200
        ))


        calc_macd(data)

        last_row = data.iloc[-1]
        macd = last_row['macd']
        macd_signal = last_row['macd_signal']
        macd_histogram = last_row['macd_histogram']
        print(symbol, '  macd: ', macd, '    signal: ', macd_signal, '  hist: ', macd_histogram)
        # when macd is higher than signal line then BUY and macd above 0
        # when macd is below the signal line the SELL and macd below 0
        if ( macd > macd_signal and macd > 0 ): 
            print('BUY ', symbol)
            speaker.Speak('alert, buy ' + symbol)

        elif ( macd < macd_signal and macd < 0 ):
            print('SELL ', symbol)
            speaker.Speak('alert, sell ' + symbol)

        else:
            print('do nothing')



    time.sleep(60)
    currentTime = time.localtime()




mt5.shutdown()
