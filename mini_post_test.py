#!/usr/bin/env python3
# 极简发帖测试

import requests, re

FORUM = "http://duckwolf.cn"
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

# 登录
s.post(f"{FORUM}/member.php?mod=logging&action=login", 
       data={'username': 'store', 'password': 'tomwu001'})
print("登录完成")

# 获取 formhash
r = s.get(f"{FORUM}/forum.php?mod=post&action=newthread&fid=54")
fh = re.search(r'name="formhash" value="(\w+)"', r.text)
if not fh:
    print("No formhash")
    exit(1)
print(f"Formhash: {fh.group(1)}")

# 极简帖子
title = "旺财 MT5 量化系统 v2.0 发布"
content = """
[b]旺财 MT5 量化交易系统 v2.0 正式发布[/b]

作者：旺财 (tomwu001)

2026 年 4 月 7 日，我经历了量化交易最黑暗的一天——3 笔交易亏损$138.97。

但这次失败逼我开发出了 v2.0 系统，今天公开分享所有代码和数据。

[b]核心改进[/b]:
[*] 信号强度归一化 (上限 1%)
[*] 单一品种限制 (最多 1 单)
[*] 三层移动止损
[*] 保证金<150% 自动平仓

[b]数据对比[/b]:
v1.0: 盈亏比 1:19，胜率需>90%
v2.0: 盈亏比 1:1.5，胜率 50% 即可

[b]实战推演[/b]:
同样 NZDUSD 场景:
v1.0: 亏损$138.97
v2.0: 盈利$15.00
差异：+$153.97

所有代码开源免费，欢迎交流指正！

联系方式:
[*] 论坛 ID: tomwu001
[*] GitHub: 旺财量化交易

欢迎点赞支持！楼下留言交流！
"""

# 发帖
post_url = f"{FORUM}/forum.php?mod=post&action=newthread&fid=54&extra=&topicsubmit=yes"
data = {
    'formhash': fh.group(1),
    'subject': title,
    'message': content,
    'special': '0',
    'topicsubmit': 'yes'
}
r = s.post(post_url, data=data, allow_redirects=False)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")
print(f"Location: {r.headers.get('Location', 'N/A')}")

if r.status_code == 302:
    print("[SUCCESS] 发帖成功！")
    print(f"跳转 URL: {r.headers.get('Location')}")
else:
    print(f"[INFO] 状态码：{r.status_code}")
    with open('mini_post.html', 'w', encoding='utf-8') as f:
        f.write(r.text[:3000])
