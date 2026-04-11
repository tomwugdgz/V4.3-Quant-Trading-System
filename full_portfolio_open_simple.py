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
        print("[%s] ERROR: No data" % symbol)
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
        # For stocks
        volume = risk_amount / (sl_distance * price)
        volume = max(1, volume)
    
    # Round to proper volume step
    volume = round(volume / info.volume_step) * info.volume_step
    volume = max(info.volume_min, volume)
    
    print("[%s] %s" % (symbol, direction_str))
    print("  Price: %.5f SL: %.5f TP: %.5f" % (price, sl, tp))
    print("  Volume: %.2f Risk: $%d" % (volume, risk_amount))
    
    # Place order
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": round(sl, 5),
        "tp": round(tp, 5),
        "deviation": 20,
        "magic": 20260317,
        "comment": "wangcai-portfolio",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == 10009:
        print("  OK: order=%d price=%.5f" % (result.order, result.price))
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
        print("  FAILED: retcode=%d %s" % (result.retcode, result.comment))
        return {
            'symbol': symbol,
            'status': 'FAILED',
            'error': result.comment
        }

def main():
    print("=" * 60)
    print("WANGCAI FULL PORTFOLIO OPENING")
    print("    Risk per position: $100 USD")
    print("    Total target: 6 positions")
    print("=" * 60)
    print()
    
    mt5.initialize()
    
    account = mt5.account_info()
    print("Account: %d" % account.login)
    print("Balance: $%.2f" % account.balance)
    print()
    
    # Step 1: List available stocks
    print("Looking for Tesla and Tencent symbols...")
    print()
    
    all_symbols = mt5.symbols_get()
    tsla_found = None
    tencent_found = None
    
    for sym in all_symbols:
        name = sym.name.upper()
        if 'TSLA' in name and not tsla_found:
            tsla_found = sym.name
            print("  Found Tesla: %s" % tsla_found)
        if ('TENC' in name or '0700' in name) and not tencent_found:
            tencent_found = sym.name
            print("  Found Tencent: %s" % tencent_found)
    
    print()
    
    # Step 2: Forex trades
    trades = [
        ('EURUSD', 'BUY', 0.0033),
        ('GBPUSD', 'BUY', 0.0036),
        ('USDJPY', 'SELL', 0.38),
        ('AUDUSD', 'BUY', 0.0031),
    ]
    
    # Add stocks if found
    if tsla_found:
        rates = mt5.copy_rates_from_pos(tsla_found, mt5.TIMEFRAME_D1, 0, 20)
        if rates is not None and len(rates) >= 14:
            ranges = [r['high'] - r['low'] for r in rates]
            atr = sum(ranges[-14:]) / 14
            trades.append((tsla_found, 'BUY', atr))
            print("Added %s with ATR=%.2f" % (tsla_found, atr))
    
    if tencent_found:
        rates = mt5.copy_rates_from_pos(tencent_found, mt5.TIMEFRAME_D1, 0, 20)
        if rates is not None and len(rates) >= 14:
            ranges = [r['high'] - r['low'] for r in rates]
            atr = sum(ranges[-14:]) / 14
            closes = [r['close'] for r in rates]
            if sum(closes[-5:])/5 > sum(closes[-20:])/20:
                direction = 'BUY'
            else:
                direction = 'SELL'
            trades.append((tencent_found, direction, atr))
            print("Added %s %s with ATR=%.2f" % (tencent_found, direction, atr))
    
    print()
    print("Total trades to open: %d" % len(trades))
    print()
    
    # Execute all trades
    results = []
    for sym, dir, atr in trades:
        result = open_position(sym, dir, atr, 100)
        results.append(result)
        print()
    
    # Summary
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print()
    
    success = len([r for r in results if r.get('status') == 'OK'])
    print("Success: %d/%d" % (success, len(results)))
    print()
    
    if success > 0:
        print("Opened positions:")
        for r in results:
            if r.get('status') == 'OK':
                print("  %s %s %.2f lot @ %.5f" % (r['symbol'], r['direction'], r['volume'], r['price']))
    
    print()
    print("Current positions:")
    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            direction = 'BUY' if pos.type == 0 else 'SELL'
            sign = '+' if pos.profit >= 0 else ''
            print("  %s %s %.2f %s$%.2f" % (pos.symbol, direction, pos.volume, sign, pos.profit))
    else:
        print("  No positions")
    
    print()
    print("Portfolio opening complete")
    mt5.shutdown()

if __name__ == "__main__":
    main()
