Open new Trade returns:

OrderSendResult(
    retcode=10009, deal=48861614, order=202684536, volume=0.01, price=2250.21, bid=0.0, ask=0.0, comment='Request executed', request_id=2825678363, retcode_external=0, request=TradeRequest(action=1, magic=0, order=0, symbol='ETHUSD', volume=0.01, price=0.0, stoplimit=0.0, sl=2243.8531766949127, tp=0.0, deviation=0, type=0, type_filling=0, type_time=0, expiration=0, comment='buyETHUSD', position=0, position_by=0))


Get an open position: ( positions_get )

(TradePosition(ticket=202684711, time=1704565254, time_msc=1704565254344, time_update=1704565254, time_update_msc=1704565254344, type=0, magic=0, identifier=202684711, reason=3, volume=0.01, price_open=2246.7, sl=2239.95, tp=0.0, price_current=2245.24, swap=0.0, profit=-0.01, symbol='ETHUSD', comment='buyETHUSD', external_id=''),)

type = 0 = buy, 1 = sell

