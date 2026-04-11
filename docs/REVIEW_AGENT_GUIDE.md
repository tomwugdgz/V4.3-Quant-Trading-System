# 复盘 Agent 指南 (Review Agent Guide)

**版本**: V4.3.0  
**创建时间**: 2026-04-11  
**最后更新**: 2026-04-11

---

## 一、概述

Review Agent 是 V4.3 系统的自动复盘模块，负责交易归因分析、每日复盘报告生成、交易模式识别。

### 1.1 核心功能

1. **归因分析**: 策略/品种/时间/因子四个维度
2. **每日复盘**: 自动生成 Markdown 格式报告
3. **模式识别**: 识别盈利/亏损模式
4. **改进建议**: 基于数据分析提供优化建议

### 1.2 文件位置

```
trading/v4_3/review_agent.py
```

### 1.3 使用场景

- 每日收盘后自动生成复盘报告
- 每周/每月绩效分析
- 交易策略优化
- 问题诊断

---

## 二、归因分析

### 2.1 策略归因

**目的**: 分析不同策略的贡献

**维度**:
```python
策略类型:
- 趋势策略 (Trend Following)
- 均值回归策略 (Mean Reversion)
- 突破策略 (Breakout)
- 波动率策略 (Volatility)
```

**计算方法**:
```python
# 按策略类型分组
for strategy_type in strategies:
    strategy_trades = [t for t in trades if t.strategy == strategy_type]
    
    total_profit = sum(t.profit for t in strategy_trades)
    win_rate = len([t for t in strategy_trades if t.profit > 0]) / len(strategy_trades)
    
    attribution[strategy_type] = {
        'count': len(strategy_trades),
        'total_profit': total_profit,
        'win_rate': win_rate,
        'avg_profit': total_profit / len(strategy_trades)
    }
```

**示例输出**:
```
策略归因:
- 趋势策略：3 单，盈利+$250，胜率 67%
- 均值回归：2 单，盈利-$80，胜率 50%
- 突破策略：1 单，盈利+$150，胜率 100%
```

---

### 2.2 品种归因

**目的**: 分析各交易品种的贡献

**维度**:
```python
品种:
- EURUSD
- GBPUSD
- USDJPY
- AUDUSD
- NZDUSD
- USDCHF
- USDCAD
```

**计算方法**:
```python
for symbol in symbols:
    symbol_trades = [t for t in trades if t.symbol == symbol]
    
    total_profit = sum(t.profit for t in symbol_trades)
    
    attribution[symbol] = {
        'count': len(symbol_trades),
        'total_profit': total_profit,
        'avg_profit': total_profit / len(symbol_trades) if symbol_trades else 0
    }
```

**示例输出**:
```
品种归因:
- EURUSD: 2 单，盈利+$180
- GBPUSD: 1 单，盈利-$50
- USDJPY: 3 单，盈利+$320
```

---

### 2.3 时间归因

**目的**: 分析不同时段的交易表现

**维度**:
```python
时段:
- 亚洲盘 (06:00-15:00 北京时间)
- 欧洲盘 (15:00-00:00 北京时间)
- 美洲盘 (20:00-05:00 北京时间)
```

**计算方法**:
```python
for trade in trades:
    hour = trade.time.hour
    
    if 6 <= hour < 15:
        session = 'asian_session'
    elif 15 <= hour < 24:
        session = 'european_session'
    else:
        session = 'american_session'
    
    session_attribution[session]['count'] += 1
    session_attribution[session]['profit'] += trade.profit
```

**示例输出**:
```
时间归因:
- 亚洲盘：2 单，盈利+$100
- 欧洲盘：3 单，盈利+$280
- 美洲盘：1 单，盈利-$50
```

---

### 2.4 因子归因

**目的**: 分析各因子的 IC 变化

**维度**:
```python
因子:
- 动量因子 (Momentum)
- 均值回归因子 (Mean Reversion)
- 突破因子 (Breakout)
- 波动率因子 (Volatility)
```

**计算方法**:
```python
# 计算各因子 IC
for factor_name in factors:
    factor_scores = get_factor_scores(factor_name)
    forward_returns = get_forward_returns()
    
    ic = factor_scores.corr(forward_returns, method='pearson')
    
    factor_attribution[factor_name] = {
        'ic': ic,
        'valid': abs(ic) > 0.02
    }
```

**示例输出**:
```
因子归因:
- 动量因子：IC=0.035 (有效)
- 均值回归因子：IC=0.012 (无效)
- 突破因子：IC=0.048 (有效)
- 波动率因子：IC=0.021 (有效)
```

---

## 三、每日复盘报告

### 3.1 生成报告

```python
from v4_3.review_agent import ReviewAgent

agent = ReviewAgent(db_path="trading.db")

# 生成今日报告
report = agent.generate_daily_report(date="2026-04-11")

print(report)
```

### 3.2 报告结构

```markdown
# 每日复盘报告
**日期**: 2026-04-11
**生成时间**: 2026-04-11 20:00:00

## 核心指标
- 交易次数：5 单
- 盈利：3 单
- 亏损：2 单
- 胜率：60%
- 总盈亏：+$350

## 交易明细
- EURUSD BUY 0.1 手
  - 入场价：1.1000
  - 止损/止盈：1.0950 / 1.1100
  - 盈亏：✅ +$100

## 问题分析
⚠️ 胜率偏低 (60% < 目标 70%)
   - 可能原因：信号质量不足
   - 改进建议：提高信号强度门槛

## 明日计划
1. 继续执行 V4.3 策略
2. 关注市场状态变化
3. 严格执行风控规则
```

---

### 3.3 自动发送

```python
# 配置定时任务
import schedule
import time

def daily_review_job():
    report = agent.generate_daily_report()
    send_to_feishu(report)  # 发送到飞书

# 每天 20:00 执行
schedule.every().day.at("20:00").do(daily_review_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 四、模式识别

### 4.1 盈利模式识别

**目的**: 找出盈利交易的共同特征

**方法**:
```python
win_trades = [t for t in trades if t.profit > 0]

# 分析品种
best_symbol = max(set(t.symbol for t in win_trades), 
                  key=lambda s: sum(t.profit for t in win_trades if t.symbol == s))

# 分析时段
best_session = max(set(get_session(t.time) for t in win_trades),
                   key=lambda s: sum(t.profit for t in win_trades if get_session(t.time) == s))

# 分析市场状态
best_regime = max(set(t.regime for t in win_trades),
                  key=lambda r: sum(t.profit for t in win_trades if t.regime == r))
```

**输出**:
```
盈利模式:
- 最佳品种：USDJPY
- 最佳时段：欧洲盘
- 最佳市场状态：TRENDING_UP
```

---

### 4.2 亏损模式识别

**目的**: 找出亏损交易的共同特征

**方法**:
```python
loss_trades = [t for t in trades if t.profit < 0]

# 分析品种
worst_symbol = min(set(t.symbol for t in loss_trades),
                   key=lambda s: sum(t.profit for t in loss_trades if t.symbol == s))

# 分析原因
reasons = [t.reason for t in loss_trades if hasattr(t, 'reason')]
most_common_reason = max(set(reasons), key=reasons.count)
```

**输出**:
```
亏损模式:
- 最差品种：GBPUSD
- 主要原因：止损过窄
```

---

### 4.3 改进建议

**基于模式识别**:
```python
suggestions = []

if best_symbol:
    suggestions.append(f"增加{best_symbol}的交易频率")

if worst_symbol:
    suggestions.append(f"减少或避免{worst_symbol}的交易")

if best_session:
    suggestions.append(f"重点关注{best_session}时段")

if most_common_reason:
    suggestions.append(f"改进：{most_common_reason}")
```

**输出**:
```
改进建议:
1. 增加 USDJPY 的交易频率
2. 减少或避免 GBPUSD 的交易
3. 重点关注欧洲盘时段
4. 改进：止损设置过窄
```

---

## 五、周报/月报

### 5.1 生成周报

```python
# 生成周报
weekly_report = agent.generate_weekly_report(
    start_date="2026-04-05",
    end_date="2026-04-11"
)

print(weekly_report)
```

### 5.2 周报内容

```markdown
# 周度复盘报告
**周期**: 2026-04-05 至 2026-04-11

## 核心指标
- 交易次数：25 单
- 盈利：15 单
- 亏损：10 单
- 胜率：60%
- 总盈亏：+$1,250
- 最大回撤：-$350
- 盈亏比：1.8:1

## 归因分析
### 策略归因
- 趋势策略：12 单，+$800
- 均值回归：8 单，+$200
- 突破策略：5 单，+$250

### 品种归因
- EURUSD: 8 单，+$450
- USDJPY: 10 单，+$600
- GBPUSD: 7 单，+$200

## 改进建议
1. 增加 USDJPY 交易频率
2. 优化均值回归策略参数
3. 关注欧洲盘时段
```

---

## 六、数据库设计

### 6.1 交易记录表

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    type TEXT,  -- BUY/SELL
    volume REAL,
    entry_price REAL,
    stop_loss REAL,
    take_profit REAL,
    exit_price REAL,
    profit REAL,
    strategy TEXT,
    regime TEXT,
    factor_score REAL,
    created_at DATETIME,
    closed_at DATETIME
);
```

### 6.2 查询示例

```python
# 获取今日交易
query = """
SELECT * FROM orders 
WHERE DATE(created_at) = '2026-04-11'
ORDER BY created_at DESC
"""

# 获取本周交易
query = """
SELECT * FROM orders 
WHERE created_at >= datetime('now', '-7 days')
ORDER BY created_at DESC
"""

# 获取某品种交易
query = """
SELECT * FROM orders 
WHERE symbol = 'EURUSD'
ORDER BY created_at DESC
"""
```

---

## 七、可视化

### 7.1 权益曲线

```python
import matplotlib.pyplot as plt

# 计算累计盈亏
trades = get_trades()
cumulative_pnl = []
total = 0

for trade in trades:
    total += trade.profit
    cumulative_pnl.append(total)

# 绘制权益曲线
plt.figure(figsize=(12, 6))
plt.plot(cumulative_pnl)
plt.title('权益曲线')
plt.xlabel('交易次数')
plt.ylabel('累计盈亏 ($)')
plt.grid(True)
plt.savefig('equity_curve.png')
```

---

### 7.2 盈亏分布

```python
# 盈亏分布直方图
profits = [t.profit for t in trades]

plt.figure(figsize=(10, 6))
plt.hist(profits, bins=20, edgecolor='black')
plt.title('盈亏分布')
plt.xlabel('盈亏 ($)')
plt.ylabel('交易次数')
plt.axvline(x=0, color='r', linestyle='--')
plt.grid(True)
plt.savefig('pnl_distribution.png')
```

---

## 八、常见问题

### Q1: 如何自定义复盘报告？

**A**: 
```python
# 继承 ReviewAgent
class CustomReviewAgent(ReviewAgent):
    def generate_daily_report(self, date=None):
        report = super().generate_daily_report(date)
        # 添加自定义内容
        report += "\n## 自定义部分\n..."
        return report
```

---

### Q2: 如何导出复盘数据？

**A**:
```python
# 导出为 CSV
import pandas as pd

trades = agent.get_trade_history(days=30)
trades.to_csv('trades_last_30_days.csv', index=False)
```

---

### Q3: 如何设置复盘提醒？

**A**:
```python
# 使用 schedule 库
import schedule

schedule.every().day.at("20:00").do(generate_daily_review)
```

---

## 九、最佳实践

### 9.1 复盘频率

- **每日复盘**: 20:00 自动生成
- **每周复盘**: 周日 20:00
- **每月复盘**: 月末 20:00

### 9.2 复盘重点

1. **执行纪律**: 是否按计划执行
2. **风控合规**: 是否违反风控规则
3. **策略表现**: 各策略盈亏
4. **问题识别**: 找出主要问题
5. **改进方案**: 制定具体行动

### 9.3 复盘模板

```markdown
## 今日总结
✅ 做得好的:
1. ...
2. ...

❌ 需要改进的:
1. ...
2. ...

## 明日计划
1. ...
2. ...
```

---

**V4.3 Development Team**  
**2026-04-11**  
**复盘是进步的阶梯**
