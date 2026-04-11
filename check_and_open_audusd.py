# -*- coding: utf-8 -*-
"""
检查账户并重新开仓 AUDUSD SELL
"""
import MetaTrader5 as mt5
import time

print("尝试连接 MT5...")

# 重试连接
for i in range(5):
    if mt5.initialize():
        print(f"MT5 连接成功！(尝试 {i+1}/5)")
        break
    print(f"尝试 {i+1}/5 失败，等待 2 秒...")
    time.sleep(2)

if not mt5.connected:
    print("MT5 连接失败，放弃")
    exit()

# 获取账户信息
account = mt5.account_info()
print(f"\n账户余额：${account.balance:.2f}")
print(f"账户净值：${account.equity:.2f}")

# 获取持仓
positions = mt5.positions_get()
print(f"\n当前持仓 ({len(positions) if positions else 0} 单):")
if positions:
    for pos in positions:
        print(f"  {pos.symbol} {pos.type == mt5.POSITION_TYPE_BUY and 'BUY' or 'SELL'} {pos.volume:.2f} 手 @ {pos.price_open:.5f}, 盈亏：${pos.profit:.2f}")
else:
    print("  无持仓")

# 扫描 AUDUSD 信号
tick = mt5.symbol_info_tick("AUDUSD")
print(f"\nAUDUSD 当前价：Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")

# 尝试开仓
symbol = "AUDUSD"
volume = 0.08
entry_price = tick.bid
sl_price = round(entry_price + 0.0030, 5)
tp_price = round(entry_price - 0.0060, 5)

print(f"\n开仓 AUDUSD SELL:")
print(f"  手数：{volume}")
print(f"  入场：{entry_price:.5f}")
print(f"  止损：{sl_price:.5f}")
print(f"  止盈：{tp_price:.5f}")

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_SELL,
    "price": entry_price,
    "sl": sl_price,
    "tp": tp_price,
    "deviation": 20,
    "magic": 234000,
    "comment": "AUDUSD_SELL_0.309pct",
    "type_filling": mt5.ORDER_FILLING_IOC
}

print("\n发送订单...")
result = mt5.order_send(request)

if result and result.retcode == 10009:
    print(f"[OK] 开仓成功！订单号：{result.order}, 成交价：{result.price:.5f}")
else:
    print(f"[FAIL] retcode={result.retcode if result else 'None'}")

time.sleep(1)

# 验证
positions_after = mt5.positions_get(symbol="AUDUSD")
print(f"\nAUDUSD 持仓：{len(positions_after) if positions_after else 0} 单")

mt5.shutdown()
