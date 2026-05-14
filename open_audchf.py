import MetaTrader5 as mt5, pandas as pd, numpy as np
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

sym = 'AUDCHF'
tick = mt5.symbol_info_tick(sym)
sym_info = mt5.symbol_info(sym)
price = float(tick.ask)
digits = sym_info.digits
pip_size = sym_info.point * 10 if digits in (3, 5) else sym_info.point

# ATR
rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 50)
df = pd.DataFrame(rates)
hi, lo, cl = df['high'], df['low'], df['close']
tr1 = hi - lo; tr2 = abs(hi - cl.shift(1)); tr3 = abs(lo - cl.shift(1))
tr = np.maximum(np.maximum(tr1, tr2), tr3)
atr = float(tr.rolling(14).mean().iloc[-1])
atr_pips = atr / pip_size

# v3: 非JPY ATR×1.5 min15pip
sl_pips = max(atr_pips * 1.5, 15)
tp_pips = sl_pips * 2.0

sl = price - sl_pips * pip_size
tp = price + tp_pips * pip_size

lot = 0.08

print(f'AUDCHF BUY {lot}@{price:.5f}')
print(f'SL={sl:.5f} ({sl_pips:.1f}pips) TP={tp:.5f} ({tp_pips:.1f}pips)')

request = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': sym,
    'volume': lot,
    'type': mt5.ORDER_TYPE_BUY,
    'price': price,
    'sl': sl,
    'tp': tp,
    'deviation': 5,
    'magic': 240501,
    'comment': 'Patrol Auto v3',
    'type_filling': mt5.ORDER_FILLING_IOC
}
result = mt5.order_send(request)
print(f'结果: {result.retcode} - {result.comment}')

info = mt5.account_info()
positions = mt5.positions_get()
print(f'余额=${info.balance:.2f} | 净值=${info.equity:.2f} | 持仓={len(positions)}单')
for p in positions:
    pdir = 'BUY' if p.type == 0 else 'SELL'
    print(f'  {p.symbol} {pdir} {p.volume}@{p.price_open:.5f} ${p.profit:.2f}')

mt5.shutdown()