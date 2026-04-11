# 旺财交易系统部署指南
**版本**: 1.0  
**更新日期**: 2026-03-23  
**适用系统**: Windows 10/11

---

## 📦 快速部署 (5 分钟)

### 1. 安装 Python
```bash
# 下载 Python 3.7+ (推荐 3.10)
# https://www.python.org/downloads/

# 安装时勾选 "Add Python to PATH"
```

### 2. 安装依赖
```bash
# 进入交易目录
cd trading

# 安装核心库
pip install MetaTrader5 pandas numpy requests matplotlib

# 可选：数据分析
pip install ta-lib scikit-learn yfinance
```

### 3. 配置 MT5
```bash
# 下载 MetaTrader5
# https://www.metatrader5.com/

# 安装后登录账户
# 工具 → 选项 → 专家顾问 → 允许自动化交易
```

### 4. 测试连接
```bash
cd mt5_tools
python account_check.py
```

看到账户信息即表示连接成功 ✅

---

## 🔧 配置文件说明

### mt5_tools/config.json
```json
{
  "default_volume": 0.01,      // 默认手数
  "default_sl_points": 50,     // 默认止损点数
  "default_tp_points": 100,    // 默认止盈点数
  "max_slippage": 20,          // 最大滑点
  "magic_number": 234000,      // 订单魔术号
  "risk_per_trade": 0.01,      // 单笔风险 (1%)
  "max_daily_loss": 0.03,      // 日最大亏损 (3%)
  "symbols": {                 // 交易品种
    "forex": ["EURUSD", "GBPUSD", "USDJPY"],
    "crypto": ["BTCUSD", "ETHUSD"],
    "metals": ["XAUUSD", "XAGUSD"]
  },
  "trading_hours": {           // 交易时间
    "start": "09:00",
    "end": "17:00",
    "timezone": "Asia/Shanghai"
  }
}
```

### .env.trading (API 配置)
```bash
# 数据 API
BOCHA_API_KEY=your_key
POLYGON_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key

# 新闻 API
NEWSAPI_KEY=your_key
GNEWS_API_KEY=your_key

# 邮件通知 (QQ)
QQ_EMAIL=your_qq@qq.com
QQ_PASSWORD=your_smtp_password

# 飞书通知
FEISHU_WEBHOOK=your_webhook_url
```

---

## 📊 核心脚本使用

### 账户检查
```bash
python check_account.py           # 检查账户信息
python check_position.py          # 检查当前持仓
python position_report.py         # 生成持仓报告
```

### 市场分析
```bash
python analyze_market.py          # 综合分析
python analyze_fx.py              # 外汇分析
python analyze_crypto.py          # 加密货币分析
python market_scan.py             # 扫描市场机会
```

### 交易执行
```bash
python execute_trade.py           # 执行交易
python execute_btc.py             # BTC 交易
python close_all.py               # 平仓所有
```

### 监控通知
```bash
python hourly_monitor.py          # 每小时监控
python monitor_and_notify.py      # 监控并通知
python send_feishu_report.py      # 发送飞书报告
```

---

## 🎯 交易规则 (必须遵守!)

### 铁律
1. **单笔风险 ≤ 2%** - 绝不超过
2. **日最大亏损 ≤ 5%** - 达到即停止
3. **必须设置止损** - 无例外
4. **止损不随意移动** - 只向有利方向

### 禁止行为
- ❌ 不止损/扛单
- ❌ 报复性交易
- ❌ 加仓摊平亏损
- ❌ 重仓赌方向
- ❌ 情绪化交易

### 良好习惯
- ✅ 盘前分析市场
- ✅ 制定交易计划
- ✅ 执行后记录
- ✅ 每日复盘
- ✅ 每周总结

---

## 📁 文件结构
```
trading/
├── memory/              # 交易记忆 (目标/规则/画像)
├── strategies/          # 交易策略
├── knowledge_base/      # 知识库
├── reviews/             # 复盘 (daily/weekly/monthly)
├── journal/             # 交易日志
├── stats/               # 绩效统计
├── lessons/             # 经验教训
├── mt5_tools/           # MT5 工具
│   ├── config.json      # 配置文件
│   ├── account_check.py
│   ├── market_scan.py
│   └── ...
├── *.py                 # 各种脚本
├── BACKUP_SUMMARY.md    # 备份汇总 (本文件)
└── DEPLOYMENT.md        # 部署指南 (本文件)
```

---

## 🔍 故障排查

### MT5 连接失败
```bash
# 1. 检查 MT5 是否运行
# 2. 检查账户是否登录
# 3. 检查自动化交易是否启用
# 4. 重启 MT5 终端
```

### Python 模块缺失
```bash
pip install --upgrade pip
pip install MetaTrader5 --force-reinstall
```

### API 调用失败
```bash
# 1. 检查 .env.trading 配置
# 2. 检查 API key 是否有效
# 3. 检查网络连接
```

---

## 📞 获取帮助

### 查看日志
```bash
# 交易日志
cd journal
cat 2026-03-*.md

# 复盘记录
cd reviews/daily
cat 2026-03-*.md
```

### 联系旺财
- 飞书群：oc_5ac77ac5e951943e6cf87de6245c3122
- 邮箱：duckwolf@qq.com

---

## 🎓 学习资源

### 新手入门
1. 阅读 `memory/rules.md` - 交易规则
2. 阅读 `memory/goals.md` - 交易目标
3. 阅读 `knowledge_base/01_交易品种选择/` - 基础概念

### 进阶学习
1. `knowledge_base/02_技术指标/` - 技术分析
2. `knowledge_base/03_交易策略/` - 策略学习
3. `knowledge_base/07_风险管理/` - 风控核心

### 实战演练
1. 先用模拟账户练习
2. 每日复盘总结
3. 逐步建立自己的策略

---

## ⚡ 快速检查清单

部署完成后，逐项检查：

- [ ] Python 安装成功
- [ ] MetaTrader5 安装并登录
- [ ] 依赖库安装完成
- [ ] config.json 配置正确
- [ ] .env.trading 配置完成
- [ ] account_check.py 运行成功
- [ ] 交易规则已阅读
- [ ] 模拟账户测试通过

全部打勾后即可开始交易！✅

---

**旺财 🎯** - 数据 > 直觉，风控 > 收益，纪律 > 情绪

*最后更新：2026-03-23*
