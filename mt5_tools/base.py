"""
MT5 工具库 - 基础模块
提供 MetaTrader5 常用操作的封装
"""

import MetaTrader5 as mt5
import json
from datetime import datetime
from pathlib import Path

# 初始化状态
_initialized = False

def initialize():
    """初始化 MT5 连接"""
    global _initialized
    if not _initialized:
        if not mt5.initialize():
            print(f"MT5 初始化失败：{mt5.last_error()}")
            return False
        _initialized = True
        print("MT5 连接成功")
    return True

def shutdown():
    """关闭 MT5 连接"""
    global _initialized
    mt5.shutdown()
    _initialized = False
    print("MT5 连接已关闭")

def get_account_info():
    """获取账户信息"""
    if not initialize():
        return None
    
    account_info = mt5.account_info()
    if account_info is None:
        return None
    
    return {
        "login": account_info.login,
        "server": account_info.server,
        "currency": account_info.currency,
        "leverage": account_info.leverage,
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin": account_info.margin,
        "margin_free": account_info.margin_free,
        "profit": account_info.profit,
        "timestamp": datetime.now().isoformat()
    }

def get_positions():
    """获取所有持仓"""
    if not initialize():
        return None
    
    positions = mt5.positions_get()
    if positions is None:
        return []
    
    result = []
    for pos in positions:
        result.append({
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "price_open": pos.price_open,
            "price_current": pos.price_current,
            "profit": pos.profit,
            "swap": pos.swap,
            "commission": pos.commission,
            "total_profit": pos.profit + pos.swap + pos.commission,
            "time": datetime.fromtimestamp(pos.time).isoformat()
        })
    
    return result

def get_symbol_info(symbol):
    """获取交易品种信息"""
    if not initialize():
        return None
    
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    
    return {
        "symbol": info.name,
        "description": info.description,
        "bid": info.bid,
        "ask": info.ask,
        "spread": info.spread,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "trade_mode": info.trade_mode,
        "trade_allowed": info.trade_mode != 0
    }

def get_rates(symbol, timeframe, count=100):
    """获取 K 线数据"""
    if not initialize():
        return None
    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        return None
    
    result = []
    for rate in rates:
        result.append({
            "time": datetime.fromtimestamp(rate['time']).isoformat(),
            "open": rate['open'],
            "high": rate['high'],
            "low": rate['low'],
            "close": rate['close'],
            "tick_volume": rate['tick_volume']
        })
    
    return result

def save_result(data, filename):
    """保存结果到 JSON 文件"""
    output_dir = Path("trading/mt5_tools/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"数据已保存：{filepath}")
    return str(filepath)

def load_config():
    """加载配置文件"""
    config_path = Path("trading/mt5_tools/config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置文件"""
    config_path = Path("trading/mt5_tools/config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"配置已保存：{config_path}")
