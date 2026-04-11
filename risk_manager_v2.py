#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风控管理器 v2.0 - 修复版
功能:
  1. 单一品种风险限制 (最多 1 单，总风险≤1%)
  2. 保证金水平自动平仓 (<150% 强制平仓)
  3. 三层移动止损
  4. 强制盈亏比检查 (≥1:1.5)

创建：2026-04-08
修复原因：2026-04-07 亏损 $143 (3 单 NZDUSD 集中风险)
"""

import MetaTrader5 as mt5
import sys
from datetime import datetime

# ========== 风控参数 ==========
MAX_SINGLE_SYMBOL_RISK = 1.0  # 单一品种最大风险 1% 账户
MAX_POSITIONS_PER_SYMBOL = 1  # 单一品种最多 1 单
MARGIN_LEVEL_CRITICAL = 150  # 危险线：强制平仓
MARGIN_LEVEL_WARNING = 200  # 警告线：禁止开新仓

# 移动止损参数
TRAILING_STOP_LAYERS = {
    'layer1': {'profit_pct': 0.3, 'action': 'breakeven'},  # 盈利 0.3% → 移至保本
    'layer2': {'profit_pct': 0.6, 'action': 'lock_50'},    # 盈利 0.6% → 锁定 50%
    'layer3': {'profit_pct': 1.0, 'action': 'lock_80'},    # 盈利 1.0% → 锁定 80%
}

# 盈亏比要求
MIN_RISK_REWARD = 1.5  # 最低盈亏比 1:1.5


def log_message(message, level="INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


def get_all_positions():
    """获取所有持仓"""
    positions = mt5.positions_get()
    if not positions:
        return []
    
    position_list = []
    for pos in positions:
        symbol = pos.symbol
        direction = "BUY" if pos.type == 0 else "SELL"
        entry_price = pos.price_open
        current_price = pos.price_current
        volume = pos.volume
        
        # 计算当前盈亏百分比
        if direction == "BUY":
            profit_pct = (current_price - entry_price) / entry_price * 100
        else:
            profit_pct = (entry_price - current_price) / entry_price * 100
        
        position_list.append({
            'ticket': pos.ticket,
            'symbol': symbol,
            'direction': direction,
            'volume': volume,
            'entry_price': entry_price,
            'current_price': current_price,
            'profit_usd': pos.profit,
            'profit_pct': profit_pct,
            'sl': pos.sl,
            'tp': pos.tp
        })
    
    return position_list


def check_symbol_exposure(symbol, positions):
    """检查单一品种风险敞口"""
    symbol_positions = [p for p in positions if p['symbol'] == symbol]
    
    # 检查持仓数量
    if len(symbol_positions) >= MAX_POSITIONS_PER_SYMBOL:
        return False, f"{symbol} 已有 {len(symbol_positions)} 单持仓 (上限 {MAX_POSITIONS_PER_SYMBOL})"
    
    # 计算总风险 (简化：用持仓价值占比)
    account = mt5.account_info()
    total_risk = sum([p['volume'] * p['entry_price'] for p in symbol_positions]) / account.balance * 100
    
    if total_risk > MAX_SINGLE_SYMBOL_RISK:
        return False, f"{symbol} 风险敞口 {total_risk:.2f}% > {MAX_SINGLE_SYMBOL_RISK}%"
    
    return True, "通过"


def check_margin_level():
    """检查保证金水平"""
    account = mt5.account_info()
    margin_level = account.margin_level
    
    # 空仓时保证金水平为 0，系正常状态
    positions = mt5.positions_get()
    if not positions or len(positions) == 0:
        return "SAFE", margin_level  # 空仓，安全
    
    if margin_level <= 0:
        return "CRITICAL", 0
    
    if margin_level < MARGIN_LEVEL_CRITICAL:
        return "CRITICAL", margin_level
    elif margin_level < MARGIN_LEVEL_WARNING:
        return "WARNING", margin_level
    else:
        return "SAFE", margin_level


def close_all_positions(reason=""):
    """强制平仓所有持仓"""
    log_message(f"开始强制平仓：{reason}", "ACTION")
    
    positions = get_all_positions()
    closed_count = 0
    
    for pos in positions:
        if close_position(pos['ticket'], reason):
            closed_count += 1
    
    log_message(f"强制平仓完成：{closed_count}/{len(positions)} 单", "RESULT")
    return closed_count


def close_position(ticket, reason=""):
    """平仓单个订单"""
    position = mt5.positions_get(ticket=ticket)
    if not position:
        log_message(f"找不到订单 {ticket}", "ERROR")
        return False
    
    pos = position[0]
    symbol = pos.symbol
    volume = pos.volume
    direction = pos.type
    
    # 准备平仓订单
    order_type = mt5.ORDER_TYPE_SELL if direction == 0 else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if direction == 0 else tick.bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": reason,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_message(f"平仓成功：{symbol} {volume} 手 @ {price:.5f}, 盈亏 ${pos.profit:.2f}", "SUCCESS")
        return True
    else:
        log_message(f"平仓失败：{result.comment}", "ERROR")
        return False


def update_trailing_stop(ticket):
    """三层移动止损"""
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return False
    
    pos = position[0]
    symbol = pos.symbol
    direction = pos.type
    entry_price = pos.price_open
    current_sl = pos.sl
    profit_pct = 0
    
    # 计算盈亏百分比
    tick = mt5.symbol_info_tick(symbol)
    current_price = tick.bid if direction == 0 else tick.ask
    
    if direction == 0:  # BUY
        profit_pct = (current_price - entry_price) / entry_price * 100
    else:  # SELL
        profit_pct = (entry_price - current_price) / entry_price * 100
    
    # 三层移动止损逻辑
    new_sl = 0
    
    # Layer 1: 盈利 0.3% → 移至保本
    if profit_pct >= TRAILING_STOP_LAYERS['layer1']['profit_pct']:
        new_sl = entry_price
        action = "移至保本"
    
    # Layer 2: 盈利 0.6% → 锁定 50% 利润
    elif profit_pct >= TRAILING_STOP_LAYERS['layer2']['profit_pct']:
        lock_pct = profit_pct * 0.5
        if direction == 0:
            new_sl = entry_price * (1 + lock_pct / 100)
        else:
            new_sl = entry_price * (1 - lock_pct / 100)
        action = "锁定 50% 利润"
    
    # Layer 3: 盈利 1.0% → 锁定 80% 利润
    elif profit_pct >= TRAILING_STOP_LAYERS['layer3']['profit_pct']:
        lock_pct = profit_pct * 0.8
        if direction == 0:
            new_sl = entry_price * (1 + lock_pct / 100)
        else:
            new_sl = entry_price * (1 - lock_pct / 100)
        action = "锁定 80% 利润"
    else:
        return False  # 未达到移动止损条件
    
    # 检查新止损是否优于当前止损
    if new_sl <= 0:
        return False
    
    if direction == 0:  # BUY
        if new_sl <= current_sl or new_sl >= current_price:
            return False  # 新止损不优于当前
    else:  # SELL
        if new_sl >= current_sl or new_sl <= current_price:
            return False  # 新止损不优于当前
    
    # 修改止损
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": ticket,
        "symbol": symbol,
        "sl": new_sl,
        "tp": pos.tp,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_message(f"移动止损：{symbol} {action}, 新 SL: {new_sl:.5f}", "SUCCESS")
        return True
    else:
        log_message(f"移动止损失败：{result.comment}", "ERROR")
        return False


def validate_risk_reward(entry, sl, tp, direction):
    """验证盈亏比"""
    if direction == "BUY":
        risk = abs(entry - sl)
        reward = abs(tp - entry)
    else:
        risk = abs(sl - entry)
        reward = abs(entry - tp)
    
    if risk <= 0:
        return False, "止损距离为 0"
    
    risk_reward = reward / risk
    
    if risk_reward < MIN_RISK_REWARD:
        return False, f"盈亏比不足：{risk_reward:.2f} < {MIN_RISK_REWARD}"
    
    return True, f"盈亏比合格：{risk_reward:.2f}"


def run_risk_check():
    """执行风控检查"""
    log_message("=" * 60)
    log_message("风控检查启动 v2.0")
    log_message("=" * 60)
    
    # 1. 检查保证金水平
    margin_status, margin_level = check_margin_level()
    log_message(f"保证金水平：{margin_level:.1f}% [{margin_status}]")
    
    if margin_status == "CRITICAL":
        log_message(f"WARNING: 保证金水平 < {MARGIN_LEVEL_CRITICAL}%，强制平仓!", "WARNING")
        close_all_positions(f"保证金水平过低：{margin_level:.1f}%")
        return "CRITICAL"
    
    # 2. 检查持仓
    positions = get_all_positions()
    log_message(f"当前持仓：{len(positions)} 单")
    
    for pos in positions:
        log_message(f"  {pos['symbol']} {pos['direction']}: {pos['profit_pips']:+.1f} pips (${pos['profit_usd']:+.2f}, {pos['profit_pct']:+.2f}%)")
    
    # 3. 执行移动止损
    log_message("检查移动止损...")
    trailing_count = 0
    for pos in positions:
        if update_trailing_stop(pos['ticket']):
            trailing_count += 1
    
    if trailing_count > 0:
        log_message(f"移动止损：{trailing_count} 单", "SUCCESS")
    
    # 4. 检查单一品种风险
    log_message("检查单一品种风险...")
    symbols = set([p['symbol'] for p in positions])
    for symbol in symbols:
        passed, message = check_symbol_exposure(symbol, positions)
        if not passed:
            log_message(f"WARNING: {message}", "WARNING")
    
    log_message("=" * 60)
    log_message("风控检查完成")
    log_message("=" * 60)
    
    return "OK"


if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 初始化失败")
        sys.exit(1)
    
    run_risk_check()
    mt5.shutdown()
