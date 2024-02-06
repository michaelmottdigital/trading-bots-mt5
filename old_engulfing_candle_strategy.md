 strategy_engulfing = False 
    if strategy_engulfing: 
        # convert to numpy array so it easier to access previous rsi values
        ind_rsi = data.ind_rsi.to_numpy()

        rsi_overbought_threshold = 65
        rsi_oversold_threshold = 35

#        is_down_trend = (
#            True if ind_rsi[1] < rsi_oversold_threshold or ind_rsi[2] < rsi_oversold_threshold or ind_rsi[3] < rsi_oversold_threshold
#            else False
#        )

#        is_up_trend = (
#            True if ind_rsi[1] > rsi_overbought_threshold or ind_rsi[2] > rsi_overbought_threshold or ind_rsi[3] > rsi_overbought_threshold
#            else False
#        )
        if ( current_cdl.ptn_bullish_engulfing_1 and
            current_cdl.is_prev_trend_down #and
            #previous_cdl.ind_rsi <= rsi_oversold_threshold
            ):
            if is_daytime():
                speaker.Speak('alert BUY')
            print("Buy")
            current_price = mt5.symbol_info_tick(symbol).ask
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "buy", number_of_lots, sl_amount, timeframe)
            return position

        if (current_cdl.ptn_bearish_engulfing_1 
            and current_cdl.is_prev_trend_up
            #and previous_cdl.ind_rsi >= rsi_overbought_threshold
            ):
            if is_daytime():
                speaker.Speak('alert SELL')
            print("Sell")
            current_price = mt5.symbol_info_tick(symbol).bid
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "sell", number_of_lots, sl_amount, timeframe)
            return position


