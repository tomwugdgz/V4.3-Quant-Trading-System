"""
参数鲁棒性测试
版本：V4.3.0
创建：2026-04-11

功能：
1. 参数敏感性分析
2. 最优参数区间识别
3. 参数稳定性评估
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from itertools import product


class ParameterRobustnessTester:
    """参数鲁棒性测试器"""
    
    def __init__(self, symbol: str = "EURUSD"):
        """
        初始化
        
        Args:
            symbol: 交易品种
        """
        self.symbol = symbol
        self.parameters = {
            'ema_fast': [8, 9, 10, 11, 12],
            'ema_slow': [18, 19, 20, 21, 22],
            'signal_threshold': [0.06, 0.08, 0.10, 0.12],
            'stop_loss_atr': [1.2, 1.5, 1.8, 2.0]
        }
    
    def generate_parameter_combinations(self) -> List[Dict]:
        """
        生成参数组合
        
        Returns:
            List[Dict]: 参数组合列表
        """
        combinations = []
        
        for ema_fast, ema_slow, threshold, sl_atr in product(
            self.parameters['ema_fast'],
            self.parameters['ema_slow'],
            self.parameters['signal_threshold'],
            self.parameters['stop_loss_atr']
        ):
            combinations.append({
                'ema_fast': ema_fast,
                'ema_slow': ema_slow,
                'signal_threshold': threshold,
                'stop_loss_atr': sl_atr
            })
        
        return combinations
    
    def analyze_sensitivity(self, results: List[Dict]) -> Dict:
        """
        分析参数敏感性
        
        Args:
            results: 各参数组合的回测结果
            
        Returns:
            Dict: 敏感性分析结果
        """
        if not results:
            return {"error": "无回测结果"}
        
        # 转换为 DataFrame
        df_results = pd.DataFrame(results)
        
        # 计算各参数的敏感性
        sensitivity = {}
        
        for param_name in ['ema_fast', 'ema_slow', 'signal_threshold', 'stop_loss_atr']:
            # 按参数分组
            grouped = df_results.groupby(param_name)
            
            # 计算该参数不同取值下的平均夏普比率
            param_sensitivity = grouped['sharpe'].agg(['mean', 'std', 'count'])
            param_sensitivity.columns = ['avg_sharpe', 'std_sharpe', 'count']
            
            # 计算敏感性（标准差越大，越敏感）
            sensitivity_score = param_sensitivity['std_sharpe'].mean()
            
            sensitivity[param_name] = {
                'sensitivity_score': sensitivity_score,
                'details': param_sensitivity.to_dict()
            }
        
        # 计算总体稳定性
        total_sharpe_std = df_results['sharpe'].std()
        total_sharpe_mean = df_results['sharpe'].mean()
        
        # 稳定性评分（标准差越小，越稳定）
        stability_score = 1 - (total_sharpe_std / (total_sharpe_mean + 0.001))
        stability_score = max(0, min(1, stability_score))  # 限制在 0-1 之间
        
        return {
            'parameter_sensitivity': sensitivity,
            'total_sharpe_mean': total_sharpe_mean,
            'total_sharpe_std': total_sharpe_std,
            'stability_score': stability_score,
            'is_robust': stability_score > 0.7  # 稳定性>0.7 认为鲁棒
        }
    
    def find_optimal_range(self, results: List[Dict], top_percent: float = 0.2) -> Dict:
        """
        识别最优参数区间
        
        Args:
            results: 各参数组合的回测结果
            top_percent: 前百分之多少的组合
            
        Returns:
            Dict: 最优参数区间
        """
        if not results:
            return {"error": "无回测结果"}
        
        # 转换为 DataFrame
        df_results = pd.DataFrame(results)
        
        # 选择前 top% 的组合
        threshold = df_results['sharpe'].quantile(1 - top_percent)
        top_results = df_results[df_results['sharpe'] >= threshold]
        
        # 计算各参数的最优区间
        optimal_ranges = {}
        
        for param_name in ['ema_fast', 'ema_slow', 'signal_threshold', 'stop_loss_atr']:
            values = top_results[param_name]
            
            optimal_ranges[param_name] = {
                'min': values.min(),
                'max': values.max(),
                'mean': values.mean(),
                'median': values.median(),
                'std': values.std()
            }
        
        return {
            'optimal_ranges': optimal_ranges,
            'top_combinations_count': len(top_results),
            'sharpe_threshold': threshold
        }
    
    def test_robustness(self, results: List[Dict]) -> Dict:
        """
        综合鲁棒性测试
        
        Args:
            results: 各参数组合的回测结果
            
        Returns:
            Dict: 鲁棒性测试结果
        """
        # 1. 敏感性分析
        sensitivity = self.analyze_sensitivity(results)
        
        # 2. 最优区间识别
        optimal_ranges = self.find_optimal_range(results)
        
        # 3. 计算鲁棒性评分
        robustness_score = sensitivity['stability_score']
        
        # 4. 判断是否通过鲁棒性测试
        passed = (
            robustness_score > 0.7 and  # 稳定性>0.7
            sensitivity['total_sharpe_mean'] > 1.0 and  # 平均夏普>1.0
            len(optimal_ranges.get('top_combinations_count', [])) > 0  # 有最优组合
        )
        
        return {
            'robustness_score': robustness_score,
            'passed': passed,
            'sensitivity_analysis': sensitivity,
            'optimal_ranges': optimal_ranges,
            'recommendation': self._generate_recommendation(sensitivity, optimal_ranges)
        }
    
    def _generate_recommendation(self, sensitivity: Dict, optimal_ranges: Dict) -> str:
        """生成参数建议"""
        if not sensitivity.get('is_robust', False):
            return "参数敏感性过高，建议缩小参数范围或增加训练数据"
        
        recommendations = []
        
        for param_name, range_info in optimal_ranges['optimal_ranges'].items():
            recommendations.append(
                f"{param_name}: 建议使用 [{range_info['min']}, {range_info['max']}] 范围"
            )
        
        return "\n".join(recommendations)


def main():
    """测试函数"""
    print("=" * 80)
    print("参数鲁棒性测试")
    print("=" * 80)
    
    # 生成模拟回测结果
    np.random.seed(42)
    n_combinations = 100
    
    results = []
    
    for i in range(n_combinations):
        results.append({
            'ema_fast': np.random.randint(8, 13),
            'ema_slow': np.random.randint(18, 23),
            'signal_threshold': np.random.choice([0.06, 0.08, 0.10, 0.12]),
            'stop_loss_atr': np.random.choice([1.2, 1.5, 1.8, 2.0]),
            'sharpe': np.random.normal(1.5, 0.5),  # 夏普均值 1.5，标准差 0.5
            'total_return': np.random.normal(0.15, 0.08),
            'max_drawdown': np.random.normal(-0.12, 0.05)
        })
    
    # 创建测试器
    tester = ParameterRobustnessTester(symbol="EURUSD")
    
    # 执行鲁棒性测试
    robustness_result = tester.test_robustness(results)
    
    print("\n鲁棒性测试结果:")
    print(f"  鲁棒性评分：{robustness_result['robustness_score']:.3f}")
    print(f"  是否通过：{'✅ PASS' if robustness_result['passed'] else '❌ FAIL'}")
    
    print("\n敏感性分析:")
    sensitivity = robustness_result['sensitivity_analysis']
    print(f"  总体夏普均值：{sensitivity['total_sharpe_mean']:.3f}")
    print(f"  总体夏普标准差：{sensitivity['total_sharpe_std']:.3f}")
    print(f"  稳定性评分：{sensitivity['stability_score']:.3f}")
    print(f"  是否鲁棒：{'是' if sensitivity['is_robust'] else '否'}")
    
    print("\n各参数敏感性:")
    for param_name, param_sensitivity in sensitivity['parameter_sensitivity'].items():
        print(f"  {param_name}: {param_sensitivity['sensitivity_score']:.4f}")
    
    print("\n最优参数区间:")
    optimal = robustness_result['optimal_ranges']
    for param_name, range_info in optimal['optimal_ranges'].items():
        print(f"  {param_name}: [{range_info['min']}, {range_info['max']}] (均值：{range_info['mean']:.2f})")
    
    print("\n建议:")
    print(robustness_result['recommendation'])


if __name__ == "__main__":
    main()
