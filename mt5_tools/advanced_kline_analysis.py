"""
高级 K 线分析工具 - 开仓前必备
包含：K 线形态、支撑/阻力、多重时间框架、技术指标
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class AdvancedKlineAnalyzer:
    """高级 K 线分析器"""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.timeframes = {
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        self.data = {}
    
    def get_kline_data(self, timeframe='H1', bars=200):
        """获取 K 线数据"""
        tf = self.timeframes.get(timeframe, mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, bars)
        
        if rates is None or len(rates) == 0:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        self.data[timeframe] = df
        return df
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        # 均线系统
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        df['MA200'] = df['close'].rolling(window=200).mean()
        
        # EMA
        df['EMA12'] = df['close'].ewm(span=12).mean()
        df['EMA26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        df['BB_Std'] = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
        
        # ATR (波动率)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        return df
    
    def identify_support_resistance(self, df, lookback=50):
        """识别支撑位和阻力位"""
        # 寻找局部高点和低点
        highs = df['high'].rolling(window=lookback, center=True).max()
        lows = df['low'].rolling(window=lookback, center=True).min()
        
        # 阻力位 (局部高点)
        resistance_levels = []
        for i in range(len(df)):
            if df['high'].iloc[i] == highs.iloc[i] and not pd.isna(highs.iloc[i]):
                resistance_levels.append(df['high'].iloc[i])
        
        # 支撑位 (局部低点)
        support_levels = []
        for i in range(len(df)):
            if df['low'].iloc[i] == lows.iloc[i] and not pd.isna(lows.iloc[i]):
                support_levels.append(df['low'].iloc[i])
        
        # 去重并排序
        resistance_levels = sorted(list(set([round(x, 5) for x in resistance_levels[-10:]])))
        support_levels = sorted(list(set([round(x, 5) for x in support_levels[-10:]])))
        
        return support_levels, resistance_levels
    
    def detect_kline_pattern(self, df):
        """检测 K 线形态"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        patterns = []
        
        # 计算实体和影线
        body = latest['close'] - latest['open']
        body_size = abs(body)
        upper_shadow = latest['high'] - max(latest['open'], latest['close'])
        lower_shadow = min(latest['open'], latest['close']) - latest['low']
        total_range = latest['high'] - latest['low']
        
        # 十字星
        if body_size < total_range * 0.1:
            patterns.append("十字星 (Doji) - 市场犹豫")
        
        # 大阳线
        if body > 0 and body_size > total_range * 0.7:
            patterns.append("大阳线 - 强势上涨")
        
        # 大阴线
        if body < 0 and body_size > total_range * 0.7:
            patterns.append("大阴线 - 强势下跌")
        
        # 锤子线
        if lower_shadow > body_size * 2 and upper_shadow < body_size * 0.5:
            patterns.append("锤子线 - 可能反转上涨")
        
        # 上吊线
        if upper_shadow > body_size * 2 and lower_shadow < body_size * 0.5:
            patterns.append("上吊线 - 可能反转下跌")
        
        # 吞没形态
        if prev['close'] < prev['open'] and latest['close'] > latest['open']:
            if latest['open'] < prev['close'] and latest['close'] > prev['open']:
                patterns.append(" bullish 吞没 - 强烈上涨信号")
        
        if prev['close'] > prev['open'] and latest['close'] < latest['open']:
            if latest['open'] > prev['close'] and latest['close'] < prev['open']:
                patterns.append("bearish 吞没 - 强烈下跌信号")
        
        return patterns if patterns else ["无明显形态"]
    
    def multi_timeframe_analysis(self):
        """多重时间框架分析"""
        results = {}
        
        for tf in ['M15', 'H1', 'H4', 'D1']:
            df = self.get_kline_data(tf, 200)
            if df is None:
                continue
            
            df = self.calculate_indicators(df)
            latest = df.iloc[-1]
            
            # 趋势判断
            if latest['close'] > latest['MA50'] > latest['MA200']:
                trend = "上升 [OK]"
            elif latest['close'] < latest['MA50'] < latest['MA200']:
                trend = "下降 [NO]"
            else:
                trend = "横盘 [WAIT]"
            
            # RSI 状态
            if latest['RSI'] > 70:
                rsi_status = "超买"
            elif latest['RSI'] < 30:
                rsi_status = "超卖"
            else:
                rsi_status = "中性"
            
            results[tf] = {
                'price': latest['close'],
                'trend': trend,
                'rsi': f"{latest['RSI']:.2f} ({rsi_status})",
                'macd': latest['MACD_Hist'],
                'atr': latest['ATR']
            }
        
        return results
    
    def generate_trading_signal(self):
        """生成交易信号"""
        # 使用 H1 和 H4 为主要参考
        h1_data = self.data.get('H1')
        h4_data = self.data.get('H4')
        
        if h1_data is None or h4_data is None:
            return "观望", 0, "数据不足"
        
        h1 = h1_data.iloc[-1]
        h4 = h4_data.iloc[-1]
        
        score = 0
        reasons = []
        
        # H4 趋势 (权重 40%)
        if h4['close'] > h4['MA50'] > h4['MA200']:
            score += 40
            reasons.append("H4 上升趋势")
        elif h4['close'] < h4['MA50'] < h4['MA200']:
            score -= 40
            reasons.append("H4 下降趋势")
        else:
            reasons.append("H4 横盘")
        
        # H1 趋势 (权重 30%)
        if h1['close'] > h1['MA50']:
            score += 20
            reasons.append("H1 价格在 MA50 上方")
        else:
            score -= 20
            reasons.append("H1 价格在 MA50 下方")
        
        # RSI (权重 20%)
        if 40 < h1['RSI'] < 60:
            score += 10
            reasons.append("RSI 中性")
        elif h1['RSI'] < 30:
            score += 20
            reasons.append("RSI 超卖 (可能反弹)")
        elif h1['RSI'] > 70:
            score -= 20
            reasons.append("RSI 超买 (可能回调)")
        
        # MACD (权重 10%)
        if h1['MACD_Hist'] > 0:
            score += 10
            reasons.append("MACD 看涨")
        else:
            score -= 10
            reasons.append("MACD 看跌")
        
        # 生成信号
        if score >= 60:
            signal = "BUY"
        elif score <= -60:
            signal = "SELL"
        else:
            signal = "观望"
        
        return signal, score, " | ".join(reasons)
    
    def full_analysis(self):
        """完整分析报告"""
        print("=" * 80)
        print(f"{self.symbol} 完整分析报告")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 1. 多重时间框架分析
        print("\n【1. 多重时间框架分析】")
        print("-" * 80)
        mtf = self.multi_timeframe_analysis()
        for tf, data in mtf.items():
            print(f"{tf}: 价格={data['price']:.5f} | 趋势={data['trend']} | RSI={data['rsi']} | ATR={data['atr']:.5f}")
        
        # 2. K 线形态
        print("\n【2. K 线形态检测】")
        print("-" * 80)
        h1_data = self.data.get('H1')
        if h1_data is not None:
            patterns = self.detect_kline_pattern(h1_data)
            for p in patterns:
                print(f"  - {p}")
        
        # 3. 支撑/阻力位
        print("\n【3. 支撑位 & 阻力位】")
        print("-" * 80)
        if h1_data is not None:
            supports, resistances = self.identify_support_resistance(h1_data)
            print(f"阻力位：{resistances[-3:] if len(resistances) >= 3 else resistances}")
            print(f"支撑位：{supports[-3:] if len(supports) >= 3 else supports}")
        
        # 4. 交易信号
        print("\n【4. 交易信号】")
        print("-" * 80)
        signal, score, reasons = self.generate_trading_signal()
        print(f"信号：{signal}")
        print(f"评分：{score}/100")
        print(f"理由：{reasons}")
        
        # 5. 建议止损止盈
        print("\n【5. 建议止损止盈】")
        print("-" * 80)
        if h1_data is not None:
            latest = h1_data.iloc[-1]
            atr = latest['ATR']
            price = latest['close']
            
            if signal == "BUY":
                sl = price - (atr * 2)
                tp1 = price + (atr * 1)
                tp2 = price + (atr * 2)
                tp3 = price + (atr * 3)
                print(f"入场价：{price:.5f}")
                print(f"止损：{sl:.5f} (-{atr*2:.5f}, 约{-((price-sl)/price)*100:.2f}%)")
                print(f"止盈 1：{tp1:.5f} (+{atr*1:.5f})")
                print(f"止盈 2：{tp2:.5f} (+{atr*2:.5f})")
                print(f"止盈 3：{tp3:.5f} (+{atr*3:.5f})")
            elif signal == "SELL":
                sl = price + (atr * 2)
                tp1 = price - (atr * 1)
                tp2 = price - (atr * 2)
                tp3 = price - (atr * 3)
                print(f"入场价：{price:.5f}")
                print(f"止损：{sl:.5f} (+{atr*2:.5f}, 约{((sl-price)/price)*100:.2f}%)")
                print(f"止盈 1：{tp1:.5f} (-{atr*1:.5f})")
                print(f"止盈 2：{tp2:.5f} (-{atr*2:.5f})")
                print(f"止盈 3：{tp3:.5f} (-{atr*3:.5f})")
            else:
                print("观望中，无建议")
        
        print("\n" + "=" * 80)
        
        return {
            'signal': signal,
            'score': score,
            'reasons': reasons
        }

# 主程序
if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 初始化失败")
        exit()
    
    # 分析所有主要品种
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"]
    
    for symbol in symbols:
        analyzer = AdvancedKlineAnalyzer(symbol)
        result = analyzer.full_analysis()
        
        # 只显示有交易信号的
        if result['signal'] in ['BUY', 'SELL']:
            print(f"\n🎯 {symbol} 信号：{result['signal']} (评分：{result['score']})\n")
    
    mt5.shutdown()
