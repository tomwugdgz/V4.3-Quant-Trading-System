import MetaTrader5 as mt5, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print('MT5 init failed')
    sys.exit()

info = mt5.account_info()
print(f"Balance: ${info.balance:.2f} | Equity: ${info.equity:.2f}")

positions = mt5.positions_get() or []
print(f"Positions: {len(positions)}")
for p in positions:
    tick = mt5.symbol_info_tick(p.symbol)
    pdir = 'BUY' if p.type == 0 else 'SELL'
    print(f"  #{p.ticket} {p.symbol} {pdir} {p.volume}@{p.price_open:.5f} P/L=${p.profit:.2f} SL={p.sl:.5f} TP={p.tp:.5f}")

# Scan signals for key symbols
symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF", "NZDUSD"]
print("\nSignal Scan:")
for sym in symbols:
    tick = mt5.symbol_info_tick(sym)
    if tick and tick.bid > 0:
        print(f"  {sym}: {tick.bid:.5f} | Spread: {tick.ask - tick.bid:.5f}")

mt5.shutdown()
