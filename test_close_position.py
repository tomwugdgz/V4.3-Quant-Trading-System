# -*- coding: utf-8 -*-
"""
测试平仓功能 - Python 3.12 + UTF-8
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime
from pathlib import Path

print("=" * 80)
print("测试平仓功能")
print("=" * 80)

# 初始化 MT5
if not mt5.initialize():
    print("❌ MT5 初始化失败")
    exit()

print("[OK] MT5 连接成功")

# 获取持仓
positions = mt5.positions_get()
print(f"\n当前持仓数量：{len(positions) if positions else 0}")

if not positions:
    print("无持仓")
    mt5.shutdown()
    exit()

# 显示持仓
for pos in positions:
    side = "BUY" if pos.type == 0 else "SELL"
    print(f"  {pos.symbol} {side} {pos.volume} 入场={pos.price_open:.5f} 盈亏=${pos.profit:.2f}")

# 测试平仓 NZDUSD
symbol_to_close = "NZDUSD"
print(f"\n准备平仓：{symbol_to_close}")

positions = mt5.positions_get(symbol=symbol_to_close)
if not positions:
    print(f"无 {symbol_to_close} 持仓")
    mt5.shutdown()
    exit()

pos = positions[0]
print(f"  Ticket: {pos.ticket}")
print(f"  Volume: {pos.volume}")
print(f"  入场价：{pos.price_open:.5f}")
print(f"  当前盈亏：${pos.profit:.2f}")

# 获取当前价格
tick = mt5.symbol_info_tick(symbol_to_close)
if pos.type == 0:  # BUY
    price = tick.bid
    order_type = mt5.ORDER_TYPE_SELL
    action = "SELL"
else:
    price = tick.ask
    order_type = mt5.ORDER_TYPE_BUY
    action = "BUY"

print(f"\n执行平仓 {action}:")
print(f"  价格：{price:.5f}")
print(f"  手数：{pos.volume}")

# 构建请求
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol_to_close,
    "volume": pos.volume,
    "type": order_type,
    "position": pos.ticket,
    "price": price,
    "deviation": 20,
    "magic": 234000,
    "comment": "Python312_test_close"
}

# 发送订单
print("\n发送订单...")
result = mt5.order_send(request)

print(f"\n订单结果:")
print(f"  Retcode: {result.retcode}")
print(f"  Order: {result.order}")
print(f"  Volume: {result.volume}")
print(f"  Price: {result.price:.5f}")
print(f"  Comment: {result.comment}")

# 检查成功
if result.retcode == 10009:
    print("\n[OK] 平仓成功！")
    
    # 保存到数据库
    db_path = Path(__file__).parent / "trading.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO orders (order_id, symbol, type, volume, price, profit, comment, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result.order,
        symbol_to_close,
        action,
        result.volume,
        result.price,
        result.profit if hasattr(result, 'profit') else pos.profit,
        'Python312_test_close',
        datetime.now()
    ))
    
    conn.commit()
    conn.close()
    print("[OK] 订单已保存到数据库")
else:
    print(f"\n❌ 平仓失败 (retcode={result.retcode})")

# 验证
import time
time.sleep(1)
positions_after = mt5.positions_get(symbol=symbol_to_close)
print(f"\n验证：{symbol_to_close} 持仓数量 = {len(positions_after) if positions_after else 0}")

mt5.shutdown()
print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
