#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旺财推荐股 - 10 步筛选系统
版本：V1.0
创建：2026-04-12
功能：成长型股票筛选 + 综合评分 + 推荐池
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==================== 配置参数 ====================

class Config:
    """筛选参数配置"""
    
    # 1. 毛利率
    MIN_GROSS_MARGIN = 20.0  # 最低 20%
    
    # 2. 股本 (亿股)
    MAX_TOTAL_SHARE = 5.0  # 最大 5 亿股
    
    # 3. ROE
    MIN_ROE = 5.0  # 最低 5%
    
    # 4. 主营业务占比
    MIN_MAIN_BUSINESS_RATIO = 70.0  # 最低 70%
    
    # 5. 股价位置
    MA_PERIODS = [20, 60, 120]  # 均线周期
    MAX_PRICE_MA_RATIO = 1.1  # 股价/均线 < 1.1
    
    # 6. 行业壁垒 (手动评分)
    MIN_BARRIER_SCORE = 3  # 最低 3 星
    
    # 7. 上涨空间
    MIN_UPSIDE = 20.0  # 最低 20%
    
    # 8. 稀缺性 (手动评分)
    MIN_RARITY_SCORE = 4  # 最低 4 星
    
    # 9. 股东架构
    PREFERRED_SHAREHOLDER_TYPES = ['创始人', '产业资本', '国资']
    
    # 10. 派息率
    MIN_DIVIDEND_YIELD = 2.0  # 最低股息率 2%


# ==================== 数据获取 ====================

def get_stock_list():
    """Get A-share stock list"""
    print("Getting A-share stock list...")
    try:
        df = ak.stock_info_a_code_name()
        return df
    except Exception as e:
        print(f"Error getting stock list: {e}")
        return None


def get_stock_basic_info(symbol):
    """获取股票基本信息"""
    try:
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        df = df[df['代码'] == symbol]
        if len(df) == 0:
            return None
        return df.iloc[0]
    except Exception as e:
        print(f"获取 {symbol} 基本信息失败：{e}")
        return None


def get_financial_data(symbol):
    """获取财务数据"""
    try:
        # 获取 ROE 数据
        df_roe = ak.stock_financial_analysis_indicator(symbol=symbol)
        
        # 获取利润表
        df_income = ak.stock_financial_report_sina(symbol=symbol, flag="利润表")
        
        return {
            'roe': df_roe,
            'income': df_income
        }
    except Exception as e:
        print(f"获取 {symbol} 财务数据失败：{e}")
        return None


def get_stock_dividend(symbol):
    """获取股票分红数据"""
    try:
        df = ak.stock_dividend_cont(symbol=symbol)
        return df
    except Exception as e:
        print(f"获取 {symbol} 分红数据失败：{e}")
        return None


# ==================== 筛选逻辑 ====================

def calculate_score(stock_data, config):
    """
    计算综合评分 (100 分制)
    """
    score = 0
    details = {}
    
    # 1. 毛利率 (10 分)
    gross_margin = stock_data.get('gross_margin', 0)
    if gross_margin >= 40:
        score += 10
        details['毛利率'] = f"{gross_margin:.1f}% ⭐⭐⭐⭐⭐"
    elif gross_margin >= 30:
        score += 8
        details['毛利率'] = f"{gross_margin:.1f}% ⭐⭐⭐⭐"
    elif gross_margin >= 20:
        score += 6
        details['毛利率'] = f"{gross_margin:.1f}% ⭐⭐⭐"
    else:
        details['毛利率'] = f"{gross_margin:.1f}% ❌"
        return 0, details  # 淘汰
    
    # 2. 股本 (10 分)
    total_share = stock_data.get('total_share', 999)
    if total_share < 1:
        score += 10
        details['股本'] = f"{total_share:.1f}亿 ⭐⭐⭐⭐⭐"
    elif total_share < 3:
        score += 8
        details['股本'] = f"{total_share:.1f}亿 ⭐⭐⭐⭐"
    elif total_share < 5:
        score += 6
        details['股本'] = f"{total_share:.1f}亿 ⭐⭐⭐"
    else:
        details['股本'] = f"{total_share:.1f}亿 ❌"
        return 0, details  # 淘汰
    
    # 3. ROE (15 分) ⭐ 重点关注
    roe = stock_data.get('roe', 0)
    if roe >= 20:
        score += 15
        details['ROE'] = f"{roe:.1f}% ⭐⭐⭐⭐⭐"
    elif roe >= 15:
        score += 12
        details['ROE'] = f"{roe:.1f}% ⭐⭐⭐⭐"
    elif roe >= 10:
        score += 8
        details['ROE'] = f"{roe:.1f}% ⭐⭐⭐"
    elif roe >= 5:
        score += 4
        details['ROE'] = f"{roe:.1f}% ⭐⭐"
    else:
        details['ROE'] = f"{roe:.1f}% ❌"
        return 0, details  # 淘汰
    
    # 4. 主营业务占比 (10 分)
    main_ratio = stock_data.get('main_ratio', 0)
    if main_ratio >= 90:
        score += 10
        details['主营占比'] = f"{main_ratio:.1f}% ⭐⭐⭐⭐⭐"
    elif main_ratio >= 70:
        score += 8
        details['主营占比'] = f"{main_ratio:.1f}% ⭐⭐⭐⭐"
    elif main_ratio >= 50:
        score += 4
        details['主营占比'] = f"{main_ratio:.1f}% ⭐⭐"
    else:
        details['主营占比'] = f"{main_ratio:.1f}% ❌"
        return 0, details  # 淘汰
    
    # 5. 股价位置 (15 分) ⭐ 重点关注
    price_ma_ratio = stock_data.get('price_ma_ratio', 999)
    if price_ma_ratio <= 1.05:
        score += 15
        details['股价位置'] = f"MA 附近 ⭐⭐⭐⭐⭐"
    elif price_ma_ratio <= 1.1:
        score += 12
        details['股价位置'] = f"MA 附近 ⭐⭐⭐⭐"
    elif price_ma_ratio <= 1.2:
        score += 8
        details['股价位置'] = f"略高 ⭐⭐⭐"
    else:
        details['股价位置'] = f"过高 ❌"
        return 0, details  # 淘汰
    
    # 6. 行业壁垒 (10 分)
    barrier = stock_data.get('barrier_score', 0)
    if barrier >= 5:
        score += 10
        details['行业壁垒'] = f"{barrier}星 ⭐⭐⭐⭐⭐"
    elif barrier >= 4:
        score += 8
        details['行业壁垒'] = f"{barrier}星 ⭐⭐⭐⭐"
    elif barrier >= 3:
        score += 6
        details['行业壁垒'] = f"{barrier}星 ⭐⭐⭐"
    else:
        details['行业壁垒'] = f"{barrier}星 ❌"
        return 0, details  # 淘汰
    
    # 7. 上涨空间 (10 分)
    upside = stock_data.get('upside', 0)
    if upside >= 50:
        score += 10
        details['上涨空间'] = f"{upside:.1f}% ⭐⭐⭐⭐⭐"
    elif upside >= 30:
        score += 8
        details['上涨空间'] = f"{upside:.1f}% ⭐⭐⭐⭐"
    elif upside >= 20:
        score += 6
        details['上涨空间'] = f"{upside:.1f}% ⭐⭐⭐"
    else:
        details['上涨空间'] = f"{upside:.1f}% ❌"
        return 0, details  # 淘汰
    
    # 8. 稀缺性 (10 分)
    rarity = stock_data.get('rarity_score', 0)
    if rarity >= 5:
        score += 10
        details['稀缺性'] = f"{rarity}星 ⭐⭐⭐⭐⭐"
    elif rarity >= 4:
        score += 8
        details['稀缺性'] = f"{rarity}星 ⭐⭐⭐⭐"
    elif rarity >= 3:
        score += 4
        details['稀缺性'] = f"{rarity}星 ⭐⭐"
    else:
        details['稀缺性'] = f"{rarity}星 ❌"
        return 0, details  # 淘汰
    
    # 9. 股东架构 (10 分)
    shareholder = stock_data.get('shareholder_type', '')
    if shareholder in ['创始人控股', '产业资本控股']:
        score += 10
        details['股东架构'] = f"{shareholder} ⭐⭐⭐⭐⭐"
    elif shareholder in ['国资控股', '员工持股']:
        score += 8
        details['股东架构'] = f"{shareholder} ⭐⭐⭐⭐"
    elif shareholder in ['混合架构']:
        score += 6
        details['股东架构'] = f"{shareholder} ⭐⭐⭐"
    else:
        details['股东架构'] = f"{shareholder} ⭐⭐"
    
    # 10. 派息率 (10 分) ⭐ 重点关注
    dividend_yield = stock_data.get('dividend_yield', 0)
    if dividend_yield >= 5:
        score += 10
        details['派息率'] = f"{dividend_yield:.1f}% ⭐⭐⭐⭐⭐"
    elif dividend_yield >= 3:
        score += 8
        details['派息率'] = f"{dividend_yield:.1f}% ⭐⭐⭐⭐"
    elif dividend_yield >= 2:
        score += 6
        details['派息率'] = f"{dividend_yield:.1f}% ⭐⭐⭐"
    elif dividend_yield > 0:
        score += 4
        details['派息率'] = f"{dividend_yield:.1f}% ⭐⭐"
    else:
        details['派息率'] = f"{dividend_yield:.1f}% ⭐"
    
    return score, details


def filter_stocks(stock_list, config):
    """
    Execute 10-step screening
    """
    results = []
    total = len(stock_list)
    
    print(f"\nStarting screening {total} stocks...")
    print("=" * 60)
    
    for idx, row in stock_list.iterrows():
        symbol = row.get('代码', '')
        name = row.get('名称', '')
        
        if not symbol:
            continue
        
        print(f"\n[{idx+1}/{total}] {symbol} {name}")
        
        # 获取数据
        basic = get_stock_basic_info(symbol)
        if basic is None:
            continue
        
        # 构建股票数据
        stock_data = {
            'symbol': symbol,
            'name': name,
            'price': basic.get('最新价', 0),
            'gross_margin': 25.0,  # 示例值，实际从财报获取
            'total_share': basic.get('总市值', 0) / basic.get('最新价', 1) / 100000000,  # 亿股
            'roe': 10.0,  # 示例值
            'main_ratio': 80.0,  # 示例值
            'price_ma_ratio': 1.05,  # 示例值
            'barrier_score': 4,  # 示例值
            'upside': 30.0,  # 示例值
            'rarity_score': 4,  # 示例值
            'shareholder_type': '创始人控股',  # 示例值
            'dividend_yield': 3.0,  # 示例值
        }
        
        # 计算评分
        score, details = calculate_score(stock_data, config)
        
        if score >= 60:  # 60+ score enters recommendation pool
            stock_data['score'] = score
            stock_data['details'] = details
            results.append(stock_data)
            print(f"  PASS: {score} points")
        else:
            print(f"  FAIL: {score} points")
        
        # Demo mode: only screen first 5 stocks
        if idx >= 5:
            print("\nDemo mode: only screening first 5 stocks")
            break
    
    return results


# ==================== 报告生成 ====================

def generate_report(results, output_path='wangcai_stock_report.md'):
    """
    Generate recommendation report
    """
    # 排序
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    
    # 分级
    strong_buy = [r for r in results if r['score'] >= 90]
    buy = [r for r in results if 80 <= r['score'] < 90]
    watch = [r for r in results if 70 <= r['score'] < 80]
    
    # 生成报告
    report = []
    report.append("# Wangcai Stock Recommendation Report")
    report.append(f"\n**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"\n**Total Screened**: {len(results)} stocks")
    report.append("\n" + "=" * 60 + "\n")
    
    # 强烈推荐
    if strong_buy:
        report.append("## Strong Buy (90-100 points)\n")
        for i, stock in enumerate(strong_buy, 1):
            report.append(f"### #{i} {stock['name']} ({stock['symbol']})")
            report.append(f"**Score**: {stock['score']} points\n")
            report.append("**Key Metrics**:")
            for k, v in stock['details'].items():
                report.append(f"- {k}: {v}")
            report.append("\n---\n")
    
    # 推荐
    if buy:
        report.append("## Buy (80-89 points)\n")
        for i, stock in enumerate(buy, 1):
            report.append(f"### #{i} {stock['name']} ({stock['symbol']})")
            report.append(f"**Score**: {stock['score']} points\n")
            report.append("---\n")
    
    # 关注
    if watch:
        report.append("## Watch (70-79 points)\n")
        for i, stock in enumerate(watch, 1):
            report.append(f"- {stock['name']} ({stock['symbol']}) - {stock['score']} points")
        report.append("\n")
    
    # 市场观点
    report.append("\n## Market View\n")
    report.append("- **Market Trend**: Consolidation, watch volume")
    report.append("- **Sector Rotation**: High dividend + Growth stocks")
    report.append("- **Risk Warning**: Geopolitical + Earnings season")
    report.append("\n" + "=" * 60 + "\n")
    report.append("**Wangcai + Laifu = Fortune & Luck**")
    
    # 保存报告
    content = '\n'.join(report)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nReport saved: {output_path}")
    return content


# ==================== 主程序 ====================

def main():
    """主程序"""
    print("=" * 60)
    print("Wangcai Stock Screener V1.0")
    print("=" * 60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取股票列表
    stock_list = get_stock_list()
    if stock_list is None or len(stock_list) == 0:
        print("❌ 获取股票列表失败")
        return
    
    print(f"Got {len(stock_list)} stocks")
    
    # 2. 执行筛选
    config = Config()
    results = filter_stocks(stock_list, config)
    
    # 3. 生成报告
    if results:
        report = generate_report(results)
        print("\n" + "=" * 60)
        print("Screening Complete!")
        print(f"Recommended: {len(results)} stocks")
        print(f"Strong Buy (90+): {len([r for r in results if r['score']>=90])} stocks")
        print(f"Buy (80-89): {len([r for r in results if 80<=r['score']<90])} stocks")
        print(f"Watch (70-79): {len([r for r in results if 70<=r['score']<80])} stocks")
    else:
        print("\nNo stocks matched criteria")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
