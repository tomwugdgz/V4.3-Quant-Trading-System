# -*- coding: utf-8 -*-
# Full Portfolio Opening
# Author: 旺财 (AI Trader)
# Date: 2026-03-17
# Description: 6 positions with $100 risk each

import MetaTrader5 as mt5

def open_position(symbol, direction_str, atr, risk_amount=100):
    """Open a position with calculated risk"""
    
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    
    if not tick or not info:
        print(f"[{symbol}] ERROR: No data")
        return None
    
    # Calculate SL/TP
    sl_distance = atr * 1.5
    tp_distance = atr * 2.5
    
    if direction_str == 'BUY':
        price = tick.ask
        sl = price - sl_distance
        tp = price + tp_distance
        order_type = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        sl = price + sl_distance
        tp = price - tp_distance
        order_type = mt5.ORDER_TYPE_SELL
    
    # Calculate volume based on risk
    if symbol.endswith('USD'):
        volume = risk_amount / (sl_distance * 100000)
    elif symbol.startswith('USD'):
        volume = (risk_amount / (sl_distance * 100000)) * price
    else:
        # For stocks: 1 lot = 1 share
        volume = risk_amount / (sl_distance * price)
        volume = max(1, volume)
    
    # Round to proper volume step
    volume = round(volume / info.volume_step) * info.volume_step
    volume = max(info.volume_min, volume)
    
    print(f"[{symbol}] {direction_str}")
    print(f"  Price: {price:.5f} SL: {sl:.5f} TP: {tp:.5f}")
    print(f"  Volume: {volume:.2f} Risk: ${risk_amount}")
    
    # Place order
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": round(sl, 5) if '.' in str(sl) else sl,
        "tp": round(tp, 5) if '.' in str(tp) else tp,
        "deviation": 20,
        "magic": 20260317,
        "comment": "wangcai-portfolio",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == 10009:
        print(f"  ✓ SUCCESS: order={result.order} price={result.price}")
        return {
            'symbol': symbol,
            'direction': direction_str,
            'volume': volume,
            'price': result.price,
            'sl': sl,
            'tp': tp,
            'ticket': result.order,
            'status': 'OK'
        }
    else:
        print(f"  ✗ FAILED: retcode={result.retcode} {result.comment}")
        return {
            'symbol': symbol,
            'status': 'FAILED',
            'error': result.comment
        }

def main():
    print("=" * 60)
    print("🚀 WANGCAI FULL PORTFOLIO OPENING")
    print("    Risk per position: $100 USD")
    print("    Total target: 6 positions")
    print("=" * 60)
    print()
    
    mt5.initialize()
    
    account = mt5.account_info()
    print(f"Account: {account.login}")
    print(f"Balance: ${account.balance:.2f}")
    print()
    
    # Step 1: List available stocks (Tesla and Tencent)
    print("🔍 Looking for Tesla and Tencent symbols...")
    print()
    
    all_symbols = mt5.symbols_get()
    tsla_found = None
    tencent_found = None
    
    for sym in all_symbols:
        name = sym.name.upper()
        if 'TSLA' in name and not tsla_found:
            tsla_found = sym.name
            print(f"  Found Tesla: {tsla_found}")
        if ('TENC' in name or '0700' in name) and not tencent_found:
            tencent_found = sym.name
            print(f"  Found Tencent: {tencent_found}")
    
    print()
    
    # Step 2: Define trades (based on H4 trend analysis)
    # Recalculated ATR from recent data
    trades = [
        # Forex: 4 positions
        ('EURUSD', 'BUY', 0.0033),
        ('GBPUSD', 'BUY', 0.0036),
        ('USDJPY', 'SELL', 0.38),
        ('AUDUSD', 'BUY', 0.0031),
    ]
    
    # Add stocks if found
    if tsla_found:
        # Get ATR for Tesla
        rates = mt5.copy_rates_from_pos(tsla_found, mt5.TIMEFRAME_D1, 0, 20)
        if rates is not None and len(rates) >= 14:
            ranges = [r['high'] - r['low'] for r in rates]
            atr = sum(ranges[-14:]) / 14
            trades.append((tsla_found, 'BUY', atr))
            print(f"✓ Added {tsla_found} with ATR={atr:.2f}")
    
    if tencent_found:
        rates = mt5.copy_rates_from_pos(tencent_found, mt5.TIMEFRAME_D1, 0, 20)
        if rates is not None and len(rates) >= 14:
            ranges = [r['high'] - r['low'] for r in rates]
            atr = sum(ranges[-14:]) / 14
            # Trend: recent bullish
            closes = [r['close'] for r in rates]
            if sum(closes[-5:])/5 > sum(closes[-20:])/20:
                direction = 'BUY'
            else:
                direction = 'SELL'
            trades.append((tencent_found, direction, atr))
            print(f"✓ Added {tencent_found} {direction} with ATR={atr:.2f}")
    
    print()
    print(f"Total trades to open: {len(trades)}")
    print()
    
    # Execute all trades
    results = []
    for sym, dir, atr in trades:
        result = open_position(sym, dir, atr, 100)
        results.append(result)
        print()
    
    # Summary
    print("=" * 60)
    print("📊 EXECUTION SUMMARY")
    print("=" * 60)
    print()
    
    success = len([r for r in results if r.get('status') == 'OK'])
    print(f"Success: {success}/{len(results)}")
    print()
    
    if success > 0:
        print("✅ Opened positions:")
        for r in results:
            if r.get('status') == 'OK':
                print(f"  {r['symbol']} {r['direction']} {r['volume']:.2f} lot @ {r['price']}")
    
    print()
    print("📋 Current positions:")
    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            direction = 'BUY' if pos.type == 0 else 'SELL'
            sign = '+' if pos.profit >= 0 else ''
            print(f"  {pos.symbol} {direction} {pos.volume:.2f} {sign}${pos.profit:.2f}")
    else:
        print("  No positions")
    
    print()
    print("✨ Portfolio opening complete")
    mt5.shutdown()

if __name__ == "__main__":
    main()
