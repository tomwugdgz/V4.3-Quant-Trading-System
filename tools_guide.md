# MT5 交易工具调用指南

**创建日期**: 2026-03-27  
**最后更新**: 2026-03-27 23:00  
**Python 环境**: `C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe`  
**工作目录**: `C:\Users\DELL\.openclaw-autoclaw\workspace\trading`

---

## 🚀 快速调用模板

### 基础命令格式
```bash
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe <脚本名>.py [参数]
```

### 常用路径
- **工作目录**: `C:\Users\DELL\.openclaw-autoclaw\workspace\trading`
- **Python**: `C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe`
- **MT5 工具**: `trading\mt5_tools\`

---

## 📊 账户查询类

### 1. 查询账户余额和持仓
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe check_account.py
```

**输出**:
- 账户余额
- 净值
- 杠杆
- 当前持仓及盈亏

**使用场景**: 每日汇报、开仓前检查

---

### 2. 简单账户检查
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe check_account_simple.py
```

**输出**: 简化版账户信息

---

### 3. 账户状态详细检查
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe check_account_status.py
```

**输出**: 详细账户状态 + 风险评估

---

### 4. 生成每日汇报
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe daily_report.py
```

**输出**: 格式化每日账户汇报

---

## 📈 市场扫描类

### 1. 扫描市场机会
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe find_opportunity.py
```

**输出**:
- 所有品种信号强度
- 最佳交易机会推荐
- 建议仓位大小

**使用场景**: 开仓前扫描

---

### 2. 市场扫描 (MT5 工具)
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe market_scan.py
```

**输出**: 详细市场扫描报告

---

### 3. 外汇市场分析
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe analyze_fx.py
```

**输出**: 外汇品种技术分析

---

### 4. 加密货币分析
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe analyze_crypto.py
```

**输出**: BTC/ETH 等加密货币分析

---

### 5. K 线分析 (开仓前必做)
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe advanced_kline_analysis.py
```

**输出**:
- K 线形态识别
- 支撑位/阻力位
- 多重时间框架分析
- 技术指标

**使用场景**: 开仓前强制检查

---

## 💼 交易执行类

### 1. 统一交易工具 (推荐)
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe mt5_tool.py <命令> [参数]
```

**支持命令**:
```
buy <品种> <手数> [止损] [止盈]   - 开多单
sell <品种> <手数> [止损] [止盈]  - 开空单
close all                         - 平所有仓
close <品种>                      - 平指定品种
scan                              - 市场扫描
opp                               - 寻找机会
help                              - 帮助
```

**示例**:
```bash
# 开多单
mt5_tool.py buy EURUSD 0.1 1.0850 1.0910

# 开空单
mt5_tool.py sell USDCHF 0.17 0.7994 0.7904

# 平所有仓
mt5_tool.py close all

# 平指定品种
mt5_tool.py close EURUSD
```

---

### 2. 开仓 (单独脚本)
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe open_position.py <品种> <方向> <手数> <止损> <止盈>
```

---

### 3. 平仓 (单独脚本)
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe close_position.py <订单号>
```

---

### 4. 平所有仓位
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe close_all.py
```

---

### 5. 简单平仓
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading\mt5_tools
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe close_nzdusd_simple.py
```

---

## 📋 工作流模板

### 工作流 1: 开仓前检查流程

```bash
# Step 1: 检查账户状态
check_account.py

# Step 2: 扫描市场机会
find_opportunity.py

# Step 3: K 线分析 (必做)
mt5_tools\advanced_kline_analysis.py

# Step 4: 执行开仓
mt5_tools\mt5_tool.py sell USDCHF 0.17 0.7994 0.7904

# Step 5: 确认持仓
check_account.py
```

---

### 工作流 2: 每日汇报流程

```bash
# 每日 20:00 执行
daily_report.py
```

---

### 工作流 3: 信号监控流程

```bash
# 每 15 分钟执行
find_opportunity.py

# 检查信号反转
# 如反转 → 平仓
mt5_tools\mt5_tool.py close <品种>
```

---

### 工作流 4: 周末加密货币扫描

```bash
# 周末执行 (信号门槛>0.2%)
analyze_crypto.py
scan_all_crypto.py
```

---

## 🔧 其他工具

### 1. 持仓检查
```bash
check_positions.py
check_open_positions.py
get_current_positions.py
```

### 2. 历史数据
```bash
get_history.py
```

### 3. 交易报告
```bash
trade_report.py
position_report.py
```

### 4. 复盘生成
```bash
review_generator.py daily    # 每日复盘
review_generator.py weekly   # 每周复盘
review_generator.py monthly  # 每月复盘
```

### 5. 策略回测
```bash
mt5_tools\backtester.py
```

---

## 📝 自动化脚本示例

### 自动扫描 + 开仓
```bash
# scan_and_trade.bat
@echo off
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe find_opportunity.py
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe mt5_tools\advanced_kline_analysis.py
# 根据信号执行开仓
```

---

## 🎯 常用命令速查

| 功能 | 命令 |
|------|------|
| 查账户 | `check_account.py` |
| 扫市场 | `find_opportunity.py` |
| K 线分析 | `mt5_tools\advanced_kline_analysis.py` |
| 开多单 | `mt5_tool.py buy EURUSD 0.1` |
| 开空单 | `mt5_tool.py sell USDCHF 0.17` |
| 平所有 | `mt5_tool.py close all` |
| 每日汇报 | `daily_report.py` |
| 复盘 | `review_generator.py daily` |

---

## ⚠️ 注意事项

1. **Python 环境**: 必须使用 Python 3.12 (`C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe`)
2. **工作目录**: 大部分脚本需要在 `trading` 目录下运行
3. **MT5 连接**: 确保 MT5 客户端已登录
4. **风险检查**: 开仓前必须检查账户状态和风险
5. **记录日志**: 所有交易自动记录到 `trading\mt5_tools\output\`

---

## 📊 策略 PK 测试

### 6 模型测试脚本
```bash
# 每个模型独立测试
TF-01: SMA 交叉
TF-02: EMA 交叉
TF-03: MACD 趋势
TF-04: ADX 趋势
TF-05: 通道突破
TF-06: AMA 自适应

# 查看结果
trading\strategy\algo_pk_results.json
```

---

## 🎯 旺财推荐工作流

### 标准开仓流程 (每次必做)

```
1. check_account.py          → 检查账户状态
2. find_opportunity.py       → 扫描市场信号
3. advanced_kline_analysis.py → K 线分析确认
4. mt5_tool.py sell/buy      → 执行开仓
5. check_account.py          → 确认持仓
```

### 每日汇报流程

```
1. daily_report.py           → 生成汇报
2. 发送到飞书群
```

### 每周复盘流程

```
1. review_generator.py weekly → 生成周复盘
2. 更新策略 PK 结果
3. 发送汇报
```

---

**旺财 🎯**: 所有工具已记录！以后可以直接调用这些脚本，提高效率！

**创建人**: 旺财  
**日期**: 2026-03-27  
**位置**: `trading\TOOLS_GUIDE.md`
