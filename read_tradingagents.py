import os

base_path = r"E:\TradingAgents-CN-1.0.0-preview\tradingagents\agents"

# 读取关键 Agent 文件
files_to_read = [
    "researchers/bull_researcher.py",
    "researchers/bear_researcher.py",
    "managers/risk_manager.py",
    "trader/trader.py",
    "analysts/market_analyst.py",
    "analysts/fundamentals_analyst.py",
    "analysts/news_analyst.py",
    "__init__.py"
]

print("=" * 80)
print("TradingAgents-CN 核心 Agent 代码分析")
print("=" * 80)
print("")

for file in files_to_read:
    full_path = os.path.join(base_path, file)
    print(f"\n{'='*80}")
    print(f"文件：{file}")
    print(f"{'='*80}")
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 显示前 200 行
            lines = content.split('\n')[:200]
            print('\n'.join(lines))
            if len(lines) < len(content.split('\n')):
                remaining = len(content.split('\n')) - len(lines)
                print(f"\n... (还有 {remaining} 行)")
    else:
        print("文件不存在")

print("\n" + "=" * 80)
print("读取完成")
print("=" * 80)
