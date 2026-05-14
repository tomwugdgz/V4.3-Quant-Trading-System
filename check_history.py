import MetaTrader5 as mt5, sys, io
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if not mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000):
    print('MT5 init failed')
    sys.exit()

end = datetime.now()
start = end - timedelta(days=2)

deals = mt5.history_deals_get(start, end)
if deals:
    print(f"Deals ({len(deals)}):")
    for d in deals:
        attrs = [a for a in dir(d) if not a.startswith('_')]
        print(f"  {d}")
else:
    print("No deals found")

mt5.shutdown()
