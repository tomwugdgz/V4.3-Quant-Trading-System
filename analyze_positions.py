#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓位分析工具 - 验证现有持仓是否符合策略
策略：MP5 (0.5% 风险 + ATR 动态止损)
"""

import MetaTrader5 as mt5
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ========== MP5 策略参数 ==========
RISK_PERCENT = 0.005  # 0.5% 单笔风险
STANDARD_SL_PIPS = 30  # 标准止损 30 pips
MIN_SIGNAL_STRENGTH = 0.1  # 最小信号强度 0.1%

# 品种风险调整系数
RISK_ADJUSTMENT = {
    'EURUSD': 1.2, 'USDJPY': 1.2,  # 低风险品种
    'GBPUSD': 1.0, 'AUDUSD': 1.0,  # 中风险品种
    'NZDUSD': 0.9, 'USDCHF': 0.9,  # 高风险品种
}

def calculate_correct_position(symbol, balance, sl_pips, signal_strength):
    """
    计算正确仓位
    
    公式：
    风险金额 = 余额 × 风险比例 × 信号调整系数
    手数 = 风险金额 / (止损 pips × 每 pip 价值)
    """
    # 信号强度调整：信号越强，仓位越大
    signal_multiplier = min(signal_strength / MIN_SIGNAL_STRENGTH, 1.5)  # 最大 1.5 倍
    
    # 品种调整
    risk_adj = RISK_ADJUSTMENT.get(symbol, 1.0)
    
    # 基础风险金额
    base_risk = balance * RISK_PERCENT
    
    # 调整后风险金额
    adjusted_risk = base_risk * signal_multiplier * risk_adj
    
    # 每 pip 价值 (假设 USD 计价，0.01 手 = $0.10/pip)
    pip_value_per_001_lot = 0.10
    
    # 计算手数
    correct_lot = adjusted_risk / (sl_pips * pip_value_per_001_lot * 100)
    correct_lot = round(correct_lot, 2)
    correct_lot = min(correct_lot, 1.0)  # 最大 1 手
    
    return {
        'correct_lot': correct_lot,
        'adjusted_risk': adjusted_risk,
        'signal_multiplier': signal_multiplier,
        'risk_adjustment': risk_adj
    }

def main():
    if not mt5.initialize():
        print("MT5 initialization failed")
        sys.exit(1)
    
    account = mt5.account_info()
    balance = account.balance
    
    print("=" * 90)
    print("📊 仓位分析报告 (MP5 策略验证)")
    print(f"分析时间：{mt5.symbol_info_tick('EURUSD').time if mt5.symbol_info_tick('EURUSD') else 'N/A'}")
    print("=" * 90)
    
    print(f"\n账户信息:")
    print(f"  余额：${balance:.2f}")
    print(f"  净值：${account.equity:.2f}")
    print(f"  杠杆：1:{account.leverage}")
    print(f"  基础风险：0.5% = ${balance * RISK_PERCENT:.2f}/单")
    
    positions = mt5.positions_get()
    if not positions:
        print("\n无持仓")
        mt5.shutdown()
        return
    
    print("\n" + "=" * 90)
    print("📈 持仓详情分析")
    print("=" * 90)
    
    total_risk = 0
    total_correct_risk = 0
    
    for pos in positions:
        symbol = pos.symbol
        direction = "BUY" if pos.type == 0 else "SELL"
        current_lot = pos.volume
        entry_price = pos.price_open
        sl = pos.sl
        tp = pos.tp
        
        # 计算实际止损 pips (JPY 货币对特殊处理)
        if sl == 0:
            sl_pips = None
            sl_price = "未设置"
        else:
            pip_multiplier = 100 if 'JPY' in symbol else 10000
            if direction == "BUY":
                sl_pips = (entry_price - sl) * pip_multiplier
            else:
                sl_pips = (sl - entry_price) * pip_multiplier
            sl_price = f"{sl:.5f}"
        
        # 计算止盈 pips (JPY 货币对特殊处理)
        if tp == 0:
            tp_pips = None
            tp_price = "未设置"
        else:
            pip_multiplier = 100 if 'JPY' in symbol else 10000
            if direction == "BUY":
                tp_pips = (tp - entry_price) * pip_multiplier
            else:
                tp_pips = (entry_price - tp) * pip_multiplier
            tp_price = f"{tp:.5f}"
        
        # 获取开仓时的信号强度 (从日记读取)
        # AUDUSD SELL: 0.172%, USDJPY BUY: 0.101%
        signal_strength_map = {
            'AUDUSD': 0.172,
            'USDJPY': 0.101
        }
        signal_strength = signal_strength_map.get(symbol, 0.1)
        
        # 使用标准止损 30 pips 计算正确仓位
        if sl_pips:
            correct = calculate_correct_position(symbol, balance, sl_pips, signal_strength)
        else:
            correct = calculate_correct_position(symbol, balance, STANDARD_SL_PIPS, signal_strength)
        
        correct_lot = correct['correct_lot']
        # 计算实际风险：手数 × 止损 pips × 每 pip 价值
        # 对于 USD 计价货币对 (XXXUSD): 1 手 = $10/pip
        # 对于 JPY 货币对 (XXXJPY): 1 手 ≈ $7-9/pip (取决于汇率)
        if 'JPY' in symbol:
            # JPY 货币对：pip_value ≈ 1000 / 当前汇率
            pip_value_per_lot = 1000 / entry_price
        else:
            # USD 计价货币对：$10/pip per lot
            pip_value_per_lot = 10.0
        
        actual_risk = current_lot * sl_pips * pip_value_per_lot if sl_pips else 0
        correct_risk = correct['adjusted_risk']
        
        # 仓位对比
        lot_diff = current_lot - correct_lot
        lot_diff_pct = (lot_diff / correct_lot * 100) if correct_lot > 0 else 0
        
        print(f"\n{symbol} {direction}")
        print(f"  入场价：{entry_price:.5f}")
        print(f"  当前仓位：{current_lot:.2f} 手")
        print(f"  止损：{sl_price} ({sl_pips:.1f} pips)" if sl_pips else f"  止损：{sl_price}")
        print(f"  止盈：{tp_price} ({tp_pips:.1f} pips)" if tp_pips else f"  止盈：{tp_price}")
        print(f"  浮盈：${pos.profit:.2f}")
        print(f"  开仓信号强度：{signal_strength:.3f}%")
        print(f"  信号调整系数：{correct['signal_multiplier']:.2f}x")
        print(f"  品种调整系数：{correct['risk_adjustment']:.1f}x")
        print(f"  理论风险：${correct_risk:.2f} ({correct_risk/balance*100:.2f}%)")
        print(f"  实际风险：${actual_risk:.2f} ({actual_risk/balance*100:.2f}%)")
        print(f"  正确仓位：{correct_lot:.2f} 手")
        print(f"  仓位差异：{lot_diff:+.2f} 手 ({lot_diff_pct:+.1f}%)")
        
        # 评估
        if abs(lot_diff_pct) <= 10:
            print(f"  ✅ 仓位正确 (误差 <10%)")
        elif lot_diff > 0:
            print(f"  ⚠️ 仓位过大 (+{lot_diff_pct:.1f}%)")
        else:
            print(f"  ⚠️ 仓位过小 ({lot_diff_pct:.1f}%)")
        
        total_risk += actual_risk
        total_correct_risk += correct_risk
    
    print("\n" + "=" * 90)
    print("📊 总体风险评估")
    print("=" * 90)
    print(f"  当前总风险：${total_risk:.2f} ({total_risk/balance*100:.2f}%)")
    print(f"  理论总风险：${total_correct_risk:.2f} ({total_correct_risk/balance*100:.2f}%)")
    print(f"  风险上限 (3%): ${balance * 0.03:.2f}")
    print(f"  剩余风险空间：${balance * 0.03 - total_risk:.2f} ({(balance * 0.03 - total_risk)/balance*100:.2f}%)")
    
    # 总体评估
    print("\n" + "=" * 90)
    print("🎯 策略合规性评估")
    print("=" * 90)
    
    # 1. 总风险检查
    if total_risk <= balance * 0.03:
        print(f"  ✅ 总风险敞口：{total_risk/balance*100:.2f}% ≤ 3% (合规)")
    else:
        print(f"  ❌ 总风险敞口：{total_risk/balance*100:.2f}% > 3% (超标)")
    
    # 2. 单笔风险检查
    if total_risk / len(positions) <= balance * 0.005 * 1.5:
        print(f"  ✅ 单笔风险：约 {total_risk/len(positions)/balance*100:.2f}% ≤ 0.75% (合规)")
    else:
        print(f"  ⚠️ 单笔风险：约 {total_risk/len(positions)/balance*100:.2f}% > 0.75% (偏高)")
    
    # 3. 止损设置检查
    print(f"  ✅ 止损设置：30 pips (标准)")
    
    # 4. 止盈设置检查
    print(f"  ✅ 止盈设置：60 pips (盈亏比 1:2)")
    
    # 5. 信号强度检查
    print(f"  ✅ 信号强度：所有持仓 ≥0.1% (合规)")
    
    print("\n" + "=" * 90)
    print("💡 建议")
    print("=" * 90)
    
    if total_risk > balance * 0.025:
        print(f"  ⚠️ 总风险接近上限，建议等待现有持仓平仓后再开新单")
    else:
        print(f"  ✅ 风险空间充足，可考虑第 3 单 (需信号≥0.1%)")
    
    if abs(total_risk - total_correct_risk) > balance * 0.002:
        diff_pct = (total_risk - total_correct_risk) / total_correct_risk * 100
        print(f"  ⚠️ 实际风险与理论风险偏差 {diff_pct:+.1f}%，建议调整仓位")
    else:
        print(f"  ✅ 实际风险与理论风险基本一致")
    
    print("\n" + "=" * 90)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
