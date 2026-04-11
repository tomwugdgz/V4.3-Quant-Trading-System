"""
V4.3 系统完整性测试
版本：V4.3.0
创建：2026-04-11

功能：
1. 测试所有模块导入
2. 测试核心功能
3. 生成测试报告
"""

import sys
import os
import json
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'factors'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'v4_3'))


class V43SystemTester:
    """V4.3 系统测试器"""
    
    def __init__(self):
        """初始化"""
        self.test_results = []
        self.errors = []
    
    def log_test(self, name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        self.test_results.append({
            'name': name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
        
        if message:
            print(f"       {message}")
        
        if not passed:
            self.errors.append(f"{name}: {message}")
    
    def test_module_imports(self):
        """测试模块导入"""
        print("\n" + "=" * 80)
        print("测试模块导入")
        print("=" * 80)
        
        # 测试因子库导入
        try:
            from factors.momentum import MomentumFactor
            from factors.mean_reversion import MeanReversionFactor
            from factors.breakout import BreakoutFactor
            from factors.volatility import VolatilityFactor
            self.log_test("因子库导入", True)
        except Exception as e:
            self.log_test("因子库导入", False, str(e))
        
        # 测试核心模块导入
        try:
            from v4_3.market_regime import MarketRegimeAgent
            self.log_test("Market Regime 导入", True)
        except Exception as e:
            self.log_test("Market Regime 导入", False, str(e))
        
        try:
            from v4_3.factor_score import FactorScoreEngine
            self.log_test("Factor Score 导入", True)
        except Exception as e:
            self.log_test("Factor Score 导入", False, str(e))
        
        try:
            from v4_3.risk_agent import RiskAgent
            self.log_test("Risk Agent 导入", True)
        except Exception as e:
            self.log_test("Risk Agent 导入", False, str(e))
        
        try:
            from v4_3.review_agent import ReviewAgent
            self.log_test("Review Agent 导入", True)
        except Exception as e:
            self.log_test("Review Agent 导入", False, str(e))
        
        try:
            from v4_3.config_loader import ConfigLoader
            self.log_test("Config Loader 导入", True)
        except Exception as e:
            self.log_test("Config Loader 导入", False, str(e))
    
    def test_factor_calculations(self):
        """测试因子计算"""
        print("\n" + "=" * 80)
        print("测试因子计算")
        print("=" * 80)
        
        try:
            import pandas as pd
            import numpy as np
            
            # 生成测试数据
            np.random.seed(42)
            n_periods = 100
            dates = pd.date_range(start='2026-04-01', periods=n_periods, freq='H')
            close = 1.1000 + np.cumsum(np.random.randn(n_periods) * 0.001)
            high = close + np.abs(np.random.randn(n_periods) * 0.0005)
            low = close - np.abs(np.random.randn(n_periods) * 0.0005)
            open_price = close.shift(1).fillna(close.iloc[0])
            volume = np.random.randint(100, 1000, n_periods)
            
            df = pd.DataFrame({
                'time': dates,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
            
            # 测试各因子
            from factors.momentum import MomentumFactor
            from factors.mean_reversion import MeanReversionFactor
            from factors.breakout import BreakoutFactor
            from factors.volatility import VolatilityFactor
            
            # 动量因子
            momentum = MomentumFactor()
            result = momentum.calculate_score(df)
            assert 0 <= result['total_score'] <= 100
            self.log_test("动量因子计算", True, f"评分：{result['total_score']:.1f}")
            
            # 均值回归因子
            mean_rev = MeanReversionFactor()
            result = mean_rev.calculate_score(df)
            assert 0 <= result['total_score'] <= 100
            self.log_test("均值回归因子计算", True, f"评分：{result['total_score']:.1f}")
            
            # 突破因子
            breakout = BreakoutFactor()
            result = breakout.calculate_score(df)
            assert 0 <= result['total_score'] <= 100
            self.log_test("突破因子计算", True, f"评分：{result['total_score']:.1f}")
            
            # 波动率因子
            volatility = VolatilityFactor()
            result = volatility.calculate_score(df)
            assert 0 <= result['total_score'] <= 100
            self.log_test("波动率因子计算", True, f"评分：{result['total_score']:.1f}")
            
        except Exception as e:
            self.log_test("因子计算", False, str(e))
    
    def test_config_loader(self):
        """测试配置加载器"""
        print("\n" + "=" * 80)
        print("测试配置加载器")
        print("=" * 80)
        
        try:
            from v4_3.config_loader import ConfigLoader
            
            loader = ConfigLoader()
            
            # 测试加载配置
            regime_config = loader.load_config('regime_config')
            assert 'trend' in regime_config or 'dynamic_thresholds' in regime_config
            self.log_test("加载 Regime Config", True)
            
            factor_weights = loader.load_config('factor_weights')
            assert 'momentum' in factor_weights
            self.log_test("加载 Factor Weights", True)
            
            risk_params = loader.load_config('risk_params')
            assert 'account' in risk_params
            self.log_test("加载 Risk Params", True)
            
            # 测试获取配置值
            adx_threshold = loader.get_config('regime_config', 'trend.ADX_threshold', default=25)
            assert isinstance(adx_threshold, (int, float))
            self.log_test("获取配置值", True, f"ADX Threshold: {adx_threshold}")
            
        except Exception as e:
            self.log_test("配置加载器", False, str(e))
    
    def test_review_agent(self):
        """测试 Review Agent"""
        print("\n" + "=" * 80)
        print("测试 Review Agent")
        print("=" * 80)
        
        try:
            from v4_3.review_agent import ReviewAgent
            
            agent = ReviewAgent(db_path=":memory:")
            
            # 测试生成报告（无数据）
            report = agent.generate_daily_report()
            assert isinstance(report, str)
            assert '每日复盘报告' in report
            self.log_test("Review Agent 生成报告", True)
            
            # 测试归因分析
            attribution = agent.attribution_analysis(days=30)
            assert isinstance(attribution, dict)
            self.log_test("Review Agent 归因分析", True)
            
        except Exception as e:
            self.log_test("Review Agent", False, str(e))
    
    def generate_report(self) -> str:
        """生成测试报告"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        report = []
        report.append("=" * 80)
        report.append("V4.3 系统完整性测试报告")
        report.append("=" * 80)
        report.append(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"总测试数：{total}")
        report.append(f"通过：{passed}")
        report.append(f"失败：{failed}")
        report.append(f"通过率：{pass_rate:.1f}%")
        report.append("")
        
        if self.errors:
            report.append("错误列表:")
            report.append("-" * 80)
            for error in self.errors:
                report.append(f"[FAIL] {error}")
            report.append("")
        
        report.append("详细结果:")
        report.append("-" * 80)
        
        for result in self.test_results:
            status = "PASS" if result['passed'] else "FAIL"
            report.append(f"{status}: {result['name']}")
            if result['message']:
                report.append(f"       {result['message']}")
        
        report.append("")
        report.append("=" * 80)
        report.append("*V4.3 System Tester - 质量保障，持续交付*")
        
        return "\n".join(report)


def main():
    """主函数"""
    print("=" * 80)
    print("V4.3 系统完整性测试")
    print("=" * 80)
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = V43SystemTester()
    
    # 执行测试
    tester.test_module_imports()
    tester.test_factor_calculations()
    tester.test_config_loader()
    tester.test_review_agent()
    
    # 生成报告
    report = tester.generate_report()
    
    print("\n" + "=" * 80)
    print("测试报告")
    print("=" * 80)
    print(report)
    
    # 保存报告
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_report.md')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存：{report_path}")


if __name__ == "__main__":
    main()
