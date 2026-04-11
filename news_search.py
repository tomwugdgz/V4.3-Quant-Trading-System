import requests
import os
from datetime import datetime

# NewsAPI
newsapi_key = "f867b18f6a794bb98fad0828fe22d228"

# GNews
gnews_key = "16e0e31741dbb155c1b3cd55694411c1"

# Currents
currents_key = "8LiYRGiO4bdZX512jGVts57EZLL7q5tD"

# MarketAux
marketaux_key = "hpTehUc4xtOMEaAfKiFmlajYKkwGiZRe"

print("=" * 60)
print("旺财 - 时事新闻搜索")
print("=" * 60)
print(f"搜索时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print("")

# 搜索主题
topics = [
    ("中东局势 胡塞武装 红海", "中东地缘政治"),
    ("原油价格 油价上涨", "原油市场"),
    ("美元 汇率 美联储", "美元走势"),
    ("比特币 Bitcoin BTC", "加密货币"),
    ("黄金 避险", "贵金属")
]

for query, label in topics:
    print(f"【{label}】")
    print(f"搜索词：{query}")
    print("")
    
    # 使用 GNews
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "zh",
            "country": "us,cn",
            "max": 3,
            "apikey": gnews_key
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if "articles" in data and len(data["articles"]) > 0:
            for i, article in enumerate(data["articles"][:2], 1):
                print(f"  {i}. {article['title']}")
                print(f"     来源：{article['source']['name']} | 时间：{article['publishedAt'][:16].replace('T', ' ')}")
                print(f"     摘要：{article['description'][:100]}...")
                print("")
        else:
            print("  暂无相关新闻")
            print("")
    except Exception as e:
        print(f"  搜索失败：{e}")
        print("")

print("=" * 60)
print("新闻搜索完成")
print("=" * 60)
