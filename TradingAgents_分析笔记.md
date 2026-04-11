# TradingAgents 多 Agent 交易系统

## 📋 系统架构

TradingAgents 系一个基于大语言模型（LLM）嘅多 Agent 协作交易框架。

### 核心 Agent 角色

```
┌─────────────────────────────────────────────────────┐
│              TradingAgents 系统                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐      ┌─────────────┐              │
│  │ Bull Agent  │      │ Bear Agent  │              │
│  │ (看涨分析)  │      │ (看跌分析)  │              │
│  └──────┬──────┘      └──────┬──────┘              │
│         │                    │                      │
│         └────────┬───────────┘                      │
│                  │                                  │
│         ┌────────▼────────┐                         │
│         │  Debate/ voting │                         │
│         │   (辩论/投票)    │                         │
│         └────────┬────────┘                         │
│                  │                                  │
│  ┌───────────────┼───────────────┐                 │
│  │               │               │                 │
│  ▼               ▼               ▼                 │
│  Risk          Sentiment      Technical            │
│  Agent         Agent          Agent                │
│ (风控)        (情绪)          (技术)                │
│                  │                                  │
│         ┌────────▼────────┐                         │
│         │  Decision Agent │                         │
│         │   (决策代理)     │                         │
│         └────────┬────────┘                         │
│                  │                                  │
│         ┌────────▼────────┐                         │
│         │ Execution Agent │                         │
│         │   (执行代理)     │                         │
│         └─────────────────┘                         │
└─────────────────────────────────────────────────────┘
```

---

## 🤖 Agent 详解

### 1. Bull Agent (看涨分析师)
**职责**: 寻找看涨信号，论证做多理由

**分析维度**:
- 技术指标（RSI, MACD, 均线）
- 基本面数据（财报，增长）
- 市场情绪（新闻，社交媒体）
- 资金流向（机构买入）

**输出**: 看涨报告 + 置信度评分

---

### 2. Bear Agent (看跌分析师)
**职责**: 寻找看跌信号，论证做空理由

**分析维度**:
- 技术超买信号
- 基本面风险
- 负面新闻情绪
- 资金流出

**输出**: 看跌报告 + 置信度评分

---

### 3. Risk Agent (风控官)
**职责**: 评估交易风险，设置仓位限制

**功能**:
- 计算 VaR (风险价值)
- 设置止损/止盈
- 仓位 sizing (凯利公式)
- 最大回撤控制
- 相关性分析

**输出**: 风险报告 + 最大仓位建议

---

### 4. Sentiment Agent (情绪分析师)
**职责**: 分析市场情绪

**数据源**:
- 新闻标题情感分析
- Twitter/Reddit 情绪
- 财经媒体倾向
- 搜索趋势（Google Trends）

**输出**: 情绪分数 (-1 到 +1)

---

### 5. Technical Agent (技术分析师)
**职责**: 纯技术分析

**指标**:
- 趋势：SMA, EMA, MACD
- 动量：RSI, Stochastic, Williams %R
- 波动：ATR, Bollinger Bands
- 成交量：OBV, Volume Profile
- 支撑阻力：Pivot Points, Fibonacci

**输出**: 技术信号 + 关键价位

---

### 6. Fundamental Agent (基本面分析师)
**职责**: 基本面分析

**分析**:
- 财报数据（PE, PB, EPS）
- 经济增长数据（GDP, CPI, 就业）
- 央行政策（利率，QE）
- 行业前景

**输出**: 基本面评分

---

### 7. Decision Agent (决策者)
**职责**: 综合所有 Agent 意见，做最终决策

**决策流程**:
1. 收集 Bull/Bear 报告
2. 参考 Risk Agent 风控建议
3. 加权投票（Technical 40% + Fundamental 30% + Sentiment 20% + Risk 10%）
4. 生成交易决策：BUY / SELL / HOLD

**输出**: 最终交易信号

---

### 8. Execution Agent (交易员)
**职责**: 执行交易

**功能**:
- 选择订单类型（市价/限价）
- 拆分大单（避免冲击）
- 监控滑点
- 执行止损/止盈

**输出**: 执行报告

---

## 🔄 工作流程

```
1. 数据收集
   ↓
2. 各 Agent 独立分析
   ↓
3. Bull vs Bear 辩论
   ↓
4. Risk Agent 评估
   ↓
5. Decision Agent 投票
   ↓
6. Execution Agent 执行
   ↓
7. 监控 + 复盘
```

---

## 📁 典型项目结构

```
TradingAgents/
├── agents/
│   ├── bull_agent.py          # 看涨分析
│   ├── bear_agent.py          # 看跌分析
│   ├── risk_agent.py          # 风控
│   ├── sentiment_agent.py     # 情绪
│   ├── technical_agent.py     # 技术
│   ├── fundamental_agent.py   # 基本面
│   ├── decision_agent.py      # 决策
│   └── execution_agent.py     # 执行
├── data/
│   ├── market_data.py         # 行情数据
│   └── news_feed.py           # 新闻
├── models/
│   ├── llm_wrapper.py         # LLM 封装
│   └── prompts/               # 提示词模板
├── utils/
│   ├── risk_calculator.py     # 风险计算
│   └── backtester.py          # 回测
├── config/
│   └── settings.yaml          # 配置
├── main.py                    # 主程序
└── requirements.txt           # 依赖
```

---

## 🔑 核心逻辑代码示例

### Bull Agent 提示词模板
```python
BULL_PROMPT = """
你系一个专业交易员，负责寻找看涨信号。

分析以下数据：
- 当前价格：{price}
- RSI: {rsi}
- MACD: {macd}
- 20 日趋势：{trend_20d}
- 新闻情绪：{sentiment}

请列出：
1. 3 个最强嘅看涨理由
2. 置信度评分（0-100）
3. 建议入场价
4. 建议止损价
5. 建议止盈价
"""
```

### Decision Agent 投票逻辑
```python
def make_decision(agents_output):
    bull_score = agents_output['bull']['confidence'] * 0.4
    bear_score = agents_output['bear']['confidence'] * 0.4
    risk_score = agents_output['risk']['risk_level']  # 0-1
    sentiment = agents_output['sentiment']['score']  # -1 to 1
    
    final_score = (bull_score - bear_score) * (1 - risk_score) * (1 + sentiment)
    
    if final_score > 0.6:
        return "STRONG_BUY"
    elif final_score > 0.3:
        return "BUY"
    elif final_score < -0.6:
        return "STRONG_SELL"
    elif final_score < -0.3:
        return "SELL"
    else:
        return "HOLD"
```

### Risk Agent 仓位计算
```python
def calculate_position_size(account_balance, risk_per_trade, stop_loss_distance):
    """
    凯利公式变种：仓位 = (账户 * 风险%) / 止损距离
    """
    risk_amount = account_balance * risk_per_trade  # 如 1%
    position_size = risk_amount / stop_loss_distance
    return position_size
```

---

## ⚙️ 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/TradingAgents/TradingAgents.git
cd TradingAgents

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入：
# - LLM API 密钥（OpenAI/Anthropic）
# - 交易所 API（Binance/IBKR）
# - 数据源（Polygon/AlphaVantage）

# 5. 运行回测
python backtest.py --symbol BTCUSD --days 30

# 6. 运行实盘
python main.py --mode live
```

---

## 📊 与旺财现有系统对比

| 特性 | TradingAgents | 旺财 MT5 系统 |
|------|---------------|---------------|
| 决策方式 | 多 Agent 投票 | 单一策略 (AMA+RSRS) |
| AI 驱动 | LLM 大模型 | 传统技术指标 |
| 可解释性 | 高（Agent 辩论） | 中（公式计算） |
| 灵活性 | 高（可加新 Agent） | 中（需改代码） |
| 成本 | 高（LLM API 费用） | 低（本地计算） |
| 延迟 | 高（秒级） | 低（毫秒级） |
| 适合场景 | 日线/小时线 | 分钟线/高频 |

---

## 💡 建议

### 可以借鉴嘅嘢：
1. **多 Agent 架构** - 旺财都可以分拆成唔同角色
2. **Bull/Bear 辩论** - 避免单边思维
3. **Risk Agent 独立** - 风控同交易分离
4. **决策投票机制** - 更稳健

### 唔适合嘅嘢：
1. **LLM 延迟高** - 唔适合旺财嘅高频交易
2. **API 成本高** - 频繁调用 GPT 好贵
3. **过度复杂** - 旺财而家嘅简单策略可能更有效

---

## 🎯 下一步行动

1. **等网络恢复** -  clone 项目源码
2. **阅读代码** - 学习 Agent 设计模式
3. **选择性借鉴** - 将好嘅 idea 融入旺财系统
4. **保持简单** - 唔好为咗 AI 而 AI

---

**记录人**: 旺财 🎯  
**日期**: 2026-03-23  
**状态**: 等待网络恢复后下载源码
