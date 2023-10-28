import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta, datetime
import os

workPath = 'd:/trading/'
dataPath = 'd:/trading/data/'

# get the list of all S & P 500 stocks
if not os.path.isfile(workPath + 'spStocks.parquet'):
    spStocks = pd.DataFrame(pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', attrs={'id': 'constituents'})[0])
    spStocks.to_parquet(workPath + 'spStocks.parquet')
else:
    spStocks = pd.read_parquet(workPath + 'spStocks.parquet')
    # extract ticker symbol to an array
    spStocks = spStocks['Symbol'].to_numpy()
    
# get list of all Nasdaq Stocks
if not os.path.isfile(workPath + 'nasdaqStocks.parquet'):    
    nasdaqStocks = pd.DataFrame(pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100', attrs={'id': 'constituents'})[0])
    nasdaqStocks.to_parquet(workPath + 'nasdaqStocks.parquet')
else:
    nasdaqStocks = pd.read_parquet(workPath + 'nasdaqStocks.parquet')
    # extract ticker symbol to an array
    nasdaqStocks = nasdaqStocks['Ticker'].to_numpy()
    
    
dowStocks = []
russelStocks = []

etfs = ['SPY', 'QQQ', 'DIA', 'IWM']


forexPairs = ['EURUSD=X', 'USDJPY=X', 'GBPUSD=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X', 'NZDUSD=X']

 #Error with these: 'NZDUSD=X', 'USDCAD=X', 'USDJPY=X', 
futures = ['ES=F', 'NQ=F', 'RTY=F', 'YM=F', 'CL=F', 'TN=F', 'GC=F', 'ZB=F', 'LE=F', 'SB=F', 'HG=F', 'SI=F']

getAllDataTickers = []
getTodaysDataTickers = []

tickersToDownload = np.concatenate( ( etfs, spStocks, forexPairs, nasdaqStocks, futures) ) 

# remove berkshire stock tickers
tickersToDownload = tickersToDownload[(tickersToDownload != 'BRK.B')]
tickersToDownload = tickersToDownload[(tickersToDownload != 'BF.B')]

# make sure we have a data file for each ticker
#   if exists then download todays data 
#   otherwise download all data
for ticker in tickersToDownload:
    if os.path.isfile(dataPath + ticker + '.parquet'):
        print(ticker + ": historical data exists")
        getTodaysDataTickers.append(ticker)

    else:
        print(ticker + ": historical data does NOT exist")
        getAllDataTickers.append(ticker)

#print('get all: ')
#print(getAllDataTickers)
#print('get today:')       
#print(getTodaysDataTickers)

# go get the data
if len(getAllDataTickers) > 0: 
    data = yf.download(getAllDataTickers, '2010-01-01', date.today(), group_by='ticker')
    #, parse_dates=['Date']

    for ticker in getAllDataTickers:
        data[ticker].to_parquet(dataPath + ticker + '.parquet')

if len(getTodaysDataTickers) > 0:
    todaysData = yf.download(getTodaysDataTickers, date.today(), date.today(), group_by='ticker')

    if todaysData.size > 0:
        for ticker in getTodaysDataTickers:
            # read historical data file and append new data
            historyData = pd.read_parquet(dataPath  + ticker + '.parquet')
            result = pd.concat([historyData, todaysData[ticker]])
            result.to_parquet(dataPath + ticker + '.parquet')
    else:
        print("no new data")
        