import MetaTrader5 as mt5
import sys

print("1. Import OK", flush=True)

# Try explicit initialization
print("2. Calling mt5.initialize()...", flush=True)
res = mt5.initialize(
    login=52797683,
    server="ICMarketsSC-Demo",
    timeout=10000
)
print(f"3. initialize returned: {res}", flush=True)

if not res:
    err = mt5.last_error()
    print(f"Error: {err}", flush=True)
    sys.exit(1)

info = mt5.account_info()
print(f"4. Balance: {info.balance}", flush=True)

mt5.shutdown()
print("5. Done", flush=True)
