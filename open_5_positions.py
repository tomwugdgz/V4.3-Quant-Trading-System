import MetaTrader5 as mt5

def open_position(symbol, direction_str, atr, risk_amount=100):
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    
    if not tick or not info:
        print("%s: No data" % symbol)
        return None
    
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
    
    if symbol.endswith('USD'):
        volume = risk_amount / (sl_distance * 100000)
    elif symbol.startswith('USD'):
        volume = (risk_amount / (sl_distance * 100000)) * price
    else:
        # Stocks
        volume = risk_amount / (sl_distance * price)
        volume = max(info.volume_min, volume)
    
    volume = round(volume / info.volume_step) * info.volume_step
    volume = max(info.volume_min, volume)
    
    print("Opening: %s %s %.2f lot" % (symbol, direction_str, volume))
    print("  Entry: %.5f SL: %.5f TP: %.5f" % (price, sl, tp))
    
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
        "comment": "wangcai",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == 10009:
        print("  OK: order=%d" % result.order)
        return {
            'symbol': symbol,
            'direction': direction_str,
            'volume': volume,
            'price': result.price,
            'status': 'OK'
        }
    else:
        print("  FAILED: %s" % result.comment)
        return {
            'symbol': symbol,
            'status': 'FAILED'
        }

def main():
    mt5.initialize()
    
    account = mt5.account_info()
    print("Account: %d Balance: $%.2f" % (account.login, account.balance))
    print()
    
    # 4 forex + 1 Tesla = 5 positions, $100 each
    trades = [
        ('EURUSD', 'BUY', 0.0033),
        ('GBPUSD', 'BUY', 0.0036),
        ('USDJPY', 'SELL', 0.38),
        ('AUDUSD', 'BUY', 0.0031),
        ('TSLA.NAS', 'BUY', 12.5),  # ATR approx from recent
    ]
    
    print("Opening %d positions..." % len(trades))
    print()
    
    results = []
    for sym, dir, atr in trades:
        res = open_position(sym, dir, atr, 100)
        results.append(res)
        print()
    
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print()
    
    success = 0
    for r in results:
        if r.get('status') == 'OK':
            success += 1
            print("✓ %s %s %.2f lot @ %.5f" % (r['symbol'], r['direction'], r['volume'], r['price']))
    
    print()
    print("Success: %d/%d" % (success, len(results)))
    print()
    
    print("Current positions:")
    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            direction = 'BUY' if pos.type == 0 else 'SELL'
            sign = '+' if pos.profit >= 0 else ''
            print("  %s %s %.2f %s$%.2f" % (pos.symbol, direction, pos.volume, sign, pos.profit))
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
