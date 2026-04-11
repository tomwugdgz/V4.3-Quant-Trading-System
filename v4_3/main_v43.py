"""
V4.3 主执行流程
版本：V4.3.0
创建：2026-04-10

功能：
1. 整合 Market Regime + Factor Score + Risk Agent
2. 完整交易决策流程
3. 自动执行（满足条件时）
"""

import MetaTrader5 as mt5
import sys
import os
from datetime import datetime
from typing import Dict, Optional

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from market_regime import MarketRegimeAgent, MarketRegime
from factor_score import FactorScoreEngine
from risk_agent import RiskAgent


class V43TradingSystem:
    """V4.3 交易系统"""
    
    def __init__(self):
        """初始化"""
        self.regime_agent = MarketRegimeAgent()
        self.factor_engine = FactorScoreEngine()
        self.risk_agent = RiskAgent()
        
        self.scan_results = []
        
    def initialize(self) -> bool:
        """初始化 MT5"""
        if not mt5.initialize():
            print("[ERROR] MT5 初始化失败")
            return False
        
        print("[OK] MT5 初始化成功")
        return True
    
    def scan_market(self, symbols: list = None) -> Dict:
        """
        扫描市场机会
        
        Args:
            symbols: 要扫描的品种列表
            
        Returns:
            Dict: 扫描结果
        """
        if symbols is None:
            symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"]
        
        print("=" * 80)
        print(f"V4.3 市场扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        opportunities = []
        
        for symbol in symbols:
            # 1. 判断市场状态
            regime = self.regime_agent.detect_regime(symbol, "H1")
            regime_report = self.regime_agent.get_regime_report(symbol, "H1")
            
            # 2. 检查是否可交易
            if not self.regime_agent.should_trade(regime):
                print(f"\n{symbol}: [SKIP] {regime.value} - 不交易")
                continue
            
            # 3. 计算因子评分
            factor_result = self.factor_engine.calculate_score(symbol, "H1")
            
            # 4. 获取动态阈值
            threshold = self.regime_agent.get_dynamic_threshold(regime)
            
            # 5. 判断是否达标
            score = factor_result['score']
            signal = factor_result['signal']
            
            # 转换评分为信号强度（简化）
            # score 50 = 0%, score 70 = 0.1%, score 100 = 0.3%
            signal_strength = (score - 50) / 200  # 转换为百分比
            
            is_strong_signal = signal_strength >= threshold / 100
            
            print(f"\n{symbol}:")
            print(f"  市场状态：{regime.value}")
            print(f"  信号阈值：{threshold:.2f}%")
            print(f"  因子评分：{score:.1f}")
            print(f"  信号强度：{signal_strength:.3f}%")
            print(f"  交易信号：{signal}")
            
            if is_strong_signal:
                print(f"  [OK] 达标信号")
                
                # 6. 风控检查
                account_info = mt5.account_info()
                positions = mt5.positions_get()
                
                account_dict = {
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "margin_level": account_info.margin_level,
                    "leverage": account_info.leverage
                }
                
                position_list = []
                if positions:
                    for pos in positions:
                        position_list.append({
                            "symbol": pos.symbol,
                            "type": "BUY" if pos.type == 0 else "SELL",
                            "volume": pos.volume,
                            "entry_price": pos.price_open,
                            "sl": pos.sl,
                            "tp": pos.tp
                        })
                
                # 计算建议仓位
                suggested_volume = self.risk_agent.calculate_position_size(symbol, account_dict)
                
                # 风控决策
                direction = "BUY" if "BUY" in signal else "SELL"
                risk_decision = self.risk_agent.can_trade(
                    symbol, direction, suggested_volume, account_dict, position_list
                )
                
                if risk_decision['can_trade']:
                    print(f"  [OK] 风控通过")
                    print(f"  建议仓位：{suggested_volume:.2f} 手")
                    
                    opportunities.append({
                        "symbol": symbol,
                        "direction": direction,
                        "volume": suggested_volume,
                        "score": score,
                        "signal_strength": signal_strength,
                        "regime": regime.value
                    })
                else:
                    print(f"  [REJECT] 风控否决")
                    for decision in risk_decision['decisions']:
                        if not decision['passed']:
                            for issue in decision['issues']:
                                print(f"     - {issue}")
            else:
                print(f"  [SKIP] 未达标")
        
        self.scan_results = opportunities
        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
    
    def execute_trade(self, opportunity: Dict) -> bool:
        """
        执行交易
        
        Args:
            opportunity: 交易机会
            
        Returns:
            bool: 是否成功
        """
        symbol = opportunity['symbol']
        direction = opportunity['direction']
        volume = opportunity['volume']
        
        print(f"\n[TRADE] 执行交易：{symbol} {direction} {volume:.2f} 手")
        
        # 获取当前价格
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"  [ERROR] 获取价格失败")
            return False
        
        price = tick.ask if direction == "BUY" else tick.bid
        
        # 计算止损止盈
        atr = self.risk_agent._get_atr(symbol)
        sl_distance = atr * 1.5
        tp_distance = atr * 3.0
        
        if direction == "BUY":
            sl = price - sl_distance
            tp = price + tp_distance
        else:
            sl = price + sl_distance
            tp = price - tp_distance
        
        # 下单
        order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,
            "comment": "V4.3_AutoTrade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"  ❌ 下单失败：{result.comment}")
            return False
        
        print(f"  [OK] 下单成功")
        print(f"     订单号：{result.order}")
        print(f"     入场价：{price:.5f}")
        print(f"     止损：{sl:.5f}")
        print(f"     止盈：{tp:.5f}")
        
        return True
    
    def run(self, auto_execute: bool = False):
        """
        运行扫描
        
        Args:
            auto_execute: 是否自动执行交易
        """
        if not self.initialize():
            return
        
        # 扫描市场
        result = self.scan_market()
        
        # 自动执行
        if auto_execute and result['opportunities']:
            print(f"\n[SIGNAL] 发现 {len(result['opportunities'])} 个交易机会")
            
            for opp in result['opportunities']:
                self.execute_trade(opp)
        else:
            print(f"\n[SCAN] 扫描完成，发现 {len(result['opportunities'])} 个交易机会")
            if not auto_execute:
                print("   自动执行未开启")
        
        mt5.shutdown()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="V4.3 交易系统")
    parser.add_argument("--auto-execute", action="store_true", help="自动执行交易")
    parser.add_argument("--symbols", nargs="+", help="要扫描的品种")
    
    args = parser.parse_args()
    
    system = V43TradingSystem()
    system.run(auto_execute=args.auto_execute)


if __name__ == "__main__":
    main()
