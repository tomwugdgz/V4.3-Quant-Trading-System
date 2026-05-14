import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

# 获取最近 7 天的成交记录
end_time = datetime.now()
start_time = datetime(2026, 4, 14)  # 从 4 月 14 日开始

history = mt5.history_deals_get(start_time, end_time)

if history:
    print(f"总成交记录：{len(history)} 条\n")
    print("=" * 80)
    
    # 按品种分组统计
    by_symbol = {}
    for deal in history:
        symbol = deal.symbol
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(deal)
    
    for symbol, deals in sorted(by_symbol.items()):
        print(f"\n{symbol}:")
        total_profit = 0
        for deal in deals:
            deal_time = datetime.fromtimestamp(deal.time)
            direction = "BUY" if deal.type == 0 else "SELL"
            profit = deal.profit
            total_profit += profit
            print(f"  {deal_time.strftime('%Y-%m-%d %H:%M')}  {direction} {deal.volume:.2f} @ {deal.price:.5f}  盈亏：${profit:.2f}")
        print(f"  → {symbol} 小计：${total_profit:.2f}")
    
    # 总盈亏
    total = sum(d.profit for d in history)
    print(f"\n{'=' * 80}")
    print(f"总盈亏：${total:.2f} ({len(history)} 笔成交)")
else:
    print("无成交记录")

mt5.shutdown()
