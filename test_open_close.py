# -*- coding: utf-8 -*-
# 测试开仓和平仓
import MetaTrader5 as mt5

print("=== Testing Open/Close ===\n")

# 初始化
result = mt5.initialize()
print("Initialize:", result)
if not result:
    print("Init failed:", mt5.last_error())
    exit()

# 账户信息
account = mt5.account_info()
print("Account:", account.login, "Balance:", account.balance)

# 打开 EURUSD 0.01 手 BUY 测试
symbol = "EURUSD"
volume = 0.01
tick = mt5.symbol_info_tick(symbol)
symbol_info = mt5.symbol_info(symbol)

if not tick:
    print("No tick for", symbol)
    mt5.shutdown()
    exit()

price = tick.ask
sl = price - 0.00100
tp = price + 0.00100

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": price,
    "sl": sl,
    "tp": tp,
    "deviation": 20,
    "magic": 999999,
    "comment": "test",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

result = mt5.order_send(request)
print("\nOpen test order:")
print("  Retcode:", result.retcode)
print("  Order:", result.order)
print("  Price:", result.price)
print("  Comment:", result.comment)

if result.retcode != 10009:
    print("\n❌ Open failed")
    mt5.shutdown()
    exit()

# 获取 position ticket
positions = mt5.positions_get()
test_pos = None
for pos in positions:
    if pos.magic == 999999:
        test_pos = pos
        break

if not test_pos:
    print("\n⚠️ Test position not found")
    mt5.shutdown()
    exit()

print("\n✅ Test position opened:")
print("  Ticket:", test_pos.ticket)
print("  Symbol:", test_pos.symbol)
print("  Volume:", test_pos.volume)
print("  Price:", test_pos.price_open)

# 平仓测试
print("\nClosing test position...")
close_request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": test_pos.symbol,
    "volume": test_pos.volume,
    "type": mt5.ORDER_TYPE_SELL,
    "position": test_pos.ticket,
    "price": tick.bid,
    "deviation": 20,
    "magic": 999999,
    "comment": "test-close",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

close_result = mt5.order_send(close_request)
print("Close result:")
print("  Retcode:", close_result.retcode)
print("  Comment:", close_result.comment)

if close_result.retcode == 10009:
    print("\n✅ Test PASSED: Open + Close OK")
else:
    print("\n❌ Test FAILED: Close failed")

# 显示当前持仓
print("\n=== Current Positions After Test ===")
positions = mt5.positions_get()
if positions:
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        print(f"  {pos.symbol} {direction} {pos.volume:.2f} lot P/L ${pos.profit:.2f}")
else:
    print("  No positions")

mt5.shutdown()
