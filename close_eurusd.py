import MetaTrader5 as mt5
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)
positions = mt5.positions_get()
for p in positions:
    if p.symbol == 'EURUSD':
        mt5.position_close(p.ticket)
        print(f"平仓 EURUSD BUY #{p.ticket} 利润=${p.profit:.2f}")
info = mt5.account_info()
print(f"余额=${info.balance:.2f} 净值=${info.equity:.2f}")
mt5.shutdown()