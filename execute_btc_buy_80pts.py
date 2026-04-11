# -*- coding: utf-8 -*-
"""
开仓 BTCUSD BUY - 信号强度 80 分 - 超强信号
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("EXECUTE BTCUSD BUY - 信号强度 80 分 (超强信号)")
print("=" * 80)

# 获取账户信息
account = mt5.account_info()
balance = account.balance
print(f"账户余额：${balance:.2f}")

# 交易参数
symbol = "BTCUSD"
risk_pct = 0.0025  # 0.25% 风险 (新规则)
stop_loss_pct = 0.020  # 2% 止损
take_profit_pct = 0.040  # 4% 止盈 (1:2 风报比)

# 计算仓位
risk_amount = balance * risk_pct
print(f"\n风险金额：${risk_amount:.2f} (0.25% 账户)")

# 获取价格
tick = mt5.symbol_info_tick(symbol)
entry_price = tick.ask
print(f"入场价：${entry_price:.2f}")

# 计算 SL 和 TP
sl_price = round(entry_price * (1 - stop_loss_pct), 2)
tp_price = round(entry_price * (1 + take_profit_pct), 2)
sl_distance = entry_price - sl_price
tp_distance = tp_price - entry_price

print(f"止损：${sl_price:.2f} (-{stop_loss_pct*100:.1f}%, -${sl_distance:.2f})")
print(f"止盈：${tp_price:.2f} (+{take_profit_pct*100:.1f}%, +${tp_distance:.2f})")
print(f"风报比：1:{take_profit_pct/stop_loss_pct:.1f}")

# 计算仓位 (BTC: $1 per 0.01 lot per $1 move)
# 风险金额 / 止损距离 = 手数
lot_size = round(risk_amount / sl_distance, 2)
print(f"\n计算仓位：{lot_size:.2f} 手")

# 发送订单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": mt5.ORDER_TYPE_BUY,
    "price": entry_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 50,
    "magic": 234000,
    "comment": "BTC_Signal_80pts_BUY",
    "type_filling": mt5.ORDER_FILLING_IOC
}

print("\n发送订单...")
result = mt5.order_send(request)

print(f"返回码：{result.retcode}")
print(f"订单号：{result.order}")
print(f"成交价：${result.price:.2f}")

if result.retcode == 10009:
    print("\n[OK] 开仓成功！")
    
    # 记录到数据库
    try:
        conn = sqlite3.connect("trading.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO orders (order_id, symbol, type, volume, price, sl, tp, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (result.order, symbol, "BUY", lot_size, result.price, sl_price, tp_price, datetime.now()))
        conn.commit()
        conn.close()
        print("[OK] 已记录到数据库")
    except Exception as e:
        print(f"[WARN] 数据库记录失败：{e}")
else:
    print(f"\n[FAIL] 开仓失败 retcode={result.retcode}")

import time
time.sleep(1)

# 显示持仓
positions = mt5.positions_get(symbol=symbol)
print(f"\nBTCUSD 持仓：{len(positions) if positions else 0} 单")
if positions:
    for pos in positions:
        print(f"  - {pos.volume:.2f} 手 @ ${pos.price_open:.2f}, 盈亏：${pos.profit:.2f}")

mt5.shutdown()
