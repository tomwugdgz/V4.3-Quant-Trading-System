# -*- coding: utf-8 -*-
# 平仓指定货币对的所有持仓
# 使用: python close_by_symbol.py EURUSD

import MetaTrader5 as mt5
import sys

def close_symbol_positions(symbol_name):
    """平仓指定货币对的所有持仓"""
    
    if not mt5.initialize():
        print("❌ 连接 MT5 失败: ", mt5.last_error())
        return False
    
    positions = mt5.positions_get()
    if not positions:
        print("ℹ️ 当前没有持仓")
        mt5.shutdown()
        return True
    
    symbol_positions = [p for p in positions if p.symbol == symbol_name]
    
    if not symbol_positions:
        print(f"ℹ️ 没有找到 {symbol_name} 的持仓")
        mt5.shutdown()
        return True
    
    print(f"📋 发现 {len(symbol_positions)} 个 {symbol_name} 持仓")
    print()
    
    closed = 0
    failed = 0
    
    for pos in symbol_positions:
        ticket = pos.ticket
        volume = pos.volume
        
        tick = mt5.symbol_info_tick(symbol_name)
        if not tick:
            print(f"❌ {symbol_name} #{ticket}: 无法获取价格")
            failed += 1
            continue
        
        if pos.type == 0:  # BUY -> SELL
            close_price = tick.bid
            close_type = mt5.ORDER_TYPE_SELL
        else:  # SELL -> BUY
            close_price = tick.ask
            close_type = mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol_name,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": close_price,
            "deviation": 30,
            "magic": pos.magic,
            "comment": "close-symbol",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == 10009:
            print(f"✅ {symbol_name} #{ticket}: 平仓成功 P/L ${pos.profit:.2f}")
            closed += 1
        else:
            print(f"❌ {symbol_name} #{ticket}: 失败 - {result.comment}")
            failed += 1
    
    print()
    print(f"完成: 成功 {closed} / 失败 {failed}")
    mt5.shutdown()
    return failed == 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python close_by_symbol.py <symbol>")
        print("示例: python close_by_symbol.py AUDUSD")
        exit()
    
    symbol = sys.argv[1]
    close_symbol_positions(symbol)
