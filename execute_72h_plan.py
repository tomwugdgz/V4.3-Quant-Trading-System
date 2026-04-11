#!/usr/bin/env python
# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
import json
from datetime import datetime

# 初始化 MT5
if not mt5.initialize():
    print("MT5 initialization failed")
    exit(1)

# 获取账户信息
account = mt5.account_info()
print(f"账户: {account.login}")
print(f"余额: {account.balance} USD")

# 获取当前持仓
positions = mt5.positions_get()
print(f"\n当前持仓: {len(positions) if positions else 0} 笔")
if positions:
    for pos in positions:
        print(f"  {pos.symbol}: {'买入' if pos.type == 0 else '卖出'} {pos.volume} @ {pos.price_open}, 浮盈: {pos.profit}")

# 获取 H4 数据，计算 ATR 和趋势
def get_atr(symbol, timeframe=mt5.TIMEFRAME_H4, period=14):
    """计算 ATR"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 1)
    if rates is None or len(rates) < period:
        return None
    tr_list = []
    for i in range(1, len(rates)):
        high = rates[i]['high']
        low = rates[i]['low']
        prev_close = rates[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
    atr = sum(tr_list) / len(tr_list)
    return atr

def get_trend(symbol, timeframe=mt5.TIMEFRAME_H4):
    """简单均线趋势判断"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 25)
    if rates is None or len(rates) < 25:
        return None
    closes = [r['close'] for r in rates]
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    if ma5 > ma20 * 1.0005:
        return 'bullish'
    elif ma5 < ma20 * 0.9995:
        return 'bearish'
    else:
        return 'sideways'

# 目标币种 (USD 相关)
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'GBPUSD', 'EURGBP', 'USDCNH']

# 分析每个币种
analysis = []
for sym in symbols:
    symbol_info = mt5.symbol_info(sym)
    if symbol_info is None:
        continue
    if not symbol_info.visible:
        if not mt5.symbol_select(sym, True):
            continue
    atr = get_atr(sym)
    trend = get_trend(sym)
    tick = mt5.symbol_info_tick(sym)
    if atr is None or trend is None or tick is None:
        continue
    analysis.append({
        'symbol': sym,
        'atr': atr,
        'trend': trend,
        'bid': tick.bid,
        'ask': tick.ask,
        'point': symbol_info.point,
        'digits': symbol_info.digits,
        'contract_size': symbol_info.volume_min,
        'tick_value': symbol_info.trade_tick_value
    })

# 筛选趋势明确的币种
filtered = [a for a in analysis if a['trend'] != 'sideways']
print(f"\n趋势明确的币种: {len(filtered)}")
for a in filtered:
    print(f"  {a['symbol']}: {a['trend']}, ATR: {a['atr']}")

# 选择 6 个，保证多空都有
bull = [a for a in filtered if a['trend'] == 'bullish']
bear = [a for a in filtered if a['trend'] == 'bearish']
print(f"\n多头: {len(bull)}, 空头: {len(bear)}")

# 选择，保证多空至少各两个
selected = []
# 先取最多趋势的，如果多头多选多头，如果空头多选空头
if len(bull) >= len(bear):
    # 多头多，选最多3个多头，剩下空头
    selected.extend(bull[:3])
    remaining = 6 - len(selected)
    selected.extend(bear[:remaining])
else:
    # 空头多
    selected.extend(bear[:3])
    remaining = 6 - len(selected)
    selected.extend(bull[:remaining])

print(f"\n选定交易机会: {len(selected)} 个")
for s in selected:
    print(f"  {s['symbol']}: {s['trend']}, ATR={s['atr']:.6f}")

# 风险参数
total_risk = 280.0  # 总风险金额 $280 (¥2000)
risk_per_trade = total_risk / len(selected)  # 每笔风险
print(f"\n每笔风险: ${risk_per_trade:.2f}")

# 计算仓位，开仓
trades_executed = []

for s in selected:
    sym = s['symbol']
    trend = s['trend']
    atr = s['atr']
    point = s['point']
    digits = s['digits']
    
    # 获取最新价格
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        print(f"{sym} 获取价格失败，跳过")
        continue
        
    # 止损 = 1.5 * ATR
    sl_distance = 1.5 * atr
    # 止盈 = 2.5 * ATR，风险回报 1:1.67
    tp_distance = 2.5 * atr
    
    # 根据方向计算入场价、止损、止盈
    if trend == 'bullish':
        # 买入，做多
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        sl = price - sl_distance
        tp = price + tp_distance
    else:
        # 卖出，做空
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        sl = price + sl_distance
        tp = price - tp_distance
    
    # 计算仓位
    # 风险金额 / (止损距离 * 每点价值)
    symbol_info = mt5.symbol_info(sym)
    tick_value = symbol_info.trade_tick_value
    ticks_in_sl = sl_distance / symbol_info.point
    risk_per_lot = ticks_in_sl * tick_value
    volume = risk_per_trade / risk_per_lot
    
    # 调整到最小步长
    volume_step = symbol_info.volume_step
    volume = round(volume / volume_step) * volume_step
    
    # 限制在最小最大之间
    if volume < symbol_info.volume_min:
        volume = symbol_info.volume_min
    if volume > symbol_info.volume_max:
        volume = symbol_info.volume_max
    
    print(f"\n准备下单: {sym} {'买入' if trend == 'bullish' else '卖出'} {volume:.2f} 手")
    print(f"  入场: {price:.{digits}f}, 止损: {sl:.{digits}f}, 止盈: {tp:.{digits}f}")
    print(f"  风险: ${risk_per_trade:.2f}")
    
    # 下单
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": sym,
        "volume": float(volume),
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 234001,
        "comment": "旺财72h计划",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"下单失败: retcode={result.retcode}, {result.comment}")
    else:
        commission = getattr(result, 'commission', 0.0)
        print(f"下单成功: 订单={result.order}, 手续费={commission}")
        trades_executed.append({
            "symbol": sym,
            "direction": trend,
            "order_type": "buy" if trend == 'bullish' else "sell",
            "volume": float(volume),
            "price": float(price),
            "sl": float(sl),
            "tp": float(tp),
            "ticket": result.order,
            "commission": float(commission),
            "time": datetime.now().isoformat()
        })

# 保存交易记录
output = {
    "start_time": datetime.now().isoformat(),
    "end_time": None,
    "total_risk": float(total_risk),
    "risk_per_trade": float(risk_per_trade),
    "trades": trades_executed
}

with open("72h_trades.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n=== 执行完成 ===")
print(f"成功执行: {len(trades_executed)}/{len(selected)} 笔交易")
print(f"交易记录已保存到 72h_trades.json")

# 查询最终持仓
positions_final = mt5.positions_get()
print(f"\n当前总持仓: {len(positions_final) if positions_final else 0} 笔")

mt5.shutdown()
