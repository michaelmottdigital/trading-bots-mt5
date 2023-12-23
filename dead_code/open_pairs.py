from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
import time
from win11toast import toast
#import win32com.client
import math
import argparse

def truncate(number, digits):
    x = number * (10**digits)
    return math.trunc(x) / (10**digits)

def do_trade(symbol, price, order_type, lot_size, stop_loss):
    
    if order_type == 'buy':
        mt5_order_type = mt5.ORDER_TYPE_BUY
    else: 
        mt5_order_type = mt5.ORDER_TYPE_SELL
        

    if order_type == 'buy':
        sl = price - stop_loss
    else:
        sl = price + stop_loss  


    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5_order_type,
        "sl": sl,
        "comment": order_type + ' ' + symbol,
        "type_time": mt5.ORDER_TIME_GTC
    }


    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("2. order_send failed, retcode={}".format(result.retcode), result)
        print("shutdown() and quit")
        mt5.shutdown()
        quit()

    print("opened position with POSITION_TICKET={}".format(result.order))





# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


parser = argparse.ArgumentParser(prog='Open Trade')
parser.add_argument('trade_type')
parser.add_argument('symbol')
parser.add_argument('size', type=int)
args = parser.parse_args()

# check arguments
if args.size > 2 or args.size <= 0:
    print('error bad lot size: ', args.size)
    quit()

print('Connected Version: ' + str(mt5.version()))
#speaker = win32com.client.Dispatch("SAPI.SpVoice")
#speaker.Speak('connected to Meta trader')

confirm = input('Are you sure you want to ' + args.trade_type + ' symbol ' + args.symbol + ' (Y/N): ')
if confirm.upper() == 'N':
    mt5.shutdown()
    quit()




currentTime = time.localtime()

print('Checking Prices ', time.strftime('%I:%M', currentTime))


# GET LAST TICK
spxData = mt5.symbol_info_tick('SP500')._asdict()
ndxData = mt5.symbol_info_tick('NAS100')._asdict()
eurusdData = mt5.symbol_info_tick('EURUSD')._asdict()

spxPrice = spxData['bid']
ndxPrice = ndxData['bid']
eurusdPrice = eurusdData['bid']

ratio =  truncate(ndxPrice/spxPrice,3)

if args.size == 1:
    ndxLots = .01
    spxLots = .03
elif args.size == 2:
    ndxLots = .02
    spxLots = .07
else: 
    ndxLots = 0
    spxLots = 0

if args.trade_type == 'sell' and args.symbol.lower() == 'nas':
    print('sell nasdaq but spy', ndxLots, spxLots)
    do_trade('NAS100', ndxPrice, 'sell', ndxLots, 200 )
    do_trade('SP500', spxPrice, 'buy', spxLots, 100 )
elif args.trade_type == 'buy' and args.symbol.lower() == 'nas':
    print('buy nasdaq sell spy', ndxLots, spxLots)
    do_trade('NAS100', ndxPrice, 'buy', ndxLots, 200 )
    do_trade('SP500', spxPrice, 'sell', spxLots, 100 )

else: 
    print('no trade to make')
    quit()




mt5.shutdown()
