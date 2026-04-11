#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛发帖工具 v2 - 直接 API 方式
"""

import requests
import re
from pathlib import Path

FORUM_BASE = "http://duckwolf.cn"
FORUM_USER = "store"
FORUM_PASS = "tomwu001"

def main():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # 1. 访问首页获取 cookies
    print("1. 访问首页...")
    resp = session.get(FORUM_BASE)
    print(f"   状态：{resp.status_code}")
    
    # 2. 登录
    print("2. 登录账号...")
    login_url = f"{FORUM_BASE}/member.php?mod=logging&action=login&loginsubmit=yes&inajax=1"
    login_data = {
        'username': FORUM_USER,
        'password': FORUM_PASS,
        'quickforward': 'yes',
        'handlekey': 'ls'
    }
    resp = session.post(login_url, data=login_data)
    print(f"   状态：{resp.status_code}")
    
    # 3. 验证登录
    print("3. 验证登录...")
    resp = session.get(f"{FORUM_BASE}/home.php?mod=spacecp")
    if FORUM_USER in resp.text or 'discuz_uid' in resp.text:
        print("   登录成功！")
    else:
        print("   登录可能失败")
    
    # 4. 读取帖子内容
    print("4. 读取帖子内容...")
    post_file = Path(__file__).parent / "forum_post_v2_share.txt"
    with open(post_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   字数：{len(content)}")
    
    # 5. 获取 formhash
    print("5. 获取 formhash...")
    post_url = f"{FORUM_BASE}/forum.php?mod=post&action=newthread&fid=54"
    resp = session.get(post_url)
    match = re.search(r'name="formhash" value="([a-zA-Z0-9]+)"', resp.text)
    if match:
        formhash = match.group(1)
        print(f"   Formhash: {formhash}")
    else:
        print("   未找到 formhash，使用默认值")
        formhash = ""
    
    # 6. 发帖
    print("6. 提交帖子...")
    title = "旺财 MT5 量化交易系统 v2.0 正式发布 - 用亏损换来的血泪经验"
    post_data = {
        'formhash': formhash,
        'subject': title,
        'message': content,
        'special': '0',
        'topicsubmit': 'yes',
        'posttime': ''
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': post_url,
        'Origin': FORUM_BASE
    }
    
    resp = session.post(post_url, data=post_data, headers=headers)
    print(f"   状态：{resp.status_code}")
    
    # 7. 检查结果
    if 'viewthread.php' in resp.url or '发布成功' in resp.text or '发表成功' in resp.text:
        print("\n[SUCCESS] 发帖成功！")
        print(f"   URL: {resp.url}")
    else:
        print("\n[WARNING] 发帖可能失败")
        # 保存响应
        with open('post_debug.html', 'w', encoding='utf-8') as f:
            f.write(resp.text[:3000])
        print("   调试信息已保存到：post_debug.html")
        
        # 尝试从响应中提取帖子链接
        match = re.search(r'viewthread\.php\?tid=(\d+)', resp.text)
        if match:
            tid = match.group(1)
            print(f"\n   可能成功！帖子 ID: {tid}")
            print(f"   URL: {FORUM_BASE}/viewthread.php?tid={tid}")

if __name__ == "__main__":
    main()
