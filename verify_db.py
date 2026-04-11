import sqlite3

conn = sqlite3.connect('C:\\Users\\DELL\\.openclaw-autoclaw\\workspace\\trading\\trading.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print("Database Tables:")
for t in tables:
    print(f"  - {t[0]}")
conn.close()
