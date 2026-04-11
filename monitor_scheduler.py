"""
72 小时交易监控 - 主调度器
每小时执行监控并发送飞书报告
"""

import subprocess
import schedule
import time
from datetime import datetime
import os

def run_monitor():
    """执行监控脚本"""
    print(f"\n{'='*70}")
    print(f"⏰ 执行定时监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # 运行监控脚本
    result = subprocess.run([
        r'C:\Users\Dell\AppData\Local\Programs\Python\Python37\python.exe',
        r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\hourly_monitor.py'
    ], capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("✅ 监控报告生成成功")
        print(result.stdout)
    else:
        print(f"❌ 监控报告生成失败: {result.stderr}")

if __name__ == '__main__':
    print("🚀 72 小时交易监控系统启动")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("监控频率：每小时一次")
    print("按 Ctrl+C 停止监控")
    
    # 立即执行一次
    run_monitor()
    
    # 每小时执行
    schedule.every().hour.do(run_monitor)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次
