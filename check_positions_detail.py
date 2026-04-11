import MetaTrader5 as mt5
import json

if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

positions = mt5.positions_get()
if not positions:
    print("No open positions")
    mt5.shutdown()
    exit(0)

print("=" * 80)
print("当前持仓详情 (Current Positions)")
print("=" * 80)

for pos in positions:
    print(f"\n{pos.symbol}:")
    print(f"  方向：{'BUY' if pos.type == 0 else 'SELL'}")
    print(f"  仓位：{pos.volume} 手")
    print(f"  入场价：{pos.price_open:.5f}")
    print(f"  当前价：{pos.price_current:.5f}")
    print(f"  止损：{pos.sl:.5f} ({'未设置' if pos.sl == 0 else f'{abs(pos.price_open - pos.sl) * 10000:.1f} pips'})")
    print(f"  止盈：{pos.tp:.5f} ({'未设置' if pos.tp == 0 else f'{abs(pos.tp - pos.price_open) * 10000:.1f} pips'})")
    print(f"  浮盈：${pos.profit:.2f}")
    print(f"  订单号：{pos.ticket}")
    print(f"  开仓时间：{pos.time}")

# 获取账户信息
account = mt5.account_info()
print("\n" + "=" * 80)
print("账户信息")
print("=" * 80)
print(f"  余额：${account.balance:.2f}")
print(f"  净值：${account.equity:.2f}")
print(f"  杠杆：1:{account.leverage}")
print(f"  可用保证金：${account.margin_free:.2f}")
print(f"  保证金水平：{account.margin_level:.1f}%")

mt5.shutdown()
