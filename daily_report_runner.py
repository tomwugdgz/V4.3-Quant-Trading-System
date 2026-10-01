"""v5.20 每日报告运行器
- 20:00 自动跑 daily_review.py
- 生成 markdown 摘要到 reports/evolution/YYYY-MM-DD_日终报告.md
- 由 Windows Task Scheduler 每天 20:00 调用
"""
import sys
import os
import io
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 强制 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

WORKSPACE = Path(r"C:\Users\DELL\.openclaw-autoclaw\workspace\trading")
PYTHON = r"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
DAILY_REVIEW = WORKSPACE / "daily_review.py"
EVOLUTION_DIR = WORKSPACE / "reports" / "evolution"
EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    log(f"日终报告 v5.20 - {today}")

    # 1. 跑 daily_review.py
    result = subprocess.run(
        [PYTHON, str(DAILY_REVIEW)],
        capture_output=True, text=True, timeout=120,
        encoding='utf-8', errors='replace'
    )

    if result.returncode != 0:
        log(f"  [ERR] daily_review.py 失败: {result.stderr}")
        return

    # 2. 读 daily_review.json
    review_json = WORKSPACE / "daily_review.json"
    if not review_json.exists():
        log("  [ERR] daily_review.json 未生成")
        return

    with open(review_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 3. 生成 markdown 摘要
    md_path = EVOLUTION_DIR / f"{today}_日终报告.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {today} 日终报告\n\n")
        f.write(f"> 自动生成 · daily_report_runner v5.20\n\n")
        f.write(f"---\n\n")
        f.write(f"## 账户状态\n\n")
        f.write(f"- 余额: **${data.get('balance', 'NA'):.2f}**\n")
        f.write(f"- 净值: ${data.get('equity', 'NA'):.2f}\n")
        f.write(f"- 持仓: {data.get('positions', 0)}\n\n")
        f.write(f"## 今日表现\n\n")
        f.write(f"- 交易笔数: {data.get('total_trades', 0)}\n")
        f.write(f"- 胜率: {data.get('win_rate', 0):.1f}%\n")
        f.write(f"- 日 P/L: **${data.get('daily_pnl', 0):.2f}**\n\n")
        f.write(f"---\n\n")
        f.write(f"_由旺财 自动生成 {datetime.now()}_\n")

    log(f"  报告: {md_path}")


if __name__ == "__main__":
    main()