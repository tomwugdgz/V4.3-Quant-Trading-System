import MetaTrader5 as mt5
import datetime
import json

# 初始化 MT5
mt5.initialize()

# 账户信息
account = mt5.account_info()
balance = account.balance
print(f"账户余额：${balance:.2f}")

# 比特币参数
symbol = "BTCUSD"
tick = mt5.symbol_info_tick(symbol)
current_price = tick.bid
print(f"BTCUSD 当前价：${current_price:.2f}")

# 交易参数
lot_size = 0.01  # 极小额测试
risk_percent = 0.005  # 0.5% 风险
risk_amount = balance * risk_percent
print(f"仓位：{lot_size} 手")
print(f"风险金额：${risk_amount:.2f}")

# 止损止盈计算 (基于 ATR 约$340)
atr = 340
stop_loss_points = 1500  # 约$1,500 止损
take_profit_points = 3000  # 约$3,000 止盈

# 做多单
sl_long = current_price - stop_loss_points
tp_long = current_price + take_profit_points

print(f"\n做多单设置:")
print(f"入场：${current_price:.2f}")
print(f"止损：${sl_long:.2f} (-${stop_loss_points})")
print(f"止盈：${tp_long:.2f} (+${take_profit_points})")

# 执行做多单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot_size,
    "type": mt5.ORDER_TYPE_BUY,
    "price": tick.ask,
    "sl": sl_long,
    "tp": tp_long,
    "deviation": 100,
    "magic": 20260322,
    "comment": "BTC_learning_day1",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

# 发送订单
result = mt5.order_send(request)
print(f"\n订单结果：{result}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("✅ 订单执行成功！")
    print(f"订单号：{result.order}")
    print(f"入场价：${result.price:.2f}")
    
    # 记录到日志
    log_entry = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "direction": "BUY",
        "volume": lot_size,
        "entry_price": result.price,
        "sl": sl_long,
        "tp": tp_long,
        "order_id": result.order
    }
    
    with open("C:/Users/DELL/.openclaw-autoclaw/workspace/trading/journal/btc_trades_log.json", "a", encoding="utf-8") as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write("\n")
    
    print("📝 已记录到交易日志")
else:
    print("❌ 订单执行失败")
    print(f"错误代码：{result.retcode}")
    print(f"错误信息：{result.comment}")

mt5.shutdown()
