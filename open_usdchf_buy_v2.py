# -*- coding: utf-8 -*-
"""
开仓 USDCHF BUY - 修复填充模式
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("开仓交易 - USDCHF BUY")
print("=" * 80)

# 初始化 MT5
if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("MT5 连接成功")

# 获取品种信息
symbol_info = mt5.symbol_info("USDCHF")
print(f"\n品种信息:")
print(f"  填充模式：{symbol_info.filling}")

# 交易参数
symbol = "USDCHF"
volume = 0.17
sl_pips = 30
tp_pips = 60

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
entry_price = tick.ask
sl_price = round(entry_price - sl_pips * 0.0001, 5)
tp_price = round(entry_price + tp_pips * 0.0001, 5)

print(f"\n交易参数:")
print(f"  品种：{symbol}")
print(f"  方向：BUY")
print(f"  手数：{volume}")
print(f"  入场价：{entry_price:.5f}")
print(f"  止损：{sl_price:.5f} (-{sl_pips} pips)")
print(f"  止盈：{tp_price:.5f} (+{tp_pips} pips)")

# 构建开仓请求 (添加 type_filling)
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
    "comment": "Python312_signal_0.128pct",
    "type_filling": mt5.ORDER_FILLING_IOC
}

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
    print("\n[OK] 开仓成功！")
    
    # 保存到数据库
    db_path = "C:\\Users\\DELL\\.openclaw-autoclaw\\workspace\\trading\\trading.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO orders (order_id, symbol, type, volume, price, sl, tp, comment, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result.order,
        symbol,
        "BUY",
        result.volume,
        result.price,
        sl_price,
        tp_price,
        "Python312_signal_0.128pct",
        datetime.now()
    ))
    
    conn.commit()
    conn.close()
    print("[OK] 订单已保存到数据库")
else:
    print(f"\n[FAIL] 开仓失败 (retcode={result.retcode})")

# 验证
import time
time.sleep(1)
positions = mt5.positions_get(symbol=symbol)
print(f"\n验证：{symbol} 持仓数量 = {len(positions) if positions else 0}")

if positions:
    for pos in positions:
        print(f"  Ticket: {pos.ticket}")
        print(f"  Volume: {pos.volume}")
        print(f"  Entry: {pos.price_open:.5f}")
        print(f"  SL: {pos.sl:.5f}")
        print(f"  TP: {pos.tp:.5f}")
        print(f"  Profit: ${pos.profit:.2f}")

mt5.shutdown()
print("\n" + "=" * 80)
print("交易执行完成")
print("=" * 80)
