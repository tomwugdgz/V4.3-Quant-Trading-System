"""
MT5 工具库 - 统一调用接口
命令行快速调用各种 MT5 功能
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

def show_help():
    """显示帮助信息"""
    print("""
╔══════════════════════════════════════════════════════════╗
║           MT5 工具库 - 快速调用指南                       ║
╠══════════════════════════════════════════════════════════╣
║  用法：python mt5_tool.py <命令> [参数]                   ║
╠══════════════════════════════════════════════════════════╣
║  账户查询                                                 ║
║    balance          - 查询账户余额和持仓                  ║
║                                                             ║
║  开仓交易                                                 ║
║    buy <symbol> <volume> [sl] [tp]  - 开多单             ║
║    sell <symbol> <volume> [sl] [tp] - 开空单             ║
║    示例：buy EURUSD 0.01                                 ║
║    示例：sell XAUUSD 0.1 2000 1950                       ║
║                                                             ║
║  平仓交易                                                 ║
║    close all        - 平掉所有持仓                        ║
║    close <symbol>   - 平掉指定品种持仓                    ║
║    示例：close all                                       ║
║    示例：close EURUSD                                    ║
║                                                             ║
║  市场扫描                                                 ║
║    scan             - 扫描所有市场                        ║
║    scan forex       - 扫描外汇                            ║
║    scan crypto      - 扫描加密货币                        ║
║    opp              - 寻找交易机会                        ║
║                                                             ║
║  其他                                                     ║
║    help             - 显示此帮助信息                       ║
║    status           - 显示 MT5 连接状态                    ║
╚══════════════════════════════════════════════════════════╝
    """)

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        show_help()
    
    elif command == "balance":
        from account_check import check_balance
        check_balance()
    
    elif command == "buy":
        from open_position import buy
        if len(sys.argv) < 4:
            print("用法：buy <symbol> <volume> [sl] [tp]")
            print("示例：buy EURUSD 0.01")
            return
        symbol = sys.argv[2]
        volume = float(sys.argv[3])
        sl = float(sys.argv[4]) if len(sys.argv) > 4 else 0
        tp = float(sys.argv[5]) if len(sys.argv) > 5 else 0
        buy(symbol, volume, sl, tp)
    
    elif command == "sell":
        from open_position import sell
        if len(sys.argv) < 4:
            print("用法：sell <symbol> <volume> [sl] [tp]")
            print("示例：sell XAUUSD 0.1")
            return
        symbol = sys.argv[2]
        volume = float(sys.argv[3])
        sl = float(sys.argv[4]) if len(sys.argv) > 4 else 0
        tp = float(sys.argv[5]) if len(sys.argv) > 5 else 0
        sell(symbol, volume, sl, tp)
    
    elif command == "close":
        from close_position import close_all_positions, close_by_symbol
        if len(sys.argv) < 3:
            print("用法：close <all|symbol>")
            return
        if sys.argv[2].lower() == "all":
            close_all_positions()
        else:
            close_by_symbol(sys.argv[2])
    
    elif command == "scan":
        from market_scan import scan_market
        if len(sys.argv) > 2:
            scan_market([sys.argv[2]])
        else:
            scan_market()
    
    elif command == "opp":
        from market_scan import find_opportunities
        find_opportunities()
    
    elif command == "status":
        import MetaTrader5 as mt5
        if mt5.initialize():
            print("MT5 连接状态：正常")
            account = mt5.account_info()
            if account:
                print(f"账户：{account.login}")
                print(f"服务器：{account.server}")
                print(f"余额：${account.balance:.2f}")
            mt5.shutdown()
        else:
            print("MT5 连接状态：失败")
            print(f"错误：{mt5.last_error()}")
    
    else:
        print(f"未知命令：{command}")
        show_help()

if __name__ == "__main__":
    main()
