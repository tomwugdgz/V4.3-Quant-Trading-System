path = r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "'USDCAD':  {'W': 0.71, 'R': 0.97, 'kf': 0.420},":
        "'USDCAD':  {'W': 0.71, 'R': 0.87, 'kf': 0.388},",
    "'AUDUSD':  {'W': 0.62, 'R': 0.71, 'kf': 0.094},":
        "'AUDUSD':  {'W': 0.62, 'R': 0.67, 'kf': 0.067},",
    "'USDCHF':  {'W': 0.57, 'R': 0.90, 'kf': 0.085},":
        "'USDCHF':  {'W': 0.57, 'R': 0.85, 'kf': 0.057},",
    "'GBPUSD':  {'W': 0.52, 'R': 1.07, 'kf': 0.080},":
        "'GBPUSD':  {'W': 0.52, 'R': 1.03, 'kf': 0.061},",
}

for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        print('Replaced: %s' % old[:40])
    else:
        print('NOT FOUND: %s' % old[:40])

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
