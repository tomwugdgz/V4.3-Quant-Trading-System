"""检查当前持仓"""
import MetaTrader5 as mt5
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from base import initialize, get_positions, shutdown

print("=" * 70)
print("当前持仓检查")
print("=" * 70)

if not initialize():
    print("MT5 连接失败")
    sys.exit(1)

positions = get_positions()

if not positions:
    print("\n当前无持仓")
else:
    print(f"\n当前持仓数量：{len(positions)}\n")
    for pos in positions:
        print(f"品种：{pos['symbol']}")
        print(f"方向：{pos['type']}")
        print(f"手数：{pos['volume']}")
        print(f"入场价：{pos['price']}")
        print(f"当前价：{pos['price_current']}")
        print(f"浮动盈亏：${pos['profit']}")
        print(f"订单号：{pos['ticket']}")
        print("-" * 40)

shutdown()
