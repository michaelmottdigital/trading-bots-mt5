from trade_utils import is_daytime

def check_rsi_signal(data):

    print("\n----------------------")
    print("Checking RSI Signal")
    print("----------------------")

    current_cdl = data.iloc[0]
   
    print( data[["ind_rsi", "signal_rsi_buy", "signal_rsi_sell"]].head(10) )

    if current_cdl.signal_rsi_buy:
        return "buy"
    elif current_cdl.signal_rsi_sell:
        return "sell"
    else:
        return None
    
    


def check_engulfing_candle(data):

    print("\n----------------------")
    print("Checking Engulfing Candle Signal")
    print("----------------------")

    print( data[["ptn_bullish_engulfing_1", "ptn_bearish_engulfing_1", "low", "high", "ind_sma50"]].head(10) )

    current_cdl = data.iloc[0]

    if ( 
        current_cdl.ptn_bullish_engulfing_1 and
        current_cdl.low < current_cdl.ind_sma50 and
        current_cdl.high < current_cdl.ind_sma50
        ):
       return "buy"

    elif (
        current_cdl.ptn_bearish_engulfing_1 and
        current_cdl.high > current_cdl.ind_sma50 and
        current_cdl.low > current_cdl.ind_sma50

        ):
        return "sell"
    else:
        return None