import requests

print("搜索 GitHub 上的 TradingAgents 项目...")
print("")

r = requests.get(
    'https://api.github.com/search/repositories?q=TradingAgents+AI+trading&sort=stars&order=desc',
    timeout=10
)
data = r.json()

print(f"找到 {data.get('total_count', 0)} 个项目")
print("")

for i, repo in enumerate(data.get('items', [])[:5], 1):
    print(f"{i}. {repo['full_name']}")
    print(f"   Stars: {repo['stargazers_count']}")
    print(f"   URL: {repo['html_url']}")
    desc = repo['description'][:80] if repo['description'] else '无描述'
    print(f"   描述：{desc}")
    print("")
