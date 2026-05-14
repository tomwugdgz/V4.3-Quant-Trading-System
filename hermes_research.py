#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询 Hermes 关于交易参数优化建议
"""
import urllib.request
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def call_hermes(query):
    """通过 Hermes Bridge v1 发送查询"""
    try:
        req = urllib.request.Request(
            'http://localhost:8642/chat',
            data=json.dumps({
                'prompt': query,
                'stream': False
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)}

# 查询 1: ATR 最优乘数
print("=== 查询 1: ATR 止损乘数研究 ===")
result1 = call_hermes(
    "我需要为外汇交易系统优化ATR止损乘数。请根据以下数据给出建议：\n"
    "当前参数: ATR周期=14, 乘数=2.0\n"
    "账户规模: ~$10,000 外汇交易\n"
    "品种: EURUSD(波动0.09%), GBPUSD(0.10%), AUDUSD(0.16%), USDJPY(0.25%), AUDJPY(0.27%)\n"
    "我的系统是趋势跟踪，请问ATR乘数应该是多少最合适？"
)
print(result1.get('response', result1.get('error', 'No response')))

# 查询 2: RSI 最优参数
print("\n=== 查询 2: RSI 超买超卖参数研究 ===")
result2 = call_hermes(
    "我的外汇趋势跟踪系统使用RSI作为择时指标。当前参数: RSI周期=14, 超买70, 超卖30。\n"
    "账户规模: ~$10,000, 目标: 最大化盈亏比同时控制频率。\n"
    "请问RSI超买超卖应该是多少最合适？"
)
print(result2.get('response', result2.get('error', 'No response')))

# 查询 3: ADX 阈值
print("\n=== 查询 3: ADX 阈值研究 ===")
result3 = call_hermes(
    "我的趋势跟踪系统使用ADX判断趋势强度。当前参数: ADX阈值=25。\n"
    "EURUSD H1 数据, ATR百分比约0.09-0.10%, ADX通常在15-40之间波动。\n"
    "请问ADX阈值设为多少最适合趋势确认？"
)
print(result3.get('response', result3.get('error', 'No response')))