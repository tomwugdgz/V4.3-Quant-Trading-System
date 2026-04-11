import MetaTrader5 as mt5

mt5.initialize()
account = mt5.account_info()
positions = mt5.positions_get()

print(f'余额：${account.balance:.2f}')
print(f'净值：${account.equity:.2f}')
print(f'持仓数：{len(positions) if positions else 0}')

if positions:
    for pos in positions:
        direction = 'BUY' if pos.type == 0 else 'SELL'
        print(f'  {pos.symbol}: {direction} {pos.volume}手 盈亏：${pos.profit:.2f}')

mt5.shutdown()
