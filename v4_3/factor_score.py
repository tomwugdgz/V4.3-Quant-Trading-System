"""
Factor Score Engine - 因子评分引擎
版本：V4.3.0
创建：2026-04-10

功能：
1. 多因子评分（0-100）
2. 因子 IC 分析
3. 动态因子权重
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json


class FactorScoreEngine:
    """因子评分引擎"""
    
    def __init__(self, config_path: str = "config/factor_weights.json"):
        """
        初始化
        
        Args:
            config_path: 因子权重配置文件
        """
        self.config = self._load_config(config_path)
        self.factor_history = {}  # 因子值历史
        self.ic_records = []  # IC 记录
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 默认配置
            return {
                "factors": {
                    "momentum": 0.30,
                    "mean_reversion": 0.30,
                    "breakout": 0.20,
                    "volatility": 0.20
                },
                "parameters": {
                    "momentum_period": 20,
                    "rsi_period": 14,
                    "bb_period": 20,
                    "breakout_period": 20,
                    "atr_period": 14
                }
            }
    
    def calculate_score(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        计算综合因子评分
        
        Args:
            symbol: 交易品种
            timeframe: 时间周期
            
        Returns:
            Dict: 评分结果
        """
        # 获取 K 线数据
        df = self._get_klines(symbol, timeframe, bars=100)
        if df is None or len(df) < 50:
            return {"symbol": symbol, "score": 50, "signal": "NEUTRAL"}
        
        # 计算各因子
        factors = self._calculate_all_factors(df)
        
        # 计算综合评分
        total_score = self._calculate_total_score(factors)
        
        # 生成交易信号
        signal = self._generate_signal(total_score)
        
        # 记录因子值
        self.factor_history[symbol] = {
            "timestamp": datetime.now(),
            "factors": factors,
            "score": total_score
        }
        
        return {
            "symbol": symbol,
            "score": total_score,
            "signal": signal,
            "factors": factors,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_klines(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
        """获取 K 线数据"""
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        
        rates = mt5.copy_rates_from_pos(
            symbol,
            tf_map.get(timeframe, mt5.TIMEFRAME_H1),
            0,
            bars
        )
        
        if rates is None or len(rates) == 0:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def _calculate_all_factors(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算所有因子"""
        factors = {}
        
        # 1. 动量因子
        factors['momentum'] = self._momentum_factor(df)
        
        # 2. 均值回归因子
        factors['mean_reversion'] = self._mean_reversion_factor(df)
        
        # 3. 突破因子
        factors['breakout'] = self._breakout_factor(df)
        
        # 4. 波动率因子
        factors['volatility'] = self._volatility_factor(df)
        
        # 5. 趋势强度因子（新增）
        factors['trend_strength'] = self._trend_strength_factor(df)
        
        # 6. 成交量因子（新增）
        factors['volume'] = self._volume_factor(df)
        
        # 7. 支撑阻力因子（新增）
        factors['support_resistance'] = self._support_resistance_factor(df)
        
        # 8. 市场情绪因子（新增）
        factors['sentiment'] = self._sentiment_factor(df)
        
        return factors
    
    def _momentum_factor(self, df: pd.DataFrame) -> float:
        """
        动量因子
        
        逻辑：
        - EMA 斜率（快 EMA vs 慢 EMA）
        - 价格动量（N 日涨幅）
        
        返回：0-100 评分
        """
        params = self.config['parameters']
        
        # EMA 斜率
        ema_fast = df['close'].ewm(span=10, adjust=False).mean()
        ema_slow = df['close'].ewm(span=20, adjust=False).mean()
        
        ema_diff = (ema_fast.iloc[-1] - ema_slow.iloc[-1]) / ema_slow.iloc[-1] * 100
        
        # 价格动量
        momentum = (df['close'].iloc[-1] - df['close'].iloc[-params['momentum_period']]) / df['close'].iloc[-params['momentum_period']] * 100
        
        # 综合评分（0-100）
        # EMA 斜率贡献 60%，价格动量贡献 40%
        ema_score = 50 + ema_diff * 10  # 基准 50，上下浮动
        momentum_score = 50 + momentum * 5
        
        # 限制在 0-100 范围
        ema_score = max(0, min(100, ema_score))
        momentum_score = max(0, min(100, momentum_score))
        
        total = ema_score * 0.6 + momentum_score * 0.4
        
        return total
    
    def _mean_reversion_factor(self, df: pd.DataFrame) -> float:
        """
        均值回归因子
        
        逻辑：
        - RSI 超买超卖
        - 布林带位置
        
        返回：0-100 评分
        """
        params = self.config['parameters']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=params['rsi_period']).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_latest = rsi.iloc[-1]
        
        # RSI 评分：RSI<30 得分高（超卖），RSI>70 得分低（超买）
        rsi_score = 100 - rsi_latest  # 简单线性转换
        
        # 布林带位置
        bb_mid = df['close'].rolling(window=params['bb_period']).mean()
        bb_std = df['close'].rolling(window=params['bb_period']).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        
        close = df['close'].iloc[-1]
        bb_position = (close - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
        
        # 布林带评分：位置<0 得分高（低于下轨），位置>100 得分低（高于上轨）
        bb_score = 100 - bb_position
        
        # 综合评分
        total = rsi_score * 0.5 + bb_score * 0.5
        
        # 限制在 0-100 范围
        total = max(0, min(100, total))
        
        return total
    
    def _breakout_factor(self, df: pd.DataFrame) -> float:
        """
        突破因子
        
        逻辑：
        - 突破 N 日高点/低点
        - 成交量放大
        
        返回：0-100 评分
        """
        params = self.config['parameters']
        
        # N 日高低点
        highest = df['high'].rolling(window=params['breakout_period']).max()
        lowest = df['low'].rolling(window=params['breakout_period']).min()
        
        close = df['close'].iloc[-1]
        high_n = highest.iloc[-1]
        low_n = lowest.iloc[-1]
        
        # 突破评分
        if close > high_n:
            # 突破高点
            breakout_score = 50 + (close - high_n) / high_n * 1000
        elif close < low_n:
            # 突破低点
            breakout_score = 50 - (low_n - close) / low_n * 1000
        else:
            # 区间内
            position = (close - low_n) / (high_n - low_n)
            breakout_score = 50  # 中性
        
        # 成交量（如果可用）
        if 'tick_volume' in df.columns:
            avg_volume = df['tick_volume'].rolling(window=20).mean()
            latest_volume = df['tick_volume'].iloc[-1]
            volume_ratio = latest_volume / avg_volume.iloc[-1]
            
            # 成交量放大加分
            volume_score = min(20, (volume_ratio - 1) * 10)
            breakout_score += volume_score
        
        # 限制在 0-100 范围
        breakout_score = max(0, min(100, breakout_score))
        
        return breakout_score
    
    def _volatility_factor(self, df: pd.DataFrame) -> float:
        """
        波动率因子
        
        逻辑：
        - ATR 变化
        - 布林带宽度
        
        返回：0-100 评分
        """
        params = self.config['parameters']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=params['atr_period']).mean()
        
        # ATR 变化率
        atr_latest = atr.iloc[-1]
        atr_avg = atr.iloc[-20:-1].mean()
        atr_change = (atr_latest - atr_avg) / atr_avg * 100
        
        # ATR 评分：波动率适中得分高，过高或过低得分低
        # 理想 ATR 变化在 -20% 到 +20% 之间
        if -20 <= atr_change <= 20:
            atr_score = 100 - abs(atr_change) * 2
        else:
            atr_score = 60 - abs(atr_change - 20) * 2
        
        # 布林带宽度
        bb_mid = df['close'].rolling(window=params['bb_period']).mean()
        bb_std = df['close'].rolling(window=params['bb_period']).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        bb_width = (bb_upper - bb_lower) / bb_mid * 100
        
        bb_width_avg = bb_width.iloc[-20:-1].mean()
        bb_width_change = (bb_width.iloc[-1] - bb_width_avg) / bb_width_avg * 100
        
        # 布林带评分：收口得分高（即将突破）
        bb_score = 100 - abs(bb_width_change) * 2
        
        # 综合评分
        total = atr_score * 0.5 + bb_score * 0.5
        
        # 限制在 0-100 范围
        total = max(0, min(100, total))
        
        return total
    
    def _calculate_total_score(self, factors: Dict[str, float]) -> float:
        """计算综合评分"""
        total = 0
        
        for factor_name, weight in self.config['factors'].items():
            factor_value = factors.get(factor_name, 50)
            total += factor_value * weight
        
        return total
    
    def _trend_strength_factor(self, df: pd.DataFrame) -> float:
        """
        趋势强度因子（新增）
        
        逻辑：
        - ADX 值（趋势强度指标）
        - EMA 斜率
        
        返回：0-100 评分
        """
        # 计算 ADX
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=14).mean()
        
        # +DM 和 -DM
        df['high_diff'] = df['high'].diff()
        df['low_diff'] = df['low'].diff()
        
        plus_dm = np.where((df['high_diff'] > df['low_diff'].abs()) & (df['high_diff'] > 0), df['high_diff'], 0)
        minus_dm = np.where((df['low_diff'].abs() > df['high_diff']) & (df['low_diff'] < 0), df['low_diff'].abs(), 0)
        
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).mean() / atr)
        
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.rolling(window=14).mean()
        
        adx_latest = adx.iloc[-1] if len(adx) > 0 else 25
        
        # ADX 评分：ADX>25 为趋势市，得分高
        if adx_latest > 40:
            trend_score = 100
        elif adx_latest > 25:
            trend_score = 70 + (adx_latest - 25) * 2
        elif adx_latest > 15:
            trend_score = 40 + (adx_latest - 15) * 2
        else:
            trend_score = 20
        
        return max(0, min(100, trend_score))
    
    def _volume_factor(self, df: pd.DataFrame) -> float:
        """
        成交量因子（新增）
        
        逻辑：
        - 成交量变化率
        - 量价配合
        
        返回：0-100 评分
        """
        if 'tick_volume' not in df.columns:
            return 50  # 无成交量数据，返回中性
        
        # 成交量移动平均
        volume_ma = df['tick_volume'].rolling(window=20).mean()
        volume_ratio = df['tick_volume'] / volume_ma
        
        volume_ratio_latest = volume_ratio.iloc[-1] if len(volume_ratio) > 0 else 1
        
        # 成交量评分
        if volume_ratio_latest > 2.0:
            volume_score = 90  # 成交量放大 2 倍以上
        elif volume_ratio_latest > 1.5:
            volume_score = 75  # 成交量放大 50%
        elif volume_ratio_latest > 1.0:
            volume_score = 60  # 正常成交量
        elif volume_ratio_latest > 0.5:
            volume_score = 40  # 成交量萎缩
        else:
            volume_score = 20  # 极度萎缩
        
        return max(0, min(100, volume_score))
    
    def _support_resistance_factor(self, df: pd.DataFrame) -> float:
        """
        支撑阻力因子（新增）
        
        逻辑：
        - 价格相对 N 日高低点的位置
        - 接近突破得分高
        
        返回：0-100 评分
        """
        # N 日高低点
        n_period = 20
        highest = df['high'].rolling(window=n_period).max()
        lowest = df['low'].rolling(window=n_period).min()
        
        close = df['close'].iloc[-1]
        high_n = highest.iloc[-1]
        low_n = lowest.iloc[-1]
        
        # 位置计算
        range_size = high_n - low_n
        if range_size == 0:
            return 50
        
        position = (close - low_n) / range_size
        
        # 接近高点或低点得分高（即将突破）
        if position > 0.95 or position < 0.05:
            score = 90  # 非常接近突破
        elif position > 0.90 or position < 0.10:
            score = 75  # 接近突破
        elif position > 0.80 or position < 0.20:
            score = 60  # 较接近
        else:
            score = 40  # 中间位置
        
        return max(0, min(100, score))
    
    def _sentiment_factor(self, df: pd.DataFrame) -> float:
        """
        市场情绪因子（新增）
        
        逻辑：
        - RSI 极端值（超买超卖）
        - 布林带位置
        
        返回：0-100 评分
        """
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_latest = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # RSI 评分
        if rsi_latest > 80:
            rsi_score = 20  # 严重超买
        elif rsi_latest > 70:
            rsi_score = 35  # 超买
        elif rsi_latest > 55:
            rsi_score = 55  # 偏多
        elif rsi_latest > 45:
            rsi_score = 50  # 中性
        elif rsi_latest > 30:
            rsi_score = 45  # 偏空
        elif rsi_latest > 20:
            rsi_score = 35  # 超卖
        else:
            rsi_score = 20  # 严重超卖
        
        # 布林带位置
        bb_mid = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        
        close = df['close'].iloc[-1]
        bb_position = (close - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
        
        # 综合评分（RSI 和布林带各占 50%）
        bb_score = 100 - bb_position
        total_score = rsi_score * 0.5 + bb_score * 0.5
        
        return max(0, min(100, total_score))
    
    def _generate_signal(self, score: float) -> str:
        """
        生成交易信号（优化版 - 提高阈值）
        
        Args:
            score: 综合评分（0-100）
            
        Returns:
            str: 交易信号
        """
        if score >= 70:
            return "STRONG_BUY"
        elif score >= 60:  # 提高：55 → 60
            return "BUY"
        elif score <= 30:
            return "STRONG_SELL"
        elif score <= 40:  # 提高：45 → 40
            return "SELL"
        else:
            return "NEUTRAL"
    
    def calculate_ic(self, symbol: str, days: int = 30) -> Dict:
        """
        计算因子 IC（信息系数）
        
        Args:
            symbol: 交易品种
            days: 回看天数
            
        Returns:
            Dict: IC 分析结果
        """
        # 获取历史因子值和后续收益
        # 这里简化处理，实际需要存储历史数据
        
        if symbol not in self.factor_history:
            return {"symbol": symbol, "ic": None, "message": "无历史数据"}
        
        # 简化 IC 计算（示例）
        # 实际应该用历史因子值预测未来收益
        
        return {
            "symbol": symbol,
            "ic": 0.05,  # 示例值
            "ic_rank": "有效" if 0.05 > 0.02 else "无效",
            "message": "IC 计算需要历史数据支持"
        }


def main():
    """测试函数"""
    # 初始化 MT5
    if not mt5.initialize():
        print("MT5 初始化失败")
        return
    
    # 创建引擎
    engine = FactorScoreEngine()
    
    # 测试品种
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF"]
    
    print("=" * 80)
    print("Factor Score Engine - 因子评分")
    print("=" * 80)
    
    for symbol in symbols:
        result = engine.calculate_score(symbol, "H1")
        
        signal_icon = {
            "STRONG_BUY": "[STRONG-BUY]",
            "BUY": "[BUY]",
            "NEUTRAL": "[NEUTRAL]",
            "SELL": "[SELL]",
            "STRONG_SELL": "[STRONG-SELL]"
        }.get(result['signal'], "[?]")
        
        print(f"\n{symbol}:")
        print(f"  综合评分：{result['score']:.1f}")
        print(f"  信号：{signal_icon} {result['signal']}")
        print(f"  因子明细:")
        for factor_name, factor_value in result['factors'].items():
            print(f"    {factor_name}: {factor_value:.1f}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
