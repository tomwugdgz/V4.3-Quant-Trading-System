# -*- coding: utf-8 -*-
"""
开仓 USDCHF BUY - 简化版
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("MT5 连接成功")

symbol = "USDCHF"
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

# 尝试不同填充模式
for filling_mode in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
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
        "comment": "Python312_test",
        "type_filling": filling_mode
    }
    
    print(f"\n尝试填充模式：{filling_mode}")
    result = mt5.order_send(request)
    
    if result.retcode == 10009:
        print(f"成功！Order: {result.order}, Price: {result.price:.5f}")
        
        # 保存数据库
        conn = sqlite3.connect("trading.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO orders (order_id, symbol, type, volume, price, sl, tp, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (result.order, symbol, "BUY", volume, result.price, sl_price, tp_price, datetime.now()))
        conn.commit()
        conn.close()
        print("订单已保存")
        break
    else:
        print(f"失败：retcode={result.retcode}")

# 验证
import time
time.sleep(1)
positions = mt5.positions_get(symbol=symbol)
print(f"\n验证持仓：{len(positions) if positions else 0}")

if positions:
    for pos in positions:
        print(f"Ticket: {pos.ticket}, Profit: ${pos.profit:.2f}")

mt5.shutdown()
