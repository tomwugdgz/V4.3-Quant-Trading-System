import MetaTrader5 as mt5
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

for sym in ['XAUUSD','XAGUSD']:
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)
    # tick_value / tick_size = value per unit
    # XAUUSD: tick_size=0.01, tick_value typically ~$10 (for 100oz contract)
    val_per_unit = info.trade_tick_value / info.trade_tick_size if info.trade_tick_size > 0 else 0
    print('{}: ask={} trade_tick_value={} tick_size={} val_per_unit=${}'.format(
        sym, tick.ask, info.trade_tick_value, info.trade_tick_size, val_per_unit))
    # 1 pip = 0.01 for XAUUSD, so pip_value = val_per_unit * 0.01
    pip_value = val_per_unit * 0.01
    print('  1 pip = ${:.2f} per lot (100 oz)'.format(pip_value))

    # With $9899, risk 0.5% = $49.5
    # ATR-based SL: use ATR*1.5 as pips
    import pandas as pd, numpy as np
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 50)
    df = pd.DataFrame(rates)
    hi, lo, cl = df['high'], df['low'], df['close']
    tr = np.maximum(hi-lo, np.maximum(abs(hi-cl.shift(1)), abs(lo-cl.shift(1))))
    atr = tr.rolling(14).mean().iloc[-1]
    # ATR in price units
    sl_pips_float = atr / 0.01  # XAUUSD pip size = 0.01
    sl_pips = max(sl_pips_float * 1.5, 15)  # ATR*1.5, min 15 pips
    tp_pips = sl_pips * 2.0
    risk_amt = 9899 * 0.005
    lots = risk_amt / (sl_pips * pip_value) if pip_value > 0 else 0.01
    print('  ATR={:.2f} | SL={:.0f}pip | TP={:.0f}pip | max_lots={:.2f}'.format(
        sl_pips_float, sl_pips, tp_pips, lots))

mt5.shutdown()