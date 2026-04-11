import MetaTrader5 as mt5
mt5.initialize()

print("Looking for TSLA and Tencent...")
print()

all_symbols = mt5.symbols_get()
tsla_list = []
tencent_list = []

for sym in all_symbols:
    name = sym.name.upper()
    if 'TSLA' in name:
        tsla_list.append(sym.name)
    if 'TENC' in name or '0700' in name or 'TCEHY' in name:
        tencent_list.append(sym.name)

print("Tesla symbols found:")
for s in tsla_list:
    print("  %s" % s)

print()
print("Tencent symbols found:")
for s in tencent_list:
    print("  %s" % s)

print()
mt5.shutdown()
