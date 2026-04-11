# -*- coding: utf-8 -*-
"""
Python 3.11 安装脚本
"""
import sys
import subprocess
import os

print("=" * 80)
print("Python 环境升级检查")
print("=" * 80)

# 检查当前 Python 版本
print(f"\n当前 Python: {sys.version}")
print(f"版本：{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# 需要安装的包
packages = [
    # 核心库
    'pandas',
    'numpy',
    'matplotlib',
    'plotly',
    
    # 技术分析
    'ta-lib',
    'backtrader',
    
    # 数据库
    'sqlite3',
    'sqlalchemy',
    'pymysql',
    
    # 数据处理
    'requests',
    'json5',
    
    # MT5 (需要单独安装)
    # 'MetaTrader5',
]

print("\n需要安装的包:")
for pkg in packages:
    print(f"  - {pkg}")

print("\n" + "=" * 80)
