#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旺财 <-> 来福 消息同步脚本 (Windows 侧)

功能:
1. 写入消息到 inbox/ (旺财 -> 来福)
2. 扫描 outbox/ 读取来福回复
3. 更新 STATUS.md

用法:
  python hermes_sync.py send --type sync --message "消息内容"
  python hermes_sync.py check
  python hermes_sync.py status
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 配置
SHARED_BASE = Path(r"D:\LLM-Wiki\trading\hermes-messages")
INBOX = SHARED_BASE / "inbox"
OUTBOX = SHARED_BASE / "outbox"
SHARED = SHARED_BASE / "shared"
STATUS = SHARED / "STATUS.md"

def generate_id():
    """生成消息 ID"""
    now = datetime.now()
    return f"msg_{now.strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"

def send_message(msg_type, message, title=None):
    """发送消息到 inbox/"""
    now = datetime.now()
    msg_id = generate_id()
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{msg_type}_{msg_id[-3:]}.md"
    filepath = INBOX / filename

    frontmatter = f"""---
protocol: wangcai-hermes-sync/v1
from: wangcai
to: hermes
timestamp: {now.isoformat()}
type: {msg_type}
id: {msg_id}
status: pending
---
"""

    title = title or f"消息 - {msg_type}"
    body = f"# {title}\n\n{message}\n"

    content = frontmatter + body
    filepath.write_text(content, encoding='utf-8')
    print(f"消息已发送: {filepath}")
    print(f"消息 ID: {msg_id}")
    return msg_id

def check_outbox():
    """扫描 outbox/ 读取来福回复"""
    replies = list(OUTBOX.glob("*.md"))
    if not replies:
        print("没有新回复。")
        return []

    replies.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    print(f"找到 {len(replies)} 条回复：\n")

    results = []
    for reply in replies[:10]:
        content = reply.read_text(encoding='utf-8')
        # Parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                header = parts[1].strip()
                body = parts[2].strip()
                print(f"=== {reply.name} ===")
                print(f"Header:\n{header}\n")
                print(f"Body:\n{body[:500]}...")
                print()
                results.append({"file": str(reply), "header": header, "body": body})

    return results

def update_status():
    """读取并显示当前状态"""
    if STATUS.exists():
        content = STATUS.read_text(encoding='utf-8')
        print(content)
    else:
        print("STATUS.md 不存在。")

def main():
    parser = argparse.ArgumentParser(description="旺财-来福消息同步")
    subparsers = parser.add_subparsers(dest="command")

    # send
    send_parser = subparsers.add_parser("send", help="发送消息")
    send_parser.add_argument("--type", default="sync", help="消息类型: sync, command, query, alert, heartbeat")
    send_parser.add_argument("--message", required=True, help="消息内容")
    send_parser.add_argument("--title", help="消息标题")

    # check
    subparsers.add_parser("check", help="检查来福回复")

    # status
    subparsers.add_parser("status", help="查看状态")

    args = parser.parse_args()

    if args.command == "send":
        send_message(args.type, args.message, args.title)
    elif args.command == "check":
        check_outbox()
    elif args.command == "status":
        update_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
