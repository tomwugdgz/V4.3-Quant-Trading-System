# 因子库文档 (Factor Library)

**版本**: V4.3.0  
**创建时间**: 2026-04-11  
**最后更新**: 2026-04-11

---

## 一、概述

V4.3 因子库包含 4 大类因子，共 16 个子因子，全面覆盖动量、均值回归、突破、波动率四大主流量化策略。

### 1.1 因子权重

| 因子类别 | 权重 | 子因子数量 | 适用市场 |
|----------|------|------------|----------|
| 动量因子 | 30% | 3 | 趋势市 |
| 均值回归因子 | 30% | 3 | 震荡市 |
| 突破因子 | 20% | 3 | 突破行情 |
| 波动率因子 | 20% | 3 | 所有市场 |

### 1.2 评分机制

```
单个因子评分：0-100 分
综合评分 = Σ(因子评分 × 权重)

信号映射：
- ≥70 分：STRONG_BUY (强烈买入)
- 55-69 分：BUY (买入)
- 46-54 分：NEUTRAL (中性)
- 31-45 分：SELL (卖出)
- ≤30 分：STRONG_SELL (强烈卖出)
```

### 1.3 目录结构

```
trading/factors/
├── __init__.py                    # 因子库初始化
├── momentum.py                    # 动量因子
├── mean_reversion.py              # 均值回归因子
├── breakout.py                    # 突破因子
└── volatility.py                  # 波动率因子
```

---

## 二、动量因子 (Momentum Factor)

**文件**: `factors/momentum.py`  
**权重**: 30%  
**适用市场**: 趋势市

### 2.1 子因子

#### 2.1.1 EMA 斜率

**原理**: 计算短期 EMA 与长期 EMA 的差值，判断趋势强度

**公式**:
```python
EMA_Slope = (EMA10 - EMA20) / EMA20 × 100%
```

**参数**:
- `ema_period_short`: 10
- `ema_period_long`: 20

**评分**:
```python
ema_score = np.clip(ema_slope × 10, -100, 100)
```

**信号**:
- 正斜率：看涨信号
- 负斜率：看跌信号

---

#### 2.1.2 价格动量

**原理**: 计算 N 日涨幅，衡量价格变化速度

**公式**:
```python
Price_Momentum = (Current_Price - Price_N_days_ago) / Price_N_days_ago × 100%
```

**参数**:
- `momentum_period`: 10

**评分**:
```python
momentum_score = np.clip(price_momentum × 5, -100, 100)
```

**信号**:
- 正动量：上涨动能
- 负动量：下跌动能

---

#### 2.1.3 MACD 信号

**原理**: 利用 MACD 线与信号线的关系判断趋势

**公式**:
```python
EMA_Fast = EMA(close, 12)
EMA_Slow = EMA(close, 26)
MACD_Line = EMA_Fast - EMA_Slow
Signal_Line = EMA(MACD_Line, 9)
Histogram = MACD_Line - Signal_Line
```

**参数**:
- `macd_fast`: 12
- `macd_slow`: 26
- `macd_signal`: 9

**评分**:
```python
if trend == 'BULLISH':
    macd_score = 50 + (histogram × 100)
elif trend == 'BEARISH':
    macd_score = -50 + (histogram × 100)
else:
    macd_score = 0
```

**信号**:
- BULLISH: MACD 线在信号线上方
- BEARISH: MACD 线在信号线下方
- NEUTRAL: 交叉状态

---

### 2.2 综合评分

```python
total_score = (ema_score × 0.4 + momentum_score × 0.4 + macd_score × 0.2)
normalized_score = (total_score + 100) / 2
```

### 2.3 使用方法

```python
from factors.momentum import MomentumFactor
import MetaTrader5 as mt5
import pandas as pd

# 获取数据
rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 100)
df = pd.DataFrame(rates)

# 计算评分
factor = MomentumFactor()
result = factor.calculate_score(df)

print(f"动量评分：{result['total_score']:.1f}")
print(f"交易信号：{result['signal']}")
```

---

## 三、均值回归因子 (Mean Reversion Factor)

**文件**: `factors/mean_reversion.py`  
**权重**: 30%  
**适用市场**: 震荡市

### 3.1 子因子

#### 3.1.1 RSI (相对强弱指数)

**原理**: 衡量价格超买超卖状态

**公式**:
```python
delta = close.diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
RS = avg_gain / avg_loss
RSI = 100 - (100 / (1 + RS))
```

**参数**:
- `rsi_period`: 14

**信号**:
- RSI > 70: 超买（看跌）
- RSI < 30: 超卖（看涨）
- 30 ≤ RSI ≤ 70: 中性

**评分**:
```python
rsi_score = 50 - (rsi - 50)
```

---

#### 3.1.2 布林带位置

**原理**: 判断价格在布林带中的相对位置

**公式**:
```python
Middle = SMA(close, 20)
Std = close.rolling(20).std()
Upper = Middle + 2 × Std
Lower = Middle - 2 × Std
Position = (Current_Price - Lower) / (Upper - Lower)
```

**参数**:
- `bb_period`: 20
- `bb_std`: 2.0

**信号**:
- Position > 0.8: 接近上轨（看跌）
- Position < 0.2: 接近下轨（看涨）
- 0.2 ≤ Position ≤ 0.8: 中性

**评分**:
```python
bb_score = 50 - (position - 0.5) × 100
```

---

#### 3.1.3 乖离率 (Bias)

**原理**: 衡量价格与均线的偏离程度

**公式**:
```python
MA = SMA(close, 20)
Bias = (Current_Price - MA) / MA × 100%
```

**参数**:
- `bias_period`: 20

**信号**:
- 正乖离过大：价格偏高（看跌）
- 负乖离过大：价格偏低（看涨）

**评分**:
```python
bias_score = 50 - (bias × 5)
```

---

### 3.2 综合评分

```python
total_score = (rsi_score × 0.4 + bb_score × 0.4 + bias_score × 0.2)
```

### 3.3 使用方法

```python
from factors.mean_reversion import MeanReversionFactor

factor = MeanReversionFactor()
result = factor.calculate_score(df)

print(f"RSI: {result['rsi']['rsi']:.1f}")
print(f"布林带位置：{result['bollinger']['position']:.2f}")
print(f"乖离率：{result['bias']:.2f}%")
print(f"均值回归评分：{result['total_score']:.1f}")
```

---

## 四、突破因子 (Breakout Factor)

**文件**: `factors/breakout.py`  
**权重**: 20%  
**适用市场**: 突破行情

### 4.1 子因子

#### 4.1.1 价格突破

**原理**: 检测价格是否突破 N 日高点/低点

**公式**:
```python
Highest_High = high.rolling(20).max()
Lowest_Low = low.rolling(20).min()

if close > Highest_High[-2]:
    breakout_type = 'UPPER'
    strength = (close - Highest_High[-2]) / Highest_High[-2]
elif close < Lowest_Low[-2]:
    breakout_type = 'LOWER'
    strength = (Lowest_Low[-2] - close) / Lowest_Low[-2]
```

**参数**:
- `breakout_period`: 20

**信号**:
- UPPER: 向上突破（看涨）
- LOWER: 向下跌破（看跌）
- NONE: 无突破

**评分**:
```python
if breakout_type == 'UPPER':
    breakout_score = 50 + (strength × 10)
elif breakout_type == 'LOWER':
    breakout_score = 50 - (strength × 10)
else:
    breakout_score = 50
```

---

#### 4.1.2 成交量放大

**原理**: 检测成交量是否异常放大

**公式**:
```python
Avg_Volume = volume.rolling(20).mean()
Volume_Ratio = Current_Volume / Avg_Volume
```

**参数**:
- `volume_period`: 20
- `volume_threshold`: 1.5

**信号**:
- Volume_Ratio > 1.5: 放量（活跃）
- Volume_Ratio ≤ 1.5: 正常

**评分**:
```python
if is_spike:
    volume_score = 75
else:
    volume_score = 50
```

---

#### 4.1.3 形态识别

**原理**: 识别简单价格形态

**规则**:
```python
# 上升形态：高点抬高，低点抬高
if high[-1] > high[0] and low[-1] > low[0]:
    pattern = 'UPTREND'
    signal = 'BULLISH'

# 下降形态：高点降低，低点降低
elif high[-1] < high[0] and low[-1] < low[0]:
    pattern = 'DOWNTREND'
    signal = 'BEARISH'

# 震荡形态
else:
    pattern = 'RANGING'
    signal = 'NEUTRAL'
```

**评分**:
```python
if pattern == 'UPTREND':
    pattern_score = 75
elif pattern == 'DOWNTREND':
    pattern_score = 25
else:
    pattern_score = 50
```

---

### 4.2 综合评分

```python
total_score = (breakout_score × 0.5 + volume_score × 0.3 + pattern_score × 0.2)
```

### 4.3 使用方法

```python
from factors.breakout import BreakoutFactor

factor = BreakoutFactor()
result = factor.calculate_score(df)

print(f"突破类型：{result['breakout']['breakout_type']}")
print(f"突破强度：{result['breakout']['strength']:.3f}%")
print(f"成交量比率：{result['volume']['volume_ratio']:.2f}x")
print(f"形态：{result['pattern']['pattern']}")
print(f"突破评分：{result['total_score']:.1f}")
```

---

## 五、波动率因子 (Volatility Factor)

**文件**: `factors/volatility.py`  
**权重**: 20%  
**适用市场**: 所有市场

### 5.1 子因子

#### 5.1.1 ATR 变化

**原理**: 衡量波动率变化

**公式**:
```python
TR = max(high - low, abs(high - close_prev), abs(low - close_prev))
ATR = TR.rolling(14).mean()
ATR_Change = (Current_ATR - Prev_ATR) / Prev_ATR × 100%
```

**参数**:
- `atr_period`: 14

**信号**:
- ATR_Change > 10%: 波动率上升
- ATR_Change < -10%: 波动率下降
- -10% ≤ ATR_Change ≤ 10%: 正常

**评分**:
```python
if signal == 'HIGH_VOLATILITY':
    atr_score = 75
elif signal == 'LOW_VOLATILITY':
    atr_score = 25
else:
    atr_score = 50
```

---

#### 5.1.2 布林带宽度

**原理**: 衡量布林带收口/开口状态

**公式**:
```python
Width = (Upper - Lower) / Middle × 100%
```

**参数**:
- `bb_period`: 20

**信号**:
- Width < 平均宽度×0.8: 收口（即将突破）
- Width ≥ 平均宽度×0.8: 正常

**评分**:
```python
if signal == 'SQUEEZE':
    bb_score = 75
else:
    bb_score = 50
```

---

#### 5.1.3 历史波动率

**原理**: 计算年化波动率并判断百分位

**公式**:
```python
Returns = close.pct_change()
HV = Returns.rolling(20).std() × sqrt(252 × 24)
Percentile = (HV_series < Current_HV).mean() × 100%
```

**参数**:
- `hv_period`: 20

**信号**:
- Percentile > 80: 高波动率
- Percentile < 20: 低波动率
- 20 ≤ Percentile ≤ 80: 正常

**评分**:
```python
if signal == 'HIGH':
    hv_score = 75
elif signal == 'LOW':
    hv_score = 25
else:
    hv_score = 50
```

---

### 5.2 综合评分

```python
total_score = (atr_score × 0.4 + bb_score × 0.4 + hv_score × 0.2)
```

### 5.3 使用方法

```python
from factors.volatility import VolatilityFactor

factor = VolatilityFactor()
result = factor.calculate_score(df)

print(f"ATR 变化：{result['atr']['atr_change']:.2f}%")
print(f"布林带宽度：{result['bollinger']['width']:.2f}%")
print(f"历史波动率：{result['historical_volatility']['hv']:.2f}%")
print(f"波动率评分：{result['total_score']:.1f}")
```

---

## 六、因子 IC 分析

### 6.1 IC 计算方法

```python
# 计算未来 N 期收益
forward_returns = close.shift(-N) / close - 1

# 计算 Spearman 秩相关
IC = factor_scores.corr(forward_returns, method='spearman')
```

### 6.2 IC 评估标准

| IC 范围 | 评价 | 建议 |
|---------|------|------|
| IC > 0.05 | 有效因子 | 重点使用 |
| 0.02 < IC ≤ 0.05 | 弱有效 | 保留观察 |
| IC ≤ 0.02 | 无效因子 | 考虑剔除 |

### 6.3 运行 IC 分析

```bash
cd trading/v4_3
python factor_ic_analysis.py
```

---

## 七、因子优化建议

### 7.1 参数优化

**动量因子**:
- 尝试不同 EMA 周期组合（8/16, 12/26, 10/20）
- 调整动量周期（5, 10, 15, 20）

**均值回归因子**:
- 调整 RSI 周期（10, 14, 20）
- 调整布林带标准差（1.5, 2.0, 2.5）

**突破因子**:
- 调整突破周期（10, 20, 30, 50）
- 调整成交量阈值（1.3, 1.5, 2.0）

**波动率因子**:
- 调整 ATR 周期（10, 14, 20）
- 调整 HV 周期（10, 20, 30）

### 7.2 权重优化

根据 Market Regime 动态调整因子权重：

| 市场状态 | 动量 | 均值回归 | 突破 | 波动率 |
|----------|------|----------|------|--------|
| TRENDING_UP | 40% | 20% | 25% | 15% |
| TRENDING_DOWN | 40% | 20% | 25% | 15% |
| RANGING | 20% | 40% | 20% | 20% |
| HIGH_VOLATILITY | 25% | 25% | 20% | 30% |

---

## 八、常见问题

### Q1: 因子 IC 偏低怎么办？

**A**: 
1. 增加样本量（至少 500 根 K 线）
2. 优化因子参数
3. 使用 Market Regime 过滤
4. 调整 forward return 周期

### Q2: 如何选择因子周期？

**A**:
- 短周期（5-10）：适合高频交易
- 中周期（10-20）：适合日内交易
- 长周期（20-50）：适合趋势跟踪

### Q3: 因子之间相关性过高怎么办？

**A**:
1. 降低相关因子的权重
2. 使用正交化方法
3. 增加其他类型因子

---

## 九、参考资料

1. **动量因子**: Jegadeesh & Titman (1993)
2. **均值回归**: Poterba & Summers (1988)
3. **突破因子**: Brock, Lakonishok & LeBaron (1992)
4. **波动率因子**: Andersen & Bollerslev (1997)

---

**V4.3 Development Team**  
**2026-04-11**  
**数据驱动，持续进化**
