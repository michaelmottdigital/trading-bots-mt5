import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime 
import json
import os

#
# Must be run at end of day after daily data is update in Yahoo Finance
#

workingFolder = "d:/StockAnalysis/"
dataFolder = "d:/StockAnalysis/data/"

listsFolder = "d:/StockAnalysis/lists/"

settingsFile = open('settings.json')
settings = json.load(settingsFile)
settingsFile.close()

SPY_holdings = pd.read_csv( listsFolder + 'SPYStocks.csv')


tickers = SPY_holdings.iloc[:, 0]


#
# check each ticker to see if we have previously dowwloaded the data
#  and that our the last run date corresponds to the last row in the
#  csv file
#
# From this we create two different lists
#    1. ticker that needs full history download
#    2. ticker that needs just the last n days, calculated from the last run date
#

tickersToDownload = []
tickersToUpdate = []

for ticker in tickers:
    if not os.path.exists(dataFolder + ticker + '.csv'):
        tickersToDownload.append(ticker)
        continue 
    
    tickersToUpdate.append(ticker)
        
        
#tickersToDownload = []
#tickersToUpdate = ['SPY']


print('- dwn: ' + ' '.join(tickersToDownload))
print('- updt: ' + ' '.join(tickersToUpdate))


#
# downlaod all history 
#
if len(tickersToDownload) > 0:
    endDate = date.today() + timedelta(days = -5)

    tickersDownloadData = yf.download(tickersToDownload, '2000-01-01', endDate, group_by='ticker')
    if len(tickersToDownload) < 2:
        ticker = tickersToDownload[0]
        print('downloading : ' + ticker)

        tickersDownloadData.sort_index(ascending=False).to_csv( dataFolder + ticker + '.csv')
    else:
        for ticker in tickersToDownload:
            print('downloading: ' + ticker)
            tickersDownloadData[ticker].sort_index(ascending=False).to_csv( dataFolder + ticker + '.csv')

#
# update recent history
#
if len(tickersToUpdate) > 0:
    # dowload last 10 days of history
    newData = yf.download(tickersToUpdate, date.today() + timedelta(days=-10), date.today(), group_by='ticker')
    
    # append new data to old data, remove dupliclates
    if len(tickersToUpdate) < 2:
        ticker = tickersToUpdate[0]
         # get old data from csv
        oldData = pd.read_csv( dataFolder + ticker + '.csv',index_col='Date', parse_dates=True )
   
        updatedData = pd.concat([oldData, newData]).sort_values(by=['Date'], ascending=False)
        
        # can not remove duplicates in place so we have to create a new variable
        outputData = updatedData.reset_index().drop_duplicates(subset='Date', keep='first').set_index('Date')
        
        print('updating : ' + ticker)
        outputData.to_csv(dataFolder + ticker + '.csv')
    else:
        for ticker in tickersToUpdate:
             # get old data from csv
            oldData = pd.read_csv( dataFolder + ticker + '.csv',index_col='Date', parse_dates=True )
   
            updatedData = pd.concat([oldData, newData[ticker]]).sort_values(by=['Date'], ascending=False)
        
            # can not remove duplicates in place so we have to create a new variable
            outputData = updatedData.reset_index().drop_duplicates(subset='Date', keep='first').set_index('Date')

            print('updating : ' + ticker)
            outputData.to_csv(dataFolder + ticker + '.csv')
    

print('****** ALL DONE ******')
    