"""
MT5 市场扫描工具
扫描多个交易品种，寻找交易机会
"""

import MetaTrader5 as mt5
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from base import initialize, shutdown, get_symbol_info, get_rates, save_result

# 常见交易品种列表
SYMBOLS = {
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"],
    "crypto": ["BTCUSD", "ETHUSD"],
    "metals": ["XAUUSD", "XAGUSD"],
    "indices": ["US30", "NAS100", "SPX500"]
}

def scan_market(groups=None):
    """
    扫描市场
    
    参数:
        groups: 要扫描的品种组，如 ["forex", "crypto"]，None 表示全部
    """
    print("=" * 70)
    print("MT5 市场扫描")
    print("=" * 70)
    
    if not initialize():
        return None
    
    # 确定要扫描的品种
    if groups is None:
        groups = list(SYMBOLS.keys())
    
    symbols_to_scan = []
    for group in groups:
        if group in SYMBOLS:
            symbols_to_scan.extend(SYMBOLS[group])
    
    print(f"\n扫描品种组：{groups}")
    print(f"扫描品种数量：{len(symbols_to_scan)}")
    print("=" * 70)
    
    results = []
    
    for symbol in symbols_to_scan:
        info = get_symbol_info(symbol)
        if not info or not info['trade_allowed']:
            continue
        
        # 获取最近 100 根 K 线
        rates = get_rates(symbol, mt5.TIMEFRAME_H1, 100)
        if not rates:
            continue
        
        # 计算简单指标
        closes = [r['close'] for r in rates[-20:]]  # 最近 20 根
        highs = [r['high'] for r in rates[-20:]]
        lows = [r['low'] for r in rates[-20:]]
        
        # 计算涨跌幅
        price_change = (closes[-1] - closes[0]) / closes[0] * 100
        
        # 计算波动率
        avg_range = sum(h - l for h, l in zip(highs, lows)) / len(highs)
        current_range = rates[-1]['high'] - rates[-1]['low']
        
        # 判断趋势
        ma_short = sum(closes[-5:]) / 5
        ma_long = sum(closes[-10:]) / 10
        trend = "UP" if ma_short > ma_long else "DOWN"
        
        result = {
            "symbol": symbol,
            "bid": info['bid'],
            "ask": info['ask'],
            "spread": info['spread'],
            "price_change_20": f"{price_change:.2f}%",
            "volatility": f"{avg_range:.5f}",
            "current_range": f"{current_range:.5f}",
            "trend": trend,
            "ma_short": f"{ma_short:.5f}",
            "ma_long": f"{ma_long:.5f}"
        }
        
        results.append(result)
        
        # 打印结果
        arrow = "↑" if trend == "UP" else "↓"
        print(f"{symbol:8} | Bid: {info['bid']:9.5f} | Spread: {info['spread']:3} | Change: {price_change:+6.2f}% | Trend: {arrow} {trend}")
    
    print("=" * 70)
    
    # 保存结果
    save_result({
        "timestamp": datetime.now().isoformat(),
        "groups": groups,
        "symbols_count": len(results),
        "results": results
    }, f"market-scan-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    
    shutdown()
    print(f"\n扫描完成！共扫描 {len(results)} 个品种")
    
    return results

def find_opportunities(min_change=1.0):
    """
    寻找交易机会（涨跌幅超过阈值的品种）
    
    参数:
        min_change: 最小涨跌幅百分比
    """
    print("=" * 70)
    print("MT5 交易机会扫描")
    print("=" * 70)
    
    results = scan_market()
    if not results:
        return None
    
    opportunities = []
    for r in results:
        change = float(r['price_change_20'].replace('%', ''))
        if abs(change) >= min_change:
            opportunities.append(r)
    
    print(f"\n发现 {len(opportunities)} 个交易机会（涨跌幅 >= {min_change}%）")
    print("=" * 70)
    
    for opp in opportunities:
        direction = "做多" if float(opp['price_change_20'].replace('%', '')) > 0 else "做空"
        print(f"{opp['symbol']}: {opp['price_change_20']} | 建议：{direction} | 趋势：{opp['trend']}")
    
    return opportunities

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "opp":
            find_opportunities()
        else:
            scan_market([sys.argv[1]])
    else:
        scan_market()
