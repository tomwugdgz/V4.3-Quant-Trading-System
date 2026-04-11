# -*- coding: utf-8 -*-
"""
执行 AUDUSD BUY - 信号强度 0.525% (最强信号)
"""
import MetaTrader5 as mt5
import sqlite3
from datetime import datetime

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("EXECUTE AUDUSD BUY - 信号强度 0.525% (最强信号)")
print("=" * 80)

# 获取账户信息
account = mt5.account_info()
balance = account.balance
print(f"账户余额：${balance:.2f}")

# 交易参数
symbol = "AUDUSD"
risk_pct = 0.005  # 0.5% 风险
stop_loss_pips = 30
take_profit_pips = 60  # 1:2 风报比

# 计算仓位
risk_amount = balance * risk_pct
pip_value_per_lot = 10  # AUDUSD: ~$10 per pip per 1.0 lot
lot_size = round(risk_amount / (stop_loss_pips * pip_value_per_lot), 2)

print(f"\n风险金额：${risk_amount:.2f} (0.5% 账户)")
print(f"止损：{stop_loss_pips} pips")
print(f"止盈：{take_profit_pips} pips (1:2 风报比)")
print(f"计算仓位：{lot_size:.2f} 手")

# 获取价格
tick = mt5.symbol_info_tick(symbol)
entry_price = tick.ask
sl_price = round(entry_price - (stop_loss_pips * 0.0001), 5)
tp_price = round(entry_price + (take_profit_pips * 0.0001), 5)

print(f"\n入场价：{entry_price:.5f}")
print(f"止损价：{sl_price:.5f}")
print(f"止盈价：{tp_price:.5f}")

# 发送订单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": mt5.ORDER_TYPE_BUY,
    "price": entry_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 10,
    "magic": 234000,
    "comment": "Signal_0.525pct_AUDUSD_BUY",
    "type_filling": mt5.ORDER_FILLING_IOC
}

print("\n发送订单...")
result = mt5.order_send(request)

print(f"返回码：{result.retcode}")
print(f"订单号：{result.order}")
print(f"成交价：{result.price:.5f}")

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
print(f"\nAUDUSD 持仓：{len(positions) if positions else 0} 单")
if positions:
    for pos in positions:
        print(f"  - {pos.volume} 手 @ {pos.price_open:.5f}, 盈亏：${pos.profit:.2f}")

mt5.shutdown()
