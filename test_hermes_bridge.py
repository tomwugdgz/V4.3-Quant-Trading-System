#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import sys

query = sys.argv[1] if len(sys.argv) > 1 else "当前JPY的止损参数"

data = json.dumps({"query": query}).encode()
req = urllib.request.Request(
    "http://localhost:8642/query",
    data=data,
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = resp.read().decode()
        print(result)
except urllib.error.URLError as e:
    print(f"ERROR: {e}")
