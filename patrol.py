#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
旺财智能交易系统 v5.0
核心策略：Kelly Criterion 底层决策 | 高胜率才出手 | 少而精
v5变更（2026-05-09）：Kelly公式作为开仓决策核心
  - Kelly f* < 5% 的品种不开仓（负期望）
  - Kelly 手数调整：高Kelly品种可用更大仓位
  - 信号强度门槛：45%（而非15%），过滤低质量信号
  - 预期值 < 0 则过滤
v5.1变更（2026-05-09）：去掉亚洲盘禁止，全天狩猎
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import sys
import io
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ACCOUNT = 52797683
SERVER = "ICMarketsSC-Demo"

# ========== v5 核心参数 ==========
KELLY_MIN_F = 0.05          # Kelly f* < 5% 不开仓（负期望过滤）
SIGNAL_MIN = 0.45           # 信号强度门槛 45%（高于v4.1的15%）
SUPER_SIGNAL = 0.60         # SUPER 信号门槛 60%
RISK_PCT = 0.005            # 每笔风险 0.5%
MAX_POS = 3                  # 最大持仓数
MAX_TRADES_PER_HOUR = 1     # 每小时最多1单
CORRELATION_COOLDOWN_H = 2  # 同组交易冷却

# ========== 手数分档（按Kelly质量） ==========
# 高Kelly品种（kf>10%）：半Kelly > 1%
# 低Kelly品种（kf 5-10%）：当前参数
# 负Kelly品种：彻底屏蔽
KELLY_LOTS = {
    'SUPER': {
        'high_kelly': 0.20,    # Kelly f*>10% 的品种
        'mid_kelly': 0.15,     # Kelly f* 5-10%
        'low_kelly': 0.08,     # Kelly f* < 5% → 用 NORMAL 档
    },
    'STRONG': {
        'high_kelly': 0.15,
        'mid_kelly': 0.10,
        'low_kelly': 0.05,
    }
}

# ========== Kelly 符号质量注册表（基于历史统计） ==========
# 格式：symbol: {'W': win_rate, 'R': avg_win/avg_loss, 'kf': Kelly f*}
# 数据来源：2026-05-09 全历史分析（217笔已平仓）
# 低于5%或负值的品种在 KellyFilter() 中自动屏蔽
KELLY_REGISTRY = {
    # 正期望品种（可交易）
    'USDCAD':  {'W': 0.71, 'R': 0.97, 'kf': 0.420, 'kf_half': 0.210},
    'AUDUSD':  {'W': 0.62, 'R': 0.71, 'kf': 0.094, 'kf_half': 0.047},
    'USDCHF':  {'W': 0.57, 'R': 0.90, 'kf': 0.085, 'kf_half': 0.042},
    'GBPUSD':  {'W': 0.52, 'R': 1.07, 'kf': 0.080, 'kf_half': 0.040},
    'EURUSD':  {'W': 0.35, 'R': 2.06, 'kf': 0.034, 'kf_half': 0.017},
    # 边缘品种（低仓位）
    'XAUUSD':  {'W': 1.00, 'R': 3.00, 'kf': 0.500, 'kf_half': 0.250},  # 2w/0l，特殊处理
    # 负期望品种（永久屏蔽）
    'NZDUSD':  {'W': 0.57, 'R': 0.25, 'kf': -1.129, 'kf_half': -0.564},
    'USDJPY':  {'W': 0.38, 'R': 0.41, 'kf': -1.138, 'kf_half': -0.569},
    'AUDJPY':  {'W': 0.20, 'R': 0.75, 'kf': -0.866, 'kf_half': -0.433},
    'BTCUSD':  {'W': 0.25, 'R': 0.18, 'kf': -3.837, 'kf_half': -1.919},
    # 其余品种未统计，默认中低质量
}

TZ = timezone(timedelta(hours=8))

SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "AUDJPY", "EURGBP", "EURCAD", "GBPAUD", "GBPJPY",
    "EURAUD", "AUDCAD", "AUDCHF", "NZDJPY", "CADJPY", "CHFJPY",
    "XAUUSD", "XAGUSD"
]

# ========== 相关性分组 ==========
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
    """返回品种的 Kelly 质量等级: 'high' / 'mid' / 'low' / 'neg'"""
    info = KELLY_REGISTRY.get(symbol)
    if info is None:
        return 'mid'  # 未知品种默认中等
    kf = info['kf']
    if kf >= 0.10:
        return 'high'
    elif kf >= 0.05:
        return 'mid'
    elif kf > 0:
        return 'low'
    else:
        return 'neg'  # 负Kelly，永久屏蔽

def kelly_filter(symbol):
    """Kelly 门槛过滤：kf < 5% 返回 False（禁止开仓）"""
    info = KELLY_REGISTRY.get(symbol)
    if info is None:
        return True  # 未知品种不屏蔽
    kf = info['kf']
    if kf < KELLY_MIN_F:
        log("  [Kelly过滤] {} kf={:.1f}% < {:.0f}%（负期望）".format(symbol, kf*100, KELLY_MIN_F*100))
        return False
    return True

def calc_expected_value(symbol, direction, strength):
    """计算预期值 EV = p*b - q
    p = 信号强度（%），b = 盈亏比（TP/SL），q = 1-p
    返回 EV > 0 才允许开仓
    """
    p = strength / 100.0  # 信号强度当胜率用
    q = 1 - p
    sl_pips, tp_pips, _, _, _ = get_dynamic_sl_tp(symbol)
    b = tp_pips / sl_pips if sl_pips > 0 else 0
    ev = p * b - q
    log("  [Kelly EV] {} {} p={:.0f}% b={:.2f} EV={:.3f}".format(direction, symbol, p*100, b, ev))
    return ev > 0

def get_kelly_lot_size(symbol, strength):
    """根据 Kelly 质量和信号强度决定手数"""
    quality = get_kelly_quality(symbol)
    if quality == 'neg':
        return 0  # 负Kelly品种不开
    if quality == 'high':
        if strength >= SUPER_SIGNAL * 100:
            return KELLY_LOTS['SUPER']['high_kelly']
        else:
            return KELLY_LOTS['STRONG']['high_kelly']
    elif quality == 'mid':
        if strength >= SUPER_SIGNAL * 100:
            return KELLY_LOTS['SUPER']['mid_kelly']
        else:
            return KELLY_LOTS['STRONG']['mid_kelly']
    else:  # low
        if strength >= SUPER_SIGNAL * 100:
            return KELLY_LOTS['SUPER']['low_kelly']
        else:
            return KELLY_LOTS['STRONG']['low_kelly']

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
    """动态计算止损止盈
    JPY: ATR*2.0（最低20pip）
    贵金属(XAU/XAG): ATR*1.5（最低50pip）
    非JPY/非贵: ATR*1.5（最低15pip）
    TP = SL * 2.0
    """
    atr = calc_atr(symbol)
    if atr is None:
        return 15, 30, 5, 0.00001, 10000

    sym = mt5.symbol_info(symbol)
    digits = sym.digits
    point = sym.point

    if is_precious_metal(symbol):
        pip_size = 0.01
        atr_pips = atr / pip_size
        sl_pips = max(atr_pips * 1.5, 50)
        tp_pips = sl_pips * 2.0
        pip_div = 0.01
    elif is_jpy(symbol):
        pip_div = 100
        pip_size = point * 10
        atr_pips = atr / pip_size
        sl_pips = max(atr_pips * 2.0, 20)
        tp_pips = sl_pips * 2.0
    else:
        pip_div = 10000
        pip_size = point * 10 if digits in (3, 5) else point
        atr_pips = atr / pip_size
        sl_pips = max(atr_pips * 1.5, 15)
        tp_pips = sl_pips * 2.0

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

# ========== 信号计算（不变） ==========

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
        d1_bull = ema20 > ema50 and price > ema20
        d1_bear = ema20 < ema50 and price < ema20
        if not d1_bull and not d1_bear:
            return None, 0
        direction = "BUY" if d1_bull else "SELL"

        delta4 = h4df['close'].diff()
        gain4 = delta4.clip(lower=0).rolling(14).mean()
        loss4 = (-delta4.clip(upper=0)).rolling(14).mean()
        rs4 = gain4 / loss4.replace(0, np.nan)
        h4_rsi = (100 - 100 / (1 + rs4)).iloc[-1]

        hi, lo, cl = h1df['high'], h1df['low'], h1df['close']
        tr1 = hi - lo
        tr2 = abs(hi - cl.shift(1))
        tr3 = abs(lo - cl.shift(1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr_h1 = tr.rolling(14).mean()
        plus_dm = hi.diff().clip(lower=0)
        minus_dm = (-lo.diff()).clip(upper=0)
        plus_di = 100 * plus_dm.rolling(14).mean() / atr_h1.replace(0, np.nan)
        minus_di = 100 * minus_dm.rolling(14).mean() / atr_h1.replace(0, np.nan)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(14).mean().iloc[-1]

        if not np.isfinite(adx) or adx < 25:
            return None, 0

        score = 0
        if d1_bull: score += 3
        elif d1_bear: score -= 3
        if (h4_rsi < 35 and d1_bull) or (h4_rsi > 65 and d1_bear): score += 2
        elif 35 <= h4_rsi <= 65: score += 1
        if adx > 25: score += 2

        strength = max(0, (abs(score) - 2) / 8 * 1.5) * 100
        return direction, round(strength, 1)
    except:
        return None, 0

# ========== 执行开仓（v5 Kelly版） ==========

def execute(symbol, direction, strength):
    """执行开仓：Kelly 决策 + 手数调整"""
    # Step 1: Kelly 过滤
    if not kelly_filter(symbol):
        log("  [Kelly拒绝] {} Kelly f* < {:.0f}%".format(symbol, KELLY_MIN_F*100))
        return False

    # Step 2: Kelly EV 过滤
    if not calc_expected_value(symbol, direction, strength):
        log("  [Kelly EV拒绝] {} 预期值 <= 0".format(symbol))
        return False

    tick = mt5.symbol_info_tick(symbol)
    sym = mt5.symbol_info(symbol)
    digits = sym.digits
    price = tick.ask if direction == "BUY" else tick.bid

    sl_pips, tp_pips, digits, point, pip_div = get_dynamic_sl_tp(symbol)

    # Step 3: 手数 = Kelly 质量分档
    lots = get_kelly_lot_size(symbol, strength)

    # Step 4: 风险校验
    if is_precious_metal(symbol):
        pip_value = (sym.trade_tick_value / sym.trade_tick_size) * 0.01 if sym.trade_tick_size > 0 else 0.01
    else:
        pip_size = point * 10 if digits in (3, 5) else point
        pip_value = sym.trade_tick_value * (pip_size / sym.trade_tick_size) if sym.trade_tick_size > 0 else pip_size

    info = mt5.account_info()
    risk_amt = info.balance * RISK_PCT
    max_by_risk = risk_amt / (sl_pips * pip_value) if sl_pips > 0 and pip_value > 0 else 0.01
    lots = min(lots, max_by_risk)
    lots = round(max(0.01, lots), 2)

    # Step 5: 盈亏比校验
    rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 0
    if rr_ratio < 1.5:
        log(f"  [过滤] 盈亏比{rr_ratio:.1f}<1.5，空间不足，跳过")
        return False

    min_tp = 50 if is_precious_metal(symbol) else 20
    if tp_pips < min_tp:
        log(f"  [过滤] TP仅{tp_pips:.0f}pip<{min_tp}pip，空间不足，跳过")
        return False

    sl_dist = sl_pips / (pip_div if pip_div > 0 else 10000)
    tp_dist = tp_pips / (pip_div if pip_div > 0 else 10000)
    sl_price = round(price - sl_dist, digits) if direction == "BUY" else round(price + sl_dist, digits)
    tp_price = round(price + tp_dist, digits) if direction == "BUY" else round(price - tp_dist, digits)

    quality = get_kelly_quality(symbol)
    kf = KELLY_REGISTRY.get(symbol, {}).get('kf', 0)
    kf_tag = {'high': 'Kelly高', 'mid': 'Kelly中', 'low': 'Kelly低', 'neg': 'Kelly负'}.get(quality, '')
    lot_tag = 'SUPER' if strength >= SUPER_SIGNAL*100 else 'STRONG' if strength >= 45 else 'NORMAL'

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
        "comment": "Patrol Smart v5",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log(f"  [{lot_tag}][{kf_tag}] {direction} {symbol} @{price:.{digits}f}")
    log(f"  手数={lots} | SL={sl_price:.{digits}f}({sl_pips:.0f}pips) | TP={tp_price:.{digits}f}({tp_pips:.0f}pips) | RR={rr_ratio:.1f}:1 | Kelly f*={kf*100:.1f}%")
    result = mt5.order_send(req)
    log(f"  结果: retcode={result.retcode} {result.comment}")
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log(f"成功开仓 #{result.order}")
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
                if d.symbol == symbol and d.comment in ('Patrol Smart', 'Patrol Smart v5', 'Patrol Auto', 'FORCE_CLOSE'):
                    return True
    except:
        pass
    return False

def trades_this_hour():
    try:
        to_time = int(datetime.now().timestamp())
        from_time = to_time - 3600
        deals = mt5.history_deals_get(from_time, to_time)
        return sum(1 for d in deals if d.comment in ('Patrol Smart', 'Patrol Smart v5', 'Patrol Auto') and d.entry in (0,1))
    except:
        return 0

# ========== 主程序 ==========

def run():
    log("=" * 60)
    log("30min Patrol - v5 Kelly Criterion版")
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

    log("扫描市场...")
    results = []
    for sym_name in SYMBOLS:
        tick = mt5.symbol_info_tick(sym_name)
        if not tick or tick.bid == 0:
            continue

        # Step 1: Kelly 品种过滤（负Kelly品种直接跳过）
        quality = get_kelly_quality(sym_name)
        if quality == 'neg':
            log(f"  {sym_name}: [Kelly负] 负期望品种，跳过")
            continue

        direction, strength = calculate_signal_v3(sym_name)

        # Step 2: 信号强度过滤（v5 提高到45%）
        if direction and strength < SIGNAL_MIN * 100:
            log(f"  {sym_name}: 信号{strength:.1f}% < {SIGNAL_MIN*100:.0f}%，跳过")
            continue

        jpy_tag = "[JPY]" if is_jpy(sym_name) else ""
        metal_tag = "[GOLD]" if is_precious_metal(sym_name) else ""
        tag = metal_tag or jpy_tag or ""
        kf_tag = {'high': '[Kelly高]', 'mid': '[Kelly中]', 'low': '[Kelly低]', 'neg': '[Kelly负]'}.get(quality, '')
        log(f"  {sym_name} {tag} {kf_tag}: {direction or 'NEUTRAL'} {strength:.1f}%")

        if direction and strength >= SIGNAL_MIN * 100:
            results.append((sym_name, direction, strength, quality))

    if not results:
        log("无达标信号")
        mt5.shutdown()
        return

    # 按信号强度排序
    results.sort(key=lambda x: x[2], reverse=True)
    best_sym, best_dir, best_str, best_qual = results[0]

    log(f"*** 强信号: {best_sym} {best_dir} {best_str:.1f}% [{best_qual}]")

    if any(p.symbol == best_sym for p in positions):
        log(f"{best_sym} 已有持仓，跳过")
        mt5.shutdown()
        return

    if has_correlated_position(best_sym, best_dir, positions):
        log(f"[相关性] {best_sym} 与现有持仓同组相关，跳过")
        mt5.shutdown()
        return

    if recently_traded(best_sym, hours=CORRELATION_COOLDOWN_H):
        log(f"[冷却] {best_sym} 最近2小时内有交易，跳过")
        mt5.shutdown()
        return

    execute(best_sym, best_dir, best_str)
    mt5.shutdown()

if __name__ == "__main__":
    run()