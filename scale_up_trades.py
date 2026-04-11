#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import json
from datetime import datetime

# 初始化 MT5
if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

# 读取已有交易计划
with open("72h_trades.json", "r") as f:
    plan = json.load(f)

# 调整: 总风险从 $280 → $2000
old_total_risk = plan['total_risk']
new_total_risk = 2000.0
scale_factor = new_total_risk / old_total_risk

print(f"原有总风险: ${old_total_risk}")
print(f"新总风险: ${new_total_risk}")
print(f"缩放系数: {scale_factor:.2f}x\n")

# 获取当前已开仓的本计划交易
existing_tickets = [t['ticket'] for t in plan['trades']]
print(f"计划内已有订单: {existing_tickets}")

# 我们加仓: 在每个原有方向基础上，再开 (scale_factor - 1) 倍仓位
# 保持相同的止损止盈价格

trades_added = []

for trade in plan['trades']:
    sym = trade['symbol']
    order_type = trade['order_type']
    old_volume = trade['volume']
    add_volume = old_volume * (scale_factor - 1)
    price_old = trade['price']
    sl = trade['sl']
    tp = trade['tp']
    
    # 调整仓位到最小步长
    symbol_info = mt5.symbol_info(sym)
    if symbol_info is None:
        print(f"{sym} 找不到，跳过")
        continue
    volume_step = symbol_info.volume_step
    add_volume = round(add_volume / volume_step) * volume_step
    
    if add_volume < symbol_info.volume_min:
        add_volume = symbol_info.volume_min
    
    # 获取最新价格下单
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        print(f"{sym} 获取价格失败，跳过")
        continue
    
    if order_type == 'buy':
        mt5_order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
    else:
        mt5_order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    
    print(f"加仓 {sym}: {order_type.upper()} +{add_volume:.2f} 手")
    print(f"  价格: {price:.5f} 止损: {sl:.5f} 止盈: {tp:.5f}")
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": sym,
        "volume": float(add_volume),
        "type": mt5_order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 234001,
        "comment": "旺财72h加仓",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"  加仓失败: retcode={result.retcode}, {result.comment}")
    else:
        print(f"  加仓成功: 订单={result.order}")
        trades_added.append({
            "symbol": sym,
            "direction": trade['direction'],
            "order_type": order_type,
            "volume": float(add_volume),
            "price": float(price),
            "sl": sl,
            "tp": tp,
            "ticket": result.order,
            "commission": float(getattr(result, 'commission', 0.0)),
            "time": datetime.now().isoformat(),
            "type": "add"
        })

# 更新计划
plan['total_risk'] = new_total_risk
plan['risk_per_trade'] = new_total_risk / len(plan['trades'])
plan['trades'].extend([{**t, 'type': 'add'} for t in trades_added])

with open("72h_trades.json", "w") as f:
    json.dump(plan, f, indent=2)

print(f"\n=== 加仓完成 ===")
print(f"成功加仓: {len(trades_added)}/{len(plan['trades'])}")

# 查询最终持仓
positions_final = mt5.positions_get()
print(f"\n当前总持仓: {len(positions_final) if positions_final else 0} 笔")

total_profit = 0
for pos in positions_final:
    total_profit += pos.profit

account = mt5.account_info()
print(f"账户余额: {account.balance:.2f} USD")
print(f"账户净值: {account.equity:.2f} USD")
print(f"总浮盈: {total_profit:.2f} USD")

mt5.shutdown()
