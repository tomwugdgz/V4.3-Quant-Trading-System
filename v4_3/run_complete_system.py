"""
V4.3 系统主运行脚本
版本：V4.3.0
创建：2026-04-11

功能：
1. 整合所有模块
2. 完整交易流程
3. 测试和验证
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# 添加路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'factors'))
sys.path.insert(0, os.path.join(base_dir, 'v4_3'))

from market_regime import MarketRegimeAgent
from factor_score import FactorScoreEngine
from risk_agent import RiskAgent
from review_agent import ReviewAgent
from config_loader import ConfigLoader
from parameter_robustness import ParameterRobustnessTester
from oos_validation import OOSValidator

from momentum import MomentumFactor
from mean_reversion import MeanReversionFactor
from breakout import BreakoutFactor
from volatility import VolatilityFactor


class V43CompleteSystem:
    """V4.3 完整系统"""
    
    def __init__(self):
        """初始化"""
        self.config_loader = ConfigLoader()
        self.regime_agent = MarketRegimeAgent()
        self.factor_engine = FactorScoreEngine()
        self.risk_agent = RiskAgent()
        self.review_agent = ReviewAgent()
        
        self.robustness_tester = ParameterRobustnessTester()
        self.oos_validator = OOSValidator()
        
        self.symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"]
    
    def initialize(self) -> bool:
        """初始化 MT5"""
        if not mt5.initialize():
            print("[ERROR] MT5 初始化失败")
            return False
        
        print("[OK] MT5 初始化成功")
        return True
    
    def scan_and_trade(self) -> dict:
        """
        扫描市场并执行交易
        
        Returns:
            dict: 扫描结果
        """
        print("=" * 80)
        print(f"V4.3 市场扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        opportunities = []
        
        for symbol in self.symbols:
            # 1. 判断市场状态
            regime = self.regime_agent.detect_regime(symbol, "H1")
            
            if not self.regime_agent.should_trade(regime):
                print(f"\n{symbol}: [SKIP] {regime.value} - 不交易")
                continue
            
            # 2. 计算因子评分
            factor_result = self.factor_engine.calculate_score(symbol, "H1")
            score = factor_result['score']
            signal = factor_result['signal']
            
            # 3. 获取动态阈值
            threshold = self.regime_agent.get_dynamic_threshold(regime)
            
            # 4. 判断是否达标
            signal_strength = (score - 50) / 200  # 转换为百分比
            is_strong_signal = signal_strength >= threshold / 100
            
            print(f"\n{symbol}:")
            print(f"  市场状态：{regime.value}")
            print(f"  信号阈值：{threshold:.2f}%")
            print(f"  因子评分：{score:.1f}")
            print(f"  信号强度：{signal_strength:.3f}%")
            print(f"  交易信号：{signal}")
            
            if is_strong_signal:
                print(f"  [OK] 达标信号")
                
                # 5. 风控检查
                if self.risk_agent.can_trade(symbol, signal):
                    print(f"  [OK] 风控通过")
                    
                    opportunities.append({
                        'symbol': symbol,
                        'signal': signal,
                        'score': score,
                        'regime': regime.value,
                        'timestamp': datetime.now()
                    })
                else:
                    print(f"  [SKIP] 风控不通过")
            else:
                print(f"  [SKIP] 信号不足")
        
        print("\n" + "=" * 80)
        print(f"扫描完成，发现 {len(opportunities)} 个交易机会")
        print("=" * 80)
        
        return {
            'timestamp': datetime.now(),
            'opportunities': opportunities,
            'total_scanned': len(self.symbols)
        }
    
    def run_robustness_test(self, results: list) -> dict:
        """
        运行鲁棒性测试
        
        Args:
            results: 回测结果列表
            
        Returns:
            dict: 测试结果
        """
        print("\n" + "=" * 80)
        print("参数鲁棒性测试")
        print("=" * 80)
        
        robustness = self.robustness_tester.test_robustness(results)
        
        print(f"\n鲁棒性评分：{robustness['robustness_score']:.3f}")
        print(f"是否通过：{'✅ PASS' if robustness['passed'] else '❌ FAIL'}")
        print(f"\n建议:\n{robustness['recommendation']}")
        
        return robustness
    
    def run_oos_validation(self, train_result: dict, test_result: dict) -> dict:
        """
        运行 OOS 验证
        
        Args:
            train_result: 训练集结果
            test_result: 测试集结果
            
        Returns:
            dict: 验证结果
        """
        print("\n" + "=" * 80)
        print("样本外验证（OOS）")
        print("=" * 80)
        
        oos_result = self.oos_validator.validate(train_result, test_result)
        
        oos_perf = oos_result['oos_performance']
        print(f"\n训练集夏普：{oos_perf['train_sharpe']:.2f}")
        print(f"测试集夏普：{oos_perf['test_sharpe']:.2f}")
        print(f"夏普衰减：{oos_perf['sharpe_decay']:.2%}")
        print(f"OOS 评分：{oos_perf['oos_score']:.3f}")
        print(f"是否过拟合：{'是' if oos_perf['is_overfitted'] else '否'}")
        print(f"是否通过：{'✅ PASS' if oos_perf['passed'] else '❌ FAIL'}")
        
        print(f"\n建议:\n{oos_result['recommendation']}")
        
        return oos_result
    
    def generate_daily_report(self) -> str:
        """
        生成每日报告
        
        Returns:
            str: 报告内容
        """
        report = self.review_agent.generate_daily_report()
        
        print("\n" + "=" * 80)
        print("每日复盘报告")
        print("=" * 80)
        print(report)
        
        return report
    
    def shutdown(self):
        """关闭系统"""
        mt5.shutdown()
        print("\n[OK] 系统已关闭")


def main():
    """主函数"""
    print("=" * 80)
    print("V4.3 完整系统测试")
    print("=" * 80)
    print(f"运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建系统
    system = V43CompleteSystem()
    
    # 初始化
    if not system.initialize():
        print("[ERROR] 系统初始化失败")
        return
    
    try:
        # 1. 市场扫描
        scan_result = system.scan_and_trade()
        
        # 2. 模拟鲁棒性测试
        print("\n" + "=" * 80)
        print("模拟鲁棒性测试（使用模拟数据）")
        print("=" * 80)
        
        # 生成模拟回测结果
        np.random.seed(42)
        mock_results = [
            {
                'ema_fast': np.random.randint(8, 13),
                'ema_slow': np.random.randint(18, 23),
                'signal_threshold': np.random.choice([0.06, 0.08, 0.10, 0.12]),
                'stop_loss_atr': np.random.choice([1.2, 1.5, 1.8, 2.0]),
                'sharpe': np.random.normal(1.5, 0.3),
                'total_return': np.random.normal(0.15, 0.05),
                'max_drawdown': np.random.normal(-0.10, 0.03)
            }
            for _ in range(100)
        ]
        
        robustness_result = system.run_robustness_test(mock_results)
        
        # 3. 模拟 OOS 验证
        mock_train_result = {
            'sharpe': 2.0,
            'total_return': 0.25,
            'max_drawdown': -0.10
        }
        
        mock_test_result = {
            'sharpe': 1.5,
            'total_return': 0.18,
            'max_drawdown': -0.12
        }
        
        oos_result = system.run_oos_validation(mock_train_result, mock_test_result)
        
        # 4. 生成每日报告
        report = system.generate_daily_report()
        
        # 5. 总结
        print("\n" + "=" * 80)
        print("V4.3 系统测试总结")
        print("=" * 80)
        print(f"市场扫描：{scan_result['total_scanned']} 个品种，{len(scan_result['opportunities'])} 个机会")
        print(f"鲁棒性测试：{'✅ PASS' if robustness_result['passed'] else '❌ FAIL'}")
        print(f"OOS 验证：{'✅ PASS' if oos_result['oos_performance']['passed'] else '❌ FAIL'}")
        print(f"每日报告：已生成")
        
    except Exception as e:
        print(f"\n[ERROR] 系统运行出错：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭系统
        system.shutdown()


if __name__ == "__main__":
    main()
