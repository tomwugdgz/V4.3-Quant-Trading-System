# 多算法测试与融合框架 (Multi-Algorithm Testing & Fusion)

**创建日期**: 2026-03-27  
**提出人**: Tom  
**执行人**: 旺财 🎯

---

## 🎯 核心目标

**测试不同算法** → **记录测试数据** → **PK 对比 KPI/ROI** → **选择最优模型融合**

---

## 📊 算法测试矩阵

### 第一类：趋势跟踪算法 (Trend Following)

| 编号 | 算法名称 | 核心指标 | 参数 | 特点 |
|------|----------|----------|------|------|
| **TF-01** | SMA 交叉 | SMA20/SMA50 | 周期：20,50 | 简单直接，滞后性高 |
| **TF-02** | EMA 交叉 | EMA12/EMA26 | 周期：12,26 | 反应更快，假信号多 |
| **TF-03** | MACD 趋势 | MACD(12,26,9) | 快线：12, 慢线：26, 信号：9 | 经典趋势指标 |
| **TF-04** | ADX 趋势 | ADX + DI | ADX>25, DI 交叉 | 过滤震荡市 |
| **TF-05** | 通道突破 | Donchian Channel | 周期：20 | 突破策略，适合趋势市 |
| **TF-06** | 自适应均线 | AMA (Kaufman) | 快线：2, 慢线：30 | 自适应市场波动 |

---

### 第二类：均值回归算法 (Mean Reversion)

| 编号 | 算法名称 | 核心指标 | 参数 | 特点 |
|------|----------|----------|------|------|
| **MR-01** | 布林带回归 | Bollinger Bands | 周期：20, 标准差：2 | 超买超卖回归 |
| **MR-02** | RSI 反转 | RSI | 超买：70, 超卖：30 | 经典反转指标 |
| **MR-03** | 随机指标 | Stochastic | K:14, D:3 | 短期反转 |
| **MR-04** | 威廉指标 | Williams %R | 周期：14 | 超买超卖极端 |
| **MR-05** | 价格通道 | Keltner Channel | ATR 周期：20 | 波动率通道回归 |

---

### 第三类：动量算法 (Momentum)

| 编号 | 算法名称 | 核心指标 | 参数 | 特点 |
|------|----------|----------|------|------|
| **MO-01** | ROC 动量 | Rate of Change | 周期：12 | 价格变化率 |
| **MO-02** | CCI 动量 | Commodity Channel | 周期：20 | 偏离均值程度 |
| **MO-03** | 动量突破 | Price Momentum | 周期：10,20,60 | 多周期动量 |
| **MO-04** | 成交量动量 | Volume + Price | OBV + MA | 量价配合 |

---

### 第四类：波动率算法 (Volatility)

| 编号 | 算法名称 | 核心指标 | 参数 | 特点 |
|------|----------|----------|------|------|
| **VO-01** | ATR 突破 | Average True Range | 周期：14 | 波动率突破 |
| **VO-02** | 标准差过滤 | Standard Deviation | 周期：20, 阈值：2 | 过滤假突破 |
| **VO-03** | 波动率收缩 | Volatility Squeeze | BB 宽度 + Keltner | 收缩后爆发 |

---

### 第五类：机器学习算法 (Machine Learning)

| 编号 | 算法名称 | 模型类型 | 特征 | 特点 |
|------|----------|----------|------|------|
| **ML-01** | 随机森林 | Random Forest | 技术指标 20 维 | 非线性分类 |
| **ML-02** | 梯度提升 | XGBoost | OHLCV + 指标 | 强预测能力 |
| **ML-03** | LSTM | 深度学习 | 价格序列 60 步 | 时序预测 |
| **ML-04** | 强化学习 | PPO/DQN | 状态 + 奖励函数 | 自适应学习 |

---

### 第六类：复合算法 (Hybrid)

| 编号 | 算法名称 | 组合方式 | 权重 | 特点 |
|------|----------|----------|------|------|
| **HX-01** | 趋势 + 动量 | TF-06 + MO-01 | 60% + 40% | 趋势确认动量 |
| **HX-02** | 均值 + 波动 | MR-01 + VO-01 | 50% + 50% | 波动率回归 |
| **HX-03** | 三重确认 | TF-04 + MO-03 + VO-02 | 40% + 30% + 30% | 多维度确认 |
| **HX-04** | 四重确认 (现行) | AMA + RSRS + ADX + 标准差 | 25% × 4 | 高准确率 |

---

## 📋 测试参数记录模板

### 单个算法测试记录

```markdown
## 算法 [编号] - [名称]

**测试开始**: YYYY-MM-DD  
**测试结束**: YYYY-MM-DD  
**测试周期**: X 天

### 参数配置
```json
{
  "algorithm": "TF-06",
  "name": "自适应均线",
  "parameters": {
    "fast_period": 2,
    "slow_period": 30,
    "signal_threshold": 0.0005,
    "stop_loss_pips": 30,
    "take_profit_pips": 60,
    "position_size": "0.1% 风险"
  },
  "market_conditions": "trending/ranging/mixed",
  "timeframe": "15m/1h/4h"
}
```

### 测试结果

| 指标 | 数值 | 目标 | 状态 |
|------|------|------|------|
| 交易数量 | - | ≥20 | ⏳ |
| 胜率 | - | ≥45% | ⏳ |
| 盈利因子 | - | ≥1.5 | ⏳ |
| 最大回撤 | - | ≤10% | ⏳ |
| 夏普比率 | - | ≥1.0 | ⏳ |
| 总 ROI | - | ≥5% | ⏳ |
| 日均收益 | - | ≥0.2% | ⏳ |

### KPI 评分

```
综合得分 = (胜率×0.3 + 盈利因子×0.3 + 夏普×0.2 + ROI×0.2) / 4
```

### 优缺点分析

**优点**:
- ...

**缺点**:
- ...

**适用市场**:
- 趋势市 / 震荡市 / 高波动 / 低波动

### 决策

- [ ] 通过 → 进入融合池
- [ ] 优化 → 调整参数重测
- [ ] 淘汰 → 放弃该算法

---
**测试人**: 旺财 🎯
**测试日期**: YYYY-MM-DD
```

---

## 🎯 算法 PK 机制

### 第一轮：单算法测试 (7 天/算法)

```
测试流程:
1. 选择算法 (如 TF-06)
2. 设置参数
3. 轻仓测试 (0.1% 风险)
4. 记录每笔交易
5. 7 天后统计 KPI
6. 决策：通过/优化/淘汰
```

### 第二轮：多算法对比 (30 天)

```
并行测试:
- 同时运行 5-10 个通过初选的算法
- 每个算法独立账户/虚拟账户
- 月底对比 ROI/KPI
- 选出 Top 3
```

### 第三轮：融合测试 (30 天)

```
融合策略:
- Top 3 算法加权融合
- 权重分配：按夏普比率/盈利因子
- 动态调整：每月 rebalance
- 对比单一算法 vs 融合策略
```

---

## 📊 融合策略设计

### 方案 A: 投票融合 (Voting Ensemble)

```python
# 每个算法投票，多数决定
def voting_fusion(signals):
    """
    signals: [BUY, SELL, HOLD, BUY, HOLD]
    结果：BUY (2 票)
    """
    buy_count = signals.count('BUY')
    sell_count = signals.count('SELL')
    
    if buy_count > sell_count and buy_count >= 3:
        return 'BUY'
    elif sell_count > buy_count and sell_count >= 3:
        return 'SELL'
    else:
        return 'HOLD'
```

**优点**: 减少假信号  
**缺点**: 可能错过时机

---

### 方案 B: 加权融合 (Weighted Ensemble)

```python
# 按算法绩效分配权重
def weighted_fusion(signals_with_weights):
    """
    signals_with_weights: [
      ('BUY', 0.4),   # 算法 1, 权重 40%
      ('SELL', 0.3),  # 算法 2, 权重 30%
      ('BUY', 0.3)    # 算法 3, 权重 30%
    ]
    结果：BUY (0.4 + 0.3 = 0.7 > 0.3)
    """
    buy_score = sum(w for s, w in signals_with_weights if s == 'BUY')
    sell_score = sum(w for s, w in signals_with_weights if s == 'SELL')
    
    if buy_score > sell_score and buy_score > 0.5:
        return 'BUY'
    elif sell_score > buy_score and sell_score > 0.5:
        return 'SELL'
    else:
        return 'HOLD'
```

**优点**: 优秀算法话语权更大  
**缺点**: 权重需要动态调整

---

### 方案 C: 分层融合 (Hierarchical Fusion)

```python
# 第一层：趋势判断
# 第二层：入场时机
# 第三层：风险控制

def hierarchical_fusion(algo_results):
    # Layer 1: 趋势方向 (TF 算法)
    trend = trend_algorithms(algo_results['trend'])  # BULL/BEAR
    
    # Layer 2: 入场时机 (MO/MR 算法)
    timing = timing_algorithms(algo_results['timing'])  # ENTRY/WAIT
    
    # Layer 3: 风险控制 (VO 算法)
    risk = risk_algorithms(algo_results['risk'])  # SAFE/RISKY
    
    if trend == 'BULL' and timing == 'ENTRY' and risk == 'SAFE':
        return 'BUY'
    elif trend == 'BEAR' and timing == 'ENTRY' and risk == 'SAFE':
        return 'SELL'
    else:
        return 'HOLD'
```

**优点**: 逻辑清晰，各司其职  
**缺点**: 复杂度高

---

### 方案 D: 动态融合 (Dynamic Fusion)

```python
# 根据市场状态动态调整权重
def dynamic_fusion(algo_results, market_state):
    """
    market_state: 'trending' / 'ranging' / 'volatile'
    """
    if market_state == 'trending':
        # 趋势市，增加趋势算法权重
        weights = {'TF': 0.5, 'MO': 0.3, 'MR': 0.2}
    elif market_state == 'ranging':
        # 震荡市，增加均值回归权重
        weights = {'TF': 0.2, 'MO': 0.3, 'MR': 0.5}
    else:  # volatile
        # 高波动，增加风控权重
        weights = {'TF': 0.3, 'MO': 0.2, 'MR': 0.2, 'VO': 0.3}
    
    return weighted_fusion(algo_results, weights)
```

**优点**: 自适应市场  
**缺点**: 需要准确识别市场状态

---

## 📈 测试时间表

### 第一阶段：单算法测试 (2026-03-27 至 2026-04-27)

| 周次 | 日期 | 测试算法 | 数量 | 目标 |
|------|------|----------|------|------|
| W1 | 03-27 ~ 04-03 | TF-01 ~ TF-06 | 6 个 | 选出 Top 2 趋势算法 |
| W2 | 04-03 ~ 04-10 | MR-01 ~ MR-05 | 5 个 | 选出 Top 2 回归算法 |
| W3 | 04-10 ~ 04-17 | MO-01 ~ MO-04 | 4 个 | 选出 Top 2 动量算法 |
| W4 | 04-17 ~ 04-24 | VO-01 ~ VO-03 + HX-01 ~ HX-04 | 7 个 | 选出 Top 3 复合算法 |

### 第二阶段：多算法对比 (2026-04-27 至 2026-05-27)

- **并行测试**: Top 10 算法同时运行
- **独立账户**: 每个算法虚拟账户 $10,000
- **月底排名**: 按 ROI/KPI 排序
- **选出 Top 3**: 进入融合池

### 第三阶段：融合测试 (2026-05-27 至 2026-06-27)

- **测试 4 种融合方案**: 投票/加权/分层/动态
- **对比**: 融合策略 vs 单一最佳算法
- **选出最优**: 成为主策略

---

## 🎯 KPI 评估体系

### 核心 KPI (权重 70%)

| 指标 | 权重 | 计算方法 | 目标值 |
|------|------|----------|--------|
| **ROI** | 25% | 总盈亏 / 初始资金 | ≥10%/月 |
| **夏普比率** | 20% | (收益 - 无风险) / 波动率 | ≥1.5 |
| **最大回撤** | 15% | 最大连续亏损 | ≤10% |
| **盈利因子** | 10% | 总盈利 / 总亏损 | ≥2.0 |

### 辅助 KPI (权重 30%)

| 指标 | 权重 | 计算方法 | 目标值 |
|------|------|----------|--------|
| **胜率** | 15% | 盈利单数 / 总单数 | ≥50% |
| **交易频率** | 10% | 交易数量 / 月 | ≥40 单 |
| **平均盈亏比** | 5% | 平均盈利 / 平均亏损 | ≥1:2 |

### 综合评分公式

```
综合得分 = (ROI 得分×0.25 + 夏普×0.20 + 回撤×0.15 + 盈利因子×0.10 + 胜率×0.15 + 频率×0.10 + 盈亏比×0.05) × 100

满分：100 分
及格线：70 分
优秀线：85 分
```

---

## 📝 算法档案模板

```markdown
# 算法档案：[编号] - [名称]

## 基本信息
- **创建日期**: YYYY-MM-DD
- **算法类型**: 趋势/回归/动量/波动/ML/复合
- **复杂度**: 低/中/高
- **计算成本**: 低/中/高

## 核心逻辑
[算法详细描述]

## 参数配置
```json
{
  "param1": value1,
  "param2": value2
}
```

## 测试结果汇总

| 测试轮次 | 日期 | ROI | 夏普 | 回撤 | 胜率 | 决策 |
|----------|------|-----|------|------|------|------|
| Round 1 | - | - | - | - | - | - |
| Round 2 | - | - | - | - | - | - |
| Round 3 | - | - | - | - | - | - |

## 最佳表现
- **最佳单月**: +X% (YYYY-MM)
- **最差单月**: -X% (YYYY-MM)
- **最长连胜**: X 单
- **最长连败**: X 单

## 适用市场
- ✅ 趋势市
- ⚠️ 震荡市
- ❌ 高波动市

## 状态
- [ ] 测试中
- [ ] 通过
- [ ] 优化中
- [ ] 淘汰

---
**最后更新**: YYYY-MM-DD
```

---

## 🔧 自动化测试脚本

### 算法测试框架 (algo_tester.py)

```python
#!/usr/bin/env python3
# 多算法自动化测试框架

class AlgorithmTester:
    def __init__(self, algorithm, params, initial_capital=10000):
        self.algo = algorithm
        self.params = params
        self.capital = initial_capital
        self.trades = []
        
    def run_backtest(self, start_date, end_date):
        """运行回测"""
        data = load_data(start_date, end_date)
        
        for bar in data:
            signal = self.algo.generate_signal(bar, self.params)
            if signal != 'HOLD':
                trade = self.execute_trade(signal, bar)
                self.trades.append(trade)
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """计算 KPI"""
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['profit'] > 0]
        losing_trades = [t for t in self.trades if t['profit'] <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        roi = (total_profit - total_loss) / self.capital
        max_drawdown = calculate_max_drawdown(self.trades)
        sharpe = calculate_sharpe_ratio(self.trades)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'roi': roi,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'score': self.calculate_score(win_rate, roi, profit_factor, max_drawdown, sharpe)
        }
    
    def calculate_score(self, win_rate, roi, profit_factor, max_drawdown, sharpe):
        """计算综合得分"""
        score = (
            roi * 25 +
            sharpe * 20 +
            (1 - max_drawdown) * 15 +
            profit_factor * 10 +
            win_rate * 15 +
            min(len(self.trades) / 40, 1) * 10 +
            0.05  # 盈亏比简化
        )
        return score * 100  # 满分 100
```

---

## 🎯 旺财执行计划

### 立即行动 (本周)
1. ✅ 建立算法档案 (6 个趋势算法)
2. ✅ 开始 TF-01 ~ TF-06 测试
3. ✅ 每日记录交易数据
4. ✅ 周末统计 KPI

### 短期目标 (1 个月)
- 测试 20+ 个算法
- 选出 Top 10
- 开始融合测试

### 中期目标 (3 个月)
- 完成 4 种融合方案测试
- 选出最优融合策略
- 实盘运行

### 长期目标 (6 个月)
- 持续优化算法池
- 引入机器学习算法
- 建立自适应融合系统

---

## 📊 算法测试追踪表

| 编号 | 名称 | 类型 | 测试开始 | 测试结束 | ROI | 夏普 | 回撤 | 得分 | 状态 |
|------|------|------|----------|----------|-----|------|------|------|------|
| TF-06 | AMA | 趋势 | 03-27 | - | - | - | - | - | 🟡 测试中 |
| HX-04 | 四重确认 | 复合 | 03-23 | - | +2.11% | - | -0.35% | - | 🟡 测试中 |
| ... | ... | ... | - | - | - | - | - | - | - |

---

## 🎯 旺财承诺

1. ✅ **广泛测试** - 测试 20+ 不同算法
2. ✅ **详细记录** - 每个算法参数/数据完整记录
3. ✅ **严格 PK** - 按 KPI/ROI 客观对比
4. ✅ **优中选优** - 只选 Top 3 融合
5. ✅ **持续优化** - 每月 rebalance 权重

---

**旺财 🎯**: 多算法测试 + 融合就系量化交易嘅终极武器！唔靠单一策略，靠团队作战！

**创建人**: Tom  
**执行人**: 旺财 🎯  
**生效日期**: 2026-03-27  
**下次汇报**: 2026-04-03 (7 天后，第一周测试结果)
