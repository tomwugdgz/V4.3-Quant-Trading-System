"""
动量因子
版本：V4.3.0
创建：2026-04-11

功能：
1. EMA 斜率
2. 价格动量（N 日涨幅）
3. MACD 信号
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, Optional


class MomentumFactor:
    """动量因子"""
    
    def __init__(self):
        """初始化"""
        self.ema_period_short = 10
        self.ema_period_long = 20
        self.momentum_period = 10
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
    
    def calculate_ema_slope(self, df: pd.DataFrame) -> float:
        """
        计算 EMA 斜率
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            float: EMA 斜率（EMA10 - EMA20）/ EMA20
        """
        if len(df) < self.ema_period_long:
            return 0.0
        
        # 计算 EMA
        ema_short = df['close'].ewm(span=self.ema_period_short, adjust=False).mean()
        ema_long = df['close'].ewm(span=self.ema_period_long, adjust=False).mean()
        
        # 计算斜率
        current_short = ema_short.iloc[-1]
        current_long = ema_long.iloc[-1]
        
        slope = (current_short - current_long) / current_long
        
        return slope * 100  # 转换为百分比
    
    def calculate_price_momentum(self, df: pd.DataFrame) -> float:
        """
        计算价格动量（N 日涨幅）
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            float: N 日涨幅（百分比）
        """
        if len(df) < self.momentum_period + 1:
            return 0.0
        
        current_price = df['close'].iloc[-1]
        past_price = df['close'].iloc[-self.momentum_period]
        
        momentum = (current_price - past_price) / past_price
        
        return momentum * 100  # 转换为百分比
    
    def calculate_macd_signal(self, df: pd.DataFrame) -> Dict:
        """
        计算 MACD 信号
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            Dict: MACD 指标
        """
        if len(df) < self.macd_slow + self.macd_signal:
            return {
                'macd': 0.0,
                'signal': 0.0,
                'histogram': 0.0,
                'trend': 'NEUTRAL'
            }
        
        # 计算 EMA
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        
        # MACD 线
        macd_line = ema_fast - ema_slow
        
        # 信号线
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        
        # 柱状图
        histogram = macd_line - signal_line
        
        # 判断趋势
        if macd_line.iloc[-1] > signal_line.iloc[-1] and histogram.iloc[-1] > 0:
            trend = 'BULLISH'
        elif macd_line.iloc[-1] < signal_line.iloc[-1] and histogram.iloc[-1] < 0:
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        return {
            'macd': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1],
            'trend': trend
        }
    
    def calculate_score(self, df: pd.DataFrame) -> Dict:
        """
        计算动量因子综合评分
        
        Args:
            df: K 线数据
            
        Returns:
            Dict: 动量因子评分结果
        """
        # 计算各子因子
        ema_slope = self.calculate_ema_slope(df)
        price_momentum = self.calculate_price_momentum(df)
        macd_result = self.calculate_macd_signal(df)
        
        # 标准化评分（-100 到 100）
        # EMA 斜率评分
        ema_score = np.clip(ema_slope * 10, -100, 100)
        
        # 价格动量评分
        momentum_score = np.clip(price_momentum * 5, -100, 100)
        
        # MACD 评分
        if macd_result['trend'] == 'BULLISH':
            macd_score = 50 + (macd_result['histogram'] * 100)
        elif macd_result['trend'] == 'BEARISH':
            macd_score = -50 + (macd_result['histogram'] * 100)
        else:
            macd_score = 0
        
        macd_score = np.clip(macd_score, -100, 100)
        
        # 加权平均（EMA 40%, 动量 40%, MACD 20%）
        total_score = (ema_score * 0.4 + momentum_score * 0.4 + macd_score * 0.2)
        
        # 转换到 0-100 范围
        normalized_score = (total_score + 100) / 2
        
        return {
            'factor_name': 'Momentum',
            'weight': 0.3,
            'ema_slope': ema_slope,
            'price_momentum': price_momentum,
            'macd': macd_result,
            'sub_scores': {
                'ema': ema_score,
                'momentum': momentum_score,
                'macd': macd_score
            },
            'total_score': normalized_score,
            'signal': 'BULLISH' if normalized_score > 55 else ('BEARISH' if normalized_score < 45 else 'NEUTRAL')
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
    
    # 计算动量因子
    factor = MomentumFactor()
    result = factor.calculate_score(df)
    
    print("=" * 80)
    print(f"{symbol} 动量因子分析")
    print("=" * 80)
    print(f"EMA 斜率：{result['ema_slope']:.4f}%")
    print(f"价格动量：{result['price_momentum']:.2f}%")
    print(f"MACD 趋势：{result['macd']['trend']}")
    print(f"动量评分：{result['total_score']:.1f}/100")
    print(f"交易信号：{result['signal']}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
