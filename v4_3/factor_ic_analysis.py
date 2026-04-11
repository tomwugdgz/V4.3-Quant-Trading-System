"""
因子 IC 分析工具
版本：V4.3.0
创建：2026-04-11

功能：
1. 计算因子 IC（信息系数）
2. IC 统计分析
3. 因子有效性评估
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import sys
import os

# 添加路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'factors'))

from momentum import MomentumFactor
from mean_reversion import MeanReversionFactor
from breakout import BreakoutFactor
from volatility import VolatilityFactor


class FactorICAnalyzer:
    """因子 IC 分析器"""
    
    def __init__(self, symbols: List[str] = None):
        """
        初始化
        
        Args:
            symbols: 要分析的品种列表
        """
        if symbols is None:
            symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"]
        
        self.symbols = symbols
        self.periods = 100  # 获取 K 线数量
        
        # 初始化因子
        self.momentum = MomentumFactor()
        self.mean_reversion = MeanReversionFactor()
        self.breakout = BreakoutFactor()
        self.volatility = VolatilityFactor()
    
    def get_historical_data(self, symbol: str, timeframe=mt5.TIMEFRAME_H1) -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 交易品种
            timeframe: 时间周期
            
        Returns:
            pd.DataFrame: K 线数据
        """
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, self.periods)
        
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df
    
    def calculate_factor_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算各因子评分
        
        Args:
            df: K 线数据
            
        Returns:
            pd.DataFrame: 因子评分
        """
        scores = pd.DataFrame(index=df.index)
        
        # 动量因子
        momentum_result = self.momentum.calculate_score(df)
        scores['momentum'] = momentum_result['total_score']
        
        # 均值回归因子
        mean_rev_result = self.mean_reversion.calculate_score(df)
        scores['mean_reversion'] = mean_rev_result['total_score']
        
        # 突破因子
        breakout_result = self.breakout.calculate_score(df)
        scores['breakout'] = breakout_result['total_score']
        
        # 波动率因子
        volatility_result = self.volatility.calculate_score(df)
        scores['volatility'] = volatility_result['total_score']
        
        return scores
    
    def calculate_forward_returns(self, df: pd.DataFrame, periods: int = 10) -> pd.Series:
        """
        计算未来收益
        
        Args:
            df: K 线数据
            periods: 向前看多少期
            
        Returns:
            pd.Series: 未来收益
        """
        # 计算未来 N 期收益
        forward_returns = df['close'].shift(-periods) / df['close'] - 1
        
        return forward_returns
    
    def calculate_ic(self, factor_scores: pd.Series, forward_returns: pd.Series) -> float:
        """
        计算 IC（信息系数）
        
        Args:
            factor_scores: 因子评分
            forward_returns: 未来收益
            
        Returns:
            float: IC 值
        """
        # 去除 NaN
        valid_idx = ~(factor_scores.isna() | forward_returns.isna())
        
        if valid_idx.sum() < 20:  # 至少 20 个有效样本
            return np.nan
        
        # 计算 Pearson 相关（scipy 可能未安装）
        ic = factor_scores[valid_idx].corr(forward_returns[valid_idx], method='pearson')
        
        return ic
    
    def analyze_all_factors(self) -> Dict:
        """
        分析所有因子的 IC
        
        Returns:
            Dict: IC 分析结果
        """
        if not mt5.initialize():
            print("[ERROR] MT5 初始化失败")
            return {}
        
        results = {}
        
        for symbol in self.symbols:
            print(f"\n分析 {symbol}...")
            
            # 获取数据
            df = self.get_historical_data(symbol)
            
            if len(df) == 0:
                print(f"  [SKIP] 数据不足")
                continue
            
            # 计算因子评分
            scores = self.calculate_factor_scores(df)
            
            # 计算未来收益（向前看 10 期）
            forward_returns = self.calculate_forward_returns(df, periods=10)
            
            # 计算各因子 IC
            factor_ics = {}
            
            for factor_name in scores.columns:
                ic = self.calculate_ic(scores[factor_name], forward_returns)
                
                factor_ics[factor_name] = {
                    'ic': ic,
                    'valid': not np.isnan(ic) and abs(ic) > 0.02
                }
                
                # 判断有效性
                if np.isnan(ic):
                    evaluation = "数据不足"
                elif abs(ic) < 0.02:
                    evaluation = "无效因子"
                elif abs(ic) < 0.05:
                    evaluation = "弱有效"
                else:
                    evaluation = "有效因子"
                
                # 打印结果（避免编码问题）
                ic_str = f"{ic:.4f}" if not np.isnan(ic) else "N/A"
                print(f"  {factor_name}: IC={ic_str} ({evaluation})")
                
                print(f"  {factor_name}: IC={ic:.4f} ({evaluation})")
            
            results[symbol] = factor_ics
        
        mt5.shutdown()
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """
        生成 IC 分析报告
        
        Args:
            results: IC 分析结果
            
        Returns:
            str: 分析报告（Markdown 格式）
        """
        report = []
        report.append("# 因子 IC 分析报告")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 分析说明")
        report.append("")
        report.append("- **IC（信息系数）**: 因子值与未来收益的相关系数")
        report.append("- **IC > 0.05**: 有效因子")
        report.append("- **IC < 0.02**: 无效因子，建议剔除")
        report.append("- **ICIR > 1.5**: 优秀因子（IC/IC 标准差）")
        report.append("")
        
        report.append("## 各品种因子 IC")
        report.append("")
        
        for symbol, factor_ics in results.items():
            report.append(f"### {symbol}")
            report.append("")
            report.append("[table]")
            report.append("| 因子 | IC 值 | 有效性 |")
            report.append("|------|-------|--------|")
            
            for factor_name, ic_data in factor_ics.items():
                ic = ic_data['ic']
                valid = "[有效]" if ic_data['valid'] else "[无效]"
                
                if np.isnan(ic):
                    ic_str = "N/A"
                else:
                    ic_str = f"{ic:.4f}"
                
                report.append(f"| {factor_name} | {ic_str} | {valid} |")
            
            report.append("[/table]")
            report.append("")
        
        report.append("## 因子筛选建议")
        report.append("")
        
        # 统计各因子的平均 IC
        factor_avg_ics = {}
        
        for factor_name in ['momentum', 'mean_reversion', 'breakout', 'volatility']:
            ics = []
            
            for symbol, factor_ics in results.items():
                if factor_name in factor_ics:
                    ic = factor_ics[factor_name]['ic']
                    if not np.isnan(ic):
                        ics.append(ic)
            
            if len(ics) > 0:
                factor_avg_ics[factor_name] = np.mean(ics)
        
        # 排序
        sorted_factors = sorted(factor_avg_ics.items(), key=lambda x: abs(x[1]), reverse=True)
        
        report.append("[table]")
        report.append("| 因子 | 平均 IC | 建议 |")
        report.append("|------|---------|------|")
        
        for factor_name, avg_ic in sorted_factors:
            if abs(avg_ic) < 0.02:
                suggestion = "[考虑剔除]"
            elif abs(avg_ic) < 0.05:
                suggestion = "[保留观察]"
            else:
                suggestion = "[重点使用]"
            
            report.append(f"| {factor_name} | {avg_ic:.4f} | {suggestion} |")
        
        report.append("[/table]")
        report.append("")
        
        report.append("---")
        report.append("*V4.3 Factor IC Analyzer - 数据驱动，持续进化*")
        
        return "\n".join(report)


def main():
    """主函数"""
    print("=" * 80)
    print("V4.3 因子 IC 分析")
    print("=" * 80)
    
    # 创建分析器
    analyzer = FactorICAnalyzer()
    
    # 执行分析
    results = analyzer.analyze_all_factors()
    
    if not results:
        print("\n[ERROR] 分析失败")
        return
    
    # 生成报告
    report = analyzer.generate_report(results)
    
    print("\n" + "=" * 80)
    print("分析报告:")
    print("=" * 80)
    print(report)


if __name__ == "__main__":
    main()
