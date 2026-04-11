import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 交易参数
symbol = "XAUUSD"
order_type = mt5.ORDER_TYPE_SELL
lot_size = 0.01
atr = 97.50
stop_loss_points = 195  # 2 ATR
take_profit_points = 390  # 4 ATR (1:2)

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
current_price = tick.bid  # SELL 用 bid 价

# 计算 SL 和 TP (SELL: SL 在上，TP 在下)
sl_price = round(current_price + stop_loss_points, 2)
tp_price = round(current_price - take_profit_points, 2)

# 获取账户信息
account = mt5.account_info()

print("=" * 70)
print("XAUUSD (GOLD) SELL ORDER")
print("=" * 70)
print(f"Account Balance: ${account.balance:.2f}")
print(f"Free Margin: ${account.margin_free:.2f}")

print(f"\nTRADE DETAILS:")
print(f"Symbol: {symbol}")
print(f"Type: SELL")
print(f"Lot Size: {lot_size}")
print(f"Entry: ${current_price:.2f}")
print(f"Stop Loss: ${sl_price:.2f} (+{stop_loss_points} points)")
print(f"Take Profit: ${tp_price:.2f} (-{take_profit_points} points)")
print(f"Risk/Reward: 1:2")

# 风险计算
risk_usd = lot_size * stop_loss_points * 100  # 100 = contract size
print(f"\nRisk: ${risk_usd:.2f} ({(risk_usd/account.balance)*100:.2f}% of balance)")

# 保证金
symbol_info = mt5.symbol_info(symbol)
margin_required = (current_price * lot_size * symbol_info.trade_contract_size) / account.leverage
print(f"Margin Required: ${margin_required:.2f}")

# 准备卖单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": order_type,
    "price": current_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 50,
    "magic": 123456,
    "comment": "Gold Downtrend Trade",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print("\n" + "=" * 70)
print("SENDING ORDER...")
print("=" * 70)

result = mt5.order_send(request)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("\n[SUCCESS] ORDER EXECUTED!")
    print(f"Order ID: {result.order}")
    print(f"Deal ID: {result.deal}")
    print(f"Volume: {result.volume} lots")
    print(f"Entry Price: ${result.price:.2f}")
    
    # 新账户状态
    account_new = mt5.account_info()
    print(f"\nNew Balance: ${account_new.balance:.2f}")
    print(f"New Equity: ${account_new.equity:.2f}")
else:
    print(f"\n[FAILED] Retcode: {result.retcode}")
    print(f"Comment: {result.comment}")

mt5.shutdown()
