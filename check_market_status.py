import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("市场状态检查")
print("=" * 80)

# 检查几个主要品种的实时数据
symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]

print(f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n品种实时数据:")

for symbol in symbols:
    tick = mt5.symbol_info_tick(symbol)
    if tick and tick.bid > 0:
        spread = (tick.ask - tick.bid) * 10000
        print(f"  {symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}, Spread={spread:.1f} pips [OK]")
    else:
        print(f"  {symbol}: 无数据 [FAIL]")

# 获取 H1 K 线数据检查
print("\nH1 K 线数据检查 (USDJPY):")
rates = mt5.copy_rates_from_pos("USDJPY", mt5.TIMEFRAME_H1, 0, 10)
if rates is not None and len(rates) > 0:
    print(f"  最新 K 线时间：{rates[-1]['time']}")
    print(f"  最新收盘价：{rates[-1]['close']:.5f}")
    print(f"  数据完整 [OK]")
else:
    print(f"  无 K 线数据 [FAIL]")

# 账户持仓
positions = mt5.positions_get()
print(f"\n当前持仓：{len(positions) if positions else 0} 单")

mt5.shutdown()
