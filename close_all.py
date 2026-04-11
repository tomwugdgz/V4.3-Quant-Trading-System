#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import json
from datetime import datetime

mt5.initialize()

# 读取 72 小时计划
with open('72h_trades.json', 'r') as f:
    plan = json.load(f)

print("=== Starting to close all 72h plan positions ===\n")

# 获取所有持仓
positions = mt5.positions_get()
if not positions:
    print("No positions")
    mt5.shutdown()
    exit()

print(f"Total positions: {len(positions)}\n")

# 平仓所有 72 小时计划的持仓
plan_tickets = [t['ticket'] for t in plan['trades']]
closed = []
total_profit = 0

for pos in positions:
    # 检查是否是计划内的持仓
    if pos.ticket not in plan_tickets:
        print(f"Skip non-plan position: {pos.symbol}")
        continue
    
    # 准备平仓请求
    if pos.type == 0:  # 买入，需要卖出平仓
        order_type = mt5.ORDER_TYPE_SELL
    else:  # 卖出，需要买入平仓
        order_type = mt5.ORDER_TYPE_BUY
    
    # 获取当前价格
    tick = mt5.symbol_info_tick(pos.symbol)
    if tick is None:
        print(f"{pos.symbol} 获取价格失败，跳过")
        continue
    
    price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
    
    # 发送平仓请求
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": order_type,
        "position": pos.ticket,
        "price": price,
        "deviation": 20,
        "magic": 234001,
        "comment": "旺财 72h 计划止损平仓",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        profit = pos.profit
        total_profit += profit
        closed.append({
            "symbol": pos.symbol,
            "volume": pos.volume,
            "profit": float(profit),
            "ticket": pos.ticket,
            "time": datetime.now().isoformat()
        })
        direction = "BUY" if pos.type == 0 else "SELL"
        print(f"[OK] {pos.symbol} {direction} {pos.volume} closed, P/L: ${profit:.2f}")
    else:
        print(f"[FAIL] {pos.symbol} close failed: retcode={result.retcode}")

# 总结
print(f"\n=== Close Complete ===")
print(f"Closed: {len(closed)} positions")
print(f"Total P/L: ${total_profit:.2f}")

# 保存到文件
output = {
    "close_time": datetime.now().isoformat(),
    "closed_positions": closed,
    "total_profit": float(total_profit),
    "reason": "Stop loss at -70%"
}

with open("72h_closed.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved to 72h_closed.json")

# 查询最终账户
account = mt5.account_info()
print(f"\nAccount Balance: ${account.balance:.2f}")
print(f"Account Equity: ${account.equity:.2f}")

mt5.shutdown()
