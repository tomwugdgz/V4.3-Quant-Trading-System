#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open(r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py', 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('ATR dynamic SL (2.5x)', 'atr_pips * 2.5' in content),
    ('JPY special handling', 'is_jpy' in content),
    ('JPY 25min SL floor', '25' in content and 'JPY' in content),
    ('Non-JPY 15min SL floor', 'atr_pips * 1.5' in content),
    ('Magic 240501', '240501' in content),
    ('Patrol Smart comment', 'Patrol Smart' in content),
]

print("=== patrol.py 版本验证 ===")
for name, ok in checks:
    status = "OK" if ok else "MISSING"
    print(f"  [{status}] {name}")

print()
print("=== SL 计算核心逻辑 ===")
lines = [l.strip() for l in content.split('\n') if 'sl_pips' in l.lower() and ('atr' in l.lower() or '25' in l or '15' in l)]
for l in lines[:8]:
    print(f"  {l}")

print()
# Check if cron is using correct file
import os
stat = os.stat(r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py')
print(f"patrol.py 最后修改: {stat.st_mtime} bytes={stat.st_size}")
