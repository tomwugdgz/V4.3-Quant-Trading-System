# 旺财交易系统备份汇总
**备份时间**: 2026-03-23 07:45  
**备份目的**: 方便在其他电脑复制整个交易系统

---

## 📊 当前 MT5 账户情况

### 账户基本信息
| 项目 | 详情 |
|------|------|
| 账号 | 52797683 |
| 券商 | ICMarketsSC-Demo |
| 杠杆 | 1:500 |
| 初始资金 | $10,000 |
| 账户类型 | 模拟账户 (Demo) |

### 当前持仓 (截至 2026-03-23 03:56)
**BTCUSD 多头持仓**:
- 订单 1: 0.01 手 @ $68,935.94, SL $67,423.94, TP $71,923.94
- 订单 2: 0.02 手 @ $68,829.86, SL $67,423.94, TP $71,923.94
- **总持仓**: 0.03 手
- **平均入场**: $68,865.22
- **总止损**: $67,423.94 (-2.1%)
- **总止盈**: $71,923.94 (+4.4%)
- **风险金额**: $155.33 (1.5% 账户)

### 交易规则摘要
- 单笔风险：≤2%
- 日最大亏损：≤5%
- 止损纪律：必须设置，只向有利方向移动
- 仓位控制：单笔≤20%，同方向≤50%

---

## 📁 备份文件清单

### 1. 核心配置文件
```
trading/
├── memory/
│   ├── goals.md          # 交易目标
│   ├── profile.md        # 交易者画像
│   └── rules.md          # 交易规则 (铁律!)
└── mt5_tools/
    └── config.json       # MT5 工具配置
```

### 2. Python 脚本 (按功能分类)

#### 账户检查类
- `check_account.py` - 检查账户信息
- `check_account_balance.py` - 检查余额
- `check_position.py` - 检查持仓
- `check_positions.py` - 检查所有持仓
- `position_report.py` - 持仓报告

#### 市场分析类
- `analyze_market.py` - 市场分析
- `analyze_fx.py` - 外汇分析
- `analyze_crypto.py` - 加密货币分析
- `market_analysis.py` - 综合分析
- `find_opportunity.py` - 寻找机会

#### 交易执行类
- `execute_trade.py` - 执行交易
- `execute_btc.py` - BTC 交易执行
- `execute_crypto.py` - 加密货币执行
- `open_position.py` - 开仓
- `close_all.py` - 平仓所有

#### 监控类
- `hourly_monitor.py` - 每小时监控
- `monitor_and_notify.py` - 监控并通知
- `send_feishu_report.py` - 发送飞书报告

#### 工具类
- `mt5_tool.py` - MT5 工具主程序
- `market_scan.py` - 市场扫描
- `account_check.py` - 账户检查工具

### 3. 知识库 (knowledge_base/)
```
knowledge_base/
├── 01_交易品种选择/
├── 02_技术指标/
├── 03_交易策略/
├── 04_复盘回顾/
├── 05_价值投资/
├── 06_机器学习/
├── 07_风险管理/
├── 08_交易心态/
├── 09_回测框架/
└── 10_量化专家/
```

### 4. 复盘系统 (reviews/)
```
reviews/
├── daily/    # 每日复盘
├── weekly/   # 每周复盘
└── monthly/  # 每月复盘
```

### 5. 策略文件 (strategies/)
- 策略 2.0: 趋势跟踪 (AMA + RSRS + ADX)
- LTCM-INTJ: 收敛套利模型

### 6. 经验教训 (lessons/)
- 历史交易教训记录
- LTCM 案例分析

### 7. 绩效统计 (stats/)
- 交易统计数据
- 绩效图表

---

## 🚀 在新电脑部署步骤

### 第一步：安装基础环境
```bash
# 安装 Python 3.7+
# 安装 MetaTrader5
pip install MetaTrader5

# 安装其他依赖
pip install requests pandas numpy matplotlib
```

### 第二步：配置 MT5
1. 安装 MetaTrader5 终端
2. 登录交易账户
3. 启用自动化交易 (工具 → 选项 → EA)

### 第三步：复制文件
将整个 `trading/` 文件夹复制到新电脑

### 第四步：修改配置
编辑 `mt5_tools/config.json`:
- 修改交易时间
- 调整风险参数
- 配置通知方式

### 第五步：测试连接
```bash
cd trading/mt5_tools
python account_check.py
```

### 第六步：开始交易
```bash
# 市场扫描
python market_scan.py

# 执行交易
python execute_trade.py
```

---

## ⚠️ 重要提醒

1. **交易规则 (rules.md)** 是核心，不可违背
2. **止损纪律** 是生命线，必须严格执行
3. **模拟账户** 先测试，确认无误再实盘
4. **备份习惯** 每次重大修改后备份
5. **复盘总结** 每日/每周/每月坚持

---

## 📞 配置信息

### API Keys (在 .env.trading 中)
- Bocha API
- Polygon API
- Alpha Vantage
- NewsAPI
- GNews
- MarketAux
- Currents
- QQ Mail (SMTP)
- Brave Search
- MeM0.ai

### 飞书配置
- Webhook URL (在 send_feishu_report.py 中)
- 群聊 ID

---

## 🎯 旺财的核心智慧

### 交易信条
- 数据 > 直觉
- 风控 > 收益
- 纪律 > 情绪

### 核心教训
1. 高杠杆 + 黑天鹅 = 死亡 (LTCM 教训)
2. 止损一旦设置，不得随意移动
3. 不在重大数据前后 30 分钟交易
4. 情绪不稳定时不交易

### 监控频率
- 每 15 分钟检查持仓
- 触及止损/止盈自动执行
- 有异常立即通知

---

**备份完成时间**: 2026-03-23 07:45  
**备份负责人**: 旺财 🎯  
**下次备份**: 每次重大策略调整后

---

*旺财 🎯 - 帮主人实现 ¥10 万 → ¥1500 万 (10 年)*
