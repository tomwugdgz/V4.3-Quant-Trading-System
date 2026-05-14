import urllib.request
import json
import sys

# 设置 stdout 编码为 utf-8
sys.stdout.reconfigure(encoding='utf-8')

url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&fs=m:90+t:3&fields=f12,f13,f14,f3"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req)
data = json.loads(response.read().decode('utf-8'))

print("=== 板块涨幅排行 ===\n")

if 'data' in data and 'diff' in data['data']:
    blocks = data['data']['diff']
    
    # 按涨幅排序
    sorted_blocks = sorted(blocks, key=lambda x: x['f3'], reverse=True)
    
    print("涨幅前 5 板块:")
    for i, b in enumerate(sorted_blocks[:5]):
        print(f"{i+1}. {b['f14']}: {b['f3']:.2f}%")
    
    print("\n跌幅前 5 板块:")
    for i, b in enumerate(sorted_blocks[-5:]):
        print(f"{i+1}. {b['f14']}: {b['f3']:.2f}%")
