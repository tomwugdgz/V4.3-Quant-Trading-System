import MetaTrader5 as mt5
import datetime
import json

mt5.initialize()

account = mt5.account_info()
balance = account.balance
print(f"账户余额：${balance:.2f}")
print("")

trades = [
    {"symbol": "EURUSD", "type": mt5.ORDER_TYPE_BUY, "direction": "BUY", "volume": 0.10, "sl_points": 0.0050, "tp_points": 0.0100, "reason": "多头趋势"},
    {"symbol": "USDCHF", "type": mt5.ORDER_TYPE_SELL, "direction": "SELL", "volume": 0.10, "sl_points": 0.0030, "tp_points": 0.0033, "reason": "空头趋势"},
    {"symbol": "XAUUSD", "type": mt5.ORDER_TYPE_BUY, "direction": "BUY", "volume": 0.02, "sl_points": 50, "tp_points": 150, "reason": "避险黄金"}
]

for trade in trades:
    symbol = trade["symbol"]
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"{symbol}: 无法获取价格")
        continue
    
    if trade["type"] == mt5.ORDER_TYPE_BUY:
        entry_price = tick.ask
        sl = entry_price - trade["sl_points"]
        tp = entry_price + trade["tp_points"]
    else:
        entry_price = tick.bid
        sl = entry_price + trade["sl_points"]
        tp = entry_price - trade["tp_points"]
    
    risk_usd = abs(entry_price - sl) * trade["volume"] * 100000
    if symbol == "XAUUSD":
        risk_usd = abs(entry_price - sl) * trade["volume"] * 100
    
    print(f"[{symbol} - {trade['direction']}]")
    print(f"  入场：{entry_price:.5f} | 止损：{sl:.5f} | 止盈：{tp:.5f}")
    print(f"  风险：${risk_usd:.2f} | 理由：{trade['reason']}")
    
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
        "comment": "learning_multi",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    print(f"  结果：{result.retcode} | 订单：{result.order if result.order else '失败'}")
    print("")

mt5.shutdown()
