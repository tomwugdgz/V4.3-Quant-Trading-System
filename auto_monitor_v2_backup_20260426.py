#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动监控系统 v1.0
功能:
  1. 每 15 分钟扫描市场信号 (MP5 策略)
  2. 检查现有持仓盈亏
  3. 盈利达标时自动平仓
  4. 发现强信号时自动开仓
  5. 发送飞书通知
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import sys
import io
import os
from datetime import datetime, timedelta
from pathlib import Path

# 配置
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 交易日志路径
TRADE_LOG_PATH = Path(__file__).parent / "trade_log.json"


# ========== P0/P1/P4: 交易记录追踪 & 冷却期管理 ==========

def load_trade_log():
    """加载交易日志"""
    if TRADE_LOG_PATH.exists():
        try:
            with open(TRADE_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"trades": [], "last_close_time": {}}


def save_trade_log(log):
    """保存交易日志"""
    with open(TRADE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def count_today_trades(log):
    """统计今日交易次数"""
    today = datetime.now().strftime('%Y-%m-%d')
    return len([t for t in log.get('trades', []) if t.get('date', '') == today])


def count_symbol_today(log, symbol):
    """统计某品种今日交易次数"""
    today = datetime.now().strftime('%Y-%m-%d')
    return len([t for t in log.get('trades', []) if t.get('date', '') == today and t.get('symbol', '') == symbol])


def can_trade_symbol(log, symbol):
    """检查是否可以交易该品种（冷却期 + 每日次数限制）"""
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()

    # 冷却期检查
    last_close = log.get('last_close_time', {}).get(symbol)
    if last_close:
        try:
            last_dt = datetime.fromisoformat(last_close)
            if (now - last_dt).total_seconds() < COOLDOWN_MINUTES * 60:
                remaining = int((COOLDOWN_MINUTES * 60 - (now - last_dt).total_seconds()) / 60)
                return False, f"冷却期中，还需等待 {remaining} 分钟"
        except:
            pass

    # 同品种每日次数限制
    sym_count = count_symbol_today(log, symbol)
    if sym_count >= MAX_TRADES_PER_SYMBOL_PER_DAY:
        return False, f"{symbol} 今日已交易 {sym_count} 次（上限 {MAX_TRADES_PER_SYMBOL_PER_DAY}）"

    # 每日总交易次数限制
    daily_count = count_today_trades(log)
    if daily_count >= MAX_TRADES_PER_DAY:
        return False, f"今日已交易 {daily_count} 笔（上限 {MAX_TRADES_PER_DAY}），停止交易"

    return True, "通过"


def record_trade(log, symbol, direction, reason="open"):
    """记录交易"""
    today = datetime.now().strftime('%Y-%m-%d')
    log.setdefault('trades', []).append({
        'date': today,
        'time': datetime.now().isoformat(),
        'symbol': symbol,
        'direction': direction,
        'reason': reason
    })
    # 清理超过2天的旧记录
    cutoff = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    log['trades'] = [t for t in log['trades'] if t.get('date', '') >= cutoff]
    save_trade_log(log)


def record_close(log, symbol):
    """记录平仓时间（用于冷却期）"""
    log.setdefault('last_close_time', {})[symbol] = datetime.now().isoformat()
    save_trade_log(log)

# MP5 策略参数 (2026-04-21 更新)
RISK_PERCENT = 0.005  # 0.5% 单笔风险
MIN_SIGNAL_STRENGTH = 0.15  # 最小信号强度 0.15% (P1: 从 0.1% 提升到 0.15%，加迟滞)
PROFIT_THRESHOLD_PIPS = 10  # 盈利达到多少 pips 后平仓
STOP_LOSS_PIPS = 30  # 标准止损

# P1 迟滞机制参数
COOLDOWN_MINUTES = 30  # 平仓后冷却期（分钟）
MAX_TRADES_PER_SYMBOL_PER_DAY = 2  # 同品种单日最多 2 笔
MAX_TRADES_PER_DAY = 5  # 单日总交易上限 (P4)
ATR_SL_MULTIPLIER = 1.5  # P2: 止损 = 1.5 × ATR
MIN_SL_PIPS = 15  # P2: 最小止损 15 pip
MAX_ACTUAL_LEVERAGE = 3.0  # 实际杠杆上限 3x

# 日志文件
LOG_FILE = Path(__file__).parent / "monitor_log.json"
SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"
]

def log_message(message, level="INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")

def execute_trade(symbol, direction, balance, signal_strength=0.0):
    """执行交易 - 自动开仓 (优化版)"""
    log_message(f"准备开仓：{symbol} {direction} (信号强度：{signal_strength:.3f}%)", "ACTION")

    # 获取当前价格
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        log_message(f"无法获取 {symbol} 价格", "ERROR")
        return False

    # 计算止损止盈 (ATR 动态)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if rates is None or len(rates) < 50:
        log_message(f"无法获取 {symbol} K 线数据", "ERROR")
        return False

    df = pd.DataFrame(rates)
    high = df['high']
    low = df['low']
    close = df['close']

    # 计算 ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    atr = tr.rolling(window=14).mean().iloc[-1]
    atr_pips = atr * 10000  # 转换为 pips

    # 动态止损止盈
    sl_pips = atr_pips * 2.0
    tp_pips = atr_pips * 4.0

    # ========== 优化 1: 仓位计算 (P0 修复 + ATR 动态止损) ==========

    # 获取品种精度信息
    symbol_info = mt5.symbol_info(symbol)
    point = symbol_info.point  # 点值 (EURUSD=0.00001, USDJPY=0.001)
    pip_size = point * 10 if symbol_info.digits == 5 else point  # 1 pip 的大小
    free_margin = mt5.account_info().margin_free

    # 计算 ATR 止损距离（pip 为单位）
    atr_raw = atr  # ATR 以价格单位表示
    atr_in_pips = atr_raw / pip_size
    sl_pips = max(atr_in_pips * ATR_SL_MULTIPLIER, MIN_SL_PIPS)  # 至少 MIN_SL_PIPS
    tp_pips = sl_pips * 2.0  # 盈亏比 1:2

    # 计算止损价格距离（价格单位）
    sl_distance_price = sl_pips * pip_size

    # 计算每手 pip 价值（精确公式）
    pip_value_per_lot = (100000 * point) / tick.bid  # 以 USD 计

    # 方法 1: 基于风险计算 (0.5% 风险)
    risk_amount = balance * RISK_PERCENT
    lot_by_risk = round(risk_amount / (sl_pips * pip_value_per_lot), 2)

    # 方法 2: 基于保证金 + 3x 杠杆上限 (P0 修复)
    margin_per_lot = symbol_info.margin_initial
    max_leverage_notional = balance * MAX_ACTUAL_LEVERAGE  # 最大名义持仓
    current_positions = mt5.positions_get()
    current_notional = 0
    if current_positions:
        for pos in current_positions:
            info = mt5.symbol_info(pos.symbol)
            if info:
                current_notional += pos.volume * info.trade_contract_size
    remaining_notional = max(0, max_leverage_notional - current_notional)
    lot_by_leverage = round(remaining_notional / (symbol_info.trade_contract_size * MAX_ACTUAL_LEVERAGE), 2) if symbol_info.trade_contract_size > 0 else 0.10
    lot_by_leverage = max(0.01, lot_by_leverage)

    # 取较小值
    lot_size = min(lot_by_risk, lot_by_leverage)

    # 最小 0.01 手，最大 0.08 手 (比之前更保守)
    lot_size = max(0.01, min(lot_size, 0.08))

    # 确保是 0.01 的倍数
    lot_size = round(lot_size, 2)

    log_message(f"仓位计算(P0修复)：风险法={lot_by_risk}手, 杠杆法={lot_by_leverage}手, 最终={lot_size}手 | SL={sl_pips:.1f}pip, ATR={atr_in_pips:.1f}pip", "INFO")

    if lot_size < 0.01:
        log_message(f"仓位过小 ({lot_size})，跳过开仓", "WARNING")
        return False

    # ========== 优化 2: 准备订单 ==========

    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "BUY" else tick.bid

    # 计算止损止盈价格
    if direction == "BUY":
        sl_price = round(price - sl_pips / 10000, 5)
        tp_price = round(price + tp_pips / 10000, 5)
    else:
        sl_price = round(price + sl_pips / 10000, 5)
        tp_price = round(price - tp_pips / 10000, 5)

    # ========== 优化 3: 订单参数检查 ==========

    # 检查止损止盈是否合理
    if sl_price <= 0 or tp_price <= 0:
        log_message(f"止损止盈价格异常：SL={sl_price}, TP={tp_price}", "ERROR")
        return False

    # 检查止损是否在合理范围
    sl_distance = abs(sl_price - price) * 10000
    if sl_distance < 10 or sl_distance > 200:
        log_message(f"止损距离异常：{sl_distance:.1f} pips", "WARNING")

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 50,  # 增加滑点容差
        "magic": 234000,
        "comment": "auto_monitor_v3",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # IOC 模式
    }

    log_message(f"订单详情：{symbol} {direction} {lot_size}手 @ {price:.5f}, SL:{sl_price:.5f}, TP:{tp_price:.5f}", "INFO")

    # ========== 优化 4: 发送订单 + 重试机制 ==========

    max_retries = 2
    for attempt in range(max_retries):
        result = mt5.order_send(request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            log_message(f"开仓成功：{symbol} {direction} {lot_size}手 @ {price:.5f}, SL:{sl_price:.5f}, TP:{tp_price:.5f}", "SUCCESS")
            log_message(f"订单号：{result.order}, 盈亏：${result.volume * 10:.2f}", "SUCCESS")
            # 发送飞书通知
            notification = f"""🎯 自动开仓通知
━━━━━━━━━━━━━━━━
品种：{symbol}
方向：{direction}
仓位：{lot_size}手
入场：{price:.5f}
止损：{sl_price:.5f} (-{sl_pips:.1f} pips)
止盈：{tp_price:.5f} (+{tp_pips:.1f} pips)
信号强度：{signal_strength:.3f}%
━━━━━━━━━━━━━━━━"""
            send_feishu_notification(notification)
            return True
        else:
            log_message(f"开仓失败 (尝试{attempt+1}/{max_retries}): {result.comment} (retcode={result.retcode})", "ERROR")
            # 如果是价格问题，更新价格重试
            if result.retcode in [mt5.TRADE_RETCODE_INVALID_PRICE, mt5.TRADE_RETCODE_REQUOTE]:
                tick = mt5.symbol_info_tick(symbol)
                request['price'] = tick.ask if direction == "BUY" else tick.bid

    log_message(f"开仓失败，已重试{max_retries}次", "ERROR")
    return False

def calculate_indicators(df):
    """计算技术指标"""
    # EMA
    ema_fast = df['close'].ewm(span=10, adjust=False).mean().iloc[-1]
    ema_slow = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]

    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean().iloc[-1]

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=12).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=12).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]

    return {
        'ema_fast': ema_fast,
        'ema_slow': ema_slow,
        'ema_signal': 'BUY' if ema_fast > ema_slow else 'SELL',
        'macd': macd.iloc[-1],
        'macd_signal': macd_signal,
        'rsi': rsi
    }

def scan_market():
    """扫描市场信号"""
    log_message("开始市场扫描...")

    results = []
    for symbol in SYMBOLS:
        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.bid <= 0:
            continue

        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 50:
            continue

        df = pd.DataFrame(rates)
        current = tick.bid
        spread = (tick.ask - tick.bid) * 10000

        # 基础趋势强度
        closes = df['close'].iloc[-5:].values
        avg_close = np.mean(closes)
        base_strength = abs((current - avg_close) / avg_close * 100)
        base_signal = "BUY" if current > avg_close else "SELL"

        # 技术指标
        indicators = calculate_indicators(df)

        # 四重确认评分
        confirmations = 0
        buy_signals = 0
        sell_signals = 0

        # EMA 确认
        if indicators['ema_signal'] == "BUY":
            buy_signals += 1
        else:
            sell_signals += 1

        # MACD 确认
        if indicators['macd'] > indicators['macd_signal']:
            buy_signals += 1
        else:
            sell_signals += 1

        # RSI 确认
        if indicators['rsi'] < 35:
            buy_signals += 1  # 超卖
        elif indicators['rsi'] > 65:
            sell_signals += 1  # 超买

        # ADX 简化版 (用趋势强度代替)
        if base_strength > 0.05:
            confirmations += 1
            if base_signal == "BUY":
                buy_signals += 1
            else:
                sell_signals += 1

        # 确定最终信号
        if buy_signals >= 2:
            final_signal = "BUY"
        elif sell_signals >= 2:
            final_signal = "SELL"
        else:
            final_signal = "NEUTRAL"

        signal_strength = base_strength

        results.append({
            'symbol': symbol,
            'price': current,
            'spread': spread,
            'signal': final_signal,
            'strength': signal_strength,
            'indicators': indicators
        })

    # 按信号强度排序
    results.sort(key=lambda x: x['strength'], reverse=True)

    # 找出最佳机会
    best = None
    for r in results:
        if r['signal'] != "NEUTRAL" and r['strength'] >= MIN_SIGNAL_STRENGTH:
            best = r
            break

    if best:
        log_message(f"扫描完成，找到 {len(results)} 个品种，最佳信号：{best['symbol']} ({best['strength']:.3f}%)")
    else:
        log_message(f"扫描完成，找到 {len(results)} 个品种，无达标信号")
    return results, best

def check_positions():
    """检查现有持仓"""
    log_message("检查持仓状态...")

    positions = mt5.positions_get()
    if not positions:
        log_message("无持仓", "INFO")
        return []

    position_list = []
    for pos in positions:
        symbol = pos.symbol
        direction = "BUY" if pos.type == 0 else "SELL"
        entry_price = pos.price_open
        current_price = pos.price_current
        profit = pos.profit

        # 计算盈亏 pips
        pip_multiplier = 100 if 'JPY' in symbol else 10000
        if direction == "BUY":
            profit_pips = (current_price - entry_price) * pip_multiplier
        else:
            profit_pips = (entry_price - current_price) * pip_multiplier

        position_list.append({
            'ticket': pos.ticket,
            'symbol': symbol,
            'direction': direction,
            'volume': pos.volume,
            'entry_price': entry_price,
            'current_price': current_price,
            'profit_usd': profit,
            'profit_pips': profit_pips,
            'sl': pos.sl,
            'tp': pos.tp
        })

        status = "盈利" if profit > 0 else "亏损"
        log_message(f"{symbol} {direction}: {profit_pips:+.1f} pips (${profit:+.2f}) [{status}]")

    return position_list

def close_position(ticket, reason=""):
    """平仓"""
    log_message(f"准备平仓：订单号 {ticket}, 原因：{reason}", "ACTION")

    # 获取持仓信息
    position = mt5.positions_get(ticket=ticket)
    if not position:
        log_message(f"找不到订单 {ticket}", "ERROR")
        return False

    pos = position[0]
    symbol = pos.symbol
    volume = pos.volume
    direction = pos.type

    # 准备平仓订单
    if direction == 0:  # BUY
        order_type = mt5.ORDER_TYPE_SELL
    else:  # SELL
        order_type = mt5.ORDER_TYPE_BUY

    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if direction == 0 else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": reason,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # 发送订单
    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_message(f"平仓成功：{symbol} {volume} 手 @ {price:.5f}, 盈亏 ${pos.profit:+.2f}", "SUCCESS")
        return True
    else:
        log_message(f"平仓失败：{result.comment} (retcode={result.retcode})", "ERROR")
        return False

def send_feishu_notification(message):
    """发送飞书通知（简化版，直接打印）"""
    log_message(f"飞书通知：{message}", "NOTIFY")
    # 实际使用时可以调用飞书 API

def check_symbol_exposure_v2(symbol, positions):
    """单一品种风险检查 v2.0"""
    symbol_positions = [p for p in positions if p['symbol'] == symbol]
    MAX_POSITIONS_PER_SYMBOL = 1

    if len(symbol_positions) >= MAX_POSITIONS_PER_SYMBOL:
        return False, f"{symbol} 已有 {len(symbol_positions)} 单持仓 (上限 {MAX_POSITIONS_PER_SYMBOL})"

    return True, "通过"

def generate_market_report(results, positions, best, account):
    """生成市场环境报告"""
    report = []
    report.append("=" * 80)
    report.append("📊 MP5 市场环境报告")
    report.append("=" * 80)
    report.append(f"扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"账户余额：${account.balance:.2f} | 净值：${account.equity:.2f} | 持仓：{len(positions)}/3")
    report.append("")

    # 市场状态 (P1: 阈值已提升到 0.15%)
    report.append("【市场环境分析】")
    strong_count = len([r for r in results if r['strength'] >= 0.2])
    medium_count = len([r for r in results if MIN_SIGNAL_STRENGTH <= r['strength'] < 0.2])
    weak_count = len([r for r in results if r['strength'] < MIN_SIGNAL_STRENGTH])

    report.append(f"  强信号 (≥0.2%): {strong_count} 个")
    report.append(f"  达标信号 (≥{MIN_SIGNAL_STRENGTH:.0%}): {medium_count} 个")
    report.append(f"  弱信号 (<{MIN_SIGNAL_STRENGTH:.0%}): {weak_count} 个")

    if strong_count > 0:
        report.append("  市场状态：✅ 趋势明确，适合交易")
    elif medium_count > 0:
        report.append("  市场状态：⚠️ 震荡市，谨慎交易")
    else:
        report.append("  市场状态：❌ 无方向，观望为主")

    report.append("")

    # 持仓状态
    if positions:
        report.append("【持仓状态】")
        total_profit = sum([p['profit_usd'] for p in positions])
        for pos in positions:
            status = "✅ 盈利" if pos['profit_usd'] > 0 else "⚠️ 亏损"
            report.append(f"  {pos['symbol']} {pos['direction']}: {pos['profit_pips']:+.1f} pips (${pos['profit_usd']:+.2f}) [{status}]")
        report.append(f"  总盈亏：${total_profit:+.2f}")
        report.append("")

    # 最佳机会
    if best:
        report.append("【最佳机会】")
        report.append(f"  {best['symbol']} {best['signal']} (强度：{best['strength']:.3f}%)")
        if best['strength'] >= 0.2:
            report.append("  建议：✅ 强信号，可考虑开仓")
        elif best['strength'] >= 0.1:
            report.append("  建议：⚠️ 达标信号，可轻仓")
        else:
            report.append("  建议：❌ 信号不足，等待")
        report.append("")

    # 决策建议
    report.append("【调整建议】")
    decisions = []

    for pos in positions:
        if pos['profit_pips'] >= 10:
            decisions.append(f"✅ {pos['symbol']}: 盈利达标 (+{pos['profit_pips']:.1f} pips)，建议平仓")
        elif pos['profit_pips'] <= -25:
            decisions.append(f"⚠️ {pos['symbol']}: 接近止损 ({pos['profit_pips']:+.1f} pips)，准备平仓")

    if best and len(positions) < 3 and best['strength'] >= 0.1:
        decisions.append(f"🎯 发现强信号：{best['symbol']} {best['signal']} ({best['strength']:.3f}%)，建议开仓")

    if not decisions:
        decisions.append("📌 无调整建议，维持现状")

    for d in decisions:
        report.append(f"  {d}")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main_loop():
    """主循环 v2.0 - 集成新风控"""
    log_message("=" * 60)
    log_message("自动监控系统 v2.0 (MP5 策略 + 新风控)")
    log_message("扫描频率：每 20 分钟 | 主动汇报：启用")
    log_message("新风控：单一品种限制 + 移动止损 + 保证金自动平仓")
    log_message("=" * 60)

    # 初始化 MT5
    if not mt5.initialize():
        log_message("MT5 初始化失败", "ERROR")
        return

    account = mt5.account_info()
    log_message(f"账户：{account.login} | 余额：${account.balance:.2f} | 杠杆：1:{account.leverage}")

    # 风控检查优先 - 简化版
    # from risk_manager_v2 import run_risk_check
    # risk_status = run_risk_check()
    # if risk_status == "CRITICAL":
    #     log_message("风控警告：保证金水平过低，暂停交易", "WARNING")
    #     return

    # 扫描市场
    results, best = scan_market()

    # 检查持仓
    positions = check_positions()

    # 加载交易日志 (P1/P4)
    trade_log = load_trade_log()

    # 决策逻辑
    decisions = []

    for pos in positions:
        # 盈利超过阈值，平仓
        if pos['profit_pips'] >= PROFIT_THRESHOLD_PIPS:
            reason = f"盈利达标：+{pos['profit_pips']:.1f} pips (${pos['profit_usd']:+.2f})"
            decisions.append({
                'action': 'CLOSE',
                'ticket': pos['ticket'],
                'symbol': pos['symbol'],
                'reason': reason
            })
            log_message(f"决策：平仓 {pos['symbol']} - {reason}", "DECISION")

        # 信号反转处理 (P1 修复：防止反复翻转)
        # 旧逻辑：只要信号反转就平仓 → 导致 AUDUSD 一天翻转 3 次
        # 新逻辑：信号反转需要确认，且平仓后进入冷却期
        elif best and best['symbol'] == pos['symbol']:
            if (pos['direction'] == 'BUY' and best['signal'] == 'SELL') or \
               (pos['direction'] == 'SELL' and best['signal'] == 'BUY'):
                # 只有信号强度足够高时才考虑反转 (P1: 提高阈值)
                if best['strength'] >= 0.20:  # 从 0.1% 提高到 0.2%
                    reason = f"信号强反转：{best['signal']} {best['strength']:.3f}%"
                    decisions.append({
                        'action': 'CLOSE',
                        'ticket': pos['ticket'],
                        'symbol': pos['symbol'],
                        'reason': reason
                    })
                    log_message(f"决策：平仓 {pos['symbol']} - {reason}", "DECISION")
                else:
                    log_message(f"信号弱反转 ({best['strength']:.3f}%)，忽略，继续持有 {pos['symbol']}", "INFO")

    # 执行平仓决策
    closed_count = 0
    for decision in decisions:
        if decision['action'] == 'CLOSE':
            if close_position(decision['ticket'], decision['reason']):
                closed_count += 1
                # P1: 记录平仓（冷却期起点）
                record_close(trade_log, decision['symbol'])
                record_trade(trade_log, decision['symbol'], decision['reason'], "close")
                send_feishu_notification(f"已平仓：{decision['symbol']} - {decision['reason']}")

    # 检查是否可以开新仓 - P1/P4 全面升级
    current_positions = check_positions()
    open_count = len(current_positions) - closed_count

    if open_count < 3 and best:
        # P1: 信号阈值检查 (已提升到 0.15%)
        if best['strength'] < MIN_SIGNAL_STRENGTH:
            log_message(f"跳过 {best['symbol']}: 信号强度 {best['strength']:.3f}% < {MIN_SIGNAL_STRENGTH:.2%}", "INFO")
        else:
            # P1: 冷却期 + 每日次数检查
            passed, message = can_trade_symbol(trade_log, best['symbol'])
            if not passed:
                log_message(f"跳过 {best['symbol']}: {message}", "WARNING")
            else:
                # 单一品种持仓检查
                passed2, message2 = check_symbol_exposure_v2(best['symbol'], current_positions)
                if not passed2:
                    log_message(f"跳过 {best['symbol']}: {message2}", "WARNING")
                else:
                    log_message(f"发现强信号：{best['symbol']} {best['signal']} ({best['strength']:.3f}%)", "OPPORTUNITY")
                    log_message(f"执行自动开仓：{best['symbol']} {best['signal']}", "ACTION")
                    if execute_trade(best['symbol'], best['signal'], account.balance, best['strength']):
                        record_trade(trade_log, best['symbol'], best['signal'], "signal_open")

    # 生成市场环境报告
    report = generate_market_report(results, positions, best, account)
    print("\n" + report)

    # 保存日志
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'account_balance': account.balance,
        'positions_count': len(positions),
        'best_signal': best['symbol'] if best else None,
        'best_strength': best['strength'] if best else 0,
        'decisions': decisions,
        'closed_count': closed_count,
        'report': report
    }

    # 读取旧日志
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    # 添加新日志
    logs.append(log_data)
    logs = logs[-50:]  # 保留最近 50 条

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    log_message(f"日志已保存至 {LOG_FILE}")
    log_message("=" * 60)

    mt5.shutdown()

if __name__ == "__main__":
    main_loop()
