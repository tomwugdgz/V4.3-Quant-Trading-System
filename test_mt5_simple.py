import sys
sys.stdout.write("Python started\n")
sys.stdout.flush()

try:
    import MetaTrader5 as mt5
    sys.stdout.write("MT5 module imported\n")
    sys.stdout.flush()
    
    result = mt5.initialize()
    sys.stdout.write(f"MT5 initialize returned: {result}\n")
    sys.stdout.flush()
    
    if result:
        info = mt5.account_info()
        sys.stdout.write(f"Account: {info.login}\n")
        sys.stdout.write(f"Balance: {info.balance}\n")
        sys.stdout.flush()
    else:
        err = mt5.last_error()
        sys.stdout.write(f"MT5 init failed, error: {err}\n")
        sys.stdout.flush()
    
    mt5.shutdown()
except Exception as e:
    sys.stdout.write(f"Exception: {e}\n")
    sys.stdout.flush()
