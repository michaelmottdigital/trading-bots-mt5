 # 1 hour chart
    # 20, 50 ma cross 
    # follow 35 sma 
    # buy only 
    strategy_ma_cross = False
    if strategy_ma_cross:
        is_test_buy = False
        is_test_sell = False
        if is_test_buy or (current_cdl.ind_ma_cross == 1 
                        #and current_cdl.cdl_up
                        ):
            # buy
            if is_daytime():
                    speaker.Speak('alert BUY')

            print("Buy")
            current_price = mt5.symbol_info_tick(symbol).ask
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "buy", number_of_lots, sl_amount, timeframe)
            return position

        elif is_test_sell or (current_cdl.ind_ma_cross == -1
                            # and current_cdl.cdl_down
                            ):
            # sell
            if is_daytime():
                    speaker.Speak('alert SELL')
            print("Sell")
            current_price = mt5.symbol_info_tick(symbol).bid
            sl_amount = current_cdl.ind_atr * 1.5
            position = create_opening_trade(symbol, "sell", number_of_lots, sl_amount, timeframe)
            return position

