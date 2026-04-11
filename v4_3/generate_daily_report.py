"""
每日报告生成脚本
版本：V4.3.0
创建：2026-04-11

功能：
1. 生成每日交易报告
2. 统计核心指标
3. 归因分析
4. 生成 Markdown 格式报告
5. 发送到飞书
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import json

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DailyReportGenerator:
    """每日报告生成器"""
    
    def __init__(self, db_path: str = "trading/paper_trading.db"):
        """
        初始化
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.report_date = datetime.now().strftime('%Y-%m-%d')
    
    def get_daily_trades(self, date: str = None) -> pd.DataFrame:
        """
        获取当日交易记录
        
        Args:
            date: 日期（YYYY-MM-DD 格式）
            
        Returns:
            pd.DataFrame: 交易记录
        """
        if date is None:
            date = self.report_date
        
        if not os.path.exists(self.db_path):
            print(f"[WARN] 数据库不存在：{self.db_path}")
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT * FROM trades 
        WHERE DATE(created_at) = ?
        ORDER BY created_at DESC
        """.format(date)
        
        try:
            df = pd.read_sql_query(query, conn, params=(date,))
        except:
            df = pd.DataFrame()
        
        conn.close()
        
        return df
    
    def calculate_statistics(self, df: pd.DataFrame) -> dict:
        """
        计算统计指标
        
        Args:
            df: 交易记录
            
        Returns:
            dict: 统计指标
        """
        if len(df) == 0:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0
            }
        
        # 计算盈亏
        if 'profit' in df.columns:
            profits = df['profit'].fillna(0)
        else:
            profits = pd.Series([0] * len(df))
        
        total_trades = len(df)
        wins = (profits > 0).sum()
        losses = (profits < 0).sum()
        win_rate = wins / total_trades if total_trades > 0 else 0
        total_pnl = profits.sum()
        
        # 平均盈亏
        win_profits = profits[profits > 0]
        loss_profits = profits[profits < 0]
        
        avg_win = win_profits.mean() if len(win_profits) > 0 else 0
        avg_loss = abs(loss_profits.mean()) if len(loss_profits) > 0 else 0
        
        # 盈亏比
        profit_factor = abs(win_profits.sum() / loss_profits.sum()) if len(loss_profits) > 0 and loss_profits.sum() != 0 else 0
        
        # 最大盈亏
        largest_win = profits.max() if len(profits) > 0 else 0
        largest_loss = profits.min() if len(profits) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'largest_win': largest_win,
            'largest_loss': largest_loss
        }
    
    def symbol_attribution(self, df: pd.DataFrame) -> dict:
        """
        品种归因
        
        Args:
            df: 交易记录
            
        Returns:
            dict: 品种归因结果
        """
        if len(df) == 0 or 'symbol' not in df.columns:
            return {}
        
        attribution = {}
        
        for symbol in df['symbol'].unique():
            symbol_trades = df[df['symbol'] == symbol]
            
            if 'profit' in symbol_trades.columns:
                total_pnl = symbol_trades['profit'].sum()
            else:
                total_pnl = 0
            
            wins = (symbol_trades['profit'] > 0).sum() if 'profit' in symbol_trades.columns else 0
            total = len(symbol_trades)
            
            attribution[symbol] = {
                'count': total,
                'wins': wins,
                'losses': total - wins,
                'win_rate': wins / total if total > 0 else 0,
                'total_pnl': total_pnl
            }
        
        return attribution
    
    def time_attribution(self, df: pd.DataFrame) -> dict:
        """
        时间归因（时段分析）
        
        Args:
            df: 交易记录
            
        Returns:
            dict: 时间归因结果
        """
        if len(df) == 0:
            return {}
        
        attribution = {
            'asian_session': {'count': 0, 'wins': 0, 'pnl': 0},
            'european_session': {'count': 0, 'wins': 0, 'pnl': 0},
            'american_session': {'count': 0, 'wins': 0, 'pnl': 0}
        }
        
        for _, trade in df.iterrows():
            try:
                if 'created_at' in trade:
                    trade_time = pd.to_datetime(trade['created_at'])
                else:
                    continue
                
                hour = trade_time.hour
                
                # 北京时间时段划分
                if 6 <= hour < 15:
                    session = 'asian_session'
                elif 15 <= hour < 24:
                    session = 'european_session'
                else:
                    session = 'american_session'
                
                attribution[session]['count'] += 1
                
                if 'profit' in trade and pd.notna(trade['profit']):
                    if trade['profit'] > 0:
                        attribution[session]['wins'] += 1
                    attribution[session]['pnl'] += trade['profit']
            except:
                continue
        
        return attribution
    
    def generate_report(self, date: str = None) -> str:
        """
        生成每日报告
        
        Args:
            date: 日期（YYYY-MM-DD 格式）
            
        Returns:
            str: Markdown 格式报告
        """
        if date is None:
            date = self.report_date
        
        # 获取交易记录
        df = self.get_daily_trades(date)
        
        # 计算统计指标
        stats = self.calculate_statistics(df)
        
        # 归因分析
        symbol_attr = self.symbol_attribution(df)
        time_attr = self.time_attribution(df)
        
        # 生成报告
        report = []
        report.append("# 每日交易报告")
        report.append(f"**日期**: {date}")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 核心指标
        report.append("## 核心指标")
        report.append("")
        
        if stats['total_trades'] == 0:
            report.append("*当日无交易记录*")
        else:
            report.append(f"- 交易次数：{stats['total_trades']} 单")
            report.append(f"- 盈利：{stats['wins']} 单")
            report.append(f"- 亏损：{stats['losses']} 单")
            report.append(f"- 胜率：{stats['win_rate']*100:.1f}%")
            report.append(f"- 总盈亏：${stats['total_pnl']:.2f}")
            report.append(f"- 平均盈利：${stats['avg_win']:.2f}")
            report.append(f"- 平均亏损：${stats['avg_loss']:.2f}")
            report.append(f"- 盈亏比：{stats['profit_factor']:.2f}")
            report.append(f"- 最大盈利：${stats['largest_win']:.2f}")
            report.append(f"- 最大亏损：${stats['largest_loss']:.2f}")
        
        report.append("")
        
        # 交易明细
        report.append("## 交易明细")
        report.append("")
        
        if len(df) == 0:
            report.append("*无交易记录*")
        else:
            for idx, trade in df.iterrows():
                symbol = trade.get('symbol', 'N/A')
                trade_type = trade.get('type', 'N/A')
                volume = trade.get('volume', 0)
                entry_price = trade.get('entry_price', 0)
                stop_loss = trade.get('stop_loss', 0)
                take_profit = trade.get('take_profit', 0)
                profit = trade.get('profit', 0)
                
                report.append(f"- {symbol} {trade_type} {volume:.2f}手")
                report.append(f"  - 入场价：{entry_price:.5f}")
                report.append(f"  - 止损/止盈：{stop_loss:.5f} / {take_profit:.5f}")
                
                if pd.notna(profit) and profit != 0:
                    profit_icon = "+" if profit > 0 else ""
                    report.append(f"  - 盈亏：{profit_icon}${profit:.2f}")
                
                report.append("")
        
        # 品种归因
        report.append("## 品种归因")
        report.append("")
        
        if len(symbol_attr) == 0:
            report.append("*无数据*")
        else:
            for symbol, data in symbol_attr.items():
                report.append(f"- **{symbol}**: {data['count']}单，盈利{data['wins']}单，胜率{data['win_rate']*100:.1f}%，盈亏${data['total_pnl']:.2f}")
        
        report.append("")
        
        # 时段归因
        report.append("## 时段归因")
        report.append("")
        
        if len(time_attr) == 0:
            report.append("*无数据*")
        else:
            session_names = {
                'asian_session': '亚洲盘 (06:00-15:00)',
                'european_session': '欧洲盘 (15:00-00:00)',
                'american_session': '美洲盘 (20:00-05:00)'
            }
            
            for session_key, data in time_attr.items():
                session_name = session_names.get(session_key, session_key)
                report.append(f"- **{session_name}**: {data['count']}单，盈利{data['wins']}单，盈亏${data['pnl']:.2f}")
        
        report.append("")
        
        # 问题与建议
        report.append("## 问题与建议")
        report.append("")
        
        if stats['total_trades'] == 0:
            report.append("[OK] 当日无交易，维持观望")
        else:
            # 胜率分析
            if stats['win_rate'] < 0.5:
                report.append("[WARN] **胜率偏低** (<50%)")
                report.append("   - 可能原因：信号质量不足，入场时机不佳")
                report.append("   - 改进建议：提高信号强度门槛，优化入场条件")
                report.append("")
            
            # 盈亏比分析
            if stats['profit_factor'] < 1.5 and stats['profit_factor'] > 0:
                report.append("[WARN] **盈亏比不足** (<1.5)")
                report.append("   - 可能原因：止盈过早，止损过宽")
                report.append("   - 改进建议：启用移动止损，优化止盈策略")
                report.append("")
            
            # 交易次数分析
            if stats['total_trades'] > 10:
                report.append("[WARN] **交易过度** (>10 单)")
                report.append("   - 可能原因：信号门槛过低，过度交易")
                report.append("   - 改进建议：提高信号强度要求，减少交易频率")
                report.append("")
        
        report.append("")
        
        # 明日计划
        report.append("## 明日计划")
        report.append("")
        report.append("1. 继续执行 V4.3 策略")
        report.append("2. 关注市场状态变化")
        report.append("3. 严格执行风控规则")
        report.append("4. 优化参数（如有必要）")
        report.append("")
        
        # 附录
        report.append("---")
        report.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report.append("*V4.3 Review Agent - 数据驱动，持续进化*")
        
        return "\n".join(report)
    
    def save_report(self, report: str, output_dir: str = "logs/reports"):
        """
        保存报告到文件
        
        Args:
            report: 报告内容
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"daily_report_{self.report_date}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[OK] 报告已保存：{filepath}")
        return filepath
    
    def send_to_feishu(self, report: str, webhook_url: str = None):
        """
        发送到飞书
        
        Args:
            report: 报告内容
            webhook_url: 飞书 webhook URL
        """
        if webhook_url is None:
            # 从配置文件读取
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       'config', 'paper_trading_config.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    webhook_url = config.get('monitoring', {}).get('feishu_webhook')
            except:
                webhook_url = None
        
        if webhook_url is None:
            print("[WARN] 飞书 webhook 未配置，跳过发送")
            return
        
        # TODO: 实现飞书发送
        print("[INFO] 飞书报告已发送（模拟）")


def main():
    """主函数"""
    print("="*80)
    print("V4.3 每日报告生成")
    print("="*80)
    print(f"报告日期：{datetime.now().strftime('%Y-%m-%d')}")
    
    generator = DailyReportGenerator()
    
    # 生成报告
    report = generator.generate_report()
    
    print("\n" + "="*80)
    print("每日交易报告")
    print("="*80)
    print(report)
    
    # 保存报告
    generator.save_report(report)
    
    # 发送到飞书
    generator.send_to_feishu(report)


if __name__ == "__main__":
    main()
