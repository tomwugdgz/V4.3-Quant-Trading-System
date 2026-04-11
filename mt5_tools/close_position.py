"""
MT5 平仓工具
支持全部平仓、按品种平仓、按订单平仓
"""

import MetaTrader5 as mt5
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from base import initialize, shutdown, get_positions, save_result

def close_all_positions():
    """平掉所有持仓"""
    print("=" * 70)
    print("MT5 全部平仓")
    print("=" * 70)
    
    if not initialize():
        return None
    
    positions = get_positions()
    if not positions:
        print("\n当前无持仓")
        shutdown()
        return []
    
    print(f"\n当前持仓数量：{len(positions)}")
    results = []
    
    for pos in positions:
        result = close_position(pos['symbol'], pos['type'], pos['volume'])
        results.append(result)
    
    shutdown()
    
    # 统计
    total_profit = sum(r['profit'] for r in results if r)
    print(f"\n平仓完成！总盈亏：${total_profit:.2f}")
    
    # 保存结果
    save_result({
        "timestamp": datetime.now().isoformat(),
        "closed_count": len(results),
        "total_profit": total_profit,
        "results": results
    }, f"close-all-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    
    return results

def close_position(symbol, order_type, volume):
    """
    平掉指定品种的持仓
    
    参数:
        symbol: 交易品种
        order_type: "BUY" 或 "SELL" (平仓方向与持仓相反)
        volume: 手数
    """
    if not initialize():
        return None
    
    # 获取当前价格
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"无法获取 {symbol} 信息")
        return None
    
    # 确定平仓订单类型（与持仓相反）
    if order_type == "BUY":
        # 持有多单，平仓用 SELL
        action = mt5.ORDER_TYPE_SELL
        price = symbol_info.bid
    else:
        # 持有空单，平仓用 BUY
        action = mt5.ORDER_TYPE_BUY
        price = symbol_info.ask
    
    # 构建订单请求
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": action,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "close_position",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # 发送订单
    result = mt5.order_send(request)
    
    order_result = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "order_type": order_type,
        "volume": volume,
        "price": price,
        "retcode": result.retcode if result else None,
        "deal": result.deal if result else None,
        "profit": result.profit if result else 0,
        "success": result.retcode == mt5.TRADE_RETCODE_DONE if result else False
    }
    
    status = "[OK]" if order_result['success'] else "[FAIL]"
    print(f"{status} {symbol} {order_type} {volume}手 @ {price:.5f} 盈亏：${order_result['profit']:.2f}")
    
    if not initialize():
        return None
    shutdown()
    
    return order_result

def close_by_symbol(symbol):
    """平掉指定品种的所有持仓"""
    print("=" * 70)
    print(f"MT5 平仓 - {symbol}")
    print("=" * 70)
    
    if not initialize():
        return None
    
    positions = get_positions()
    target_positions = [p for p in positions if p['symbol'] == symbol]
    
    if not target_positions:
        print(f"\n{symbol} 无持仓")
        shutdown()
        return []
    
    print(f"\n{symbol} 持仓数量：{len(target_positions)}")
    results = []
    
    for pos in target_positions:
        result = close_position(pos['symbol'], pos['type'], pos['volume'])
        results.append(result)
    
    shutdown()
    
    total_profit = sum(r['profit'] for r in results if r)
    print(f"\n{symbol} 平仓完成！总盈亏：${total_profit:.2f}")
    
    save_result({
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "closed_count": len(results),
        "total_profit": total_profit,
        "results": results
    }, f"close-{symbol}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            close_all_positions()
        else:
            close_by_symbol(sys.argv[1])
    else:
        print("用法：python close_position.py <all|symbol>")
        print("示例：python close_position.py all")
        print("示例：python close_position.py EURUSD")
