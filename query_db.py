#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('C:/Users/DELL/.openclaw-autoclaw/workspace/trading/trading.db')
cursor = conn.cursor()

# 查询 orders 表
print("=" * 80)
print("ORDERS 表")
print("=" * 80)
try:
    cursor.execute("SELECT * FROM orders ORDER BY rowid DESC LIMIT 20")
    rows = cursor.fetchall()
    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    print("列名:", columns)
    print(f"\n最近 20 条记录:")
    for row in rows:
        print(dict(zip(columns, row)))
except Exception as e:
    print(f"查询失败：{e}")

# 查询 daily_stats 表
print("\n" + "=" * 80)
print("DAILY_STATS 表")
print("=" * 80)
try:
    cursor.execute("SELECT * FROM daily_stats ORDER BY date DESC LIMIT 10")
    rows = cursor.fetchall()
    cursor.execute("PRAGMA table_info(daily_stats)")
    columns = [col[1] for col in cursor.fetchall()]
    print("列名:", columns)
    print(f"\n最近 10 条记录:")
    for row in rows:
        print(dict(zip(columns, row)))
except Exception as e:
    print(f"查询失败：{e}")

# 查询 positions 表
print("\n" + "=" * 80)
print("POSITIONS 表")
print("=" * 80)
try:
    cursor.execute("SELECT * FROM positions ORDER BY rowid DESC LIMIT 20")
    rows = cursor.fetchall()
    cursor.execute("PRAGMA table_info(positions)")
    columns = [col[1] for col in cursor.fetchall()]
    print("列名:", columns)
    print(f"\n最近 20 条记录:")
    for row in rows:
        print(dict(zip(columns, row)))
except Exception as e:
    print(f"查询失败：{e}")

conn.close()
