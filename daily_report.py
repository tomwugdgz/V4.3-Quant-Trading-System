"""
每日账户状态汇报
自动查询账户余额、持仓、盈亏，并生成汇报
"""

import sys
sys.path.insert(0, 'mt5_tools')

from base import initialize, shutdown, get_account_info, get_positions
from datetime import datetime

def daily_report():
    """生成每日账户汇报"""
    print("=" * 70)
    print("MT5 每日账户汇报")
    print("=" * 70)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if not initialize():
        print("❌ MT5 初始化失败")
        return
    
    # 获取账户信息
    account = get_account_info()
    if not account:
        print("❌ 获取账户信息失败")
        shutdown()
        return
    
    # 账户基本信息
    print(f"\n[账户信息]")
    print(f"账户号码：{account.get('login', 'N/A')}")
    print(f"账户类型：{account.get('server', 'N/A')}")
    print(f"货币：{account.get('currency', 'USD')}")
    print(f"杠杆：1:{account.get('leverage', 1)}")
    
    # 资金信息
    print(f"\n[资金状况]")
    balance = account.get('balance', 0)
    equity = account.get('equity', 0)
    profit = equity - balance
    
    print(f"余额：${balance:.2f}")
    print(f"净值：${equity:.2f}")
    print(f"浮动盈亏：${profit:.2f} ({profit/balance*100:.2f}%)")
    
    # 保证金使用
    margin_used = account.get('margin', 0)
    margin_free = account.get('margin_free', 0)
    margin_level = account.get('margin_level', 0)
    
    print(f"\n[保证金使用]")
    print(f"已用保证金：${margin_used:.2f}")
    print(f"可用保证金：${margin_free:.2f}")
    print(f"保证金水平：{margin_level:.2f}%")
    
    # 持仓情况
    positions = get_positions()
    
    print(f"\n[当前持仓] ({len(positions)} 单)")
    print("=" * 70)
    
    if not positions:
        print("无持仓")
    else:
        total_profit = 0
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            type_str = "BUY  " if pos.get('type') == 0 else "SELL "
            volume = pos.get('volume', 0)
            price_open = pos.get('price_open', 0)
            profit_val = pos.get('profit', 0)
            total_profit += profit_val
            
            status = "[+]" if profit_val > 0 else "[-]" if profit_val < 0 else "[0]"
            
            print(f"{status} {symbol} {type_str} {volume:.2f}手 @ {price_open:.5f}  盈亏：${profit_val:.2f}")
        
        print("-" * 70)
        print(f"合计浮动盈亏：${total_profit:.2f}")
    
    # 交易统计
    print(f"\n[今日统计]")
    print("=" * 70)
    
    # 计算初始资金 (假设 $10,000)
    initial_capital = 10000
    total_pnl = equity - initial_capital
    
    print(f"初始资金：${initial_capital:.2f}")
    print(f"当前净值：${equity:.2f}")
    print(f"总盈亏：${total_pnl:.2f} ({total_pnl/initial_capital*100:.2f}%)")
    print(f"持仓数量：{len(positions)} 单")
    
    # 风险提示
    print(f"\n[风险状态]")
    print("=" * 70)
    
    if margin_level < 200:
        print("[!] 保证金水平过低 (<200%)，注意风险！")
    elif margin_level < 300:
        print("[*] 保证金水平偏低 (<300%)，谨慎开仓")
    else:
        print("[OK] 保证金水平安全")
    
    leverage = equity / margin_used if margin_used > 0 else 0
    if leverage > 3:
        print(f"[!] 实际杠杆过高 ({leverage:.2f}x > 3x)")
    elif leverage > 2:
        print(f"[*] 实际杠杆偏高 ({leverage:.2f}x)")
    else:
        print(f"[OK] 实际杠杆安全 ({leverage:.2f}x)")
    
    shutdown()
    print("\n" + "=" * 70)
    print("汇报完成")
    print("=" * 70)

if __name__ == "__main__":
    daily_report()
