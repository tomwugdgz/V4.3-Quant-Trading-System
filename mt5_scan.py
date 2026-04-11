import MetaTrader5 as mt5
import sys
from datetime import datetime

# 初始化 MT5
if not mt5.initialize():
    print("MT5 初始化失败")
    sys.exit(1)

# 获取主要货币对行情
symbols = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]

print("=" * 60)
print(f"MT5 实时行情扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

for symbol in symbols:
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        # 获取 1 小时 K 线
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 20)
        if len(rates) > 0:
            current_price = tick.last
            spread = (tick.ask - tick.bid) * 10000  # 点差
            
            # 简单趋势判断
            if len(rates) >= 5:
                ma_short = sum(r['close'] for r in rates[-5:]) / 5
                ma_long = sum(r['close'] for r in rates[-10:]) / 10 if len(rates) >= 10 else ma_short
                
                trend = "UP" if current_price > ma_short else "DOWN"
                signal = "BUY" if current_price > ma_short else "SELL"
                
                print(f"\n{symbol}:")
                print(f"  价格：{current_price:.5f}")
                print(f"  点差：{spread:.1f} 点")
                print(f"  趋势：{trend}")
                print(f"  信号：{signal}")
    else:
        print(f"{symbol}: 无数据")

# 获取账户信息
account = mt5.account_info()
if account:
    print("\n" + "=" * 60)
    print("账户信息:")
    print(f"  余额：${account.balance:.2f}")
    print(f"  净值：${account.equity:.2f}")
    print(f"  可用保证金：${account.margin_free:.2f}")
    print(f"  杠杆：1:{account.leverage}")
    
    # 计算风险
    risk_per_trade = account.balance * 0.005  # 0.5%
    print(f"  单笔风险 (0.5%): ${risk_per_trade:.2f}")

mt5.shutdown()
