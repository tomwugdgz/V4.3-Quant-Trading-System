import json

path = r'C:\Users\DELL\.openclaw-autoclaw\workspace\trading\patrol.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update version
content = content.replace('30min Patrol - v5.5 第一性原理版', '30min Patrol - v5.6 累积优化版')
content = content.replace('Patrol Smart v5.5', 'Patrol Smart v5.6')
content = content.replace('v5.5 第一性原理版', 'v5.6 累积优化版')

# 2. Update Kelly Registry - add XAUUSD, remove EURUSD etc
old_registry = """KELLY_REGISTRY = {
    # 高 Kelly（kf > 10%）：优先交易
    'USDCAD':  {'W': 0.71, 'R': 0.87, 'kf': 0.388},
    'XAUUSD':  {'W': 1.00, 'R': 3.00, 'kf': 0.500},  # 2w/0l，极端高期望
    # 中 Kelly（kf 5-10%）：标准风险
    'AUDUSD':  {'W': 0.62, 'R': 0.67, 'kf': 0.067},
    'USDCHF':  {'W': 0.57, 'R': 0.85, 'kf': 0.057},
    'GBPUSD':  {'W': 0.52, 'R': 1.03, 'kf': 0.061},
    # 低 Kelly（kf 3-5%）：v5.5禁止交易（来福P0）
    'EURUSD':  {'W': 0.35, 'R': 2.06, 'kf': 0.034},
    # 未注册品种：v5.5禁止交易（来福P0）
    # EURCAD, EURGBP, GBPAUD, NZDJPY, CADJPY, CHFJPY, XAGUSD — 不在注册表，不开仓
    # 负 Kelly（kf < 0%）：Micro-Test 模式（小单重新调优验证）
    'NZDUSD':  {'W': 0.57, 'R': 0.25, 'kf': -1.129},
    'USDJPY':  {'W': 0.38, 'R': 0.41, 'kf': -1.138},
    'AUDJPY':  {'W': 0.20, 'R': 0.75, 'kf': -0.866},
    'BTCUSD':  {'W': 0.25, 'R': 0.18, 'kf': -3.837},  # 加密货币永久屏蔽
}"""

new_registry = """KELLY_REGISTRY = {
    # 正 EV 品种（基于真实 MT5 数据 221 笔）
    # === 核心交易品种 ===
    'USDCAD':  {'W': 0.71, 'R': 0.87, 'kf': 0.388},  # 7笔 +$14.21 EV=0.339
    'AUDUSD':  {'W': 0.62, 'R': 0.67, 'kf': 0.067},  # 48笔 +$40.61 EV=0.045
    'USDCHF':  {'W': 0.57, 'R': 0.85, 'kf': 0.057},  # 37笔 +$28.91 EV=0.049
    'GBPUSD':  {'W': 0.52, 'R': 1.03, 'kf': 0.061},  # 21笔 +$19.98 EV=0.063
    # === Micro-Test 品种（小单累积数据）===
    'XAUUSD':  {'W': 1.00, 'R': 3.00, 'kf': 0.500},  # 2笔 +$396 样本不足 Micro-Test
    # 永久禁止（负 EV）: EURUSD/NZDUSD/USDJPY/AUDJPY/BTCUSD/AUDCHF
}"""

content = content.replace(old_registry, new_registry)

# 3. Update version header comment
old_header = """v5.0 变更（2026-05-09）：
  - Kelly 公式作为底层仓位决策逻辑
  - 信号门槛 45%，SUPER 信号 60%
  - 信号 >=60%：0.5% 风险仓位
  - 信号 45-60%：0.3% 风险仓位
  - 信号 <45%：不开仓
  - Kelly 作为底层仓位决策（历史胜率 p、盈亏比 R）
  - Kelly f* < 5% 品种 永久屏蔽"""

new_header = """v5.6 变更（2026-05-13）：
  - 基于 221 笔真实 MT5 数据重建 Kelly 注册表
  - 只交易 4 个正 EV 品种 + XAUUSD Micro-Test
  - XAUUSD 加入 Micro-Test 模式（0.02手，信号 70%+）
  - TP/SL 降至 1:1.5（实际 R=0.90）
  - 止损缓冲 = ATR x 0.5（动态自适应）"""

content = content.replace(old_header, new_header)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('v5.6 applied: XAUUSD Micro-Test added')
