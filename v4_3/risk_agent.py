"""
Risk Agent - 独立风控 Agent
版本：V4.3.0
创建：2026-04-10

功能：
1. 实时风险监控
2. 动态仓位计算
3. 交易否决权
4. VaR 计算
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import json


class RiskAgent:
    """独立风控 Agent"""
    
    def __init__(self, config_path: str = "config/risk_params.json"):
        """
        初始化
        
        Args:
            config_path: 风控参数配置文件
        """
        self.config = self._load_config(config_path)
        self.var_cache = {}  # VaR 缓存
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 默认配置
            return {
                "max_leverage": 3.0,
                "min_margin_level": 200,
                "max_daily_loss_percent": 0.03,
                "max_total_risk": 0.03,
                "max_positions": 3,
                "max_position_per_symbol": 1,
                "var_confidence": 0.95,
                "var_lookback_days": 30
            }
    
    def can_trade(self, symbol: str, direction: str, volume: float, 
                  account_info: Dict, positions: List[Dict]) -> Dict:
        """
        判断是否可以交易
        
        Args:
            symbol: 交易品种
            direction: 方向（BUY/SELL）
            volume: 手数
            account_info: 账户信息
            positions: 当前持仓列表
            
        Returns:
            Dict: 决策结果
        """
        decisions = []
        can_trade = True
        
        # 1. 账户级检查
        account_check = self._check_account_level(account_info)
        if not account_check['passed']:
            can_trade = False
            decisions.append(account_check)
        
        # 2. 仓位检查
        position_check = self._check_positions(symbol, positions)
        if not position_check['passed']:
            can_trade = False
            decisions.append(position_check)
        
        # 3. 风险敞口检查
        risk_check = self._check_risk_exposure(symbol, volume, positions)
        if not risk_check['passed']:
            can_trade = False
            decisions.append(risk_check)
        
        # 4. VaR 检查
        var_check = self._check_var(symbol, volume, account_info)
        if not var_check['passed']:
            can_trade = False
            decisions.append(var_check)
        
        # 5. 相关性检查
        correlation_check = self._check_correlation(symbol, direction, positions)
        if not correlation_check['passed']:
            can_trade = False
            decisions.append(correlation_check)
        
        return {
            "can_trade": can_trade,
            "decisions": decisions,
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_account_level(self, account_info: Dict) -> Dict:
        """账户级检查"""
        margin_level = account_info.get('margin_level', 500)  # 默认 500%（安全值）
        leverage = account_info.get('leverage', 5)  # 默认 5x
        
        issues = []
        
        # 保证金水平检查（仅当数据有效时）
        if margin_level > 0 and margin_level < self.config['min_margin_level']:
            issues.append(f"保证金水平 {margin_level:.0f}% < {self.config['min_margin_level']}%")
        
        # 杠杆检查（仅当数据有效时）
        if leverage > 0 and leverage > self.config['max_leverage']:
            issues.append(f"实际杠杆 {leverage:.1f}x > {self.config['max_leverage']}x")
        
        return {
            "check": "account_level",
            "passed": len(issues) == 0,
            "issues": issues,
            "margin_level": margin_level,
            "leverage": leverage
        }
    
    def _check_positions(self, symbol: str, positions: List[Dict]) -> Dict:
        """仓位检查"""
        issues = []
        
        # 总持仓数量检查
        if len(positions) >= self.config['max_positions']:
            issues.append(f"持仓数量 {len(positions)} >= 上限 {self.config['max_positions']}")
        
        # 单一品种持仓检查
        symbol_positions = [p for p in positions if p['symbol'] == symbol]
        if len(symbol_positions) >= self.config['max_position_per_symbol']:
            issues.append(f"{symbol} 持仓 {len(symbol_positions)} >= 上限 {self.config['max_position_per_symbol']}")
        
        return {
            "check": "positions",
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def _check_risk_exposure(self, symbol: str, volume: float, positions: List[Dict]) -> Dict:
        """风险敞口检查"""
        issues = []
        
        # 计算总风险（简化：使用手数代替风险金额）
        total_volume = volume + sum(pos.get('volume', 0) for pos in positions)
        
        # 最大允许手数（基于 3% 总风险，单手风险约 0.5%）
        max_volume = 6.0  # 最多 6 手
        
        if total_volume > max_volume:
            issues.append(f"总持仓手数 {total_volume:.2f} > 上限 {max_volume:.2f}")
        
        return {
            "check": "risk_exposure",
            "passed": len(issues) == 0,
            "issues": issues,
            "total_volume": total_volume
        }
    
    def _calculate_position_risk(self, position: Dict) -> float:
        """计算单个持仓风险"""
        # 简化计算：风险 = 手数 * 点值 * 止损点数 / 账户净值
        volume = position.get('volume', 0)
        sl_distance = abs(position.get('entry_price', 0) - position.get('sl', 0))
        
        # 假设点值为 10（简化）
        point_value = 10
        risk = volume * sl_distance * point_value
        
        return risk
    
    def _calculate_new_position_risk(self, symbol: str, volume: float) -> float:
        """计算新持仓风险"""
        # 获取当前价格
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return 0
        
        # 获取止损距离（基于 ATR）
        atr = self._get_atr(symbol)
        sl_distance = atr * 1.5  # 1.5 倍 ATR 止损
        
        # 点值
        point_value = self._get_point_value(symbol)
        
        risk = volume * sl_distance * point_value
        
        return risk
    
    def _get_atr(self, symbol: str, period: int = 14) -> float:
        """获取 ATR"""
        # 获取 K 线
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        if rates is None or len(rates) < period + 1:
            return 0
        
        df = pd.DataFrame(rates)
        
        # 计算 ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr.iloc[-1]
    
    def _get_point_value(self, symbol: str) -> float:
        """获取点值"""
        # 简化处理，实际应该根据品种计算
        major_pairs = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
        if symbol in major_pairs:
            return 10  # 标准手点值
        return 10
    
    def _check_var(self, symbol: str, volume: float, account_info: Dict) -> Dict:
        """VaR 检查"""
        issues = []
        
        # 计算 VaR
        var_95 = self._calculate_var(symbol, volume)
        
        # VaR 上限：2% 净值
        equity = account_info.get('equity', 10000)
        if equity <= 0:
            equity = 10000  # 默认值
        max_var = equity * 0.02
        
        # 仅当 VaR 计算有效时检查
        if var_95 > 0 and var_95 > max_var:
            issues.append(f"VaR(95%) ${var_95:.2f} > 上限 ${max_var:.2f}")
        
        return {
            "check": "var",
            "passed": len(issues) == 0,
            "issues": issues,
            "var_95": var_95,
            "max_var": max_var
        }
    
    def _calculate_var(self, symbol: str, volume: float) -> float:
        """
        计算 VaR（Value at Risk）
        
        使用历史模拟法
        """
        # 获取历史收益率
        returns = self._get_historical_returns(symbol)
        
        if len(returns) < 20:
            return 0
        
        # 计算分位数
        var_95 = np.percentile(returns, 5)  # 5% 分位数
        
        # 转换为金额
        position_value = volume * 100000  # 标准手
        var_amount = abs(var_95) * position_value
        
        return var_amount
    
    def _get_historical_returns(self, symbol: str, days: int = 30) -> List[float]:
        """获取历史收益率"""
        # 获取日线数据
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, days)
        
        if rates is None or len(rates) < 2:
            return []
        
        df = pd.DataFrame(rates)
        returns = df['close'].pct_change().dropna().tolist()
        
        return returns
    
    def _check_correlation(self, symbol: str, direction: str, positions: List[Dict]) -> Dict:
        """相关性检查"""
        issues = []
        
        # 定义相关性组
        correlation_groups = {
            "USD_bull": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],  # USD 涨，这些跌
            "USD_bear": ["USDJPY", "USDCHF", "USDCAD"],  # USD 跌，这些跌
            "commodity": ["AUDUSD", "NZDUSD", "USDCAD"],  # 商品货币
            "safe_haven": ["USDJPY", "CHFJPY", "XAUUSD"]  # 避险
        }
        
        # 检查同向持仓
        for group_name, group_symbols in correlation_groups.items():
            if symbol in group_symbols:
                # 检查组内已有持仓
                for pos in positions:
                    if pos['symbol'] in group_symbols and pos['symbol'] != symbol:
                        if pos['type'] == direction:
                            issues.append(f"与 {pos['symbol']} 同向持仓，相关性风险")
        
        return {
            "check": "correlation",
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def calculate_position_size(self, symbol: str, account_info: Dict) -> float:
        """
        计算合适仓位
        
        Args:
            symbol: 交易品种
            account_info: 账户信息
            
        Returns:
            float: 建议手数
        """
        # 基于风险百分比计算
        risk_percent = 0.005  # 单笔风险 0.5%
        risk_amount = account_info.get('balance', 10000) * risk_percent
        
        # 获取止损距离
        atr = self._get_atr(symbol)
        sl_distance = atr * 1.5  # 1.5 倍 ATR
        
        # 点值
        point_value = self._get_point_value(symbol)
        
        # 计算手数
        if sl_distance == 0 or point_value == 0:
            return 0
        
        volume = risk_amount / (sl_distance * point_value)
        
        # 限制最小和最大手数（更保守）
        volume = max(0.01, min(volume, 0.10))  # 最大 0.1 手
        
        # 四舍五入到 0.01
        volume = round(volume, 2)
        
        return volume
    
    def get_risk_report(self, account_info: Dict, positions: List[Dict]) -> Dict:
        """
        生成风控报告
        
        Args:
            account_info: 账户信息
            positions: 持仓列表
            
        Returns:
            Dict: 风控报告
        """
        # 计算各项指标
        total_risk = sum(self._calculate_position_risk(pos) for pos in positions)
        margin_level = account_info.get('margin_level', 0)
        leverage = account_info.get('leverage', 1)
        daily_pnl = account_info.get('daily_profit', 0)
        daily_pnl_percent = daily_pnl / account_info.get('balance', 10000)
        
        report = {
            "margin_level": margin_level,
            "leverage": leverage,
            "total_risk": total_risk,
            "daily_pnl_percent": daily_pnl_percent,
            "positions_count": len(positions),
            "risk_status": "normal",
            "warnings": []
        }
        
        # 生成警告
        if margin_level < 250:
            report["warnings"].append(f"[WARNING] 保证金水平偏低：{margin_level:.0f}%")
            report["risk_status"] = "warning"
        
        if leverage > 2.5:
            report["warnings"].append(f"[WARNING] 杠杆偏高：{leverage:.1f}x")
            report["risk_status"] = "warning"
        
        if daily_pnl_percent < -self.config['max_daily_loss_percent']:
            report["warnings"].append(f"[WARNING] 日亏损接近上限：{daily_pnl_percent:.2%}")
            report["risk_status"] = "warning"
        
        if margin_level < 200 or leverage > 3.0:
            report["risk_status"] = "danger"
        
        return report


def main():
    """测试函数"""
    # 初始化 MT5
    if not mt5.initialize():
        print("MT5 初始化失败")
        return
    
    # 创建风控 Agent
    agent = RiskAgent()
    
    # 获取账户信息
    account_info = mt5.account_info()
    if account_info is None:
        print("获取账户信息失败")
        return
    
    account_dict = {
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin_level": account_info.margin_level,
        "leverage": account_info.leverage,
        "daily_profit": 0  # 简化
    }
    
    # 获取持仓
    positions = mt5.positions_get()
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
    
    # 生成风控报告
    report = agent.get_risk_report(account_dict, position_list)
    
    print("=" * 80)
    print("Risk Agent - 风控报告")
    print("=" * 80)
    print(f"保证金水平：{report['margin_level']:.0f}%")
    print(f"实际杠杆：{report['leverage']:.1f}x")
    print(f"持仓数量：{report['positions_count']}")
    print(f"总风险：${report['total_risk']:.2f}")
    print(f"风险状态：{report['risk_status']}")
    
    if report['warnings']:
        print("\n警告:")
        for warning in report['warnings']:
            print(f"  {warning}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
