import json
from datetime import datetime
from pathlib import Path
import sys
import io

# 修复编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读取监控日志
LOG_FILE = Path("monitor_log.json")
with open(LOG_FILE, 'r', encoding='utf-8') as f:
    logs = json.load(f)

# 筛选今日数据
today = "2026-04-13"
today_logs = [log for log in logs if log['timestamp'].startswith(today)]

print("=" * 80)
print(f"今日交易数据汇总 - {today}")
print("=" * 80)

# 基础统计
print(f"\n📊 扫描统计")
print(f"扫描次数：{len(today_logs)}")

# 信号分析
strong_signals = [log for log in today_logs if log.get('best_strength', 0) >= 0.1]
medium_signals = [log for log in today_logs if 0.05 <= log.get('best_strength', 0) < 0.1]
weak_signals = [log for log in today_logs if 0 < log.get('best_strength', 0) < 0.05]
no_signals = [log for log in today_logs if log.get('best_strength', 0) == 0]

print(f"\n📈 信号分布")
print(f"强信号 (≥0.1%): {len(strong_signals)} 次")
print(f"中等信号 (≥0.05%): {len(medium_signals)} 次")
print(f"弱信号 (<0.05%): {len(weak_signals)} 次")
print(f"无信号：{len(no_signals)} 次")

# 最强信号
if strong_signals:
    best = max(strong_signals, key=lambda x: x.get('best_strength', 0))
    print(f"\n🎯 最强信号")
    print(f"品种：{best.get('best_signal')}")
    print(f"强度：{best.get('best_strength', 0):.3f}%")
    print(f"时间：{best.get('timestamp')}")

# 持仓变化
positions_changes = [log for log in today_logs if log.get('positions_count', 0) > 0]
print(f"\n💼 持仓情况")
print(f"有持仓的扫描次数：{len(positions_changes)}")
if positions_changes:
    current_positions = max([log.get('positions_count', 0) for log in positions_changes])
    print(f"最大持仓数：{current_positions}")

# 账户余额变化
balances = [log.get('account_balance', 0) for log in today_logs if log.get('account_balance')]
if balances:
    print(f"\n💰 账户变化")
    print(f"期初余额：${balances[0]:.2f}")
    print(f"期末余额：${balances[-1]:.2f}")
    print(f"余额变化：${balances[-1] - balances[0]:.2f}")

# 决策统计
decisions_count = sum([len(log.get('decisions', [])) for log in today_logs])
closed_count = sum([log.get('closed_count', 0) for log in today_logs])
print(f"\n📋 决策统计")
print(f"决策次数：{decisions_count}")
print(f"平仓次数：{closed_count}")

# 时间分布
print(f"\n⏰ 时间分布")
hours = {}
for log in today_logs:
    hour = log['timestamp'].split('T')[1].split(':')[0]
    hours[hour] = hours.get(hour, 0) + 1

for hour in sorted(hours.keys()):
    count = hours[hour]
    bar = "█" * (count // 2)
    print(f"{hour}:00 - {count:2d} 次 {bar}")

print("\n" + "=" * 80)
