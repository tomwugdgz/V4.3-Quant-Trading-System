import sys
sys.path.insert(0, r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading')
import MT5Trader

m = MT5Trader.MT5Trader()
acc = m.get_account_info()
print("Balance:", acc.get('balance'))
print("Equity:", acc.get('equity'))
print("MarginLevel:", acc.get('margin_level'))

pos = m.get_positions()
print("Positions:", len(pos))
for p in pos:
    sym = p.get('symbol', '?')
    typ = p.get('type', '?')
    vol = p.get('volume', '?')
    prof = p.get('profit', '?')
    print(f"  {sym} {typ} vol={vol} profit={prof}")
