"""
均值回归因子
版本：V4.3.0
创建：2026-04-11

功能：
1. RSI 超买超卖
2. 布林带位置
3. 乖离率
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict


class MeanReversionFactor:
    """均值回归因子"""
    
    def __init__(self):
        """初始化"""
        self.rsi_period = 14
        self.bb_period = 20
        self.bb_std = 2.0
        self.bias_period = 20
    
    def calculate_rsi(self, df: pd.DataFrame) -> Dict:
        """
        计算 RSI
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            Dict: RSI 指标
        """
        if len(df) < self.rsi_period + 1:
            return {
                'rsi': 50,
                'signal': 'NEUTRAL'
            }
        
        # 计算价格变化
        delta = df['close'].diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        # 计算 RS 和 RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        # 判断信号
        if current_rsi > 70:
            signal = 'OVERBOUGHT'  # 超买，看跌
        elif current_rsi < 30:
            signal = 'OVERSOLD'  # 超卖，看涨
        else:
            signal = 'NEUTRAL'
        
        return {
            'rsi': current_rsi,
            'signal': signal
        }
    
    def calculate_bollinger_position(self, df: pd.DataFrame) -> Dict:
        """
        计算布林带位置
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            Dict: 布林带指标
        """
        if len(df) < self.bb_period:
            return {
                'position': 0.5,
                'signal': 'NEUTRAL'
            }
        
        # 计算中轨
        middle = df['close'].rolling(window=self.bb_period).mean()
        
        # 计算标准差
        std = df['close'].rolling(window=self.bb_period).std()
        
        # 计算上下轨
        upper = middle + (self.bb_std * std)
        lower = middle - (self.bb_std * std)
        
        # 当前位置
        current_price = df['close'].iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        current_middle = middle.iloc[-1]
        
        # 计算位置（0-1 之间，0=下轨，1=上轨）
        position = (current_price - current_lower) / (current_upper - current_lower)
        
        # 判断信号
        if position > 0.8:
            signal = 'OVERBOUGHT'  # 接近上轨，看跌
        elif position < 0.2:
            signal = 'OVERSOLD'  # 接近下轨，看涨
        else:
            signal = 'NEUTRAL'
        
        return {
            'position': position,
            'upper': current_upper,
            'middle': current_middle,
            'lower': current_lower,
            'signal': signal
        }
    
    def calculate_bias(self, df: pd.DataFrame) -> float:
        """
        计算乖离率（价格与均线的偏离程度）
        
        Args:
            df: K 线数据（包含 close 列）
            
        Returns:
            float: 乖离率（百分比）
        """
        if len(df) < self.bias_period:
            return 0.0
        
        # 计算均线
        ma = df['close'].rolling(window=self.bias_period).mean()
        
        # 计算乖离率
        current_price = df['close'].iloc[-1]
        current_ma = ma.iloc[-1]
        
        bias = (current_price - current_ma) / current_ma
        
        return bias * 100  # 转换为百分比
    
    def calculate_score(self, df: pd.DataFrame) -> Dict:
        """
        计算均值回归因子综合评分
        
        Args:
            df: K 线数据
            
        Returns:
            Dict: 均值回归因子评分结果
        """
        # 计算各子因子
        rsi_result = self.calculate_rsi(df)
        bb_result = self.calculate_bollinger_position(df)
        bias = self.calculate_bias(df)
        
        # RSI 评分（反向：超买=低分，超卖=高分）
        rsi_score = 50 - (rsi_result['rsi'] - 50)
        
        # 布林带评分（反向：高位=低分，低位=高分）
        bb_score = 50 - (bb_result['position'] - 0.5) * 100
        
        # 乖离率评分（反向：正乖离=低分，负乖离=高分）
        bias_score = 50 - (bias * 5)
        
        # 标准化到 0-100
        rsi_score = np.clip(rsi_score, 0, 100)
        bb_score = np.clip(bb_score, 0, 100)
        bias_score = np.clip(bias_score, 0, 100)
        
        # 加权平均（RSI 40%, 布林带 40%, 乖离率 20%）
        total_score = (rsi_score * 0.4 + bb_score * 0.4 + bias_score * 0.2)
        
        # 判断信号
        if total_score > 55:
            signal = 'BUY'  # 价格偏低，可能反弹
        elif total_score < 45:
            signal = 'SELL'  # 价格偏高，可能回调
        else:
            signal = 'NEUTRAL'
        
        return {
            'factor_name': 'Mean Reversion',
            'weight': 0.3,
            'rsi': rsi_result,
            'bollinger': bb_result,
            'bias': bias,
            'sub_scores': {
                'rsi': rsi_score,
                'bollinger': bb_score,
                'bias': bias_score
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
    
    # 计算均值回归因子
    factor = MeanReversionFactor()
    result = factor.calculate_score(df)
    
    print("=" * 80)
    print(f"{symbol} 均值回归因子分析")
    print("=" * 80)
    print(f"RSI: {result['rsi']['rsi']:.1f} ({result['rsi']['signal']})")
    print(f"布林带位置：{result['bollinger']['position']:.2f} ({result['bollinger']['signal']})")
    print(f"乖离率：{result['bias']:.2f}%")
    print(f"因子评分：{result['total_score']:.1f}/100")
    print(f"交易信号：{result['signal']}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
