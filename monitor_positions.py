"""
盈利监控脚本 — 2026-05-08
监控持仓盈利变化，浮盈>30pip时考虑移动止损保护
"""
import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)
info = mt5.account_info()
positions = mt5.positions_get()

print("=" * 55)
print(f"盈利监控 {datetime.now().strftime('%H:%M')}")
print("=" * 55)
print(f"余额=${info.balance:.2f}  净值=${info.equity:.2f}")
print()

peak_profit = 0
for p in positions:
    pdir = 'BUY' if p.type == 0 else 'SELL'
    profit = float(p.profit)
    peak_profit = max(peak_profit, profit)

    tick = mt5.symbol_info_tick(p.symbol)
    current = tick.bid if p.type == 0 else tick.ask

    # 计算距TP和SL的距离
    if p.type == 0:  # BUY
        dist_sl = (current - float(p.sl)) / (current - float(p.price_open)) * 100 if float(p.sl) > 0 else 999
        dist_tp = (float(p.tp) - current) / (current - float(p.price_open)) * 100 if float(p.tp) > 0 else 999
        pips = (current - float(p.price_open)) / 0.0001
    else:
        dist_sl = (float(p.sl) - current) / (float(p.price_open) - current) * 100 if float(p.sl) > 0 else 999
        dist_tp = (float(p.price_open) - float(p.tp)) / (float(p.price_open) - current) * 100 if float(p.tp) > 0 else 999
        pips = (float(p.price_open) - current) / 0.0001

    status = "PROFIT" if profit > 0 else "LOSS"
    alert = ""
    if profit > 30:
        alert = ">>> 考虑移动止损到入场价！"
    elif profit > 20:
        alert = ">>> 盈利良好，继续持有"

    print(f"{p.symbol} {pdir} {p.volume}@{float(p.price_open):.5f}")
    print(f"  浮盈: ${profit:.2f} ({pips:.0f}pip) [{status}]")
    print(f"  现价: {current:.5f}")
    print(f"  SL: {float(p.sl):.5f} | TP: {float(p.tp):.5f}")
    if alert:
        print(f"  {alert}")
    print()

# 总账户状态
total_profit = float(info.equity) - float(info.balance)
print(f"总浮盈: ${total_profit:.2f}")
if total_profit > 50:
    print(">>> 整体盈利丰厚，可考虑部分平仓落袋")

mt5.shutdown()