import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialization failed")
    sys.exit(1)

# 加密货币列表
crypto_symbols = ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD", "ADAUSD", "SOLUSD"]

print("=" * 70)
print("CRYPTO TRADING OPPORTUNITIES - Weekend Analysis")
print("=" * 70)

account = mt5.account_info()
print(f"\nAccount Balance: ${account.balance:.2f}")
print(f"Free Margin: ${account.margin_free:.2f}")
print(f"Leverage: 1:{account.leverage}")

best_opportunity = None
best_score = 0

for symbol in crypto_symbols:
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.bid == 0:
        continue
    
    spread = (tick.ask - tick.bid)
    current_price = tick.bid
    
    # 获取 H4 数据 (4 小时线，更适合 crypto)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
    if rates is None or len(rates) < 10:
        continue
    
    closes = [r['close'] for r in rates]
    
    # 计算多个时间框架的趋势
    ma_12 = sum(closes[-12:]) / 12  # 12 周期均线
    ma_24 = sum(closes[-24:]) / 24 if len(closes) >= 24 else ma_12
    ma_50 = sum(closes) / len(closes)
    
    # 趋势强度
    trend_12h = ((current_price - ma_12) / ma_12) * 100
    trend_24h = ((current_price - ma_24) / ma_24) * 100
    trend_50 = ((current_price - ma_50) / ma_50) * 100
    
    # 波动性 (ATR 近似)
    highs = [r['high'] for r in rates[-14:]]
    lows = [r['low'] for r in rates[-14:]]
    atr = sum(h - l for h, l in zip(highs, lows)) / 14
    
    # 评分系统
    score = 0
    
    # 趋势一致性 (3 个时间框架同向)
    if trend_12h > 0.1 and trend_24h > 0.1 and trend_50 > 0.1:
        score += 30  # 强势上涨
        signal = "BUY"
    elif trend_12h < -0.1 and trend_24h < -0.1 and trend_50 < -0.1:
        score += 30  # 强势下跌
        signal = "SELL"
    elif trend_12h > 0.05 and trend_24h > 0.05:
        score += 15
        signal = "BUY"
    elif trend_12h < -0.05 and trend_24h < -0.05:
        score += 15
        signal = "SELL"
    else:
        signal = "NEUTRAL"
    
    # 点差评分 (越低越好)
    spread_pct = (spread / current_price) * 100
    if spread_pct < 0.02:
        score += 20
    elif spread_pct < 0.05:
        score += 10
    
    # 波动性评分 (适中最好)
    atr_pct = (atr / current_price) * 100
    if 2 < atr_pct < 8:
        score += 20  # 理想波动
    elif 1 < atr_pct < 10:
        score += 10
    
    # 显示分析结果
    print(f"\n{symbol}:")
    print(f"  Price: ${current_price:.2f}")
    print(f"  Spread: {spread:.2f} ({spread_pct:.3f}%)")
    print(f"  Signal: {signal}")
    print(f"  Trend 12H: {trend_12h:+.2f}%")
    print(f"  Trend 24H: {trend_24h:+.2f}%")
    print(f"  Trend 50: {trend_50:+.2f}%")
    print(f"  ATR (14): {atr:.2f} ({atr_pct:.2f}%)")
    print(f"  Score: {score}/70")
    
    if score > best_score:
        best_score = score
        best_opportunity = {
            'symbol': symbol,
            'signal': signal,
            'price': current_price,
            'spread': spread,
            'score': score,
            'atr': atr
        }

# 显示最佳机会
print("\n" + "=" * 70)
print("BEST OPPORTUNITY")
print("=" * 70)

if best_opportunity and best_score >= 30:
    op = best_opportunity
    print(f"Symbol: {op['symbol']}")
    print(f"Signal: {op['signal']}")
    print(f"Price: ${op['price']:.2f}")
    print(f"Score: {op['score']}/70")
    
    # 仓位计算
    risk_amount = account.balance * 0.005  # 0.5% risk
    stop_loss_atr = 2 * op['atr']  # 2 ATR stop
    take_profit_atr = 4 * op['atr']  # 4 ATR target (1:2)
    
    # 计算手数 (crypto 合约规格通常 1 lot = 1 coin)
    if op['symbol'] == "BTCUSD":
        contract_size = 1
        lot_size = round(risk_amount / (stop_loss_atr * contract_size), 3)
    else:
        contract_size = 1
        lot_size = round(risk_amount / (stop_loss_atr * contract_size), 2)
    
    # 限制最大仓位
    lot_size = min(lot_size, 0.5)  # max 0.5 lot for crypto
    
    sl_price = op['price'] - stop_loss_atr if op['signal'] == "BUY" else op['price'] + stop_loss_atr
    tp_price = op['price'] + take_profit_atr if op['signal'] == "BUY" else op['price'] - take_profit_atr
    
    margin_required = (op['price'] * lot_size * contract_size) / account.leverage
    
    print(f"\nPOSITION SIZING:")
    print(f"  Risk: ${risk_amount:.2f} (0.5%)")
    print(f"  Stop Loss: {stop_loss_atr:.2f} points ({sl_price:.2f})")
    print(f"  Take Profit: {take_profit_atr:.2f} points ({tp_price:.2f})")
    print(f"  Lot Size: {lot_size:.3f}")
    print(f"  Margin Required: ${margin_required:.2f}")
    
    if margin_required < account.margin_free * 0.5:
        print(f"\n[OK] Margin sufficient - Ready to trade!")
    else:
        print(f"\n[WARN] High margin usage - reduce position size")
else:
    print("No strong opportunity found (score < 30)")
    print("Market may be ranging - wait for clearer signal")

mt5.shutdown()
