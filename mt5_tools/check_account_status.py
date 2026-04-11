"""检查账户状态"""
import MetaTrader5 as mt5
from datetime import datetime

print("=" * 70)
print("MT5 账户状态")
print("=" * 70)

if not mt5.initialize():
    print("MT5 连接失败")
    mt5.shutdown()
    sys.exit(1)

# 获取账户信息
account_info = mt5.account_info()

if account_info is None:
    print("无法获取账户信息")
    mt5.shutdown()
    sys.exit(1)

print(f"\n账户号码：{account_info.login}")
print(f"服务器：{account_info.server}")
print(f"货币：{account_info.currency}")
print(f"余额：${account_info.balance:.2f}")
print(f"净值：${account_info.equity:.2f}")
print(f"保证金：${account_info.margin:.2f}")
print(f"可用保证金：${account_info.margin_free:.2f}")
print(f"保证金水平：{account_info.margin_level:.2f}%")
print(f"杠杆：1:{account_info.leverage}")
print(f"持仓数量：{account_info.positions}")
print(f"总盈亏：${account_info.profit:.2f}")

mt5.shutdown()

print("\n" + "=" * 70)
