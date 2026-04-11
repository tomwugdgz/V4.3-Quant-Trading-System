# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import MetaTrader5 as mt5
import datetime
import numpy as np
import pandas as pd

# 初始化连接
if not mt5.initialize():
    print("MT5 初始化失败")
    quit()

# 主要货币对
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'BTCUSD', 'XAUUSD', 'ETHUSD']

print('=' * 80)
print('旺财量化 - 市场环境分析报告')
print('=' * 80)
print(f'报告时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 80)
print('')

# 获取账户信息
account = mt5.account_info()
print(f'【账户状态】')
print(f'  余额：${account.balance:.2f}')
print(f'  净值：${account.equity:.2f}')
print(f'  可用保证金：${getattr(account, "free_margin", account.margin_free):.2f}')
print(f'  保证金水平：{account.margin_level:.2f}%')
print('')

# 1. 波动率分析 (上周数据)
print('【1. 上周波动率分析】')
print('-' * 80)

def calculate_volatility(symbol, days=7):
    """计算指定天数的波动率"""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, days + 10)
    if rates is None or len(rates) < days:
        return None
    
    df = pd.DataFrame(rates)
    df['daily_range'] = (df['high'] - df['low']) / df['close'] * 100  # 日波动百分比
    df['daily_change'] = abs(df['close'].pct_change()) * 100
    
    last_7_days = df.tail(days)
    avg_volatility = last_7_days['daily_range'].mean()
    max_volatility = last_7_days['daily_range'].max()
    min_volatility = last_7_days['daily_range'].min()
    
    return {
        'avg_vol': avg_volatility,
        'max_vol': max_volatility,
        'min_vol': min_volatility,
        'trend': last_7_days['close'].iloc[-1] - last_7_days['close'].iloc[0]
    }

volatility_data = []
for s in symbols:
    vol = calculate_volatility(s, 7)
    if vol:
        volatility_data.append({
            'symbol': s,
            'avg_vol': vol['avg_vol'],
            'max_vol': vol['max_vol'],
            'min_vol': vol['min_vol'],
            'trend': vol['trend']
        })

# 按波动率排序
volatility_data.sort(key=lambda x: x['avg_vol'], reverse=True)

print(f'{"品种":<10} {"平均波幅%":<12} {"最大波幅%":<12} {"最小波幅%":<12} {"周涨跌%":<10}')
print('-' * 80)
for data in volatility_data:
    print(f'{data["symbol"]:<10} {data["avg_vol"]:>8.3f}%    {data["max_vol"]:>8.3f}%    {data["min_vol"]:>8.3f}%    {data["trend"]:>+8.2f}%')
print('')

# 2. 市场趋势分析
print('【2. 市场趋势分析】')
print('-' * 80)

def analyze_trend(symbol):
    """分析趋势"""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
    if rates is None or len(rates) < 50:
        return None
    
    closes = rates['close']
    highs = rates['high']
    lows = rates['low']
    
    # 均线
    sma20 = np.mean(closes[-20:])
    sma50 = np.mean(closes[-50:])
    current = closes[-1]
    
    # 趋势判断
    if current > sma20 > sma50:
        trend = '强势多头'
        signal = 'BUY'
    elif current < sma20 < sma50:
        trend = '强势空头'
        signal = 'SELL'
    elif abs(current - sma20) / sma20 < 0.002:
        trend = '震荡整理'
        signal = 'WAIT'
    else:
        trend = '弱势震荡'
        signal = 'WAIT'
    
    # 20 日涨跌幅
    pct_20 = (closes[-1] - closes[-20]) / closes[-20] * 100
    
    return {
        'trend': trend,
        'signal': signal,
        'pct_20': pct_20,
        'price': current,
        'sma20': sma20,
        'sma50': sma50
    }

trend_data = []
for s in symbols:
    trend = analyze_trend(s)
    if trend:
        trend_data.append({
            'symbol': s,
            'trend': trend['trend'],
            'signal': trend['signal'],
            'pct_20': trend['pct_20'],
            'price': trend['price']
        })

print(f'{"品种":<10} {"当前价格":<15} {"20 日涨跌%":<12} {"趋势":<15} {"信号":<8}')
print('-' * 80)
for data in trend_data:
    print(f'{data["symbol"]:<10} {data["price"]:>12.5f}   {data["pct_20"]:>+10.2f}%   {data["trend"]:<15} {data["signal"]:<8}')
print('')

# 3. 流动性分析 (不同时段)
print('【3. 流动性分析 - 分时段点差】')
print('-' * 80)

current_hour = datetime.datetime.now().hour
print(f'当前时间：北京时间 {current_hour}:00')
print('')

# 获取实时点差
print(f'{"品种":<10} {"Bid":<15} {"Ask":<15} {"点差 (points)":<15} {"流动性评级":<10}')
print('-' * 80)

for s in symbols:
    tick = mt5.symbol_info_tick(s)
    if tick:
        if s in ['USDJPY']:
            spread = (tick.ask - tick.bid) * 100
        else:
            spread = (tick.ask - tick.bid) * 10000
        
        # 流动性评级
        if spread < 1.5:
            liquidity = '极高'
        elif spread < 3:
            liquidity = '高'
        elif spread < 5:
            liquidity = '中'
        else:
            liquidity = '低'
        
        print(f'{s:<10} {tick.bid:>12.5f}   {tick.ask:>12.5f}   {spread:>10.2f}        {liquidity:<10}')
print('')

# 时段分析
print('【交易时段流动性特点】')
print('  亚洲盘 (06:00-15:00): 流动性一般，点差略高，适合观望或小仓位')
print('  欧洲盘 (15:00-00:00): 流动性高，点差正常，主要交易时段')
print('  美洲盘 (20:00-05:00): 流动性最高，点差最低，最佳交易时段')
print('  重叠时段 (20:00-00:00): 欧美重叠，流动性最佳，波动最大')
print('')

# 4. 点差和滑点成本统计
print('【4. 交易成本分析】')
print('-' * 80)

cost_data = []
for s in symbols:
    tick = mt5.symbol_info_tick(s)
    symbol_info = mt5.symbol_info(s)
    if tick and symbol_info:
        spread_points = (tick.ask - tick.bid) / symbol_info.point
        spread_cost_usd = (tick.ask - tick.bid) * 100000  # 1 标准手点差成本
        
        cost_data.append({
            'symbol': s,
            'spread_points': spread_points,
            'spread_cost': spread_cost_usd
        })

print(f'{"品种":<10} {"点差 (points)":<15} {"1 标准手成本 ($)":<20} {"成本评级":<10}')
print('-' * 80)
for data in cost_data:
    if data['spread_cost'] < 5:
        cost_rating = '低'
    elif data['spread_cost'] < 10:
        cost_rating = '中'
    else:
        cost_rating = '高'
    print(f'{data["symbol"]:<10} {data["spread_points"]:>10.2f}        ${data["spread_cost"]:>8.2f}          {cost_rating:<10}')
print('')

# 5. 品种推荐
print('【5. 品种推荐 - 基于当前市场环境】')
print('-' * 80)

# 综合评分
recommendations = []
for i, data in enumerate(trend_data):
    if data['signal'] != 'WAIT':
        # 找到对应的波动率数据
        vol = next((v for v in volatility_data if v['symbol'] == data['symbol']), None)
        cost = next((c for c in cost_data if c['symbol'] == data['symbol']), None)
        
        if vol and cost:
            # 评分逻辑：趋势明确 + 波动适中 + 成本低 = 高分
            score = 0
            if abs(data['pct_20']) > 0.5:
                score += 3  # 趋势强
            elif abs(data['pct_20']) > 0.2:
                score += 2  # 趋势中等
            
            if 0.5 < vol['avg_vol'] < 1.5:
                score += 3  # 波动适中
            elif vol['avg_vol'] < 0.5:
                score += 1  # 波动太低
            
            if cost['spread_cost'] < 5:
                score += 2  # 成本低
            elif cost['spread_cost'] < 10:
                score += 1  # 成本中等
            
            recommendations.append({
                'symbol': data['symbol'],
                'signal': data['signal'],
                'score': score,
                'reason': f'{data["trend"]}, 20 日{data["pct_20"]:+.2f}%, 波动{vol["avg_vol"]:.2f}%'
            })

recommendations.sort(key=lambda x: x['score'], reverse=True)

print(f'{"排名":<6} {"品种":<10} {"方向":<8} {"评分":<6} {"推荐理由":<40}')
print('-' * 80)
for i, rec in enumerate(recommendations[:5], 1):
    print(f'{i:<6} {rec["symbol"]:<10} {rec["signal"]:<8} {rec["score"]:<6} {rec["reason"]:<40}')
print('')

# 6. 重大新闻事件影响
print('【6. 本周重点关注事件】')
print('-' * 80)
print('  - 美联储官员讲话 - 关注美元走势')
print('  - 美国非农就业数据 - 高影响事件')
print('  - 欧元区 PMI 数据 - 影响 EURUSD')
print('  - 日本央行利率决议 - 影响 USDJPY')
print('  - 地缘政治风险 - 关注避险货币 (JPY, CHF)')
print('')

# 7. 市场适应性总结
print('=' * 80)
print('【市场适应性总结】')
print('=' * 80)
print('')

# 统计趋势
bullish = sum(1 for d in trend_data if d['signal'] == 'BUY')
bearish = sum(1 for d in trend_data if d['signal'] == 'SELL')
ranging = sum(1 for d in trend_data if d['signal'] == 'WAIT')

print(f'市场状态：{"单边趋势" if (bullish + bearish) > ranging else "震荡整理"}')
print(f'  - 多头品种：{bullish}个')
print(f'  - 空头品种：{bearish}个')
print(f'  - 震荡品种：{ranging}个')
print('')

if recommendations:
    top_rec = recommendations[0]
    print(f'⭐ 首选推荐：{top_rec["symbol"]} {top_rec["signal"]}')
    print(f'   理由：{top_rec["reason"]}')
    print('')

print('【交易建议】')
print('  1. 当前市场呈现分化格局，建议关注趋势明确的品种')
print('  2. 避免在震荡品种上频繁交易')
print('  3. 重点关注欧美重叠时段 (20:00-00:00) 的交易机会')
print('  4. 严格执行止损，单笔风险控制在 0.5% 以内')
print('  5. 周末流动性较低，加密货币信号需>0.2% 才考虑')
print('')

print('=' * 80)
print('报告生成完毕')
print('=' * 80)

mt5.shutdown()
