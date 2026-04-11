# -*- coding: utf-8 -*-
"""
平仓 1 单 USDCHF - 修复版
"""
import MetaTrader5 as mt5
import time

if not mt5.initialize():
    print("Init failed")
    exit()

print("平仓 1 单 USDCHF...")

positions = mt5.positions_get(symbol="USDCHF")
if not positions:
    print("No USDCHF positions")
    mt5.shutdown()
    exit()

pos = positions[0]
print(f"Ticket: {pos.ticket}, Volume: {pos.volume}, Profit: ${pos.profit:.2f}")

tick = mt5.symbol_info_tick("USDCHF")

# 尝试不同填充模式
for filling in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "USDCHF",
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": pos.ticket,
        "price": tick.bid,
        "deviation": 10,
        "magic": 234000,
        "comment": "close",
        "type_filling": filling
    }
    
    print(f"\n尝试填充模式：{filling}")
    result = mt5.order_send(request)
    
    if result.retcode == 10009:
        print(f"成功！Order: {result.order}, Price: {result.price:.5f}")
        break
    else:
        print(f"失败：retcode={result.retcode}")
    
    time.sleep(0.5)

time.sleep(1)

# 验证
positions_after = mt5.positions_get(symbol="USDCHF")
print(f"\nUSDCHF 持仓数：{len(positions_after) if positions_after else 0}")

mt5.shutdown()
