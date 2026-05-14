import json
from pathlib import Path
log = Path(r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\trade_log.json')
data = json.loads(log.read_text(encoding='utf-8'))
today = '2026-04-27'
trades = [t for t in data if t.get('timestamp','').startswith(today)]
print(f'Today trades: {len(trades)}')
for t in trades:
    sym = t.get('symbol','?')
    act = t.get('action','?')
    rsn = t.get('reason','?')
    ts = t.get('timestamp','?')
    print(f'  {ts} | {sym} | {act} | {rsn}')
