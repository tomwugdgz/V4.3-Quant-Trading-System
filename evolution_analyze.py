#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import json
from datetime import datetime

# 初始化 MT5
if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

# 读取当前交易计划
with open("72h_trades.json", "r") as f:
    plan = json.load(f)

print("=== 当前交易分析 ===\n")

# 获取当前价格，分析各品种走势
total_profit = 0
total_risk = 0
analysis = []

for trade in plan['trades']:
    sym = trade['symbol']
    direction = trade['direction']
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        continue
    
    symbol_info = mt5.symbol_info(sym)
    current_price = tick.ask if trade['order_type'] == 'buy' else tick.bid
    
    # 计算当前盈亏
    if trade['order_type'] == 'buy':
        price_diff = current_price - trade['price']
    else:
        price_diff = trade['price'] - current_price
    
    point = symbol_info.point
    digits = symbol_info.digits
    tick_value = symbol_info.trade_tick_value
    ticks_diff = price_diff / point
    profit = ticks_diff * tick_value * trade['volume']
    
    # 计算到止损还有多少空间
    if trade['order_type'] == 'buy':
        stop_dist = (current_price - trade['sl']) / point
    else:
        stop_dist = (trade['sl'] - current_price) / point
    
    analysis.append({
        **trade,
        'current_price': float(current_price),
        'profit': float(profit),
        'stop_dist_pips': float(stop_dist)
    })
    
    total_profit += profit
    # 计算潜在风险
    if trade['order_type'] == 'buy':
                risk_pips = (trade['price'] - trade['sl']) / point
    else:
        risk_pips = (trade['sl'] - trade['price']) / point
    risk = risk_pips * tick_value * trade['volume']
    total_risk += risk

print(f"总计划风险: ${total_risk:.2f}")
print(f"当前总浮盈: ${total_profit:.2f}\n")

print("=== 各品种详细分析 ===\n")

for a in analysis:
    direction_str = "买入" if a['order_type'] == 'buy' else "卖出"
    print(f"{a['symbol']} {direction_str} {a['volume']:.2f} 手")
    print(f"  入场: {a['price']:.5f} | 当前: {a['current_price']:.5f}")
    print(f"  止损: {a['sl']:.5f} | 止盈: {a['tp']:.5f}")
    print(f"  浮盈: ${a['profit']:.2f} | 到止损还有: {a['stop_dist_pips']:.0f} 点\n")

# 进化建议
print("=== 进化建议 ===\n")

# 统计
win_trades = [a for a in analysis if a['profit'] > 0]
lose_trades = [a for a in analysis if a['profit'] <= 0]
print(f"盈利单: {len(win_trades)}, 亏损单: {len(lose_trades)}")

# 建议
print("\n基于当前战况，进化方向:")

# 检查是否有可以移动止损的
print("\n1. 移动止损进化 - 盈利单子移到保本:")
for a in analysis:
    if a['profit'] > 0 and a['profit'] > (total_risk / len(analysis)) * 0.5:
        # 盈利达到 0.5R，移动止损到入场价
        print(f"   {a['symbol']}: 当前浮盈 ${a['profit']:.2f}，可以移动止损到入场价 ${a['price']}")

# 检查是否有亏损太大接近止损的
print("\n2. 止损检查:")
for a in analysis:
    if a['stop_dist_pips'] < 50:
        print(f"   {a['symbol']}: 仅剩 {a['stop_dist_pips']:.0f} 点到止损，接近出局")

# 策略进化建议
print("\n3. 策略进化:")
print("   - 当前策略: H4均线 + ATR风控，本身没问题")
print("   - 可以进化: 添加过滤条件，只做趋势方向和大级别趋势一致的机会")
print("   - 可以进化: 盈利后追踪止损，让利润奔跑")
print("   - 可以进化: 浮亏达到一定比例提前截断，减少止损冲击")

# 输出到文件
output = {
    'analysis_time': datetime.now().isoformat(),
    'total_risk': float(total_risk),
    'total_profit': float(total_profit),
    'trades': analysis,
    'win_count': len(win_trades),
    'lose_count': len(lose_trades)
}

with open("evolution_analysis.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n分析完成，结果保存到 evolution_analysis.json")

mt5.shutdown()
