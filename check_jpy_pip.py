import MetaTrader5 as mt5
mt5.initialize()
mt5.login(52797683)
for sym in ['USDJPY','EURJPY','GBPJPY','EURUSD','GBPUSD']:
    info = mt5.symbol_info(sym)
    if info:
        print(sym + ':')
        print('  point=' + str(info.point) + '  digits=' + str(info.digits))
        print('  tick_size=' + str(info.trade_tick_size) + '  tick_value=' + str(info.trade_tick_value))
        print('  contract_size=' + str(info.trade_contract_size))
        pip = info.point * 10 if info.digits in (3,5) else info.point
        if info.trade_tick_size > 0:
            pv = info.trade_tick_value * (pip / info.trade_tick_size)
        else:
            pv = pip * info.trade_contract_size
        print('  pip_size=' + str(pip) + '  pip_value_per_lot=$' + str(round(pv, 4)))
        print()
