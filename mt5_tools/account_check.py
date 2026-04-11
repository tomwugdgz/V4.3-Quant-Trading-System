"""
MT5 账户查询工具
查询账户余额、净值、持仓等信息
"""

import sys
sys.path.insert(0, str(Path(__file__).parent))

from base import initialize, shutdown, get_account_info, get_positions, save_result
from datetime import datetime
from pathlib import Path

def check_balance():
    """查询账户余额"""
    print("=" * 70)
    print("MT5 账户余额查询")
    print("=" * 70)
    
    if not initialize():
        return None
    
    account = get_account_info()
    if not account:
        print("获取账户信息失败")
        shutdown()
        return None
    
    # 打印账户信息
    print(f"\n账户信息")
    print("=" * 70)
    print(f"账户号码：{account['login']}")
    print(f"服务器：{account['server']}")
    print(f"货币：{account['currency']}")
    print(f"杠杆：1:{account['leverage']}")
    print("=" * 70)
    
    # 打印资金状况
    print(f"\n资金状况")
    print("=" * 70)
    print(f"余额 (Balance): ${account['balance']:.2f}")
    print(f"净值 (Equity): ${account['equity']:.2f}")
    print(f"预付款 (Margin): ${account['margin']:.2f}")
    print(f"可用资金 (Margin Free): ${account['margin_free']:.2f}")
    print("=" * 70)
    
    # 打印盈亏
    print(f"\n盈亏统计")
    print("=" * 70)
    print(f"浮动盈亏：${account['profit']:.2f}")
    print(f"初始资金：$10,000.00")
    print(f"收益率：{(account['equity'] - 10000) / 10000 * 100:.2f}%")
    print("=" * 70)
    
    # 获取持仓
    positions = get_positions()
    if positions:
        print(f"\n当前持仓：{len(positions)} 个")
        print("=" * 70)
        for pos in positions:
            print(f"{pos['symbol']}: {pos['volume']}手 {pos['type']} @ {pos['price_open']} -> 盈亏：${pos['total_profit']:.2f}")
        print("=" * 70)
    else:
        print(f"\n当前无持仓")
    
    # 保存结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "account": account,
        "positions": positions,
        "positions_count": len(positions)
    }
    
    save_result(result, f"account-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    
    shutdown()
    print(f"\n查询完成！")
    
    return result

if __name__ == "__main__":
    check_balance()
