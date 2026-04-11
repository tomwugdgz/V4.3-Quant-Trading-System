# MT5 工具库

MetaTrader 5 自动化交易工具集，提供快速命令行接口和 Python 模块调用。

## 📁 目录结构

```
mt5_tools/
├── base.py              # 基础模块（初始化、通用函数）
├── account_check.py     # 账户查询工具
├── open_position.py     # 开仓工具
├── close_position.py    # 平仓工具
├── market_scan.py       # 市场扫描工具
├── mt5_tool.py          # 统一命令行接口
├── config.json          # 配置文件（自动生成）
├── output/              # 输出目录（自动创建）
└── README.md            # 本文档
```

## 🚀 快速开始

### 命令行调用（推荐）

```bash
# 查看帮助
python mt5_tool.py help

# 查询账户余额
python mt5_tool.py balance

# 开仓交易
python mt5_tool.py buy EURUSD 0.01
python mt5_tool.py sell XAUUSD 0.1 2000 1950  # 带止损止盈

# 平仓
python mt5_tool.py close all        # 平掉所有持仓
python mt5_tool.py close EURUSD     # 只平 EURUSD

# 市场扫描
python mt5_tool.py scan             # 扫描所有市场
python mt5_tool.py scan forex       # 只扫描外汇
python mt5_tool.py opp              # 寻找交易机会

# 查看状态
python mt5_tool.py status
```

### Python 模块调用

```python
# 导入基础模块
from mt5_tools.base import initialize, get_account_info, get_positions

# 查询账户
from mt5_tools.account_check import check_balance
check_balance()

# 开仓
from mt5_tools.open_position import buy, sell
buy("EURUSD", 0.01)  # 开 0.01 手多单
sell("XAUUSD", 0.1, sl=2000, tp=1950)  # 带止损止盈

# 平仓
from mt5_tools.close_position import close_all_positions, close_by_symbol
close_all_positions()  # 全部平仓
close_by_symbol("EURUSD")  # 只平 EURUSD

# 市场扫描
from mt5_tools.market_scan import scan_market, find_opportunities
scan_market(["forex", "crypto"])  # 扫描外汇和加密货币
find_opportunities(min_change=1.5)  # 寻找涨跌幅>1.5% 的机会
```

## 📋 功能说明

### 1. 账户查询 (`account_check.py`)

- 账户余额、净值、可用资金
- 持仓盈亏统计
- 收益率计算
- 自动保存 JSON 报告

### 2. 开仓交易 (`open_position.py`)

- 市价单开多/开空
- 支持止损止盈
- 自动滑点保护（20 点）
- 订单结果记录

**参数说明：**
- `symbol`: 交易品种（如 "EURUSD", "XAUUSD", "BTCUSD"）
- `volume`: 手数（如 0.01, 0.1, 1.0）
- `sl`: 止损价格（0 表示无止损）
- `tp`: 止盈价格（0 表示无止盈）

### 3. 平仓交易 (`close_position.py`)

- 全部平仓
- 按品种平仓
- 盈亏统计
- 平仓记录保存

### 4. 市场扫描 (`market_scan.py`)

- 多品种同时扫描
- 趋势判断（MA 交叉）
- 涨跌幅计算
- 波动率分析
- 交易机会识别

**支持的品种组：**
- `forex`: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- `crypto`: BTCUSD, ETHUSD
- `metals`: XAUUSD, XAGUSD
- `indices`: US30, NAS100, SPX500

## ⚙️ 配置

### 默认配置

首次运行时会自动创建 `config.json`：

```json
{
  "default_volume": 0.01,
  "default_sl_points": 50,
  "default_tp_points": 100,
  "max_slippage": 20,
  "magic_number": 234000,
  "risk_per_trade": 0.01,
  "max_daily_loss": 0.03
}
```

### 风险管理参数

- `risk_per_trade`: 每笔交易风险（占账户百分比）
- `max_daily_loss`: 每日最大亏损（占账户百分比）
- `default_volume`: 默认手数
- `max_slippage`: 最大滑点（点）

## 📊 输出文件

所有操作会自动保存 JSON 报告到 `output/` 目录：

```
output/
├── account-20260321-150000.json    # 账户查询
├── order-EURUSD-BUY-20260321-150500.json  # 开仓记录
├── close-all-20260321-151000.json   # 平仓记录
└── market-scan-20260321-150000.json # 市场扫描
```

## 🔧 高级用法

### 自定义品种列表

编辑 `market_scan.py` 中的 `SYMBOLS` 字典：

```python
SYMBOLS = {
    "forex": ["EURUSD", "GBPUSD", "USDJPY"],
    "my_symbols": ["EURUSD", "XAUUSD", "BTCUSD"]  # 自定义组
}
```

然后扫描：
```bash
python mt5_tool.py scan my_symbols
```

### 批量开仓

```python
from mt5_tools.open_position import buy

# 一篮子开仓
symbols = ["EURUSD", "GBPUSD", "AUDUSD"]
for symbol in symbols:
    buy(symbol, 0.01)
```

### 条件平仓

```python
from mt5_tools.close_position import close_position
from mt5_tools.base import get_positions

positions = get_positions()
for pos in positions:
    if pos['total_profit'] > 100:  # 盈利超过$100 就平
        close_position(pos['symbol'], pos['type'], pos['volume'])
```

## ⚠️ 注意事项

1. **模拟盘测试**: 首次使用请在模拟账户测试
2. **风险控制**: 设置合理的止损，不要重仓交易
3. **网络连接**: 确保 MT5 终端已登录且网络正常
4. **交易时间**: 避免在非交易时间下单（周末、节假日）
5. **滑点风险**: 重大新闻期间滑点可能超过设置值

## 🛠️ 故障排除

### MT5 初始化失败

```python
# 检查 MT5 终端是否运行
# 确保使用正确的 Python 环境（已安装 MetaTrader5 包）
pip install MetaTrader5
```

### 品种不存在

```python
# 检查品种名称是否正确
# 在 MT5 终端中查看"市场报价"窗口中的准确名称
```

### 订单被拒绝

- 检查账户余额是否足够
- 检查品种是否允许交易
- 检查手数是否在最小/最大范围内
- 检查市场是否开盘

## 📚 扩展开发

### 添加新功能

1. 在 `mt5_tools/` 目录创建新的 `.py` 文件
2. 导入 `base.py` 中的工具函数
3. 在 `mt5_tool.py` 中添加命令映射

### 示例：添加订单历史查询

```python
# history.py
from base import initialize, shutdown
import MetaTrader5 as mt5

def get_history(days=7):
    initialize()
    history = mt5.history_deals_get(
        datetime.now().minus(days=days),
        datetime.now()
    )
    shutdown()
    return history
```

## 📝 更新日志

- **2026-03-21**: 初始版本
  - 账户查询
  - 开仓/平仓
  - 市场扫描
  - 命令行接口

---

**开发**: Tom / 旺财  
**用途**: 外汇量化交易自动化  
**版本**: 1.0.0
