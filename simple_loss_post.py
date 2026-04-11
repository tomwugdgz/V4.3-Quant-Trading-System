#!/usr/bin/env python3
# 简化版发帖

import requests, re

FORUM = "http://duckwolf.cn"
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# 登录
print("登录...")
s.post(f"{FORUM}/member.php?mod=logging&action=login", 
       data={'username': 'store', 'password': 'tomwu001', 'quickforward': 'yes'})

# 获取 formhash
print("获取 formhash...")
r = s.get(f"{FORUM}/forum.php?mod=post&action=newthread&fid=54")
fh = re.search(r'name="formhash" value="(\w+)"', r.text)
if not fh:
    print("No formhash")
    exit(1)
print(f"Formhash: {fh.group(1)}")

# 简化帖子
title = "【深度复盘】旺财 MT5 亏损$163 全分析 - 从 v1.0 血泪到 v2.0 重生"
content = """
[b][size=180][color=darkred]【深度复盘】旺财 MT5 亏损$163 全分析 - 从 v1.0 血泪到 v2.0 重生[/color][/size][/b]

[b]作者[/b]: 旺财 (tomwu001)
[b]发布时间[/b]: 2026-04-08

[size=150][b]前言[/b][/size]

2026 年 4 月 7 日，我经历了量化交易生涯中最黑暗的一天——单日亏损$138.97，总亏损$163.97。

但正是这次惨痛失败，逼我开发出了 v2.0 系统。今天，我将整个亏损过程、原因分析和系统改进全部公开分享。

所有数据真实可查，所有代码开源免费，希望能帮助正在量化路上摸索的同行们。

---

[size=180][b]一、亏损数据总览[/b][/size]

[table]
[b]指标[/b][b]数值[/b][b]状态[/b]
总盈亏 | -$163.97 | 严重亏损
最大单日亏损 | -$138.97 (04-07) | 异常
胜率 | 22.2% (2 赢/7 输) | 偏低
盈亏比 | 1:19 | 严重失衡
[/table]

---

[size=180][b]二、四大核心问题[/b][/size]

[size=150][b]问题 1: 信号系统缺陷 (最严重)[/b][/size]

[table]
[b]项目[/b][b]v1.0[/b][b]正常范围[/b][b]异常倍数[/b]
NZDUSD 信号强度 | 30.0% | 0.1%-0.4% | 75-300 倍
[/table]

后果:
- 系统误判为"极佳机会"
- 20 分钟内连续开 3 单
- 方向做反后亏损叠加

[size=150][b]问题 2: 集中风险失控[/b][/size]

[table]
[b]时间[/b][b]品种[/b][b]方向[/b][b]仓位[/b][b]累计风险[/b]
23:04 | NZDUSD | SELL | 0.25 手 | 0.25 手
23:24 | NZDUSD | SELL | 0.25 手 | 0.50 手
23:44 | NZDUSD | SELL | 0.25 手 | 0.75 手 (危险!)
[/table]

对比 (如果有单一品种限制):
[code]只能开 1 单 NZDUSD
最大亏损：$52.00 (而非$138.97)
减少亏损：62%![/code]

[size=150][b]问题 3: 无止损移动机制[/b][/size]

[table]
[b]时间[/b][b]浮盈/浮亏[/b][b]动作[/b][b]结果[/b]
23:04 | +$3.40 | 未移动止损 | 期待更多利润
00:04 | -$48.53 | 未止损 | 期待反弹
01:44 | -$101.50 | 死扛 | 恐慌
03:24 | -$52.00 | 平仓 | 盈利变亏损
[/table]

[size=150][b]问题 4: 保证金监控失效[/b][/size]

[table]
[b]时间[/b][b]保证金水平[/b][b]状态[/b][b]动作[/b]
23:04 | 523.5% | 安全 | 开仓
23:44 | 132.8% | 危险 | 仅警告，未平仓
02:24 | 131.6% | 持续危险 | 仅警告，未平仓
04:04 | 0% | 全部平仓 | 亏损扩大
[/table]

---

[size=180][b]三、v1.0 vs v2.0 系统对比[/b][/size]

[table]
[b]功能[/b][b]v1.0 (旧版)[/b][b]v2.0 (新版)[/b][b]改善[/b]
信号强度上限 | 无上限 (出现 30%) | 严格上限 1% | 修复
单一品种限制 | 无限制 | 最多 1 单 | 新增
移动止损 | 无 | 3 层 (0.3%/0.6%/1.0%) | 新增
保证金监控 | 仅警告 | <150% 自动平仓 | 增强
盈亏比检查 | 无 | ≥1:1.5 | 新增
[/table]

---

[size=180][b]四、预期改善效果[/b][/size]

[table]
[b]指标[/b][b]v1.0 实际[/b][b]v2.0 目标[/b][b]改善幅度[/b]
盈亏比 | 1:19 | 1:1.5 | +1166%
胜率要求 | >90% | >50% | -40%
单笔最大亏损 | -$78 | -$10 | -87%
单笔最大盈利 | +$3 | +$15 | +400%
月收益率 | -1.21% | +5% | +516%
[/table]

---

[size=180][b]五、旺财总结[/b][/size]

[quote]这次亏损系系统设计缺陷，不是市场的错！[/quote]

[b]核心教训[/b]:
1. 信号强度 30% 明显异常，但系统没有预警
2. 3 笔交易同一品种，违反分散风险原则
3. 浮盈$3 不移动止损，最终变亏损$52
4. 保证金从 523% 跌至 131%，系统只警告不平仓

[b]改进承诺[/b]:
- 信号强度归一化 (上限 1%)
- 单一品种最多 1 单
- 三层移动止损 (0.3%/0.6%/1.0%)
- 保证金<150% 自动平仓

[b]预期效果[/b]:
[code]v1.0: 盈亏比 1:19，胜率需>90% 才能盈利
v2.0: 盈亏比 1:1.5，胜率 50% 即可长期盈利[/code]

---

[size=150][b]结语[/b][/size]

量化交易这条路，注定孤独且充满挑战。但我相信，只要能从失败中学习，持续迭代优化，终会找到属于自己的盈利模式。

v2.0 系统只是开始，不是终点。我会在论坛持续更新系统的实战数据和优化进展，也欢迎各位坛友提出宝贵建议。

[b]联系方式[/b]:
- 论坛 ID: tomwu001
- 飞书群：旺财量化交易交流

[size=120][color=gray]最后更新：2026-04-08 21:45[/color][/size]

[b][color=red]如果觉得本文对你有帮助，欢迎点赞支持！也欢迎在楼下留言交流！[/color][/b]
"""

# 发帖
print("发帖...")
post_url = f"{FORUM}/forum.php?mod=post&action=newthread&fid=54&extra=&topicsubmit=yes"
data = {
    'formhash': fh.group(1),
    'subject': title,
    'message': content,
    'special': '0',
    'topicsubmit': 'yes',
    'addtradeinfo': '0',
    'posttime': ''
}
r = s.post(post_url, data=data, allow_redirects=False)
print(f"状态：{r.status_code}")
print(f"URL: {r.url}")
print(f"Location: {r.headers.get('Location', 'N/A')}")

if r.status_code == 302 or r.status_code == 301:
    print("[SUCCESS] 发帖成功！")
    print(f"跳转 URL: {r.headers.get('Location')}")
else:
    print(f"[INFO] 状态码：{r.status_code}")
    with open('simple_post_check.html', 'w', encoding='utf-8') as f:
        f.write(r.text[:3000])
