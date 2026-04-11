"""
Factor IC Analyzer - 因子 IC 分析工具
版本：V4.3.0
创建：2026-04-10

功能：
1. 计算因子 IC（信息系数）
2. 因子有效性检验
3. 因子衰减分析
4. 因子组合优化
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class FactorICAnalyzer:
    """因子 IC 分析工具"""
    
    def __init__(self, db_path: str = "trading.db"):
        """
        初始化
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.factor_data = {}
        
    def calculate_factor_ic(self, symbol: str, factor_name: str, 
                           days: int = 90) -> Dict:
        """
        计算因子 IC
        
        Args:
            symbol: 交易品种
            factor_name: 因子名称
            days: 回看天数
            
        Returns:
            Dict: IC 分析结果
        """
        print(f"计算 {symbol} - {factor_name} 因子 IC...")
        
        # 获取历史数据
        data = self._get_historical_data(symbol, days)
        
        if data is None or len(data) < 30:
            return {
                "symbol": symbol,
                "factor": factor_name,
                "ic": None,
                "message": "数据不足"
            }
        
        # 计算因子值
        data = self._calculate_factor(data, factor_name)
        
        # 计算未来收益
        data['future_return'] = data['close'].shift(-1).pct_change()
        
        # 移除 NaN
        data = data.dropna()
        
        if len(data) < 20:
            return {
                "symbol": symbol,
                "factor": factor_name,
                "ic": None,
                "message": "有效数据不足"
            }
        
        # 计算 IC（相关系数）
        ic = data[factor_name].corr(data['future_return'])
        
        # IC 显著性检验
        t_stat = ic * np.sqrt(len(data) - 2) / np.sqrt(1 - ic**2)
        p_value = 2 * (1 - self._t_cdf(abs(t_stat), len(data) - 2))
        
        # 评级
        if abs(ic) >= 0.10:
            rating = "强有效"
        elif abs(ic) >= 0.05:
            rating = "有效"
        elif abs(ic) >= 0.02:
            rating = "弱有效"
        else:
            rating = "无效"
        
        return {
            "symbol": symbol,
            "factor": factor_name,
            "ic": ic,
            "t_stat": t_stat,
            "p_value": p_value,
            "sample_size": len(data),
            "rating": rating,
            "is_significant": p_value < 0.05
        }
    
    def _get_historical_data(self, symbol: str, days: int = 90) -> Optional[pd.DataFrame]:
        """获取历史数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        rates = mt5.copy_rates_range(
            symbol,
            mt5.TIMEFRAME_D1,
            start_date,
            end_date
        )
        
        if rates is None or len(rates) == 0:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df
    
    def _calculate_factor(self, df: pd.DataFrame, factor_name: str) -> pd.DataFrame:
        """计算因子值"""
        if factor_name == "momentum":
            # 动量因子：N 日收益率
            df[factor_name] = df['close'].pct_change(periods=20)
        
        elif factor_name == "rsi":
            # RSI 因子
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df[factor_name] = 100 - (100 / (1 + rs))
        
        elif factor_name == "volatility":
            # 波动率因子：收益率标准差
            df['return'] = df['close'].pct_change()
            df[factor_name] = df['return'].rolling(window=20).std()
        
        elif factor_name == "breakout":
            # 突破因子：价格相对 N 日高点的位置
            highest = df['high'].rolling(window=20).max()
            df[factor_name] = (df['close'] - highest) / highest * 100
        
        else:
            # 默认：收益率
            df[factor_name] = df['close'].pct_change()
        
        return df
    
    def _t_cdf(self, x: float, df: int) -> float:
        """t 分布 CDF（简化近似）"""
        # 使用正态分布近似（大样本）
        from scipy import stats
        return stats.t.cdf(x, df)
    
    def analyze_all_factors(self, symbol: str, days: int = 90) -> Dict:
        """
        分析所有因子
        
        Args:
            symbol: 交易品种
            days: 回看天数
            
        Returns:
            Dict: 所有因子的 IC 分析结果
        """
        factors = ["momentum", "rsi", "volatility", "breakout"]
        
        results = {}
        
        for factor in factors:
            result = self.calculate_factor_ic(symbol, factor, days)
            results[factor] = result
        
        # 汇总
        valid_factors = [f for f, r in results.items() 
                        if r['ic'] is not None and r['is_significant']]
        
        return {
            "symbol": symbol,
            "period": f"{days} days",
            "factors": results,
            "valid_factors": valid_factors,
            "best_factor": max(results.items(), 
                             key=lambda x: abs(x[1]['ic']) if x[1]['ic'] else 0)[0] 
                          if results else None
        }
    
    def factor_decay_analysis(self, symbol: str, factor_name: str, 
                             days: int = 90) -> Dict:
        """
        因子衰减分析
        
        Args:
            symbol: 交易品种
            factor_name: 因子名称
            days: 回看天数
            
        Returns:
            Dict: 衰减分析结果
        """
        data = self._get_historical_data(symbol, days)
        
        if data is None or len(data) < 30:
            return {"message": "数据不足"}
        
        # 计算因子值
        data = self._calculate_factor(data, factor_name)
        
        # 计算不同滞后的 IC
        decay_results = []
        
        for lag in [1, 2, 3, 5, 10, 20]:
            # 未来 lag 日收益
            data[f'future_return_{lag}'] = data['close'].shift(-lag).pct_change()
            data_clean = data.dropna()
            
            if len(data_clean) < 20:
                continue
            
            ic = data_clean[factor_name].corr(data_clean[f'future_return_{lag}'])
            
            decay_results.append({
                "lag": lag,
                "ic": ic
            })
        
        # 计算半衰期
        ics = [r['ic'] for r in decay_results]
        if ics[0] > 0:
            half_life = next((r['lag'] for r in decay_results 
                            if r['ic'] < ics[0] / 2), len(decay_results))
        else:
            half_life = None
        
        return {
            "symbol": symbol,
            "factor": factor_name,
            "decay": decay_results,
            "half_life": half_life,
            "initial_ic": ics[0] if ics else None
        }
    
    def optimize_factor_weights(self, symbol: str, days: int = 90) -> Dict:
        """
        优化因子权重
        
        Args:
            symbol: 交易品种
            days: 回看天数
            
        Returns:
            Dict: 最优权重
        """
        # 获取各因子 IC
        ic_results = self.analyze_all_factors(symbol, days)
        
        # 基于 IC 绝对值分配权重
        factors = ic_results['valid_factors']
        
        if not factors:
            return {"message": "无有效因子"}
        
        # 计算权重（IC 绝对值归一化）
        ics = {f: abs(ic_results['factors'][f]['ic']) for f in factors}
        total_ic = sum(ics.values())
        
        weights = {f: ic / total_ic for f, ic in ics.items()}
        
        return {
            "symbol": symbol,
            "valid_factors": factors,
            "optimal_weights": weights,
            "ics": ics
        }
    
    def generate_report(self, symbol: str, days: int = 90) -> str:
        """
        生成 IC 分析报告
        
        Args:
            symbol: 交易品种
            days: 回看天数
            
        Returns:
            str: 报告（Markdown 格式）
        """
        # 分析所有因子
        all_factors = self.analyze_all_factors(symbol, days)
        
        report = []
        report.append("# 📊 因子 IC 分析报告")
        report.append("")
        report.append(f"**品种**: {symbol}")
        report.append(f"**周期**: {days} 天")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 核心发现
        report.append("## 🎯 核心发现")
        report.append("")
        report.append(f"- 有效因子数量：{len(all_factors['valid_factors'])}")
        report.append(f"- 最佳因子：{all_factors['best_factor']}")
        report.append("")
        
        # 各因子详情
        report.append("## 📈 因子详情")
        report.append("")
        report.append("| 因子 | IC | T 统计 | P 值 | 评级 | 显著性 |")
        report.append("|------|-----|--------|------|------|--------|")
        
        for factor_name, result in all_factors['factors'].items():
            if result['ic'] is None:
                continue
            
            ic_icon = "✅" if result['is_significant'] else "❌"
            report.append(f"| {factor_name} | {result['ic']:.3f} | {result['t_stat']:.2f} | {result['p_value']:.3f} | {result['rating']} | {ic_icon} |")
        
        report.append("")
        
        # 最优权重
        weights_result = self.optimize_factor_weights(symbol, days)
        
        if 'optimal_weights' in weights_result:
            report.append("## 🎛️ 最优因子权重")
            report.append("")
            
            for factor, weight in weights_result['optimal_weights'].items():
                ic = weights_result['ics'][factor]
                report.append(f"- **{factor}**: {weight:.1%} (IC={ic:.3f})")
            
            report.append("")
        
        # 衰减分析（仅最佳因子）
        if all_factors['best_factor']:
            decay_result = self.factor_decay_analysis(
                symbol, all_factors['best_factor'], days
            )
            
            report.append("## 📉 因子衰减分析")
            report.append("")
            report.append(f"最佳因子：{all_factors['best_factor']}")
            
            if 'half_life' in decay_result and decay_result['half_life']:
                report.append(f"半衰期：{decay_result['half_life']} 天")
            
            report.append("")
            report.append("| 滞后天数 | IC |")
            report.append("|----------|-----|")
            
            for r in decay_result.get('decay', []):
                report.append(f"| {r['lag']} | {r['ic']:.3f} |")
            
            report.append("")
        
        report.append("---")
        report.append("*V4.3 Factor IC Analyzer - 数据驱动因子选择*")
        
        return "\n".join(report)


def main():
    """测试函数"""
    # 初始化 MT5
    if not mt5.initialize():
        print("❌ MT5 初始化失败")
        return
    
    # 创建分析器
    analyzer = FactorICAnalyzer()
    
    # 测试品种
    symbol = "EURUSD"
    
    print("=" * 80)
    print(f"Factor IC Analyzer - {symbol}")
    print("=" * 80)
    
    # 生成报告
    report = analyzer.generate_report(symbol, 90)
    print("\n" + report)
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
