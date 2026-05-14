#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能开仓脚本 — 自动根据品种调整止损
JPY 品种用更大止损（ATR 动态计算）
非 JPY 品种用标准止损
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ACCOUNT = 52797683
SERVER = "ICMarketsSC-Demo"
RISK_PCT = 0.005      # 0.5% 单笔风险
MAX_LOTS = 0.15        # 强信号最大 0.15 手
ATR_SL_MULT = 2.0      # ATR 倍数止损

def log(msg):
    print(msg, flush=True)

def calc_atr(symbol, tf=mt5.TIMEFRAME_H1, period=14):
    """计算 ATR"""
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

def open_position(symbol, direction, volume=None):
    """智能开仓 — 自动根据 ATR 计算止损"""
    if not mt5.initialize(login=ACCOUNT, server=SERVER, timeout=10000):
        log("MT5 连接失败")
        return False
    
    tick = mt5.symbol_info_tick(symbol)
    sym = mt5.symbol_info(symbol)
    if not tick or not sym:
        log(f"{symbol} 信息获取失败")
        mt5.shutdown()
        return False
    
    digits = sym.digits
    point = sym.point
    price = tick.ask if direction == "BUY" else tick.bid
    
    # 计算 ATR
    atr = calc_atr(symbol)
    if atr is None:
        log("ATR 计算失败，使用默认值")
        atr = point * 100
    
    # 动态止损 = ATR * 倍数
    sl_pips_raw = atr * ATR_SL_MULT
    
    # 转换为 pips
    pip_div = 100 if digits == 3 else 10000
    pip_size = point * 10 if digits in (3, 5) else point
    sl_pips = sl_pips_raw / pip_size
    
    # 最小止损保护
    min_pips = 15 if digits == 5 else 150
    sl_pips = max(sl_pips, min_pips / pip_div * (10000 if digits == 5 else 100))
    
    tp_pips = sl_pips * 2.0
    
    # 计算手数
    info = mt5.account_info()
    pip_value = sym.trade_tick_value * (pip_size / sym.trade_tick_size) if sym.trade_tick_size > 0 else pip_size * sym.trade_contract_size
    risk_amt = info.balance * RISK_PCT
    lots = risk_amt / (sl_pips * pip_value) if sl_pips > 0 and pip_value > 0 else 0.01
    lots = round(max(0.01, min(lots, MAX_LOTS)), 2)
    
    # 执行价格
    sl_dist = sl_pips / pip_div
    tp_dist = tp_pips / pip_div
    
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
        "comment": "Wangcai Smart",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    log(f"开仓: {direction} {lots} {symbol} @{price:.{digits}f}")
    log(f"ATR={atr:.{digits}f} | SL={sl_pips:.1f}pips | TP={tp_pips:.1f}pips")
    log(f"止损={sl_price:.{digits}f} | 止盈={tp_price:.{digits}f}")
    log(f"风险=${risk_amt:.2f}")
    
    result = mt5.order_send(req)
    log(f"结果: retcode={result.retcode} {result.comment}")
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log(f"成功开仓 #{result.order}")
        mt5.shutdown()
        return True
    else:
        log(f"开仓失败: {result.comment}")
        mt5.shutdown()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        log("用法: python open_smart.py SYMBOL DIRECTION [VOLUME]")
        log("例如: python open_smart.py EURUSD BUY")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    direction = sys.argv[2].upper()
    volume = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    success = open_position(symbol, direction, volume)
    sys.exit(0 if success else 1)
