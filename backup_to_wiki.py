#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4.3 备份脚本 - 将核心文件打包备份到 LLM Wiki 目录
用法: python backup_to_wiki.py
"""

import os
import sys
import shutil
import json
from datetime import datetime
from pathlib import Path

# 配置
SOURCE_TRADING = Path(r"C:\Users\DELL\.openclaw-autoclaw\workspace\trading")
SOURCE_WORKSPACE = Path(r"C:\Users\DELL\.openclaw-autoclaw\workspace")
BACKUP_DIR = Path(r"D:\LLM-Wiki\trading\backups")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# 核心交易文件清单（精选，排除一次性/测试/历史脚本）
CORE_TRADING_FILES = [
    # 核心系统
    "check_account.py",
    "find_opportunity.py",
    "find_opportunity.py.bak",
    "find_opportunity_v2.py",
    "auto_monitor.py",
    "auto_monitor_readme.md",
    "risk_manager_v2.py",
    "monitor_scheduler.py",
    "hourly_monitor.py",
    "daily_report.py",
    "send_feishu_report.py",
    # 交易执行
    "execute_trade.py",
    "close_by_symbol.py",
    "close_all_simple.py",
    "modify_trailing_stop.py",
    "position_report.py",
    # 信号扫描
    "market_scan.py",
    "scan_all_signals.py",
    "scan_all_crypto.py",
    "scan_weekend.py",
    "find_crypto_signal.py",
    "hourly_update.py",
    "today_deals.py",
    # 市场分析
    "analyze_market.py",
    "analyze_fx.py",
    "analyze_fx_alpha.py",
    "analyze_crypto.py",
    "analyze_positions.py",
    "analyze_monitor_log.py",
    "decision_analysis.py",
    # 账户相关
    "check_account_balance.py",
    "check_positions.py",
    "check_market_status.py",
    "check_history.py",
    "check_daily_summary.py",
    "check_weekly_deals.py",
    "trade_report.py",
    # MT5 工具
    "mt5_check.py",
    "mt5_scan.py",
    "fix_mt5_connection.py",
    "mt5-account-status.json",
    # 数据/数据库
    "create_database.py",
    "check_db.py",
    "query_db.py",
    "trading.db",
    # 日志/状态
    "trade_log.json",
    "trade_history.json",
    "monitor_log.json",
    "72h_plan_config.md",
    "72h_plan_results.json",
    "72h_plan_summary.md",
    # V4.3 文档
    "SYSTEM.md",
    "DEPLOYMENT.md",
    "DEPLOYMENT_CHECKLIST.md",
    "tools_guide.md",
    "monitor_setup.md",
    "deployment_guide_v2.md",
    "optimization_report_v2.md",
    "system_comparison_v1_vs_v2.md",
    "UPGRADE_PLAN.md",
    "UPGRADE_COMPLETE.md",
    "BACKUP_SUMMARY.md",
    "first_trade_confirmation.md",
    "monthly_report_2026-04.md",
    "weekly_report_config.md",
    # 配置文件
    ".gitignore",
    "requirements.txt",
    "README.md",
]

# Workspace 进化文件
WORKSPACE_FILES = [
    # 核心身份文件
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "USER.md",
    "IDENTITY.md",
    "MEMORY.md",
    "HEARTBEAT.md",
]

def copy_with_utf8(src, dst):
    """复制文件，确保目录存在"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"  [WARN] 跳过 {src.name}: {e}")
        return False

def backup_trading_files():
    """备份核心交易文件"""
    print("\n[1/3] 备份核心交易文件...")
    dest = BACKUP_DIR / TIMESTAMP / "trading_core"
    dest.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    skipped = 0
    
    for filename in CORE_TRADING_FILES:
        src = SOURCE_TRADING / filename
        if src.exists():
            copy_with_utf8(src, dest / filename)
            copied += 1
        else:
            skipped += 1
    
    print(f"  已复制: {copied} 个文件, 跳过: {skipped} 个 (不存在)")
    return copied

def backup_workspace_files():
    """备份 workspace 进化文件"""
    print("\n[2/3] 备份 Workspace 进化文件...")
    dest = BACKUP_DIR / TIMESTAMP / "workspace_evolved"
    dest.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    
    # 根目录文件
    for filename in WORKSPACE_FILES:
        src = SOURCE_WORKSPACE / filename
        if src.exists():
            copy_with_utf8(src, dest / filename)
            copied += 1
            print(f"  + {filename}")
    
    # memory 目录
    memory_src = SOURCE_WORKSPACE / "memory"
    memory_dest = dest / "memory"
    if memory_src.exists():
        shutil.copytree(memory_src, memory_dest, dirs_exist_ok=True)
        memory_count = sum(1 for _ in memory_src.rglob("*") if _.is_file())
        copied += memory_count
        print(f"  + memory/ 目录 ({memory_count} 个文件)")
    
    # scene_blocks 目录
    scene_src = SOURCE_WORKSPACE / "scene_blocks"
    if not scene_src.exists():
        # 检查是否在 memory-tdai 下
        scene_src = Path(r"C:\Users\DELL\.openclaw-autoclaw\memory-tdai") / "scene_blocks"
    scene_dest = dest / "scene_blocks"
    if scene_src.exists():
        shutil.copytree(scene_src, scene_dest, dirs_exist_ok=True)
        scene_count = sum(1 for _ in scene_src.rglob("*") if _.is_file())
        copied += scene_count
        print(f"  + scene_blocks/ 目录 ({scene_count} 个文件)")
    
    print(f"  已复制: {copied} 个文件/目录")
    return copied

def create_zip():
    """打包成 zip"""
    print("\n[3/3] 创建 zip 压缩包...")
    base_dir = BACKUP_DIR / TIMESTAMP
    zip_path = BACKUP_DIR / f"V4.3_backup_{TIMESTAMP}"
    
    try:
        shutil.make_archive(str(zip_path), 'zip', base_dir)
        zip_size = os.path.getsize(str(zip_path) + ".zip")
        size_mb = zip_size / (1024 * 1024)
        print(f"  打包完成: {zip_path}.zip ({size_mb:.1f} MB)")
        return str(zip_path) + ".zip"
    except Exception as e:
        print(f"  [WARN] zip 失败: {e}")
        print(f"  文件已保留在: {base_dir}")
        return str(base_dir)

def main():
    print("=" * 60)
    print(f"V4.3 备份脚本")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {BACKUP_DIR}")
    print("=" * 60)
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    t1 = backup_trading_files()
    t2 = backup_workspace_files()
    zip_path = create_zip()
    
    print("\n" + "=" * 60)
    print(f"备份完成！")
    print(f"  交易文件: {t1} 个")
    print(f"  进化文件: {t2} 个")
    print(f"  压缩包: {zip_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
