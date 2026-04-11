# -*- coding: utf-8 -*-
"""
平仓 USDCAD - 信号反转 (SELL 0.012%)
"""
import MetaTrader5 as mt5
import time

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("平仓 USDCAD - 信号反转 (SELL 0.012%)")
print("=" * 80)

positions = mt5.positions_get(symbol="USDCAD")
if not positions:
    print("无 USDCAD 持仓")
    mt5.shutdown()
    exit()

pos = positions[0]
print(f"订单号：{pos.ticket}")
print(f"手数：{pos.volume:.2f}")
print(f"入场价：{pos.price_open:.5f}")
tick = mt5.symbol_info_tick("USDCAD")
print(f"当前买价：{tick.ask:.5f}")
print(f"当前卖价：{tick.bid:.5f}")
print(f"浮动盈亏：${pos.profit:.2f}")

# 尝试不同填充模式
for filling in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "USDCAD",
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": pos.ticket,
        "price": tick.bid,
        "deviation": 20,
        "magic": 234000,
        "comment": "Signal_Reversal_Close",
        "type_filling": filling
    }
    
    print(f"\n尝试填充模式：{filling}")
    result = mt5.order_send(request)
    
    print(f"返回码：{result.retcode}")
    print(f"订单号：{result.order}")
    print(f"成交价：{result.price:.5f}")
    
    if result.retcode == 10009:
        print("[OK] 平仓成功！")
        break
    else:
        print(f"[FAIL] retcode={result.retcode}")
    
    time.sleep(0.5)

time.sleep(1)

# 验证
positions_after = mt5.positions_get(symbol="USDCAD")
print(f"\nUSDCAD 剩余持仓：{len(positions_after) if positions_after else 0} 单")

mt5.shutdown()
