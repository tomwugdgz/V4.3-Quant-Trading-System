# -*- coding: utf-8 -*-
"""
平仓 AUDUSD - 简单版本
"""
import MetaTrader5 as mt5
import time

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("平仓 AUDUSD...")

positions = mt5.positions_get(symbol="AUDUSD")
if not positions:
    print("无 AUDUSD 持仓")
    mt5.shutdown()
    exit()

for pos in positions:
    print(f"订单号：{pos.ticket}, 手数：{pos.volume}, 盈亏：${pos.profit:.2f}")
    
    tick = mt5.symbol_info_tick("AUDUSD")
    
    # 用 ORDER_TYPE_SELL 平多单
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "AUDUSD",
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": pos.ticket,
        "price": tick.bid,
        "deviation": 50,
        "magic": 234000,
        "comment": "close_all",
        "type_filling": mt5.ORDER_FILLING_IOC
    }
    
    print("发送平仓订单...")
    for i in range(3):
        result = mt5.order_send(request)
        if result and result.retcode == 10009:
            print(f"成功！订单号：{result.order}, 成交价：{result.price:.5f}")
            break
        elif result:
            print(f"尝试 {i+1}: retcode={result.retcode}")
        else:
            print(f"尝试 {i+1}: 返回 None")
        time.sleep(1)

time.sleep(2)

# 验证
positions_after = mt5.positions_get(symbol="AUDUSD")
print(f"\nAUDUSD 剩余持仓：{len(positions_after) if positions_after else 0} 单")

mt5.shutdown()
