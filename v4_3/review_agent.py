"""
Review Agent - 自动复盘 Agent
版本：V4.3.0
创建：2026-04-10

功能：
1. 交易归因分析
2. 每日复盘报告
3. 问题识别与改进建议
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class ReviewAgent:
    """自动复盘 Agent"""
    
    def __init__(self, db_path: str = "trading.db"):
        """
        初始化
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        
    def get_trade_history(self, days: int = 30) -> pd.DataFrame:
        """获取交易历史"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT * FROM orders 
        WHERE created_at >= datetime('now', '-{} days')
        ORDER BY created_at DESC
        """.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def attribution_analysis(self, days: int = 30) -> Dict:
        """
        归因分析
        
        Args:
            days: 回看天数
            
        Returns:
            Dict: 归因分析结果
        """
        trades = self.get_trade_history(days)
        
        if len(trades) == 0:
            return {"message": "无交易记录"}
        
        # 1. 策略归因（简化：按品种分组）
        strategy_attribution = self._strategy_attribution(trades)
        
        # 2. 品种归因
        symbol_attribution = self._symbol_attribution(trades)
        
        # 3. 时间归因
        time_attribution = self._time_attribution(trades)
        
        # 4. 因子归因（需要因子数据，暂略）
        factor_attribution = {"message": "需要因子数据支持"}
        
        return {
            "period": f"{days} days",
            "total_trades": len(trades),
            "strategy_attribution": strategy_attribution,
            "symbol_attribution": symbol_attribution,
            "time_attribution": time_attribution,
            "factor_attribution": factor_attribution
        }
    
    def _strategy_attribution(self, trades: pd.DataFrame) -> Dict:
        """策略归因"""
        # 简化：按订单类型分组
        attribution = {}
        
        for order_type in trades['type'].unique():
            type_trades = trades[trades['type'] == order_type]
            total_profit = type_trades['profit'].sum() if 'profit' in type_trades.columns else 0
            count = len(type_trades)
            
            attribution[order_type] = {
                "count": count,
                "total_profit": total_profit,
                "avg_profit": total_profit / count if count > 0 else 0
            }
        
        return attribution
    
    def _symbol_attribution(self, trades: pd.DataFrame) -> Dict:
        """品种归因"""
        attribution = {}
        
        for symbol in trades['symbol'].unique():
            symbol_trades = trades[trades['symbol'] == symbol]
            total_profit = symbol_trades['profit'].sum() if 'profit' in symbol_trades.columns else 0
            count = len(symbol_trades)
            
            attribution[symbol] = {
                "count": count,
                "total_profit": total_profit,
                "avg_profit": total_profit / count if count > 0 else 0
            }
        
        return attribution
    
    def _time_attribution(self, trades: pd.DataFrame) -> Dict:
        """时间归因"""
        attribution = {
            "asian_session": {"count": 0, "profit": 0},
            "european_session": {"count": 0, "profit": 0},
            "american_session": {"count": 0, "profit": 0}
        }
        
        for _, trade in trades.iterrows():
            # 解析时间
            try:
                trade_time = pd.to_datetime(trade['created_at'])
                hour = trade_time.hour
                
                # 北京时间时段划分
                if 6 <= hour < 15:
                    session = "asian_session"
                elif 15 <= hour < 24:
                    session = "european_session"
                else:
                    session = "american_session"
                
                attribution[session]["count"] += 1
                if 'profit' in trade and pd.notna(trade['profit']):
                    attribution[session]["profit"] += trade['profit']
            except:
                continue
        
        return attribution
    
    def generate_daily_report(self, date: str = None) -> str:
        """
        生成每日复盘报告
        
        Args:
            date: 日期（YYYY-MM-DD 格式）
            
        Returns:
            str: 复盘报告（Markdown 格式）
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取当日交易
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT * FROM orders 
        WHERE DATE(created_at) = '{}'
        """.format(date)
        
        trades = pd.read_sql_query(query, conn)
        conn.close()
        
        # 生成报告
        report = []
        report.append("# 📊 每日复盘报告")
        report.append(f"**日期**: {date}")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 核心指标
        report.append("## 📈 核心指标")
        report.append("")
        
        if len(trades) == 0:
            report.append("*当日无交易记录*")
        else:
            total_profit = trades['profit'].sum() if 'profit' in trades.columns else 0
            win_trades = trades[trades['profit'] > 0] if 'profit' in trades.columns else []
            loss_trades = trades[trades['profit'] < 0] if 'profit' in trades.columns else []
            
            win_count = len(win_trades)
            loss_count = len(loss_trades)
            win_rate = win_count / len(trades) * 100 if len(trades) > 0 else 0
            
            report.append(f"- 交易次数：{len(trades)} 单")
            report.append(f"- 盈利：{win_count} 单")
            report.append(f"- 亏损：{loss_count} 单")
            report.append(f"- 胜率：{win_rate:.1f}%")
            report.append(f"- 总盈亏：${total_profit:.2f}")
        
        report.append("")
        
        # 交易明细
        report.append("## 📋 交易明细")
        report.append("")
        
        if len(trades) == 0:
            report.append("*无交易记录*")
        else:
            for _, trade in trades.iterrows():
                report.append(f"- {trade['symbol']} {trade['type']} {trade['volume']} 手")
                report.append(f"  - 入场价：{trade['price']}")
                report.append(f"  - 止损/止盈：{trade['sl']} / {trade['tp']}")
                if 'profit' in trade and pd.notna(trade['profit']):
                    profit_icon = "✅" if trade['profit'] > 0 else "❌"
                    report.append(f"  - 盈亏：{profit_icon} ${trade['profit']:.2f}")
                report.append("")
        
        # 问题分析
        report.append("## 🔍 问题分析")
        report.append("")
        
        if len(trades) > 0 and 'profit' in trades.columns:
            # 检查胜率
            if win_rate < 50:
                report.append("⚠️ **胜率偏低** (<50%)")
                report.append("   - 可能原因：信号质量不足，入场时机不佳")
                report.append("   - 改进建议：提高信号强度门槛，优化入场条件")
                report.append("")
            
            # 检查盈亏比
            avg_win = win_trades['profit'].mean() if len(win_trades) > 0 else 0
            avg_loss = abs(loss_trades['profit'].mean()) if len(loss_trades) > 0 else 1
            
            if avg_loss > 0:
                reward_risk_ratio = avg_win / avg_loss
                if reward_risk_ratio < 1.5:
                    report.append("⚠️ **盈亏比不足** (<1.5)")
                    report.append("   - 可能原因：止盈过早，止损过宽")
                    report.append("   - 改进建议：启用移动止损，优化止盈策略")
                    report.append("")
        
        if len(trades) == 0:
            report.append("✅ 当日无交易，维持观望")
            report.append("")
        
        # 明日计划
        report.append("## 📅 明日计划")
        report.append("")
        report.append("1. 继续执行 V4.3 策略")
        report.append("2. 关注市场状态变化")
        report.append("3. 严格执行风控规则")
        report.append("")
        
        report.append("---")
        report.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report.append("*V4.3 Review Agent - 数据驱动，持续进化*")
        
        return "\n".join(report)
    
    def identify_patterns(self, days: int = 30) -> Dict:
        """
        识别交易模式
        
        Args:
            days: 回看天数
            
        Returns:
            Dict: 模式识别结果
        """
        trades = self.get_trade_history(days)
        
        if len(trades) == 0:
            return {"message": "无交易记录"}
        
        patterns = {
            "winning_patterns": [],
            "losing_patterns": [],
            "suggestions": []
        }
        
        # 分析盈利单特征
        if 'profit' in trades.columns:
            win_trades = trades[trades['profit'] > 0]
            loss_trades = trades[trades['profit'] < 0]
            
            # 盈利单的共同特征
            if len(win_trades) > 0:
                # 哪些品种表现好
                best_symbol = win_trades.groupby('symbol')['profit'].sum().idxmax()
                patterns["winning_patterns"].append(f"最佳品种：{best_symbol}")
                
                # 哪个时段表现好
                # （简化：略）
            
            # 亏损单的共同特征
            if len(loss_trades) > 0:
                worst_symbol = loss_trades.groupby('symbol')['profit'].sum().idxmin()
                patterns["losing_patterns"].append(f"最差品种：{worst_symbol}")
        
        # 改进建议
        if len(patterns["winning_patterns"]) > 0:
            patterns["suggestions"].append(f"增加{patterns['winning_patterns'][0].split('：')[1]}的交易频率")
        
        if len(patterns["losing_patterns"]) > 0:
            patterns["suggestions"].append(f"减少或避免{patterns['losing_patterns'][0].split('：')[1]}的交易")
        
        return patterns


def main():
    """测试函数"""
    agent = ReviewAgent()
    
    print("=" * 80)
    print("Review Agent - 自动复盘")
    print("=" * 80)
    
    # 归因分析
    print("\n📊 归因分析（近 30 天）:")
    attribution = agent.attribution_analysis(30)
    print(json.dumps(attribution, indent=2, ensure_ascii=False))
    
    # 每日报告
    print("\n📋 每日复盘报告:")
    report = agent.generate_daily_report()
    print(report)
    
    # 模式识别
    print("\n🔍 交易模式识别:")
    patterns = agent.identify_patterns(30)
    print(json.dumps(patterns, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
