#!/usr/bin/env python3
import urllib.request
import json

query = "用一句话回答：ATR乘数2.0对外汇趋势跟踪交易是否合适？"
req = urllib.request.Request(
    'http://127.0.0.1:8642/chat',
    data=json.dumps({'prompt': query, 'stream': False}).encode('utf-8'),
    headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print("Hermes Response:", result.get('response', result))
except Exception as e:
    print("Error:", e)