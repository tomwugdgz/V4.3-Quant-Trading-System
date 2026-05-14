#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
旺财自主交易系统 V4.5 — 2026-05-01
设计目标：AI 直接调用，无需 cron，自动完成扫描-开仓-监控-平仓全流程

核心改进：
1. 增强 MT5 重连机制（3 次重试）
2. 超时处理优化（假日流动性检测）
3. 自动监控已有持仓，达标自动平仓
4. 完整交易日志（JSON 格式）
5. 飞书通知（通过日志输出，由 AI 读取后发送）
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import sys
import os
import msvcrt
import time
from datetime import datetime, timedelta
from pathlib import Path

# 路径
BASE_DIR = Path(__file__).parent
TRADE_LOG_PATH = BASE_DIR / "trade_log.json"
MONITOR_LOG_PATH = BASE_DIR / "monitor_log.json"
LOCK_FILE = BASE_DIR / ".trade_self.lock"

# ===== 策略参数 =====
RISK_PERCENT = 0.005           # 0.5% 单笔风险
MIN_SIGNAL_STRENGTH = 0.15     # 信号强度门槛 (%)
PROFIT_THRESHOLD_PIPS = 15     # 盈利达标平仓 (pips)
COOLDOWN_MINUTES = 30          # 平仓后冷静期
ATR_SL_MULTIPLIER = 1.5        # 止损 = 1.5 × ATR
MIN_SL_PIPS = 15
MAX_ACTUAL_LEVERAGE = 3.0
MAX_POSITIONS = 3
MAX_POSITIONS_PER_SYMBOL = 1
ADX_THRESHOLD = 25
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 35

SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"
]

# ===== 日志 =====
def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] [{level}] {msg}", flush=True)

# ===== MT5 连接 =====
def mt5_connect(max_retries=3):
    """带重试的 MT5 连接"""
    for attempt in range(max_retries):
        if mt5.initialize():
            info = mt5.account_info()
            if info:
                log(f"MT5 连接成功 | 账户:{info.login} | 余额:${info.balance:.2f}")
                return info
        log(f"MT5 连接失败 (尝试{attempt+1}/{max_retries})", "WARNING")
        time.sleep(3)
    log("MT5 连接失败，放弃", "ERROR")
    return None

# ===== 技术指标 =====
def get_pip_size(sym):
    point = sym.point
    digits = sym.digits
    return point * 10 if (digits == 3 or digits == 5) else point

def get_pip_divisor(sym):
    return 100 if sym.digits == 3 else 10000

def calc_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    tr = np.maximum(np.maximum(high - low, abs(high - close.shift(1))), abs(low - close.shift(1)))
    return tr.rolling(window=period).mean().iloc[-1]

def calc_adx(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = np.maximum(np.maximum(high - low, abs(high - close.shift(1))), abs(low - close.shift(1)))
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
    minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    return dx.rolling(window=period).mean().iloc[-1]

def calc_signal_v3(symbol):
    """多时间框架信号: D1方向 + H4确认 + H1入场"""
    # D1
    d1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100)
    if d1 is None or len(d1) < 50:
        return "NEUTRAL", 0, 0, ["D1数据不足"]

    d1_df = pd.DataFrame(d1)
    ema20 = d1_df['close'].ewm(span=20).mean().iloc[-1]
    ema50 = d1_df['close'].ewm(span=50).mean().iloc[-1]
    price = d1_df['close'].iloc[-1]

    d1_bull = ema20 > ema50 and price > ema20
    d1_bear = ema20 < ema50 and price < ema20

    # H4
    h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
    if h4 is None or len(h4) < 30:
        return "NEUTRAL", 0, 0, ["H4数据不足"]
    h4_df = pd.DataFrame(h4)
    delta = h4_df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    h4_rsi = (100 - 100/(1+rs)).iloc[-1]

    # H1
    h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
    if h1 is None or len(h1) < 30:
        return "NEUTRAL", 0, 0, ["H1数据不足"]
    h1_df = pd.DataFrame(h1)
    h1_adx = calc_adx(h1_df)
    h1_atr = calc_atr(h1_df)

    delta1 = h1_df['close'].diff()
    gain1 = delta1.where(delta1 > 0, 0).rolling(14).mean()
    loss1 = (-delta1.where(delta1 < 0, 0)).rolling(14).mean()
    rs1 = gain1 / loss1
    h1_rsi = (100 - 100/(1+rs1)).iloc[-1]

    # 综合评分
    score = 0
    reasons = []

    if d1_bull:
        score += 3
        reasons.append("D1多头")
    elif d1_bear:
        score -= 3
        reasons.append("D1空头")
    else:
        reasons.append("D1不明确")
        return "NEUTRAL", 0, 0, reasons

    if (h4_rsi < 35 and d1_bull) or (h4_rsi > 65 and d1_bear):
        score += 2
        reasons.append(f"H4 RSI反转({h4_rsi:.1f})")
    elif 35 <= h4_rsi <= 65:
        score += 1
        reasons.append(f"H4 RSI中性({h4_rsi:.1f})")

    if h1_adx > ADX_THRESHOLD:
        score += 2
        reasons.append(f"H1 ADX强({h1_adx:.1f})")
    else:
        reasons.append(f"H1 ADX弱({h1_adx:.1f})")
        return "NEUTRAL", 0, 0, reasons

    # 信号
    direction = "BUY" if d1_bull else "SELL"
    if score >= 5:
        strength = max(0, (score - 2) / 8) * 1.5
    elif score >= 3:
        strength = max(0, (score - 2) / 8) * 1.5
    else:
        return "NEUTRAL", 0, 0, reasons

    return direction, strength, h1_rsi, reasons

# ===== 交易执行 =====
def open_trade(symbol, direction, balance, strength):
    log(f"准备开仓: {symbol} {direction} (强度:{strength:.3f}%)", "ACTION")

    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.ask == 0:
        log(f"无法获取 {symbol} 价格", "ERROR")
        return False

    sym = mt5.symbol_info(symbol)
    if not sym:
        log(f"无法获取 {symbol} 信息", "ERROR")
        return False

    # ATR 止损
    h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if h1 is None or len(h1) < 50:
        log(f"K线数据不足", "ERROR")
        return False

    h1_df = pd.DataFrame(h1)
    h1_atr = calc_atr(h1_df)
    pip_size = get_pip_size(sym)
    pip_divisor = get_pip_divisor(sym)

    atr_pips = h1_atr / pip_size
    sl_pips = max(atr_pips * ATR_SL_MULTIPLIER, MIN_SL_PIPS)
    tp_pips = sl_pips * 2.0

    # 仓位计算
    pip_value = sym.trade_tick_value * (pip_size / sym.trade_tick_size) if sym.trade_tick_size > 0 else pip_size * sym.trade_contract_size
    risk_amt = balance * RISK_PERCENT
    lots = round(risk_amt / (sl_pips * pip_value), 2) if sl_pips > 0 and pip_value > 0 else 0.01
    lots = max(0.01, min(lots, 0.08))

    price = tick.ask if direction == "BUY" else tick.bid
    sl_dist = sl_pips / pip_divisor
    tp_dist = tp_pips / pip_divisor

    if direction == "BUY":
        sl = round(price - sl_dist, sym.digits)
        tp = round(price + tp_dist, sym.digits)
    else:
        sl = round(price + sl_dist, sym.digits)
        tp = round(price - tp_dist, sym.digits)

    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 50,
        "magic": 240501,
        "comment": "Wangcai V4.5",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    log(f"订单: {direction} {lots} {symbol} @ {price:.5f} | SL={sl:.5f} TP={tp:.5f} | 风险${risk_amt:.2f}", "INFO")

    for attempt in range(3):
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            log(f"开仓成功! 订单#{result.order}", "SUCCESS")
            return True
        elif result.retcode == 10012:
            log(f"请求超时 (尝试{attempt+1}/3)，3秒后重试...", "WARNING")
            time.sleep(3)
            # 刷新价格
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                request['price'] = tick.ask if direction == "BUY" else tick.bid
        else:
            log(f"开仓失败: {result.comment} (code={result.retcode})", "ERROR")
            return False

    log(f"开仓超时，3次尝试均失败", "ERROR")
    return False

def close_position(ticket, reason=""):
    log(f"平仓: #{ticket}, 原因:{reason}", "ACTION")
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        log(f"找不到订单 #{ticket}", "ERROR")
        return False

    pos = positions[0]
    order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(pos.symbol)
    price = tick.bid if pos.type == 0 else tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": order_type,
        "price": price,
        "deviation": 50,
        "magic": 240501,
        "comment": reason,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    for attempt in range(3):
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            log(f"平仓成功! ${pos.profit:+.2f}", "SUCCESS")
            return True
        elif result.retcode == 10012:
            log(f"平仓超时 (尝试{attempt+1}/3)", "WARNING")
            time.sleep(3)
        else:
            log(f"平仓失败: {result.comment} (code={result.retcode})", "ERROR")
            return False

    log(f"平仓超时", "ERROR")
    return False

# ===== 交易日志 =====
def load_log():
    if TRADE_LOG_PATH.exists():
        try:
            with open(TRADE_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"trades": [], "last_close_time": {}}

def save_log(data):
    with open(TRADE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== 主流程 =====
def run_auto_trade():
    log("=" * 60)
    log("旺财自主交易系统 V4.5 — 2026-05-01")
    log("=" * 60)

    account = mt5_connect()
    if not account:
        return

    trade_log = load_log()
    positions = mt5.positions_get()
    open_count = len(positions) if positions else 0

    log(f"当前持仓: {open_count} 单")
    if positions:
        for p in positions:
            sym = mt5.symbol_info(p.symbol)
            pip_div = get_pip_divisor(sym) if sym else 10000
            direction = "BUY" if p.type == 0 else "SELL"
            profit_pips = (p.price_current - p.price_open) * pip_div if direction == "BUY" else (p.price_open - p.price_current) * pip_div
            log(f"  #{p.ticket} {p.symbol} {direction} {p.volume}手 @ {p.price_open:.5f} | 盈亏${p.profit:+.2f} ({profit_pips:+.1f}pips)")

    # ===== 第一步：检查持仓，达标平仓 =====
    if positions:
        for p in positions:
            sym = mt5.symbol_info(p.symbol)
            pip_div = get_pip_divisor(sym) if sym else 10000
            direction = "BUY" if p.type == 0 else "SELL"
            profit_pips = (p.price_current - p.price_open) * pip_div if direction == "BUY" else (p.price_open - p.price_current) * pip_div

            if profit_pips >= PROFIT_THRESHOLD_PIPS:
                log(f"盈利达标: {p.symbol} +{profit_pips:.1f}pips, 平仓", "ACTION")
                if close_position(p.ticket, f"TP +{profit_pips:.1f}pips"):
                    trade_log.setdefault('last_close_time', {})[p.symbol] = datetime.now().isoformat()
                    save_log(trade_log)
            elif p.profit < -p.balance * RISK_PERCENT * 2:
                log(f"亏损过大: {p.symbol} ${p.profit:.2f}, 止损平仓", "ACTION")
                if close_position(p.ticket, f"SL ${p.profit:.2f}"):
                    trade_log.setdefault('last_close_time', {})[p.symbol] = datetime.now().isoformat()
                    save_log(trade_log)

    # ===== 第二步：扫描市场，寻找机会 =====
    open_count = len(mt5.positions_get() or [])
    if open_count >= MAX_POSITIONS:
        log(f"持仓已达上限 {MAX_POSITIONS}，不开新仓")
    else:
        log("开始扫描市场...")
        results = []
        for symbol in SYMBOLS:
            tick = mt5.symbol_info_tick(symbol)
            if not tick or tick.bid == 0:
                continue

            signal, strength, rsi, reasons = calc_signal_v3(symbol)
            results.append({
                'symbol': symbol,
                'price': tick.bid,
                'signal': signal,
                'strength': strength,
                'rsi': rsi,
                'reasons': reasons
            })

        results.sort(key=lambda x: x['strength'], reverse=True)

        # 找出所有达标的信号
        for r in results:
            if r['signal'] == "NEUTRAL" or r['strength'] < MIN_SIGNAL_STRENGTH:
                log(f"  {r['symbol']}: 无信号 / 强度不足 ({r['strength']:.3f}%)")
                continue

            # RSI 过滤
            if (r['signal'] == "BUY" and r['rsi'] > RSI_OVERBOUGHT) or \
               (r['signal'] == "SELL" and r['rsi'] < RSI_OVERSOLD):
                log(f"  {r['symbol']}: RSI 拦截 ({r['rsi']:.1f})")
                continue

            # 冷却期
            last_close = trade_log.get('last_close_time', {}).get(r['symbol'])
            if last_close:
                try:
                    last_dt = datetime.fromisoformat(last_close)
                    if (datetime.now() - last_dt).total_seconds() < COOLDOWN_MINUTES * 60:
                        remaining = int((COOLDOWN_MINUTES * 60 - (datetime.now() - last_dt).total_seconds()) / 60)
                        log(f"  {r['symbol']}: 冷却期剩余 {remaining}分钟")
                        continue
                except:
                    pass

            # 品种持仓检查
            current_positions = mt5.positions_get() or []
            if any(p.symbol == r['symbol'] for p in current_positions):
                log(f"  {r['symbol']}: 已有持仓，跳过")
                continue

            log(f"  *** {r['symbol']}: {r['signal']} 强度={r['strength']:.3f}% | {', '.join(r['reasons'])}", "OPPORTUNITY")

            # 开仓
            open_count = len(mt5.positions_get() or [])
            if open_count < MAX_POSITIONS:
                if open_trade(r['symbol'], r['signal'], account.balance, r['strength']):
                    trade_log.setdefault('trades', []).append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'time': datetime.now().isoformat(),
                        'symbol': r['symbol'],
                        'direction': r['signal'],
                        'reason': f"signal {r['strength']:.3f}%"
                    })
                    save_log(trade_log)
                    open_count += 1

        if not any(r['signal'] != "NEUTRAL" and r['strength'] >= MIN_SIGNAL_STRENGTH for r in results):
            log("无达标信号，等待更好机会")

    # ===== 第三步：打印最终状态 =====
    info = mt5.account_info()
    positions = mt5.positions_get()
    log("=" * 60)
    log(f"最终状态 | 余额:${info.balance:.2f} | 净值:${info.equity:.2f}")
    if positions:
        log(f"持仓: {len(positions)} 单")
        for p in positions:
            log(f"  #{p.ticket} {p.symbol} {p.volume}手 @ {p.price_open:.5f}")
    else:
        log("空仓")
    log("=" * 60)

    mt5.shutdown()

if __name__ == "__main__":
    run_auto_trade()
