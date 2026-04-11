"""
MT5 开仓工具
支持市价单开多/开空
"""

import MetaTrader5 as mt5
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from base import initialize, shutdown, get_symbol_info, save_result

def open_position(symbol, order_type, volume, sl=0, tp=0, comment="MT5_Tool"):
    """
    开仓函数
    
    参数:
        symbol: 交易品种 (如 "EURUSD", "XAUUSD")
        order_type: "BUY" 或 "SELL"
        volume: 手数 (如 0.01, 0.1, 1.0)
        sl: 止损价格 (0 表示无止损)
        tp: 止盈价格 (0 表示无止盈)
        comment: 订单备注
    
    返回:
        订单结果字典
    """
    print("=" * 70)
    print("MT5 开仓订单")
    print("=" * 70)
    
    if not initialize():
        return None
    
    # 获取品种信息
    info = get_symbol_info(symbol)
    if not info:
        print(f"无法获取 {symbol} 信息")
        shutdown()
        return None
    
    print(f"\n交易品种：{symbol}")
    print(f"当前价格：Bid={info['bid']}, Ask={info['ask']}")
    print(f"订单类型：{order_type}")
    print(f"手数：{volume}")
    print(f"止损：{sl if sl > 0 else '无'}")
    print(f"止盈：{tp if tp > 0 else '无'}")
    
    # 确定订单类型
    if order_type.upper() == "BUY":
        action = mt5.ORDER_TYPE_BUY
        price = info['ask']
    elif order_type.upper() == "SELL":
        action = mt5.ORDER_TYPE_SELL
        price = info['bid']
    else:
        print(f"无效的订单类型：{order_type}")
        shutdown()
        return None
    
    # 构建订单请求
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": action,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,  # 最大滑点 20 点
        "magic": 234000,  # 魔术编号，用于标识 EA
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,  # 订单有效期：直到取消
        "type_filling": mt5.ORDER_FILLING_IOC,  # 立即成交或取消
    }
    
    # 发送订单
    print(f"\n发送订单...")
    result = mt5.order_send(request)
    
    if result is None:
        print(f"订单发送失败：{mt5.last_error()}")
        shutdown()
        return None
    
    # 解析结果
    order_result = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "order_type": order_type,
        "volume": volume,
        "price_requested": price,
        "retcode": result.retcode,
        "deal": result.deal,
        "order": result.order,
        "volume_done": result.volume,
        "price_done": result.price,
        "comment": result.comment,
        "success": result.retcode == mt5.TRADE_RETCODE_DONE
    }
    
    print(f"\n订单结果")
    print("=" * 70)
    print(f"返回码：{result.retcode}")
    print(f"成交：{result.deal}")
    print(f"订单号：{result.order}")
    print(f"成交手数：{result.volume}")
    print(f"成交价格：{result.price}")
    print(f"备注：{result.comment}")
    print("=" * 70)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"\n[SUCCESS] 开仓成功!")
    else:
        print(f"\n[FAILED] 开仓失败：{result.comment}")
    
    # 保存结果
    save_result(order_result, f"order-{symbol}-{order_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    
    shutdown()
    return order_result

def buy(symbol, volume, sl=0, tp=0):
    """快捷开多单"""
    return open_position(symbol, "BUY", volume, sl, tp)

def sell(symbol, volume, sl=0, tp=0):
    """快捷开空单"""
    return open_position(symbol, "SELL", volume, sl, tp)

if __name__ == "__main__":
    # 示例：开 0.01 手 EURUSD 多单
    import sys
    if len(sys.argv) >= 3:
        symbol = sys.argv[1]
        order_type = sys.argv[2]
        volume = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
        open_position(symbol, order_type, volume)
    else:
        print("用法：python open_position.py <symbol> <BUY|SELL> [volume]")
        print("示例：python open_position.py EURUSD BUY 0.01")
