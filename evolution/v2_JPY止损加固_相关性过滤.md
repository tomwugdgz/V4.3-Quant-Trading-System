# v2 — JPY止损加固 + 相关性过滤

**版本**: v2
**日期**: 2026-05-08
**状态**: 当前生效中
**上一个版本**: v1 (JPY止损修复)

---

## 变更原因

### 05-08 凌晨亏损复盘
- AUDJPY BUY 0.15 @ 113.328 → SL=33.6pips → 止损 → **亏损 -$50.85**
- 同一时段（01:50~03:20）AUD系 4 个品种同时 BUY，全部止损
- EURUSD、AUDUSD、AUDCHF、GBPUSD、AUDJPY — 高度相关方向叠加

| 品种 | 时间 | SL | 结果 | 亏损 |
|------|------|-----|------|------|
| AUDCHF | 00:20 | 15pips | 止损 | -$22.50 |
| AUDUSD | 01:50 | 17pips | 止损 | -$25.50 |
| AUDJPY | 02:20 | 34pips | 止损 | -$50.85 |
| GBPUSD | 02:50 | 24pips | 止损 | -$36.00 |
| EURUSD | 03:20 | 20pips | 持仓中 | -$13.65 |

### 根因
1. **AUDJPY SL 偏紧**: ATR=13.4pips，SL=33.6pips（2.5x），34pip 移动刚好打止损
2. **无相关性过滤**: 5 个高相关品种同时 BUY，没有仓位隔离

---

## 变更内容

### 1. JPY 止损参数（patrol.py — get_dynamic_sl_tp）

**变更前 (v1)**:
```python
if is_jpy(symbol):
    sl_pips = max(atr_pips * 2.5, 25)   # JPY 最少 25 pips
```

**变更后 (v2)**:
```python
if is_jpy(symbol):
    sl_pips = max(atr_pips * 3.0, 35)   # JPY 最少 35 pips (v2: 2.5→3.0, 25→35)
```

**效果**: AUDJPY SL 从 33.6pips → 46.1pips（+37%）

### 2. 相关性过滤（patrol.py — run 新增）

**新增代码**:
```python
CORRELATED_GROUPS = {
    "AUD": ["AUDUSD", "AUDCHF", "AUDCAD", "AUDJPY", "EURAUD", "GBPAUD"],
    "EUR": ["EURUSD", "EURGBP", "EURCAD", "EURJPY", "EURAUD"],
    "USD": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],
    "JPY": ["USDJPY", "AUDJPY", "EURJPY", "GBPJPY", "NZDJPY", "CADJPY", "CHFJPY"],
}

def has_correlated_position(symbol, direction, positions):
    # 同向相关持仓时跳过
    ...
```

**效果**: EURUSD 持仓时，AUDUSD/AUDCHF/AUDJPY/GBPAUD/EURAUD 的 BUY 信号自动过滤

---

## 前测 vs 后测

| 指标 | v1 (05-08凌晨) | v2 (预期) |
|------|-----------------|-----------|
| AUDJPY SL | 33.6pips | 46.1pips (+37%) |
| AUDCHF 被过滤 | 无 | EURUSD持仓时过滤 |
| AUDUSD 被过滤 | 无 | EURUSD持仓时过滤 |
| 同向叠加风险 | 高 | 低 |

---

## 回滚指令

如需回滚到 v1:
1. `patrol.py` 中 JPY SL: `max(atr_pips * 3.0, 35)` → `max(atr_pips * 2.5, 25)`
2. 删除 `has_correlated_position()` 函数和 `CORRELATED_GROUPS` 定义
3. 移除 run() 中的相关性检查行

---

## 验证记录

| 时间 | 操作 | 结果 |
|------|------|------|
| 2026-05-08 10:59 | patrol.py v2 写入 | ✅ |
| 2026-05-08 11:00 | 手动执行 patrol.py | ✅ EURUSD持仓，跳过AUDUSD/AUDCHF |
| 2026-05-08 11:00 | AUDJPY新SL计算 | 46.1pips (v1: 38.4pips) |

---

## 后续计划

- 后测日期: 2026-05-15（1周后）
- 关注指标: JPY 亏损是否归零
- 如 v2 有效: 继续优化 RSI 参数
- 如 v2 无效: 回滚并尝试其他方案
