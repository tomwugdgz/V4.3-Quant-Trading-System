"""
模拟盘环境检查
版本：V4.3.0
创建：2026-04-11

功能：
1. 检查 Python 环境
2. 检查 MT5 连接
3. 检查配置文件
4. 检查数据库
5. 生成检查报告
"""

import sys
import os
import json
import sqlite3
from datetime import datetime


class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self):
        """初始化"""
        self.results = []
        self.errors = []
        self.warnings = []
    
    def check_python_version(self):
        """检查 Python 版本"""
        print("\n" + "="*80)
        print("检查 Python 环境")
        print("="*80)
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        print(f"Python 版本：{version_str}")
        
        if version.major >= 3 and version.minor >= 8:
            print("[OK] Python 版本符合要求 (>=3.8)")
            self.results.append(("Python 版本", "PASS", version_str))
            return True
        else:
            print("[ERROR] Python 版本过低，需要>=3.8")
            self.results.append(("Python 版本", "FAIL", version_str))
            self.errors.append("Python 版本过低")
            return False
    
    def check_dependencies(self):
        """检查依赖包"""
        print("\n" + "="*80)
        print("检查依赖包")
        print("="*80)
        
        required_packages = [
            'MetaTrader5',
            'pandas',
            'numpy',
            'sqlite3'
        ]
        
        missing = []
        
        for package in required_packages:
            try:
                if package == 'sqlite3':
                    __import__(package)
                else:
                    __import__(package.lower())
                
                print(f"[OK] {package} 已安装")
                self.results.append((package, "PASS", "已安装"))
                
            except ImportError:
                print(f"[ERROR] {package} 未安装")
                missing.append(package)
                self.results.append((package, "FAIL", "未安装"))
                self.errors.append(f"{package} 未安装")
        
        if missing:
            print(f"\n[WARN] 缺少依赖包：{', '.join(missing)}")
            print(f"安装命令：pip install {' '.join(missing)}")
            return False
        
        print("\n[OK] 所有依赖包已安装")
        return True
    
    def check_mt5_connection(self):
        """检查 MT5 连接"""
        print("\n" + "="*80)
        print("检查 MT5 连接")
        print("="*80)
        
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                print("[ERROR] MT5 初始化失败")
                print("请确保：")
                print("  1. MetaTrader 5 已启动")
                print("  2. 账户已登录")
                print("  3. 数据连接正常")
                
                self.results.append(("MT5 连接", "FAIL", "初始化失败"))
                self.errors.append("MT5 连接失败")
                return False
            
            # 获取账户信息
            account_info = mt5.account_info()
            
            if account_info is None:
                print("[ERROR] 无法获取账户信息")
                self.results.append(("MT5 账户", "FAIL", "未登录"))
                self.errors.append("MT5 账户未登录")
                mt5.shutdown()
                return False
            
            print(f"[OK] MT5 已连接")
            print(f"  账户：{account_info.login}")
            print(f"  类型：{'模拟账户' if 'demo' in account_info.server.lower() else '实盘账户'}")
            print(f"  余额：${account_info.balance:.2f}")
            print(f"  杠杆：1:{account_info.leverage}")
            
            self.results.append(("MT5 连接", "PASS", "已连接"))
            self.results.append(("MT5 账户", "PASS", str(account_info.login)))
            
            mt5.shutdown()
            return True
            
        except Exception as e:
            print(f"[ERROR] MT5 检查失败：{e}")
            self.results.append(("MT5 连接", "FAIL", str(e)))
            self.errors.append(f"MT5 检查失败：{e}")
            return False
    
    def check_config_files(self):
        """检查配置文件"""
        print("\n" + "="*80)
        print("检查配置文件")
        print("="*80)
        
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        
        required_configs = [
            'regime_config.json',
            'factor_weights.json',
            'risk_params.json',
            'paper_trading_config.json'
        ]
        
        missing = []
        
        for config in required_configs:
            config_path = os.path.join(config_dir, config)
            
            if os.path.exists(config_path):
                print(f"[OK] {config} 存在")
                
                # 验证 JSON 格式
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    print(f"  [OK] JSON 格式正确")
                    self.results.append((config, "PASS", "存在且有效"))
                except json.JSONDecodeError as e:
                    print(f"  [ERROR] JSON 格式错误：{e}")
                    self.results.append((config, "FAIL", "JSON 格式错误"))
                    self.warnings.append(f"{config} JSON 格式错误")
            else:
                print(f"[ERROR] {config} 不存在")
                missing.append(config)
                self.results.append((config, "FAIL", "不存在"))
                self.errors.append(f"{config} 不存在")
        
        if missing:
            print(f"\n[WARN] 缺少配置文件：{', '.join(missing)}")
            return False
        
        print("\n[OK] 所有配置文件存在且有效")
        return True
    
    def check_database(self):
        """检查数据库"""
        print("\n" + "="*80)
        print("检查数据库")
        print("="*80)
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trading', 'paper_trading.db')
        db_dir = os.path.dirname(db_path)
        
        # 确保目录存在
        os.makedirs(db_dir, exist_ok=True)
        
        print(f"数据库路径：{db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    type TEXT,
                    volume REAL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    exit_price REAL,
                    profit REAL,
                    status TEXT,
                    created_at DATETIME,
                    closed_at DATETIME
                )
            ''')
            
            # 检查表是否创建成功
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            if cursor.fetchone():
                print("[OK] 交易记录表已创建")
                self.results.append(("数据库表", "PASS", "trades 表已创建"))
            else:
                print("[ERROR] 交易记录表创建失败")
                self.results.append(("数据库表", "FAIL", "创建失败"))
                self.errors.append("数据库表创建失败")
                conn.close()
                return False
            
            conn.close()
            print("[OK] 数据库初始化成功")
            self.results.append(("数据库", "PASS", "已初始化"))
            return True
            
        except Exception as e:
            print(f"[ERROR] 数据库检查失败：{e}")
            self.results.append(("数据库", "FAIL", str(e)))
            self.errors.append(f"数据库检查失败：{e}")
            return False
    
    def check_log_directory(self):
        """检查日志目录"""
        print("\n" + "="*80)
        print("检查日志目录")
        print("="*80)
        
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        
        print(f"日志目录：{log_dir}")
        
        # 确保目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        if os.path.exists(log_dir):
            print("[OK] 日志目录存在")
            self.results.append(("日志目录", "PASS", "已创建"))
            return True
        else:
            print("[ERROR] 日志目录创建失败")
            self.results.append(("日志目录", "FAIL", "创建失败"))
            self.errors.append("日志目录创建失败")
            return False
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*80)
        print("环境检查报告")
        print("="*80)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r[1] == "PASS")
        failed = total - passed
        
        print(f"检查时间：{timestamp}")
        print(f"总检查项：{total}")
        print(f"通过：{passed}")
        print(f"失败：{failed}")
        print(f"警告：{len(self.warnings)}")
        print()
        
        print("详细结果:")
        print("-"*80)
        
        for item, status, detail in self.results:
            icon = "[OK]" if status == "PASS" else "[FAIL]"
            print(f"{icon} {item}: {status} ({detail})")
        
        print()
        
        if self.errors:
            print("错误列表:")
            print("-"*80)
            for error in self.errors:
                print(f"[ERROR] {error}")
            print()
        
        if self.warnings:
            print("警告列表:")
            print("-"*80)
            for warning in self.warnings:
                print(f"[WARN] {warning}")
            print()
        
        # 总体评估
        print("="*80)
        if failed == 0 and len(self.warnings) == 0:
            print("[PASS] 环境检查通过，可以启动模拟盘")
        elif failed == 0:
            print("[WARN] 环境检查通过，但有警告，建议修复后启动")
        else:
            print("[FAIL] 环境检查失败，请修复错误后重新启动")
        
        print("="*80)
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 
                                   f'environment_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"环境检查报告 - {timestamp}\n")
            f.write("="*80 + "\n")
            f.write(f"总检查项：{total}\n")
            f.write(f"通过：{passed}\n")
            f.write(f"失败：{failed}\n")
            f.write(f"警告：{len(self.warnings)}\n\n")
            
            for item, status, detail in self.results:
                f.write(f"{status}: {item} ({detail})\n")
            
            if self.errors:
                f.write("\n错误:\n")
                for error in self.errors:
                    f.write(f"- {error}\n")
        
        print(f"\n报告已保存：{report_path}")


def main():
    """主函数"""
    print("="*80)
    print("V4.3 模拟盘环境检查")
    print("="*80)
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checker = EnvironmentChecker()
    
    # 执行检查
    checker.check_python_version()
    checker.check_dependencies()
    checker.check_mt5_connection()
    checker.check_config_files()
    checker.check_database()
    checker.check_log_directory()
    
    # 生成报告
    checker.generate_report()


if __name__ == "__main__":
    main()
