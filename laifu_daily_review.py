#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

# DashScope API (阿里云) - 通义千问
url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
api_key = "sk-sp-2a54f93a8dc44eaba3707cfddc85fc2e"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 今日交易数据
today_data = """
## 2026-04-15 交易数据

### 账户概览
- 账户余额：$10,060.20
- 账户净值：$10,059.59
- 可用保证金：$8,413.76
- 保证金水平：607.66%
- 实际杠杆：0.82x
- 杠杆设置：1:5

### 今日盈亏
- 已实现盈亏：+$141.41
- 当前浮亏：-$0.61
- 净盈利：+$140.80
- 交易笔数：120 笔

### 当前持仓 (2 单)
1. AUDUSD BUY 0.04 @ 0.71411, 浮亏 -$0.16
2. USDCHF BUY 0.05 @ 0.78228, 浮亏 -$0.45

### 最佳盈利交易
1. USDCHF SELL 0.10 @ 0.78988 -> +$42.92
2. USDCHF BUY 0.10 @ 0.78629 -> +$33.96
3. USDCHF BUY 0.10 @ 0.78634 -> +$27.72
4. USDCHF BUY 0.05 @ 0.78069 -> +$18.25
5. USDCAD BUY 0.10 @ 1.38096 -> +$8.54

### 亏损交易
1. USDCHF SELL 0.10 @ 0.78701 -> -$17.41
2. USDCHF SELL 0.10 @ 0.78677 -> -$17.29
3. AUDUSD SELL 0.04 @ 0.71091 -> -$11.48
4. NZDUSD SELL 0.04 @ 0.58972 -> -$7.60
5. AUDUSD BUY 0.04 @ 0.71376 -> -$8.48

### 基线测试进度
- 测试期：4/13-4/22 (第 3 天/共 10 天)
- 扫描频率：15 分钟/次
- 信号阈值：>=0.1% 自动执行
- 当前状态：空仓等待强信号
- 持仓上限：5 单

### 交易品种分布
- USDCHF: 主要盈利来源 (+$100+)
- USDCAD: +$20+
- NZDUSD: +$10+
- GBPUSD: +$6.00
- EURUSD: +$5.45
- AUDUSD: 小幅波动
"""

# 分析提示词
prompt = f"""
你是一个专业的量化交易分析师 (来福)。请根据以下交易数据，对今日 (2026-04-15) 的交易操作进行深度复盘分析。

{today_data}

请从以下维度进行分析：

1. 整体表现评估 - 今日盈利状况如何？胜率同盈亏比如何？风险控制是否到位？
2. 交易策略分析 - 边个品种表现最好？点解？入场时机选择如何？止损止盈设置是否合理？
3. 风险指标评估 - 保证金水平是否安全？实际杠杆是否合理？持仓集中度如何？
4. 问题识别 - 今日有咩操作需要改进？有咩重复性错误？有咩可以优化嘅地方？
5. 改进建议 - 听日应该重点关注咩？策略上需要调整咩？基线测试期 (4/13-4/22) 应该注意咩？

请用粤语 (广东话) 回复，保持专业但通俗易懂，像朋友倾计咁。
"""

payload = {
    "model": "qwen-plus",
    "input": {
        "messages": [
            {
                "role": "system",
                "content": "你是来福，策略分析 AI，擅长深度研究和结构化输出。请用粤语 (广东话) 进行专业但易懂的交易分析。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    },
    "parameters": {
        "result_format": "message",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}

try:
    print("[INFO] 正在调用来福 AI 进行分析...")
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    print(f"[INFO] 状态码：{response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if "output" in result and "choices" in result["output"] and len(result["output"]["choices"]) > 0:
            analysis = result["output"]["choices"][0]["message"]["content"]
            print("\n" + "="*60)
            print("[REPORT] 来福 AI 复盘分析报告")
            print("="*60)
            print(analysis)
            print("="*60)
        else:
            print("[ERROR] 响应格式异常:", json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"[ERROR] {response.text}")
        
except Exception as e:
    print(f"[ERROR] 调用失败：{e}")
