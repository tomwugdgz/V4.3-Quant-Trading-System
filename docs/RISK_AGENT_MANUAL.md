# 风控 Agent 手册 (Risk Agent Manual)

**版本**: V4.3.0  
**创建时间**: 2026-04-11  
**最后更新**: 2026-04-11

---

## 一、概述

Risk Agent 是 V4.3 系统的独立风控模块，拥有实时否决权，确保所有交易符合风控规则。

### 1.1 核心特性

1. **独立性**: 与策略生成模块完全解耦
2. **实时性**: 每笔交易前实时检查
3. **否决权**: 一票否决，即使信号再好也可拒绝
4. **多维度**: 账户级 + 仓位级 + VaR + 相关性检查

### 1.2 风控理念

```
风控优先于收益
本金安全第一
宁可错过，不可做错
```

### 1.3 文件位置

```
trading/v4_3/risk_agent.py
```

---

## 二、风控规则

### 2.1 账户级检查

#### 2.1.1 保证金水平

**规则**:
```python
min_margin_level = 200%
```

**检查**:
```python
if account.margin_level < 200:
    return False, "保证金水平不足"
```

**说明**:
- 保证金水平 = 净值 / 已用保证金 × 100%
- <200% 表示风险过高
- 建议保持在 300% 以上

---

#### 2.1.2 实际杠杆

**规则**:
```python
max_leverage = 3.0x
```

**检查**:
```python
if account.leverage > 3.0:
    return False, "杠杆过高"
```

**说明**:
- 实际杠杆 = 持仓总市值 / 净值
- 账户杠杆可能为 5x、10x，但实际使用不超过 3x
- 高杠杆放大收益也放大风险

---

#### 2.1.3 单日亏损

**规则**:
```python
max_daily_loss_percent = 3%
```

**检查**:
```python
if daily_loss > 3% of equity:
    return False, "触及单日亏损红线"
```

**说明**:
- 触及红线后停止当日交易
- 防止情绪化交易
- 保护本金

---

#### 2.1.4 总回撤

**规则**:
```python
max_total_drawdown_percent = 10%
```

**检查**:
```python
if total_drawdown > 10% of peak_equity:
    return False, "触及总回撤红线"
```

**说明**:
- 总回撤从权益峰值计算
- 触及红线后暂停系统，重新评估
- 防止系统性风险

---

### 2.2 仓位级检查

#### 2.2.1 总持仓数

**规则**:
```python
max_positions = 3
```

**检查**:
```python
if len(positions) >= 3:
    return False, "持仓数已达上限"
```

**说明**:
- 避免过度分散
- 集中优势兵力
- 便于管理

---

#### 2.2.2 单一品种持仓

**规则**:
```python
max_same_symbol = 2
```

**检查**:
```python
symbol_positions = [p for p in positions if p.symbol == symbol]
if len(symbol_positions) >= 2:
    return False, "单一品种持仓已达上限"
```

**说明**:
- 避免风险过度集中
- 防止重复开仓
- 特殊情况：加仓策略

---

#### 2.2.3 总风险敞口

**规则**:
```python
max_total_risk_percent = 3%
```

**检查**:
```python
total_risk = sum(position.risk for position in positions)
if total_risk > 3% of equity:
    return False, "总风险敞口过大"
```

**说明**:
- 单笔风险：0.5%
- 总风险：3%
- 风险 = 手数 × 止损距离 × 点值

---

### 2.3 VaR 检查

#### 2.3.1 VaR 计算

**规则**:
```python
confidence_level = 95%
max_var_percent = 2% of equity
```

**公式**:
```python
# 历史模拟法
returns = calculate_historical_returns(periods=252)
var_95 = np.percentile(returns, 5)  # 5% 分位数

# 参数法
var_95 = portfolio_value × z_score × volatility
z_score = 1.645  # 95% 置信度
```

**检查**:
```python
if var_95 > 2% of equity:
    return False, "VaR 超标"
```

**说明**:
- VaR (Value at Risk): 在险价值
- 95% 置信度：95% 的情况下损失不超过 VaR
- 极端情况下可能失效

---

### 2.4 相关性检查

#### 2.4.1 原理

**目的**: 避免同向风险叠加

**规则**:
```python
# 检查新订单与现有持仓的相关性
if correlation(new_order, existing_positions) > 0.7:
    return False, "相关性过高"
```

**说明**:
- 高相关性品种：EURUSD 与 GBPUSD
- 避免同时做多/做空高相关品种
- 分散风险

---

#### 2.4.2 相关品种分组

**高相关组** (相关系数 > 0.7):
```
EURUSD, GBPUSD, AUDUSD, NZDUSD  (美元弱势组)
USDJPY, USDCHF, USDCAD          (美元强势组)
```

**规则**:
```python
# 同一组内不超过 2 个同向持仓
if same_group_same_direction_count >= 2:
    return False, "同组同向持仓过多"
```

---

### 2.5 止损检查

#### 2.5.1 硬止损

**规则**:
```python
stop_loss_atr_multiplier = 1.5
min_stop_points = 20
```

**计算**:
```python
atr = calculate_atr(symbol, period=14)
stop_distance = max(atr × 1.5, 20 points)

if signal.direction == 'BUY':
    stop_loss = entry_price - stop_distance
else:
    stop_loss = entry_price + stop_distance
```

**检查**:
```python
if not has_stop_loss(order):
    return False, "必须设置止损"

if stop_distance < min_stop_points:
    return False, "止损过窄"
```

---

#### 2.5.2 移动止损

**规则**:
```python
# 盈利达到 1R 后启动移动止损
trailing_start_profit = 1R  # R = 初始风险

# 移动止损距离
trailing_distance = 1.5 × ATR
```

**执行**:
```python
if current_profit >= initial_risk:
    # 启动移动止损
    new_stop = highest_price_since_entry - trailing_distance
    
    if new_stop > current_stop:
        modify_stop_loss(new_stop)
```

---

## 三、仓位计算

### 3.1 基本公式

```python
# 单笔风险金额
risk_amount = equity × risk_per_trade_percent
risk_per_trade_percent = 0.5%

# 止损距离（点数）
stop_distance_points = abs(entry_price - stop_loss) / point_value

# 手数计算
lot_size = risk_amount / (stop_distance_points × point_value)
```

### 3.2 点值计算

**直盘** (USD 在后):
```python
point_value = 10  # 标准手
# EURUSD: 1 点 = $10
```

**横盘** (USD 在前):
```python
point_value = 10 / exchange_rate
# USDJPY: 1 点 = ¥10 / 110 = $0.091
```

### 3.3 示例

**场景**: EURUSD 买入，账户$10,000

```python
equity = 10000
risk_percent = 0.005  # 0.5%
entry_price = 1.1000
stop_loss = 1.0950
point_value = 10

# 风险金额
risk_amount = 10000 × 0.005 = $50

# 止损距离
stop_distance = (1.1000 - 1.0950) / 0.0001 = 50 点

# 手数
lot_size = 50 / (50 × 10) = 0.1 手
```

---

## 四、使用方法

### 4.1 基本使用

```python
from v4_3.risk_agent import RiskAgent

# 初始化
agent = RiskAgent()

# 检查是否可以交易
can_trade, reason = agent.can_trade(
    symbol="EURUSD",
    signal="BUY",
    volume=0.1,
    account_info=account,
    positions=positions
)

if can_trade:
    print("风控通过，可以交易")
else:
    print(f"风控不通过：{reason}")
```

### 4.2 批量检查

```python
# 检查多个信号
signals = [
    {"symbol": "EURUSD", "signal": "BUY", "volume": 0.1},
    {"symbol": "GBPUSD", "signal": "SELL", "volume": 0.1},
    {"symbol": "USDJPY", "signal": "BUY", "volume": 0.1},
]

approved_signals = []

for signal in signals:
    can_trade, reason = agent.can_trade(**signal)
    if can_trade:
        approved_signals.append(signal)
    else:
        print(f"{signal['symbol']}: {reason}")

print(f"通过：{len(approved_signals)}/{len(signals)}")
```

### 4.3 自定义风控参数

```python
# 加载配置
from v4_3.config_loader import ConfigLoader

loader = ConfigLoader()
risk_params = loader.load_config('risk_params')

# 自定义参数
custom_params = {
    'max_daily_loss_percent': 0.02,  # 2%
    'max_positions': 5,
    'risk_per_trade_percent': 0.003,  # 0.3%
}

# 创建 Agent
agent = RiskAgent(custom_params=custom_params)
```

---

## 五、风控报告

### 5.1 生成报告

```python
# 生成风控报告
report = agent.generate_risk_report(positions, account)

print(report)
```

### 5.2 报告内容

```
================================================================================
风控报告 - 2026-04-11 15:30
================================================================================

账户状态:
  余额：$10,000.00
  净值：$10,022.92
  保证金水平：350%
  实际杠杆：1.5x

持仓状态:
  总持仓：2/3
  总风险敞口：1.2%/3.0%

风险指标:
  VaR(95%): $150 (1.5%)
  最大单日亏损：-$120 (-1.2%)
  最大回撤：-$250 (-2.5%)

合规检查:
  ✅ 保证金水平充足
  ✅ 杠杆在安全范围
  ✅ 单日亏损未超标
  ✅ 总回撤在控制内
  ✅ 持仓数未超限
  ✅ 风险敞口合理

建议:
  - 可新增 1 个持仓
  - 可用风险敞口：1.8%
  - 当前风险状态：安全

================================================================================
```

---

## 六、常见问题

### Q1: 为什么我的交易被风控拒绝？

**A**: 检查以下项目：
1. 保证金水平是否>200%
2. 实际杠杆是否<3x
3. 持仓数是否<3
4. 总风险敞口是否<3%
5. 是否设置止损
6. 止损是否合理（≥1.5×ATR 或≥20 点）

---

### Q2: 如何调整风控参数？

**A**: 
1. 修改 `config/risk_params.json`
2. 或在代码中传入自定义参数
3. 建议逐步调整，观察效果

---

### Q3: VaR 计算准确吗？

**A**:
- VaR 基于历史数据，不能预测未来
- 极端市场情况下可能失效
- 建议与其他风控指标配合使用

---

### Q4: 相关性检查有必要吗？

**A**:
- 非常有必要！
- 2008 年金融危机中，很多基金因相关性失效而破产
- 正常市场下相关性稳定，危机时相关性趋向 1

---

### Q5: 移动止损如何设置？

**A**:
```python
# 盈利达到 1R 后启动
if profit >= initial_risk:
    # 移动止损 = 最高价 - 1.5×ATR
    new_stop = highest_price - 1.5 × ATR
    modify_stop_loss(new_stop)
```

---

## 七、最佳实践

### 7.1 风控检查清单

**交易前**:
- [ ] 保证金水平>200%
- [ ] 实际杠杆<3x
- [ ] 持仓数<3
- [ ] 风险敞口<3%
- [ ] 设置止损
- [ ] 止损合理

**交易中**:
- [ ] 监控保证金水平
- [ ] 跟踪浮动盈亏
- [ ] 调整移动止损
- [ ] 关注相关性变化

**交易后**:
- [ ] 记录交易数据
- [ ] 更新风控指标
- [ ] 生成风控报告
- [ ] 复盘总结

---

### 7.2 风控日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='risk_log.log'
)

# 记录风控检查
def log_risk_check(signal, result, reason):
    logging.info(f"风控检查：{signal} -> {result} ({reason})")
```

---

### 7.3 风控仪表板

**关键指标**:
```
保证金水平：██████████ 350% (安全)
实际杠杆：  ████░░░░░░ 1.5x/3.0x (安全)
持仓数：    ████░░░░░░ 2/3 (安全)
风险敞口：  ████░░░░░░ 1.2%/3.0% (安全)
VaR(95%):   ████░░░░░░ 1.5%/2.0% (安全)
```

---

## 八、风控案例

### 案例 1: 保证金不足

**场景**: 
- 账户余额：$5,000
- 已用保证金：$3,000
- 净值：$4,800

**计算**:
```python
margin_level = 4800 / 3000 × 100% = 160%
```

**结果**: 
```
❌ 风控拒绝
原因：保证金水平 160% < 200%
```

---

### 案例 2: 风险敞口过大

**场景**:
- 账户净值：$10,000
- 现有持仓风险：2.5%
- 新订单风险：0.5%

**计算**:
```python
total_risk = 2.5% + 0.5% = 3.0%
```

**结果**:
```
❌ 风控拒绝
原因：总风险敞口 3.0% 已达上限
```

---

### 案例 3: 相关性过高

**场景**:
- 现有持仓：EURUSD BUY
- 新订单：GBPUSD BUY

**检查**:
```python
correlation(EURUSD, GBPUSD) = 0.85 > 0.7
```

**结果**:
```
❌ 风控拒绝
原因：EURUSD 与 GBPUSD 相关性过高 (0.85)
```

---

## 九、总结

**风控核心**:
1. 保证金安全第一
2. 风险分散优先
3. 止损必须设置
4. 实时监控执行

**风控目标**:
- 单日亏损≤3%
- 总回撤≤10%
- 避免灾难性损失
- 长期稳定盈利

---

**V4.3 Development Team**  
**2026-04-11**  
**风控是交易的生命线**
