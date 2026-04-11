# -*- coding: utf-8 -*-
"""
安装交易必要库
"""
import subprocess
import sys

packages = [
    # 核心数据处理
    'pandas',
    'numpy',
    
    # 图表绘制
    'matplotlib',
    'plotly',
    
    # 技术分析
    'ta-lib',
    'backtrader',
    
    # 数据库
    'sqlalchemy',
    
    # HTTP 请求
    'requests',
    
    # MT5
    'MetaTrader5',
]

print("=" * 80)
print("安装交易必要库")
print("=" * 80)

for pkg in packages:
    print(f"\n安装 {pkg}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
        print(f"✅ {pkg} 安装成功")
    except Exception as e:
        print(f"❌ {pkg} 安装失败：{e}")

print("\n" + "=" * 80)
print("安装完成")
print("=" * 80)
