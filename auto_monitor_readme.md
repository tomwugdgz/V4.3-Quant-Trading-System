# MT5 自动监控系统 v1.0

**创建时间**: 2026-04-07  
**策略**: MP5 (四重确认 + 动态风控)  
**运行频率**: 每 15 分钟自动扫描

---

## 📋 功能清单

### ✅ 已实现功能

1. **自动市场扫描**
   - 每 15 分钟扫描 13 个品种（含日元交叉盘）
   - 四重确认：EMA + MACD + RSI + 趋势强度
   - 信号强度门槛：≥0.1% (标准), ≥0.05% (轻仓)

2. **持仓监控**
   - 实时检查现有持仓盈亏
   - 盈利达标自动平仓 (≥10 pips)
   - 信号反转自动平仓

3. **自动决策**
   - 盈利 → 自动平仓
   - 信号反转 → 自动平仓
   - 发现强信号 → 提示（可配置自动开仓）

4. **日志记录**
   - 每次扫描保存至 `monitor_log.json`
   - 包含账户状态、持仓、决策记录
   - 保留最近 100 条记录

---

## 🚀 快速开始

### 1. 启动监控

定时任务已创建，系统会自动运行。

**手动运行**（测试用）:
```bash
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
py -3 auto_monitor.py
```

### 2. 查看日志

**实时日志**:
```bash
# 查看最新扫描结果
cat monitor_log.json
```

**历史日志**: 每次扫描自动保存

### 3. 管理系统

**查看任务状态**:
```bash
schtasks /query /tn "MT5-AutoMonitor"
```

**手动运行一次**:
```bash
schtasks /run /tn "MT5-AutoMonitor"
```

**暂停任务**:
```bash
schtasks /change /tn "MT5-AutoMonitor" /disable
```

**恢复任务**:
```bash
schtasks /change /tn "MT5-AutoMonitor" /enable
```

**删除任务**:
```bash
schtasks /delete /tn "MT5-AutoMonitor" /f
```

---

## ⚙️ 配置参数

编辑 `auto_monitor.py` 修改配置：

```python
# MP5 策略参数
RISK_PERCENT = 0.005  # 0.5% 单笔风险
MIN_SIGNAL_STRENGTH = 0.1  # 最小信号强度 0.1%
PROFIT_THRESHOLD_PIPS = 10  # 盈利达到多少 pips 后平仓
STOP_LOSS_PIPS = 30  # 标准止损

# 监控品种
SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"
]
```

---

## 📊 决策逻辑

### 平仓条件

| 条件 | 阈值 | 动作 |
|------|------|------|
| **盈利达标** | ≥10 pips | 自动平仓 |
| **信号反转** | 反向信号 ≥0.1% | 自动平仓 |
| **止损触发** | -30 pips | MT5 自动执行 |
| **止盈触发** | +60 pips | MT5 自动执行 |

### 开仓条件（暂未启用）

| 条件 | 阈值 | 动作 |
|------|------|------|
| **强信号** | ≥0.1% | 提示，可手动确认 |
| **超强信号** | ≥0.2% | 可配置自动开仓 |
| **持仓<3 单** | 有可用风险空间 | 允许开新仓 |

---

## 🔍 日志格式

```json
{
  "timestamp": "2026-04-07T08:23:36",
  "account_balance": 10127.86,
  "positions_count": 2,
  "best_signal": null,
  "best_strength": 0,
  "decisions": [],
  "closed_count": 0
}
```

---

## 📝 当前持仓（示例）

| 品种 | 方向 | 仓位 | 入场价 | 止损 | 止盈 | 状态 |
|------|------|------|--------|------|------|------|
| AUDUSD | SELL | 0.08 | 0.69124 | 0.69425 | 0.68525 | 监控中 |
| USDJPY | BUY | 0.10 | 159.742 | 159.442 | 160.342 | 监控中 |

---

## ⚠️ 注意事项

### 安全提示

1. **首次使用建议观察 1-2 天**，确认系统运行正常
2. **定期检查日志**，确保决策符合预期
3. **周末休市时暂停监控**（周六 05:00 - 周一 06:00）

### 风险控制

- ✅ 总风险敞口 ≤3%
- ✅ 单笔风险 ≤0.5%
- ✅ 最大持仓 ≤3 单
- ✅ 止损自动执行（MT5 层面）

### 性能优化

- 扫描频率：15 分钟（可调整）
- 每次扫描耗时：约 1-2 秒
- 日志文件大小：约 10-20KB/天

---

## 🛠️ 故障排查

### 问题 1: 任务未运行

**检查**:
```bash
schtasks /query /tn "MT5-AutoMonitor"
```

**解决**:
```bash
# 手动运行一次
schtasks /run /tn "MT5-AutoMonitor"

# 查看日志
cat monitor_log.json
```

### 问题 2: MT5 连接失败

**检查**:
- MT5 软件是否运行
- 账户是否登录
- 网络连接是否正常

**解决**:
```bash
# 测试 MT5 连接
py -3 check_market_status.py
```

### 问题 3: 无扫描结果

**可能原因**:
- 周末休市
- 市场波动率过低
- MT5 数据延迟

**解决**: 等待市场活跃时段（欧盘 15:00+, 美盘 20:00+）

---

## 📞 支持

**日志文件**: `monitor_log.json`  
**脚本位置**: `auto_monitor.py`  
**安装脚本**: `install_monitor.bat`

---

**旺财 🎯**: 自动监控系统已就绪！每 15 分钟自动扫描，盈利达标自动平仓。你可以完全放心交给系统！

**最后更新**: 2026-04-07 08:38
