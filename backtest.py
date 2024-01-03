import MetaTrader5 as mt5
import time
from utils import get_symbol_history, append_cdl_patterns

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()


data = get_symbol_history(symbol="ETHUSD", closed_candles_only=True)

data = append_cdl_patterns(data)


# oldest first so we can test trades from the beginning of time period
data.sort_index(ascending=False, inplace=True)

#print(data.info())
#exit(0)

#current_time = ""
# get ticks so we can check current price

# go through each period
while True:
    is_position_open = False
    for index, row in data.iterrows():
        print(row.close, row.rsi)
    
        # define entry criteria
        if row.rsi >= 70: 
            print("sell")
            is_position_open = True
        elif row.rsi <= 30:
            print("buy")
            is_position_open = True

        # if position is open look , make adjustments
        if is_position_open:
            



        time.sleep(.05)
    






