import json
from datetime import datetime

try:
    with open('C:/Users/DELL/.openclaw-autoclaw/workspace/trading/trade_history.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    today = datetime.now().strftime('%Y-%m-%d')
    trades = [t for t in data if t.get('close_time', '')[:10] == today or t.get('open_time', '')[:10] == today]
    
    print(f'今日交易：{len(trades)}单')
    print()
    for t in trades[-10:]:
        print(f"{t['symbol']} {t['type']} {t['lots']} Lot @ {t['open_price']}")
        print(f"  SL: {t['sl']} TP: {t['tp']} | 盈亏：{t.get('profit', 'N/A')}")
        print()
except FileNotFoundError:
    print('暂无交易记录')
except Exception as e:
    print(f'错误：{e}')
