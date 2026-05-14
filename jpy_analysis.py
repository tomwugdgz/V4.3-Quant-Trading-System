import MetaTrader5 as mt5, pandas as pd, numpy as np
from datetime import datetime

mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

jpy_pairs = ['USDJPY','AUDJPY','EURJPY','GBPJPY','NZDJPY','CADJPY','CHFJPY']

print("=== JPY品种波动率分析（最近30天）===")
results = []
for sym in jpy_pairs:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 720)
    df = pd.DataFrame(rates)
    hi, lo, cl = df['high'], df['low'], df['close']
    tr1 = hi - lo; tr2 = abs(hi - cl.shift(1)); tr3 = abs(lo - cl.shift(1))
    tr = np.maximum(np.maximum(tr1, tr2), tr3)
    atr = tr.rolling(14).mean()
    recent_atr = atr.iloc[-14:].mean()
    
    daily = df.groupby(df['time'].apply(lambda x: datetime.fromtimestamp(x).date())).agg({
        'high': 'max', 'low': 'min'
    })
    daily_ranges = (daily['high'] - daily['low']) / 0.01
    
    results.append({
        'sym': sym,
        'atr_pips': recent_atr / 0.01,
        'avg_daily': daily_ranges.mean(),
        'max_daily': daily_ranges.max(),
        'days': len(daily)
    })

for r in sorted(results, key=lambda x: -x['atr_pips']):
    vol = 'HIGH' if r['atr_pips'] > 16 else 'MID' if r['atr_pips'] > 12 else 'LOW'
    print(f"{r['sym']:8} ATR={r['atr_pips']:5.1f}pips [{vol}] 日均{r['avg_daily']:5.1f}pips 最大{r['max_daily']:5.1f}pips ({r['days']}天)")

print()
print("=== AUDJPY SL被打概率分析 ===")
sym = 'AUDJPY'
rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 720)
df = pd.DataFrame(rates)
daily = df.groupby(df['time'].apply(lambda x: datetime.fromtimestamp(x).date())).agg({
    'high': 'max', 'low': 'min'
})
daily['range'] = (daily['high'] - daily['low']) / 0.01

for sl in [15, 20, 25, 30, 35, 40]:
    hit = (daily['range'] >= sl).sum()
    pct = hit / len(daily) * 100
    print(f"SL={sl:2d}pip被打: {hit:3d}/{len(daily)}天 = {pct:.1f}%")

print()
print("=== AUDJPY 历史交易记录 ===")
from_sec = int(datetime(2026,4,1).timestamp())
to_sec = int(datetime(2026,5,8).timestamp())
deals = mt5.history_deals_get(from_sec, to_sec)
audjpy = [d for d in deals if d.symbol == 'AUDJPY']
print(f"总笔数: {len(audjpy)}")
for d in audjpy:
    tag = d.comment.strip('[]') if d.comment else 'no_comment'
    t = datetime.fromtimestamp(d.time).strftime('%m-%d %H:%M')
    dirc = 'BUY' if d.type == 0 else 'SELL'
    pnl = float(d.profit)
    print(f"  {t} {dirc} vol={float(d.volume):.2f} pnl=${pnl:+.2f} [{tag}]")

print()
print("=== EURJPY 历史交易记录 ===")
eurjpy = [d for d in deals if d.symbol == 'EURJPY']
print(f"总笔数: {len(eurjpy)}")
for d in eurjpy:
    tag = d.comment.strip('[]') if d.comment else 'no_comment'
    t = datetime.fromtimestamp(d.time).strftime('%m-%d %H:%M')
    dirc = 'BUY' if d.type == 0 else 'SELL'
    pnl = float(d.profit)
    print(f"  {t} {dirc} vol={float(d.volume):.2f} pnl=${pnl:+.2f} [{tag}]")

mt5.shutdown()