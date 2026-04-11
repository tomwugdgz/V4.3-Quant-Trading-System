#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查持仓时长
"""

import MetaTrader5 as mt5
from datetime import datetime
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

account = mt5.account_info()
positions = mt5.positions_get()

print("=" * 90)
print("📊 持仓时长分析")
print("=" * 90)

print(f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"账户：{account.login} | 余额：${account.balance:.2f} | 持仓：{len(positions) if positions else 0} 单")

if not positions:
    print("\n无持仓")
    mt5.shutdown()
    exit(0)

print("\n" + "=" * 90)
print("持仓详情")
print("=" * 90)

total_profit = 0
total_duration_hours = 0

for pos in positions:
    symbol = pos.symbol
    direction = "BUY" if pos.type == 0 else "SELL"
    volume = pos.volume
    entry_price = pos.price_open
    current_price = pos.price_current
    profit = pos.profit
    sl = pos.sl
    tp = pos.tp
    
    # 开仓时间
    open_time = datetime.fromtimestamp(pos.time)
    now = datetime.now()
    duration = now - open_time
    
    # 计算时长
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    
    # 计算 pips
    pip_mult = 100 if 'JPY' in symbol else 10000
    if direction == "BUY":
        profit_pips = (current_price - entry_price) * pip_mult
    else:
        profit_pips = (entry_price - current_price) * pip_mult
    
    total_profit += profit
    total_duration_hours += hours
    
    print(f"\n{symbol} {direction} {volume}手")
    print(f"  入场价：{entry_price:.5f}")
    print(f"  当前价：{current_price:.5f}")
    print(f"  止损：{sl:.5f} | 止盈：{tp:.5f}")
    print(f"  盈亏：{profit_pips:+.1f} pips (${profit:+.2f})")
    print(f"  开仓时间：{open_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  持仓时长：{hours}小时 {minutes}分钟")
    
    # 持仓时长评估
    if hours < 1:
        print(f"  状态：⏱️ 新开仓 (<1 小时)")
    elif hours < 4:
        print(f"  状态：🕐 短线持仓 ({hours}小时)")
    elif hours < 12:
        print(f"  状态：🕓 中线持仓 ({hours}小时)")
    elif hours < 24:
        print(f"  状态：🕘 长线持仓 ({hours}小时)")
    else:
        days = hours // 24
        print(f"  状态：📅 隔夜持仓 ({days}天 {hours%24}小时)")
    
    # 预期持有时间 (基于策略)
    expected_hours = 4  # 预期 4-24 小时
    if hours < expected_hours:
        remaining = expected_hours - hours
        print(f"  预期：还需持有约 {remaining} 小时 (目标 4-24 小时)")
    else:
        print(f"  预期：已达到最短持有时间，可考虑止盈")

print("\n" + "=" * 90)
print("汇总统计")
print("=" * 90)
print(f"  总持仓数：{len(positions)} 单")
print(f"  平均持仓时长：{total_duration_hours / len(positions):.1f} 小时")
print(f"  总浮盈：${total_profit:+.2f} ({total_profit/account.balance*100:+.2f}%)")
durations = [datetime.now() - datetime.fromtimestamp(p.time) for p in positions]
min_dur = min(durations)
max_dur = max(durations)
print(f"  最短持仓：{int(min_dur.total_seconds() // 60)}分钟")
print(f"  最长持仓：{int(max_dur.total_seconds() // 60)}分钟")

print("\n" + "=" * 90)
print("持仓时长建议")
print("=" * 90)
print("\nMP5 策略建议持有时间：4-24 小时")
print("  - <4 小时：给仓位一些时间波动")
print("  - 4-12 小时：观察盈利情况")
print("  - 12-24 小时：如盈利达标可平仓")
print("  - >24 小时：如未止盈，考虑移动止损")

print("\n当前建议:")
for pos in positions:
    duration = datetime.now() - datetime.fromtimestamp(pos.time)
    hours = int(duration.total_seconds() // 3600)
    symbol = pos.symbol
    profit = pos.profit
    
    if hours < 4:
        print(f"  ⏱️ {symbol}: 持仓{hours}小时，建议继续持有")
    elif profit > 0:
        print(f"  ✅ {symbol}: 持仓{hours}小时且盈利，可考虑平仓或移动止损")
    else:
        print(f"  ⚠️ {symbol}: 持仓{hours}小时仍亏损，接近止损可准备平仓")

print("=" * 90)

mt5.shutdown()
