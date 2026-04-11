import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 交易参数
symbol = "BTCUSD"
order_type = mt5.ORDER_TYPE_BUY
lot_size = 0.03  # 正确手数
stop_loss_points = 1500
take_profit_points = 3000

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
current_price = tick.ask

# 计算 SL 和 TP
sl_price = round(current_price - stop_loss_points, 2)
tp_price = round(current_price + take_profit_points, 2)

# 获取账户信息
account = mt5.account_info()

print("=" * 70)
print("BTCUSD BUY ORDER")
print("=" * 70)
print(f"Symbol: {symbol}")
print(f"Type: BUY")
print(f"Lot Size: {lot_size}")
print(f"Entry: ${current_price:.2f}")
print(f"Stop Loss: ${sl_price:.2f}")
print(f"Take Profit: ${tp_price:.2f}")
print(f"Risk/Reward: 1:2")
print(f"Risk: ${lot_size * stop_loss_points:.2f}")

# 准备订单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": order_type,
    "price": current_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 100,
    "magic": 123456,
    "comment": "BTC Weekend Trade",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print("\nSending order...")

result = mt5.order_send(request)

print("\n" + "=" * 70)
if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("[SUCCESS] ORDER EXECUTED!")
    print(f"Order ID: {result.order}")
    print(f"Deal ID: {result.deal}")
    print(f"Volume: {result.volume} lots")
    print(f"Price: ${result.price:.2f}")
    
    # 显示新账户状态
    account_new = mt5.account_info()
    print(f"\nBalance: ${account_new.balance:.2f}")
    print(f"Equity: ${account_new.equity:.2f}")
else:
    print(f"[FAILED] Retcode: {result.retcode}")
    print(f"Comment: {result.comment}")

mt5.shutdown()
