from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
from win11toast import toast
#import win32com.client
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


# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
#speaker = win32com.client.Dispatch("SAPI.SpVoice")
#speaker.Speak('connected to Meta trader')
#listAvailableSymbols()
  
#listSymbolInfo('NAS100')

currentTime = time.localtime()
minutesToSleep = 10

while currentTime.tm_hour <= 20:
    #print('Checking Prices ', time.strftime('%I:%M', currentTime))

    # GET LAST TICK
    spxData = mt5.symbol_info_tick('SP500')._asdict()
    ndxData = mt5.symbol_info_tick('NAS100')._asdict()

    spxPrice = spxData['bid']
    ndxPrice = ndxData['bid']
    ratio =  truncate(ndxPrice/spxPrice,3)

    #3.428
    if ratio >= 3.43:
        print('Sell Nasdaq => ' + str(ratio) + '    NDX:' + str(ndxPrice) + '  SPX: ' + str(spxPrice)) 
        #toast('Trade Alert -> But Now ' + time.strftime('%H:%M', currentTime) + '    '  + str(ratio) )
        #speaker.Speak('Alert, Sell Nasdaq buy S and P ')
        quit()
    elif ratio <= 3.35: 
        print('Buy Nasaq => ' + str(ratio) + '    NDX:' + str(ndxPrice) + '  SPX: ' + str(spxPrice)) 
        #speaker.Speak('Alert, Buy Nasdaq')
        quit()
    else:
        print(ratio)

    time.sleep(10)
    currentTime = time.localtime()


mt5.shutdown()
