"""
72 小时交易计划 - 每小时监控报告生成器
自动计算实时盈亏、交易费用、风险指标
"""

import MetaTrader5 as mt5
import json
from datetime import datetime
import os

def get_trading_costs(symbol, volume, direction, swap_long, swap_short):
    """计算交易费用（点差 + 隔夜利息）"""
    tick = mt5.symbol_info_tick(symbol)
    symbol_info = mt5.symbol_info(symbol)
    
    if not tick or not symbol_info:
        return 0, 0
    
    # 点差成本 (开仓时的隐性成本)
    spread_cost = (tick.ask - tick.bid) * volume * 100000
    
    # 隔夜利息 (swap) - 按天计算
    if direction == 'BUY':
        swap_rate = swap_long
    else:
        swap_rate = swap_short
    
    # swap 是每手的费用，按持有天数
    swap_cost = swap_rate * volume
    
    return spread_cost, swap_cost

def generate_report():
    """生成交易监控报告"""
    mt5.initialize()
    
    account = mt5.account_info()
    positions = mt5.positions_get()
    
    # 筛选 72h 计划的仓位
    plan_positions = []
    total_profit = 0
    total_swap = 0
    total_spread = 0
    
    report_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'account': {
            'balance': account.balance,
            'equity': account.equity,
            'margin_free': account.margin_free,
            'margin_level': account.margin_level
        },
        'positions': []
    }
    
    if positions:
        for pos in positions:
            if pos.comment == '72h_plan':
                direction = 'BUY' if pos.type == 0 else 'SELL'
                
                # 获取交易费用
                symbol_info = mt5.symbol_info(pos.symbol)
                spread_cost, swap_cost = get_trading_costs(
                    pos.symbol, 
                    pos.volume, 
                    direction,
                    symbol_info.swap_long,
                    symbol_info.swap_short
                )
                
                # 计算未实现盈亏
                profit = pos.profit
                swap = pos.swap
                
                # 计算盈亏百分比
                if direction == 'BUY':
                    price_change = (pos.price_current - pos.price_open) / pos.price_open * 100
                else:
                    price_change = (pos.price_open - pos.price_current) / pos.price_open * 100
                
                # 判断状态
                if profit >= pos.profit + 10:  # 接近止盈
                    status = '🟢 接近止盈'
                elif profit <= -10:  # 接近止损
                    status = '🔴 接近止损'
                elif profit > 0:
                    status = '🟢 盈利中'
                elif profit < 0:
                    status = '🔴 亏损中'
                else:
                    status = '⚪ 持平'
                
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
                    'status': status,
                    'distance_to_sl': abs(pos.price_current - pos.sl),
                    'distance_to_tp': abs(pos.price_current - pos.tp)
                }
                
                plan_positions.append(position_data)
                total_profit += profit
                total_swap += swap
                total_spread += spread_cost
    
    report_data['positions'] = plan_positions
    report_data['summary'] = {
        'total_profit': total_profit,
        'total_swap': total_swap,
        'total_spread': total_spread,
        'total_fees': total_spread + abs(total_swap),
        'net_profit': total_profit - total_spread,
        'positions_count': len(plan_positions),
        'winning_positions': len([p for p in plan_positions if p['profit'] > 0]),
        'losing_positions': len([p for p in plan_positions if p['profit'] < 0])
    }
    
    mt5.shutdown()
    return report_data

def format_report(data):
    """格式化报告为可读文本"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"📊 72 小时交易计划 - 监控报告")
    lines.append(f"⏰ 时间：{data['timestamp']}")
    lines.append("=" * 70)
    lines.append("")
    
    # 账户概览
    acc = data['account']
    lines.append("💰 账户状态")
    lines.append(f"  余额：${acc['balance']:.2f} USD")
    lines.append(f"  净值：${acc['equity']:.2f} USD")
    lines.append(f"  可用保证金：${acc['margin_free']:.2f} USD")
    lines.append(f"  保证金水平：{acc['margin_level']:.1f}%")
    lines.append("")
    
    # 汇总
    summary = data['summary']
    lines.append("📈 交易汇总")
    lines.append(f"  活跃仓位：{summary['positions_count']} 笔")
    lines.append(f"  盈利仓位：{summary['winning_positions']} 笔")
    lines.append(f"  亏损仓位：{summary['losing_positions']} 笔")
    lines.append(f"  浮动盈亏：${summary['total_profit']:.2f} USD")
    lines.append(f"  点差成本：${summary['total_spread']:.2f} USD")
    lines.append(f"  隔夜利息：${summary['total_swap']:.2f} USD")
    lines.append(f"  净盈亏：${summary['net_profit']:.2f} USD")
    lines.append("")
    
    # 详细仓位
    lines.append("🎯 仓位详情")
    lines.append("-" * 70)
    
    for pos in data['positions']:
        profit_color = "🟢" if pos['profit'] >= 0 else "🔴"
        lines.append(f"{pos['symbol']} {pos['direction']} {pos['volume']:.2f}手 {pos['status']}")
        lines.append(f"  入场：{pos['entry_price']:.5f} → 当前：{pos['current_price']:.5f} ({pos['price_change_pct']:+.3f}%)")
        lines.append(f"  止损：{pos['sl']:.5f} | 止盈：{pos['tp']:.5f}")
        lines.append(f"  距止损：{pos['distance_to_sl']:.5f} | 距止盈：{pos['distance_to_tp']:.5f}")
        lines.append(f"  盈亏：{profit_color} ${pos['profit']:.2f} | 利息：${pos['swap']:.2f} | 点差：${pos['spread_cost']:.2f}")
        lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)

if __name__ == '__main__':
    # 生成报告
    report = generate_report()
    
    # 保存 JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = f'C:/Users/DELL/.openclaw-autoclaw/workspace/trading/72h_reports/report_{timestamp}.json'
    
    os.makedirs('C:/Users/DELL/.openclaw-autoclaw/workspace/trading/72h_reports', exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印格式化报告
    formatted = format_report(report)
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(formatted)
    
    # 保存文本报告
    txt_path = f'C:/Users/DELL/.openclaw-autoclaw/workspace/trading/72h_reports/report_{timestamp}.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    print(f"\n📁 报告已保存:")
    print(f"  JSON: {json_path}")
    print(f"  TXT:  {txt_path}")
