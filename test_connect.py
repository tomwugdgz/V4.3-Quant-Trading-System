# -*- coding: utf-8 -*-
# 测试 MT5 Python API 连接
# 如果这个脚本可以正常运行并显示账户信息，说明连接正常

import MetaTrader5 as mt5

print("=== MT5 Connection Test ===\n")

result = mt5.initialize()
print("Initialize: ", result)

if not result:
    error = mt5.last_error()
    print("Error: ", error)
    print("\nCommon fixes:")
    print("1. 确认 MT5 终端已启动并登录账号")
    print("2. 确认 MT5 设置中允许自动交易")
    print("3. 重启 MT5 终端后重试")
    exit()

account = mt5.account_info()
print("\nConnect OK!")
print("Account: ", account.login)
print("Balance: $", account.balance)
print("Equity: $", account.equity)
print("Free Margin: $", account.margin_free)
print()

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'USDCAD']
print("Symbols check:")
for sym in symbols:
    tick = mt5.symbol_info_tick(sym)
    if tick:
        print(f"  {sym}: OK (bid={tick.bid:.5f} ask={tick.ask:.5f})")
    else:
        print(f"  {sym}: ❌ 无法获取")

positions = mt5.positions_get()
print(f"\nCurrent positions: {len(positions)}")
if positions:
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        print(f"  {pos.symbol} {direction} {pos.volume:.2f} lot P/L ${pos.profit:.2f}")

print("\n=== 测试完成 ===")
mt5.shutdown()
