#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛自动发帖工具
论坛：http://duckwolf.cn
用户：store / tomwu001
"""

import requests
from pathlib import Path

# 配置
FORUM_BASE = "http://duckwolf.cn"
LOGIN_URL = f"{FORUM_BASE}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash=LaonO&inajax=1"
POST_URL = f"{FORUM_BASE}/forum.php?mod=post&action=newthread&fid=54&extra=&topicsubmit=yes"

FORUM_USER = "store"
FORUM_PASS = "tomwu001"

POST_FILE = Path(__file__).parent / "forum_post_v2_share.txt"

def login():
    """登录论坛"""
    print(f"正在登录：{FORUM_USER}")
    
    session = requests.Session()
    
    # 获取 formhash
    resp = session.get(FORUM_BASE)
    print(f"访问首页：{resp.status_code}")
    
    # 尝试登录
    login_data = {
        'username': FORUM_USER,
        'password': FORUM_PASS,
        'quickforward': 'yes',
        'handlekey': 'ls'
    }
    
    resp = session.post(LOGIN_URL, data=login_data)
    print(f"登录请求：{resp.status_code}")
    
    # 验证登录
    resp = session.get(f"{FORUM_BASE}/home.php?mod=spacecp")
    if FORUM_USER in resp.text:
        print("登录成功！")
        return session
    else:
        print("登录失败，可能需要手动验证")
        return session


def create_post(session, title, content):
    """创建新帖子"""
    print(f"\n准备发帖...")
    print(f"标题：{title}")
    print(f"字数：{len(content)}")
    
    # 获取 formhash
    resp = session.get(POST_URL)
    print(f"访问发帖页：{resp.status_code}")
    
    # 提取 formhash (Discuz! 需要)
    import re
    formhash_match = re.search(r'name="formhash" value="([a-zA-Z0-9]+)"', resp.text)
    if not formhash_match:
        print("未找到 formhash，尝试直接发帖...")
        formhash = ""
    else:
        formhash = formhash_match.group(1)
        print(f"Formhash: {formhash}")
    
    # 构建帖子数据
    post_data = {
        'formhash': formhash,
        'subject': title,
        'message': content,
        'special': '0',
        'posttime': '',
        'topicsubmit': 'yes'
    }
    
    # 发送发帖请求
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': POST_URL
    }
    
    resp = session.post(POST_URL, data=post_data, headers=headers)
    print(f"发帖请求：{resp.status_code}")
    
    # 检查发帖结果
    if 'viewthread.php' in resp.url or '发布成功' in resp.text:
        print("发帖成功！")
        print(f"帖子 URL: {resp.url}")
        return resp.url
    else:
        print("发帖可能失败，请检查论坛账户状态")
        # 保存响应以便调试
        with open('post_response.html', 'w', encoding='utf-8') as f:
            f.write(resp.text[:2000])
        print("响应已保存到：post_response.html")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("旺财论坛自动发帖工具")
    print("=" * 60)
    
    # 读取帖子内容
    if not POST_FILE.exists():
        print(f"错误：帖子文件不存在 {POST_FILE}")
        print("请先运行：python forum_post_generator.py")
        return
    
    with open(POST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题 (第一行)
    title = "旺财 MT5 量化交易系统 v2.0 正式发布 - 用亏损换来的血泪经验"
    
    print(f"\n帖子文件：{POST_FILE}")
    print(f"帖子标题：{title}")
    print(f"内容长度：{len(content)} 字符")
    
    # 登录
    session = login()
    
    # 发帖
    post_url = create_post(session, title, content)
    
    if post_url:
        print("\n" + "=" * 60)
        print("发帖完成！")
        print(f"帖子链接：{post_url}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("发帖失败，请手动发布")
        print("文件位置：" + str(POST_FILE))
        print("=" * 60)


if __name__ == "__main__":
    main()
