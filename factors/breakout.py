"""
突破因子
版本：V4.3.0
创建：2026-04-11

功能：
1. N 日高点/低点突破
2. 成交量放大
3. 形态识别
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict


class BreakoutFactor:
    """突破因子"""
    
    def __init__(self):
        """初始化"""
        self.breakout_period = 20
        self.volume_period = 20
        self.volume_threshold = 1.5  # 成交量放大阈值
    
    def calculate_price_breakout(self, df: pd.DataFrame) -> Dict:
        """
        计算价格突破（N 日高点/低点）
        
        Args:
            df: K 线数据（包含 high, low, close 列）
            
        Returns:
            Dict: 突破信号
        """
        if len(df) < self.breakout_period + 1:
            return {
                'breakout_type': 'NONE',
                'strength': 0.0,
                'signal': 'NEUTRAL'
            }
        
        # 计算 N 日高低点
        highest_high = df['high'].rolling(window=self.breakout_period).max()
        lowest_low = df['low'].rolling(window=self.breakout_period).min()
        
        # 当前价格
        current_close = df['close'].iloc[-1]
        prev_high = highest_high.iloc[-2]  # 前 N 日最高
        prev_low = lowest_low.iloc[-2]  # 前 N 日最低
        
        # 判断突破
        breakout_type = 'NONE'
        strength = 0.0
        
        if current_close > prev_high:
            breakout_type = 'UPPER'  # 向上突破
            strength = (current_close - prev_high) / prev_high
        elif current_close < prev_low:
            breakout_type = 'LOWER'  # 向下跌破
            strength = (prev_low - current_close) / prev_low
        
        # 判断信号
        if breakout_type == 'UPPER' and strength > 0.001:  # 突破幅度>0.1%
            signal = 'BULLISH'
        elif breakout_type == 'LOWER' and strength > 0.001:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
            breakout_type = 'NONE'
        
        return {
            'breakout_type': breakout_type,
            'strength': strength * 100,  # 转换为百分比
            'signal': signal,
            'resistance': prev_high,
            'support': prev_low
        }
    
    def calculate_volume_spike(self, df: pd.DataFrame) -> Dict:
        """
        计算成交量放大
        
        Args:
            df: K 线数据（包含 tick_volume 列，MT5 使用 tick_volume）
            
        Returns:
            Dict: 成交量分析
        """
        if len(df) < self.volume_period + 1:
            return {
                'volume_ratio': 1.0,
                'is_spike': False,
                'signal': 'NEUTRAL'
            }
        
        # 计算平均成交量（MT5 使用 tick_volume）
        volume_col = 'tick_volume' if 'tick_volume' in df.columns else 'volume'
        avg_volume = df[volume_col].rolling(window=self.volume_period).mean()
        
        # 当前成交量
        current_volume = df[volume_col].iloc[-1]
        avg_vol = avg_volume.iloc[-1]
        
        # 成交量比率
        volume_ratio = current_volume / avg_vol if avg_vol > 0 else 1.0
        
        # 判断是否放量
        is_spike = volume_ratio > self.volume_threshold
        
        # 判断信号
        if is_spike:
            signal = 'ACTIVE'  # 成交活跃
        else:
            signal = 'NORMAL'  # 成交正常
        
        return {
            'volume_ratio': volume_ratio,
            'current_volume': current_volume,
            'avg_volume': avg_vol,
            'is_spike': is_spike,
            'signal': signal
        }
    
    def calculate_pattern(self, df: pd.DataFrame) -> Dict:
        """
        识别简单形态（简化版）
        
        Args:
            df: K 线数据
            
        Returns:
            Dict: 形态识别结果
        """
        if len(df) < 5:
            return {
                'pattern': 'NONE',
                'signal': 'NEUTRAL'
            }
        
        # 最近 5 根 K 线
        recent = df.tail(5)
        
        # 判断趋势
        highs = recent['high'].values
        lows = recent['low'].values
        closes = recent['close'].values
        
        # 简化形态识别
        pattern = 'NONE'
        signal = 'NEUTRAL'
        
        # 上升形态：高点抬高，低点抬高
        if highs[-1] > highs[0] and lows[-1] > lows[0]:
            pattern = 'UPTREND'
            signal = 'BULLISH'
        # 下降形态：高点降低，低点降低
        elif highs[-1] < highs[0] and lows[-1] < lows[0]:
            pattern = 'DOWNTREND'
            signal = 'BEARISH'
        # 震荡形态
        else:
            pattern = 'RANGING'
            signal = 'NEUTRAL'
        
        return {
            'pattern': pattern,
            'signal': signal
        }
    
    def calculate_score(self, df: pd.DataFrame) -> Dict:
        """
        计算突破因子综合评分
        
        Args:
            df: K 线数据
            
        Returns:
            Dict: 突破因子评分结果
        """
        # 计算各子因子
        breakout_result = self.calculate_price_breakout(df)
        volume_result = self.calculate_volume_spike(df)
        pattern_result = self.calculate_pattern(df)
        
        # 突破评分
        if breakout_result['breakout_type'] == 'UPPER':
            breakout_score = 50 + (breakout_result['strength'] * 10)
        elif breakout_result['breakout_type'] == 'LOWER':
            breakout_score = 50 - (breakout_result['strength'] * 10)
        else:
            breakout_score = 50
        
        # 成交量评分
        if volume_result['is_spike']:
            volume_score = 75  # 放量加分
        else:
            volume_score = 50
        
        # 形态评分
        if pattern_result['pattern'] == 'UPTREND':
            pattern_score = 75
        elif pattern_result['pattern'] == 'DOWNTREND':
            pattern_score = 25
        else:
            pattern_score = 50
        
        # 标准化到 0-100
        breakout_score = np.clip(breakout_score, 0, 100)
        volume_score = np.clip(volume_score, 0, 100)
        pattern_score = np.clip(pattern_score, 0, 100)
        
        # 加权平均（突破 50%, 成交量 30%, 形态 20%）
        total_score = (breakout_score * 0.5 + volume_score * 0.3 + pattern_score * 0.2)
        
        # 判断信号
        if total_score > 55:
            signal = 'BUY'
        elif total_score < 45:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'factor_name': 'Breakout',
            'weight': 0.2,
            'breakout': breakout_result,
            'volume': volume_result,
            'pattern': pattern_result,
            'sub_scores': {
                'breakout': breakout_score,
                'volume': volume_score,
                'pattern': pattern_score
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
    
    # 计算突破因子
    factor = BreakoutFactor()
    result = factor.calculate_score(df)
    
    print("=" * 80)
    print(f"{symbol} 突破因子分析")
    print("=" * 80)
    print(f"突破类型：{result['breakout']['breakout_type']}")
    print(f"突破强度：{result['breakout']['strength']:.3f}%")
    print(f"成交量比率：{result['volume']['volume_ratio']:.2f}x")
    print(f"形态：{result['pattern']['pattern']}")
    print(f"因子评分：{result['total_score']:.1f}/100")
    print(f"交易信号：{result['signal']}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
