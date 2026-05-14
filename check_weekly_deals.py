import MetaTrader5 as mt5
import datetime
import pandas as pd

mt5.initialize()

now = int(datetime.datetime.now().timestamp())
week_ago = now - 7*24*3600

history = mt5.history_deals_get(week_ago, now)

if history:
    print(f"本周交易笔数：{len(history)}")
    
    # 转换为 DataFrame
    deals = []
    for d in history:
        deals.append({
            'time': datetime.datetime.fromtimestamp(d.time),
            'symbol': d.symbol,
            'volume': d.volume,
            'price': d.price,
            'profit': d.profit,
            'magic': d.magic
        })
    
    df = pd.DataFrame(deals)
    
    # 按品种分组统计
    print("\n=== 按品种统计 ===")
    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        total_profit = symbol_df['profit'].sum()
        count = len(symbol_df)
        print(f"{symbol}: {count} 笔，总盈亏 ${total_profit:.2f}")
    
    # 总盈亏
    total_profit = df['profit'].sum()
    print(f"\n总盈亏：${total_profit:.2f}")
    
    # 最近 10 笔交易
    print("\n=== 最近 10 笔交易 ===")
    for _, row in df.tail(10).iterrows():
        print(f"{row['time']}: {row['symbol']} {row['volume']} @ {row['price']} profit=${row['profit']:.2f}")
else:
    print("无交易记录")
