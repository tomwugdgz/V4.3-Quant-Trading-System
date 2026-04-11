"""
pytest 配置文件
版本：V4.3.0
创建：2026-04-11
"""

import pytest
import MetaTrader5 as mt5
import pandas as pd
import numpy as np


@pytest.fixture(scope="module")
def mt5_connection():
    """MT5 连接 fixture"""
    if not mt5.initialize():
        pytest.skip("MT5 初始化失败")
    
    yield mt5
    
    mt5.shutdown()


@pytest.fixture
def sample_kline_data():
    """示例 K 线数据"""
    # 生成模拟数据
    np.random.seed(42)
    
    n_periods = 100
    dates = pd.date_range(start='2026-04-01', periods=n_periods, freq='H')
    
    # 随机游走价格
    close = 1.1000 + np.cumsum(np.random.randn(n_periods) * 0.001)
    high = close + np.abs(np.random.randn(n_periods) * 0.0005)
    low = close - np.abs(np.random.randn(n_periods) * 0.0005)
    open_price = close.shift(1).fillna(close.iloc[0])
    
    # 成交量
    volume = np.random.randint(100, 1000, n_periods)
    
    df = pd.DataFrame({
        'time': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    return df


@pytest.fixture
def factor_analyzers():
    """因子分析器集合"""
    from factors.momentum import MomentumFactor
    from factors.mean_reversion import MeanReversionFactor
    from factors.breakout import BreakoutFactor
    from factors.volatility import VolatilityFactor
    
    return {
        'momentum': MomentumFactor(),
        'mean_reversion': MeanReversionFactor(),
        'breakout': BreakoutFactor(),
        'volatility': VolatilityFactor()
    }


@pytest.fixture
def review_agent():
    """Review Agent fixture"""
    from v4_3.review_agent import ReviewAgent
    return ReviewAgent(db_path=":memory:")  # 使用内存数据库
