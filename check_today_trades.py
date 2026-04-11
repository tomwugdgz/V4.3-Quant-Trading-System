import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

# 获取今日交易历史
history = mt5.history_deals_get(datetime(2026, 4, 10), datetime.now())

print("=" * 80)
print(f"今日交易历史（{len(history)} 笔）")
print("=" * 80)

if history:
    total_profit = 0
    for deal in history:
        direction = "BUY" if deal.type == 0 else "SELL"
        print(f"{deal.time}: {deal.symbol} {direction} {deal.volume:.2f} lots @ {deal.price:.5f}, profit: ${deal.profit:.2f}")
        total_profit += deal.profit
    
    print()
    print("=" * 80)
    print(f"总盈亏：${total_profit:.2f}")
    print("=" * 80)
else:
    print("今日无交易记录")

mt5.shutdown()
