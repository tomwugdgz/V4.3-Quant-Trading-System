import MetaTrader5 as mt5, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print("MT5 init failed")
    sys.exit()

info = mt5.account_info()
print(f"Balance: ${info.balance:.2f}")
print(f"Equity: ${info.equity:.2f}")
print(f"Margin: ${info.margin:.2f}")
print(f"Free Margin: ${info.margin_free:.2f}")
print(f"Margin Level: {info.margin_level:.2f}%")
print(f"Leverage: 1:{info.leverage}")
print(f"Positions: {len(mt5.positions_get() or [])}")

mt5.shutdown()
