# V4.3 Edge 修复系统

**版本**: V4.3.0  
**创建时间**: 2026-04-10  
**状态**: 开发中  

---

## 快速开始

### 1. 安装依赖

```bash
pip install pandas numpy MetaTrader5
```

### 2. 测试模块

```bash
# 测试 Market Regime
cd trading/v4_3
python market_regime.py

# 测试 Factor Score
python factor_score.py

# 测试 Risk Agent
python risk_agent.py
```

### 3. 运行扫描

```bash
# 仅扫描
python main_v43.py

# 自动执行交易
python main_v43.py --auto-execute

# 指定品种
python main_v43.py --symbols EURUSD GBPUSD USDJPY
```

---

## 系统架构

```
┌─────────────────────┐
│  Market Regime      │  ← 判断市场状态
│      Agent          │     (趋势/震荡/高波动)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Factor Score       │  ← 多因子评分
│      Engine         │     (0-100 分)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Risk Agent         │  ← 风控检查
│                     │     (否决权)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Execution          │  ← 订单执行
│      Agent          │
└─────────────────────┘
```

---

## 核心模块

### Market Regime Agent

**功能**: 判断市场状态，动态调整阈值

**市场状态**:
- `TRENDING_UP` - 上涨趋势
- `TRENDING_DOWN` - 下跌趋势
- `RANGING` - 震荡市
- `HIGH_VOLATILITY` - 高波动

**动态阈值**:
| 市场状态 | 信号阈值 | 仓位系数 |
|----------|----------|----------|
| TRENDING_UP | 0.08% | 1.0x |
| TRENDING_DOWN | 0.08% | 1.0x |
| RANGING | 0.15% | 0.5x |
| HIGH_VOLATILITY | 0.20% | 0.3x |

---

### Factor Score Engine

**功能**: 多因子评分（0-100 分）

**因子库**:
1. **动量因子** (权重 30%)
   - EMA 斜率
   - 价格动量

2. **均值回归因子** (权重 30%)
   - RSI 超买超卖
   - 布林带位置

3. **突破因子** (权重 20%)
   - 突破 N 日高点/低点
   - 成交量放大

4. **波动率因子** (权重 20%)
   - ATR 变化
   - 布林带宽度

**信号映射**:
| 评分 | 信号 |
|------|------|
| ≥70 | STRONG_BUY |
| 55-69 | BUY |
| 46-54 | NEUTRAL |
| 31-45 | SELL |
| ≤30 | STRONG_SELL |

---

### Risk Agent

**功能**: 独立风控，实时否决权

**风控检查**:
1. 账户级检查（保证金水平、杠杆）
2. 仓位检查（总持仓、单一品种）
3. 风险敞口检查（总风险≤3%）
4. VaR 检查（95% VaR ≤ 2% 净值）
5. 相关性检查（避免同向叠加）

**仓位计算**:
```
单笔风险 = 0.5% 账户
止损距离 = 1.5 × ATR
手数 = 风险金额 / (止损距离 × 点值)
```

---

## 配置文件

### config/regime_config.json

市场状态判断参数

### config/factor_weights.json

因子权重配置

### config/risk_params.json

风控参数配置

---

## 验收标准

| 指标 | V4 标准 | 当前 v2.0 | V4.3 目标 |
|------|--------|----------|----------|
| 一致性 | ≥85 | 100% | ≥90 |
| 回撤控制 | ≥70 | 95% | ≥80 |
| 回测稳定性 | ≥70 | 45% | ≥70 |
| 胜率 | ≥55% | 52.8% | ≥58% |
| 盈亏比 | ≥1.5 | 1.9 | ≥1.8 |
| 综合评分 | ≥85 | 72.9 | ≥80 |

---

## 实施计划

| 阶段 | 时间 | 模块 | 状态 |
|------|------|------|------|
| 1 | 4/10-4/12 | Market Regime | ✅ 完成 |
| 2 | 4/12-4/15 | Factor Score | ✅ 完成 |
| 3 | 4/15-4/17 | Risk Agent | ✅ 完成 |
| 4 | 4/17-4/20 | Review Agent | ⏳ 待开发 |
| 5 | 4/20-4/25 | Walk-Forward | ⏳ 待开发 |

---

## 测试

### 单元测试

```bash
cd trading/tests
python test_regime.py
python test_factors.py
python test_risk.py
```

### 模拟盘测试

```bash
# 模拟盘运行 2 周
python main_v43.py --paper-trading
```

### 实盘部署

```bash
# 通过验收后
python main_v43.py --auto-execute --live
```

---

## 故障排除

### MT5 连接失败

```bash
# 检查 MT5 是否运行
# 检查账户是否登录
```

### 模块导入错误

```bash
# 确保在 trading/v4_3 目录下运行
# 或者添加路径到 PYTHONPATH
```

### 数据不足

```bash
# 确保有足够的历史 K 线
# 检查网络连接
```

---

## 下一步

1. ✅ Market Regime Agent - 完成
2. ✅ Factor Score Engine - 完成
3. ✅ Risk Agent - 完成
4. ⏳ Review Agent - 开发中
5. ⏳ Walk-Forward Validator - 待开发

---

**文档**: `V4.3_实施流程.md`  
**代码**: `trading/v4_3/`  
**配置**: `trading/config/`
