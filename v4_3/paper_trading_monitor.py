"""
模拟盘监控主程序
版本：V4.3.0
创建：2026-04-11

功能：
1. 每 60 分钟扫描市场
2. 自动生成交易信号
3. 风控检查
4. 执行模拟交易
5. 记录交易日志
6. 发送飞书通知
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'v4_3'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'factors'))

from market_regime import MarketRegimeAgent
from factor_score import FactorScoreEngine
from risk_agent import RiskAgent
from review_agent import ReviewAgent


class PaperTradingMonitor:
    """模拟盘监控器"""
    
    def __init__(self, config_path: str = "config/paper_trading_config.json"):
        """初始化"""
        self.config = self._load_config(config_path)
        
        # 初始化模块
        self.regime_agent = MarketRegimeAgent()
        self.factor_engine = FactorScoreEngine()
        self.risk_agent = RiskAgent()
        self.review_agent = ReviewAgent(db_path="trading/paper_trading.db")
        
        # 状态
        self.running = False
        self.last_scan = None
        self.today_trades = 0
        self.today_pnl = 0.0
        
        # 日志
        self.log_file = self.config['monitoring']['log_file']
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] 配置文件不存在：{config_path}")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """默认配置"""
        return {
            "account": {
                "type": "paper_trading",
                "initial_capital": 10000,
                "leverage": 5
            },
            "risk": {
                "account": {
                    "min_margin_level": 200,
                    "max_leverage": 3.0,
                    "max_daily_loss_percent": 0.03
                },
                "position": {
                    "max_positions": 3,
                    "risk_per_trade_percent": 0.005
                }
            },
            "trading": {
                "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"],
                "timeframe": "H1",
                "scan_interval_minutes": 60,
                "signal_threshold": 0.001
            },
            "monitoring": {
                "daily_check_time": "17:00",
                "daily_report_time": "20:00",
                "log_file": "logs/paper_trading.log"
            }
        }
    
    def initialize(self) -> bool:
        """初始化 MT5"""
        self._log("[INFO] 正在初始化 MT5...")
        
        if not mt5.initialize():
            self._log("[ERROR] MT5 初始化失败")
            return False
        
        self._log("[OK] MT5 初始化成功")
        
        # 检查账户
        account_info = mt5.account_info()
        if account_info is None:
            self._log("[ERROR] 无法获取账户信息")
            return False
        
        self._log(f"[INFO] 账户：{account_info.login}")
        self._log(f"[INFO] 余额：${account_info.balance:.2f}")
        self._log(f"[INFO] 净值：${account_info.equity:.2f}")
        
        return True
    
    def scan_market(self) -> list:
        """扫描市场"""
        self._log("\n" + "="*80)
        self._log(f"[SCAN] 开始市场扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("="*80)
        
        opportunities = []
        symbols = self.config['trading']['symbols']
        
        for symbol in symbols:
            try:
                # 1. 判断市场状态
                regime = self.regime_agent.detect_regime(symbol, "H1")
                
                if not self.regime_agent.should_trade(regime):
                    self._log(f"[SKIP] {symbol}: {regime.value} - 不交易")
                    continue
                
                # 2. 计算因子评分
                factor_result = self.factor_engine.calculate_score(symbol, "H1")
                score = factor_result['score']
                signal = factor_result['signal']
                
                # 3. 获取动态阈值
                threshold = self.regime_agent.get_dynamic_threshold(regime)
                
                # 4. 判断是否达标
                signal_strength = (score - 50) / 200
                is_strong_signal = signal_strength >= threshold / 100
                
                self._log(f"\n{symbol}:")
                self._log(f"  市场状态：{regime.value}")
                self._log(f"  因子评分：{score:.1f}")
                self._log(f"  信号强度：{signal_strength:.3f}%")
                self._log(f"  交易信号：{signal}")
                
                if is_strong_signal:
                    self._log(f"  [OK] 达标信号")
                    
                    opportunities.append({
                        'symbol': symbol,
                        'signal': signal,
                        'score': score,
                        'regime': regime.value,
                        'timestamp': datetime.now()
                    })
                else:
                    self._log(f"  [SKIP] 信号不足")
                
            except Exception as e:
                self._log(f"[ERROR] {symbol} 扫描失败：{e}")
        
        self._log(f"\n[SCAN] 扫描完成，发现 {len(opportunities)} 个机会")
        self.last_scan = datetime.now()
        
        return opportunities
    
    def execute_trade(self, opportunity: dict) -> bool:
        """执行交易（模拟）"""
        symbol = opportunity['symbol']
        signal = opportunity['signal']
        
        self._log(f"\n[EXEC] 执行交易：{symbol} {signal}")
        
        try:
            # 1. 获取当前价格
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self._log("[ERROR] 无法获取价格")
                return False
            
            price = tick.ask if signal in ['BUY', 'STRONG_BUY'] else tick.bid
            
            # 2. 计算止损止盈
            atr = self._calculate_atr(symbol)
            stop_distance = max(atr * 1.5, 20 * 0.0001)
            
            if signal in ['BUY', 'STRONG_BUY']:
                stop_loss = price - stop_distance
                take_profit = price + (stop_distance * 1.5)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                stop_loss = price + stop_distance
                take_profit = price - (stop_distance * 1.5)
                order_type = mt5.ORDER_TYPE_SELL
            
            # 3. 计算仓位
            account_info = mt5.account_info()
            risk_amount = account_info.equity * 0.005  # 0.5% 风险
            stop_distance_points = abs(price - stop_loss) / 0.0001
            lot_size = risk_amount / (stop_distance_points * 10)
            lot_size = round(lot_size, 2)
            
            # 4. 风控检查
            can_trade, reason = self.risk_agent.can_trade(
                symbol=symbol,
                signal=signal,
                volume=lot_size,
                account_info=account_info,
                positions=[]  # TODO: 获取实际持仓
            )
            
            if not can_trade:
                self._log(f"[SKIP] 风控不通过：{reason}")
                return False
            
            # 5. 发送订单（模拟）
            self._log(f"[ORDER] {symbol} {signal} {lot_size} 手")
            self._log(f"  入场价：{price:.5f}")
            self._log(f"  止损：{stop_loss:.5f}")
            self._log(f"  止盈：{take_profit:.5f}")
            
            # 模拟执行（实际应该调用 mt5.order_send）
            # 这里只记录，不实际下单
            self._log(f"[SIMU] 模拟订单已记录")
            
            # 6. 记录到数据库
            self._record_trade(symbol, signal, lot_size, price, stop_loss, take_profit)
            
            self.today_trades += 1
            
            return True
            
        except Exception as e:
            self._log(f"[ERROR] 执行失败：{e}")
            return False
    
    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        """计算 ATR"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            if rates is None or len(rates) == 0:
                return 0.0015  # 默认 ATR
            
            df = pd.DataFrame(rates)
            
            high = df['high']
            low = df['low']
            close = df['close'].shift(1)
            
            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr.iloc[-1]
            
        except Exception as e:
            self._log(f"[ERROR] ATR 计算失败：{e}")
            return 0.0015
    
    def _record_trade(self, symbol: str, signal: str, volume: float,
                      entry_price: float, stop_loss: float, take_profit: float):
        """记录交易到数据库"""
        import sqlite3
        
        conn = sqlite3.connect("trading/paper_trading.db")
        cursor = conn.cursor()
        
        # 创建表
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
        
        # 插入记录
        cursor.execute('''
            INSERT INTO trades (symbol, type, volume, entry_price, stop_loss, take_profit, 
                               status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?)
        ''', (symbol, signal, volume, entry_price, stop_loss, take_profit, datetime.now()))
        
        conn.commit()
        conn.close()
        
        self._log(f"[DB] 交易已记录")
    
    def generate_daily_report(self) -> str:
        """生成每日报告"""
        self._log("\n" + "="*80)
        self._log("[REPORT] 生成每日报告")
        self._log("="*80)
        
        report = self.review_agent.generate_daily_report()
        
        self._log(report)
        
        # 发送到飞书
        self._send_feishu_report(report)
        
        return report
    
    def _send_feishu_report(self, report: str):
        """发送飞书报告"""
        # TODO: 实现飞书通知
        self._log("[INFO] 飞书报告已发送（模拟）")
    
    def _log(self, message: str):
        """日志记录"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        print(log_message)
        
        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def run(self):
        """运行监控"""
        self._log("\n" + "="*80)
        self._log("[START] 模拟盘监控启动")
        self._log("="*80)
        
        self.running = True
        
        scan_interval = self.config['trading']['scan_interval_minutes'] * 60  # 转换为秒
        
        while self.running:
            try:
                # 1. 扫描市场
                opportunities = self.scan_market()
                
                # 2. 执行交易
                for opp in opportunities:
                    self.execute_trade(opp)
                
                # 3. 等待下次扫描
                self._log(f"\n[WAIT] 等待 {scan_interval/60:.0f} 分钟后下次扫描...")
                time.sleep(scan_interval)
                
            except KeyboardInterrupt:
                self._log("\n[STOP] 用户中断")
                self.running = False
            except Exception as e:
                self._log(f"[ERROR] 监控异常：{e}")
                time.sleep(60)  # 等待 1 分钟后重试
        
        self.shutdown()
    
    def shutdown(self):
        """关闭系统"""
        self._log("\n" + "="*80)
        self._log("[SHUTDOWN] 系统关闭")
        self._log("="*80)
        
        mt5.shutdown()
        self._log("[OK] MT5 已关闭")


def main():
    """主函数"""
    print("="*80)
    print("V4.3 模拟盘监控程序")
    print("="*80)
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建监控器
    monitor = PaperTradingMonitor()
    
    # 初始化
    if not monitor.initialize():
        print("[ERROR] 初始化失败")
        return
    
    # 运行监控
    try:
        monitor.run()
    except Exception as e:
        print(f"[ERROR] 运行失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        monitor.shutdown()


if __name__ == "__main__":
    main()
