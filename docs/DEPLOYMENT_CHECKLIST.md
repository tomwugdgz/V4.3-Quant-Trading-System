# 部署检查清单 (Deployment Checklist)

**版本**: V4.3.0  
**创建时间**: 2026-04-11  
**最后更新**: 2026-04-11

---

## 一、部署前准备

### 1.1 环境检查

- [ ] Python 3.8+ 已安装
- [ ] MetaTrader5 已安装并登录
- [ ] 依赖包已安装 (`pip install -r requirements.txt`)
- [ ] 网络连接正常
- [ ] 磁盘空间充足 (>1GB)

**检查命令**:
```bash
python --version
pip list | grep MetaTrader5
pip list | grep pandas
pip list | grep numpy
```

---

### 1.2 配置文件

- [ ] `config/regime_config.json` 已配置
- [ ] `config/factor_weights.json` 已配置
- [ ] `config/risk_params.json` 已配置
- [ ] `config/walk_forward_config.json` 已配置

**配置验证**:
```bash
cd trading/v4_3
python config_loader.py
```

---

### 1.3 数据库初始化

- [ ] 创建 `trading.db` 数据库
- [ ] 创建 `orders` 表
- [ ] 创建 `positions` 表
- [ ] 创建 `account_log` 表

**初始化脚本**:
```sql
-- 创建交易记录表
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    type TEXT,
    volume REAL,
    entry_price REAL,
    stop_loss REAL,
    take_profit REAL,
    exit_price REAL,
    profit REAL,
    strategy TEXT,
    regime TEXT,
    factor_score REAL,
    created_at DATETIME,
    closed_at DATETIME
);

-- 创建持仓表
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    type TEXT,
    volume REAL,
    entry_price REAL,
    current_price REAL,
    stop_loss REAL,
    take_profit REAL,
    unrealized_pnl REAL,
    created_at DATETIME
);

-- 创建账户日志表
CREATE TABLE IF NOT EXISTS account_log (
    id INTEGER PRIMARY KEY,
    balance REAL,
    equity REAL,
    margin_level REAL,
    leverage REAL,
    timestamp DATETIME
);
```

---

## 二、模块测试

### 2.1 单元测试

- [ ] 因子库测试通过
- [ ] Market Regime 测试通过
- [ ] Factor Score 测试通过
- [ ] Risk Agent 测试通过
- [ ] Review Agent 测试通过

**运行测试**:
```bash
cd trading/tests
pytest test_factors.py -v
pytest test_review.py -v
```

---

### 2.2 集成测试

- [ ] 系统完整性测试通过
- [ ] 市场扫描测试通过
- [ ] 信号生成测试通过
- [ ] 风控检查测试通过

**运行测试**:
```bash
cd trading/tests
python test_v43_system.py
```

---

### 2.3 模拟交易测试

- [ ] MT5 连接正常
- [ ] 数据获取正常
- [ ] 订单执行正常
- [ ] 止损止盈设置正常

**运行测试**:
```bash
cd trading/v4_3
python main_v43.py --test
```

---

## 三、验收标准

### 3.1 功能验收

| 功能 | 标准 | 测试结果 |
|------|------|----------|
| 市场扫描 | 7 个品种，<30 秒 | ⬜ |
| 因子计算 | 4 大因子，评分正常 | ⬜ |
| 信号生成 | 阈值判断准确 | ⬜ |
| 风控检查 | 规则执行正确 | ⬜ |
| 订单执行 | 成功执行，无错误 | ⬜ |
| 复盘报告 | 每日自动生成 | ⬜ |

---

### 3.2 性能验收

| 指标 | 标准 | 测试结果 |
|------|------|----------|
| 扫描速度 | <30 秒/7 品种 | ⬜ |
| 内存占用 | <500MB | ⬜ |
| CPU 占用 | <30% | ⬜ |
| 响应时间 | <5 秒 | ⬜ |

---

### 3.3 稳定性验收

| 测试 | 标准 | 测试结果 |
|------|------|----------|
| 连续运行 24 小时 | 无崩溃 | ⬜ |
| MT5 断线重连 | 自动重连成功 | ⬜ |
| 异常处理 | 捕获并记录 | ⬜ |
| 日志记录 | 完整准确 | ⬜ |

---

## 四、Walk-Forward 验证

### 4.1 回测设置

- [ ] 训练集：6 个月数据
- [ ] 测试集：1 个月数据
- [ ] 滚动次数：≥3 次
- [ ] 参数范围：已定义

---

### 4.2 验收指标

| 指标 | 标准 | 测试结果 |
|------|------|----------|
| 训练集夏普 | >1.5 | ⬜ |
| 测试集夏普 | >1.0 | ⬜ |
| 最大回撤 | <15% | ⬜ |
| 胜率 | >50% | ⬜ |
| 盈亏比 | >1.5 | ⬜ |
| 参数敏感性 | <20% | ⬜ |

---

### 4.3 运行 Walk-Forward

```bash
cd trading/v4_3
python walk_forward.py --symbol EURUSD --start 2025-01-01 --end 2026-04-01
```

---

## 五、模拟盘部署

### 5.1 模拟盘设置

- [ ] 模拟账户已开通
- [ ] 初始资金：$10,000
- [ ] 杠杆：1:5
- [ ] 品种：7 个主要外汇

---

### 5.2 监控设置

- [ ] 每日 17:00 自动检查
- [ ] 飞书通知已配置
- [ ] 异常报警已设置
- [ ] 日志记录已开启

---

### 5.3 模拟盘运行周期

**周期**: 2 周 (2026-04-15 至 2026-04-29)

**监控指标**:
- 每日交易次数
- 胜率
- 盈亏比
- 最大回撤
- 风控触发记录

---

### 5.4 模拟盘验收

| 指标 | 标准 | 测试结果 |
|------|------|----------|
| 交易次数 | ≥10 单 | ⬜ |
| 胜率 | >50% | ⬜ |
| 盈亏比 | >1.5 | ⬜ |
| 最大回撤 | <5% | ⬜ |
| 风控触发 | 0 次违规 | ⬜ |
| 系统稳定性 | 无崩溃 | ⬜ |

---

## 六、实盘部署

### 6.1 实盘前检查

- [ ] 模拟盘验收通过
- [ ] Go/No-Go 决策通过
- [ ] 实盘账户已开通
- [ ] 初始资金到位
- [ ] 风控参数已确认

---

### 6.2 实盘参数

```json
{
  "account": {
    "initial_capital": 10000,
    "leverage": 5,
    "max_daily_loss": 0.03,
    "max_total_drawdown": 0.10
  },
  "position": {
    "max_positions": 3,
    "risk_per_trade": 0.005
  },
  "execution": {
    "auto_execute": true,
    "signal_threshold": 0.001
  }
}
```

---

### 6.3 实盘监控

**监控频率**:
- 每 60 分钟：市场扫描
- 每日 17:00: 账户检查
- 每日 20:00: 复盘报告
- 每周日：周度总结

**监控指标**:
- 账户余额
- 持仓状态
- 保证金水平
- 当日盈亏
- 风控状态

---

### 6.4 应急预案

**MT5 断线**:
```python
# 自动重连
max_retries = 3
retry_delay = 5  # 秒

for i in range(max_retries):
    if mt5.initialize():
        print("重连成功")
        break
    time.sleep(retry_delay)
else:
    # 重连失败，发送报警
    send_alert("MT5 重连失败")
```

**异常亏损**:
```python
# 触及单日亏损红线
if daily_loss >= 0.03 * equity:
    # 停止交易
    auto_execute = False
    # 平仓所有持仓
    close_all_positions()
    # 发送报警
    send_alert("触及单日亏损红线，已停止交易")
```

---

## 七、文档清单

- [ ] V4.3_ARCHITECTURE.md ✅
- [ ] FACTOR_LIBRARY.md ✅
- [ ] RISK_AGENT_MANUAL.md ✅
- [ ] REVIEW_AGENT_GUIDE.md ✅
- [ ] WALK_FORWARD_TUTORIAL.md ⬜
- [ ] DEPLOYMENT_CHECKLIST.md ✅
- [ ] API_REFERENCE.md ⬜
- [ ] TROUBLESHOOTING.md ⬜

---

## 八、部署流程

### 8.1 部署步骤

1. **环境准备** (Day 1)
   - 安装 Python 和依赖
   - 配置 MT5
   - 初始化数据库

2. **模块测试** (Day 2-3)
   - 单元测试
   - 集成测试
   - 模拟交易测试

3. **Walk-Forward 验证** (Day 4-7)
   - 滚动回测
   - 参数优化
   - 验收评估

4. **模拟盘运行** (Day 8-21)
   - 2 周模拟盘
   - 每日监控
   - 数据收集

5. **实盘部署** (Day 22+)
   - Go/No-Go 决策
   - 实盘参数配置
   - 正式上线

---

### 8.2 回滚计划

**如果实盘出现问题**:
```
1. 立即停止自动交易
2. 平仓所有持仓
3. 切换到模拟盘模式
4. 分析问题原因
5. 修复后重新测试
6. 再次评估实盘
```

---

## 九、总结

**部署前必须完成**:
1. ✅ 环境检查和配置
2. ✅ 模块测试通过
3. ✅ Walk-Forward 验证
4. ✅ 模拟盘验收
5. ✅ Go/No-Go 决策

**部署后持续监控**:
1. 每日交易数据
2. 风控指标
3. 系统稳定性
4. 异常事件

---

**V4.3 Development Team**  
**2026-04-11**  
**充分准备，稳健部署**
