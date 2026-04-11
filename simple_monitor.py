# -*- coding: utf-8 -*-
"""
72 小时交易监控 - 单次执行版本
"""

import MetaTrader5 as mt5
from datetime import datetime
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def generate_report():
    mt5.initialize()
    
    account = mt5.account_info()
    positions = mt5.positions_get()
    
    plan_positions = []
    total_profit = 0
    total_spread = 0
    
    if positions:
        for pos in positions:
            if pos.comment == '72h_plan':
                direction = 'BUY' if pos.type == 0 else 'SELL'
                
                profit = pos.profit
                
                if direction == 'BUY':
                    price_change = (pos.price_current - pos.price_open) / pos.price_open * 100
                else:
                    price_change = (pos.price_open - pos.price_current) / pos.price_open * 100
                
                status = 'OK' if profit >= 0 else 'LOSS'
                
                position_data = {
                    'symbol': pos.symbol,
                    'direction': direction,
                    'volume': pos.volume,
                    'entry_price': pos.price_open,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': profit,
                    'price_change_pct': round(price_change, 3),
                    'status': status
                }
                
                plan_positions.append(position_data)
                total_profit += profit
    
    mt5.shutdown()
    return account, plan_positions, total_profit

if __name__ == '__main__':
    account, positions, total_profit = generate_report()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    winning = len([p for p in positions if p['profit'] > 0])
    losing = len([p for p in positions if p['profit'] < 0])
    net_profit = total_profit
    
    print(f"Time: {timestamp}")
    print(f"Balance: ${account.balance:.2f}")
    print(f"Equity: ${account.equity:.2f}")
    print(f"Positions: {len(positions)} (Win:{winning} Loss:{losing})")
    print(f"Total P/L: ${total_profit:.2f}")
    print()
    
    for pos in positions:
        arrow = "UP" if pos['direction'] == 'BUY' else "DOWN"
        sign = "+" if pos['profit'] >= 0 else ""
        print(f"{pos['symbol']} {arrow} {pos['volume']:.2f} lot {sign}${pos['profit']:.2f} ({pos['price_change_pct']:+.3f}%)")
        print(f"  Entry:{pos['entry_price']:.5f} Current:{pos['current_price']:.5f}")
        print(f"  SL:{pos['sl']:.5f} TP:{pos['tp']:.5f}")
        print()
