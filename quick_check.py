import MetaTrader5 as mt5
from datetime import datetime
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)
info = mt5.account_info()
positions = mt5.positions_get()
for p in positions:
    pdir = 'BUY' if p.type == 0 else 'SELL'
    open_time = datetime.fromtimestamp(p.time)
    print(f"{p.symbol} {pdir} {p.volume}@{p.price_open:.5f} 浮盈=${p.profit:.2f} 开仓{open_time.strftime('%m-%d %H:%M')}")
print(f"余额=${info.balance:.2f} 净值=${info.equity:.2f}")
mt5.shutdown()