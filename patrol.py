#!/usr/bin/env python
import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), 'trade_state.json')

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_update': None, 'version': 'v1.0',
        'patrol_runs': [], 'consecutive_no_signal': 0,
        'last_trade': None, 'last_signal': None,
        'daily_pnl': 0.0, 'daily_loss_limit': 50.0, 'consecutive_losses': 0
    }

def save_state(state):
    state['last_update'] = __import__('datetime').datetime.now().__str__()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
# -*- coding: utf-8 -*-
"""
旺财智能交易系统 v5.1
核心策略：Kelly Criterion 底层决策 | 高胜率才出手 | 少而精
v5规范（Karen 2026-05-09）：
  - 信号 >=60%：0.5% 风险仓位
  - 信号 45-60%：0.3% 风险仓位
  - 信号 <45%：不开仓
  - Kelly 作为底层仓位决策（历史胜率 p）
  - Kelly f* < 5% 品种 → 永久屏蔽
v5.1变更（2026-05-09）：
  - Kelly优质品种（kf>10%）在SUPER信号时可提至1%风险
  - 手数直接由风险倒推，非固定档次
  - 彻底删除亚洲盘禁止
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
np.seterr(divide="ignore", invalid="ignore")
import sys
import io
from datetime import datetime, timezone, timedelta

# v5.11: Signal de-dup cache and SuperTrend (from QuantDinger analysis)
import time as _time

# In-memory price cache (symbol -> (price, timestamp), TTL=10s)
_price_cache = {}
_price_cache_ttl = 10.0

# Signal de-dup cache: prevent repeated orders on same candle
_signal_dedup = {}  # (symbol, direction, bar_time) -> first_seen_ts
_signal_dedup_ttl = 1800  # 30min

def _get_cached_price(symbol):
    """Get price from cache or fetch fresh (MT5)."""
    now = _time.time()
    key = symbol
    if key in _price_cache:
        price, ts = _price_cache[key]
        if now - ts < _price_cache_ttl:
            return price
    tick = mt5.symbol_info_tick(symbol)
    if tick and tick.bid > 0:
        _price_cache[key] = (tick.bid, now)
        return tick.bid
    return None

def _is_signal_duplicate(symbol, direction, bar_time, ttl=_signal_dedup_ttl):
    """Check if signal is duplicate within TTL window."""
    key = (symbol, direction, int(bar_time))
    now = _time.time()
    if key in _signal_dedup:
        if now - _signal_dedup[key] < ttl:
            return True
    _signal_dedup[key] = now
    return False



sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ACCOUNT = 52797683
SERVER = "ICMarketsSC-Demo"

# ========== v5.5 全链路优化版 ==========
SIGNAL_MIN = 0.35           # 信号强度门槛 35%（<35%不开仓）
SUPER_SIGNAL = 0.60        # SUPER 信号门槛 60%
RISK_PCT_SUPER = 0.005     # 60%+ 信号：0.5% 风险
RISK_PCT_STRONG = 0.003     # 45-60% 信号：0.3% 风险
KELLY_BOOST_MULT = 2.0      # 高Kelly品种（kf>10%）可双倍风险
KELLY_MIN_TRADE = 0.05     # Kelly f* < 10% 品种禁止交易（来福P0建议）
MAX_POS = 3
MAX_TRADES_PER_HOUR = 1
CORRELATION_COOLDOWN_H = 2
SL_COOLDOWN_H = 4           # 止损后同品种4小时冷却
DAILY_LOSS_LIMIT = 50       # 单日亏损上限 $50
CONSECUTIVE_LOSS_REDUCE = 2 # 连亏2次后仓位减半
ATR_SL_MULT = {'jpy': 2.0, 'metal': 1.5, 'default': 1.5}  # ATR倍数
ATR_SL_BUFFER_MULT = 0.5   # 止损缓冲 = ATR × 0.5（动态，非固定5pip）
TP_SL_RATIO = 1.3           # v5.14 TP:SL = 1:1.3

# ========== Kelly 品种注册表（基于217笔历史统计） ==========
# W = 历史胜率 | R = 平均赢/平均亏 | kf = Kelly f*
# kf < 10% → 禁止交易（来福P0建议） | kf >= 10% → 可交易
KELLY_REGISTRY = {
    # 正 EV 品种（基于真实 MT5 数据 221 笔）
    # === 核心交易品种 ===
    'USDCAD':  {'W': 0.71, 'R': 0.87, 'kf': 0.388},  # 7笔 +$14.21 EV=0.339
    'AUDUSD':  {'W': 0.62, 'R': 0.67, 'kf': 0.067},  # 48笔 +$40.61 EV=0.045
    'USDCHF':  {'W': 0.57, 'R': 0.85, 'kf': 0.057},  # 37笔 +$28.91 EV=0.049
    'GBPUSD':  {'W': 0.52, 'R': 1.03, 'kf': 0.061},  # 21笔 +$19.98 EV=0.063
    # === Micro-Test 品种（小单累积数据）===
    'XAUUSD':  {'W': 1.00, 'R': 3.00, 'kf': 0.500},  # 2笔 +$396 Micro-Test 0.05手
    # 永久禁止（负 EV）: EURUSD/NZDUSD/USDJPY/AUDJPY/BTCUSD/AUDCHF
}

TZ = timezone(timedelta(hours=8))

SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "AUDJPY", "EURGBP", "EURCAD", "GBPAUD", "GBPJPY",
    "EURAUD", "AUDCAD", "AUDCHF", "NZDJPY", "CADJPY", "CHFJPY",
    "XAUUSD", "XAGUSD"
]

CORRELATED_GROUPS = {
    "AUD": ["AUDUSD", "AUDCHF", "AUDCAD", "AUDJPY", "EURAUD", "GBPAUD"],
    "EUR": ["EURUSD", "EURGBP", "EURCAD", "EURJPY", "EURAUD"],
    "USD": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],
    "JPY": ["USDJPY", "AUDJPY", "EURJPY", "GBPJPY", "NZDJPY", "CADJPY", "CHFJPY"],
    "METAL": ["XAUUSD", "XAGUSD"],
}

def log(msg):
    print(msg, flush=True)

def is_jpy(symbol):
    return "JPY" in symbol

def is_precious_metal(symbol):
    return symbol in ('XAUUSD', 'XAGUSD')

# ========== Kelly 核心函数 ==========

def get_kelly_quality(symbol):
    """返回 Kelly 质量: 'high'(kf>10%) / 'mid'(5-10%) / 'low'(<5%) / 'neg' / 'unreg'(未注册)"""
    info = KELLY_REGISTRY.get(symbol)
    if info is None:
        return 'unreg'  # v5.5: 未注册品种
    kf = info['kf']
    if kf > 0.10:
        return 'high'
    elif kf >= 0.05:
        return 'mid'
    elif kf > 0:
        return 'low'
    return 'neg'

def kelly_filter(symbol):
    """Kelly 过滤 v5.5:
    - 未注册品种 → 禁止
    - 负 Kelly 品种 → Micro-Test 模式
    - BTCUSD → 永久屏蔽
    - Kelly < 10% → 禁止交易（来福P0）
    """
    if symbol == 'BTCUSD':
        log("  [永久屏蔽] {} 加密货币禁止交易".format(symbol))
        return False

    quality = get_kelly_quality(symbol)

    if quality == 'unreg':
        log("  [未注册] {} 不在Kelly注册表，禁止开仓".format(symbol))
        return False

    kf = KELLY_REGISTRY.get(symbol, {}).get('kf', 0)
    if kf < KELLY_MIN_TRADE:
        log("  [Kelly过滤] {} kf={:.1f}% < {:.0f}%，禁止交易".format(
            symbol, kf*100, KELLY_MIN_TRADE*100))
        return False

    if quality == 'neg':
        log("  [Micro-Test] {} kf={:.1f}% 进入小单重新验证模式".format(
            symbol, kf*100))
    return True

def is_micro_test(symbol):
    """负 Kelly 品种进入 Micro-Test 模式"""
    quality = get_kelly_quality(symbol)
    return quality == 'neg' and symbol != 'BTCUSD'

def get_consecutive_losses():
    """获取连续亏损次数（最近3天）"""
    try:
        to_time = int(datetime.now(TZ).timestamp())
        from_time = to_time - 86400 * 3
        history = mt5.history_deals_get(from_time, to_time) or []
        closes = [d for d in history if d.entry == 1]
        consecutive = 0
        for d in sorted(closes, key=lambda x: x.time, reverse=True):
            pnl = d.profit + d.swap + d.commission
            if pnl < 0:
                consecutive += 1
            else:
                break
        return consecutive
    except:
        return 0

def get_kelly_lot_size(symbol, strength):
    """Kelly 分档手数上限：
    高Kelly(kf>10%) → SUPER 0.10 / STRONG 0.06
    中Kelly(kf 5-10%) → SUPER 0.10 / STRONG 0.06
    低Kelly(kf <5%) → SUPER 0.08 / STRONG 0.05
    Micro-Test(负Kelly) → SUPER 0.05 / STRONG 0.05
    """
    quality = get_kelly_quality(symbol)
    is_super = strength >= SUPER_SIGNAL*100

    if is_micro_test(symbol):
        return 0.05  # Micro-Test 最大 0.05 手（$9700 * 0.5% = $48.5风险上限）

    if quality == 'high':
        return 0.10 if is_super else 0.06
    elif quality == 'mid':
        return 0.10 if is_super else 0.06
    elif quality == 'low':
        return 0.08 if is_super else 0.05
    else:
        return 0.05  # 默认保守

def calc_expected_value(symbol, direction, strength):
    """计算预期值 EV = p*b - q（Kelly核心公式）
    p = 信号强度（%）| b = 盈亏比（TP/SL）| q = 1-p
    EV > 0 才允许开仓
    """
    p = strength / 100.0
    q = 1 - p
    sl_pips, tp_pips, _, _, _ = get_dynamic_sl_tp(symbol)
    b = tp_pips / sl_pips if sl_pips > 0 else 0
    ev = p * b - q
    log("  [Kelly EV] {} {} p={:.0f}% b={:.2f} EV={:.3f}".format(
        direction, symbol, p*100, b, ev))
    return ev > 0

def get_risk_pct(symbol, strength):
    """决定本笔交易的风险百分比"""
    # Micro-Test 模式：极低风险
    if is_micro_test(symbol):
        risk_pct = 0.0005  # 0.05%（每笔最多 $5）
        log("  [Micro-Test] {} 极低风险 {:.1f}%".format(
            symbol, risk_pct*100))
        return risk_pct

    risk_pct = RISK_PCT_SUPER if strength >= SUPER_SIGNAL*100 else RISK_PCT_STRONG
    # 高 Kelly 品种 + SUPER 信号 → 可提升至双倍风险
    if get_kelly_quality(symbol) == 'high' and strength >= SUPER_SIGNAL*100:
        risk_pct = min(risk_pct * KELLY_BOOST_MULT, 0.01)  # 上限1%
        log("  [Kelly提升] {} 高Kelly+SUPER信号，风险提升至{:.1f}%".format(
            symbol, risk_pct*100))
    return risk_pct

# ========== ATR 计算 ==========

def calc_atr(symbol, tf=mt5.TIMEFRAME_H1, period=14):
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, 50)
    if rates is None or len(rates) < period + 1:
        return None
    df = pd.DataFrame(rates)
    hi, lo, cl = df['high'], df['low'], df['close']
    tr1 = hi - lo
    tr2 = abs(hi - cl.shift(1))
    tr3 = abs(lo - cl.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    return tr.rolling(period).mean().iloc[-1]

def get_dynamic_sl_tp(symbol):
    """动态止损止盈 v5.5
    止损缓冲 = ATR × 0.5（动态，非固定5pip，来福P1建议）
    JPY: ATR*2.0 + ATR*0.5缓冲（最低20pip）
    贵金属: ATR*1.5 + ATR*0.5缓冲（最低50pip）
    其他: ATR*1.5 + ATR*0.5缓冲（最低15pip）
    TP = SL * 2.0
    """
    atr = calc_atr(symbol)
    if atr is None:
        return 20, 40, 5, 0.00001, 10000

    sym = mt5.symbol_info(symbol)
    digits = sym.digits
    point = sym.point

    # v5.11: 先初始化 sl_pips/tp_pips，再做Pivot调整
    if is_precious_metal(symbol):
        pip_size = 0.01
        atr_pips = atr / pip_size
        buffer_pips = atr_pips * ATR_SL_BUFFER_MULT
        sl_pips = max(atr_pips * ATR_SL_MULT['metal'] + buffer_pips, 50)
        tp_pips = sl_pips * TP_SL_RATIO
        pip_div = 0.01
    elif is_jpy(symbol):
        pip_div = 100
        pip_size = point * 10
        atr_pips = atr / pip_size
        buffer_pips = atr_pips * ATR_SL_BUFFER_MULT
        sl_pips = max(atr_pips * ATR_SL_MULT['jpy'] + buffer_pips, 20)
        tp_pips = sl_pips * TP_SL_RATIO
    else:
        pip_div = 10000
        pip_size = point * 10 if digits in (3, 5) else point
        atr_pips = atr / pip_size
        buffer_pips = atr_pips * ATR_SL_BUFFER_MULT
        sl_pips = max(atr_pips * ATR_SL_MULT['default'] + buffer_pips, 25)
        tp_pips = sl_pips * TP_SL_RATIO

    # v5.11: 策略11 - 止损放在Pivot外侧，留出反抽空间
    # "33点能安全渡过反抽，那就用33点"
    pivot_threshold = max(sl_pips, 25)  # 至少25pip或ATR计算值

    # 调整SL到Pivot外侧
    if sl_pips < pivot_threshold:
        buffer_extra = pivot_threshold - sl_pips
        sl_pips = pivot_threshold
        tp_pips = tp_pips + buffer_extra  # TP也相应调整，保持RR

    log(f"  ATR={atr:.5f} | SL={sl_pips:.1f}pips | TP={tp_pips:.1f}pips")
    return sl_pips, tp_pips, digits, point, pip_div

# ========== MT5 连接 ==========

def mt5_connect():
    if not mt5.initialize(login=ACCOUNT, server=SERVER, timeout=10000):
        log("MT5 init failed")
        return None
    info = mt5.account_info()
    log(f"MT5 ok 余额=${info.balance:.2f} 净值=${info.equity:.2f}")
    return info

# ========== 信号计算 ==========



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


def get_pip_size(symbol):
    """Get pip size for a symbol"""
    sym_info = mt5.symbol_info(symbol)
    digits = sym_info.digits
    point = sym_info.point
    return point * 10 if digits in [3, 5] else point

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
        return 1.0  # 非London时段无折扣（v5.13修复）

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


def supertrend_signal(symbol, period=10, multiplier=3.0, tf=mt5.TIMEFRAME_H1):
    """SuperTrend signal using ATR Wilder smoothing (standard, matches TradingView/MT5).
    
    Returns: ('BUY' | 'SELL' | None, strength 0-100)
    
    SuperTrend uses ATR channel direction flip as signal.
    Edge-triggered: fires only on direction flip, no repeated signals while trend persists.
    """
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, 100)
    if rates is None or len(rates) < period + 5:
        return None, 0
    
    import pandas as pd
    import numpy as np
    df = pd.DataFrame(rates)
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range = max(H-L, |H-prevC|, |L-prevC|)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    
    # ATR via Wilder smoothing (RMA) - standard, matches TradingView
    atr = tr.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()
    
    hl2 = (high + low) / 2.0
    upper_basic = hl2 + multiplier * atr
    lower_basic = hl2 - multiplier * atr
    
    n = len(df)
    final_upper = np.full(n, np.nan)
    final_lower = np.full(n, np.nan)
    direction = np.zeros(n, dtype=np.int8)  # 1=long, -1=short, 0=warmup
    
    start_idx = period  # Wilder ATR needs period bars to stabilize
    
    for i in range(start_idx, n):
        if i == start_idx:
            final_upper[i] = float(upper_basic.iloc[i])
            final_lower[i] = float(lower_basic.iloc[i])
        else:
            # Upper band: can only go down (tighten) when trend is up, otherwise follow price up
            prev_upper = float(final_upper[i-1]) if np.isfinite(float(final_upper[i-1])) else float(upper_basic.iloc[i])
            prev_lower = float(final_lower[i-1]) if np.isfinite(float(final_lower[i-1])) else float(lower_basic.iloc[i])
            curr_close = float(close.iloc[i])
            
            if float(atr.iloc[i]) < 1e-10:
                continue
            
            upper_val = float(upper_basic.iloc[i])
            lower_val = float(lower_basic.iloc[i])
            
            # Upper: min(prev_upper, upper_basic) when price < upper, else follow
            if curr_close < prev_upper:
                final_upper[i] = min(prev_upper, upper_val)
            else:
                final_upper[i] = upper_val
            
            # Lower: max(prev_lower, lower_basic) when price > lower, else follow
            if curr_close > prev_lower:
                final_lower[i] = max(prev_lower, lower_val)
            else:
                final_lower[i] = lower_val
        
        # Direction: compare close vs final bands (path-dependent)
        curr_close = float(close.iloc[i])
        fu = float(final_upper[i])
        fl = float(final_lower[i])
        
        if np.isfinite(fu) and np.isfinite(fl):
            if curr_close > fu:
                direction[i] = 1  # bullish
            elif curr_close < fl:
                direction[i] = -1  # bearish
            else:
                direction[i] = direction[i-1] if i > start_idx else 0
    
    # Signal on direction flip (edge-triggered)
    strength = 0
    signal = None
    for i in range(start_idx + 1, n):
        if direction[i] != direction[i-1] and direction[i] != 0:
            # Flip detected
            if direction[i] == 1:
                signal = 'BUY'
            else:
                signal = 'SELL'
            # Strength based on ATR volatility and how long trend has been
            atr_val = float(atr.iloc[i])
            price_val = float(close.iloc[i])
            strength = min(atr_val / price_val * 10000, 100)  # rough mapping to %
            break
    
    return signal, round(strength, 1)

def calculate_signal_v3(symbol):
    try:
        d1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
        h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
        h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        if d1 is None or h4 is None or h1 is None:
            return None, 0

        d1df = pd.DataFrame(d1)
        h4df = pd.DataFrame(h4)
        h1df = pd.DataFrame(h1)

        ema20 = d1df['close'].ewm(span=20).mean().iloc[-1]
        ema50 = d1df['close'].ewm(span=50).mean().iloc[-1]
        price = d1df['close'].iloc[-1]
        d1_bull = ema20 > ema50
        d1_bear = ema20 < ema50
        if not d1_bull and not d1_bear:
            return None, 0
        direction = "BUY" if d1_bull else "SELL"

        delta4 = h4df['close'].diff()
        gain4 = delta4.clip(lower=0).ewm(alpha=1.0/14, adjust=False).mean()
        loss4 = (-delta4.clip(upper=0)).ewm(alpha=1.0/14, adjust=False).mean()
        rs4 = gain4 / loss4.replace(0, 1e-10)
        h4_rsi = (100 - 100 / (1 + rs4)).iloc[-1]

        hi, lo, cl = h1df['high'], h1df['low'], h1df['close']
        tr1 = hi - lo
        tr2 = abs(hi - cl.shift(1))
        tr3 = abs(lo - cl.shift(1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        sym_info = mt5.symbol_info(symbol)
        digits = sym_info.digits
        pip_mult = 0.0001 if digits == 5 else (0.01 if digits == 3 else 0.0001)
        # Normalize to pips
        tr1 = (hi - lo) / pip_mult
        tr2 = abs(hi - cl.shift(1)) / pip_mult
        tr3 = abs(lo - cl.shift(1)) / pip_mult
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        plus_dm = (hi - hi.shift(1)).clip(lower=0) / pip_mult
        minus_dm = (lo.shift(1) - lo).clip(lower=0) / pip_mult
        atr14 = tr.ewm(alpha=1.0/14, adjust=False).mean()
        plus_di = plus_dm.ewm(alpha=1.0/14, adjust=False).mean() / atr14.replace(0, 1e-10) * 100
        minus_di = minus_dm.ewm(alpha=1.0/14, adjust=False).mean() / atr14.replace(0, 1e-10) * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-10) * 100
        adx = dx.ewm(alpha=1.0/14, adjust=False).mean().iloc[-1]

        if not np.isfinite(adx) or abs(adx) < 12:
            return None, 0

        score = 0
        if d1_bull: score += 3
        elif d1_bear: score -= 3
        if (h4_rsi < 35 and d1_bull) or (h4_rsi > 65 and d1_bear): score += 2
        elif 35 <= h4_rsi <= 65: score += 1
        if adx > 25: score += 2

        strength = max(0, (abs(score) - 2) / 8 * 1.5) * 100

        # v5.11: Pivot Zone Check (策略32-33, 39, 43)
        pivot_ok, zone = pivot_zone_check(symbol, price, direction, threshold_pips=25)
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
        # else: 无折扣，不打印
        strength = strength * london_mult

        strength = min(strength, 100)
        return direction, round(strength, 1)
    except:
        return None, 0

def detect_market_state(symbol):
    """检测市场状态：趋势 vs 震荡
    返回 'trending' 或 'ranging'
    来福P2建议：震荡市不追趋势
    """
    try:
        h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
        if h4 is None or len(h4) < 30:
            return 'trending'  # 默认趋势
        df = pd.DataFrame(h4)
        # ADX < 20 = 震荡
        hi, lo, cl = df['high'], df['low'], df['close']
        tr1 = hi - lo
        tr2 = abs(hi - cl.shift(1))
        tr3 = abs(lo - cl.shift(1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr_h4 = tr.ewm(alpha=1.0/14, adjust=False).mean()
        plus_dm = hi.diff().clip(lower=0)
        minus_dm = (-lo.diff()).clip(upper=0)
        plus_di = 100 * plus_dm.ewm(alpha=1.0/14, adjust=False).mean() / atr_h4.replace(0, 1e-10)
        minus_di = 100 * minus_dm.ewm(alpha=1.0/14, adjust=False).mean() / atr_h4.replace(0, 1e-10)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-10)
        adx = dx.ewm(alpha=1.0/14, adjust=False).mean().iloc[-1]
        if abs(adx) < 20:
            return 'ranging'
        return 'trending'
    except:
        return 'trending'

# ========== 执行开仓（v5.5 全链路优化版）============

def execute(symbol, direction, strength):
    """执行开仓：Kelly风险决策 + 预期值校验 + 手数倒推"""
    # Step 1: Kelly 品种过滤
    if not kelly_filter(symbol):
        return False

    # Step 2: Kelly EV 校验
    if not calc_expected_value(symbol, direction, strength):
        log("  [Kelly EV拒绝] {} 预期值<=0，跳过".format(symbol))
        return False

    # v5.5: 市场状态检查
    market_state = detect_market_state(symbol)
    # v5.11: 暂时禁用震荡市过滤（ADX计算异常导致误判）
    # if market_state == 'ranging':
    #     log("  [市场状态] {} 震荡市，趋势策略跳过".format(symbol))
    #     return False

    # v5.5: 连续亏损仓位降级
    cons_losses = get_consecutive_losses()
    if cons_losses >= CONSECUTIVE_LOSS_REDUCE:
        log("  [连亏降级] 连续{}次亏损，仓位减半".format(cons_losses))

    tick = mt5.symbol_info_tick(symbol)
    sym = mt5.symbol_info(symbol)
    digits = sym.digits
    price = tick.ask if direction == "BUY" else tick.bid

    sl_pips, tp_pips, digits, point, pip_div = get_dynamic_sl_tp(symbol)

    # Step 3: 计算每 pip 价值
    if is_precious_metal(symbol):
        pip_value = (sym.trade_tick_value / sym.trade_tick_size) * 0.01 \
            if sym.trade_tick_size > 0 else 0.01
    else:
        pip_size = point * 10 if digits in (3, 5) else point
        pip_value = sym.trade_tick_value * (pip_size / sym.trade_tick_size) \
            if sym.trade_tick_size > 0 else pip_size

    # Step 4: Kelly 风险百分比
    risk_pct = get_risk_pct(symbol, strength)
    info = mt5.account_info()
    risk_amt = info.balance * risk_pct

    # Step 5: 手数 = min(风险金额手数, Kelly分档上限)
    if pip_value > 0 and sl_pips > 0:
        raw_lots = risk_amt / (sl_pips * pip_value)
    else:
        raw_lots = 0.01

    # Kelly 分档上限
    kelly_max_lot = get_kelly_lot_size(symbol, strength)
    lots = round(min(raw_lots, kelly_max_lot), 2)

    # v5.5: 连亏仓位减半
    if cons_losses >= CONSECUTIVE_LOSS_REDUCE:
        lots = round(lots * 0.5, 2)

    lots = max(0.01, lots)  # 最小0.01手

    # Step 6: 盈亏比校验
    rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 0
    if rr_ratio < TP_SL_RATIO - 1e-9:
        log(f"  [过滤] 盈亏比{rr_ratio:.1f}<{TP_SL_RATIO}，空间不足，跳过")
        return False

    min_tp = 50 if is_precious_metal(symbol) else 20
    if tp_pips < min_tp:
        log(f"  [过滤] TP仅{tp_pips:.0f}pip<{min_tp}pip，空间不足，跳过")
        return False

    sl_dist = sl_pips / pip_div
    tp_dist = tp_pips / pip_div
    sl_price = round(price - sl_dist, digits) if direction == "BUY" else round(price + sl_dist, digits)
    tp_price = round(price + tp_dist, digits) if direction == "BUY" else round(price - tp_dist, digits)

    quality = get_kelly_quality(symbol)
    kf = KELLY_REGISTRY.get(symbol, {}).get('kf', 0)
    if is_micro_test(symbol):
        kf_tag = 'Micro-Test'
    else:
        kf_tag = {'high': 'Kelly高', 'mid': 'Kelly中', 'low': 'Kelly低', 'neg': 'Kelly负'}.get(quality, '')
    tier_tag = 'SUPER' if strength >= SUPER_SIGNAL*100 else 'STRONG'

    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 50,
        "magic": 240501,
        "comment": "Patrol Smart v5.11",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log(f"  [{tier_tag}][{kf_tag}] {direction} {symbol} @{price:.{digits}f}")
    log(f"  风险={risk_pct*100:.1f}%=${risk_amt:.2f} | 手数={lots} | SL={sl_pips:.0f}pips | TP={tp_pips:.0f}pips | RR={rr_ratio:.1f}:1 | Kelly f*={kf*100:.1f}%")
    result = mt5.order_send(req)
    log(f"  结果: retcode={result.retcode} {result.comment}")
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log(f"成功开仓 #{result.order}")
        # 更新状态：记录交易
        try:
            st = load_state()
            st['last_trade'] = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'symbol': symbol, 'direction': direction,
                'volume': float(lots), 'entry': float(price),
                'sl': float(sl_price), 'tp': float(tp_price),
                'strength': float(strength), 'kf': float(kf),
                'ticket': int(result.order), 'sl_pips': float(sl_pips), 'tp_pips': float(tp_pips)
            }
            st['last_signal'] = {'symbol': symbol, 'direction': direction, 'strength': float(strength), 'kf': float(kf)}
            st['consecutive_no_signal'] = 0
            save_state(st)
        except Exception as e:
            log(f"  [状态记录失败] {e}")
        return True
    else:
        log(f"失败: {result.comment}")
        return False

# ========== 辅助函数 ==========

def has_correlated_position(symbol, direction, positions):
    groups = [g for g, syms in CORRELATED_GROUPS.items() if symbol in syms]
    for p in positions:
        if p.symbol == symbol:
            continue
        pgroups = [g for g, syms in CORRELATED_GROUPS.items() if p.symbol in syms]
        if any(g in groups for g in pgroups):
            pdir = "BUY" if p.type == 0 else "SELL"
            if pdir == direction:
                return True
    return False

def recently_traded(symbol, hours=2):
    try:
        to_time = int(datetime.now().timestamp())
        from_time = to_time - hours * 3600
        deals = mt5.history_deals_get(from_time, to_time)
        if deals:
            for d in deals:
                if d.symbol == symbol and d.comment in (
                    'Patrol Smart', 'Patrol Smart v5', 'Patrol Smart v5.1',
                    'Patrol Smart v5.12', 'Patrol Smart v5.12', 'Patrol Auto', 'FORCE_CLOSE'):
                    return True
    except:
        pass
    return False

def trades_this_hour():
    try:
        to_time = int(datetime.now().timestamp())
        from_time = to_time - 3600
        deals = mt5.history_deals_get(from_time, to_time)
        return sum(1 for d in deals if d.comment in (
            'Patrol Smart', 'Patrol Smart v5', 'Patrol Smart v5.1', 'Patrol Smart v5.12', 'Patrol Smart v5.12', 'Patrol Auto')
            and d.entry in (0,1))
    except:
        return 0

def symbol_hit_sl_recently(symbol, hours=SL_COOLDOWN_H):
    """检查品种是否在冷却期内（止损后4小时内不开新仓）"""
    try:
        to_time = int(datetime.now().timestamp())
        from_time = to_time - hours * 3600
        deals = mt5.history_deals_get(from_time, to_time)
        if deals:
            for d in deals:
                if d.symbol == symbol and d.entry == 1 and d.profit < 0:
                    comment = d.comment or ''
                    if 'sl' in comment.lower() or d.profit < -(d.volume * 5):
                        t = datetime.fromtimestamp(d.time, TZ).strftime('%H:%M')
                        log("  [品种冷却] {} {}止损@{}，{}h内不开新仓".format(
                            symbol, t, comment, hours))
                        return True
    except:
        pass
    return False

def get_daily_pnl():
    """获取今日净盈亏"""
    try:
        today_start = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        today_ts = int(today_start.timestamp())
        to_ts = int(datetime.now(TZ).timestamp())
        history = mt5.history_deals_get(today_ts, to_ts) or []
        closes = [d for d in history if d.entry == 1]
        total = sum(d.profit + d.swap + d.commission for d in closes)
        return total
    except:
        return 0

# ========== 主程序 ==========

def run():
    log("=" * 60)
    log("30min Patrol - v5.11 累积优化版")
    log("=" * 60)
    info = mt5_connect()
    if not info:
        return

    positions = mt5.positions_get() or []
    log(f"持仓: {len(positions)}/{MAX_POS} 余额=${info.balance:.2f}")
    for p in positions:
        tick = mt5.symbol_info_tick(p.symbol)
        pdir = "BUY" if p.type == 0 else "SELL"
        log(f"  {p.symbol} {pdir} {p.volume}@{p.price_open:.5f} 浮盈=${p.profit:.2f}")

    if len(positions) >= MAX_POS:
        log("持仓已满，跳过")
        mt5.shutdown()
        return

    if trades_this_hour() >= MAX_TRADES_PER_HOUR:
        log(f"[v5频率] 本小时已开{MAX_TRADES_PER_HOUR}单，跳过")
        mt5.shutdown()
        return

    # v5.5 新增：每日亏损上限检查
    daily_pnl = get_daily_pnl()
    if daily_pnl < -DAILY_LOSS_LIMIT:
        log(f"[日内亏损限制] 今日已亏${daily_pnl:.2f}，超过${DAILY_LOSS_LIMIT}上限，停止交易")
        mt5.shutdown()
        return
    elif daily_pnl < 0:
        log(f"[日内亏损] 今日已亏${daily_pnl:.2f}（上限${DAILY_LOSS_LIMIT}）")

    log("扫描市场...")
    results = []
    for sym_name in SYMBOLS:
        tick = mt5.symbol_info_tick(sym_name)
        if not tick or tick.bid == 0:
            continue

        # Kelly 品种过滤
        if not kelly_filter(sym_name):
            log(f"  {sym_name}: [Kelly负] 负期望品种，禁止开仓")
            continue

        direction, strength = calculate_signal_v3(sym_name)

        # 信号强度过滤：Micro-Test 70%+，普通品种 45%+
        min_signal = 60 if is_micro_test(sym_name) else SIGNAL_MIN * 100
        if direction and strength < min_signal:
            log(f"  {sym_name}: 信号{strength:.1f}% < {min_signal:.0f}%{'(Micro-Test门槛)' if is_micro_test(sym_name) else ''}，跳过")
            continue

        quality = get_kelly_quality(sym_name)
        jpy_tag = "[JPY]" if is_jpy(sym_name) else ""
        metal_tag = "[GOLD]" if is_precious_metal(sym_name) else ""
        tag = metal_tag or jpy_tag or ""
        if is_micro_test(sym_name):
            kf_tag = '[Micro-Test]'
        else:
            kf_tag = {'high': '[Kelly高]', 'mid': '[Kelly中]', 'low': '[Kelly低]'}.get(quality, '')
        tier = 'SUPER' if strength >= SUPER_SIGNAL*100 else 'STRONG' if strength >= SIGNAL_MIN * 100 else 'LOW'
        log(f"  {sym_name} {tag} {kf_tag}: {direction or 'NEUTRAL'} {strength:.1f}% [{tier}]")

        if direction and strength >= SIGNAL_MIN * 100:
            results.append((sym_name, direction, strength, quality))

    if not results:
        # 更新状态：记录无信号
        st = load_state()
        st['consecutive_no_signal'] = st.get('consecutive_no_signal', 0) + 1
        save_state(st)
        log("无达标信号（信号>=35%或XAUUSD>=60%，Kelly正期望）")
        mt5.shutdown()
        return

    results.sort(key=lambda x: x[2], reverse=True)
    best_sym, best_dir, best_str, best_qual = results[0]

    log(f"*** 候选: {best_sym} {best_dir} {best_str:.1f}% [{best_qual}]")

    if any(p.symbol == best_sym for p in positions):
        log(f"{best_sym} 已有持仓，跳过")
        mt5.shutdown()
        return

    # v5.11: Signal de-dup check (prevent repeated orders on same candle)
    bar_time = int(mt5.copy_rates_from_pos(best_sym, mt5.TIMEFRAME_H1, 0, 1)[0]['time'])
    if _is_signal_duplicate(best_sym, best_dir, bar_time):
        log(f"  [De-dup] {best_sym} {best_dir} 信号重复，跳过")
        mt5.shutdown()
        return

    if has_correlated_position(best_sym, best_dir, positions):
        log(f"[相关性] {best_sym} 与现有持仓同组，跳过")
        mt5.shutdown()
        return

    if recently_traded(best_sym, hours=CORRELATION_COOLDOWN_H):
        log(f"[冷却] {best_sym} 最近{CORRELATION_COOLDOWN_H}h有交易，跳过")
        mt5.shutdown()
        return

    # v5.5 新增：品种止损冷却检查
    if symbol_hit_sl_recently(best_sym):
        log(f"[品种冷却] {best_sym} 近期止损，跳过")
        mt5.shutdown()
        return

    execute(best_sym, best_dir, best_str)
    mt5.shutdown()

if __name__ == "__main__":
    run()