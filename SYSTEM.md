# 旺财交易记忆与复盘系统

---

## ✅ 系统已就绪

**创建时间**: 2026-03-17
**状态**: 完整可用

---

## 📁 目录结构

```
trading/
├── README.md                  # 系统说明
├── review_generator.py        # 复盘生成器
│
├── memory/                    # 长期记忆
│   ├── profile.md            # 交易者画像
│   ├── goals.md              # 交易目标
│   └── rules.md              # 交易规则
│
├── reviews/                   # 复盘记录
│   ├── daily/                # 每日复盘
│   │   ├── template.md       # 模板
│   │   └── 2026-03-17.md     # 今日复盘 ✅
│   ├── weekly/               # 每周复盘
│   │   ├── template.md       # 模板
│   │   └── 2026-W12.md       # 本周复盘 ✅
│   └── monthly/              # 每月复盘
│       ├── template.md       # 模板
│       └── 2026-03.md        # 本月复盘 ✅
│
├── stats/                     # 统计数据
│   └── performance.md        # 绩效统计
│
├── strategies/                # 策略记录
│   └── (待创建)
│
└── lessons/                   # 经验教训
    └── lessons.md            # 教训清单
```

---

## 🎯 核心功能

### 1. 长期记忆 (memory/)

**profile.md** - 你的交易者画像
- 交易风格
- 风险偏好
- 优势劣势
- 心理特征

**goals.md** - 交易目标
- 10 年终极目标：¥10 万 → ¥1500 万
- 阶段性目标 (年/季/月)
- 目标追踪

**rules.md** - 交易规则
- 铁律 (不可违背)
- 交易前检查清单
- 持仓管理规则
- 禁止行为
- 违规处罚

### 2. 复盘系统 (reviews/)

**每日复盘** - 每个交易日
- 交易记录
- 执行评估
- 心理状态
- 明日计划

**每周复盘** - 每周五/周末
- 周度绩效
- 策略表现
- 规则遵守
- 下周计划

**每月复盘** - 每月末
- 月度绩效
- 品种/策略分析
- 目标完成度
- 下月计划

### 3. 统计数据 (stats/)

**performance.md** - 绩效统计
- 总体绩效
- 月度绩效
- 品种统计
- 风险指标
- 权益曲线

### 4. 经验教训 (lessons/)

**lessons.md** - 教训清单
- 重大教训
- 常见错误模式
- 重要认知
- 改进追踪

---

## 🔧 工具使用

### 复盘生成器

```bash
# 生成今日复盘
python trading/review_generator.py daily

# 生成本周复盘
python trading/review_generator.py weekly

# 生成本月复盘
python trading/review_generator.py monthly

# 生成所有复盘
python trading/review_generator.py all
```

### 旺财命令

```
旺财，开始今日复盘
旺财，生成本周复盘
旺财，查看交易规则
旺财，记录教训：[内容]
旺财，我的交易统计
旺财，查看绩效
```

---

## 📋 使用流程

### 交易日流程

```
盘前 (9:00)
├─ 阅读 rules.md (交易规则)
├─ 查看 goals.md (目标)
└─ 制定交易计划

盘中
├─ 执行交易
└─ 记录到 trading_log.md

盘后 (22:00)
├─ 生成每日复盘
├─ 填写复盘内容
├─ 更新 performance.md
└─ 记录 lessons.md
```

### 周末流程

```
周五收盘后/周末
├─ 生成周复盘
├─ 汇总本周交易
├─ 分析策略表现
├─ 评估规则遵守
└─ 制定下周计划
```

### 月末流程

```
月末最后 1 个交易日
├─ 生成月复盘
├─ 汇总本月交易
├─ 分析品种/策略
├─ 评估目标完成度
├─ 制定下月计划
└─ 更新年度追踪
```

---

## 📊 当前状态

### 已创建文件
- ✅ memory/profile.md
- ✅ memory/goals.md
- ✅ memory/rules.md
- ✅ reviews/daily/template.md
- ✅ reviews/weekly/template.md
- ✅ reviews/monthly/template.md
- ✅ reviews/daily/2026-03-17.md
- ✅ reviews/weekly/2026-W12.md
- ✅ reviews/monthly/2026-03.md
- ✅ stats/performance.md
- ✅ lessons/lessons.md
- ✅ review_generator.py

### 待创建
- ⏳ strategies/ (策略记录)
- ⏳ 更多交易数据

---

## 🎯 下一步

### 立即开始
1. 阅读 `memory/rules.md` - 熟悉交易规则
2. 查看 `memory/goals.md` - 明确交易目标
3. 填写 `reviews/daily/2026-03-17.md` - 完成今日复盘

### 养成习惯
- 每日复盘 (22:00)
- 每周复盘 (周五)
- 每月复盘 (月末)

### 持续改进
- 定期回顾 lessons.md
- 更新 performance.md
- 优化 rules.md

---

## 💡 最佳实践

1. **诚实记录** - 不掩饰错误，不夸大成功
2. **数据驱动** - 用数据说话，避免主观
3. **持续复盘** - 复盘是进步的阶梯
4. **遵守规则** - 纪律是交易的根本
5. **吸取教训** - 避免重复犯错

---

## 🔔 自动化提醒

旺财会在以下时间提醒你：

- **每日 22:00** - "该做今日复盘了"
- **每周五 18:00** - "该做本周复盘了"
- **月末 18:00** - "该做本月复盘了"

---

**旺财 🎯** - 数据 > 直觉，风控 > 收益，纪律 > 情绪

**系统已就绪，开始你的交易之旅！**

---

## 📝 快速命令

```
旺财，开始今日复盘
旺财，查看交易规则
旺财，我的交易目标是什么
旺财，记录教训：[内容]
旺财，查看交易统计
旺财，生成本周复盘
```
