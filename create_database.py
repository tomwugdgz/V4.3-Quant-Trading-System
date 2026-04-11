# -*- coding: utf-8 -*-
"""
创建交易数据库
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "trading.db"

print("=" * 80)
print("创建交易数据库")
print(f"数据库路径：{db_path}")
print("=" * 80)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 1. 账户信息表
cursor.execute('''
CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY,
    login VARCHAR(20),
    server VARCHAR(50),
    balance DECIMAL(15,2),
    equity DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("[OK] 账户表 (accounts) 已创建")

# 2. 持仓记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    symbol VARCHAR(20),
    type VARCHAR(10),
    volume DECIMAL(10,2),
    entry_price DECIMAL(15,5),
    sl DECIMAL(15,5),
    tp DECIMAL(15,5),
    profit DECIMAL(15,2),
    open_time TIMESTAMP,
    close_time TIMESTAMP,
    status VARCHAR(20),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
)
''')
print("[OK] 持仓表 (positions) 已创建")

# 3. 交易信号表
cursor.execute('''
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20),
    direction VARCHAR(10),
    strength DECIMAL(10,5),
    timeframe VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("[OK] 信号表 (signals) 已创建")

# 4. K 线分析记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS kline_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20),
    timeframe VARCHAR(10),
    trend VARCHAR(50),
    rsi DECIMAL(10,2),
    macd_status VARCHAR(20),
    support DECIMAL(15,5),
    resistance DECIMAL(15,5),
    pattern VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("[OK] K 线分析表 (kline_analysis) 已创建")

# 5. 每日盈亏统计表
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_stats (
    date DATE PRIMARY KEY,
    opening_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    total_profit DECIMAL(15,2),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate DECIMAL(5,2),
    max_drawdown DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("[OK] 每日统计表 (daily_stats) 已创建")

# 6. 交易订单记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    symbol VARCHAR(20),
    type VARCHAR(10),
    volume DECIMAL(10,2),
    price DECIMAL(15,5),
    sl DECIMAL(15,5),
    tp DECIMAL(15,5),
    profit DECIMAL(15,2),
    comment VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("[OK] 订单表 (orders) 已创建")

conn.commit()
conn.close()

print("\n" + "=" * 80)
print(f"数据库创建成功：{db_path}")
print("=" * 80)
