"""
V4.3 实时监控仪表板
版本：1.0
创建：2026-04-10

功能：
1. 显示最新扫描结果
2. 显示今日交易统计
3. 显示账户状态
4. 实时更新（每 5 秒）
"""

import json
import os
from pathlib import Path
from datetime import datetime
import time


class MonitorDashboard:
    """监控仪表板"""
    
    def __init__(self, log_dir: str = "paper_trading_logs"):
        self.log_dir = Path(log_dir)
        
    def get_latest_scan(self) -> dict:
        """获取最新扫描结果"""
        if not self.log_dir.exists():
            return None
        
        # 获取所有扫描文件
        scan_files = list(self.log_dir.glob("scan_*.json"))
        if not scan_files:
            return None
        
        # 按文件名排序（最新的在前）
        scan_files.sort(reverse=True)
        
        # 读取最新文件
        with open(scan_files[0], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_trades(self) -> list:
        """获取所有交易记录"""
        all_signals_path = self.log_dir / "all_signals.json"
        if not all_signals_path.exists():
            return []
        
        with open(all_signals_path, 'r', encoding='utf-8') as f:
            all_scans = json.load(f)
        
        trades = []
        for scan in all_scans:
            for signal in scan.get('signals', []):
                if signal.get('trade_executed'):
                    trades.append({
                        "timestamp": scan.get('timestamp', ''),
                        "symbol": signal.get('symbol', ''),
                        "signal": signal.get('signal', ''),
                        "score": signal.get('score', 0),
                        "volume": signal.get('suggested_volume', 0)
                    })
        
        return trades
    
    def display(self):
        """显示仪表板"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 80)
        print("V4.3 实时监控仪表板")
        print("=" * 80)
        print(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 最新扫描
        latest = self.get_latest_scan()
        if latest:
            print(f"最新扫描：#{latest.get('scan_id', 0)} - {latest.get('timestamp', '')[:19]}")
            print(f"账户余额：${latest.get('account', {}).get('balance', 0):.2f}")
            print(f"账户净值：${latest.get('account', {}).get('equity', 0):.2f}")
            print()
            
            # 信号统计
            signals = latest.get('signals', [])
            strong_signals = [s for s in signals if s.get('is_strong')]
            
            print(f"扫描品种：{len(signals)}")
            print(f"达标信号：{len(strong_signals)}")
            print()
            
            # 显示所有信号
            print("信号详情:")
            print("-" * 80)
            print(f"{'品种':<10} {'评分':<8} {'信号':<12} {'强度':<10} {'状态':<10}")
            print("-" * 80)
            
            for signal in signals:
                symbol = signal.get('symbol', '')
                score = signal.get('score', 0)
                sig = signal.get('signal', '')
                strength = signal.get('signal_strength', 0)
                is_strong = signal.get('is_strong', False)
                
                status = "达标" if is_strong else "-"
                if signal.get('trade_executed'):
                    status = "已执行"
                
                sig_icon = "→" if "BUY" in sig else "↓" if "SELL" in sig else "→"
                
                print(f"{symbol:<10} {score:<8.1f} {sig_icon:<4}{sig:<8} {strength*100:<10.3f}% {status:<10}")
            
            print()
        
        # 今日交易
        trades = self.get_all_trades()
        if trades:
            print(f"今日交易：{len(trades)} 笔")
            print("-" * 80)
            print(f"{'时间':<18} {'品种':<10} {'方向':<8} {'评分':<8} {'手数':<8}")
            print("-" * 80)
            
            for trade in trades[-10:]:  # 最近 10 笔
                timestamp = trade.get('timestamp', '')[:16]
                symbol = trade.get('symbol', '')
                sig = trade.get('signal', '')
                score = trade.get('score', 0)
                volume = trade.get('volume', 0)
                
                direction = "BUY" if "BUY" in sig else "SELL"
                
                print(f"{timestamp:<18} {symbol:<10} {direction:<8} {score:<8.1f} {volume:<8.2f}")
        
        print()
        print("=" * 80)
        print("按 Ctrl+C 退出监控")
        print("=" * 80)


def main():
    """主函数"""
    dashboard = MonitorDashboard()
    
    print("启动监控仪表板...")
    print("刷新频率：每 5 秒")
    print()
    
    try:
        while True:
            dashboard.display()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n监控已退出")


if __name__ == "__main__":
    main()
