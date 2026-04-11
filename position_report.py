import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

account = mt5.account_info()
positions = mt5.positions_get()

print("=" * 80)
print("WEEKEND TRADING PORTFOLIO REPORT")
print("=" * 80)
print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Account: {account.login} | Balance: ${account.balance:.2f} | Equity: ${account.equity:.2f}")

# 持仓统计
total_profit = 0
positions_count = 0

print("\n" + "=" * 80)
print("OPEN POSITIONS")
print("=" * 80)

if positions:
    for pos in positions:
        positions_count += 1
        total_profit += pos.profit
        
        current_pnl_pct = ((pos.price_current - pos.price_open) / pos.price_open) * 100 if pos.type == 0 else ((pos.price_open - pos.price_current) / pos.price_open) * 100
        
        print(f"\n[Position #{positions_count}]")
        print(f"  Symbol: {pos.symbol}")
        print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"  Volume: {pos.volume} lots")
        print(f"  Entry: ${pos.price_open:.2f}")
        print(f"  Current: ${pos.price_current:.2f}")
        print(f"  P/L: ${pos.profit:.2f} ({current_pnl_pct:+.2f}%)")
        print(f"  Stop Loss: ${pos.sl:.2f}")
        print(f"  Take Profit: ${pos.tp:.2f}")
        
        # 距离分析
        if pos.type == 0:  # BUY
            dist_sl_pct = ((pos.price_current - pos.sl) / pos.price_open) * 100
            dist_tp_pct = ((pos.tp - pos.price_current) / pos.price_open) * 100
        else:  # SELL
            dist_sl_pct = ((pos.sl - pos.price_current) / pos.price_open) * 100
            dist_tp_pct = ((pos.price_current - pos.tp) / pos.price_open) * 100
        
        print(f"  Distance to SL: {dist_sl_pct:.1f}%")
        print(f"  Distance to TP: {dist_tp_pct:.1f}%")
        
        # 策略建议
        if pos.profit > 0:
            print(f"  Status: [PROFIT] - Consider trailing stop if >50% to TP")
        else:
            print(f"  Status: [DRAWNDOWN] - Monitor closely, respect SL")
else:
    print("\nNo open positions")

# 市场分析
print("\n" + "=" * 80)
print("MARKET STATUS")
print("=" * 80)
print("Forex Market: CLOSED (Weekend)")
print("Gold/Silver: CLOSED (Weekend)")
print("Crypto: OPEN (24/7)")
print("\nCurrent Focus: BTCUSD (only liquid crypto opportunity)")

# 交易总结
print("\n" + "=" * 80)
print("TRADING SUMMARY")
print("=" * 80)
print(f"Total Positions: {positions_count}")
print(f"Total Floating P/L: ${total_profit:.2f}")
print(f"Return on Account: {(total_profit/account.balance)*100:+.2f}%")

if positions_count > 0:
    print(f"\nStrategy: Weekend Crypto Breakout")
    print(f"Next Review: Monday forex open (05:00 Beijing time)")
    print(f"Risk Management: 0.5% per trade, 3% daily max")

print("\n" + "=" * 80)
print("ACTION ITEMS")
print("=" * 80)
if positions:
    for pos in positions:
        if pos.profit > (pos.tp - pos.price_open) * 0.5 * pos.volume:
            print(f"- {pos.symbol}: Consider trailing stop (50% to TP)")
        elif pos.profit < 0:
            print(f"- {pos.symbol}: Monitor, respect stop loss")
        else:
            print(f"- {pos.symbol}: Hold, monitor for breakout")

print("\n- Monday: Re-scan forex market (EURUSD, USDJPY, etc.)")
print("- Monitor BTC: Key levels $70,000 support / $71,000 resistance")

mt5.shutdown()
