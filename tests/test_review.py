"""
Review Agent 测试
版本：V4.3.0
创建：2026-04-11
"""

import pytest
import sqlite3
import pandas as pd
from datetime import datetime, timedelta


class TestReviewAgent:
    """Review Agent 测试"""
    
    def test_get_trade_history(self, review_agent):
        """测试获取交易历史"""
        # 创建测试数据
        conn = sqlite3.connect(review_agent.db_path)
        
        test_data = [
            ('EURUSD', 'BUY', 0.1, 1.1000, 1.0950, 1.1100, 100.0, datetime.now()),
            ('GBPUSD', 'SELL', 0.2, 1.3000, 1.3050, 1.2900, -50.0, datetime.now() - timedelta(days=1)),
            ('USDJPY', 'BUY', 0.15, 110.00, 109.50, 111.00, 150.0, datetime.now() - timedelta(days=2)),
        ]
        
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                type TEXT,
                volume REAL,
                price REAL,
                sl REAL,
                tp REAL,
                profit REAL,
                created_at DATETIME
            )
        ''')
        
        cursor.executemany(
            'INSERT INTO orders (symbol, type, volume, price, sl, tp, profit, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            test_data
        )
        
        conn.commit()
        conn.close()
        
        # 测试获取
        df = review_agent.get_trade_history(days=30)
        
        assert len(df) == 3
        assert 'symbol' in df.columns
        assert 'profit' in df.columns
    
    def test_attribution_analysis_no_data(self, review_agent):
        """测试无数据时的归因分析"""
        result = review_agent.attribution_analysis(days=30)
        
        assert isinstance(result, dict)
        assert 'message' in result or 'total_trades' in result
    
    def test_strategy_attribution(self, review_agent):
        """测试策略归因"""
        # 创建测试数据
        conn = sqlite3.connect(review_agent.db_path)
        
        test_data = [
            ('EURUSD', 'BUY', 0.1, 1.1000, 1.0950, 1.1100, 100.0, datetime.now()),
            ('GBPUSD', 'BUY', 0.2, 1.3000, 1.3050, 1.2900, 50.0, datetime.now()),
        ]
        
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                type TEXT,
                volume REAL,
                price REAL,
                sl REAL,
                tp REAL,
                profit REAL,
                created_at DATETIME
            )
        ''')
        
        cursor.executemany(
            'INSERT INTO orders (symbol, type, volume, price, sl, tp, profit, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            test_data
        )
        
        conn.commit()
        conn.close()
        
        # 测试归因
        result = review_agent.attribution_analysis(days=30)
        
        assert 'strategy_attribution' in result
        assert 'symbol_attribution' in result
        assert 'time_attribution' in result
    
    def test_generate_daily_report_no_data(self, review_agent):
        """测试生成每日报告（无数据）"""
        report = review_agent.generate_daily_report()
        
        assert isinstance(report, str)
        assert '每日复盘报告' in report
        assert '无交易记录' in report or '当日无交易' in report
    
    def test_identify_patterns(self, review_agent):
        """测试模式识别"""
        result = review_agent.identify_patterns(days=30)
        
        assert isinstance(result, dict)
        assert 'winning_patterns' in result or 'message' in result
        assert 'losing_patterns' in result or 'message' in result
        assert 'suggestions' in result or 'message' in result
