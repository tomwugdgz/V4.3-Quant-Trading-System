import sqlite3
conn = sqlite3.connect('trading.db')
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# 获取每个表的结构
for table in tables:
    print(f"\n=== {table[0]} ===")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    for col in cursor.fetchall():
        print(col)
    
    # 获取前 10 条数据
    cursor.execute(f"SELECT * FROM {table[0]} ORDER BY rowid DESC LIMIT 10")
    rows = cursor.fetchall()
    print(f"Recent {len(rows)} records:")
    for row in rows:
        print(row)

conn.close()
