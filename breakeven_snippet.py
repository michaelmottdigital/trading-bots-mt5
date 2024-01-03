 # get current price so we can adjust the stop loss
        # only move stop loss if 
        #   1. the current_price is greater than (long) or less than (short) the price at which we opened the trade
        #   2. the gap between the old and new ts is big enough
        #
        if position["long_or_short"] == "long" :
            current_price = mt5.symbol_info_tick(symbol).ask
            
            print(" --- open position ", open_position)
            print("---- position", position)
            # move to breakeven or next ts increment
            if (not is_at_breakeven and 
                current_cdl.cdl_up == True and 
                current_price >= open_position.price_open + position["ts_amount"]
                ):
                    new_ts = open_position.price_open + 1
                    is_at_breakeven = True
                    print("--! -- at breakeven")    
                    if IS_SPEECH_ENABLED:
                        speaker.Speak('At Break even')
                    move_stop_loss = True
            
            elif (is_at_breakeven):

                # move stop loss to bottom of previous candle if 
                # the new stop loss is atleast 
                
                if (current_price >= current_cdl.close and 
                    current_cdl.cdl_up):

                    new_ts = previous_cdl.open 
                    move_stop_loss = True
                    


                # move the stop loss
                #new_ts = current_price - ts_amount
                #move_stop_loss = True


        else: 
            # short position
            current_price = mt5.symbol_info_tick(symbol).bid

            if (not is_at_breakeven and 
                current_cdl.cdl_down == True and 
                current_price <= open_position.price_open - position["ts_amount"]
                ):
                    new_ts = open_position.price_open - 1
                    is_at_breakeven = True
                    print("--! -- at breakeven")    
                    if IS_SPEECH_ENABLED:
                        speaker.Speak('At Break even')
                    move_stop_loss = True

            elif (is_at_breakeven):
                # move the stop loss
                 if (current_price <= current_cdl.close and 
                    current_cdl.cdl_down):

                    new_ts = previous_cdl.open 
                    move_stop_loss = True