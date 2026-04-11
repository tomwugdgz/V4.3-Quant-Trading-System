"""
每小时监控报告 - 飞书推送
读取最新报告并发送到飞书群
"""

import json
import os
from datetime import datetime

def get_latest_report():
    """获取最新的监控报告"""
    report_dir = 'C:/Users/DELL/.openclaw-autoclaw/workspace/trading/72h_reports'
    
    if not os.path.exists(report_dir):
        return None
    
    files = [f for f in os.listdir(report_dir) if f.endswith('.json')]
    if not files:
        return None
    
    # 按时间排序，取最新
    files.sort(reverse=True)
    latest_file = os.path.join(report_dir, files[0])
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_feishu_message(data):
    """格式化为飞书消息"""
    timestamp = data['timestamp']
    summary = data['summary']
    account = data['account']
    
    # 盈亏状态
    if summary['net_profit'] > 0:
        profit_emoji = "🟢"
        profit_text = f"+${summary['net_profit']:.2f}"
    elif summary['net_profit'] < 0:
        profit_emoji = "🔴"
        profit_text = f"-${abs(summary['net_profit']):.2f}"
    else:
        profit_emoji = "⚪"
        profit_text = "$0.00"
    
    # 构建消息
    title = f"⏰ {timestamp} | 72h 交易监控"
    
    account_info = f"""💰 账户状态
├ 余额：${account['balance']:.2f}
├ 净值：${account['equity']:.2f}
└ 保证金：{account['margin_level']:.1f}%"""

    summary_info = f"""📊 交易汇总
├ 仓位：{summary['positions_count']}笔 (盈利{summary['winning_positions']} | 亏损{summary['losing_positions']})
├ 浮动盈亏：${summary['total_profit']:.2f}
├ 交易费用：${summary['total_fees']:.2f}
└ 净盈亏：{profit_emoji} {profit_text}"""

    # 仓位详情
    positions_text = "🎯 仓位详情\n"
    for pos in data['positions']:
        direction = "↑" if pos['direction'] == 'BUY' else "↓"
        profit_sign = "+" if pos['profit'] >= 0 else ""
        profit_color = "🟢" if pos['profit'] >= 0 else "🔴"
        
        positions_text += f"""
{pos['symbol']} {direction} {pos['volume']:.2f}手 {profit_color} {profit_sign}${pos['profit']:.2f}
  入场:{pos['entry_price']:.5f}→当前:{pos['current_price']:.5f} ({pos['price_change_pct']:+.3f}%)
  止损:{pos['sl']:.5f} | 止盈:{pos['tp']:.5f}"""

    message = f"""{title}

{account_info}

{summary_info}
{positions_text}

━━━━━━━━━━━━━━━━
📈 下一报告：1 小时后
🎯 72 小时交易计划进行中"""

    return message

if __name__ == '__main__':
    report = get_latest_report()
    
    if report:
        message = format_feishu_message(report)
        print(message)
        print("\n--- 消息已生成，准备发送 ---")
    else:
        print("❌ 未找到监控报告")
