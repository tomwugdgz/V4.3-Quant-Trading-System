#!/usr/bin/env python3
import requests
import json

url = "http://localhost:8644/v1/chat/completions"
payload = {
    "model": "glm-5",
    "messages": [
        {
            "role": "user",
            "content": "请分析 A 股市场，给出周一可以关注的股票和板块，包括风险提示"
        }
    ]
}

try:
    response = requests.post(url, json=payload, timeout=60)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
