import MetaTrader5 as mt5
import pandas as pd
import sys

mt5.initialize()

for sym in ['BTCUSD', 'ETHUSD']:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 20)
    df = pd.DataFrame(rates)
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma5'] = df['close'].rolling(5).mean()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    print(f'{sym}:')
    print(f'  Current Price: {latest["close"]}')
    print(f'  SMA5: {latest["sma5"]:.2f}')
    print(f'  SMA20: {latest["sma20"]:.2f}')
    print(f'  RSI(14): {latest["rsi"]:.1f}')
    print(f'  D1 Change: {((latest["close"] - prev["close"]) / prev["close"] * 100):.2f}%')
    
    above_sma20 = latest['close'] > latest['sma20']
    above_sma5 = latest['close'] > latest['sma5']
    rsi_overbought = latest['rsi'] > 70
    rsi_oversold = latest['rsi'] < 30
    
    if above_sma20 and above_sma5 and not rsi_overbought:
        signal = "BUY bias"
    elif not above_sma20 and not above_sma5 and not rsi_oversold:
        signal = "SELL bias"
    elif rsi_overbought:
        signal = "SELL bias (RSI overbought)"
    elif rsi_oversold:
        signal = "BUY bias (RSI oversold)"
    else:
        signal = "NEUTRAL"
    
    print(f'  Signal: {signal}')
    print()

# Also check existing positions
positions = mt5.positions_get()
if positions:
    print("Current Positions:")
    for p in positions:
        direction = "BUY" if p.type == 0 else "SELL"
        print(f"  {p.symbol}: {direction} {p.volume} lots @ {p.price_open}, P/L: {p.profit:.2f}")
else:
    print("No open positions.")

acct = mt5.account_info()
print(f"\nAccount: Balance={acct.balance:.2f}, Equity={acct.equity:.2f}, Leverage={acct.leverage}")

mt5.shutdown()
