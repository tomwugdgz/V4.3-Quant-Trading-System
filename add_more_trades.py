# Add more trades to increase profit
# 继续加仓，寻找更多机会，目标极致盈利
import MetaTrader5 as mt5
import time

# 交易品种
SYMBOLS = [
    "GBPUSD",
    "USDJPY", 
    "AUDUSD",
    "USDCHF",
    "USDCAD",
    "GBPJPY",
    "EURJPY",
]

def get_current_price(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    return (tick.bid + tick.ask) / 2

def get_sma(symbol, timeframe, period):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 10)
    if rates is None or len(rates) < period:
        return None
    close_prices = [rate['close'] for rate in rates]
    return sum(close_prices[-period:]) / period

def calculate_rsi(symbol, timeframe, period=14):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 1)
    if rates is None or len(rates) <= period:
        return 50
    
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
    return rsi

def calculate_position_size(symbol, entry, stop_loss, account_balance, risk_pct=0.05):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return 0.1
    
    point = symbol_info.point
    pips_risk = abs(entry - stop_loss) / point
    if pips_risk == 0:
        pips_risk = 15
    
    risk_amount = account_balance * risk_pct
    
    if 'JPY' in symbol:
        pip_value = 100
    else:
        pip_value = 10
    
    volume = risk_amount / (pips_risk * pip_value)
    
    volume = max(volume, symbol_info.volume_min)
    volume = min(volume, symbol_info.volume_max)
    step = symbol_info.volume_step
    volume = round(volume / step) * step
    
    return volume

def open_position(symbol, direction, entry, sl, tp):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print("  ERROR: Can't get tick for " + symbol)
        return None
    
    if direction == 'BUY':
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    
    account = mt5.account_info()
    volume = calculate_position_size(symbol, entry, sl, account.balance, 0.05)
    
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
        "comment": "24h-aggressive",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("  OK: %s %s %.2f lot @ %.5f" % (direction, symbol, volume, price))
        print("  OK: SL=%.5f TP=%.5f Order=%d" % (sl, tp, result.order))
        return result.order
    else:
        print("  FAIL: Retcode=%d Error=%s" % (result.retcode, mt5.last_error()))
        return None

def main():
    if not mt5.initialize():
        print("ERROR: Can't initialize MT5")
        print("Error:", mt5.last_error())
        return False
    
    print("=" * 60)
    print("ADD MORE TRADES - AGGRESSIVE STRATEGY")
    print("Goal: Max profit in 24h with $2000 risk capital")
    print("=" * 60)
    print()
    
    # Current account
    account = mt5.account_info()
    print("Account:", account.login)
    print("Balance: $%.2f  Equity: $%.2f" % (account.balance, account.equity))
    print()
    
    # Count current positions
    positions = mt5.positions_get()
    current_count = len(positions) if positions else 0
    print("Current open positions:", current_count)
    print()
    
    # Analyze new opportunities
    print("Analyzing new opportunities...")
    print()
    
    opportunities = []
    
    for symbol in SYMBOLS:
        mt5.symbol_select(symbol, True)
        current_price = get_current_price(symbol)
        if current_price is None:
            continue
        
        sma20 = get_sma(symbol, mt5.TIMEFRAME_H1, 20)
        sma50 = get_sma(symbol, mt5.TIMEFRAME_H1, 50)
        if sma20 is None or sma50 is None:
            continue
        
        trend = "BULLISH" if sma20 > sma50 else "BEARISH"
        rsi = calculate_rsi(symbol, mt5.TIMEFRAME_H1, 14)
        
        print("  %s: Price=%.5f Trend=%s RSI=%.1f" % (symbol, current_price, trend, rsi))
        
        # Check if already have position
        has_position = False
        if positions:
            for pos in positions:
                if pos.symbol == symbol:
                    has_position = True
                    break
        if has_position:
            continue
        
        # Find entry
        if trend == "BULLISH" and 35 < rsi < 68:
            if 'JPY' in symbol:
                sl = current_price - 0.35
                tp = current_price + 1.40
            else:
                sl = current_price * (1 - 0.0025)
                tp = current_price * (1 + 0.010)
            opportunities.append({
                'symbol': symbol, 'direction': 'BUY',
                'entry': current_price, 'sl': sl, 'tp': tp,
                'rsi': rsi
            })
        
        elif trend == "BEARISH" and 32 < rsi < 65:
            if 'JPY' in symbol:
                tp = current_price - 1.40
                sl = current_price + 0.35
            else:
                tp = current_price * (1 - 0.010)
                sl = current_price * (1 + 0.0025)
            opportunities.append({
                'symbol': symbol, 'direction': 'SELL',
                'entry': current_price, 'sl': sl, 'tp': tp,
                'rsi': rsi
            })
    
    print()
    print("Found %d new opportunities" % len(opportunities))
    print()
    
    # Open top 3 new positions (total max 6 positions)
    max_new = min(3, 6 - current_count)
    if max_new <= 0:
        print("Already enough positions, stopping.")
        mt5.shutdown()
        return True
    
    opportunities = opportunities[:max_new]
    
    opened = 0
    for opp in opportunities:
        print("Opening %s %s..." % (opp['direction'], opp['symbol']))
        order = open_position(
            opp['symbol'], opp['direction'],
            opp['entry'], opp['sl'], opp['tp']
        )
        if order:
            opened += 1
        time.sleep(1)
        print()
    
    # Final report
    print("=" * 60)
    print("FINAL POSITION REPORT")
    print("=" * 60)
    print()
    
    final_positions = mt5.positions_get()
    print("Total positions now: %d" % len(final_positions))
    print()
    
    total_pl = 0.0
    for pos in final_positions:
        dir = "BUY" if pos.type == 0 else "SELL"
        pl = pos.profit
        total_pl += pl
        sign = "+" if pl >= 0 else ""
        print("  %s %s %.2f lot -> %s%.2f" % (pos.symbol, dir, pos.volume, sign, pl))
    
    print()
    print("Total floating P/L: %s%.2f USD" % (("+" if total_pl >= 0 else ""), total_pl))
    print("Account balance: $%.2f" % account.balance)
    print("Account equity: $%.2f" % account.equity)
    print()
    print("Aggressive trading started. Come back in 24h for result!")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    main()
