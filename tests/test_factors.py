"""
因子测试套件
版本：V4.3.0
创建：2026-04-11
"""

import pytest
import numpy as np


class TestMomentumFactor:
    """动量因子测试"""
    
    def test_ema_slope(self, sample_kline_data, factor_analyzers):
        """测试 EMA 斜率计算"""
        factor = factor_analyzers['momentum']
        result = factor.calculate_ema_slope(sample_kline_data)
        
        assert isinstance(result, float)
        assert -10 < result < 10  # 斜率应该在合理范围内
    
    def test_price_momentum(self, sample_kline_data, factor_analyzers):
        """测试价格动量计算"""
        factor = factor_analyzers['momentum']
        result = factor.calculate_price_momentum(sample_kline_data)
        
        assert isinstance(result, float)
        assert -50 < result < 50  # 动量应该在合理范围内
    
    def test_macd_signal(self, sample_kline_data, factor_analyzers):
        """测试 MACD 信号计算"""
        factor = factor_analyzers['momentum']
        result = factor.calculate_macd_signal(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result
        assert 'trend' in result
    
    def test_total_score(self, sample_kline_data, factor_analyzers):
        """测试综合评分"""
        factor = factor_analyzers['momentum']
        result = factor.calculate_score(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'total_score' in result
        assert 0 <= result['total_score'] <= 100
        assert 'signal' in result
        assert result['signal'] in ['BULLISH', 'BEARISH', 'NEUTRAL']


class TestMeanReversionFactor:
    """均值回归因子测试"""
    
    def test_rsi(self, sample_kline_data, factor_analyzers):
        """测试 RSI 计算"""
        factor = factor_analyzers['mean_reversion']
        result = factor.calculate_rsi(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'rsi' in result
        assert 0 <= result['rsi'] <= 100
    
    def test_bollinger_position(self, sample_kline_data, factor_analyzers):
        """测试布林带位置计算"""
        factor = factor_analyzers['mean_reversion']
        result = factor.calculate_bollinger_position(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'position' in result
        assert 0 <= result['position'] <= 1
    
    def test_bias(self, sample_kline_data, factor_analyzers):
        """测试乖离率计算"""
        factor = factor_analyzers['mean_reversion']
        result = factor.calculate_bias(sample_kline_data)
        
        assert isinstance(result, float)
        assert -20 < result < 20  # 乖离率应该在合理范围内
    
    def test_total_score(self, sample_kline_data, factor_analyzers):
        """测试综合评分"""
        factor = factor_analyzers['mean_reversion']
        result = factor.calculate_score(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'total_score' in result
        assert 0 <= result['total_score'] <= 100


class TestBreakoutFactor:
    """突破因子测试"""
    
    def test_price_breakout(self, sample_kline_data, factor_analyzers):
        """测试价格突破计算"""
        factor = factor_analyzers['breakout']
        result = factor.calculate_price_breakout(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'breakout_type' in result
        assert 'strength' in result
        assert 'signal' in result
    
    def test_volume_spike(self, sample_kline_data, factor_analyzers):
        """测试成交量放大计算"""
        factor = factor_analyzers['breakout']
        result = factor.calculate_volume_spike(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'volume_ratio' in result
        assert 'is_spike' in result
    
    def test_total_score(self, sample_kline_data, factor_analyzers):
        """测试综合评分"""
        factor = factor_analyzers['breakout']
        result = factor.calculate_score(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'total_score' in result
        assert 0 <= result['total_score'] <= 100


class TestVolatilityFactor:
    """波动率因子测试"""
    
    def test_atr_change(self, sample_kline_data, factor_analyzers):
        """测试 ATR 变化计算"""
        factor = factor_analyzers['volatility']
        result = factor.calculate_atr_change(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'atr' in result
        assert 'atr_change' in result
    
    def test_bollinger_width(self, sample_kline_data, factor_analyzers):
        """测试布林带宽度计算"""
        factor = factor_analyzers['volatility']
        result = factor.calculate_bollinger_width(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'width' in result
        assert result['width'] >= 0
    
    def test_historical_volatility(self, sample_kline_data, factor_analyzers):
        """测试历史波动率计算"""
        factor = factor_analyzers['volatility']
        result = factor.calculate_historical_volatility(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'hv' in result
        assert 'percentile' in result
        assert 0 <= result['percentile'] <= 100
    
    def test_total_score(self, sample_kline_data, factor_analyzers):
        """测试综合评分"""
        factor = factor_analyzers['volatility']
        result = factor.calculate_score(sample_kline_data)
        
        assert isinstance(result, dict)
        assert 'total_score' in result
        assert 0 <= result['total_score'] <= 100
