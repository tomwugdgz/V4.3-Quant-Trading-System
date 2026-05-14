#!/usr/bin/env python3
import requests
import json

# DashScope API (阿里云) - 通义千问
url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
api_key = "sk-sp-2a54f93a8dc44eaba3707cfddc85fc2e"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "qwen-plus",
    "input": {
        "messages": [
            {
                "role": "system",
                "content": "你是来福，策略分析 AI，擅长深度研究和结构化输出。请用专业但易懂的语言分析 A 股市场。"
            },
            {
                "role": "user",
                "content": "请分析 A 股市场，给出周一 (2026-04-13) 可以关注的股票和板块，包括风险提示。周末消息面有：3 股被立案调查，48 股减持，9 股高管减持。"
            }
        ]
    },
    "parameters": {
        "result_format": "message"
    }
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    print("Status:", response.status_code)
    result = response.json()
    if "output" in result and "choices" in result["output"] and len(result["output"]["choices"]) > 0:
        print("\n=== 来福分析 ===\n")
        print(result["output"]["choices"][0]["message"]["content"])
    else:
        print("Response:", json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
