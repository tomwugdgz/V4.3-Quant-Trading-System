# 故障排除指南 (Troubleshooting Guide)

**版本**: V4.3.0  
**创建时间**: 2026-04-11  
**最后更新**: 2026-04-11

---

## 一、MT5 连接问题

### 1.1 MT5 初始化失败

**错误信息**:
```
[ERROR] MT5 初始化失败
```

**可能原因**:
1. MT5 未运行
2. MT5 未登录账户
3. 路径配置错误
4. 权限问题

**解决方案**:

**检查 MT5 是否运行**:
```python
import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 未运行或未登录")
    # 手动启动 MT5
```

**检查账户登录**:
```python
info = mt5.symbol_info_tick("EURUSD")
if info is None:
    print("MT5 未登录或数据不可用")
```

**修复步骤**:
1. 启动 MetaTrader 5
2. 登录交易账户
3. 确保数据连接正常
4. 重新运行脚本

---

### 1.2 数据获取失败

**错误信息**:
```
[ERROR] 获取数据失败
```

**可能原因**:
1. 品种代码错误
2. 时间周期错误
3. 市场休市
4. 网络问题

**解决方案**:

**检查品种代码**:
```python
# 正确代码
symbols = ["EURUSD", "GBPUSD", "USDJPY"]

# 错误代码（注意大小写）
symbols = ["eurusd", "gbpusd"]  # ❌
```

**检查时间周期**:
```python
# 正确周期
timeframe = mt5.TIMEFRAME_H1
timeframe = mt5.TIMEFRAME_H4
timeframe = mt5.TIMEFRAME_D1

# 错误周期
timeframe = "H1"  # ❌ 应该是 mt5.TIMEFRAME_H1
```

**检查市场状态**:
```python
# 汇市休市时间：周六 05:00 - 周一 06:00 (北京时间)
# 加密货币 24/7 交易
```

---

## 二、因子计算问题

### 2.1 因子评分为 NaN

**错误信息**:
```
因子评分：nan
```

**可能原因**:
1. 数据量不足
2. 计算周期超过数据长度
3. 除零错误

**解决方案**:

**检查数据量**:
```python
if len(df) < 100:
    print(f"数据量不足：{len(df)}，需要至少 100 根 K 线")
```

**检查计算周期**:
```python
# EMA 需要至少 ema_period 根 K 线
if len(df) < ema_period_long:
    return 0.0  # 返回默认值
```

**添加异常处理**:
```python
try:
    result = factor.calculate_score(df)
except ZeroDivisionError:
    print("除零错误，返回默认值")
    result = {'score': 50, 'signal': 'NEUTRAL'}
```

---

### 2.2 因子 IC 为 NaN

**错误信息**:
```
momentum: IC=nan (数据不足)
```

**可能原因**:
1. 样本量太少
2. 未来收益计算错误
3. 数据质量问题

**解决方案**:

**增加样本量**:
```python
# 修改 factor_ic_analysis.py
self.periods = 500  # 从 100 增加到 500
```

**检查未来收益计算**:
```python
# 确保 forward return 计算正确
forward_returns = close.shift(-10) / close - 1

# 检查 NaN
print(f"NaN 数量：{forward_returns.isna().sum()}")
```

---

## 三、风控问题

### 3.1 风控总是拒绝

**错误信息**:
```
风控不通过：保证金水平不足
```

**可能原因**:
1. 保证金水平确实不足
2. 参数设置过严
3. 账户信息获取错误

**解决方案**:

**检查保证金水平**:
```python
account = mt5.account_info()
print(f"保证金水平：{account.margin_level}%")

# 要求>200%
if account.margin_level < 200:
    print("保证金水平不足，需要入金或减仓")
```

**调整风控参数**:
```python
# config/risk_params.json
{
  "account": {
    "min_margin_level": 150  // 从 200 降低到 150
  }
}
```

---

### 3.2 仓位计算错误

**错误信息**:
```
手数计算错误：0.00
```

**可能原因**:
1. 止损距离为 0
2. 点值计算错误
3. 风险金额过小

**解决方案**:

**检查止损距离**:
```python
stop_distance = abs(entry_price - stop_loss)

if stop_distance == 0:
    print("止损距离为 0，请设置合理止损")
    stop_distance = 0.0050  # 默认 50 点
```

**检查点值**:
```python
# 直盘点值
point_value = 10  # EURUSD, GBPUSD 等

# 横盘点值
point_value = 10 / exchange_rate  # USDJPY 等
```

---

## 四、回测问题

### 4.1 Walk-Forward 回测失败

**错误信息**:
```
Walk-Forward 回测失败：数据不足
```

**可能原因**:
1. 历史数据不足
2. 滚动窗口设置过大
3. 品种不支持

**解决方案**:

**检查数据量**:
```python
# 需要至少 train_months + test_months 的数据
required_months = 6 + 1  # 7 个月
required_bars = required_months * 30 * 24  # 小时线

if len(df) < required_bars:
    print(f"数据不足：需要{required_bars}根 K 线")
```

**调整窗口大小**:
```python
# config/walk_forward_config.json
{
  "train_months": 3,  // 从 6 降低到 3
  "test_months": 1
}
```

---

### 4.2 参数优化失败

**错误信息**:
```
参数优化失败：无有效参数组合
```

**可能原因**:
1. 参数范围过小
2. 回测逻辑错误
3. 市场条件变化

**解决方案**:

**扩大参数范围**:
```python
# config/walk_forward_config.json
{
  "parameters": {
    "ema_fast": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    "ema_slow": [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
  }
}
```

**检查回测逻辑**:
```python
# 确保回测函数返回正确格式
result = {
    'sharpe': 1.5,
    'total_return': 0.15,
    'max_drawdown': -0.10
}
```

---

## 五、复盘问题

### 5.1 复盘报告为空

**错误信息**:
```
每日复盘报告
当日无交易记录
```

**可能原因**:
1. 确实无交易
2. 数据库连接错误
3. 日期范围错误

**解决方案**:

**检查数据库**:
```python
import sqlite3

conn = sqlite3.connect("trading.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM orders")
count = cursor.fetchone()[0]
print(f"数据库中有{count}条交易记录")
```

**检查日期范围**:
```python
# 确保日期格式正确
date = "2026-04-11"  # YYYY-MM-DD

# 查询当日交易
query = f"""
SELECT * FROM orders 
WHERE DATE(created_at) = '{date}'
"""
```

---

### 5.2 归因分析错误

**错误信息**:
```
归因分析失败：无交易记录
```

**可能原因**:
1. 数据库表不存在
2. 字段名称错误
3. 时间范围无数据

**解决方案**:

**初始化数据库**:
```sql
-- 创建交易记录表
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    type TEXT,
    volume REAL,
    profit REAL,
    created_at DATETIME
);
```

**检查字段名称**:
```python
# 确保字段名称匹配
required_fields = ['symbol', 'type', 'profit', 'created_at']

for field in required_fields:
    if field not in df.columns:
        print(f"缺少字段：{field}")
```

---

## 六、配置问题

### 6.1 配置文件加载失败

**错误信息**:
```
[WARNING] 配置文件不存在：config/regime_config.json
```

**可能原因**:
1. 文件路径错误
2. 文件未创建
3. 权限问题

**解决方案**:

**检查文件路径**:
```python
import os

config_path = "config/regime_config.json"
print(f"配置文件路径：{os.path.abspath(config_path)}")
print(f"文件是否存在：{os.path.exists(config_path)}")
```

**创建默认配置**:
```python
import json

default_config = {
    "trend": {
        "ADX_threshold": 25,
        "ema_short": 10,
        "ema_long": 20
    }
}

with open("config/regime_config.json", 'w') as f:
    json.dump(default_config, f, indent=2)
```

---

### 6.2 配置参数错误

**错误信息**:
```
配置类型错误：trend 应为 dict
```

**可能原因**:
1. JSON 格式错误
2. 参数类型错误
3. 缺少必需参数

**解决方案**:

**验证 JSON 格式**:
```python
import json

try:
    with open("config/regime_config.json", 'r') as f:
        config = json.load(f)
    print("JSON 格式正确")
except json.JSONDecodeError as e:
    print(f"JSON 格式错误：{e}")
```

**检查必需参数**:
```python
required_keys = ['trend', 'volatility', 'ranging', 'dynamic_thresholds']

for key in required_keys:
    if key not in config:
        print(f"缺少必需参数：{key}")
```

---

## 七、编码问题

### 7.1 Unicode 编码错误

**错误信息**:
```
UnicodeEncodeError: 'gbk' codec can't encode character
```

**可能原因**:
1. Windows 控制台编码问题
2. 中文字符问题
3. emoji 字符问题

**解决方案**:

**设置控制台编码**:
```python
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

**移除 emoji**:
```python
# 使用纯文本代替 emoji
status = "PASS" if passed else "FAIL"  # ✅ 改为 PASS/FAIL
```

**指定文件编码**:
```python
# 读写文件时指定编码
with open("file.md", 'w', encoding='utf-8') as f:
    f.write(content)
```

---

## 八、性能问题

### 8.1 扫描速度过慢

**错误信息**:
```
扫描耗时：120 秒（标准<30 秒）
```

**可能原因**:
1. 数据获取慢
2. 因子计算复杂
3. 网络延迟

**解决方案**:

**优化数据获取**:
```python
# 批量获取数据
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)

# 而不是循环获取
for i in range(100):
    rate = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, i, 1)
```

**缓存计算结果**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def calculate_factor(symbol, timeframe):
    # 因子计算
    pass
```

---

### 8.2 内存占用过高

**错误信息**:
```
内存占用：800MB（标准<500MB）
```

**可能原因**:
1. 数据加载过多
2. 未释放资源
3. 缓存过大

**解决方案**:

**限制数据量**:
```python
# 只加载必要的数据
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)  # 100 根
# 而不是
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 10000)  # 10000 根
```

**释放资源**:
```python
# 及时释放 DataFrame
del df
import gc
gc.collect()
```

---

## 九、日志和调试

### 9.1 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("V4.3")
logger.debug("调试信息")
logger.info("正常信息")
logger.warning("警告信息")
logger.error("错误信息")
```

---

### 9.2 调试技巧

**打印关键变量**:
```python
def calculate_score(self, df):
    print(f"数据量：{len(df)}")
    print(f"收盘价范围：{df['close'].min():.5f} - {df['close'].max():.5f}")
    
    # 计算过程
    score = ...
    
    print(f"计算结果：{score}")
    return score
```

**使用断点**:
```python
import pdb

def complex_calculation(self, df):
    # ...
    pdb.set_trace()  # 设置断点
    # 在断点处可以检查变量、单步执行
```

---

## 十、获取帮助

### 10.1 查看文档

```bash
# 架构文档
cat docs/V4.3_ARCHITECTURE.md

# API 参考
cat docs/API_REFERENCE.md

# 故障排除
cat docs/TROUBLESHOOTING.md
```

---

### 10.2 提交问题

**提供以下信息**:
1. 错误信息（完整截图）
2. 复现步骤
3. 环境信息（Python 版本、MT5 版本）
4. 日志文件

---

**V4.3 Development Team**  
**2026-04-11**  
**遇到问题，先查文档，再看日志**
