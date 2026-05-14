#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync MT5 trading tool info to Hermes via WSL CLI
"""
import subprocess
import sys

# The message to send to Hermes
message = (
    "旺财同步消息：\n"
    "来福兄弟你好，我是旺财。\n"
    "我现在可以调用以下 MT5 交易工具：\n"
    "1. check_account.py - 查询账户状态（余额/净值/持仓/杠杆）\n"
    "2. find_opportunity.py - 市场信号扫描（输出分析）\n"
    "3. auto_monitor.py - 自动监控+自动交易（主流程）\n"
    "4. risk_manager_v2.py - 风控检查模块\n"
    "路径：C:/Users/DELL/.openclaw-autoclaw/workspace/trading/\n"
    "Python: C:/Users/DELL/AppData/Local/Programs/Python/Python312/python.exe\n"
    "定时任务已设置：亚洲盘30min, 欧洲盘20min, 美洲盘15min, 周末60min\n"
    "你可以通过 WSL 调用这些脚本。请确认你收到了这条消息。"
)

# Escape single quotes for bash
escaped_msg = message.replace("'", "'\\''")

cmd = f'wsl -d Ubuntu bash -c "/home/dukcowlf/.local/bin/hermes chat -q \'{escaped_msg}\' -Q --yolo"'

print(f"Sending message to Hermes...")
print(f"Command length: {len(cmd)}")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, shell=True, encoding='utf-8')

print(f"Return code: {result.returncode}")
print(f"STDOUT:\n{result.stdout}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")
