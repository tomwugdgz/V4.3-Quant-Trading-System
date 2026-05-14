#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旺财选股 - AKShare 数据接入
功能：获取单只股票完整数据 + 10 步筛选评分
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import time

def get_stock_info_002188():
    """获取 002188 中天服务完整数据"""
    
    print("=" * 60)
    print("Wangcai Stock Analysis - 002188")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 获取实时行情
    print("1. Getting real-time quote...")
    try:
        df_quote = ak.stock_zh_a_spot_em()
        stock_002188 = df_quote[df_quote['代码'] == '002188']
        
        if len(stock_002188) > 0:
            quote = stock_002188.iloc[0]
            print(f"   Stock Name: {quote['名称']}")
            print(f"   Current Price: {quote['最新价']}")
            print(f"   Change: {quote['涨跌幅']}%")
            print(f"   Volume: {quote['成交量']}")
            print(f"   Turnover: {quote['成交额']}")
            print(f"   Market Cap: {quote['总市值']}")
            print(f"   PE Ratio: {quote['市盈率 - 动态']}")
            print(f"   PB Ratio: {quote['市净率']}")
        else:
            print("   Stock not found!")
            return None
    except Exception as e:
        print(f"   Error getting quote: {e}")
        return None
    
    print()
    
    # 2. 获取财务指标
    print("2. Getting financial indicators...")
    try:
        df_finance = ak.stock_financial_analysis_indicator(symbol="002188")
        print(f"   Data rows: {len(df_finance)}")
        print(df_finance.head(10))
    except Exception as e:
        print(f"   Error getting finance data: {e}")
    
    print()
    
    # 3. 获取利润表
    print("3. Getting income statement...")
    try:
        df_income = ak.stock_financial_report_sina(symbol="002188", flag="利润表")
        print(f"   Data rows: {len(df_income)}")
        print(df_income.head())
    except Exception as e:
        print(f"   Error getting income statement: {e}")
    
    print()
    
    # 4. 获取分红数据
    print("4. Getting dividend history...")
    try:
        df_dividend = ak.stock_dividend_cont(symbol="002188")
        print(f"   Dividend records: {len(df_dividend)}")
        if len(df_dividend) > 0:
            print(df_dividend.head())
    except Exception as e:
        print(f"   Error getting dividend data: {e}")
    
    print()
    
    # 5. 获取十大股东
    print("5. Getting top 10 shareholders...")
    try:
        df_shareholders = ak.stock_hold_control_cninfo(symbol="002188")
        print(f"   Shareholder records: {len(df_shareholders)}")
        if len(df_shareholders) > 0:
            print(df_shareholders.head())
    except Exception as e:
        print(f"   Error getting shareholder data: {e}")
    
    print()
    
    # 6. 获取股本信息
    print("6. Getting share capital info...")
    try:
        df_capital = ak.stock_info_1000(symbol="002188")
        print(f"   Capital info: {df_capital}")
    except Exception as e:
        print(f"   Error getting capital info: {e}")
    
    print()
    print("=" * 60)
    print("Data collection complete!")
    print("=" * 60)


if __name__ == '__main__':
    get_stock_info_002188()
