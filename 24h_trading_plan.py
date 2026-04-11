# -*- coding: utf-8 -*-
"""
24-Hour Aggressive USD Forex Trading Plan
本金: $2,000 USD
目标: 极致盈利
策略: 多空双向 + 短线波段 + 金字塔加仓
Author: 旺财 AI Trader
Date: 2026-03-17
"""

import MetaTrader5 as mt5
import time
from datetime import datetime

# 配置参数
INITIAL_CAPITAL = 2000.0
MAX_DAILY_LOSS_PCT = 0.10  # 最大单日亏损 10%
RISK_PER_TRADE_PCT = 0.05   # 每单风险 5%
LEVERAGE = 1000

# 交易品种 - 主要 USD 币种
SYMBOLS = [
    "EURUSD",
    "GBPUSD", 
    "USDJPY",
    "AUDUSD",
    "USDCHF",
    "USDCAD",
    "NZDUSD",
    "XAUUSD"  # 黄金
]

def print_banner():
    print("=" * 60)
    print("24-HOUR AGGRESSIVE USD FOREX TRADING")
    print("=" * 60)
    print(f"Initial Capital: ${INITIAL_CAPITAL:.2f}")
    print(f"Max Daily Loss: {MAX_DAILY_LOSS_PCT*100:.0f}%")
    print(f"Risk per Trade: {RISK_PER_TRADE_PCT*100:.0f}%")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

def get_current_account_info():
    account = mt5.account_info()
    return {
        'balance': account.balance,
        'equity': account.equity,
        'margin_free': account.margin_free,
        'profit': account.profit
    }

def calculate_position_size(symbol, entry, stop_loss, account_balance, risk_pct):
    """计算仓位大小"""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return 0.1
    
    point = symbol_info.point
    contract_size = symbol_info.volume_min
    
    # 计算风险金额
    risk_amount = account_balance * risk_pct
    
    # 计算每点风险
    if 'JPY' in symbol:
        pip_value = 100  # 大概估算
    else:
        pip_value = 10  # 标准手每点 $10
    
    pips_risk = abs(entry - stop_loss) / point
    if pips_risk == 0:
        pips_risk = 20
    
    # 计算手数
    volume = risk_amount / (pips_risk * pip_value)
    
    # 限制最小/最大手数
    volume = max(volume, symbol_info.volume_min)
    volume = min(volume, symbol_info.volume_max)
    
    # 标准化到最小步长
    step = symbol_info.volume_step
    volume = round(volume / step) * step
    
    return volume

def open_position(symbol, direction, entry, sl, tp, comment="24h-trade"):
    """开仓"""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"  [ERROR] Can't get tick for {symbol}")
        return None
    
    if direction == 'BUY':
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        close_type = mt5.ORDER_TYPE_SELL
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        close_type = mt5.ORDER_TYPE_BUY
    
    account = mt5.account_info()
    volume = calculate_position_size(symbol, entry, sl, account.balance, RISK_PER_TRADE_PCT)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 30,
        "magic": 242026,
        "comment": comment,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"  [OK] {direction} {symbol} {volume:.2f} lot @ {price:.5f}")
        print(f"  [OK] SL: {sl:.5f}, TP: {tp:.5f}, Order: {result.order}")
        return result.order
    else:
        print(f"  [FAIL] Retcode: {result.retcode}, Error: {mt5.last_error()}")
        return None

def get_current_price(symbol):
    """获取当前价格"""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    return (tick.bid + tick.ask) / 2

def get_sma(symbol, timeframe, period):
    """获取简单移动平均线"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 10)
    if rates is None or len(rates) < period:
        return None
    close_prices = [rate['close'] for rate in rates]
    sma = sum(close_prices[-period:]) / period
    return sma

def analyze_market():
    """市场分析 - 多品种技术分析找机会"""
    print("[*] Analyzing market conditions...")
    print()
    
    opportunities = []
    
    for symbol in SYMBOLS:
        # 确保符号选中
        mt5.symbol_select(symbol, True)
        
        current_price = get_current_price(symbol)
        if current_price is None:
            continue
        
        sma20 = get_sma(symbol, mt5.TIMEFRAME_H1, 20)
        sma50 = get_sma(symbol, mt5.TIMEFRAME_H1, 50)
        
        if sma20 is None or sma50 is None:
            continue
        
        # 趋势判断
        trend = "BULLISH" if sma20 > sma50 else "BEARISH"
        
        # RSI 简单计算 (14)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 15)
        if rates is None or len(rates) < 15:
            continue
        
        # 计算简单 RSI
        gains = []
        losses = []
        for i in range(1, len(rates)):
            change = rates[i]['close'] - rates[i-1]['close']
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) > 0:
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(gains)
            if avg_loss != 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100
        else:
            rsi = 50
        
        print(f"  {symbol}: Price={current_price:.5f}, Trend={trend}, RSI={rsi:.1f}")
        
        # 找入场机会
        opportunity = None
        
        if trend == "BULLISH" and rsi < 70:
            # 多头机会
            sl = current_price * (1 - 0.002) if 'USD' in symbol and not 'JPY' in symbol else current_price * (1 - 0.002)
            tp = current_price * (1 + 0.008)
            opportunity = {
                'symbol': symbol,
                'direction': 'BUY',
                'entry': current_price,
                'sl': sl,
                'tp': tp,
                'rsi': rsi,
                'trend': trend
            }
        
        elif trend == "BEARISH" and rsi > 30:
            # 空头机会
            tp = current_price * (1 - 0.008)
            sl = current_price * (1 + 0.002)
            opportunity = {
                'symbol': symbol,
                'direction': 'SELL',
                'entry': current_price,
                'sl': sl,
                'tp': tp,
                'rsi': rsi,
                'trend': trend
            }
        
        if opportunity:
            opportunities.append(opportunity)
    
    print()
    print(f"[*] Found {len(opportunities)} trading opportunities")
    print()
    
    # 选择最好的 2-3 个机会开仓 (分散风险)
    if len(opportunities) > 3:
        # 按趋势强度排序，选择 RSI 接近极值但未超买超卖
        opportunities.sort(key=lambda x: (
            40 < x['rsi'] < 60 if x['direction'] == 'BUY' else 
            40 < x['rsi'] < 60), reverse=True)
        opportunities = opportunities[:3]
    
    return opportunities

def main():
    # 初始化 MT5
    if not mt5.initialize():
        print("ERROR: Can't initialize MT5")
        print("Error:", mt5.last_error())
        return False
    
    print_banner()
    
    # 检查当前持仓
    positions = mt5.positions_get()
    print(f"[*] Current open positions: {len(positions) if positions else 0}")
    
    if positions:
        print()
        for pos in positions:
            dir = "BUY" if pos.type == 0 else "SELL"
            print(f"  {pos.symbol} {dir} {pos.volume:.2f} @ {pos.price_open:.5f} P/L: {pos.profit:.2f}")
    
    print()
    
    # 获取当前账户信息
    acc_info = get_current_account_info()
    print(f"[*] Account: {mt5.account_info().login} @ {mt5.account_info().server}")
    print(f"[*] Balance: ${acc_info['balance']:.2f}, Equity: ${acc_info['equity']:.2f}")
    print()
    
    # 分析市场找机会
    opportunities = analyze_market()
    
    if not opportunities:
        print("[!] No good opportunities found right now")
        mt5.shutdown()
        return False
    
    # 开仓
    print("[*] Opening positions...")
    print()
    
    opened = 0
    for opp in opportunities:
        print(f"  Opening {opp['direction']} {opp['symbol']}...")
        order = open_position(
            opp['symbol'], 
            opp['direction'], 
            opp['entry'], 
            opp['sl'], 
            opp['tp']
        )
        if order:
            opened += 1
        time.sleep(1)
    
    print()
    print("=" * 60)
    print("TRADING PLAN STARTED")
    print("=" * 60)
    print()
    print(f"✅ Opened {opened} positions")
    print()
    
    # 显示最终持仓
    final_positions = mt5.positions_get()
    if final_positions:
        print("Current positions:")
        print()
        total_volume = 0
        total_profit = 0
        for pos in final_positions:
            dir = "BUY" if pos.type == 0 else "SELL"
            total_volume += pos.volume
            total_profit += pos.profit
            print(f"  {pos.symbol} {dir} {pos.volume:.2f} lot")
            print(f"    Entry: {pos.price_open:.5f}, Current: {pos.price_current:.5f}")
            print(f"    P/L: ${pos.profit:.2f}")
            print()
    
    final_acc = get_current_account_info()
    print(f"Final Balance: ${final_acc['balance']:.2f}")
    print(f"Final Equity: ${final_acc['equity':'value']:.2f}")
    print()
    print("Trading bot is running. I'll monitor and add pyramiding.")
    print("Come back in 24h to check the result! 🚀")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    main()
