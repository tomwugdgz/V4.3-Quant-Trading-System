import os
import shutil

base_path = r"E:\TradingAgents-CN-1.0.0-preview"

# 复制关键文件到 workspace
target_base = r"C:\Users\DELL\.openclaw-autoclaw\workspace\trading\TradingAgents_Source"
os.makedirs(target_base, exist_ok=True)

# 复制目录结构
dirs_to_copy = [
    "tradingagents/agents",
    "tradingagents/graph",
    "tradingagents/config",
    "docs"
]

print("开始复制 TradingAgents 源码...")
print("")

for dir_name in dirs_to_copy:
    src = os.path.join(base_path, dir_name)
    dst = os.path.join(target_base, dir_name.replace('/', '\\'))
    
    if os.path.exists(src):
        print(f"复制：{dir_name}")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"  -> {dst}")
    else:
        print(f"跳过（不存在）: {dir_name}")

# 复制 README 和关键文档
files_to_copy = [
    "README.md",
    "README_CN.md",
    "requirements.txt",
    "tradingagents/default_config.py"
]

for file in files_to_copy:
    src = os.path.join(base_path, file)
    dst = os.path.join(target_base, os.path.basename(file))
    
    if os.path.exists(src):
        print(f"复制：{file}")
        shutil.copy2(src, dst)

print("")
print("复制完成！")
print(f"目标路径：{target_base}")
