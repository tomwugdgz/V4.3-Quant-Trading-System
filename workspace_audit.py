import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

tz = timezone(timedelta(hours=8))
trading = r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading'
memory = r'C:\Users\DELL\.openclaw-autoclaw\workspace\memory'
scene = r'C:\Users\DELL\.openclaw-autoclaw\memory-tdai\scene_blocks'
wiki = r'D:\LLM-Wiki\trading'

print('=' * 60)
print('旺财工作区全面筛查')
print('=' * 60)
print()

# 1. Trading directory analysis
print('【1. trading/ 目录分析】')
py_files = [f for f in os.listdir(trading) if f.endswith('.py')]
md_files = [f for f in os.listdir(trading) if f.endswith('.md')]
txt_files = [f for f in os.listdir(trading) if f.endswith('.txt')]

print('  总Python文件: {}'.format(len(py_files)))
print('  总Markdown文件: {}'.format(len(md_files)))
print('  总Text文件: {}'.format(len(txt_files)))
print()

# 按前缀分类
prefixes = defaultdict(list)
for f in py_files:
    prefix = f.split('_')[0] if '_' in f else f.rsplit('.', 1)[0]
    prefixes[prefix].append(f)

print('  文件前缀分布:')
for prefix, files in sorted(prefixes.items(), key=lambda x: len(x[1]), reverse=True):
    print('    {}_ : {} 个'.format(prefix, len(files)))

print()

# 按修改时间分类（30天分界）
cutoff = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
old_30 = []
recent = []

for f in py_files:
    path = os.path.join(trading, f)
    mtime = datetime.fromtimestamp(os.path.getmtime(path), tz)
    days = (cutoff - mtime).days
    if days > 30:
        old_30.append((f, days))
    else:
        recent.append((f, days))

print('  30天未修改: {} 个'.format(len(old_30)))
print('  30天内修改: {} 个'.format(len(recent)))
print()

# 建议保留的核心文件
core_files = [
    'patrol.py', 'kelly_analysis.py', 'system_check.py',
    'monitor_positions.py', 'evolver_v1.py', 'daily_summary.py',
    'auto_trade_self.py', 'auto_execute.py', 'auto_monitor.py'
]

# 建议删除的类别
deletable_prefixes = [
    'test_', 'check_', 'open_', 'close_',
    'debug_', 'quick_', 'backup', 'analyze',
    'execute_', 'verify_', 'run_', 'scan_'
]

print('  【建议保留的核心文件】')
for f in core_files:
    exists = os.path.exists(os.path.join(trading, f))
    print('    {} {}'.format(f.ljust(30), 'OK' if exists else 'MISSING'))
print()

print('  【建议归档/删除的文件类别】')
for prefix in deletable_prefixes:
    count = len([f for f in py_files if f.startswith(prefix)])
    if count > 0:
        print('    {}_ : {} 个'.format(prefix.replace('_', ''), count))

print()

# 2. Memory files
print('【2. memory/ 目录分析】')
if os.path.exists(memory):
    mem_files = [f for f in os.listdir(memory) if f.endswith('.md')]
    print('  Daily notes: {} 个'.format(len(mem_files)))
    # Sort by date
    dates = sorted(mem_files)
    if dates:
        print('  最早: {}'.format(dates[0]))
        print('  最晚: {}'.format(dates[-1]))
else:
    print('  目录不存在')
print()

# 3. Scene blocks
print('【3. Scene Blocks 分析】')
if os.path.exists(scene):
    blocks = os.listdir(scene)
    total_size = sum(os.path.getsize(os.path.join(scene, f)) for f in blocks)
    print('  场景块数量: {}'.format(len(blocks)))
    print('  总大小: {} bytes ({} KB)'.format(total_size, total_size//1024))
    for f in sorted(blocks, key=lambda x: os.path.getmtime(os.path.join(scene, x))):
        path = os.path.join(scene, f)
        size = os.path.getsize(path)
        mtime = datetime.fromtimestamp(os.path.getmtime(path), tz).strftime('%m-%d')
        print('    {} ({:.1f}KB, last: {})'.format(f, size/1024, mtime))
else:
    print('  目录不存在')
print()

# 4. Wiki files
print('【4. Wiki/LLM-Wiki/trading 分析】')
if os.path.exists(wiki):
    wiki_files = os.listdir(wiki)
    print('  文件数: {}'.format(len(wiki_files)))
else:
    print('  目录不存在')
print()

# 5. 每次对话加载内容
print('【5. 每次对话加载内容估算】')
workspace_files = [
    'AGENTS.md', 'SOUL.md', 'USER.md', 'TOOLS.md',
    'MEMORY.md', 'HEARTBEAT.md', 'IDENTITY.md',
    'scene_blocks/* (12个, ~150KB total)'
]
print('  固定加载:')
for f in workspace_files:
    print('    - {}'.format(f))
print('  总加载量: ~200KB/对话 (含场景块)')
print()

# 6. 精简建议
print('【6. 精简建议】')
print('  1. 归档 trading/ 下 30天未修改的非核心文件')
print('  2. 合并 scene_blocks 中已合并的内容（竖屏短视频已合并到小红书运营体系）')
print('  3. 删除 test_*.py, check_*.py, debug_*.py 等一次性文件')
print('  4. MEMORY.md 中过时内容清理')
print()

print('=== 建议创建每周自动瘦身 cron ===')
print('每周一 14:00 执行：归档旧文件 + 删除临时文件 + 合并重复场景块')
