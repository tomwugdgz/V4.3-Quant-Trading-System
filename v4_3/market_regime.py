"""
Market Regime Agent - 市场状态判断模块
版本：V4.3.0
创建：2026-04-10

功能：
1. 判断市场状态（趋势/震荡/高波动）
2. 动态调整信号阈值
3. 为策略选择提供依据
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Tuple
import json


class MarketRegime(Enum):
    """市场状态枚举"""
    TRENDING_UP = "TRENDING_UP"          # 上涨趋势
    TRENDING_DOWN = "TRENDING_DOWN"      # 下跌趋势
    RANGING = "RANGING"                   # 震荡市
    HIGH_VOLATILITY = "HIGH_VOLATILITY"  # 高波动
    UNKNOWN = "UNKNOWN"                   # 未知


class MarketRegimeAgent:
    """市场状态判断 Agent"""
    
    def __init__(self, config_path: str = "config/regime_config.json"):
        """
        初始化
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.regime_history = []  # 状态历史
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 默认配置
            return {
                "adx_threshold": 25,
                "adx_low_threshold": 20,
                "atr_multiplier": 1.5,
                "atr_period": 14,
                "bb_period": 20,
                "bb_std": 2.0,
                "ema_fast": 10,
                "ema_slow": 20
            }
    
    def detect_regime(self, symbol: str, timeframe: str = "H1") -> MarketRegime:
        """
        检测市场状态
        
        Args:
            symbol: 交易品种
            timeframe: 时间周期
            
        Returns:
            MarketRegime: 市场状态
        """
        # 获取 K 线数据
        df = self._get_klines(symbol, timeframe, bars=100)
        if df is None or len(df) < 50:
            return MarketRegime.UNKNOWN
        
        # 计算指标
        df = self._calculate_indicators(df)
        
        # 判断市场状态
        regime = self._classify_regime(df)
        
        # 记录历史
        self.regime_history.append({
            "timestamp": datetime.now(),
            "symbol": symbol,
            "regime": regime.value
        })
        
        return regime
    
    def _get_klines(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
        """获取 K 线数据"""
        # 时间周期映射
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
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # EMA
        df['ema_fast'] = df['close'].ewm(
            span=self.config['ema_fast'],
            adjust=False
        ).mean()
        
        df['ema_slow'] = df['close'].ewm(
            span=self.config['ema_slow'],
            adjust=False
        ).mean()
        
        # ADX
        df = self._calculate_adx(df, period=14)
        
        # ATR
        df['atr'] = self._calculate_atr(df, period=self.config['atr_period'])
        
        # 布林带
        df['bb_mid'] = df['close'].rolling(
            window=self.config['bb_period']
        ).mean()
        
        bb_std = df['close'].rolling(
            window=self.config['bb_period']
        ).std()
        
        df['bb_upper'] = df['bb_mid'] + self.config['bb_std'] * bb_std
        df['bb_lower'] = df['bb_mid'] - self.config['bb_std'] * bb_std
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        
        return df
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算 ADX"""
        # +DM 和 -DM
        df['high_diff'] = df['high'].diff()
        df['low_diff'] = df['low'].diff()
        
        df['plus_dm'] = np.where(
            (df['high_diff'] > df['low_diff'].abs()) & (df['high_diff'] > 0),
            df['high_diff'],
            0
        )
        
        df['minus_dm'] = np.where(
            (df['low_diff'].abs() > df['high_diff']) & (df['low_diff'] < 0),
            df['low_diff'].abs(),
            0
        )
        
        # TR
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = (df['high'] - df['close'].shift()).abs()
        df['tr3'] = (df['low'] - df['close'].shift()).abs()
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # 平滑
        df['atr'] = df['tr'].rolling(window=period).mean()
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr'])
        
        # DX 和 ADX
        df['dx'] = 100 * ((df['plus_di'] - df['minus_di']).abs() / 
                         (df['plus_di'] + df['minus_di']))
        df['adx'] = df['dx'].rolling(window=period).mean()
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算 ATR"""
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def _classify_regime(self, df: pd.DataFrame) -> MarketRegime:
        """分类市场状态"""
        latest = df.iloc[-1]
        
        # 检查高波动
        avg_atr = df['atr'].iloc[-20:-1].mean()
        if latest['atr'] > self.config['atr_multiplier'] * avg_atr:
            return MarketRegime.HIGH_VOLATILITY
        
        # 检查趋势
        adx = latest['adx']
        
        if adx > self.config['adx_threshold']:
            # 强趋势
            if latest['ema_fast'] > latest['ema_slow'] and latest['close'] > latest['ema_slow']:
                return MarketRegime.TRENDING_UP
            elif latest['ema_fast'] < latest['ema_slow'] and latest['close'] < latest['ema_slow']:
                return MarketRegime.TRENDING_DOWN
        
        # 检查震荡
        if adx < self.config['adx_low_threshold']:
            # 布林带收口
            bb_width = latest['bb_width']
            avg_bb_width = df['bb_width'].iloc[-20:-1].mean()
            
            if bb_width < avg_bb_width * 0.8:
                return MarketRegime.RANGING
        
        # 默认：弱趋势
        if latest['ema_fast'] > latest['ema_slow']:
            return MarketRegime.TRENDING_UP
        else:
            return MarketRegime.TRENDING_DOWN
    
    def get_dynamic_threshold(self, regime: MarketRegime) -> float:
        """
        获取动态信号阈值
        
        Args:
            regime: 市场状态
            
        Returns:
            float: 信号强度阈值（百分比）
        """
        thresholds = {
            MarketRegime.TRENDING_UP: 0.08,      # 趋势市，降低阈值
            MarketRegime.TRENDING_DOWN: 0.08,
            MarketRegime.RANGING: 0.15,          # 震荡市，提高阈值
            MarketRegime.HIGH_VOLATILITY: 0.20,  # 高波动，最严格
            MarketRegime.UNKNOWN: 0.10           # 未知，使用默认
        }
        
        return thresholds.get(regime, 0.10)
    
    def get_position_size_multiplier(self, regime: MarketRegime) -> float:
        """
        获取仓位调整系数
        
        Args:
            regime: 市场状态
            
        Returns:
            float: 仓位系数（0.0-1.0）
        """
        multipliers = {
            MarketRegime.TRENDING_UP: 1.0,       # 标准仓位
            MarketRegime.TRENDING_DOWN: 1.0,
            MarketRegime.RANGING: 0.5,           # 半仓
            MarketRegime.HIGH_VOLATILITY: 0.3,   # 轻仓
            MarketRegime.UNKNOWN: 0.5            # 未知，半仓
        }
        
        return multipliers.get(regime, 0.5)
    
    def should_trade(self, regime: MarketRegime) -> bool:
        """
        判断是否应该交易
        
        Args:
            regime: 市场状态
            
        Returns:
            bool: 是否交易
        """
        # 高波动市场谨慎交易
        if regime == MarketRegime.HIGH_VOLATILITY:
            return False
        
        # 未知状态不交易
        if regime == MarketRegime.UNKNOWN:
            return False
        
        return True
    
    def get_regime_report(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        生成市场状态报告
        
        Args:
            symbol: 交易品种
            timeframe: 时间周期
            
        Returns:
            Dict: 市场状态报告
        """
        regime = self.detect_regime(symbol, timeframe)
        threshold = self.get_dynamic_threshold(regime)
        position_multiplier = self.get_position_size_multiplier(regime)
        should_trade = self.should_trade(regime)
        
        report = {
            "symbol": symbol,
            "timeframe": timeframe,
            "regime": regime.value,
            "threshold": threshold,
            "position_multiplier": position_multiplier,
            "should_trade": should_trade,
            "timestamp": datetime.now().isoformat()
        }
        
        return report


def main():
    """测试函数"""
    # 初始化 MT5
    if not mt5.initialize():
        print("MT5 初始化失败")
        return
    
    # 创建 Agent
    agent = MarketRegimeAgent()
    
    # 测试品种
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF"]
    
    print("=" * 80)
    print("Market Regime Agent - 市场状态检测")
    print("=" * 80)
    
    for symbol in symbols:
        report = agent.get_regime_report(symbol, "H1")
        
        regime_icon = {
            "TRENDING_UP": "[UP]",
            "TRENDING_DOWN": "[DOWN]",
            "RANGING": "[FLAT]",
            "HIGH_VOLATILITY": "[VOL]",
            "UNKNOWN": "[?]"
        }.get(report['regime'], "[?]")
        
        trade_icon = "[GO]" if report['should_trade'] else "[NO-GO]"
        
        print(f"\n{symbol}:")
        print(f"  状态：{regime_icon} {report['regime']}")
        print(f"  信号阈值：{report['threshold']:.2f}%")
        print(f"  仓位系数：{report['position_multiplier']:.1f}x")
        print(f"  可交易：{trade_icon}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
