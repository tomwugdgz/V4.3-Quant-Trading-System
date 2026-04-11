import MetaTrader5 as mt5
import datetime
import json

mt5.initialize()

# 账户信息
account = mt5.account_info()
balance = account.balance
print(f"账户余额：${balance:.2f}")
print("")

# 学习单配置
trades = [
    {
        "symbol": "EURUSD",
        "type": mt5.ORDER_TYPE_BUY,
        "direction": "做多",
        "volume": 0.10,
        "sl_points": 0.0050,  # 50 点
        "tp_points": 0.0100,  # 100 点
        "reason": "多头趋势 + 技术面突破"
    },
    {
        "symbol": "USDCHF",
        "type": mt5.ORDER_TYPE_SELL,
        "direction": "做空",
        "volume": 0.10,
        "sl_points": 0.0030,  # 30 点
        "tp_points": 0.0033,  # 33 点
        "reason": "空头趋势 + 地缘避险资金流出瑞郎"
    },
    {
        "symbol": "XAUUSD",
        "type": mt5.ORDER_TYPE_BUY,
        "direction": "做多",
        "volume": 0.02,
        "sl_points": 50,  # $50
        "tp_points": 150,  # $150
        "reason": "中东局势避险首选黄金"
    }
]

results = []

for trade in trades:
    symbol = trade["symbol"]
    tick = mt5.symbol_info_tick(symbol)
    
    if not tick:
        print(f"{symbol}: 无法获取价格")
        continue
    
    # 计算止损止盈
    if trade["type"] == mt5.ORDER_TYPE_BUY:
        entry_price = tick.ask
        sl = entry_price - trade["sl_points"]
        tp = entry_price + trade["tp_points"]
    else:
        entry_price = tick.bid
        sl = entry_price + trade["sl_points"]
        tp = entry_price - trade["tp_points"]
    
    # 风险计算
    risk_usd = abs(entry_price - sl) * trade["volume"] * 100000
    if symbol == "USDJPY":
        risk_usd = abs(entry_price - sl) * trade["volume"] * 1000
    elif symbol == "XAUUSD":
        risk_usd = abs(entry_price - sl) * trade["volume"] * 100
    
    print(f"【{symbol} - {trade['direction']}】")
    print(f"  手数：{trade['volume']}")
    print(f"  入场：{entry_price:.5f}")
    print(f"  止损：{sl:.5f}")
    print(f"  止盈：{tp:.5f}")
    print(f"  风险：${risk_usd:.2f} ({risk_usd/balance*100:.2f}%)")
    print(f"  理由：{trade['reason']}")
    
    # 执行订单
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": trade["volume"],
        "type": trade["type"],
        "price": entry_price,
        "sl": sl,
        "tp": tp,
        "deviation": 50,
        "magic": 20260322,
        "comment": "learning_multi_symbol",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"  ✅ 订单执行成功！订单号：{result.order}")
        results.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "direction": trade["direction"],
            "volume": trade["volume"],
            "entry_price": result.price,
            "sl": sl,
            "tp": tp,
            "order_id": result.order,
            "risk_usd": risk_usd,
            "reason": trade["reason"]
        })
    else:
        print(f"  ❌ 订单失败：{result.comment}")
    
    print("")

# 记录到日志
if results:
    with open("C:/Users/DELL/.openclaw-autoclaw/workspace/trading/journal/learning_trades_log.json", "a", encoding="utf-8") as f:
        for r in results:
            json.dump(r, f, ensure_ascii=False)
            f.write("\n")
    print("📝 已记录到交易日志")

mt5.shutdown()
