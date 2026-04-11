import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 交易参数
symbol = "BTCUSD"
order_type = mt5.ORDER_TYPE_BUY
lot_size = 0.035  # 从分析得出
stop_loss_points = 1500  # $1500 SL
take_profit_points = 3000  # $3000 TP (1:2)

# 获取账户信息
account = mt5.account_info()
print("=" * 70)
print("CRYPTO TRADE EXECUTION")
print("=" * 70)
print(f"Account Balance: ${account.balance:.2f}")
print(f"Free Margin: ${account.margin_free:.2f}")

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
current_price = tick.ask

# 计算 SL 和 TP
sl_price = round(current_price - stop_loss_points, 2)
tp_price = round(current_price + take_profit_points, 2)

print(f"\nTRADE DETAILS:")
print(f"Symbol: {symbol}")
print(f"Type: BUY")
print(f"Lot Size: {lot_size}")
print(f"Entry Price: ${current_price:.2f}")
print(f"Stop Loss: ${sl_price:.2f} (-{stop_loss_points} points)")
print(f"Take Profit: ${tp_price:.2f} (+{take_profit_points} points)")
print(f"Risk/Reward: 1:{take_profit_points/stop_loss_points:.1f}")

# 风险计算
risk_usd = lot_size * stop_loss_points
print(f"\nRisk: ${risk_usd:.2f} ({(risk_usd/account.balance)*100:.2f}% of balance)")

# 保证金检查
symbol_info = mt5.symbol_info(symbol)
margin_required = (current_price * lot_size * symbol_info.trade_contract_size) / account.leverage
print(f"Margin Required: ${margin_required:.2f}")

if margin_required > account.margin_free * 0.5:
    print("\n[WARN] High margin usage - reducing position size")
    lot_size = round((account.margin_free * 0.3) / (current_price * symbol_info.trade_contract_size / account.leverage), 3)
    print(f"Adjusted Lot Size: {lot_size}")

# 准备买单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": order_type,
    "price": current_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 50,  # crypto 波动大，放宽偏差
    "magic": 123456,
    "comment": "Crypto Weekend Trade",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print("\n" + "=" * 70)
print("SENDING ORDER...")
print("=" * 70)

result = mt5.order_send(request)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("\n[OK] ORDER EXECUTED SUCCESSFULLY!")
    print(f"Order ID: {result.order}")
    print(f"Deal ID: {result.deal}")
    print(f"Volume: {result.volume} lots")
    print(f"Entry Price: ${result.price:.2f}")
    
    # 获取新账户状态
    account_new = mt5.account_info()
    print(f"\nNew Balance: ${account_new.balance:.2f}")
    print(f"New Equity: ${account_new.equity:.2f}")
    print(f"Open Positions: {account_new.margin_so_called}")
else:
    print(f"\n[FAIL] ORDER FAILED!")
    print(f"Retcode: {result.retcode}")
    print(f"Comment: {result.comment}")
    
    # 尝试市价单
    print("\nTrying market execution...")
    request["type_filling"] = mt5.ORDER_FILLING_FOK
    result2 = mt5.order_send(request)
    if result2.retcode == mt5.TRADE_RETCODE_DONE:
        print("[OK] Market order executed!")
    else:
        print(f"[FAIL] Market order also failed: {result2.comment}")

mt5.shutdown()
