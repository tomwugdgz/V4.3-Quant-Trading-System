import requests
from datetime import datetime

# GNews
gnews_key = "16e0e31741dbb155c1b3cd55694411c1"

print("=" * 60)
print("旺财 - 地缘政治与市场分析")
print("=" * 60)
print(f"搜索时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print("")

# 英文搜索，获取更全面的新闻
topics_en = [
    ("Houthi rebels Red Sea shipping attack", "胡塞武装/红海"),
    ("Israel Iran Middle East war March 2026", "中东战争"),
    ("oil price surge OPEC", "油价"),
    ("US dollar index Federal Reserve", "美元"),
    ("Bitcoin price analysis March 2026", "比特币"),
    ("gold price safe haven", "黄金避险")
]

for query, label in topics_en:
    print(f"【{label}】")
    print(f"搜索：{query}")
    print("")
    
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "country": "us",
            "max": 3,
            "apikey": gnews_key
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if "articles" in data and len(data["articles"]) > 0:
            for i, article in enumerate(data["articles"][:2], 1):
                print(f"  {i}. {article['title']}")
                print(f"     来源：{article['source']['name']}")
                print(f"     时间：{article['publishedAt'][:16].replace('T', ' ')}")
                desc = article.get('description', '')[:150]
                if desc:
                    print(f"     摘要：{desc}...")
                print("")
        else:
            print("  暂无最新新闻")
            print("")
    except Exception as e:
        print(f"  搜索失败：{e}")
        print("")

print("=" * 60)
