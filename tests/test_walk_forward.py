"""
Walk-Forward 验证器测试
版本：V4.3.0
创建：2026-04-11
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime


class TestParameterRobustness:
    """参数鲁棒性测试"""
    
    def test_generate_combinations(self):
        """测试参数组合生成"""
        from v4_3.parameter_robustness import ParameterRobustnessTester
        
        tester = ParameterRobustnessTester()
        combinations = tester.generate_parameter_combinations()
        
        assert len(combinations) > 0
        assert 'ema_fast' in combinations[0]
        assert 'ema_slow' in combinations[0]
    
    def test_analyze_sensitivity(self):
        """测试敏感性分析"""
        from v4_3.parameter_robustness import ParameterRobustnessTester
        
        tester = ParameterRobustnessTester()
        
        # 生成模拟结果
        results = [
            {
                'ema_fast': 10,
                'ema_slow': 20,
                'signal_threshold': 0.08,
                'stop_loss_atr': 1.5,
                'sharpe': 1.5,
                'total_return': 0.15,
                'max_drawdown': -0.10
            }
            for _ in range(50)
        ]
        
        # 添加一些变化
        for i, result in enumerate(results):
            result['sharpe'] = 1.5 + np.random.randn() * 0.3
        
        sensitivity = tester.analyze_sensitivity(results)
        
        assert 'parameter_sensitivity' in sensitivity
        assert 'stability_score' in sensitivity
        assert 0 <= sensitivity['stability_score'] <= 1
    
    def test_find_optimal_range(self):
        """测试最优区间识别"""
        from v4_3.parameter_robustness import ParameterRobustnessTester
        
        tester = ParameterRobustnessTester()
        
        results = [
            {
                'ema_fast': np.random.randint(8, 13),
                'ema_slow': np.random.randint(18, 23),
                'signal_threshold': np.random.choice([0.06, 0.08, 0.10, 0.12]),
                'stop_loss_atr': np.random.choice([1.2, 1.5, 1.8, 2.0]),
                'sharpe': np.random.normal(1.5, 0.5)
            }
            for _ in range(100)
        ]
        
        optimal = tester.find_optimal_range(results)
        
        assert 'optimal_ranges' in optimal
        assert 'ema_fast' in optimal['optimal_ranges']
    
    def test_robustness_test(self):
        """测试鲁棒性综合测试"""
        from v4_3.parameter_robustness import ParameterRobustnessTester
        
        tester = ParameterRobustnessTester()
        
        results = [
            {
                'ema_fast': np.random.randint(8, 13),
                'ema_slow': np.random.randint(18, 23),
                'signal_threshold': np.random.choice([0.06, 0.08, 0.10, 0.12]),
                'stop_loss_atr': np.random.choice([1.2, 1.5, 1.8, 2.0]),
                'sharpe': np.random.normal(1.5, 0.3)
            }
            for _ in range(100)
        ]
        
        robustness = tester.test_robustness(results)
        
        assert 'robustness_score' in robustness
        assert 'passed' in robustness
        assert 'recommendation' in robustness


class TestOOSValidation:
    """OOS 验证测试"""
    
    def test_split_data(self):
        """测试数据分割"""
        from v4_3.oos_validation import OOSValidator
        
        validator = OOSValidator()
        
        # 生成测试数据
        df = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 100
        })
        
        train, test = validator.split_data(df, train_ratio=0.7)
        
        assert len(train) == 70
        assert len(test) == 30
    
    def test_calculate_oos_performance(self):
        """测试 OOS 表现计算"""
        from v4_3.oos_validation import OOSValidator
        
        validator = OOSValidator()
        
        train_result = {
            'sharpe': 2.0,
            'total_return': 0.25,
            'max_drawdown': -0.10
        }
        
        test_result = {
            'sharpe': 1.5,
            'total_return': 0.18,
            'max_drawdown': -0.12
        }
        
        oos_perf = validator.calculate_oos_performance(train_result, test_result)
        
        assert 'sharpe_decay' in oos_perf
        assert 'oos_score' in oos_perf
        assert 0 <= oos_perf['oos_score'] <= 1
    
    def test_deflated_sharpe_ratio(self):
        """测试去膨胀夏普比率"""
        from v4_3.oos_validation import OOSValidator
        
        validator = OOSValidator()
        
        returns = pd.Series(np.random.randn(252) * 0.01)  # 252 天收益率
        
        dsr_result = validator.deflated_sharpe_ratio(returns, n_trials=100)
        
        assert 'raw_sharpe' in dsr_result
        assert 'deflated_sharpe' in dsr_result
        assert 'adjustment_factor' in dsr_result
    
    def test_validate(self):
        """测试综合验证"""
        from v4_3.oos_validation import OOSValidator
        
        validator = OOSValidator()
        
        train_result = {
            'sharpe': 2.0,
            'total_return': 0.25,
            'max_drawdown': -0.10
        }
        
        test_result = {
            'sharpe': 1.5,
            'total_return': 0.18,
            'max_drawdown': -0.12
        }
        
        result = validator.validate(train_result, test_result)
        
        assert 'oos_performance' in result
        assert 'passed' in result
        assert 'recommendation' in result
