"""
MT5 策略回测系统
基于历史数据测试交易策略的盈利能力
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class Backtester:
    """策略回测器"""
    
    def __init__(self, symbol, initial_balance=10000, risk_per_trade=0.01):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.trades = []
        self.equity_curve = []
    
    def get_historical_data(self, timeframe='H1', bars=1000):
        """获取历史数据"""
        tf_map = {
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, bars)
        
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        # 均线
        df['MA50'] = df['close'].rolling(window=50).mean()
        df['MA200'] = df['close'].rolling(window=200).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        return df
    
    def strategy_ma_crossover(self, df):
        """
        均线交叉策略
        买入：MA50 上穿 MA200
        卖出：MA50 下穿 MA200
        """
        signals = []
        positions = 0
        entry_price = 0
        
        for i in range(1, len(df)):
            prev_ma50 = df['MA50'].iloc[i-1]
            prev_ma200 = df['MA200'].iloc[i-1]
            curr_ma50 = df['MA50'].iloc[i]
            curr_ma200 = df['MA200'].iloc[i]
            price = df['close'].iloc[i]
            
            # 金叉买入
            if prev_ma50 <= prev_ma200 and curr_ma50 > curr_ma200 and positions == 0:
                positions = 1
                entry_price = price
                signals.append(('BUY', i, price))
            
            # 死叉卖出
            elif prev_ma50 >= prev_ma200 and curr_ma50 < curr_ma200 and positions == 1:
                profit = (price - entry_price) * 100000 * 0.17  # 0.17 手
                self.balance += profit
                positions = 0
                signals.append(('SELL', i, price, profit))
                self.trades.append({
                    'entry': entry_price,
                    'exit': price,
                    'profit': profit,
                    'time': df.index[i]
                })
        
        return signals
    
    def strategy_rsi(self, df, oversold=30, overbought=70):
        """
        RSI 策略
        买入：RSI < 30 (超卖)
        卖出：RSI > 70 (超买)
        """
        signals = []
        positions = 0
        entry_price = 0
        
        for i in range(1, len(df)):
            prev_rsi = df['RSI'].iloc[i-1]
            curr_rsi = df['RSI'].iloc[i]
            price = df['close'].iloc[i]
            
            # 超卖买入
            if prev_rsi >= oversold and curr_rsi < oversold and positions == 0:
                positions = 1
                entry_price = price
                signals.append(('BUY', i, price))
            
            # 超买卖出
            elif prev_rsi <= overbought and curr_rsi > overbought and positions == 1:
                profit = (price - entry_price) * 100000 * 0.17
                self.balance += profit
                positions = 0
                signals.append(('SELL', i, price, profit))
                self.trades.append({
                    'entry': entry_price,
                    'exit': price,
                    'profit': profit,
                    'time': df.index[i]
                })
        
        return signals
    
    def strategy_breakout(self, df, lookback=20):
        """
        突破策略
        买入：价格突破 N 周期高点
        卖出：价格跌破 N 周期低点
        """
        signals = []
        positions = 0
        entry_price = 0
        stop_loss = 0
        
        df['high_n'] = df['high'].rolling(window=lookback).max()
        df['low_n'] = df['low'].rolling(window=lookback).min()
        
        for i in range(lookback, len(df)):
            price = df['close'].iloc[i]
            high_n = df['high_n'].iloc[i-1]
            low_n = df['low_n'].iloc[i-1]
            atr = df['ATR'].iloc[i]
            
            # 突破高点买入
            if price > high_n and positions == 0:
                positions = 1
                entry_price = price
                stop_loss = price - (atr * 2)
                signals.append(('BUY', i, price, stop_loss))
            
            # 跌破低点或止损卖出
            elif (price < low_n or price < stop_loss) and positions == 1:
                profit = (price - entry_price) * 100000 * 0.17
                self.balance += profit
                positions = 0
                signals.append(('SELL', i, price, profit))
                self.trades.append({
                    'entry': entry_price,
                    'exit': price,
                    'profit': profit,
                    'time': df.index[i]
                })
        
        return signals
    
    def run_backtest(self, strategy='ma_crossover', timeframe='H1', bars=1000):
        """运行回测"""
        print("=" * 80)
        print(f"{self.symbol} 策略回测报告")
        print(f"策略：{strategy}")
        print(f"时间框架：{timeframe}")
        print(f"初始资金：${self.initial_balance}")
        print("=" * 80)
        
        # 获取数据
        df = self.get_historical_data(timeframe, bars)
        if df is None:
            print("无法获取历史数据")
            return
        
        # 计算指标
        df = self.calculate_indicators(df)
        
        # 运行策略
        if strategy == 'ma_crossover':
            signals = self.strategy_ma_crossover(df)
        elif strategy == 'rsi':
            signals = self.strategy_rsi(df)
        elif strategy == 'breakout':
            signals = self.strategy_breakout(df)
        else:
            print(f"未知策略：{strategy}")
            return
        
        # 计算统计
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t['profit'] > 0)
        losing_trades = sum(1 for t in self.trades if t['profit'] <= 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = sum(t['profit'] for t in self.trades)
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        max_profit = max((t['profit'] for t in self.trades), default=0)
        max_loss = min((t['profit'] for t in self.trades), default=0)
        
        # 计算最大回撤
        peak = self.initial_balance
        max_drawdown = 0
        for trade in self.trades:
            peak = max(peak, self.initial_balance + sum(t['profit'] for t in self.trades[:self.trades.index(trade)+1]))
            drawdown = peak - (self.initial_balance + sum(t['profit'] for t in self.trades[:self.trades.index(trade)+1]))
            max_drawdown = max(max_drawdown, drawdown)
        
        # 打印报告
        print(f"\n【回测结果】")
        print(f"总交易次数：{total_trades}")
        print(f"盈利交易：{winning_trades} ({win_rate:.1f}%)")
        print(f"亏损交易：{losing_trades}")
        print(f"总盈亏：${total_profit:.2f}")
        print(f"平均盈亏：${avg_profit:.2f}/单")
        print(f"最大单笔盈利：${max_profit:.2f}")
        print(f"最大单笔亏损：${max_loss:.2f}")
        print(f"最大回撤：${max_drawdown:.2f}")
        print(f"最终余额：${self.balance:.2f}")
        print(f"总收益率：{((self.balance - self.initial_balance) / self.initial_balance * 100):.2f}%")
        
        # 绘制权益曲线
        self.plot_equity_curve(df)
        
        print("\n" + "=" * 80)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'final_balance': self.balance,
            'max_drawdown': max_drawdown
        }
    
    def plot_equity_curve(self, df):
        """绘制权益曲线"""
        try:
            # 计算累计盈亏
            cumulative = [self.initial_balance]
            for trade in self.trades:
                cumulative.append(cumulative[-1] + trade['profit'])
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # 价格曲线
            ax1.plot(df.index, df['close'], label='Price', linewidth=1)
            ax1.set_title(f'{self.symbol} Price Chart')
            ax1.set_ylabel('Price')
            ax1.grid(True)
            
            # 权益曲线
            ax2.plot(range(len(cumulative)), cumulative, label='Equity', color='green', linewidth=2)
            ax2.axhline(y=self.initial_balance, color='gray', linestyle='--', label='Initial Balance')
            ax2.set_title('Equity Curve')
            ax2.set_ylabel('Balance ($)')
            ax2.set_xlabel('Trade Number')
            ax2.grid(True)
            ax2.legend()
            
            plt.tight_layout()
            
            # 保存图片
            filename = f"backtest_{self.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(f"C:\\Users\\DELL\\.openclaw-autoclaw\\workspace\\trading\\backtest_results\\{filename}")
            print(f"\n图表已保存：{filename}")
            
        except Exception as e:
            print(f"无法绘制图表：{e}")

# 主程序
if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 初始化失败")
        exit()
    
    # 回测多个品种
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF"]
    strategies = ['ma_crossover', 'rsi', 'breakout']
    
    results = []
    
    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"回测品种：{symbol}")
        print(f"{'='*80}\n")
        
        for strategy in strategies:
            backtester = Backtester(symbol, initial_balance=10000, risk_per_trade=0.01)
            result = backtester.run_backtest(strategy=strategy, timeframe='H1', bars=1000)
            
            if result:
                results.append({
                    'symbol': symbol,
                    'strategy': strategy,
                    **result
                })
    
    # 汇总最佳策略
    print("\n" + "=" * 80)
    print("最佳策略汇总")
    print("=" * 80)
    
    if results:
        best = max(results, key=lambda x: x['total_profit'])
        print(f"\n最佳策略：{best['symbol']} - {best['strategy']}")
        print(f"总盈利：${best['total_profit']:.2f}")
        print(f"胜率：{best['win_rate']:.1f}%")
        print(f"收益率：{((best['final_balance'] - 10000) / 10000 * 100):.2f}%")
    
    mt5.shutdown()
