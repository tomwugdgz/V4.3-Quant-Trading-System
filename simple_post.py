#!/usr/bin/env python3
"""
论坛发帖 - 简化版测试
"""

import requests
import re

FORUM = "http://duckwolf.cn"
USER = "store"
PASS = "tomwu001"

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# 登录
print("登录...")
s.post(f"{FORUM}/member.php?mod=logging&action=login", 
       data={'username': USER, 'password': PASS})

# 获取 formhash
print("获取 formhash...")
r = s.get(f"{FORUM}/forum.php?mod=post&action=newthread&fid=54")
fh = re.search(r'name="formhash" value="(\w+)"', r.text)
if not fh:
    print("未找到 formhash")
    exit(1)
formhash = fh.group(1)
print(f"Formhash: {formhash}")

# 简化帖子
title = "旺财 MT5 量化系统 v2.0 发布"
content = f"""
[b][size=150]旺财 MT5 量化交易系统 v2.0 正式发布[/size][/b]

[b]作者[/b]: 旺财 (tomwu001)

各位坛友好，2026 年 4 月 7 日我经历了量化交易最黑暗的一天——3 笔交易亏损$138.97。

但这次失败逼我开发出了 v2.0 系统，今天公开分享所有代码和数据。

[b]核心改进[/b]:
[*] 信号强度归一化 (上限 1%)
[*] 单一品种限制 (最多 1 单)
[*] 三层移动止损
[*] 保证金<150% 自动平仓

[b]数据对比[/b]:
[table]
[b]指标[/b][b]v1.0[/b][b]v2.0[/b][b]改善[/b]
盈亏比 | 1:19 | 1:1.5 | +1166%
胜率要求 | >90% | >50% | -40%
单笔亏损 | -$78 | -$10 | -87%
[/table]

[b]实战推演[/b]:
同样 NZDUSD 场景:
v1.0: 亏损$138.97
v2.0: 盈利$15.00
差异：+$153.97

所有代码开源免费，欢迎交流指正！

[b]联系方式[/b]:
[*] 论坛 ID: tomwu001
[*] GitHub: 旺财量化交易

[color=red]欢迎点赞支持！楼下留言交流！[/color]
"""

# 发帖
print("发帖...")
r = s.post(f"{FORUM}/forum.php?mod=post&action=newthread&fid=54",
           data={'formhash': formhash, 'subject': title, 'message': content, 
                 'topicsubmit': 'yes'},
           headers={'Referer': f'{FORUM}/forum.php?mod=post&action=newthread&fid=54'})

print(f"状态：{r.status_code}")
print(f"URL: {r.url}")

if 'viewthread' in r.url or '成功' in r.text:
    print("[SUCCESS] 发帖成功!")
else:
    print("[WARNING] 可能失败")
    with open('test_post.html', 'w', encoding='utf-8') as f:
        f.write(r.text[:2000])
