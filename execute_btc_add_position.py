import MetaTrader5 as mt5
import datetime
import json

mt5.initialize()

# 账户信息
account = mt5.account_info()
balance = account.balance
print(f"账户余额：${balance:.2f}")
print("")

# 加仓参数
symbol = "BTCUSD"
add_volume = 0.02  # 加仓 0.02 手
total_volume = 0.03  # 总仓位 0.03 手

# 获取当前价格
tick = mt5.symbol_info_tick(symbol)
current_price = tick.ask

# 止损止盈 (和原有持仓一致)
entry_price = 68935.94  # 原有入场价
stop_loss = 67423.94    # 原有止损
take_profit = 71923.94  # 原有止盈

# 风险计算
risk_per_trade = 0.005  # 0.5%
total_risk = balance * risk_per_trade * 3  # 3 倍风险 (因为加到 3 倍仓位)

print(f"【BTCUSD 加仓单】")
print(f"加仓手数：{add_volume} 手")
print(f"总仓位：{total_volume} 手")
print(f"入场价：${current_price:.2f}")
print(f"止损：${stop_loss:.2f}")
print(f"止盈：${take_profit:.2f}")
print(f"总风险：${total_risk:.2f} ({total_risk/balance*100:.2f}%)")
print("")

# 执行买单
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": add_volume,
    "type": mt5.ORDER_TYPE_BUY,
    "price": tick.ask,
    "sl": stop_loss,
    "tp": take_profit,
    "deviation": 100,
    "magic": 20260322,
    "comment": "BTC_add_position_user_approved",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

print("执行订单中...")
result = mt5.order_send(request)

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print("✅ 加仓成功！")
    print(f"订单号：{result.order}")
    print(f"成交价：${result.price:.2f}")
    
    # 记录到日志
    log_entry = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": "ADD_POSITION",
        "symbol": symbol,
        "add_volume": add_volume,
        "total_volume": total_volume,
        "entry_price": result.price,
        "sl": stop_loss,
        "tp": take_profit,
        "order_id": result.order,
        "reason": "用户批准加仓 - 干就完了",
        "risk_usd": total_risk
    }
    
    with open("C:/Users/DELL/.openclaw-autoclaw/workspace/trading/journal/btc_trades_log.json", "a", encoding="utf-8") as f:
        json.dump(log_entry, f, ensure_ascii=False)
        f.write("\n")
    
    print("📝 已记录到交易日志")
else:
    print("❌ 加仓失败")
    print(f"错误代码：{result.retcode}")
    print(f"错误信息：{result.comment}")

mt5.shutdown()
