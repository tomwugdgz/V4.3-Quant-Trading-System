#!/usr/bin/env python3
"""
patrol_auto.py — 自动巡查 + 记录
每次运行执行一次完整巡查，有信号则开仓，所有结果记录到日志
供 Windows Task Scheduler 每30分钟调用一次
"""
import sys
import io
import os
import json
import subprocess
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PYTHON = r"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
PATROL_SCRIPT = os.path.join(os.path.dirname(__file__), "patrol.py")
LOG_DIR = r"D:\LLM-Wiki\trading\logs"
TRADE_LOG = os.path.join(LOG_DIR, f"trade_log_{datetime.now().strftime('%Y-%m-%d')}.json")
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_patrol():
    """执行 patrol.py，返回原始输出"""
    log("执行 patrol.py...")
    try:
        result = subprocess.run(
            [PYTHON, PATROL_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"ERROR: {e}"

def parse_output(output):
    """解析 patrol.py 输出"""
    import re
    balance = equity = pos_count = None
    trade_executed = False
    signal_info = None
    lines = output.split('\n')

    for line in lines:
        line = line.strip()
        if '余额=' in line:
            try:
                balance = float(line.split('余额=$')[-1].split()[0])
            except: pass
        if '净值=' in line:
            try:
                equity = float(line.split('净值=$')[-1].split()[0])
            except: pass
        if '持仓:' in line:
            m = re.search(r'持仓:?\s*(\d+)', line)
            if m:
                pos_count = int(m.group(1))
        if '强信号' in line:
            signal_info = line
        if '成功开仓' in line:
            trade_executed = True

    return {
        'balance': balance,
        'equity': equity,
        'pos_count': pos_count,
        'trade_executed': trade_executed,
        'signal': signal_info
    }

def load_trade_log():
    """加载当日 trade log"""
    if os.path.exists(TRADE_LOG):
        try:
            with open(TRADE_LOG, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except: pass
    return {'date': datetime.now().strftime('%Y-%m-%d'), 'trades': []}

def save_trade_log(data):
    """保存当日 trade log"""
    with open(TRADE_LOG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def main():
    log("=" * 50)
    log("PATROL AUTO — 自动巡查开始")
    log("=" * 50)

    # 执行 patrol
    output = run_patrol()

    # 解析
    result = parse_output(output)

    # 打印输出摘要
    for line in output.split('\n'):
        if line.strip():
            log(f"  {line.strip()}")

    # 记录到 trade log
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'balance': result['balance'],
        'equity': result['equity'],
        'positions': result['pos_count'],
        'trade_executed': result['trade_executed'],
        'signal': result['signal'],
        'raw_snippet': output[-500:] if len(output) > 500 else output
    }

    trade_log = load_trade_log()
    trade_log['trades'].append(log_entry)
    save_trade_log(trade_log)

    # 摘要
    event = '交易执行' if result['trade_executed'] else ('有信号' if result['signal'] else '无信号')
    log(f"[{event}] 持仓:{result['pos_count']}/5 余额:{result['balance']} 净值:{result['equity']}")
    log(f"Trade log 已保存到: {TRADE_LOG}")
    log("=" * 50)

if __name__ == "__main__":
    main()
