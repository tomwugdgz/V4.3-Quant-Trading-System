import json
from datetime import datetime

with open('monitor_log.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

print("=" * 80)
print(f"监控日志分析（共 {len(logs)} 条记录）")
print("=" * 80)

# 统计信号强度分布
strong_signals = []  # >= 0.1%
medium_signals = []  # >= 0.05%
weak_signals = []    # < 0.05%

for log in logs:
    strength = log.get('best_strength', 0)
    if strength >= 0.1:
        strong_signals.append(log)
    elif strength >= 0.05:
        medium_signals.append(log)
    elif strength > 0:
        weak_signals.append(log)

print(f"\n信号强度分布:")
print(f"  强信号 (≥0.1%): {len(strong_signals)} 次 ({len(strong_signals)/len(logs)*100:.1f}%)")
print(f"  中等信号 (≥0.05%): {len(medium_signals)} 次 ({len(medium_signals)/len(logs)*100:.1f}%)")
print(f"  弱信号 (<0.05%): {len(weak_signals)} 次 ({len(weak_signals)/len(logs)*100:.1f}%)")
print(f"  无信号：{len(logs) - len(strong_signals) - len(medium_signals) - len(weak_signals)} 次")

# 如果有强信号，显示详情
if strong_signals:
    print(f"\n强信号详情（共 {len(strong_signals)} 次）:")
    for log in strong_signals[:10]:  # 显示前 10 次
        print(f"  {log['timestamp']}: {log['best_signal']} {log['best_strength']:.4f}%")

# 统计时间跨度
if logs:
    first_time = logs[0]['timestamp']
    last_time = logs[-1]['timestamp']
    print(f"\n时间跨度：{first_time} 至 {last_time}")
