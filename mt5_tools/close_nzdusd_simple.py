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
print(f"找到持仓：ticket={pos.ticket}, volume={pos.volume}, profit={pos.profit}")

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
if pos.type == 0:  # BUY
    price = tick.bid
    order_type = mt5.ORDER_TYPE_SELL
else:  # SELL
    price = tick.ask
    order_type = mt5.ORDER_TYPE_BUY

print(f"平仓价格：{price:.5f}, 类型：{'SELL' if pos.type == 0 else 'BUY'}")

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
    "comment": "close"
}

# 发送订单
for i in range(3):
    result = mt5.order_send(request)
    print(f"尝试 {i+1}: retcode={result.retcode}, comment={result.comment}")
    if result.retcode == 10009:  # 成功
        print(f"平仓成功！成交价：{result.price:.5f}")
        break
    time.sleep(0.5)

mt5.shutdown()
