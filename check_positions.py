import MetaTrader5 as mt5
import datetime

mt5.initialize()

# 当前持仓
positions = mt5.positions_get()
print("=== 当前持仓 ===")
if positions:
    total_profit = 0
    for p in positions:
        direction = "SELL" if p.type == 1 else "BUY"
        profit = p.profit
        total_profit += profit
        print(f"{p.symbol}: {direction} {p.volume} @ {p.price_open:.5f} profit=${profit:.2f}")
    print(f"\n持仓总盈亏：${total_profit:.2f}")
    print(f"持仓数量：{len(positions)}")
else:
    print("无持仓")

# 账户信息
info = mt5.account_info()
print(f"\n=== 账户信息 ===")
print(f"余额：${info.balance:.2f}")
print(f"净值：${info.equity:.2f}")
print(f"杠杆：1:{info.leverage}")
print(f"保证金水平：{info.margin_level:.2f}%")
