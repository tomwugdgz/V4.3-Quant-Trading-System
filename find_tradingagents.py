import requests
import json

# 搜索 TradingAgents 相关项目
queries = [
    "TradingAgents AI trading",
    "trading agents multi-agent",
    "AI trading agent framework"
]

for query in queries:
    print(f"\n搜索：{query}")
    print("-" * 60)
    
    try:
        url = f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}&sort=stars&order=desc&per_page=5"
        r = requests.get(url, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            items = data.get('items', [])[:3]
            
            for repo in items:
                print(f"\n项目名称：{repo['full_name']}")
                print(f"Stars: ⭐ {repo['stargazers_count']:,}")
                print(f"Forks: 🍴 {repo['forks_count']:,}")
                print(f"URL: {repo['html_url']}")
                print(f"描述：{repo['description'][:100] if repo['description'] else '无描述'}")
                print(f"语言：{repo['language']}")
                print(f"更新时间：{repo['updated_at'][:10]}")
        else:
            print(f"API 错误：{r.status_code}")
            
    except Exception as e:
        print(f"搜索失败：{e}")

print("\n" + "=" * 60)
print("搜索完成")
