# -*- coding: utf-8 -*-
# 一键平仓所有持仓
# 执行方式: python close_all_positions.py
# 用途: 紧急情况下一键平仓所有仓位

import MetaTrader5 as mt5

def close_all_positions():
    """平仓所有持仓"""
    
    # 初始化连接
    if not mt5.initialize():
        print("❌ 连接 MT5 失败: ", mt5.last_error())
        return False
    
    print("✅ 连接成功")
    print(f"📊 账户: {mt5.account_info().login}")
    print()
    
    # 获取所有持仓
    positions = mt5.positions_get()
    
    if not positions:
        print("ℹ️ 当前没有持仓")
        mt5.shutdown()
        return True
    
    print(f"📋 发现 {len(positions)} 个持仓，开始平仓...")
    print()
    
    closed = 0
    failed = 0
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        volume = pos.volume
        direction = "BUY" if pos.type == 0 else "SELL"
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"❌ {symbol} #{ticket}: 无法获取价格，跳过")
            failed += 1
            continue
        
        # 平仓方向与持仓方向相反
        if pos.type == 0:  # BUY -> SELL
            close_price = tick.bid
            close_type = mt5.ORDER_TYPE_SELL
        else:  # SELL -> BUY
            close_price = tick.ask
            close_type = mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": close_price,
            "deviation": 30,
            "magic": pos.magic,
            "comment": "force-close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == 10009:
            print(f"✅ {symbol} #{ticket}: 平仓成功 (${pos.profit:.2f})")
            closed += 1
        else:
            print(f"❌ {symbol} #{ticket}: 平仓失败 - {result.comment} (retcode={result.retcode})")
            failed += 1
    
    print()
    print("=" * 40)
    print(f"平仓完成: 成功 {closed} / 失败 {failed}")
    
    # 显示最终余额
    account = mt5.account_info()
    print(f"最终余额: ${account.balance:.2f}")
    
    mt5.shutdown()
    return failed == 0

if __name__ == "__main__":
    print("=" * 40)
    print("🚀 一键平仓工具 - 强制平仓所有持仓")
    print("=" * 40)
    print()
    
    confirm = input("⚠️ 确认平仓所有持仓吗? 输入 YES 确认: ")
    
    if confirm.strip().upper() != "YES":
        print("✅ 已取消")
        exit()
    
    print()
    close_all_positions()
