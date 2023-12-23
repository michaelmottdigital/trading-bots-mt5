import yfinance as yf
import pandas as pd
import numpy as np
import time
from win11toast import toast

currentTime = time.localtime()

minutesToSleep = 10


# trading stops at 4pm
while currentTime.tm_hour <= 16:
    print('--- testing at ', time.strftime('%H:%M', currentTime))
    esTicker = yf.Ticker('ES=F')
    esData = esTicker.history(period ='1d', interval='1m') 
    esCurrentPrice = esData['Close'].iloc[-1]


    nqTicker = yf.Ticker('NQ=F')
    nqData = nqTicker.history(period='1d', interval='1m') 
    nqCurrentPrice = nqData['Close'].iloc[-1]

    ratio = nqCurrentPrice/esCurrentPrice

    #print(nqCurrentPrice, esCurrentPrice)
    #print(ratio)

    if ratio >= 3.437:
        print('buy', ratio)
        toast('Trade Alert -> But Now ' + time.strftime('%H:%M', currentTime) + '    '  + str(ratio) )
    else: 
        print('ratio: ' + str(ratio) + ' NQ: ' + str(nqCurrentPrice) + '  ES: ' + str(esCurrentPrice) )

    currentTime = time.localtime()
    time.sleep(minutesToSleep * 60)