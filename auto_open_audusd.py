# -*- coding: utf-8 -*-
"""
开仓 AUDUSD BUY - 信号 0.125% - 全仓出击
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("开仓 AUDUSD BUY - 信号 0.125% - 全仓出击")
print("=" * 80)

symbol = "AUDUSD"
volume = 0.17

tick = mt5.symbol_info_tick(symbol)
entry_price = tick.ask
sl_price = round(entry_price - 0.0030, 5)
tp_price = round(entry_price + 0.0060, 5)

print(f"品种：{symbol}")
print(f"手数：{volume}")
print(f"入场：{entry_price:.5f}")
print(f"止损：{sl_price:.5f}")
print(f"止盈：{tp_price:.5f}")

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
    "comment": "AllIn_signal_0.125pct",
    "type_filling": mt5.ORDER_FILLING_IOC
}

print("\n发送订单...")
result = mt5.order_send(request)

print(f"Retcode: {result.retcode}")
print(f"Order: {result.order}")
print(f"Price: {result.price:.5f}")

if result.retcode == 10009:
    print("\n[OK] 开仓成功！")
    
    conn = sqlite3.connect("trading.db")
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO orders (order_id, symbol, type, volume, price, sl, tp, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (result.order, symbol, "BUY", volume, result.price, sl_price, tp_price, datetime.now()))
    conn.commit()
    conn.close()
else:
    print(f"\n[FAIL] retcode={result.retcode}")

import time
time.sleep(1)
positions = mt5.positions_get(symbol=symbol)
print(f"\nAUDUSD 持仓：{len(positions) if positions else 0}")

mt5.shutdown()
