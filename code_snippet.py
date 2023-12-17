        indicators = data.ta.cdl_pattern(name="all")

        #is_engulfing_pattern = check_engulfing_pattern(data)
        engulfing_pattern = indicators.iloc[-1]["CDL_ENGULFING"]

        data["cndl_body_size"] = data["close"] - data["open"]
        data["cndl_direction"] = data.apply(set_cndl_up_or_down, axis=1)

        down_days = len(data.iloc[-8:].query("cndl_direction == 'down'"))
        up_days = len(data.iloc[-8:].query("cndl_direction == 'up'"))

        is_down_trend = (
            True if len(data.iloc[-4:-1].query("cndl_direction == 'down'")) == 3
            else False 
        )
        is_up_trend = (
            True if len(data.iloc[-4:-1].query("cndl_direction == 'up'")) == 3
            else False
        )


        print("is down trend? ", is_down_trend)
        print("is up trend? ", is_up_trend)


        print('first row first column')

        if engulfing_pattern == 100 and is_down_trend: 
            is_engulfing_pattern = "bullish engulfing"
        elif engulfing_pattern == -100 and is_up_trend:
            is_engulfing_pattern = "bearish engulfing"
        else:
            is_engulfing_pattern = None


        
        

        print(indicators.tail(6)[["CDL_ENGULFING", "CDL_MORNINGSTAR", "CDL_EVENINGSTAR"]] )

