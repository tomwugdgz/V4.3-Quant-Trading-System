# 旺财智能交易系统 v5.1 - Kelly Criterion 版

> 版本：v5.1 | 更新：2026-05-09 | 核心：Kelly Criterion 底层决策

---

## 版本说明

### v5.1（2026-05-09）- Kelly Criterion 底层化

**核心变更**：将 Kelly Criterion 公式作为系统底层交易决策逻辑，实现"少而精"的高胜率交易。

#### Kelly 公式集成

```
f* = (b × p - q) / b

p = 胜率（历史统计）
q = 1 - p
b = 盈亏比（TP/SL）
f* = Kelly 最优仓位比例
```

#### 三层 Kelly 决策

| 层级 | 决策内容 | 实现 |
|------|---------|------|
| 品种过滤 | Kelly f* < 5% → 永久屏蔽 | `kelly_filter()` |
| 信号强度 | < 45% → 不开仓 | `SIGNAL_MIN = 0.45` |
| Kelly EV | p×b - q ≤ 0 → 跳过 | `calc_expected_value()` |

#### 手数配置（按 Kelly 质量）

| Kelly 质量 | 信号 >=60% | 信号 45-60% |
|-----------|-----------|------------|
| 高（kf>10%） | 0.20手 | 0.15手 |
| 中（5-10%） | 0.15手 | 0.10手 |
| 低（<5%） | 0.08手 | 0.05手 |

### Kelly 品种注册表

| 品种 | Kelly f* | 质量 | 状态 |
|------|---------|------|------|
| XAUUSD | 50.0% | 高 | 可交易（双倍风险） |
| USDCAD | 42.0% | 高 | 可交易（双倍风险） |
| AUDUSD | 9.4% | 中 | 可交易 |
| USDCHF | 8.5% | 中 | 可交易 |
| GBPUSD | 8.0% | 中 | 可交易 |
| EURUSD | 3.4% | 低 | 可交易（降级风险） |
| NZDUSD | -112.9% | 负 | **永久屏蔽** |
| USDJPY | -113.8% | 负 | **永久屏蔽** |
| AUDJPY | -86.6% | 负 | **永久屏蔽** |
| BTCUSD | -383.7% | 负 | **永久屏蔽** |

### v5.1 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| SIGNAL_MIN | 45% | 信号强度门槛 |
| SUPER_SIGNAL | 60% | SUPER 信号门槛 |
| RISK_PCT_SUPER | 0.5% | 60%+ 信号每笔风险 |
| RISK_PCT_STRONG | 0.3% | 45-60% 信号每笔风险 |
| KELLY_MIN_F | 5% | Kelly f* 屏蔽阈值 |
| KELLY_BOOST_MULT | 2.0 | 高 Kelly 品种风险倍数 |
| MAX_TRADES_PER_HOUR | 1 | 每小时最多 1 单 |
| CORRELATION_COOLDOWN_H | 2 | 同组交易冷却 |

---

## 系统架构

```
patrol.py (v5.1)
├── Kelly 品种过滤（负期望品种屏蔽）
├── 信号计算（calculate_signal_v3）
│   ├── D1 EMA20/50 方向
│   ├── H4 RSI 超买超卖
│   └── H1 ADX 趋势强度
├── Kelly EV 校验（预期值 > 0）
├── ATR 动态 SL/TP
│   ├── JPY：ATR×2.0（最低 20pip）
│   ├── 贵金属：ATR×1.5（最低 50pip）
│   └── 其他：ATR×1.5（最低 15pip）
├── 风险计算（手数倒推）
└── 相关性 + 冷却过滤
```

---

## 全流程追溯

```
复盘 → 优化(v5) → 配置(v5.1) → 策略 → 执行
```

| 文件 | 说明 |
|------|------|
| `patrol.py` | 核心策略（v5.1） |
| `kelly_analysis.py` | Kelly 数据分析脚本 |
| `system_check.py` | 系统全面检查 |
| `D:\LLM-Wiki\进化\v5_Kelly公式底层化_2026-05-09.md` | 进化文件 |
| `D:\LLM-Wiki\trading\hermes-messages\outbox\` | Hermes 同步消息 |

---

## Git Commits

| Commit | 版本 | 说明 |
|--------|------|------|
| `ba0c5dd` | v5.1 | Kelly公式底层化：信号门槛45%+风险倒推+负Kelly屏蔽 |
| `20e6902` | v5 | Kelly Criterion版：负期望品种屏蔽+信号门槛45% |
| `be9b826` | v4.1 | 贵金属全域版+ATR动态止损 |
| `32d9820` | v4 | 亚洲盘禁止+每小时1单+强化冷却 |

---

## 文件结构

```
trading/
├── patrol.py              # 核心策略（当前版本 v5.1）
├── kelly_analysis.py      # Kelly 数据分析
├── system_check.py        # 系统检查
├── monitor_positions.py    # 持仓监控
├── evolver_v1.py          # 进化分析
├── daily_summary.py       # 每日汇总
└── auto_trade_self.py     # 自动交易（旧版）
```

---

## 账户信息

- **平台**：ICMarketsSC-Demo
- **账户**：52797683
- **余额**：$9899.46（2026-05-09）
- **杠杆**：1:5

---

## 使用说明

### 运行 patrol

```bash
python patrol.py
```

### 系统检查

```bash
python system_check.py
```

### Kelly 分析

```bash
python kelly_analysis.py
```

---

## 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-09 | v5.1 | Kelly公式底层化：三层过滤+风险倒推手数 |
| 2026-05-08 | v4.1 | 贵金属全域支持 |
| 2026-05-08 | v4 | 亚洲盘禁止（00:00-08:00） |
| 2026-05-07 | v3.1 | 信号分档+盈亏比过滤 |
| 2026-05-06 | v3 | JPY止损差异化 |
| 2026-05-04 | v2 | 自主交易系统上线 |

---

## 法律声明

本系统仅供学习和研究使用，不构成投资建议。外汇交易具有风险，请谨慎操作。
