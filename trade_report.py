import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

account = mt5.account_info()
positions = mt5.positions_get()

print("=" * 70)
print("WEEKEND CRYPTO TRADE - POSITION REPORT")
print("=" * 70)
print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Account: {account.login}")
print(f"Balance: ${account.balance:.2f}")
print(f"Equity: ${account.equity:.2f}")
print(f"Free Margin: ${account.margin_free:.2f}")

print("\n" + "=" * 70)
print("OPEN POSITION")
print("=" * 70)

for pos in positions:
    if pos.symbol == "BTCUSD":
        print(f"Symbol: {pos.symbol}")
        print(f"Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"Volume: {pos.volume} lots")
        print(f"Entry Price: ${pos.price_open:.2f}")
        print(f"Current Price: ${pos.price_current:.2f}")
        print(f"Stop Loss: ${pos.sl:.2f}")
        print(f"Take Profit: ${pos.tp:.2f}")
        print(f"Floating P/L: ${pos.profit:.2f}")
        
        # 计算盈亏百分比
        entry = pos.price_open
        current = pos.price_current
        pnl_pct = ((current - entry) / entry) * 100 if pos.type == 0 else ((entry - current) / entry) * 100
        print(f"P/L %: {pnl_pct:+.2f}%")
        
        # 距离 SL 和 TP 的距离
        dist_sl = abs(current - pos.sl)
        dist_tp = abs(pos.tp - current)
        print(f"Distance to SL: ${dist_sl:.2f} ({dist_sl/1500*100:.1f}%)")
        print(f"Distance to TP: ${dist_tp:.2f} ({dist_tp/3000*100:.1f}%)")

print("\n" + "=" * 70)
print("TRADE SUMMARY")
print("=" * 70)
print("Strategy: Crypto Weekend Breakout")
print("Rationale: BTC showing bullish momentum on H1/H4")
print("Risk: 0.5% of account ($45-52)")
print("Reward Target: 1:2 Risk/Reward ratio")
print("Monitoring: Check every 4-6 hours")

print("\n" + "=" * 70)
print("NEXT ACTIONS")
print("=" * 70)
print("1. Monitor price action")
print("2. If price moves +50% to TP, consider trailing stop")
print("3. If price reverses, respect the stop loss")
print("4. Review on Monday when forex market opens")

mt5.shutdown()
