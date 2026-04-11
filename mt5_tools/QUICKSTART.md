# MT5 工具库 - 快速参考卡

## 🚀 一行命令

```bash
# 查询余额
python mt5_tool.py balance

# 开多 0.01 手 EURUSD
python mt5_tool.py buy EURUSD 0.01

# 开空 0.1 手黄金，止损 2000，止盈 1950
python mt5_tool.py sell XAUUSD 0.1 2000 1950

# 全部平仓
python mt5_tool.py close all

# 扫描市场机会
python mt5_tool.py opp
```

## 📁 文件夹位置

```
trading/mt5_tools/          # 工具库目录
├── mt5_tool.py            # 主入口（命令行调用）
├── base.py                # 基础模块
├── account_check.py       # 账户查询
├── open_position.py       # 开仓
├── close_position.py      # 平仓
├── market_scan.py         # 市场扫描
├── config.json            # 配置
└── output/                # 输出文件
```

## 🐍 Python 调用

```python
from mt5_tools import buy, sell, close_all_positions, check_balance

# 查询
check_balance()

# 交易
buy("EURUSD", 0.01)
sell("XAUUSD", 0.1, sl=2000, tp=1950)

# 平仓
close_all_positions()
```

## 📊 支持品种

- **外汇**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- **加密货币**: BTCUSD, ETHUSD
- **贵金属**: XAUUSD (黄金), XAGUSD (白银)
- **指数**: US30, NAS100, SPX500

## ⚙️ 默认配置

- 手数：0.01
- 止损：50 点
- 止盈：100 点
- 滑点：20 点
- 风险：1%/笔

---
**详细文档**: `trading/mt5_tools/README.md`
