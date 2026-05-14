#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Send message to Hermes gateway via WSL"""
import requests
import json

# The gateway is at WSL IP:8644
# Try to find the correct endpoint
wsl_ip = "172.23.137.223"

message = {
    "message": "来自旺财的同步消息：\n我现在可以调用MT5交易工具，包括check_account.py、find_opportunity.py、auto_monitor.py、risk_manager_v2.py。定时任务已设置完成（亚洲盘30min/欧洲盘20min/美洲盘15min）。来福兄弟你收到后，确认一下。"
}

# Try POST to various endpoints
endpoints = ["/v1/chat/completions", "/chat", "/api/chat", "/message", "/send"]

for ep in endpoints:
    url = f"http://{wsl_ip}:8644{ep}"
    try:
        r = requests.post(url, json=message, timeout=10)
        print(f"{ep}: {r.status_code}")
        if r.status_code == 200:
            print(r.text[:500])
            break
    except Exception as e:
        print(f"{ep}: {type(e).__name__}")

# If none work, try the stdin approach with a file
print("\nTrying stdin approach...")
import subprocess
msg_file = "/mnt/c/Users/DELL/.openclaw-autoclaw/workspace/trading/hermes_msg.txt"
cmd = f"echo '旺财同步：MT5工具可用，定时任务已设置。请确认。' | /home/dukcowlf/.local/bin/hermes chat -Q --yolo"
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "bash", "-c", cmd],
    capture_output=True, text=True, timeout=60, encoding='utf-8'
)
print(f"Return: {result.returncode}")
print(f"Output: {result.stdout[-500:] if result.stdout else 'none'}")
if result.stderr:
    print(f"Stderr: {result.stderr[-200:]}")
