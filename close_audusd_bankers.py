# -*- coding: utf-8 -*-
"""
平仓 AUDUSD - 信号反转 (SELL 0.244%)
银行家天团决议：立即平仓
"""
import MetaTrader5 as mt5
import time

if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

print("=" * 80)
print("平仓 AUDUSD - 信号反转 (SELL 0.244%)")
print("银行家天团决议：立即平仓")
print("=" * 80)

positions = mt5.positions_get(symbol="AUDUSD")
if not positions:
    print("无 AUDUSD 持仓")
    mt5.shutdown()
    exit()

pos = positions[0]
print(f"订单号：{pos.ticket}")
print(f"手数：{pos.volume:.2f}")
print(f"入场价：{pos.price_open:.5f}")
tick = mt5.symbol_info_tick("AUDUSD")
print(f"当前买价：{tick.ask:.5f}")
print(f"当前卖价：{tick.bid:.5f}")
print(f"浮动盈亏：${pos.profit:.2f}")

# 平仓
for filling in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "AUDUSD",
        "volume": pos.volume,
        "type": mt5.ORDER_TYPE_SELL,
        "position": pos.ticket,
        "price": tick.bid,
        "deviation": 20,
        "magic": 234000,
        "comment": "Signal_Reversal_BankersDecision",
        "type_filling": filling
    }
    
    print(f"\n尝试填充模式：{filling}")
    result = mt5.order_send(request)
    
    if result is None:
        print("返回：None (请求失败)")
        continue
    
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
positions_after = mt5.positions_get(symbol="AUDUSD")
print(f"\nAUDUSD 剩余持仓：{len(positions_after) if positions_after else 0} 单")

mt5.shutdown()
