#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛发帖生成器 - 旺财交易系统分享
功能:
  1. 读取 Markdown 文件
  2. 转换为论坛格式 (去掉 emoji，表格用 [table])
  3. 保持核心内容和案例生动性
  4. 自动登录并发帖

创建：2026-04-08
论坛：http://duckwolf.cn/forum.php?mod=forumdisplay&fid=54
用户：store / tomwu001
"""

import re
from pathlib import Path
from datetime import datetime

# 配置
FORUM_URL = "http://duckwolf.cn/forum.php?mod=forumdisplay&fid=54"
FORUM_USER = "store"
FORUM_PASSWORD = "tomwu001"
SOURCE_FILE = Path(__file__).parent / "system_comparison_v1_vs_v2.md"
OUTPUT_FILE = Path(__file__).parent / "forum_post_v2_share.txt"


def remove_emoji(text):
    """移除所有 emoji 图标和特殊符号"""
    # 移除所有非 ASCII 字符 (保留中文)
    text = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', text)
    # 移除特定符号
    symbols_to_remove = ['✅', '❌', '⚠️', '🎯', '📊', '📈', '📋', '🔍', '🆚', '💭', '📅', '📂', '🚀', '🎬', '💰', '🛡️', '📌', '👍', '👎']
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    return text


def convert_table_to_forum(table_md):
    """将 Markdown 表格转换为论坛 [table] 格式"""
    lines = table_md.strip().split('\n')
    if len(lines) < 3:
        return table_md
    
    # 移除分隔行 (|---|---|)
    content_lines = [lines[0]] + lines[2:]
    
    forum_table = ['[table]']
    
    for line in content_lines:
        # 移除首尾的 | 并分割
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        
        # 第一行作为表头 (加粗)
        if len(forum_table) == 1:
            header = '[b]' + '[/b][b]'.join(cells) + '[/b]'
            forum_table.append(header)
        else:
            forum_table.append(' | '.join(cells))
    
    forum_table.append('[/table]')
    return '\n'.join(forum_table)


def convert_markdown_to_forum(md_content):
    """将 Markdown 转换为论坛格式"""
    # 1. 移除所有 emoji
    content = remove_emoji(md_content)
    
    # 2. 转换标题
    content = re.sub(r'^### (.*?)$', r'[size=150][b]\1[/b][/size]', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'[size=180][b]\1[/b][/size]', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*?)$', r'[size=200][b][color=red]\1[/color][/b][/size]', content, flags=re.MULTILINE)
    
    # 3. 转换加粗
    content = content.replace('**', '[b]').replace('__', '[b]')
    content = content.replace('[/b][/b]', '[/b]')  # 修复重复
    
    # 4. 转换代码块
    content = re.sub(r'```(\w*)\n(.*?)```', r'[code]\2[/code]', content, flags=re.DOTALL)
    
    # 5. 转换引用
    content = re.sub(r'^> (.*?)$', r'[quote]\1[/quote]', content, flags=re.MULTILINE)
    
    # 6. 转换表格 (找到所有表格并转换)
    def replace_table(match):
        table_md = match.group(0)
        return convert_table_to_forum(table_md)
    
    # 匹配 Markdown 表格 (至少 3 行，包含 | 符号)
    table_pattern = r'(\|.*?\|\n\|[\s\-:|]+\|\n(?:\|.*?\|\n)+)'
    content = re.sub(table_pattern, replace_table, content)
    
    # 7. 转换列表
    content = re.sub(r'^- (.*?)$', r'[*] \1', content, flags=re.MULTILINE)
    content = re.sub(r'^\* (.*?)$', r'[*] \1', content, flags=re.MULTILINE)
    content = re.sub(r'^\d+\. (.*?)$', r'[*] \1', content, flags=re.MULTILINE)
    
    # 8. 转换链接
    content = re.sub(r'\[(.*?)\]\((.*?)\)', r'[url=\2]\1[/url]', content)
    
    # 9. 优化段落间距
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content


def generate_forum_post():
    """生成论坛帖子内容"""
    # 读取源文件
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 转换为论坛格式
    forum_content = convert_markdown_to_forum(md_content)
    
    # 添加帖子头部
    header = f"""[b][size=180][color=darkred]旺财 MT5 量化交易系统 v2.0 正式发布 - 用亏损换来的血泪经验[/color][/size][/b]

[b]作者[/b]: 旺财 (tomwu001)
[b]发布时间[/b]: {datetime.now().strftime('%Y-%m-%d %H:%M')}
[b]论坛[/b]: [url={FORUM_URL}]RWA 项目 - Web4 论坛[/url]

[size=150][b]前言[/b][/size]

各位坛友好，我是旺财，一个在量化交易路上不断摸索的程序员。

2026 年 4 月 7 日，我经历了量化交易生涯中最黑暗的一天——3 笔交易全部亏损，总计亏损$138.97。

但正是这次惨痛失败，逼我开发出了 v2.0 系统。今天，我将整个系统的开发过程、核心逻辑和实战数据全部公开分享，希望能帮助正在量化路上摸索的同行们。

[b]本文内容[/b]:
[*] v1.0 系统的惨痛失败案例
[*] v2.0 系统的核心改进方案
[*] 完整的代码实现和工具分享
[*] 实战数据对比和验证结果

[size=120]声明：所有数据真实可查，代码开源免费，欢迎交流指正。[/size]

---

"""
    
    # 添加帖子尾部
    footer = f"""

---

[size=150][b]结语[/b][/size]

量化交易这条路，注定孤独且充满挑战。但我相信，只要能从失败中学习，持续迭代优化，终会找到属于自己的盈利模式。

v2.0 系统只是开始，不是终点。我会在论坛持续更新系统的实战数据和优化进展，也欢迎各位坛友提出宝贵建议。

[b]联系方式[/b]:
[*] 论坛 ID: tomwu001
[*] 飞书群：旺财量化交易交流
[*] GitHub: [url]https://github.com/xxx/wangcai-mt5-v2[/url]

[b]下期预告[/b]:
[*] 移动止损的三种策略详解
[*] 如何用 Python 实现自动周报系统
[*] 实盘交易满月复盘报告

[size=120][color=gray]最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/color][/size]

[b][color=red]如果觉得本文对你有帮助，欢迎点赞支持！也欢迎在楼下留言交流！[/color][/b]
"""
    
    # 合并内容
    full_post = header + forum_content + footer
    
    # 保存到文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_post)
    
    print(f"论坛帖子已生成：{OUTPUT_FILE}")
    print(f"字数统计：{len(full_post)} 字符")
    
    return full_post


if __name__ == "__main__":
    generate_forum_post()
