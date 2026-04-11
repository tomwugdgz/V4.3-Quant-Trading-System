# -*- coding: utf-8 -*-
"""
调仓操作：平仓 1 单 USDCHF → 开 AUDUSD
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("调仓操作：平仓 USDCHF → 开 AUDUSD")
print("=" * 80)

# 第 1 步：平仓 1 单 USDCHF
print("\n[第 1 步] 平仓 1 单 USDCHF...")
positions = mt5.positions_get(symbol="USDCHF")
if positions:
    pos = positions[0]  # 平第一单
    print(f"  平仓：Ticket {pos.ticket}, Volume {pos.volume}, Profit ${pos.profit:.2f}")
    
    tick = mt5.symbol_info_tick("USDCHF")
    # BUY 平仓用 SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "USDCHF",
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": pos.ticket,
        "price": tick.bid,
        "deviation": 10,
        "magic": 234000,
        "comment": "Rebalance_for_AUDUSD"
    }
    
    result = mt5.order_send(request)
    print(f"  Retcode: {result.retcode}")
    if result.retcode == 10009:
        print(f"  [OK] 平仓成功！成交价：{result.price:.5f}")
    else:
        print(f"  [FAIL] retcode={result.retcode}")
else:
    print("  无 USDCHF 持仓")

import time
time.sleep(2)

# 第 2 步：开 AUDUSD BUY
print("\n[第 2 步] 开仓 AUDUSD BUY - 信号 0.125%...")
symbol = "AUDUSD"
volume = 0.17

tick = mt5.symbol_info_tick(symbol)
entry_price = tick.ask
sl_price = round(entry_price - 0.0030, 5)
tp_price = round(entry_price + 0.0060, 5)

print(f"  品种：{symbol}")
print(f"  手数：{volume}")
print(f"  入场：{entry_price:.5f}")
print(f"  止损：{sl_price:.5f}")
print(f"  止盈：{tp_price:.5f}")

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": entry_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 10,
    "magic": 234000,
    "comment": "Rebalance_signal_0.125pct",
    "type_filling": mt5.ORDER_FILLING_IOC
}

result = mt5.order_send(request)
print(f"  Retcode: {result.retcode}")
if result.retcode == 10009:
    print(f"  [OK] 开仓成功！成交价：{result.price:.5f}")
    
    # 保存数据库
    conn = sqlite3.connect("trading.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO orders (order_id, symbol, type, volume, price, sl, tp, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (result.order, symbol, "BUY", volume, result.price, sl_price, tp_price, datetime.now()))
    conn.commit()
    conn.close()
else:
    print(f"  [FAIL] retcode={result.retcode}")

time.sleep(2)

# 第 3 步：验证持仓
print("\n[第 3 步] 验证持仓...")
all_positions = mt5.positions_get()
print(f"总持仓数量：{len(all_positions) if all_positions else 0}")

if all_positions:
    for pos in all_positions:
        side = "BUY" if pos.type == 0 else "SELL"
        print(f"  {pos.symbol} {side} {pos.volume} profit=${pos.profit:.2f}")

mt5.shutdown()
print("\n" + "=" * 80)
print("调仓完成")
print("=" * 80)
