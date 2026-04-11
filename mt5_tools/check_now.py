"""检查当前持仓和账户状态"""
import MetaTrader5 as mt5
import time

mt5.initialize()
time.sleep(1)

account = mt5.account_info()
print("=" * 70)
print("当前账户状态")
print("=" * 70)
print(f"账户：{account.login}")
print(f"服务器：{account.server}")
print(f"余额：${account.balance:.2f}")
print(f"净值：${account.equity:.2f}")
print(f"浮动盈亏：${account.profit:.2f}")

print(f"可用保证金：${account.margin_free:.2f}")
print(f"保证金水平：{account.margin_level:.2f}%")

positions = mt5.positions_get()
print("\n" + "=" * 70)
print("当前持仓详情")
print("=" * 70)

if positions:
    total_profit = 0
    for p in positions:
        direction = "BUY" if p.type == 0 else "SELL"
        profit = p.profit
        total_profit += profit
        print(f"\n{p.symbol} {direction}")
        print(f"  手数：{p.volume}")
        print(f"  入场价：{p.price_open:.5f}")
        print(f"  当前价：{p.price_current:.5f}")
        print(f"  止损：{p.sl:.5f}")
        print(f"  止盈：{p.tp:.5f}")
        print(f"  浮动盈亏：${profit:.2f}")
        print(f"  订单号：{p.ticket}")
    print("\n" + "=" * 70)
    print(f"总浮动盈亏：${total_profit:.2f}")
    print("=" * 70)
else:
    print("\n无持仓")

mt5.shutdown()
