# -*- coding: utf-8 -*-
"""
旺财 - 交易复盘生成器
功能：生成每日/每周/每月复盘报告
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime, timedelta
import json
import os

# 工作区路径
WORKSPACE = "C:\\Users\\DELL\\.openclaw-autoclaw\\workspace"
TRADING_DIR = os.path.join(WORKSPACE, "trading")
REVIEWS_DIR = os.path.join(TRADING_DIR, "reviews")

def get_today_review_path():
    """获取今日复盘文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(REVIEWS_DIR, "daily", f"{today}.md")

def get_week_review_path():
    """获取本周复盘文件路径"""
    today = datetime.now()
    week_num = today.isocalendar()[1]
    return os.path.join(REVIEWS_DIR, "weekly", f"{today.year}-W{week_num:02d}.md")

def get_month_review_path():
    """获取本月复盘文件路径"""
    today = datetime.now().strftime("%Y-%m")
    return os.path.join(REVIEWS_DIR, "monthly", f"{today}.md")

def create_daily_review():
    """创建每日复盘"""
    path = get_today_review_path()
    
    if os.path.exists(path):
        print(f"⚠️ 今日复盘已存在：{path}")
        return
    
    today = datetime.now()
    
    # 读取模板
    template_path = os.path.join(REVIEWS_DIR, "daily", "template.md")
    if not os.path.exists(template_path):
        print(f"❌ 模板不存在：{template_path}")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换日期
    content = content.replace("YYYY-MM-DD", today.strftime("%Y-%m-%d"))
    content = content.replace("星期 X", f"星期{['一','二','三','四','五','六','日'][today.weekday()]}")
    content = content.replace("交易第 X 天", "第 1 天")  # TODO: 计算实际天数
    
    # 写入文件
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已创建今日复盘：{path}")

def create_week_review():
    """创建每周复盘"""
    path = get_week_review_path()
    
    if os.path.exists(path):
        print(f"⚠️ 本周复盘已存在：{path}")
        return
    
    today = datetime.now()
    week_num = today.isocalendar()[1]
    
    # 读取模板
    template_path = os.path.join(REVIEWS_DIR, "weekly", "template.md")
    if not os.path.exists(template_path):
        print(f"❌ 模板不存在：{template_path}")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换日期
    content = content.replace("YYYY-Www", f"{today.year}-W{week_num:02d}")
    
    # 计算周一起始日期
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    content = content.replace("YYYY-MM-DD ~ YYYY-MM-DD", 
                              f"{monday.strftime('%Y-%m-%d')} ~ {sunday.strftime('%Y-%m-%d')}")
    content = content.replace("交易第 X 周", "第 1 周")  # TODO: 计算实际周数
    
    # 写入文件
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已创建本周复盘：{path}")

def create_month_review():
    """创建每月复盘"""
    path = get_month_review_path()
    
    if os.path.exists(path):
        print(f"⚠️ 本月复盘已存在：{path}")
        return
    
    today = datetime.now()
    
    # 读取模板
    template_path = os.path.join(REVIEWS_DIR, "monthly", "template.md")
    if not os.path.exists(template_path):
        print(f"❌ 模板不存在：{template_path}")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换日期
    content = content.replace("YYYY-MM", today.strftime("%Y-%m"))
    content = content.replace("交易第 X 月", "第 1 月")  # TODO: 计算实际月数
    
    # 写入文件
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已创建本月复盘：{path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='旺财 - 交易复盘生成器')
    parser.add_argument('type', choices=['daily', 'weekly', 'monthly', 'all'],
                        help='复盘类型')
    
    args = parser.parse_args()
    
    print("🎯 旺财复盘生成器")
    print("=" * 50)
    
    if args.type in ['daily', 'all']:
        create_daily_review()
    
    if args.type in ['weekly', 'all']:
        create_week_review()
    
    if args.type in ['monthly', 'all']:
        create_month_review()
    
    print("=" * 50)
    print("完成！")

if __name__ == "__main__":
    main()
