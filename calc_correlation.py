import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import os
import matplotlib.pyplot as plt
import sys
import statsmodels.tsa.stattools as ts
import math

workPath = 'd:/trading/'
dataPath = 'd:/trading/data/'

print('calculating correlations')

MONTHS_LIST = [1,3,6,9,12,24,36,48,60,120, 180]
ETF_SYMBOLS_LIST = ['SPY', 'QQQ', 'IWM', 'DIA']
CURRENCY_PAIRS = ['EURUSD=X', 'USDJPY=X', 'GBPUSD=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X', 'NZDUSD=X']
FUTURES_SYMBOLS_LIST = ['ES=F', 'NQ=F', 'RTY=F', 'YM=F', 'CL=F', 'TN=F', 'GC=F', 'ZB=F', 'LE=F', 'SB=F', 'HG=F', 'SI=F']

symbolsToCompare = ETF_SYMBOLS_LIST + CURRENCY_PAIRS + FUTURES_SYMBOLS_LIST


set1 = symbolsToCompare
set2 = symbolsToCompare


result = pd.DataFrame()

for symbol1 in set1:
    symbol1Data = pd.read_parquet(dataPath + symbol1 + '.parquet').dropna()
    if len(symbol1Data) == 0:
        print('no data found for ' + symbol1)
        continue

    symbol1Data['Return'] = symbol1Data['Close'] / symbol1Data.shift(-1)['Close'] - 1

    for symbol2 in set2:
        # skip comparing the same symbol against each other
        if symbol1 == symbol2:
            continue

        if not os.path.isfile(dataPath + symbol2 + '.parquet'): 
            print('no data file for symbol: ' + symbol2)
            continue
        
        print('calculating - ' + symbol1 + '  ' + symbol2)
        symbol2Data = pd.read_parquet(dataPath + symbol2 + '.parquet').dropna()
        # check to make sure we have data
        if len(symbol2Data) == 0:
            print('no data for symbol ' + symbol2)
            continue

        symbol2Data['Return'] = symbol2Data['Close'] / symbol2Data.shift(-1)['Close'] - 1

        for months in MONTHS_LIST:
            startDate = pd.to_datetime(date.today() + timedelta(days = -(months*30)))

            selectedSymbol1Data = symbol1Data.query('Date > @startDate')
            selectedSymbol2Data = symbol2Data.query('Date > @startDate')            
                
            # merge SPY and current Symbol so we can calculate correlation
            correlationData = pd.merge(selectedSymbol1Data, selectedSymbol2Data, on = "Date", how = "inner")
            

            #colculate correlation
            corr = correlationData['Return_x'].corr(correlationData['Return_y'])
            #coint = ts.coint(correlationData['Close_x'], correlationData['Close_y'])
            
            newRow = {
                'months': months,
                'symbol1': symbol1,
                'symbol2': symbol2,
                'corr': round(corr,3)
            }

            # print('correlation for ' + symbol1)

            result = pd.concat([result, pd.DataFrame([newRow])],ignore_index=False)


print(result)
result.to_csv( workPath + 'correlation.csv')
