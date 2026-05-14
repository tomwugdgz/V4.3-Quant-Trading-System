import MetaTrader5 as mt5
mt5.initialize()
for sym in ['EURUSD', 'USDJPY', 'NZDUSD']:
    si = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)
    if si and tick:
        digits = si.digits
        pip_size = si.point * 10 if digits in (3, 5) else si.point
        if si.trade_tick_size > 0:
            pip_value = si.trade_tick_value * (pip_size / si.trade_tick_size)
        else:
            pip_value = pip_size * si.trade_contract_size
        print(f'{sym}: pip_size={pip_size}, pip_value_per_lot=${pip_value:.2f}')
mt5.shutdown()
