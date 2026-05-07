#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动监控系统 V3.0 — 2026-04-26 重构版
修复清单:
  P0 仓位计算 — pip value 动态获取（非硬编码）
  P0 JPY 止损 — 按 digits 自动判断除数
  P1 信号算法统一 — 删除 find_opportunity.py，只保留此一套
  P1 重复持仓 — 文件锁 + 持仓去重
  P2 方向冲突 — 持仓方向与信号方向校验

策略升级:
  多时间框架: D1 定方向 + H4 确认 + H1 精确入场
  趋势强度: ADX > 25 才开仓
  波动率: ATR 确认止损距离
  相关性: 品种相关系数 >0.7 过滤
  风控层: 8 项独立校验
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import sys
import io
import os
import msvcrt
from datetime import datetime, timedelta
from pathlib import Path

# 强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 路径
BASE_DIR = Path(__file__).parent
TRADE_LOG_PATH = BASE_DIR / "trade_log.json"
LOG_FILE = BASE_DIR / "monitor_log.json"
LOCK_FILE = BASE_DIR / ".monitor.lock"

# ============================================================
# 策略参数
# ============================================================
RISK_PERCENT = 0.005           # 0.5% 单笔风险
MIN_SIGNAL_STRENGTH = 0.15     # 信号强度门槛 (%)
PROFIT_THRESHOLD_PIPS = 10     # 盈利达标平仓
COOLDOWN_MINUTES = 30          # 冷却期
MAX_TRADES_PER_SYMBOL_PER_DAY = 2
MAX_TRADES_PER_DAY = 5
ATR_SL_MULTIPLIER = 1.5        # 止损 = 1.5 × ATR
MIN_SL_PIPS = 15
MAX_ACTUAL_LEVERAGE = 3.0
MAX_POSITIONS = 3
MAX_POSITIONS_PER_SYMBOL = 1

ADX_THRESHOLD = 25             # 趋势强度门槛
CORRELATION_THRESHOLD = 0.7    # 相关性上限

SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"
]

# 品种相关性矩阵 (简化版，基于历史经验)
CORRELATION_MAP = {
    "NZDUSD": ["AUDUSD"],
    "AUDUSD": ["NZDUSD"],
    "EURUSD": ["GBPUSD"],
    "GBPUSD": ["EURUSD"],
    "USDCHF": ["EURUSD", "GBPUSD"],
    "USDCAD": [],
    "USDJPY": [],
}

def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")

# ============================================================
# 文件锁 (P1 修复: 重复持仓)
# ============================================================
def acquire_lock():
    """获取文件锁 (Windows 兼容), 防止并发重复开仓"""
    try:
        lock_fd = open(LOCK_FILE, 'w')
        msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        return lock_fd
    except (IOError, OSError):
        log_message("文件锁已被占用，跳过本轮 (避免并发重复)", "WARNING")
        return None

def release_lock(lock_fd):
    """释放文件锁"""
    if lock_fd:
        try:
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
            lock_fd.close()
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
        except:
            pass

# ============================================================
# 交易日志 & 冷却期
# ============================================================
def load_trade_log():
    if TRADE_LOG_PATH.exists():
        try:
            with open(TRADE_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"trades": [], "last_close_time": {}}

def save_trade_log(log):
    with open(TRADE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def count_today_trades(log):
    today = datetime.now().strftime('%Y-%m-%d')
    return len([t for t in log.get('trades', []) if t.get('date', '') == today])

def count_symbol_today(log, symbol):
    today = datetime.now().strftime('%Y-%m-%d')
    return len([t for t in log.get('trades', []) if t.get('date', '') == today and t.get('symbol', '') == symbol])

def can_trade_symbol(log, symbol):
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()

    last_close = log.get('last_close_time', {}).get(symbol)
    if last_close:
        try:
            last_dt = datetime.fromisoformat(last_close)
            if (now - last_dt).total_seconds() < COOLDOWN_MINUTES * 60:
                remaining = int((COOLDOWN_MINUTES * 60 - (now - last_dt).total_seconds()) / 60)
                return False, f"冷却期，还需等待 {remaining} 分钟"
        except:
            pass

    sym_count = count_symbol_today(log, symbol)
    if sym_count >= MAX_TRADES_PER_SYMBOL_PER_DAY:
        return False, f"{symbol} 今日已交易 {sym_count} 次（上限 {MAX_TRADES_PER_SYMBOL_PER_DAY}）"

    daily_count = count_today_trades(log)
    if daily_count >= MAX_TRADES_PER_DAY:
        return False, f"今日已交易 {daily_count} 笔（上限 {MAX_TRADES_PER_DAY}）"

    return True, "通过"

def record_trade(log, symbol, direction, reason="open"):
    today = datetime.now().strftime('%Y-%m-%d')
    log.setdefault('trades', []).append({
        'date': today,
        'time': datetime.now().isoformat(),
        'symbol': symbol,
        'direction': direction,
        'reason': reason
    })
    cutoff = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    log['trades'] = [t for t in log['trades'] if t.get('date', '') >= cutoff]
    save_trade_log(log)

def record_close(log, symbol):
    log.setdefault('last_close_time', {})[symbol] = datetime.now().isoformat()
    save_trade_log(log)

# ============================================================
# 技术指标计算 (V3: 多时间框架 + ADX + ATR)
# ============================================================
def get_pip_size(symbol_info):
    """获取 1 pip 的大小（P0 修复: JPY 自动判断）"""
    point = symbol_info.point
    digits = symbol_info.digits
    if digits == 3 or digits == 5:  # JPY 品种 (3位) 或 5位小数
        return point * 10
    return point  # 正常 4位小数

def get_pip_divisor(symbol_info):
    """获取 pip 除数（P0 修复: JPY 用 100，非 10000）"""
    if symbol_info.digits == 3:  # JPY
        return 100
    return 10000

def calculate_atr(df, period=14):
    """计算 ATR"""
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    return tr.rolling(window=period).mean().iloc[-1]

def calculate_adx(df, period=14):
    """计算 ADX 趋势强度"""
    high = df['high']
    low = df['low']
    close = df['close']

    # +DM / -DM
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    atr = tr.rolling(window=period).mean()

    plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
    minus_di = 100 * minus_dm.rolling(window=period).mean() / atr

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    return adx.iloc[-1], plus_di.iloc[-1], minus_di.iloc[-1]

def calculate_signal_v3(symbol):
    """
    V3 多时间框架信号算法
    D1 定方向 + H4 确认 + H1 精确入场
    """
    # --- D1 时间框架 ---
    d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
    if d1_rates is None or len(d1_rates) < 50:
        return "NEUTRAL", 0, [], "D1 数据不足"

    d1_df = pd.DataFrame(d1_rates)

    # D1 EMA 20/50
    d1_ema20 = d1_df['close'].ewm(span=20, min_periods=1).mean().iloc[-1]
    d1_ema50 = d1_df['close'].ewm(span=50, min_periods=1).mean().iloc[-1]
    d1_price = d1_df['close'].iloc[-1]

    # D1 方向
    d1_bullish = d1_ema20 > d1_ema50 and d1_price > d1_ema20
    d1_bearish = d1_ema20 < d1_ema50 and d1_price < d1_ema20

    # --- H4 时间框架 ---
    h4_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
    if h4_rates is None or len(h4_rates) < 30:
        return "NEUTRAL", 0, [], "H4 数据不足"

    h4_df = pd.DataFrame(h4_rates)

    # H4 RSI
    delta_h4 = h4_df['close'].diff()
    gain_h4 = delta_h4.where(delta_h4 > 0, 0).rolling(window=14).mean()
    loss_h4 = (-delta_h4.where(delta_h4 < 0, 0)).rolling(window=14).mean()
    rs_h4 = gain_h4 / loss_h4
    h4_rsi = (100 - (100 / (1 + rs_h4))).iloc[-1]

    # H4 MACD
    ema12_h4 = h4_df['close'].ewm(span=12, min_periods=1).mean()
    ema26_h4 = h4_df['close'].ewm(span=26, min_periods=1).mean()
    h4_macd = ema12_h4 - ema26_h4
    h4_macd_signal = h4_macd.ewm(span=9, min_periods=1).mean()

    # --- H1 时间框架 (精确入场) ---
    h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
    if h1_rates is None or len(h1_rates) < 30:
        return "NEUTRAL", 0, [], "H1 数据不足"

    h1_df = pd.DataFrame(h1_rates)

    # H1 ADX
    h1_adx, h1_plus_di, h1_minus_di = calculate_adx(h1_df)

    # H1 ATR
    h1_atr = calculate_atr(h1_df)

    # H1 RSI
    delta_h1 = h1_df['close'].diff()
    gain_h1 = delta_h1.where(delta_h1 > 0, 0).rolling(window=14).mean()
    loss_h1 = (-delta_h1.where(delta_h1 < 0, 0)).rolling(window=14).mean()
    rs_h1 = gain_h1 / loss_h1
    h1_rsi = (100 - (100 / (1 + rs_h1))).iloc[-1]

    # --- 综合评分 ---
    reasons = []
    score = 0

    # 1. D1 趋势方向 (权重: 最高)
    if d1_bullish:
        score += 3
        reasons.append(f"D1 多头趋势 (EMA20={d1_ema20:.5f} > EMA50={d1_ema50:.5f})")
    elif d1_bearish:
        score -= 3
        reasons.append(f"D1 空头趋势 (EMA20={d1_ema20:.5f} < EMA50={d1_ema50:.5f})")
    else:
        reasons.append("D1 趋势不明确")
        return "NEUTRAL", 0, reasons, "D1 无明确方向"

    # 2. H4 RSI 确认
    if h4_rsi < 35 and d1_bullish:
        score += 2
        reasons.append(f"H4 RSI 超卖反弹 ({h4_rsi:.1f})")
    elif h4_rsi > 65 and d1_bearish:
        score += 2
        reasons.append(f"H4 RSI 超买回落 ({h4_rsi:.1f})")
    elif 35 <= h4_rsi <= 65:
        score += 1
        reasons.append(f"H4 RSI 中性 ({h4_rsi:.1f})")
    else:
        reasons.append(f"H4 RSI ({h4_rsi:.1f}) 与 D1 方向不符")

    # 3. H4 MACD 确认
    if h4_macd.iloc[-1] > h4_macd_signal.iloc[-1] and d1_bullish:
        score += 1
        reasons.append("H4 MACD 看涨")
    elif h4_macd.iloc[-1] < h4_macd_signal.iloc[-1] and d1_bearish:
        score += 1
        reasons.append("H4 MACD 看跌")

    # 4. H1 ADX 趋势强度 (铁律: ADX > 25)
    if h1_adx > ADX_THRESHOLD:
        score += 2
        reasons.append(f"H1 ADX={h1_adx:.1f} (趋势强)")
    else:
        reasons.append(f"H1 ADX={h1_adx:.1f} (趋势弱，< {ADX_THRESHOLD})")
        return "NEUTRAL", 0, reasons, f"ADX {h1_adx:.1f} 低于阈值"

    # 5. H1 布林带
    h1_ma20 = h1_df['close'].rolling(20).mean()
    h1_std20 = h1_df['close'].rolling(20).std()
    h1_upper = h1_ma20.iloc[-1] + 2 * h1_std20.iloc[-1]
    h1_lower = h1_ma20.iloc[-1] - 2 * h1_std20.iloc[-1]
    h1_price = h1_df['close'].iloc[-1]

    if h1_price < h1_lower and d1_bullish:
        score += 1
        reasons.append(f"H1 触及布林带下轨 ({h1_price:.5f} < {h1_lower:.5f})")
    elif h1_price > h1_upper and d1_bearish:
        score += 1
        reasons.append(f"H1 触及布林带上轨 ({h1_price:.5f} > {h1_upper:.5f})")

    # --- 确定信号 ---
    if score >= 5:
        signal = "BUY" if d1_bullish else "SELL"
        strength = min(score / 10, 1.0) * 100  # 转换为百分比
    elif score >= 3:
        signal = "BUY" if d1_bullish else "SELL"
        strength = min(score / 10, 1.0) * 100
    else:
        signal = "NEUTRAL"
        strength = 0

    return signal, strength, reasons, f"ADX={h1_adx:.1f}, ATR={h1_atr:.5f}, RSI_H1={h1_rsi:.1f}"

# ============================================================
# 独立风控层 (8 项校验)
# ============================================================
def risk_check(symbol, direction, lot_size, account_info, positions_list):
    """
    独立风控层 — 8 项校验全部通过才允许开仓
    返回: (bool, str)
    """
    checks = []

    # 1. 当前持仓数 < 3
    if len(positions_list) >= MAX_POSITIONS:
        checks.append((False, f"持仓数 {len(positions_list)} >= 上限 {MAX_POSITIONS}"))
    else:
        checks.append((True, "持仓数通过"))

    # 2. 该品种持仓数 < 1
    sym_positions = [p for p in positions_list if p.symbol == symbol]
    if len(sym_positions) >= MAX_POSITIONS_PER_SYMBOL:
        checks.append((False, f"{symbol} 已有 {len(sym_positions)} 单"))
    else:
        checks.append((True, f"{symbol} 无重复持仓"))

    # 3. 日累计亏损 < 3%
    # (简化：检查今日已平仓的亏损，需要从 trade_log 获取)
    # 这里用净值/余额比近似
    if account_info.equity < account_info.balance * 0.97:
        checks.append((False, f"净值 {account_info.equity:.2f} < 余额的 97% (日亏红线)"))
    else:
        checks.append((True, "日亏损通过"))

    # 4. 实际杠杆 < 3x
    total_notional = 0
    for pos in positions_list:
        si = mt5.symbol_info(pos.symbol)
        if si:
            total_notional += pos.volume * si.trade_contract_size
    current_notional = total_notional + lot_size * mt5.symbol_info(symbol).trade_contract_size if mt5.symbol_info(symbol) else total_notional
    actual_leverage = current_notional / account_info.balance if account_info.balance > 0 else 0
    if actual_leverage > MAX_ACTUAL_LEVERAGE:
        checks.append((False, f"实际杠杆 {actual_leverage:.2f}x > 上限 {MAX_ACTUAL_LEVERAGE}x"))
    else:
        checks.append((True, f"实际杠杆 {actual_leverage:.2f}x 通过"))

    # 5. 保证金水平 > 200%
    if account_info.margin > 0:
        margin_level = account_info.equity / account_info.margin * 100
        if margin_level < 200:
            checks.append((False, f"保证金水平 {margin_level:.0f}% < 200%"))
        else:
            checks.append((True, f"保证金水平 {margin_level:.0f}% 通过"))
    else:
        checks.append((True, "无保证金占用"))

    # 6. 品种相关性检查
    correlated_symbols = CORRELATION_MAP.get(symbol, [])
    for cs in correlated_symbols:
        if any(p.symbol == cs for p in positions_list):
            checks.append((False, f"{symbol} 与持仓 {cs} 相关性 > {CORRELATION_THRESHOLD}"))
            break
    else:
        checks.append((True, "相关性通过"))

    # 7. 冷却期检查 (在 can_trade_symbol 中已做，这里跳过)
    checks.append((True, "冷却期 (外层检查)"))

    # 8. 信号强度 >= 0.15% (外层检查)
    checks.append((True, "信号强度 (外层检查)"))

    # 汇总
    failed = [c for c in checks if not c[0]]
    if failed:
        reasons = "; ".join([f[1] for f in failed])
        return False, reasons
    return True, "全部通过"

# ============================================================
# 交易执行 (P0 修复版)
# ============================================================
def execute_trade(symbol, direction, balance, signal_strength=0.0):
    log_message(f"准备开仓：{symbol} {direction} (信号强度：{signal_strength:.3f}%)", "ACTION")

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        log_message(f"无法获取 {symbol} 价格", "ERROR")
        return False

    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        log_message(f"无法获取 {symbol} 信息", "ERROR")
        return False

    # H1 ATR 计算
    h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if h1_rates is None or len(h1_rates) < 50:
        log_message(f"无法获取 {symbol} K 线数据", "ERROR")
        return False

    h1_df = pd.DataFrame(h1_rates)
    h1_atr = calculate_atr(h1_df)
    pip_size = get_pip_size(symbol_info)
    pip_divisor = get_pip_divisor(symbol_info)

    atr_in_pips = h1_atr / pip_size
    sl_pips = max(atr_in_pips * ATR_SL_MULTIPLIER, MIN_SL_PIPS)
    tp_pips = sl_pips * 2.0

    # P0 修复: 动态 pip value
    pip_size = get_pip_size(symbol_info)  # 1 pip 的价格距离
    if symbol_info.trade_tick_size > 0:
        pip_value_per_lot = symbol_info.trade_tick_value * (pip_size / symbol_info.trade_tick_size)
    else:
        pip_value_per_lot = pip_size * symbol_info.trade_contract_size

    risk_amount = balance * RISK_PERCENT
    lot_by_risk = round(risk_amount / (sl_pips * pip_value_per_lot), 2) if sl_pips > 0 and pip_value_per_lot > 0 else 0.01

    # 杠杆校验
    margin_per_lot = symbol_info.margin_initial
    if margin_per_lot and margin_per_lot > 0:
        max_lots_by_margin = balance / margin_per_lot
        lot_by_risk = min(lot_by_risk, max_lots_by_margin)

    lot_size = max(0.01, min(lot_by_risk, 0.08))
    lot_size = round(lot_size, 2)

    log_message(f"仓位(P0修复)：风险法={lot_by_risk}手 | pip_value={pip_value_per_lot:.4f} | SL={sl_pips:.1f}pip | ATR={atr_in_pips:.1f}pip | 最终={lot_size}手", "INFO")

    if lot_size < 0.01:
        log_message(f"仓位过小 ({lot_size})，跳过", "WARNING")
        return False

    # 开仓价格
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid

    # P0 修复: 止损止盈按 pip_divisor 计算
    sl_distance = sl_pips / pip_divisor
    tp_distance = tp_pips / pip_divisor

    if direction == "BUY":
        sl_price = round(price - sl_distance, symbol_info.digits)
        tp_price = round(price + tp_distance, symbol_info.digits)
    else:
        sl_price = round(price + sl_distance, symbol_info.digits)
        tp_price = round(price - tp_distance, symbol_info.digits)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 50,
        "magic": 234000,
        "comment": "auto_monitor_v3",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log_message(f"订单：{symbol} {direction} {lot_size}手 @ {price:.5f}, SL:{sl_price:.5f}, TP:{tp_price:.5f}", "INFO")

    for attempt in range(2):
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            log_message(f"开仓成功：{symbol} {direction} {lot_size}手 | 订单号：{result.order}", "SUCCESS")
            send_feishu_notification(f"开仓：{symbol} {direction} {lot_size}手 @ {price:.5f} | SL:{sl_price:.5f} TP:{tp_price:.5f} | 信号:{signal_strength:.3f}%")
            return True
        else:
            log_message(f"开仓失败 (尝试{attempt+1}/2): {result.comment} (retcode={result.retcode})", "ERROR")
            if result.retcode in [mt5.TRADE_RETCODE_INVALID_PRICE, mt5.TRADE_RETCODE_REQUOTE]:
                tick = mt5.symbol_info_tick(symbol)
                request['price'] = tick.ask if direction == "BUY" else tick.bid

    log_message(f"开仓失败，已重试", "ERROR")
    return False

# ============================================================
# 扫描市场 (V3)
# ============================================================
def scan_market_v3():
    """V3 多时间框架扫描"""
    log_message("开始 V3 市场扫描...")
    results = []

    for symbol in SYMBOLS:
        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.bid <= 0:
            continue

        signal, strength, reasons, meta = calculate_signal_v3(symbol)
        spread = (tick.ask - tick.bid) * 10000

        results.append({
            'symbol': symbol,
            'price': tick.bid,
            'spread': spread,
            'signal': signal,
            'strength': strength,
            'reasons': reasons,
            'meta': meta
        })

    results.sort(key=lambda x: x['strength'], reverse=True)

    best = None
    for r in results:
        if r['signal'] != "NEUTRAL" and r['strength'] >= MIN_SIGNAL_STRENGTH:
            best = r
            break

    log_message(f"扫描完成，找到 {len(results)} 个品种，最佳：{best['symbol']} ({best['strength']:.3f}%)" if best else f"扫描完成，{len(results)} 个品种，无达标信号")
    return results, best

# ============================================================
# 持仓检查
# ============================================================
def check_positions():
    positions = mt5.positions_get()
    if not positions:
        log_message("无持仓", "INFO")
        return []

    result = []
    for pos in positions:
        pip_divisor = get_pip_divisor(mt5.symbol_info(pos.symbol))
        direction = "BUY" if pos.type == 0 else "SELL"
        if direction == "BUY":
            profit_pips = (pos.price_current - pos.price_open) * pip_divisor
        else:
            profit_pips = (pos.price_open - pos.price_current) * pip_divisor

        result.append({
            'ticket': pos.ticket,
            'symbol': pos.symbol,
            'direction': direction,
            'volume': pos.volume,
            'entry_price': pos.price_open,
            'current_price': pos.price_current,
            'profit_usd': pos.profit,
            'profit_pips': profit_pips,
            'sl': pos.sl,
            'tp': pos.tp
        })

        status = "盈利" if pos.profit > 0 else "亏损"
        log_message(f"{pos.symbol} {direction}: {profit_pips:+.1f} pips (${pos.profit:+.2f}) [{status}]")

    return result

# ============================================================
# 平仓
# ============================================================
def close_position(ticket, reason=""):
    log_message(f"平仓：订单 {ticket}, 原因：{reason}", "ACTION")
    position = mt5.positions_get(ticket=ticket)
    if not position:
        log_message(f"找不到订单 {ticket}", "ERROR")
        return False

    pos = position[0]
    order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(pos.symbol)
    price = tick.ask if pos.type == 0 else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": reason,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_message(f"平仓成功：{pos.symbol} {pos.volume}手 @ {price:.5f}, ${pos.profit:+.2f}", "SUCCESS")
        return True
    else:
        log_message(f"平仓失败：{result.comment} (retcode={result.retcode})", "ERROR")
        return False

# ============================================================
# 通知
# ============================================================
def send_feishu_notification(message):
    log_message(f"飞书通知：{message}", "NOTIFY")

# ============================================================
# 主循环 V3
# ============================================================
def main_loop():
    log_message("=" * 60)
    log_message("自动监控系统 V3.0 (2026-04-26 重构)")
    log_message("多时间框架: D1+H4+H1 | ADX>25 | ATR 止损 | 独立风控层")
    log_message("=" * 60)

    if not mt5.initialize():
        log_message("MT5 初始化失败", "ERROR")
        return

    account = mt5.account_info()
    log_message(f"账户：{account.login} | 余额：${account.balance:.2f} | 杠杆：1:{account.leverage}")

    # 获取文件锁
    lock_fd = acquire_lock()
    if not lock_fd:
        log_message("跳过本轮 (文件锁占用)", "WARNING")
        mt5.shutdown()
        return

    try:
        # 扫描
        results, best = scan_market_v3()

        # 检查持仓
        positions = check_positions()
        trade_log = load_trade_log()

        # 决策：平仓
        decisions = []
        for pos in positions:
            if pos['profit_pips'] >= PROFIT_THRESHOLD_PIPS:
                decisions.append({
                    'action': 'CLOSE',
                    'ticket': pos['ticket'],
                    'symbol': pos['symbol'],
                    'reason': f"盈利达标：+{pos['profit_pips']:.1f} pips (${pos['profit_usd']:+.2f})"
                })
            elif best and best['symbol'] == pos['symbol']:
                if (pos['direction'] == 'BUY' and best['signal'] == 'SELL' and best['strength'] >= 0.20) or \
                   (pos['direction'] == 'SELL' and best['signal'] == 'BUY' and best['strength'] >= 0.20):
                    decisions.append({
                        'action': 'CLOSE',
                        'ticket': pos['ticket'],
                        'symbol': pos['symbol'],
                        'reason': f"强信号反转：{best['signal']} {best['strength']:.3f}%"
                    })

        # 执行平仓
        for decision in decisions:
            if decision['action'] == 'CLOSE':
                if close_position(decision['ticket'], decision['reason']):
                    record_close(trade_log, decision['symbol'])
                    record_trade(trade_log, decision['symbol'], 'CLOSE', decision['reason'])

        # 重新获取持仓
        current_positions_raw = mt5.positions_get() or []
        open_count = len(current_positions_raw)

        # 开仓决策 (含 8 项风控校验)
        if open_count < MAX_POSITIONS and best and best['strength'] >= MIN_SIGNAL_STRENGTH:
            passed1, msg1 = can_trade_symbol(trade_log, best['symbol'])
            if not passed1:
                log_message(f"跳过 {best['symbol']}: {msg1}", "WARNING")
            else:
                # 风控层校验
                passed2, msg2 = risk_check(best['symbol'], best['signal'], 0.01, account, current_positions_raw)
                if not passed2:
                    log_message(f"风控拒绝 {best['symbol']}: {msg2}", "WARNING")
                else:
                    log_message(f"强信号：{best['symbol']} {best['signal']} ({best['strength']:.3f}%) | 风控通过", "OPPORTUNITY")
                    execute_trade(best['symbol'], best['signal'], account.balance, best['strength'])
                    record_trade(trade_log, best['symbol'], best['signal'], "signal_open")
        elif best:
            log_message(f"无达标信号：{best['symbol']} 强度 {best['strength']:.3f}% < {MIN_SIGNAL_STRENGTH:.0%}", "INFO")

        # 打印扫描结果
        print("\n--- V3 扫描结果 ---")
        for r in results:
            indicator = "+" if r['signal'] == "BUY" else ("-" if r['signal'] == "SELL" else "·")
            print(f"  {indicator} {r['symbol']}: {r['signal']} | 强度={r['strength']:.3f}% | 价格={r['price']:.5f} | {r['meta']}")

    finally:
        release_lock(lock_fd)

    # 保存日志
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'account_balance': account.balance,
        'positions_count': len(positions),
        'best_signal': best['symbol'] if best else None,
        'best_strength': best['strength'] if best else 0,
    }

    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append(log_data)
    logs = logs[-50:]
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    log_message(f"日志已保存")
    log_message("=" * 60)
    mt5.shutdown()

if __name__ == "__main__":
    main_loop()
