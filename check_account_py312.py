import MetaTrader5 as mt5

if not mt5.initialize():
    print("Init failed")
    exit()

info = mt5.account_info()
if info:
    print(f"Account: {info.login}")
    print(f"Balance: ${info.balance:.2f}")
    print(f"Equity: ${info.equity:.2f}")
    print(f"Profit: ${info.profit:.2f}")
    print(f"Margin: ${info.margin:.2f}")
    print(f"Margin Level: {info.margin_level:.2f}%")

mt5.shutdown()
