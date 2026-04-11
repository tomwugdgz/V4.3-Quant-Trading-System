import MetaTrader5 as mt5
from datetime import datetime, timedelta

mt5.initialize()

# 获取今日交易历史
start_time = datetime(2026, 4, 10, 0, 0, 0)
end_time = datetime.now()

history = mt5.history_deals_get(start_time, end_time)

print("=" * 80)
print(f"今日交易历史（{len(history)} 笔）")
print("=" * 80)

if history:
    total_profit = 0
    total_volume = 0
    symbols = {}
    
    for deal in history:
        direction = "BUY" if deal.type == 0 else "SELL"
        print(f"{deal.time}: {deal.symbol} {direction} {deal.volume:.2f} lots @ {deal.price:.5f}, profit: ${deal.profit:.2f}")
        total_profit += deal.profit
        total_volume += deal.volume
        
        # 统计每个品种
        if deal.symbol not in symbols:
            symbols[deal.symbol] = {"buy": 0, "sell": 0, "profit": 0}
        if deal.type == 0:
            symbols[deal.symbol]["buy"] += 1
        else:
            symbols[deal.symbol]["sell"] += 1
        symbols[deal.symbol]["profit"] += deal.profit
    
    print()
    print("=" * 80)
    print(f"总交易笔数：{len(history)}")
    print(f"总交易量：{total_volume:.2f} lots")
    print(f"总盈亏：${total_profit:.2f}")
    print("=" * 80)
    
    print()
    print("按品种统计:")
    print("-" * 80)
    print(f"{'品种':<10} {'BUY':<8} {'SELL':<8} {'盈亏':<10}")
    print("-" * 80)
    for symbol, data in symbols.items():
        print(f"{symbol:<10} {data['buy']:<8} {data['sell']:<8} ${data['profit']:+.2f}")
else:
    print("今日无交易记录")

mt5.shutdown()
