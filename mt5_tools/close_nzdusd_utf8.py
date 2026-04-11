# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

symbol = "NZDUSD"
positions = mt5.positions_get(symbol)

if not positions:
    print(f"无 {symbol} 持仓")
    mt5.shutdown()
    exit()

pos = positions[0]
print(f"找到持仓:")
print(f"  Ticket: {pos.ticket}")
print(f"  Volume: {pos.volume}")
print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
print(f"  Entry: {pos.price_open}")
print(f"  Profit: ${pos.profit}")

# 获取价格
tick = mt5.symbol_info_tick(symbol)
print(f"\n当前价格:")
print(f"  Bid: {tick.bid:.5f}")
print(f"  Ask: {tick.ask:.5f}")

# 平仓
if pos.type == 0:  # BUY
    price = tick.bid
    order_type = mt5.ORDER_TYPE_SELL
    action = "SELL"
else:
    price = tick.ask
    order_type = mt5.ORDER_TYPE_BUY
    action = "BUY"

print(f"\n执行平仓 {action}:")
print(f"  Price: {price:.5f}")
print(f"  Volume: {pos.volume}")
print(f"  Position: {pos.ticket}")

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": pos.volume,
    "type": order_type,
    "position": pos.ticket,
    "price": price,
    "deviation": 20,
    "magic": 234000,
    "comment": "close"
}

result = mt5.order_send(request)
print(f"\n订单结果:")
print(f"  Retcode: {result.retcode}")
print(f"  Comment: {result.comment}")

if result.retcode == 10009:
    print("\n*** 平仓成功 ***")
else:
    print(f"\n*** 平仓失败 ***")

# 验证
import time
time.sleep(1)
positions_after = mt5.positions_get(symbol)
print(f"\n验证：NZDUSD 持仓数 = {len(positions_after) if positions_after else 0}")

mt5.shutdown()
