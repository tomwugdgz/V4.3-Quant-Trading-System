import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('trading.db')
cursor = conn.cursor()

# 获取所有订单
cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
orders = cursor.fetchall()

print("=" * 80)
print("V1.0 系统交易记录（3 月份）")
print("=" * 80)

total_profit = 0
win_count = 0
loss_count = 0

for order in orders:
    order_id, mt5_id, symbol, order_type, volume, price, sl, tp, profit, comment, created_at = order
    print(f"\n订单 {order_id}:")
    print(f"  品种：{symbol} {order_type}")
    print(f"  手数：{volume}")
    print(f"  入场价：{price}")
    print(f"  止损/止盈：{sl} / {tp}")
    print(f"  盈亏：${profit}")
    print(f"  时间：{created_at}")
    
    if profit is not None:
        total_profit += profit
        if profit > 0:
            win_count += 1
        elif profit < 0:
            loss_count += 1

print("\n" + "=" * 80)
print("统计汇总")
print("=" * 80)
print(f"总订单数：{len(orders)}")
print(f"已平仓：{win_count + loss_count}")
print(f"盈利：{win_count} 单")
print(f"亏损：{loss_count} 单")
if win_count + loss_count > 0:
    win_rate = win_count / (win_count + loss_count) * 100
    print(f"胜率：{win_rate:.1f}%")
print(f"总盈亏：${total_profit:.2f}")

conn.close()
