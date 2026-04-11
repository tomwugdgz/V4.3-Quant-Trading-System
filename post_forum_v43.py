"""
论坛自动发帖工具 - duckwolf.cn
版本：1.0
创建：2026-04-10
"""

import requests
from bs4 import BeautifulSoup
import re

class DiscuzBot:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.formhash = None
        
    def login(self):
        """登录论坛"""
        print(f"正在登录：{self.username}@{self.base_url}")
        
        # 获取登录页面
        login_url = f"{self.base_url}/member.php?mod=logging"
        response = self.session.get(login_url)
        
        # 提取 formhash
        formhash_match = re.search(r'name="formhash" value="(\w+)"', response.text)
        if formhash_match:
            self.formhash = formhash_match.group(1)
            print(f"Formhash: {self.formhash}")
        else:
            print("未找到 formhash")
            return False
        
        # 登录
        login_data = {
            'formhash': self.formhash,
            'referer': self.base_url,
            'loginfield': 'username',
            'username': self.username,
            'password': self.password,
            'questionid': '0',
            'answer': '',
            'loginsubmit': 'true',
            'cookietime': '2592000'
        }
        
        response = self.session.post(login_url, data=login_data)
        
        # 检查是否登录成功
        if self.username in response.text:
            print("登录成功！")
            return True
        else:
            print("登录失败")
            return False
    
    def post_thread(self, fid: int, subject: str, message: str):
        """发布新主题"""
        print(f"正在发布主题到版块 {fid}...")
        
        # 获取发帖页面
        post_url = f"{self.base_url}/forum.php?mod=post&action=newthread&fid={fid}"
        response = self.session.get(post_url)
        
        # 更新 formhash
        formhash_match = re.search(r'name="formhash" value="(\w+)"', response.text)
        if formhash_match:
            self.formhash = formhash_match.group(1)
        
        # 发帖数据
        post_data = {
            'formhash': self.formhash,
            'subject': subject,
            'message': message,
            'typeid': '',
            'sortid': '',
            'postsent': 'true',
            'addtrade': '0',
            'postsubmit': 'true'
        }
        
        # 发布
        response = self.session.post(post_url, data=post_data)
        
        # 检查是否发布成功
        if '发表成功' in response.text or 'thread-' in response.url:
            print("发帖成功！")
            # 提取帖子 URL
            thread_match = re.search(r'href="(.+?thread-\d+)', response.text)
            if thread_match:
                thread_url = match.group(1)
                print(f"帖子链接：{thread_url}")
                return thread_url
        else:
            print("发帖失败")
            print(response.text[:500])
            return None
    
    def close(self):
        """关闭会话"""
        self.session.close()


def main():
    # 论坛配置
    base_url = "http://duckwolf.cn"
    username = "store"
    password = "tomwu001"
    
    # 创建机器人
    bot = DiscuzBot(base_url, username, password)
    
    # 登录
    if not bot.login():
        print("登录失败，请检查用户名和密码")
        return
    
    # 读取帖子内容
    with open('forum_post_v43.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 转换 Markdown 为 Discuz 代码（简化版）
    message = content
    message = message.replace('### ', '[b]')
    message = message.replace('## ', '[b][size=4]')
    message = message.replace('# ', '[b][size=5]')
    message = message.replace('**', '[/b]')
    message = message.replace('```', '[code]')
    
    # 发帖
    fid = 54  # 版块 ID
    subject = "MT5 自动交易系统 V4.3 - 从'稳定不赚钱'到'稳定盈利'的架构升级"
    
    thread_url = bot.post_thread(fid, subject, message)
    
    if thread_url:
        print(f"\n帖子已发布：{base_url}/{thread_url}")
    else:
        print("\n发帖失败")
    
    bot.close()


if __name__ == "__main__":
    main()
