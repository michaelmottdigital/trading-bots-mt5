from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
from win11toast import toast
#import win32com.client
import math

def truncate(number, digits):
    x = number * (10**digits)
    return math.trunc(x) / (10**digits)

def getOpenPositions():    
    positions = mt5.positions_get()
    for position in positions:
        print('position ', position.symbol, position.price_open, position)
    return positions


# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


print('Connected Version: ' + str(mt5.version()))
#speaker = win32com.client.Dispatch("SAPI.SpVoice")
#speaker.Speak('connected to Meta trader')


while True:
    # GET LAST TICK
    spxData = mt5.symbol_info_tick('SP500')._asdict()
    ndxData = mt5.symbol_info_tick('NAS100')._asdict()
    spxPrice = spxData['bid']
    ndxPrice = ndxData['bid']
    ratio =  truncate(ndxPrice/spxPrice,3)
    
    positions = mt5.positions_get()

    profit = 0
    for position in positions:
        #print('position ', position.symbol, position.price_open, position.profit)
        if position.symbol == 'NAS100' or position.symbol == 'SP500':
            profit += truncate(position.profit,2)

    print('profit: ' + str(profit) + '     ratio: ' + str(ratio))

    if profit >= 6.00:
        #speaker.Speak('you have reached your profit target')
        print('you have reacjed your profit target')
        
    time.sleep(10)
