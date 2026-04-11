#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛发帖 - 最终版
"""

import requests
import re
from pathlib import Path

FORUM = "http://duckwolf.cn"
USER = "store"
PASS = "tomwu001"

def main():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    })
    
    # 1. 访问首页
    print("1. 访问首页...")
    r = s.get(FORUM)
    print(f"   Status: {r.status_code}")
    
    # 2. 登录
    print("2. 登录...")
    login_url = f"{FORUM}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash=LaonO"
    login_data = {
        'username': USER,
        'password': PASS,
        'quickforward': 'yes',
        'handlekey': 'ls'
    }
    r = s.post(login_url, data=login_data, allow_redirects=True)
    print(f"   Status: {r.status_code}")
    
    # 3. 验证登录
    print("3. 验证登录...")
    r = s.get(f"{FORUM}/home.php?mod=spacecp")
    if 'discuz_uid' in r.text:
        print("   登录成功！")
    else:
        print("   登录失败")
        return
    
    # 4. 读取帖子内容
    print("4. 读取帖子内容...")
    post_file = Path(__file__).parent / "forum_post_v2_share.txt"
    with open(post_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   字数：{len(content)}")
    
    # 5. 获取 formhash
    print("5. 获取 formhash...")
    post_url = f"{FORUM}/forum.php?mod=post&action=newthread&fid=54"
    r = s.get(post_url)
    match = re.search(r'name="formhash" value="([a-zA-Z0-9]+)"', r.text)
    if match:
        formhash = match.group(1)
        print(f"   Formhash: {formhash}")
    else:
        print("   未找到 formhash")
        return
    
    # 6. 发帖
    print("6. 发帖...")
    title = "旺财 MT5 量化交易系统 v2.0 正式发布 - 用亏损换来的血泪经验"
    post_data = {
        'formhash': formhash,
        'subject': title,
        'message': content,
        'special': '0',
        'topicsubmit': 'yes',
        'posttime': '',
        'addtradeinfo': '0'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': post_url,
        'Origin': FORUM,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    r = s.post(post_url, data=post_data, headers=headers, allow_redirects=False)
    print(f"   Status: {r.status_code}")
    print(f"   URL: {r.url}")
    
    # 7. 检查结果
    if r.status_code == 302 and 'viewthread' in r.url:
        print("\n[SUCCESS] 发帖成功！")
        print(f"   帖子 URL: {r.url}")
    elif r.status_code == 200:
        # 检查是否包含帖子链接
        match = re.search(r'viewthread\.php\?tid=(\d+)', r.text)
        if match:
            tid = match.group(1)
            print(f"\n[SUCCESS] 发帖成功！")
            print(f"   帖子 ID: {tid}")
            print(f"   URL: {FORUM}/viewthread.php?tid={tid}")
        else:
            print("\n[INFO] 发帖可能失败，保存响应...")
            with open('final_post_check.html', 'w', encoding='utf-8') as f:
                f.write(r.text)
            print("   已保存到：final_post_check.html")
    else:
        print(f"\n[ERROR] 发帖失败：{r.status_code}")

if __name__ == "__main__":
    main()
