import MetaTrader5 as mt5
import time

if not mt5.initialize():
    print("初始化失败")
    exit()

symbol = "NZDUSD"
ticket = 1551795763

# 获取持仓
positions = mt5.positions_get(symbol)
if not positions:
    print(f"无 {symbol} 持仓")
    mt5.shutdown()
    exit()

pos = positions[0]
print(f"持仓 ticket: {pos.ticket}")
print(f"手数：{pos.volume}")
print(f"类型：{'BUY' if pos.type == 0 else 'SELL'}")
print(f"入场价：{pos.price_open}")
print(f"当前盈亏：{pos.profit}")

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
print(f"\n当前 Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")

# BUY 持仓平仓需要用 SELL，价格是 Bid
price = tick.bid
order_type = mt5.ORDER_TYPE_SELL

print(f"\n准备平仓:")
print(f"  动作：SELL")
print(f"  价格：{price:.5f}")
print(f"  手数：{pos.volume}")
print(f"  持仓 ticket: {pos.ticket}")

# 构建平仓请求
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": pos.volume,
    "type": order_type,
    "position": pos.ticket,
    "price": price,
    "deviation": 20,
    "magic": 234000,
    "comment": "close_position"
}

print("\n发送订单...")
result = mt5.order_send(request)

print(f"\n结果:")
print(f"  Retcode: {result.retcode}")
print(f"  Order: {result.order}")
print(f"  Volume: {result.volume}")
print(f"  Price: {result.price}")
print(f"  Comment: {result.comment}")

# 检查是否成功
if result.retcode == 10009:
    print("\n*** 平仓成功！***")
else:
    print(f"\n*** 平仓失败 (retcode={result.retcode}) ***")
    # 查询最后错误
    last_error = mt5.last_error()
    print(f"最后错误：{last_error}")

time.sleep(1)

# 验证
positions_after = mt5.positions_get(symbol)
print(f"\n验证：NZDUSD 持仓数量 = {len(positions_after) if positions_after else 0}")

mt5.shutdown()
