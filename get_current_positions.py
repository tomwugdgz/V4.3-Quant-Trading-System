#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5

mt5.initialize()

positions = mt5.positions_get()
print(f"当前总持仓: {len(positions) if positions else 0} 笔\n")

if positions:
    total_profit = 0
    for pos in positions:
        direction = "买入" if pos.type == 0 else "卖出"
        print(f"{pos.symbol}: {direction} {pos.volume} 手")
        print(f"  入场: {pos.price_open:.6f} | 当前: {pos.price_current:.6f}")
        print(f"  止损: {pos.sl:.6f} | 止盈: {pos.tp:.6f}")
        print(f"  浮盈: {pos.profit:.2f} USD\n")
        total_profit += pos.profit
    
    account = mt5.account_info()
    print("=== 汇总 ===")
    print(f"账户余额: {account.balance:.2f} USD")
    print(f"账户净值: {account.equity:.2f} USD")
    print(f"总浮盈: {total_profit:.2f} USD")

mt5.shutdown()
