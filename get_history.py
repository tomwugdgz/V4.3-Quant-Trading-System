#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""获取 MT5 历史订单记录"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import json

# 初始化 MT5
mt5.initialize()

# 获取 10 天前的时间（扩大范围确保覆盖）
now = datetime.now()
days_ago = now - timedelta(days=10)

# 获取历史订单
orders = mt5.orders_get(from_date=days_ago, to_date=now)
deals = mt5.history_deals_get(from_date=days_ago, to_date=now)

print("=" * 80)
print(f"MT5 交易历史记录 ({days_ago.strftime('%Y-%m-%d')} 至今)")
print("=" * 80)

print(f"\n当前时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"查询范围：{days_ago.strftime('%Y-%m-%d %H:%M:%S')} 至今")

# 订单统计
if orders:
    print(f"\n挂单记录：{len(orders)} 条")
else:
    print(f"\n挂单记录：0 条")

# 成交记录统计
if deals:
    print(f"成交记录：{len(deals)} 条")
    
    # 按品种分组统计
    symbol_stats = {}
    total_profit = 0
    total_deals = 0
    
    print("\n" + "=" * 80)
    print("成交明细")
    print("=" * 80)
    
    for deal in deals:
        symbol = deal.symbol
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'profit': 0,
                'deals': 0,
                'volume': 0,
                'trades': []
            }
        
        profit = deal.profit
        symbol_stats[symbol]['profit'] += profit
        symbol_stats[symbol]['deals'] += 1
        symbol_stats[symbol]['volume'] += deal.volume
        
        total_profit += profit
        total_deals += 1
        
        # 打印每笔成交
        deal_type = "BUY" if deal.entry_type == mt5.DEAL_ENTRY_IN else "SELL"
        if deal.entry_type == mt5.DEAL_ENTRY_OUT:
            deal_type = "CLOSE"
        
        print(f"\n{deal.time} | {symbol} | {deal_type} | {deal.volume}手 | 价格:{deal.price} | 盈亏:${profit:.2f}")
    
    # 汇总统计
    print("\n" + "=" * 80)
    print("品种汇总")
    print("=" * 80)
    
    for symbol, stats in sorted(symbol_stats.items()):
        print(f"\n{symbol}:")
        print(f"  成交笔数：{stats['deals']}")
        print(f"  总成交量：{stats['volume']:.2f}手")
        print(f"  总盈亏：${stats['profit']:.2f}")
    
    print("\n" + "=" * 80)
    print("总体统计")
    print("=" * 80)
    print(f"总成交笔数：{total_deals}")
    print(f"总盈亏：${total_profit:.2f}")
    print(f"平均单笔盈亏：${total_profit/total_deals:.2f}" if total_deals > 0 else "N/A")
    
else:
    print(f"成交记录：0 条")

mt5.shutdown()
