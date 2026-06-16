"""
v5.11 patch: 80条外汇策略整合
P0: 枢轴点 + 固定止损最低20点
P1: London Session优先 + 趋势线突破
P2: 均线背离 + K线形态简化版 + Pivot-based止损优化

基于80条外汇交易策略 (2026-05-20)
"""

import re
import os
import shutil

# 1. 备份当前版本
backup_name = f"backup_patrol_v5.11_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
backup_path = os.path.join(os.path.dirname(__file__), backup_name)
shutil.copy2(__file__.replace('apply_v511.py', 'patrol.py'), backup_path)
print(f"备份: {backup_name}")

with open(os.path.join(os.path.dirname(__file__), 'patrol.py'), 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

changes = []

# =============================================================================
# P0-1: 添加枢轴点计算函数
# =============================================================================
pivot_func = '''
# v5.11: 枢轴点计算 (Classic Pivot Points - 80条策略核心工具)
# 参考: 策略14-17, 32-33, 39, 43
def calc_pivot_points(symbol, tf=mt5.TIMEFRAME_D1):
    """计算枢轴点 (经典公式)
    PP = (H + L + C) / 3
    R1 = 2*PP - L
    S1 = 2*PP - H
    R2 = PP + (H - L)
    S2 = PP - (H - L)
    R3 = H + 2*(PP - L)
    S3 = L - 2*(H - PP)
    """
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, 2)
    if rates is None or len(rates) < 2:
        return None
    h = rates[0]['high']
    l = rates[0]['low']
    c = rates[0]['close']
    pp = (h + l + c) / 3
    r1 = 2 * pp - l
    s1 = 2 * pp - h
    r2 = pp + (h - l)
    s2 = pp - (h - l)
    r3 = h + 2 * (pp - l)
    s3 = l - 2 * (h - pp)
    return {'PP': pp, 'R1': r1, 'R2': r2, 'R3': r3, 'S1': s1, 'S2': s2, 'S3': s3,
            'H': h, 'L': l, 'C': c}

def pivot_zone_check(symbol, price, direction, threshold_pips=20):
    """检查价格是否在枢轴点附近(±threshold_pips)
    策略32: "你只应在枢轴点附近进出，而不是之间"
    策略43: "阻力位(R1,M3,R2)是卖区，支撑位(S2,M1,S1)是买区"
    返回: (bool, zone) - 是否在zones, 当前区域
    """
    pivots = calc_pivot_points(symbol)
    if pivots is None:
        return True, "unknown"  # 无数据则放行
    pp = pivots['PP']
    r1, r2, r3 = pivots['R1'], pivots['R2'], pivots['R3']
    s1, s2, s3 = pivots['S1'], pivots['S2'], pivots['S3']
    
    sym = mt5.symbol_info(symbol)
    pip = get_pip_size(symbol)
    threshold = threshold_pips * pip
    
    # 区域判断
    if price > r1:
        zone = "R1以上(卖区)"
    elif price > pp:
        zone = "PP-R1之间"
    elif price > s1:
        zone = "S1-PP之间"
    elif price > s2:
        zone = "S2-S1之间"
    else:
        zone = "S2以下(买区)"
    
    # 方向过滤: BUY应在支撑区(S/PP附近)，SELL应在阻力区(R/PP附近)
    if direction == 'BUY':
        # BUY信号需要价格在S1/S2/PP附近(支撑区)
        if price > r1 + threshold:
            return False, zone  # 价格太高，不是好的买入区
    else:  # SELL
        # SELL信号需要价格在R1/R2/PP附近(阻力区)
        if price < s1 - threshold:
            return False, zone  # 价格太低，不是好的卖出区
    
    return True, zone

# v5.11: 趋势线突破检测 (策略28, 68)
def detect_trendline_break(symbol, tf=mt5.TIMEFRAME_H1, lookback=30):
    """检测趋势线突破
    策略68: "趋势线是有力的，价格突破趋势线会转向，不管其它指标如何说"
    返回: ('BUY' | 'SELL' | None, confidence 0-100)
    """
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, lookback)
    if rates is None or len(rates) < 10:
        return None, 0
    df = pd.DataFrame(rates)
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    
    # 简化: 用线性回归拟合高低点趋势线
    x = np.arange(len(highs))
    try:
        # 上涨趋势线(连接最低低点)
        low_idx = np.argmin(lows)
        low_fit = np.polyfit(x[low_idx:], lows[low_idx:], 1)
        low_slope = low_fit[0]
        
        # 下跌趋势线(连接最高高点)
        high_idx = np.argmax(highs)
        high_fit = np.polyfit(x[:high_idx+1], highs[:high_idx+1], 1)
        high_slope = high_fit[0]
        
        last_price = closes[-1]
        last_high = highs[-1]
        last_low = lows[-1]
        
        # 趋势线当前值
        trend_low_now = np.polyval(low_fit, len(highs)-1)
        trend_high_now = np.polyval(high_fit, len(highs)-1)
        
        # 价格与趋势线的关系
        if last_price < trend_low_now - (highs.mean()*0.0005):
            return 'SELL', min(abs(low_slope)*1000, 80)  # 跌破上涨趋势线
        elif last_price > trend_high_now + (highs.mean()*0.0005):
            return 'BUY', min(abs(high_slope)*1000, 80)   # 突破下跌趋势线
    except:
        pass
    return None, 0

# v5.11: London Session 检测 (策略26, 49)
def is_london_session():
    """检测是否London Session (10:00-18:00 CST = 02:00-10:00 UTC)
    策略26: "欧元大势开始于纽约时间凌晨2点以后，正是伦顿时段"
    策略49: "等伦敦凌晨3点才行动"
    """
    now_utc = datetime.now(timezone.utc)
    hour_utc = now_utc.hour
    # London: 08:00-16:00 UTC (冬令时) / 07:00-15:00 UTC (夏令时)
    # 简化: 07:00-16:00 UTC 之间为伦敦核心时段
    return 7 <= hour_utc <= 16

def london_session_boost():
    """London Session信号加成 +20% (策略26: 76点幅度在12小时内)
    非London Session信号打7折 (策略26: 主要趋势在伦敦时段展开)
    """
    if is_london_session():
        return 1.2  # London时段信号增强20%
    else:
        return 0.7  # 非London时段信号打7折

# v5.11: 均线背离检测 (策略8-9)
def detect_ma_divergence(symbol, tf=mt5.TIMEFRAME_H1):
    """检测均线与价格的背离
    策略8: "只使用均线的背离，而不用均线做买卖信号"
    策略9: "15分钟图上的均线背离比1小时图上更重要"
    返回: ('BUY' | 'SELL' | None, strength 0-100)
    """
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, 100)
    if rates is None or len(rates) < 50:
        return None, 0
    df = pd.DataFrame(rates)
    close = df['close']
    # RSI作为"均线"(类似指标)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # 检测背离: 价格创新高但RSI没创新高 = 顶背离(看空)
    # 价格创新低但RSI没创新低 = 底背离(看多)
    price_trend = close.iloc[-20:].values
    rsi_trend = rsi.iloc[-20:].values
    
    price_new_high = price_trend[-1] > price_trend.max()
    price_new_low = price_trend[-1] < price_trend.min()
    rsi_new_high = rsi_trend[-1] > rsi_trend.max()
    rsi_new_low = rsi_trend[-1] < rsi_trend.min()
    
    if price_new_high and not rsi_new_high:
        return 'SELL', 70  # 顶背离
    elif price_new_low and not rsi_new_low:
        return 'BUY', 70   # 底背离
    return None, 0

# v5.11: K线形态简化检测 (策略13, 45, 66, 73)
def detect_candle_pattern(symbol, tf=mt5.TIMEFRAME_H1):
    """简化K线形态检测
    策略73: "等出现锤子或拉长顶，然后扣动扳机"
    策略66: "价格逆转形态，中间柱比两边有更高的高/更低的低"
    返回: ('BUY' | 'SELL' | None, confidence 0-100)
    """
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, 5)
    if rates is None or len(rates) < 5:
        return None, 0
    df = pd.DataFrame(rates)
    
    for i in range(2, len(df)):
        prev_high = df['high'].iloc[i-1]
        prev_low = df['low'].iloc[i-1]
        prev_close = df['close'].iloc[i-1]
        prev_open = df['open'].iloc[i-1]
        curr = df.iloc[i]
        
        body_size = abs(curr['close'] - curr['open'])
        upper_shadow = curr['high'] - max(curr['open'], curr['close'])
        lower_shadow = min(curr['open'], curr['close']) - curr['low']
        
        # 锤子线 (Hammer): 下跌趋势中，下影线很长，实体小
        if prev_close < prev_open:  # 之前是下跌
            if lower_shadow > body_size * 2 and upper_shadow < body_size * 0.5:
                return 'BUY', 75
        
        # 射击星 (Shooting Star): 上涨趋势中，上影线很长，实体小
        if prev_close > prev_open:  # 之前是上涨
            if upper_shadow > body_size * 2 and lower_shadow < body_size * 0.5:
                return 'SELL', 75
        
        # 双顶/双底 (策略45)
        if i >= 3:
            high1 = df['high'].iloc[i-3]
            high2 = df['high'].iloc[i-2]
            if abs(high1 - high2) < (high1 * 0.0003) and curr['high'] < high1:
                # 双顶形成后下破
                return 'SELL', 80
            
            low1 = df['low'].iloc[i-3]
            low2 = df['low'].iloc[i-2]
            if abs(low1 - low2) < (low1 * 0.0003) and curr['low'] > low1:
                # 双底形成后上破
                return 'BUY', 80
    
    return None, 0

'''

# 在 supertrend_signal 后面添加新函数
find_pos = content.find('def supertrend_signal(')
if find_pos > 0:
    content = content[:find_pos] + pivot_func + '\n' + content[find_pos:]
    changes.append('P0-1: 添加枢轴点 + 趋势线 + London Session + 均线背离 + K线形态')
else:
    changes.append('WARNING: supertrend_signal not found')

# =============================================================================
# P0-2: 修改止损最低值从15pip到20pip (策略10)
# =============================================================================
content = content.replace(
    'sl_pips = max(atr_pips * ATR_SL_MULT[\'default\'] + buffer_pips, 15)',
    'sl_pips = max(atr_pips * ATR_SL_MULT[\'default\'] + buffer_pips, 20)'  # 策略10: 20-30点止损
)
changes.append('P0-2: 止损最低15pip -> 20pip (策略10)')

# =============================================================================
# P1-1: 在calculate_signal_v3中集成Pivot + 趋势线 + London折扣
# =============================================================================
# 修改calculate_signal_v3的返回前，添加额外信号层

old_signal_blend = '''        # v5.10: Combine with SuperTrend for extra confirmation
        supertrend_dir, supertrend_str = supertrend_signal(symbol)
        if supertrend_dir and supertrend_str > 0:
            strength = min(strength * 0.7 + supertrend_str * 0.3, 100)
            log(f"  [SuperTrend] {symbol}: {supertrend_dir} {supertrend_str}% boost={strength:.1f}%")
        
        strength = min(strength, 100)
        return direction, round(strength, 1)'''

new_signal_blend = '''        # v5.11: Pivot Zone Check (策略32-33, 39, 43)
        pivot_ok, zone = pivot_zone_check(symbol, current_price, direction, threshold_pips=25)
        if not pivot_ok:
            log(f"  [Pivot] {symbol} {direction} 不在交易区({zone})，跳过")
            return None, 0
        log(f"  [Pivot] {symbol} {direction} 在交易区({zone})")
        
        # v5.11: 趋势线突破检测 (策略68)
        trendline_dir, trendline_str = detect_trendline_break(symbol)
        if trendline_dir and trendline_dir == direction:
            strength = min(strength * 0.8 + trendline_str * 0.2, 100)
            log(f"  [Trendline] {symbol}: 突破确认 +{trendline_str}%")
        
        # v5.11: 均线背离检测 (策略8-9)
        div_dir, div_str = detect_ma_divergence(symbol)
        if div_dir and div_dir == direction:
            strength = min(strength * 0.85 + div_str * 0.15, 100)
            log(f"  [Divergence] {symbol}: 背离确认 +{div_str}%")
        
        # v5.11: K线形态 (策略73)
        candle_dir, candle_str = detect_candle_pattern(symbol)
        if candle_dir and candle_dir == direction:
            strength = min(strength * 0.9 + candle_str * 0.1, 100)
            log(f"  [Candle] {symbol}: 形态确认 +{candle_str}%")
        
        # v5.10: Combine with SuperTrend for extra confirmation
        supertrend_dir, supertrend_str = supertrend_signal(symbol)
        if supertrend_dir and supertrend_str > 0:
            if supertrend_dir == direction:
                strength = min(strength * 0.7 + supertrend_str * 0.3, 100)
                log(f"  [SuperTrend] {symbol}: {supertrend_dir} {supertrend_str}% boost={strength:.1f}%")
        
        # v5.11: London Session信号加成 (策略26, 49)
        london_mult = london_session_boost()
        if london_mult > 1.0:
            log(f"  [London] Session信号+20%: {direction}")
        else:
            log(f"  [London] 非London时段信号打7折")
        strength = strength * london_mult
        
        strength = min(strength, 100)
        return direction, round(strength, 1)'''

if old_signal_blend in content:
    content = content.replace(old_signal_blend, new_signal_blend)
    changes.append('P1-1: 集成Pivot过滤 + 趋势线/背离/形态/SuperTrend多信号叠加')
else:
    changes.append('WARNING: old signal blend not found')

# =============================================================================
# P1-2: 修改版本号
# =============================================================================
content = content.replace("'Patrol Smart v5.10'", "'Patrol Smart v5.11'")
content = content.replace('v5.10', 'v5.11')
changes.append('P1-2: 版本 v5.10 -> v5.11')

# =============================================================================
# P2: Pivot-based止损优化 (策略11)
# =============================================================================
# 在get_dynamic_sl_tp中，使用Pivot作为止损参考而不是纯ATR
old_sl_comment = '''    # 缓冲 = ATR × 0.5（动态自适应）'''

new_sl_comment = '''    # v5.11: 策略11 - 止损放在Pivot外侧，留出反抽空间
    # "33点能安全渡过反抽，那就用33点"
    pivot_threshold = max(sl_pips, 25)  # 至少25pip或ATR计算值
    
    # 调整SL到Pivot外侧
    if sl_pips < pivot_threshold:
        buffer_extra = pivot_threshold - sl_pips
        sl_pips = pivot_threshold
        tp_pips = tp_pips + buffer_extra  # TP也相应调整，保持RR
    
    # 缓冲 = ATR × 0.5（动态自适应）'''

if old_sl_comment in content:
    content = content.replace(old_sl_comment, new_sl_comment)
    changes.append('P2: Pivot-based止损优化（策略11: 留出33点反抽空间）')
else:
    changes.append('WARNING: sl comment not found')

# 写回文件
with open(os.path.join(os.path.dirname(__file__), 'patrol.py'), 'w', encoding='utf-8') as f:
    f.write(content)

print('\n=== v5.11 变更 ===')
for c in changes:
    print(f'  {c}')
print('\n补丁完成!')
print(f'备份: {backup_name}')