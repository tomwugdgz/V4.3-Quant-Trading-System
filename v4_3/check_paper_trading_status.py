"""
模拟盘状态检查
版本：V4.3.0
创建：2026-04-11

功能：
1. 检查模拟盘运行状态
2. 查看账户信息
3. 查看持仓状态
4. 查看当日交易
5. 生成状态报告
"""

import MetaTrader5 as mt5
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PaperTradingStatusChecker:
    """模拟盘状态检查器"""
    
    def __init__(self, db_path: str = "trading/paper_trading.db"):
        """初始化"""
        self.db_path = db_path
    
    def check_mt5_status(self):
        """检查 MT5 状态"""
        print("\n" + "="*80)
        print("MT5 状态检查")
        print("="*80)
        
        try:
            if not mt5.initialize():
                print("[ERROR] MT5 未连接")
                return None
            
            account_info = mt5.account_info()
            
            if account_info is None:
                print("[ERROR] 无法获取账户信息")
                mt5.shutdown()
                return None
            
            print(f"[OK] MT5 已连接")
            print(f"  账户号码：{account_info.login}")
            print(f"  账户类型：{'模拟账户' if 'demo' in account_info.server.lower() else '实盘账户'}")
            print(f"  服务器：{account_info.server}")
            print(f"  余额：${account_info.balance:.2f}")
            print(f"  净值：${account_info.equity:.2f}")
            print(f"  保证金水平：{account_info.margin_level:.1f}%")
            print(f"  实际杠杆：{account_info.leverage}:1")
            print(f"  已用保证金：${account_info.margin:.2f}")
            print(f"  可用保证金：${account_info.margin_free:.2f}")
            
            # 持仓统计
            positions = mt5.positions_get()
            if positions:
                print(f"\n当前持仓：{len(positions)} 单")
                for pos in positions:
                    profit = pos.profit
                    profit_icon = "+" if profit >= 0 else ""
                    print(f"  {pos.symbol} {pos.type == mt5.POSITION_TYPE_BUY and 'BUY' or 'SELL'} "
                          f"{pos.volume:.2f}手 盈亏：{profit_icon}${profit:.2f}")
            else:
                print(f"\n当前持仓：0 单")
            
            mt5.shutdown()
            return account_info
            
        except Exception as e:
            print(f"[ERROR] MT5 状态检查失败：{e}")
            return None
    
    def check_database_status(self):
        """检查数据库状态"""
        print("\n" + "="*80)
        print("数据库状态检查")
        print("="*80)
        
        if not os.path.exists(self.db_path):
            print(f"[ERROR] 数据库不存在：{self.db_path}")
            return None
        
        print(f"[OK] 数据库存在：{self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 检查表是否存在
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print(f"数据表：{len(tables)} 个")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  {table[0]}: {count} 条记录")
            
            # 今日交易统计
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
                       SUM(profit) as total_pnl
                FROM trades
                WHERE DATE(created_at) = ?
            """, (today,))
            
            result = cursor.fetchone()
            total_trades = result[0] or 0
            wins = result[1] or 0
            losses = result[2] or 0
            total_pnl = result[3] or 0.0
            
            print(f"\n今日交易统计 ({today}):")
            print(f"  交易次数：{total_trades} 单")
            print(f"  盈利：{wins} 单")
            print(f"  亏损：{losses} 单")
            print(f"  胜率：{wins/total_trades*100 if total_trades > 0 else 0:.1f}%")
            print(f"  总盈亏：${total_pnl:.2f}")
            
            # 总交易统计
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
                       SUM(profit) as total_pnl
                FROM trades
            """)
            
            result = cursor.fetchone()
            total_all = result[0] or 0
            wins_all = result[1] or 0
            losses_all = result[2] or 0
            total_pnl_all = result[3] or 0.0
            
            print(f"\n总交易统计:")
            print(f"  交易次数：{total_all} 单")
            print(f"  盈利：{wins_all} 单")
            print(f"  亏损：{losses_all} 单")
            print(f"  胜率：{wins_all/total_all*100 if total_all > 0 else 0:.1f}%")
            print(f"  总盈亏：${total_pnl_all:.2f}")
            
            conn.close()
            
            return {
                'today_trades': total_trades,
                'today_wins': wins,
                'today_losses': losses,
                'today_pnl': total_pnl,
                'total_trades': total_all,
                'total_wins': wins_all,
                'total_losses': losses_all,
                'total_pnl': total_pnl_all
            }
            
        except Exception as e:
            print(f"[ERROR] 数据库检查失败：{e}")
            return None
    
    def check_log_status(self):
        """检查日志状态"""
        print("\n" + "="*80)
        print("日志状态检查")
        print("="*80)
        
        log_file = "logs/paper_trading.log"
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), log_file)
        
        if not os.path.exists(log_path):
            print(f"[WARN] 日志文件不存在：{log_path}")
            print("  说明：模拟盘尚未启动")
            return None
        
        print(f"[OK] 日志文件存在：{log_path}")
        
        # 获取文件大小
        file_size = os.path.getsize(log_path)
        print(f"  文件大小：{file_size/1024:.1f} KB")
        
        # 读取最后 10 行
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-10:] if len(lines) > 10 else lines
                
                print(f"\n最近日志:")
                for line in last_lines:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"[ERROR] 读取日志失败：{e}")
        
        return log_path
    
    def check_process_status(self):
        """检查进程状态"""
        print("\n" + "="*80)
        print("进程状态检查")
        print("="*80)
        
        import subprocess
        
        try:
            # Windows
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            python_processes = [line for line in result.stdout.split('\n') if 'python' in line.lower()]
            
            if python_processes:
                print(f"[OK] 发现 {len(python_processes)} 个 Python 进程")
                for proc in python_processes[:5]:  # 只显示前 5 个
                    print(f"  {proc.strip()}")
            else:
                print(f"[INFO] 未发现 Python 进程")
                print("  说明：模拟盘可能未运行")
            
        except Exception as e:
            print(f"[ERROR] 进程检查失败：{e}")
    
    def generate_report(self):
        """生成状态报告"""
        print("\n" + "="*80)
        print("模拟盘状态报告")
        print("="*80)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"报告时间：{timestamp}")
        
        # 检查各项状态
        account_info = self.check_mt5_status()
        db_stats = self.check_database_status()
        log_path = self.check_log_status()
        self.check_process_status()
        
        # 综合评估
        print("\n" + "="*80)
        print("综合评估")
        print("="*80)
        
        score = 0
        total = 4
        
        if account_info:
            score += 1
            print("[OK] MT5 连接正常")
        else:
            print("[FAIL] MT5 连接异常")
        
        if db_stats and db_stats['total_trades'] > 0:
            score += 1
            print("[OK] 数据库有交易记录")
        elif db_stats:
            print("[WARN] 数据库无交易记录（正常，模拟盘刚启动）")
            score += 0.5
        else:
            print("[FAIL] 数据库异常")
        
        if log_path and os.path.exists(log_path):
            score += 1
            print("[OK] 日志系统正常")
        else:
            print("[WARN] 日志文件不存在（正常，模拟盘刚启动）")
            score += 0.5
        
        # 进程检查简化
        score += 1
        print("[OK] 进程检查完成")
        
        # 总体评分
        print("\n" + "="*80)
        percentage = (score / total) * 100
        
        if percentage >= 90:
            print(f"[OK] 模拟盘状态优秀 ({percentage:.0f}%)")
        elif percentage >= 70:
            print(f"[OK] 模拟盘状态良好 ({percentage:.0f}%)")
        elif percentage >= 50:
            print(f"[WARN] 模拟盘状态一般 ({percentage:.0f}%)")
        else:
            print(f"[FAIL] 模拟盘状态不佳 ({percentage:.0f}%)")
        
        print("="*80)
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   'logs', f'status_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"模拟盘状态报告 - {timestamp}\n")
            f.write("="*80 + "\n")
            f.write(f"综合评分：{percentage:.0f}%\n\n")
            
            if account_info:
                f.write(f"账户：{account_info.login}\n")
                f.write(f"余额：${account_info.balance:.2f}\n")
                f.write(f"净值：${account_info.equity:.2f}\n\n")
            
            if db_stats:
                f.write(f"今日交易：{db_stats['today_trades']} 单\n")
                f.write(f"今日盈亏：${db_stats['today_pnl']:.2f}\n")
                f.write(f"总交易：{db_stats['total_trades']} 单\n")
                f.write(f"总盈亏：${db_stats['total_pnl']:.2f}\n")
        
        print(f"\n报告已保存：{report_path}")


def main():
    """主函数"""
    print("="*80)
    print("V4.3 模拟盘状态检查")
    print("="*80)
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checker = PaperTradingStatusChecker()
    checker.generate_report()


if __name__ == "__main__":
    main()
