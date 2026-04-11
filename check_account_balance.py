import MetaTrader5 as mt5
import json
from datetime import datetime

# 初始化 MT5
print("=" * 70)
print("MT5 账户余额查询")
print("=" * 70)

if not mt5.initialize():
    print(f"初始化失败：{mt5.last_error()}")
    exit()

# 获取账户信息
account_info = mt5.account_info()

if account_info is None:
    print("获取账户信息失败")
    mt5.shutdown()
    exit()

print(f"\n账户信息")
print("=" * 70)
print(f"账户号码：{account_info.login}")
print(f"服务器：{account_info.server}")
print(f"货币：{account_info.currency}")
print(f"杠杆：1:{account_info.leverage}")
print("=" * 70)

print(f"\n资金状况")
print("=" * 70)
print(f"余额 (Balance): ${account_info.balance:.2f}")
print(f"净值 (Equity): ${account_info.equity:.2f}")
print(f"预付款 (Margin): ${account_info.margin:.2f}")
print(f"可用资金 (Margin Free): ${account_info.margin_free:.2f}")
print(f"账户状态：{account_info.trade_mode}")
print("=" * 70)

print(f"\n盈亏统计")
print("=" * 70)
print(f"浮动盈亏：${account_info.profit:.2f}")
print(f"初始资金：$10,000.00")
print(f"收益率：{(account_info.equity - 10000) / 10000 * 100:.2f}%")
print("=" * 70)

# 获取持仓
positions = mt5.positions_get()
if positions:
    print(f"\n当前持仓：{len(positions)} 个")
    print("=" * 70)
    total_profit = 0
    for pos in positions:
        profit = pos.profit + pos.swap + pos.commission
        total_profit += profit
        pos_type = "多" if pos.type == 0 else "空"
        print(f"{pos.symbol}: {pos.volume}手 {pos_type} @ {pos.price_open} -> 盈亏：${profit:.2f}")
    print(f"持仓总盈亏：${total_profit:.2f}")
    print("=" * 70)
else:
    print(f"\n当前无持仓")

# 保存结果
result = {
    "timestamp": datetime.now().isoformat(),
    "account": account_info.login,
    "server": account_info.server,
    "currency": account_info.currency,
    "balance": account_info.balance,
    "equity": account_info.equity,
    "margin": account_info.margin,
    "margin_free": account_info.margin_free,
    "profit": account_info.profit,
    "positions_count": len(positions) if positions else 0,
    "leverage": account_info.leverage
}

with open("trading/mt5-account-status.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n数据已保存：trading/mt5-account-status.json")

mt5.shutdown()
print(f"\n查询完成！")
