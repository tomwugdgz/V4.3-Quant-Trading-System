"""
样本外验证（Out-of-Sample Validation）
版本：V4.3.0
创建：2026-04-11

功能：
1. OOS 测试
2. 过拟合检测
3. 前向分析验证
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple


class OOSValidator:
    """样本外验证器"""
    
    def __init__(self, symbol: str = "EURUSD"):
        """
        初始化
        
        Args:
            symbol: 交易品种
        """
        self.symbol = symbol
    
    def split_data(self, df: pd.DataFrame, train_ratio: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分割训练集和测试集
        
        Args:
            df: K 线数据
            train_ratio: 训练集占比
            
        Returns:
            Tuple: (训练集，测试集)
        """
        split_idx = int(len(df) * train_ratio)
        
        train_data = df.iloc[:split_idx].copy()
        test_data = df.iloc[split_idx:].copy()
        
        return train_data, test_data
    
    def calculate_oos_performance(self, train_result: Dict, test_result: Dict) -> Dict:
        """
        计算 OOS 表现
        
        Args:
            train_result: 训练集回测结果
            test_result: 测试集回测结果
            
        Returns:
            Dict: OOS 分析结果
        """
        # 计算各项指标的衰减
        sharpe_decay = (train_result['sharpe'] - test_result['sharpe']) / (train_result['sharpe'] + 0.001)
        return_decay = (train_result['total_return'] - test_result['total_return']) / (train_result['total_return'] + 0.001)
        dd_decay = (train_result['max_drawdown'] - test_result['max_drawdown']) / (abs(train_result['max_drawdown']) + 0.001)
        
        # OOS 评分（衰减越小，评分越高）
        avg_decay = (sharpe_decay + return_decay + dd_decay) / 3
        oos_score = 1 - avg_decay
        oos_score = max(0, min(1, oos_score))  # 限制在 0-1 之间
        
        # 判断是否过拟合
        is_overfitted = sharpe_decay > 0.5  # 夏普衰减超过 50% 认为过拟合
        
        return {
            'train_sharpe': train_result['sharpe'],
            'test_sharpe': test_result['sharpe'],
            'sharpe_decay': sharpe_decay,
            'return_decay': return_decay,
            'drawdown_decay': dd_decay,
            'oos_score': oos_score,
            'is_overfitted': is_overfitted,
            'passed': oos_score > 0.6 and not is_overfitted  # OOS 评分>0.6 且未过拟合
        }
    
    def forward_analysis(self, df: pd.DataFrame, strategy_func, params: Dict) -> Dict:
        """
        前向分析验证
        
        Args:
            df: K 线数据
            strategy_func: 策略函数
            params: 策略参数
            
        Returns:
            Dict: 前向分析结果
        """
        # 分割为多个时间段
        n_periods = 5
        period_size = len(df) // n_periods
        
        results = []
        
        for i in range(n_periods - 1):
            # 训练集：前 i+1 个时间段
            train_end = (i + 1) * period_size
            train_data = df.iloc[:train_end]
            
            # 测试集：第 i+2 个时间段
            test_start = train_end
            test_end = (i + 2) * period_size
            test_data = df.iloc[test_start:test_end]
            
            # 在训练集上优化参数（简化：直接使用给定参数）
            optimized_params = params
            
            # 在测试集上验证
            test_result = strategy_func(test_data, optimized_params)
            
            results.append({
                'period': i + 1,
                'train_size': train_end,
                'test_size': len(test_data),
                'result': test_result
            })
        
        # 分析前向稳定性
        sharpes = [r['result']['sharpe'] for r in results]
        
        return {
            'period_results': results,
            'avg_sharpe': np.mean(sharpes),
            'sharpe_std': np.std(sharpes),
            'sharpe_trend': sharpes[-1] - sharpes[0],  # 夏普趋势
            'is_stable': np.std(sharpes) < 0.5  # 标准差<0.5 认为稳定
        }
    
    def deflated_sharpe_ratio(self, returns: pd.Series, n_trials: int = 100) -> Dict:
        """
        计算去膨胀夏普比率（Deflated Sharpe Ratio）
        
        Args:
            returns: 收益率序列
            n_trials: 尝试的策略数量
            
        Returns:
            Dict: DSR 分析结果
        """
        # 计算普通夏普比率
        sharpe = returns.mean() / returns.std() * np.sqrt(252)  # 年化
        
        # 计算去膨胀调整
        # 假设尝试了 n_trials 个策略，需要调整夏普比率
        adjustment_factor = np.sqrt(2 * np.log(n_trials))
        deflated_sharpe = sharpe - adjustment_factor
        
        # 判断是否显著
        is_significant = deflated_sharpe > 1.0
        
        return {
            'raw_sharpe': sharpe,
            'deflated_sharpe': deflated_sharpe,
            'adjustment_factor': adjustment_factor,
            'n_trials': n_trials,
            'is_significant': is_significant
        }
    
    def validate(self, train_result: Dict, test_result: Dict, returns: pd.Series = None) -> Dict:
        """
        综合 OOS 验证
        
        Args:
            train_result: 训练集结果
            test_result: 测试集结果
            returns: 收益率序列（可选，用于 DSR 计算）
            
        Returns:
            Dict: 验证结果
        """
        # 1. OOS 表现
        oos_perf = self.calculate_oos_performance(train_result, test_result)
        
        # 2. DSR 分析（如果有收益率数据）
        dsr_result = None
        if returns is not None:
            dsr_result = self.deflated_sharpe_ratio(returns)
        
        # 3. 综合判断
        passed = (
            oos_perf['passed'] and
            (dsr_result is None or dsr_result['is_significant'])
        )
        
        return {
            'oos_performance': oos_perf,
            'dsr_analysis': dsr_result,
            'passed': passed,
            'recommendation': self._generate_recommendation(oos_perf, dsr_result)
        }
    
    def _generate_recommendation(self, oos_perf: Dict, dsr_result: Dict = None) -> str:
        """生成建议"""
        recommendations = []
        
        if not oos_perf['passed']:
            if oos_perf['sharpe_decay'] > 0.5:
                recommendations.append("⚠️ 夏普比率衰减过大，可能存在过拟合")
            if oos_perf['oos_score'] < 0.6:
                recommendations.append("⚠️ OOS 评分偏低，建议增加训练数据或简化策略")
        
        if dsr_result and not dsr_result['is_significant']:
            recommendations.append("⚠️ 去膨胀夏普比率不显著，可能有多重假设检验问题")
        
        if not recommendations:
            recommendations.append("✅ OOS 验证通过，策略表现稳健")
        
        return "\n".join(recommendations)


def main():
    """测试函数"""
    print("=" * 80)
    print("样本外验证（OOS）")
    print("=" * 80)
    
    # 生成模拟结果
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
    
    # 创建验证器
    validator = OOSValidator(symbol="EURUSD")
    
    # 执行 OOS 验证
    oos_result = validator.validate(train_result, test_result)
    
    print("\nOOS 表现:")
    oos_perf = oos_result['oos_performance']
    print(f"  训练集夏普：{oos_perf['train_sharpe']:.2f}")
    print(f"  测试集夏普：{oos_perf['test_sharpe']:.2f}")
    print(f"  夏普衰减：{oos_perf['sharpe_decay']:.2%}")
    print(f"  收益衰减：{oos_perf['return_decay']:.2%}")
    print(f"  OOS 评分：{oos_perf['oos_score']:.3f}")
    print(f"  是否过拟合：{'是' if oos_perf['is_overfitted'] else '否'}")
    print(f"  是否通过：{'✅ PASS' if oos_perf['passed'] else '❌ FAIL'}")
    
    print("\n建议:")
    print(oos_result['recommendation'])


if __name__ == "__main__":
    main()
