"""
波动率因子
版本：V4.3.0
创建：2026-04-11

功能：
1. ATR 变化
2. 布林带宽度
3. 历史波动率
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict


class VolatilityFactor:
    """波动率因子"""
    
    def __init__(self):
        """初始化"""
        self.atr_period = 14
        self.bb_period = 20
        self.hv_period = 20
    
    def calculate_atr_change(self, df: pd.DataFrame) -> Dict:
        """
        计算 ATR 变化
        
        Args:
            df: K 线数据（包含 high, low, close 列）
            
        Returns:
            Dict: ATR 分析
        """
        if len(df) < self.atr_period + 1:
            return {
                'atr': 0.0,
                'atr_change': 0.0,
                'signal': 'NEUTRAL'
            }
        
        # 计算 TR
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算 ATR
        atr = tr.rolling(window=self.atr_period).mean()
        
        # 当前 ATR 和之前 ATR
        current_atr = atr.iloc[-1]
        prev_atr = atr.iloc[-2] if len(atr) > 1 else current_atr
        
        # ATR 变化率
        atr_change = (current_atr - prev_atr) / prev_atr if prev_atr > 0 else 0
        
        # 判断信号
        if atr_change > 0.1:  # ATR 上升 10%
            signal = 'HIGH_VOLATILITY'  # 波动率上升
        elif atr_change < -0.1:  # ATR 下降 10%
            signal = 'LOW_VOLATILITY'  # 波动率下降
        else:
            signal = 'NORMAL'
        
        return {
            'atr': current_atr,
            'atr_change': atr_change * 100,  # 转换为百分比
            'signal': signal
        }
    
    def calculate_bollinger_width(self, df: pd.DataFrame) -> Dict:
        """
        计算布林带宽度
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            Dict: 布林带宽度分析
        """
        if len(df) < self.bb_period:
            return {
                'width': 0.0,
                'percent_b': 0.5,
                'signal': 'NEUTRAL'
            }
        
        # 计算中轨
        middle = df['close'].rolling(window=self.bb_period).mean()
        
        # 计算标准差
        std = df['close'].rolling(window=self.bb_period).std()
        
        # 计算上下轨
        upper = middle + (2.0 * std)
        lower = middle - (2.0 * std)
        
        # 计算带宽
        width = (upper - lower) / middle
        
        # 计算 %B（价格在布林带中的位置）
        current_price = df['close'].iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        
        percent_b = (current_price - current_lower) / (current_upper - current_lower)
        
        # 判断信号
        if width.iloc[-1] < width.rolling(window=20).mean().iloc[-1] * 0.8:
            signal = 'SQUEEZE'  # 布林带收口，即将突破
        else:
            signal = 'NORMAL'
        
        return {
            'width': width.iloc[-1] * 100,  # 转换为百分比
            'percent_b': percent_b,
            'upper': current_upper,
            'lower': current_lower,
            'signal': signal
        }
    
    def calculate_historical_volatility(self, df: pd.DataFrame) -> Dict:
        """
        计算历史波动率
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            Dict: 历史波动率
        """
        if len(df) < self.hv_period + 1:
            return {
                'hv': 0.0,
                'percentile': 50,
                'signal': 'NEUTRAL'
            }
        
        # 计算收益率
        returns = df['close'].pct_change()
        
        # 计算波动率（标准差）
        hv = returns.rolling(window=self.hv_period).std()
        
        # 年化（假设是小时线，一年约 252*24 小时）
        hv_annualized = hv * np.sqrt(252 * 24)
        
        current_hv = hv_annualized.iloc[-1]
        
        # 计算历史波动率百分位
        hv_series = hv_annualized.dropna()
        percentile = (hv_series < current_hv).mean() * 100
        
        # 判断信号
        if percentile > 80:
            signal = 'HIGH'  # 高波动率
        elif percentile < 20:
            signal = 'LOW'  # 低波动率
        else:
            signal = 'NORMAL'
        
        return {
            'hv': current_hv * 100,  # 转换为百分比
            'percentile': percentile,
            'signal': signal
        }
    
    def calculate_score(self, df: pd.DataFrame) -> Dict:
        """
        计算波动率因子综合评分
        
        Args:
            df: K 线数据
            
        Returns:
            Dict: 波动率因子评分结果
        """
        # 计算各子因子
        atr_result = self.calculate_atr_change(df)
        bb_result = self.calculate_bollinger_width(df)
        hv_result = self.calculate_historical_volatility(df)
        
        # ATR 评分
        if atr_result['signal'] == 'HIGH_VOLATILITY':
            atr_score = 75  # 高波动率，趋势可能延续
        elif atr_result['signal'] == 'LOW_VOLATILITY':
            atr_score = 25  # 低波动率，可能盘整
        else:
            atr_score = 50
        
        # 布林带评分
        if bb_result['signal'] == 'SQUEEZE':
            bb_score = 75  # 收口，即将突破
        else:
            bb_score = 50
        
        # 历史波动率评分
        if hv_result['signal'] == 'HIGH':
            hv_score = 75  # 高波动率
        elif hv_result['signal'] == 'LOW':
            hv_score = 25  # 低波动率
        else:
            hv_score = 50
        
        # 标准化到 0-100
        atr_score = np.clip(atr_score, 0, 100)
        bb_score = np.clip(bb_score, 0, 100)
        hv_score = np.clip(hv_score, 0, 100)
        
        # 加权平均（ATR 40%, 布林带 40%, HV 20%）
        total_score = (atr_score * 0.4 + bb_score * 0.4 + hv_score * 0.2)
        
        # 判断信号
        if total_score > 55:
            signal = 'HIGH_VOLATILITY'
        elif total_score < 45:
            signal = 'LOW_VOLATILITY'
        else:
            signal = 'NORMAL'
        
        return {
            'factor_name': 'Volatility',
            'weight': 0.2,
            'atr': atr_result,
            'bollinger': bb_result,
            'historical_volatility': hv_result,
            'sub_scores': {
                'atr': atr_score,
                'bollinger': bb_score,
                'hv': hv_score
            },
            'total_score': total_score,
            'signal': signal
        }


def main():
    """测试函数"""
    # 获取测试数据
    symbol = "EURUSD"
    
    if not mt5.initialize():
        print("[ERROR] MT5 初始化失败")
        return
    
    # 获取 K 线数据
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    
    if rates is None or len(rates) == 0:
        print("[ERROR] 获取数据失败")
        mt5.shutdown()
        return
    
    df = pd.DataFrame(rates)
    
    # 计算波动率因子
    factor = VolatilityFactor()
    result = factor.calculate_score(df)
    
    print("=" * 80)
    print(f"{symbol} 波动率因子分析")
    print("=" * 80)
    print(f"ATR 变化：{result['atr']['atr_change']:.2f}% ({result['atr']['signal']})")
    print(f"布林带宽度：{result['bollinger']['width']:.2f}% ({result['bollinger']['signal']})")
    print(f"历史波动率：{result['historical_volatility']['hv']:.2f}% (百分位：{result['historical_volatility']['percentile']:.0f}%)")
    print(f"因子评分：{result['total_score']:.1f}/100")
    print(f"波动率状态：{result['signal']}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
