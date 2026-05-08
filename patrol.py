#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
30分钟巡查 + 自动开仓 — ATR动态止损版
修复 JPY 止损问题：JPY 用更大止损，非 JPY 用标准止损
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ACCOUNT = 52797683
SERVER = "ICMarketsSC-Demo"
THRESHOLD = 0.15        # 信号强度门槛 %
MAX_POS = 3              # v2.1: 5→3（5月7日亏损根因：5个相关品种同向叠加）
RISK_PCT = 0.005       # 0.5% 单笔风险
MAX_LOTS_STRONG = 0.15  # 强信号最大仓位

SYMBOLS = [
    # 直盘
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    # 交叉盘
    "EURJPY", "AUDJPY", "EURGBP", "EURCAD", "GBPAUD", "GBPJPY",
    "EURAUD", "AUDCAD", "AUDCHF", "NZDJPY", "CADJPY", "CHFJPY",
    # 贵金属
    "XAUUSD", "XAGUSD"
]

def log(msg):
    print(msg, flush=True)

def is_jpy(symbol):
    return "JPY" in symbol

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
    """根据 ATR 动态计算止损止盈
    JPY: ATR×1.5 (最低20pip) | 非JPY: ATR×1.5 (最低15pip)
    TP = SL × 2.0 (1:2 盈亏比)
    v2.2: JPY从v2.1固定15pip升级为ATR×1.5最低20pip（回测证明15pip 100%必打）
    """
    atr = calc_atr(symbol)
    sym = mt5.symbol_info(symbol)
    digits = sym.digits
    point = sym.point

    # pip 计算
    pip_div = 100 if digits == 3 else 10000
    pip_size = point * 10 if digits in (3, 5) else point

    # ATR 转 pips
    atr_pips = atr / pip_size

    # JPY 品种：ATR×2.0（进化结果最优参数）
    if is_jpy(symbol):
        sl_pips = max(atr_pips * 2.0, 20)   # v3: ATR×2.0（进化验证最优）
        tp_pips = sl_pips * 2.0
    else:
        sl_pips = max(atr_pips * 1.5, 15)  # 非JPY ATR动态止损
        tp_pips = sl_pips * 2.0

    log(f"  ATR={atr:.5f} | SL={sl_pips:.1f}pips | TP={tp_pips:.1f}pips")
    return sl_pips, tp_pips, digits, point, pip_div

def mt5_connect():
    if not mt5.initialize(login=ACCOUNT, server=SERVER, timeout=10000):
        log("MT5 init failed")
        return None
    info = mt5.account_info()
    log(f"MT5 ok 余额=${info.balance:.2f} 净值=${info.equity:.2f}")
    return info

def calculate_signal_v3(symbol):
    """V3 多时间框架信号算法"""
    try:
        d1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
        h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
        h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        if d1 is None or h4 is None or h1 is None:
            return None, 0

        d1df = pd.DataFrame(d1)
        h4df = pd.DataFrame(h4)
        h1df = pd.DataFrame(h1)

        # D1 方向
        ema20 = d1df['close'].ewm(span=20).mean().iloc[-1]
        ema50 = d1df['close'].ewm(span=50).mean().iloc[-1]
        price = d1df['close'].iloc[-1]
        d1_bull = ema20 > ema50 and price > ema20
        d1_bear = ema20 < ema50 and price < ema20
        if not d1_bull and not d1_bear:
            return None, 0

        direction = "BUY" if d1_bull else "SELL"

        # H4 RSI
        delta4 = h4df['close'].diff()
        gain4 = delta4.clip(lower=0).rolling(14).mean()
        loss4 = (-delta4.clip(upper=0)).rolling(14).mean()
        rs4 = gain4 / loss4.replace(0, np.nan)
        h4_rsi = (100 - 100 / (1 + rs4)).iloc[-1]

        # H1 ADX
        hi, lo, cl = h1df['high'], h1df['low'], h1df['close']
        tr1 = hi - lo
        tr2 = abs(hi - cl.shift(1))
        tr3 = abs(lo - cl.shift(1))
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = tr.rolling(14).mean()
        plus_dm = hi.diff().clip(lower=0)
        minus_dm = (-lo.diff()).clip(upper=0)
        plus_di = 100 * plus_dm.rolling(14).mean() / atr.replace(0, np.nan)
        minus_di = 100 * minus_dm.rolling(14).mean() / atr.replace(0, np.nan)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(14).mean().iloc[-1]

        if not np.isfinite(adx) or adx < 25:
            return None, 0

        # 评分
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

def execute(symbol, direction, strength):
    """执行开仓 — 使用动态止损"""
    tick = mt5.symbol_info_tick(symbol)
    sym = mt5.symbol_info(symbol)
    digits = sym.digits
    price = tick.ask if direction == "BUY" else tick.bid
    log(f"执行: {direction} {symbol} @{price:.{digits}f} (信号强度{strength:.1f}%)")

    # 动态计算 SL/TP
    sl_pips, tp_pips, digits, point, pip_div = get_dynamic_sl_tp(symbol)

    # 计算手数
    pip_size = point * 10 if digits in (3, 5) else point
    pip_value = sym.trade_tick_value * (pip_size / sym.trade_tick_size) if sym.trade_tick_size > 0 else pip_size * sym.trade_contract_size
    info = mt5.account_info()
    risk_amt = info.balance * RISK_PCT
    lots = risk_amt / (sl_pips * pip_value) if sl_pips > 0 and pip_value > 0 else 0.01
    lots = round(max(0.01, min(lots, MAX_LOTS_STRONG)), 2)

    # SL/TP 价格
    sl_dist = sl_pips / pip_div
    tp_dist = tp_pips / pip_div
    pip_unit = 0.0001 if digits == 5 else 0.01
    sl_price = round(price - sl_dist, digits) if direction == "BUY" else round(price + sl_dist, digits)
    tp_price = round(price + tp_dist, digits) if direction == "BUY" else round(price - tp_dist, digits)

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
        "comment": "Patrol Smart",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log(f"  手数={lots} | SL={sl_price:.{digits}f}({sl_pips:.0f}pips) | TP={tp_price:.{digits}f}({tp_pips:.0f}pips)")
    result = mt5.order_send(req)
    log(f"  结果: retcode={result.retcode} {result.comment}")
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log(f"成功开仓 #{result.order}")
        return True
    else:
        log(f"失败: {result.comment}")
        return False

def run():
    log("=" * 60)
    log("30min Patrol — v3 进化优化版 (JPY ATR×2.0)")
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
        return

    # === v2 相关性过滤 ===
    # 已有持仓的货币族
    CORRELATED_GROUPS = {
        "AUD": ["AUDUSD", "AUDCHF", "AUDCAD", "AUDJPY", "EURAUD", "GBPAUD"],
        "EUR": ["EURUSD", "EURGBP", "EURCAD", "EURJPY", "EURAUD"],
        "USD": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],
        "JPY": ["USDJPY", "AUDJPY", "EURJPY", "GBPJPY", "NZDJPY", "CADJPY", "CHFJPY"],
    }

    def has_correlated_position(symbol, direction, positions):
        """检查是否已有相关品种同向持仓"""
        groups = [g for g, syms in CORRELATED_GROUPS.items() if symbol in syms]
        for p in positions:
            if p.symbol == symbol:
                continue  # 跳过自己
            pgroups = [g for g, syms in CORRELATED_GROUPS.items() if p.symbol in syms]
            if any(g in groups for g in pgroups):
                # 检查方向是否相同
                pdir = "BUY" if p.type == 0 else "SELL"
                if pdir == direction:
                    return True
        return False

    def recently_traded(symbol, hours=2):
        """检查该品种是否在最近N小时内有平仓记录（SL/TP/人工平仓）"""
        try:
            to_time = int(datetime.now().timestamp())
            from_time = to_time - hours * 3600
            deals = mt5.history_deals_get(from_time, to_time)
            if deals:
                for d in deals:
                    if d.symbol == symbol and d.comment in ('Patrol Smart', 'Patrol Auto', 'FORCE_CLOSE'):
                        return True
        except:
            pass
        return False

    # 扫描所有品种
    log("扫描市场...")
    results = []
    for sym_name in SYMBOLS:
        tick = mt5.symbol_info_tick(sym_name)
        if not tick or tick.bid == 0:
            continue
        direction, strength = calculate_signal_v3(sym_name)
        jpy_tag = "[JPY]" if is_jpy(sym_name) else ""
        log(f"  {sym_name} {jpy_tag}: {direction or 'NEUTRAL'} {strength:.1f}%")
        if direction and strength >= THRESHOLD * 100:
            results.append((sym_name, direction, strength))

    if not results:
        log("无达标信号")
        return

    # 按强度排序，取最强
    results.sort(key=lambda x: x[2], reverse=True)
    best_sym, best_dir, best_str = results[0]
    log(f"*** 强信号: {best_sym} {best_dir} {best_str:.1f}%")

    # 检查是否已有该品种持仓
    if any(p.symbol == best_sym for p in positions):
        log(f"{best_sym} 已有持仓，跳过")
        return

    # === v2.1 同品种冷却检查 ===
    if recently_traded(best_sym, hours=2):
        log(f"  [v2.1 冷却] {best_sym} 2小时内刚平仓，跳过")
        return

    # === v2 相关性检查 ===
    if has_correlated_position(best_sym, best_dir, positions):
        log(f"  [v2 过滤] {best_sym} 与已有持仓同向相关，跳过")
        return

    # 执行
    execute(best_sym, best_dir, best_str)
    mt5.shutdown()
    log("Patrol完成")

if __name__ == "__main__":
    run()