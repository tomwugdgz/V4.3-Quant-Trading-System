import MetaTrader5 as mt5
import datetime
import json

mt5.initialize()

# 获取账户信息
account = mt5.account_info()
print(f"账户余额：${account.balance:.2f}")
print(f"账户净值：${account.equity:.2f}")
print(f"总盈亏：${account.profit:.2f}")
print("")

# 获取 BTC 持仓
positions = mt5.positions_get(symbol='BTCUSD')
print("=== 当前 BTC 持仓 ===")
if positions:
    for p in positions:
        direction = "做多" if p.type == 0 else "做空"
        print(f"订单号：{p.ticket}")
        print(f"方向：{direction}")
        print(f"手数：{p.volume}")
        print(f"入场价：${p.price_open:.2f}")
        print(f"当前价：${p.price_current:.2f}")
        print(f"止损：${p.sl:.2f}")
        print(f"止盈：${p.tp:.2f}")
        print(f"浮动盈亏：${p.profit:.2f}")
        print(f"开仓时间：{datetime.datetime.fromtimestamp(p.time)}")
else:
    print("无 BTC 持仓")

print("")

# 获取所有持仓
all_positions = mt5.positions_get()
print(f"总持仓数：{len(all_positions) if all_positions else 0}")

mt5.shutdown()
