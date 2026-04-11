# Python 3.12 + 数据库升级方案

## 升级目标

1. **Python 3.7 → Python 3.12**
2. **解决 UTF-8 编码问题**
3. **增强数据库支持**
4. **保留所有交易脚本**

---

## 安装步骤

### 1. 安装 Python 3.12
```powershell
# 下载完成後安装
Start-Process "$env:TEMP\python-3.12.exe" -Wait -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1"
```

### 2. 安装必要库
```bash
pip install pandas numpy matplotlib plotly
pip install ta-lib backtrader
pip install sqlalchemy pymysql
pip install MetaTrader5
```

### 3. 数据库支持

#### SQLite3 (内置)
```python
import sqlite3
# 无需安装，Python 内置
```

#### MySQL 支持
```bash
pip install pymysql sqlalchemy
```

#### PostgreSQL 支持
```bash
pip install psycopg2-binary sqlalchemy
```

---

## 数据库架构设计

### 交易记录数据库 (trading.db)

```sql
-- 账户信息表
CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    login VARCHAR(20),
    server VARCHAR(50),
    balance DECIMAL(15,2),
    equity DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 持仓记录表
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    symbol VARCHAR(20),
    type VARCHAR(10),  -- BUY/SELL
    volume DECIMAL(10,2),
    entry_price DECIMAL(15,5),
    sl DECIMAL(15,5),
    tp DECIMAL(15,5),
    profit DECIMAL(15,2),
    open_time TIMESTAMP,
    close_time TIMESTAMP,
    status VARCHAR(20),  -- OPEN/CLOSED
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- 交易信号表
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20),
    direction VARCHAR(10),
    strength DECIMAL(10,5),
    timeframe VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- K 线分析记录表
CREATE TABLE kline_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20),
    timeframe VARCHAR(10),
    trend VARCHAR(50),
    rsi DECIMAL(10,2),
    macd_status VARCHAR(20),
    support DECIMAL(15,5),
    resistance DECIMAL(15,5),
    pattern VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日盈亏统计表
CREATE TABLE daily_stats (
    date DATE PRIMARY KEY,
    opening_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    total_profit DECIMAL(15,2),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate DECIMAL(5,2),
    max_drawdown DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Python 3.12 优势

1. **UTF-8 默认编码** - 解决中文乱码
2. **性能提升 5-10%** - 更快执行
3. **更好的错误提示** - 调试更容易
4. **最新库支持** - 兼容最新 pandas/numpy

---

## 迁移计划

### 第 1 步：安装 Python 3.12 ✅
### 第 2 步：安装必要库 ⏳
### 第 3 步：创建数据库 ⏳
### 第 4 步：测试交易脚本 ⏳
### 第 5 步：验证平仓功能 ⏳

---

**预计完成时间**: 10-15 分钟
