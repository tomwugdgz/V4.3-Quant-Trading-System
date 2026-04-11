import MetaTrader5 as mt5
import datetime

mt5.initialize()

print("=== 账户信息 ===")
account = mt5.account_info()
print(f"余额：${account.balance:.2f}")
print(f"净值：${account.equity:.2f}")
print(f"预付款：${account.margin:.2f}")
print(f"可用保证金：${account.margin_free:.2f}")
print("")

print("=== 当前持仓 ===")
positions = mt5.positions_get()
if positions:
    for p in positions:
        print(f"{p.symbol} | {p.volume}手 | {p.price_open:.5f} -> {p.price_current:.5f} | 盈亏：${p.profit:.2f}")
else:
    print("无持仓")
print("")

print("=== 尝试开单测试 (EURUSD 0.01 手) ===")
tick = mt5.symbol_info_tick('EURUSD')
print(f"EURUSD 当前价：Bid={tick.bid:.5f} Ask={tick.ask:.5f}")

# 测试单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "EURUSD",
    "volume": 0.01,
    "type": mt5.ORDER_TYPE_BUY,
    "price": tick.ask,
    "sl": tick.ask - 0.0050,
    "tp": tick.ask + 0.0100,
    "deviation": 50,
    "magic": 20260322,
    "comment": "test_order",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

result = mt5.order_send(request)
print(f"订单结果：retcode={result.retcode}")
print(f"评论：{result.comment}")
print(f"订单号：{result.order if result.order else '无'}")
print(f"错误详情：{mt5.last_error()}")

mt5.shutdown()
