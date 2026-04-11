# V4.3 量化交易系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

**一个基于多因子评分的智能量化交易系统**

---

## 📖 项目简介

V4.3 是一个多因子量化交易系统，通过市场状态判断、多因子评分、动态风控三大核心模块，实现智能化交易决策。

### 核心特性

- 🎯 **市场状态感知**: 根据趋势/震荡/高波动动态调整策略
- 📊 **多因子评分**: 4 大因子库，16 个子因子，全面评估市场
- 🛡️ **动态风控**: 独立 Risk Agent，实时否决权
- 📈 **自动化复盘**: 自动归因分析，持续进化

### 性能目标

| 指标 | v2.0 当前 | V4.3 目标 | 提升 |
|------|----------|----------|------|
| 回测稳定性 | 45% | ≥70% | +55% |
| 综合评分 | 72.9 | ≥80 | +10% |
| 胜率 | 52.8% | ≥58% | +10% |

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MetaTrader 5
- Windows/Linux/macOS

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置系统

1. 编辑配置文件 `config/` 目录下的 JSON 文件
2. 配置 MetaTrader 5 账户信息
3. 设置风控参数

### 运行系统

```bash
# 环境检查
python v4_3/check_environment.py

# 启动模拟盘
python v4_3/paper_trading_monitor.py

# 查看状态
python v4_3/check_paper_trading_status.py

# 生成每日报告
python v4_3/generate_daily_report.py
```

---

## 📁 项目结构

```
V4.3-Quant-Trading-System/
├── core/                        # 核心模块
│   ├── market_regime.py         # 市场状态判断
│   ├── factor_score.py          # 因子评分引擎
│   ├── risk_agent.py            # 风控 Agent
│   └── review_agent.py          # 复盘 Agent
│
├── factors/                     # 因子库
│   ├── momentum.py              # 动量因子
│   ├── mean_reversion.py        # 均值回归因子
│   ├── breakout.py              # 突破因子
│   └── volatility.py            # 波动率因子
│
├── config/                      # 配置文件
│   ├── regime_config.json
│   ├── factor_weights.json
│   ├── risk_params.json
│   └── paper_trading_config.json
│
├── docs/                        # 文档
│   ├── V4.3_ARCHITECTURE.md
│   ├── FACTOR_LIBRARY.md
│   ├── RISK_AGENT_MANUAL.md
│   └── ...
│
├── tests/                       # 测试
│   ├── test_factors.py
│   ├── test_review.py
│   └── test_v43_system.py
│
├── logs/                        # 日志
├── trading/                     # 数据库
│
├── requirements.txt             # 依赖
├── README.md                    # 本文件
└── LICENSE                      # 开源协议
```

---

## 📊 因子库

### 4 大因子类别

| 因子 | 权重 | 子因子 | 适用市场 |
|------|------|--------|----------|
| 动量因子 | 30% | EMA 斜率、价格动量、MACD | 趋势市 |
| 均值回归因子 | 30% | RSI、布林带、乖离率 | 震荡市 |
| 突破因子 | 20% | 价格突破、成交量、形态 | 突破行情 |
| 波动率因子 | 20% | ATR、布林带宽度、历史波动率 | 所有市场 |

---

## 🛡️ 风控系统

### 账户级风控

- 保证金水平 >200%
- 实际杠杆 <3x
- 单日亏损 ≤3%
- 总回撤 ≤10%

### 仓位级风控

- 最大持仓 ≤3 单
- 单一品种 ≤2 单
- 单笔风险 ≤0.5%
- 总风险敞口 ≤3%

### 止损设置

- 硬止损：ATR×1.5 或 20 点
- 移动止损：盈利 1R 后启动

---

## 📈 模拟盘

### 当前状态

- **状态**: 🟢 运行中
- **启动时间**: 2026-04-11
- **扫描间隔**: 60 分钟
- **交易品种**: 7 个主要外汇

### 验收标准

| 指标 | 标准 | 周期 |
|------|------|------|
| 交易次数 | ≥10 单 | 2 周 |
| 胜率 | >50% | 2 周 |
| 盈亏比 | >1.5:1 | 2 周 |
| 最大回撤 | <5% | 2 周 |
| 风控违规 | 0 次 | 2 周 |

---

## 📚 文档

### 核心文档

- [系统架构](docs/V4.3_ARCHITECTURE.md) - 完整系统架构说明
- [因子库文档](docs/FACTOR_LIBRARY.md) - 4 大因子详细说明
- [风控手册](docs/RISK_AGENT_MANUAL.md) - 风控规则和案例
- [复盘指南](docs/REVIEW_AGENT_GUIDE.md) - 归因分析和报告生成

### 使用文档

- [部署检查清单](docs/DEPLOYMENT_CHECKLIST.md) - 部署前准备
- [Walk-Forward 教程](docs/WALK_FORWARD_TUTORIAL.md) - 滚动回测验证
- [API 参考](docs/API_REFERENCE.md) - 完整 API 文档
- [故障排除](docs/TROUBLESHOOTING.md) - 常见问题解决

---

## 🧪 测试

### 运行测试

```bash
# 因子测试
pytest tests/test_factors.py -v

# Review Agent 测试
pytest tests/test_review.py -v

# Walk-Forward 测试
pytest tests/test_walk_forward.py -v

# 系统完整性测试
python tests/test_v43_system.py
```

### 测试覆盖

| 模块 | 测试用例 | 状态 |
|------|----------|------|
| 因子库 | 16 个 | ✅ |
| Review Agent | 5 个 | ✅ |
| Walk-Forward | 8 个 | ✅ |
| 系统完整性 | 10 个 | ✅ 70% |

---

## 🔧 配置说明

### 市场状态配置 (config/regime_config.json)

```json
{
  "trend": {
    "ADX_threshold": 25,
    "ema_short": 10,
    "ema_long": 20
  },
  "dynamic_thresholds": {
    "TRENDING_UP": 0.08,
    "RANGING": 0.15,
    "HIGH_VOLATILITY": 0.20
  }
}
```

### 风控配置 (config/risk_params.json)

```json
{
  "account": {
    "min_margin_level": 200,
    "max_daily_loss_percent": 0.03
  },
  "position": {
    "max_positions": 3,
    "risk_per_trade_percent": 0.005
  }
}
```

---

## 📊 性能监控

### 实时监控

- 每 60 分钟扫描市场
- 自动生成交易信号
- 实时风控检查
- 自动记录日志

### 每日报告

- 20:00 自动生成
- 核心指标统计
- 归因分析
- 问题识别
- 改进建议

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 开源协议

本项目采用 MIT 协议 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/YOUR_USERNAME/V4.3-Quant-Trading-System)
- **问题反馈**: [Issues](https://github.com/YOUR_USERNAME/V4.3-Quant-Trading-System/issues)

---

## 🙏 致谢

感谢以下开源项目：

- MetaTrader 5 - 交易平台
- pandas - 数据分析
- numpy - 科学计算
- pytest - 测试框架

---

**V4.3 Development Team**  
**2026-04-11**  
**数据驱动，持续进化**

---

*如果这个项目对你有帮助，请给一个 ⭐️ Star！*
