path = r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update version strings
content = content.replace('Patrol Smart v5.5', 'Patrol Smart v5.6')

# Update comment filter for v5.6
content = content.replace("'Patrol Smart v5.4', 'Patrol Auto'",
                          "'Patrol Smart v5.4', 'Patrol Smart v5.6', 'Patrol Auto'")

# Check if XAUUSD is in the symbols list
if 'XAUUSD' in content:
    print('XAUUSD found in SYMBOLS: OK')
else:
    print('XAUUSD NOT found!')

# Update version in patrol header
content = content.replace('30min Patrol - v5.5 第一性原理版',
                          '30min Patrol - v5.6 累积优化版')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated to v5.6')
