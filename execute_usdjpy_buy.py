import MetaTrader5 as mt5
import sys
from datetime import datetime

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# USDJPY BUY
symbol = "USDJPY"
order_type = mt5.ORDER_TYPE_BUY
volume = 0.10  # 0.1 lots
stop_loss_pips = 30
take_profit_pips = 60

account = mt5.account_info()
balance = account.balance

print("=" * 70)
print(f"EXECUTE USDJPY BUY - Signal 0.101%")
print("=" * 70)
print(f"Balance: ${balance:.2f}")

tick = mt5.symbol_info_tick(symbol)
entry_price = tick.ask

sl_price = entry_price - (stop_loss_pips * 0.01)
tp_price = entry_price + (take_profit_pips * 0.01)

print(f"Entry: {entry_price:.3f}")
print(f"Stop Loss: {sl_price:.3f} (-{stop_loss_pips} pips)")
print(f"Take Profit: {tp_price:.3f} (+{take_profit_pips} pips)")
print(f"Volume: {volume} lots")
print()

# Place order
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": order_type,
    "price": entry_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 10,
    "magic": 234000,
    "comment": "USDJPY BUY Signal",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

result = mt5.order_send(request)

if result.retcode != mt5.TRADE_RETCODE_DONE:
    print(f"ERROR: {result.retcode}")
    sys.exit(1)

print(f"Order ID: {result.order}")
print(f"Deal ID: {result.deal}")
print(f"Volume: {result.volume} lots")
print(f"Price: {result.price:.3f}")
print()
print("[OK] USDJPY BUY executed successfully!")

mt5.shutdown()
