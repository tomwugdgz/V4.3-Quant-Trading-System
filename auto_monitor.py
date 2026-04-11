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
from datetime import datetime
from pathlib import Path

# 配置
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# MP5 策略参数
RISK_PERCENT = 0.005  # 0.5% 单笔风险
MIN_SIGNAL_STRENGTH = 0.1  # 最小信号强度 0.1%
PROFIT_THRESHOLD_PIPS = 10  # 盈利达到多少 pips 后平仓
STOP_LOSS_PIPS = 30  # 标准止损

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
        log_message(f"平仓成功：{symbol} {volume} 手 @ {price:.5f}, 盈亏 ${pos.profit:.2f}", "SUCCESS")
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
    
    # 市场状态
    report.append("【市场环境分析】")
    strong_count = len([r for r in results if r['strength'] >= 0.1])
    medium_count = len([r for r in results if 0.05 <= r['strength'] < 0.1])
    weak_count = len([r for r in results if r['strength'] < 0.05])
    
    report.append(f"  强信号 (≥0.1%): {strong_count} 个")
    report.append(f"  中等信号 (≥0.05%): {medium_count} 个")
    report.append(f"  弱信号 (<0.05%): {weak_count} 个")
    
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
    
    # 风控检查优先
    from risk_manager_v2 import run_risk_check, check_margin_level, get_all_positions
    risk_status = run_risk_check()
    
    if risk_status == "CRITICAL":
        log_message("风控警告：保证金水平过低，暂停交易", "WARNING")
        return
    
    # 扫描市场
    results, best = scan_market()
    
    # 检查持仓
    positions = check_positions()
    
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
        
        # 信号反转，考虑平仓
        elif best and best['symbol'] == pos['symbol']:
            if (pos['direction'] == 'BUY' and best['signal'] == 'SELL') or \
               (pos['direction'] == 'SELL' and best['signal'] == 'BUY'):
                if best['strength'] >= MIN_SIGNAL_STRENGTH:
                    reason = f"信号反转：{best['signal']} {best['strength']:.3f}%"
                    decisions.append({
                        'action': 'CLOSE',
                        'ticket': pos['ticket'],
                        'symbol': pos['symbol'],
                        'reason': reason
                    })
                    log_message(f"决策：平仓 {pos['symbol']} - {reason}", "DECISION")
    
    # 执行平仓决策
    closed_count = 0
    for decision in decisions:
        if decision['action'] == 'CLOSE':
            if close_position(decision['ticket'], decision['reason']):
                closed_count += 1
                send_feishu_notification(f"已平仓：{decision['symbol']} - {decision['reason']}")
    
    # 检查是否可以开新仓 v2.0 - 增加单一品种限制
    if len(positions) - closed_count < 3 and best:
        # 单一品种风险检查
        passed, message = check_symbol_exposure_v2(best['symbol'], positions)
        if not passed:
            log_message(f"跳过 {best['symbol']}: {message}", "WARNING")
        elif best['strength'] >= MIN_SIGNAL_STRENGTH:
            log_message(f"发现强信号：{best['symbol']} {best['signal']} ({best['strength']:.3f}%)", "OPPORTUNITY")
            # 这里可以添加自动开仓逻辑
    
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
