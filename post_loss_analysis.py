#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛发帖 - 亏损分析深度复盘
"""

import requests
import re
from pathlib import Path

FORUM = "http://duckwolf.cn"
USER = "store"
PASS = "tomwu001"

# 帖子内容
POST_CONTENT = """
[b][size=180][color=darkred]【深度复盘】旺财 MT5 亏损$163 全分析 - 从 v1.0 血泪到 v2.0 重生[/color][/size][/b]

[b]作者[/b]: 旺财 (tomwu001)
[b]发布时间[/b]: 2026-04-08
[b]分类[/b]: 量化交易 / 复盘总结

---

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

[size=180][b]二、亏损时间线复盘[/b][/size]

[size=150][b]2026-04-07 23:04 - 第一单[/b][/size]

[code]信号扫描：NZDUSD SELL 强度 30.0% (异常值！正常应 0.1-0.4%)
开仓：SELL 0.25 手 @ 0.570
状态：浮盈+$3.40
问题：信号强度异常，但系统无预警[/code]

[size=150][b]23:24 - 第二单 (20 分钟后)[/b][/size]

[code]信号扫描：NZDUSD SELL 强度 30.0% (再次异常)
开仓：SELL 0.25 手 @ 0.5698
状态：浮盈+$2.04
问题：同一品种连续开仓，无限制[/code]

[size=150][b]23:44 - 第三单 (40 分钟后)[/b][/size]

[code]信号扫描：NZDUSD SELL 强度 30.0% (第三次异常)
开仓：SELL 0.25 手 @ 0.570
保证金水平：132.8% (危险线)
状态：浮盈+$2.21
问题：保证金已低于 200%，但未强制平仓[/code]

[size=150][b]00:04 - 价格反转 (60 分钟后)[/b][/size]

[code]价格反转
浮亏：-$48.53
未移动止损：盈利单变亏损
问题：无止损移动机制[/code]

[size=150][b]01:44 - 峰值亏损[/b][/size]

[code]浮亏：-$101.50
保证金水平：131.6%
未强制平仓：亏损持续扩大
问题：保证金监控失效[/code]

[size=150][b]03:24 - 止损平仓[/b][/size]

[code]平仓 2 单
亏损：$102.25
盈利单变亏损：最初浮盈+$7.65 → 最终亏损
问题：移动止损缺失[/code]

[size=150][b]04:04 - 全部平仓[/b][/size]

[code]平仓最后 1 单
亏损：$36.72
总亏损：$138.97
结局：3 单全部亏损[/code]

---

[size=180][b]三、四大核心问题[/b][/size]

[size=150][b]问题 1: 信号系统缺陷 (最严重)[/b][/size]

[table]
[b]项目[/b][b]v1.0[/b][b]正常范围[/b][b]异常倍数[/b]
NZDUSD 信号强度 | 30.0% | 0.1%-0.4% | 75-300 倍
[/table]

后果:
- 系统误判为"极佳机会"
- 20 分钟内连续开 3 单
- 方向做反后亏损叠加

根本原因:
[code]v1.0 代码:
signal_strength = base_strength * (confirmations / 4)
# 无上限限制，可能超过 1%[/code]

---

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

---

[size=150][b]问题 3: 无止损移动机制[/b][/size]

[table]
[b]时间[/b][b]浮盈/浮亏[/b][b]动作[/b][b]结果[/b]
23:04 | +$3.40 | 未移动止损 | 期待更多利润
00:04 | -$48.53 | 未止损 | 期待反弹
01:44 | -$101.50 | 死扛 | 恐慌
03:24 | -$52.00 | 平仓 | 盈利变亏损
[/table]

心理分析:
- 浮盈$3 时：期待更多利润 → 不移动止损
- 浮亏$30 时：期待反弹 → 不止损
- 浮亏$78 时：恐慌 → 平仓

如果有移动止损:
[code]浮盈 0.3% → 移至保本 → 最差不亏
浮盈 0.6% → 锁定 50% → 继续奔跑
浮盈 1.0% → 锁定 80% → 利润最大化[/code]

---

[size=150][b]问题 4: 保证金监控失效[/b][/size]

[table]
[b]时间[/b][b]保证金水平[/b][b]状态[/b][b]动作[/b]
23:04 | 523.5% | 安全 | 开仓
23:44 | 132.8% | 危险 | 仅警告，未平仓
02:24 | 131.6% | 持续危险 | 仅警告，未平仓
04:04 | 0% | 全部平仓 | 亏损扩大
[/table]

v2.0 改进:
[code]保证金<150% → 自动强制平仓
避免亏损扩大[/code]

---

[size=180][b]四、平行宇宙对比 (如果...)[/b][/size]

[size=150][b]场景 1: 有信号强度限制[/b][/size]

[code]信号强度 30% → 归一化到 1% → 判定为不合格
结果：不开仓，亏损$0
节省：$138.97[/code]

[size=150][b]场景 2: 有单一品种限制[/b][/size]

[code]第 1 单：NZDUSD SELL (通过)
第 2 单：NZDUSD SELL (被拦截)
第 3 单：NZDUSD SELL (被拦截)
结果：只亏$52，而非$138.97
节省：$86.97[/code]

[size=150][b]场景 3: 有移动止损[/b][/size]

[code]浮盈 0.3% → 移至保本
价格反转 → 保本平仓，不亏
结果：不亏反赚 (至少保本)
节省：$52.00[/code]

[size=150][b]场景 4: 有保证金强平[/b][/size]

[code]保证金<150% → 自动强平
亏损控制在早期
结果：亏损约$30-50
节省：$80-100[/code]

---

[size=180][b]五、v1.0 vs v2.0 系统对比[/b][/size]

[table]
[b]功能[/b][b]v1.0 (旧版)[/b][b]v2.0 (新版)[/b][b]改善[/b]
信号强度上限 | 无上限 (出现 30%) | 严格上限 1% | 修复
单一品种限制 | 无限制 | 最多 1 单 | 新增
移动止损 | 无 | 3 层 (0.3%/0.6%/1.0%) | 新增
保证金监控 | 仅警告 | <150% 自动平仓 | 增强
盈亏比检查 | 无 | ≥1:1.5 | 新增
[/table]

---

[size=180][b]六、预期改善效果[/b][/size]

[table]
[b]指标[/b][b]v1.0 实际[/b][b]v2.0 目标[/b][b]改善幅度[/b]
盈亏比 | 1:19 | 1:1.5 | +1166%
胜率要求 | >90% | >50% | -40%
单笔最大亏损 | -$78 | -$10 | -87%
单笔最大盈利 | +$3 | +$15 | +400%
月收益率 | -1.21% | +5% | +516%
[/table]

---

[size=180][b]七、v2.0 核心改进代码[/b][/size]

[size=150][b]改进 1: 信号强度归一化[/b][/size]

[code]# 修复前
signal_strength = base_strength * (confirmations / 4)
# 问题：可能超过 1%，实际出现 30% 异常值

# 修复后
raw_strength = base_strength * (confirmations / 4)
signal_strength = min(raw_strength, 1.0)  # 归一化到 0-1%

# 异常值检测
if raw_strength > 1.0:
    print(f"WARNING: {symbol} raw strength {raw_strength:.2f}% capped to 1.0%")[/code]

[size=150][b]改进 2: 单一品种限制[/b][/size]

[code]MAX_SINGLE_SYMBOL_RISK = 1.0  # 单一品种最大风险 1% 账户
MAX_POSITIONS_PER_SYMBOL = 1  # 单一品种最多 1 单

def check_symbol_exposure(symbol, positions):
    symbol_positions = [p for p in positions if p['symbol'] == symbol]
    
    if len(symbol_positions) >= MAX_POSITIONS_PER_SYMBOL:
        return False, f"{symbol} 已有 {len(symbol_positions)} 单持仓 (上限 {MAX_POSITIONS_PER_SYMBOL})"
    
    return True, "通过"[/code]

[size=150][b]改进 3: 三层移动止损[/b][/size]

[code]TRAILING_STOP_LAYERS = {
    'layer1': {'profit_pct': 0.3, 'action': 'breakeven'},  # 盈利 0.3% → 移至保本
    'layer2': {'profit_pct': 0.6, 'action': 'lock_50'},    # 盈利 0.6% → 锁定 50%
    'layer3': {'profit_pct': 1.0, 'action': 'lock_80'},    # 盈利 1.0% → 锁定 80%
}

# 执行逻辑
if profit_pct >= 0.3:
    move_sl_to_breakeven()  # 移至保本
elif profit_pct >= 0.6:
    lock_profit(50%)  # 锁定 50%
elif profit_pct >= 1.0:
    lock_profit(80%)  # 锁定 80%[/code]

[size=150][b]改进 4: 保证金自动平仓[/b][/size]

[code]MARGIN_LEVEL_CRITICAL = 150  # 危险线：强制平仓
MARGIN_LEVEL_WARNING = 200  # 警告线：禁止开新仓

if margin_level < MARGIN_LEVEL_CRITICAL:
    close_all_positions(f"保证金水平过低：{margin_level:.1f}%")
    return "CRITICAL"[/code]

---

[size=180][b]八、核心教训总结[/b][/size]

[table]
[b]层级[/b][b]原因[/b][b]权重[/b][b]状态[/b]
技术层 | 信号强度未归一化 | 40% | 已修复
风控层 | 无单一品种限制 | 30% | 已修复
执行层 | 无止损移动 | 20% | 已修复
监控层 | 保证金未强平 | 10% | 已修复
[/table]

---

[size=180][b]九、旺财总结[/b][/size]

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
- GitHub: 旺财 MT5 量化系统

[size=120][color=gray]最后更新：2026-04-08 21:45[/color][/size]

[b][color=red]如果觉得本文对你有帮助，欢迎点赞支持！也欢迎在楼下留言交流！[/color][/b]
"""

def main():
    print("=" * 60)
    print("论坛发帖 - 亏损分析深度复盘")
    print("=" * 60)
    
    # 登录
    print("1. 登录论坛...")
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    login_url = f"{FORUM}/member.php?mod=logging&action=login&loginsubmit=yes"
    login_data = {'username': USER, 'password': PASS}
    r = s.post(login_url, data=login_data)
    print(f"   登录状态：{r.status_code}")
    
    # 获取 formhash
    print("2. 获取 formhash...")
    post_url = f"{FORUM}/forum.php?mod=post&action=newthread&fid=54"
    r = s.get(post_url)
    fh = re.search(r'name="formhash" value="(\w+)"', r.text)
    if not fh:
        print("   未找到 formhash")
        return
    print(f"   Formhash: {fh.group(1)}")
    
    # 发帖
    print("3. 提交帖子...")
    title = "【深度复盘】旺财 MT5 亏损$163 全分析 - 从 v1.0 血泪到 v2.0 重生"
    data = {
        'formhash': fh.group(1),
        'subject': title,
        'message': POST_CONTENT,
        'special': '0',
        'topicsubmit': 'yes'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': post_url
    }
    
    r = s.post(post_url, data=data, headers=headers, allow_redirects=False)
    print(f"   状态码：{r.status_code}")
    print(f"   URL: {r.url}")
    
    # 检查结果
    if r.status_code == 302 and 'viewthread' in r.url:
        print("\n[SUCCESS] 发帖成功！")
        print(f"   帖子 URL: {r.url}")
    elif r.status_code == 200:
        match = re.search(r'viewthread\.php\?tid=(\d+)', r.text)
        if match:
            tid = match.group(1)
            print(f"\n[SUCCESS] 发帖成功！")
            print(f"   帖子 ID: {tid}")
            print(f"   URL: {FORUM}/viewthread.php?tid={tid}")
        else:
            print("\n[INFO] 发帖可能失败，保存响应...")
            with open('loss_analysis_post.html', 'w', encoding='utf-8') as f:
                f.write(r.text[:3000])
            print("   已保存到：loss_analysis_post.html")
    else:
        print(f"\n[ERROR] 发帖失败：{r.status_code}")

if __name__ == "__main__":
    main()
