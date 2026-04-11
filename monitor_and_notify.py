"""
72 小时交易监控 - 单次执行版本
生成报告并通过飞书发送
"""

import MetaTrader5 as mt5
import json
from datetime import datetime
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_trading_costs(symbol, volume, direction, swap_long, swap_short):
    """计算交易费用"""
    tick = mt5.symbol_info_tick(symbol)
    symbol_info = mt5.symbol_info(symbol)
    
    if not tick or not symbol_info:
        return 0, 0
    
    spread_cost = (tick.ask - tick.bid) * volume * 100000
    swap_rate = swap_long if direction == 'BUY' else swap_short
    swap_cost = swap_rate * volume
    
    return spread_cost, swap_cost

def generate_and_send_report():
    """生成报告并返回飞书消息"""
    mt5.initialize()
    
    account = mt5.account_info()
    positions = mt5.positions_get()
    
    plan_positions = []
    total_profit = 0
    total_swap = 0
    total_spread = 0
    
    if positions:
        for pos in positions:
            if pos.comment == '72h_plan':
                direction = 'BUY' if pos.type == 0 else 'SELL'
                symbol_info = mt5.symbol_info(pos.symbol)
                spread_cost, swap_cost = get_trading_costs(
                    pos.symbol, pos.volume, direction,
                    symbol_info.swap_long, symbol_info.swap_short
                )
                
                profit = pos.profit
                swap = pos.swap
                
                if direction == 'BUY':
                    price_change = (pos.price_current - pos.price_open) / pos.price_open * 100
                else:
                    price_change = (pos.price_open - pos.price_current) / pos.price_open * 100
                
                if profit > 0:
                    status = '🟢'
                elif profit < 0:
                    status = '🔴'
                else:
                    status = '⚪'
                
                position_data = {
                    'symbol': pos.symbol,
                    'direction': direction,
                    'volume': pos.volume,
                    'entry_price': pos.price_open,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': profit,
                    'swap': swap,
                    'price_change_pct': round(price_change, 3),
                    'spread_cost': spread_cost,
                    'status': status
                }
                
                plan_positions.append(position_data)
                total_profit += profit
                total_swap += swap
                total_spread += spread_cost
    
    mt5.shutdown()
    
    # 计算净盈亏
    net_profit = total_profit - total_spread
    
    if net_profit > 0:
        profit_emoji = "🟢"
        profit_text = f"+${net_profit:.2f}"
    elif net_profit < 0:
        profit_emoji = "🔴"
        profit_text = f"-${abs(net_profit):.2f}"
    else:
        profit_emoji = "⚪"
        profit_text = "$0.00"
    
    # 构建飞书消息
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    winning = len([p for p in plan_positions if p['profit'] > 0])
    losing = len([p for p in plan_positions if p['profit'] < 0])
    
    # 仓位详情
    positions_text = ""
    for pos in plan_positions:
        direction_arrow = "↑" if pos['direction'] == 'BUY' else "↓"
        profit_sign = "+" if pos['profit'] >= 0 else ""
        
        positions_text += f"""
{pos['symbol']} {direction_arrow} {pos['volume']:.2f}手 {pos['status']} {profit_sign}${pos['profit']:.2f}
  入场:{pos['entry_price']:.5f}→当前:{pos['current_price']:.5f} ({pos['price_change_pct']:+.3f}%)
  止损:{pos['sl']:.5f} | 止盈:{pos['tp']:.5f}"""
    
    message = f"""⏰ **{timestamp} | 72h 交易监控**

💰 账户状态
├ 余额：${account['balance']:.2f}
├ 净值：${account['equity']:.2f}
└ 保证金：{account['margin_level']:.1f}%

📊 交易汇总
├ 仓位：{len(plan_positions)}笔 (盈利{winning} | 亏损{losing})
├ 浮动盈亏：${total_profit:.2f}
├ 交易费用：${total_spread + abs(total_swap):.2f}
└ 净盈亏：{profit_emoji} {profit_text}
{positions_text}

━━━━━━━━━━━━━━━━
📈 下一报告：1 小时后
🎯 72 小时交易计划进行中"""

    return message

if __name__ == '__main__':
    message = generate_and_send_report()
    print(message)
    
    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('C:/Users/DELL/.openclaw-autoclaw/workspace/trading/72h_reports', exist_ok=True)
    
    with open(f'C:/Users/DELL/.openclaw-autoclaw/workspace/trading/72h_reports/report_{timestamp}.txt', 'w', encoding='utf-8') as f:
        f.write(message)
    
    print(f"\n📁 报告已保存：report_{timestamp}.txt")
