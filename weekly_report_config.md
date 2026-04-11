# 旺财周报系统配置指南

**版本**: 1.0  
**创建时间**: 2026-04-08  
**执行频率**: 每周五 20:00 自动生成

---

## 一、快速开始

### 1.1 手动执行测试

```powershell
cd C:\Users\DELL\.openclaw-autoclaw\workspace\trading
python weekly_report_generator.py
```

**预期输出**:
```
============================================================
旺财交易周报生成器 v1.0
============================================================
统计周期：2026-04-08 - 2026-04-14
本周交易：3 单
胜率：66.7%
总盈亏：$150.00
盈利因子：2.50
平均盈亏比：1.85
报告已保存：...\weekly_reports\weekly_report_20260408_to_20260414.md
飞书通知：周报已生成
============================================================
周报生成完成
============================================================
```

---

## 二、Windows 定时任务配置

### 2.1 创建计划任务

**方法 1: 使用任务计划程序 (GUI)**

1. 打开 **任务计划程序** (Win + R → `taskschd.msc`)
2. 点击 **创建基本任务**
3. 填写信息:
   ```
   名称：旺财交易周报
   描述：每周五 20:00 自动生成交易周报
   触发器：每周
   开始时间：2026-04-11 20:00
   重复：每 1 周，星期五
   操作：启动程序
   程序：python.exe
   参数：weekly_report_generator.py
   起始目录：C:\Users\DELL\.openclaw-autoclaw\workspace\trading
   ```

4. 完成创建

---

**方法 2: 使用命令行 (推荐)**

```powershell
# 创建定时任务
schtasks /Create /TN "旺财交易周报" /TR "python.exe C:\Users\DELL\.openclaw-autoclaw\workspace\trading\weekly_report_generator.py" /SC WEEKLY /D FRI /ST 20:00 /SD 2026/04/11 /RU "DELL" /RL HIGHEST

# 查看任务
schtasks /Query /TN "旺财交易周报"

# 测试运行
schtasks /Run /TN "旺财交易周报"

# 删除任务 (如需要)
schtasks /Delete /TN "旺财交易周报" /F
```

---

### 2.2 验证配置

```powershell
# 查看任务状态
schtasks /Query /TN "旺财交易周报" /V

# 查看任务历史
Get-ScheduledTask -TaskName "旺财交易周报" | Get-ScheduledTaskInfo
```

**预期输出**:
```
TaskName               : 旺财交易周报
LastRunTime            : 2026-04-11T20:00:00
LastTaskResult         : 0 (成功)
NextRunTime            : 2026-04-18T20:00:00
NumberOfMissedRuns     : 0
Status                 : Ready
```

---

## 三、飞书通知配置

### 3.1 配置飞书 Webhook

1. 在飞书群中添加 **自定义机器人**
2. 获取 Webhook URL
3. 修改脚本 `weekly_report_generator.py`:

```python
def send_feishu_notification(report_path):
    """发送飞书通知"""
    import requests
    import json
    
    webhook_url = "YOUR_FEISHU_WEBHOOK_URL"
    
    # 读取报告摘要
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # 提取关键指标
    lines = report_content.split('\n')
    summary = []
    for line in lines:
        if '| 胜率 |' in line or '| 总盈亏 |' in line or '| 盈利因子 |' in line:
            summary.append(line)
    
    # 构建消息
    message = {
        "msg_type": "text",
        "content": {
            "text": f"📊 旺财交易周报已生成\n\n报告路径：{report_path}\n\n核心指标:\n" + "\n".join(summary)
        }
    }
    
    # 发送
    response = requests.post(webhook_url, json=message)
    
    if response.status_code == 200:
        log_message("飞书通知发送成功", "SUCCESS")
    else:
        log_message(f"飞书通知发送失败：{response.text}", "ERROR")
```

---

## 四、报告管理

### 4.1 报告存储结构

```
trading/
└── weekly_reports/
    ├── weekly_report_20260408_to_20260414.md
    ├── weekly_report_20260415_to_20260421.md
    ├── weekly_report_20260422_to_20260428.md
    └── ...
```

### 4.2 报告归档

**月度汇总** (每月 1 号执行):
```powershell
# 创建月度汇总脚本
python monthly_summary.py
```

**年度归档** (每年 1 月 1 号):
```powershell
# 打包旧报告
Compress-Archive -Path weekly_reports\2026*.md -DestinationPath archive\2026_weekly_reports.zip
```

---

## 五、报告内容说明

### 5.1 核心指标

| 指标 | 说明 | 合格线 |
|------|------|--------|
| **交易次数** | 本周交易总数 | 10-30 单 |
| **胜率** | 盈利交易占比 | ≥50% |
| **总盈亏** | 本周净盈亏 | >$0 |
| **盈利因子** | 总盈利/总亏损 | ≥1.5 |
| **平均盈亏比** | 平均盈利/平均亏损 | ≥1.5 |

### 5.2 状态标记

- ✅ **优秀**: 达到或超过目标
- ⚠️ **注意**: 接近警戒线
- ❌ **警告**: 低于合格线

### 5.3 问题诊断

**胜率<50%**:
- 可能原因：信号质量不足
- 改进建议：提高信号强度门槛

**盈亏比<1.5**:
- 可能原因：止盈过早或止损过宽
- 改进建议：启用移动止损

**盈利因子<1.5**:
- 可能原因：亏损单金额过大
- 改进建议：严格执行止损

---

## 六、v1.0 vs v2.0 对比追踪

### 6.1 每周更新

周报会自动包含 v1.0 vs v2.0 对比表格：

```markdown
## 🆚 系统版本对比 (v1.0 vs v2.0)

| 指标 | v1.0 (上周) | v2.0 (本周) | 改善 |
|------|-------------|-------------|------|
| 胜率 | 45% | 55% | +10% ✅ |
| 盈亏比 | 1:5 | 1:1.8 | +20% ✅ |
| 总盈亏 | -$200 | +$300 | +$500 ✅ |
```

### 6.2 月度汇总

每月生成一份深度对比报告：

```powershell
# 月度对比报告
python monthly_comparison.py
```

输出：`monthly_comparison_v1_vs_v2_202604.md`

---

## 七、故障排查

### 7.1 常见问题

**Q1: 任务未执行**
```
检查：任务计划程序 → 查看任务历史
解决：重新创建任务，确保用户权限正确
```

**Q2: MT5 连接失败**
```
检查：MT5 是否运行
解决：在脚本开头添加 MT5 启动逻辑
```

**Q3: 飞书通知未发送**
```
检查：Webhook URL 是否正确
解决：测试 Webhook 连通性
```

### 7.2 日志位置

```
trading/weekly_reports/weekly_report.log
```

查看最新日志:
```powershell
Get-Content trading\weekly_reports\weekly_report.log -Tail 50
```

---

## 八、配置检查清单

### 8.1 首次配置

- [ ] Python 环境已安装
- [ ] MetaTrader5 已安装
- [ ] 脚本权限已授予
- [ ] 定时任务已创建
- [ ] 飞书 Webhook 已配置
- [ ] 测试运行成功

### 8.2 每周检查

- [ ] 周报已生成
- [ ] 飞书通知已收到
- [ ] 数据准确性验证
- [ ] 问题及时跟进

---

## 九、旺财承诺

> **透明公开，持续改进！**

**承诺事项**:
1. ✅ 每周五 20:00 准时生成报告
2. ✅ 数据真实准确，不隐瞒亏损
3. ✅ 问题及时分析，提出改进方案
4. ✅ v1.0 vs v2.0 对比持续追踪

**监督方式**:
- 飞书群自动通知
- 报告公开可查
- 随时接受质询

---

**配置完成时间**: 2026-04-08  
**首次执行时间**: 2026-04-11 (周五) 20:00  
**系统版本**: v2.0  
**旺财 🎯**: 数据 > 直觉，风控 > 收益，纪律 > 情绪

---

*配置文档路径：trading/weekly_report_config.md*  
*脚本路径：trading/weekly_report_generator.py*  
*报告路径：trading/weekly_reports/*
