"""
平仓 NZDUSD - 按指导执行
"""

import MetaTrader5 as mt5
import json
from datetime import datetime

# 初始化 MT5
if not mt5.initialize():
    print("MT5 初始化失败")
    exit()

# 平仓参数
symbol = "NZDUSD"
position_ticket = 1551795763  # NZDUSD 持仓订单号
volume = 0.17
current_price = mt5.symbol_info_tick(symbol).ask  # BUY 平仓用 ask 价

print("=" * 80)
print("平仓 NZDUSD BUY")
print("=" * 80)
print(f"订单号：{position_ticket}")
print(f"品种：{symbol}")
print(f"手数：{volume}")
print(f"当前价：{current_price:.5f}")

# 获取持仓信息
positions = mt5.positions_get(symbol=symbol)
if positions is None:
    print("无法获取持仓")
    mt5.shutdown()
    exit()

position = None
for pos in positions:
    if pos.ticket == position_ticket:
        position = pos
        break

if position is None:
    print(f"未找到订单 {position_ticket}")
    # 尝试找第一个 NZDUSD 持仓
    if len(positions) > 0:
        position = positions[0]
        print(f"使用第一个持仓：ticket={position.ticket}")
    else:
        print("无任何持仓")
        mt5.shutdown()
        exit()

print(f"入场价：{position.price_open:.5f}")
print(f"当前盈亏：${position.profit:.2f}")

# 平仓请求
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_SELL,  # 平仓 BUY 需要 SELL
    "position": position.ticket,
    "price": current_price,
    "deviation": 10,
    "magic": 234000,
    "comment": "K 线分析平仓 - 趋势转弱"
}

# 发送订单
result = mt5.order_send(request)

print("\n订单执行结果:")
print("-" * 80)
print(f"返回码：{result.retcode}")
print(f"订单号：{result.order}")
print(f"成交量：{result.volume}")
print(f"成交价：{result.price:.5f}")
print(f"盈亏：${result.profit:.2f}")
print(f"备注：{result.comment}")

# 保存结果
order_result = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'symbol': symbol,
    'action': 'CLOSE',
    'position_ticket': position.ticket,
    'entry_price': position.price_open,
    'exit_price': result.price if result.price > 0 else current_price,
    'volume': volume,
    'profit': result.profit if hasattr(result, 'profit') else 0,
    'retcode': result.retcode,
    'comment': 'K 线分析平仓 - 趋势转弱'
}

# 保存到文件
import os
os.makedirs('output', exist_ok=True)
filename = f"output/close-NZDUSD-BUY-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(order_result, f, indent=2, ensure_ascii=False)

print(f"\n结果已保存：{filename}")
print("=" * 80)

mt5.shutdown()
