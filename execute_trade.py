import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 交易参数
symbol = "EURUSD"
order_type = mt5.ORDER_TYPE_BUY
stop_loss_pips = 30
take_profit_pips = 60  # 1:2 风报比

# 获取账户信息
account = mt5.account_info()
balance = account.balance
equity = account.equity
margin_free = account.margin_free

print("=" * 70)
print("ACCOUNT STATUS")
print("=" * 70)
print(f"Balance: ${balance:.2f}")
print(f"Equity: ${equity:.2f}")
print(f"Free Margin: ${margin_free:.2f}")
print(f"Leverage: 1:{account.leverage}")

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
current_price = tick.ask

# 计算合适的仓位 (风险 0.5% = $51.76)
risk_amount = balance * 0.005
pip_value_per_lot = 10  # EURUSD: $10 per pip per 1.0 lot
stop_loss_pips = 30

# 仓位 = 风险金额 / (止损点数 * 每点价值)
lot_size = risk_amount / (stop_loss_pips * pip_value_per_lot)
lot_size = round(lot_size, 2)

# 检查保证金要求
symbol_info = mt5.symbol_info(symbol)
margin_required = (current_price * lot_size * symbol_info.trade_contract_size) / account.leverage

print(f"\nTRADE PARAMETERS")
print(f"Symbol: {symbol}")
print(f"Entry Price: {current_price:.5f}")
print(f"Risk Amount: ${risk_amount:.2f} (0.5% of balance)")
print(f"Stop Loss: {stop_loss_pips} pips")
print(f"Calculated Lot Size: {lot_size:.2f}")
print(f"Margin Required: ${margin_required:.2f}")

# 确保保证金足够
if margin_required > margin_free * 0.9:
    lot_size = round((margin_free * 0.5) / (current_price * symbol_info.trade_contract_size / account.leverage), 2)
    print(f"\n[WARN] Adjusted lot size to {lot_size:.2f} (margin constraint)")

# 计算 SL 和 TP
sl_price = round(current_price - (stop_loss_pips * 0.0001), 5)
tp_price = round(current_price + (take_profit_pips * 0.0001), 5)

print(f"Stop Loss: {sl_price:.5f} ({stop_loss_pips} pips)")
print(f"Take Profit: {tp_price:.5f} ({take_profit_pips} pips)")
print(f"Risk/Reward: 1:{take_profit_pips/stop_loss_pips:.1f}")

# 准备买单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": order_type,
    "price": current_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 20,
    "magic": 123456,
    "comment": "Agency-Agent Trade",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print("\n" + "=" * 70)
print("SENDING ORDER...")
print("=" * 70)

# 发送订单
result = mt5.order_send(request)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("\n[OK] ORDER EXECUTED SUCCESSFULLY!")
    print(f"Order ID: {result.order}")
    print(f"Deal ID: {result.deal}")
    print(f"Volume: {result.volume} lots")
    print(f"Entry Price: {result.price:.5f}")
    
    # 获取新账户状态
    account_new = mt5.account_info()
    print(f"\nNew Balance: ${account_new.balance:.2f}")
    print(f"New Equity: ${account_new.equity:.2f}")
else:
    print(f"\n[FAIL] ORDER FAILED!")
    print(f"Retcode: {result.retcode}")
    print(f"Comment: {result.comment}")

mt5.shutdown()
