#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多算法并行 PK 测试框架
Algorithm PK Testing Framework

功能:
- 同时运行 6 个趋势算法
- 每个算法独立虚拟账户
- 自动记录交易数据
- 实时计算 KPI
- 生成对比报告
"""

import json
import datetime
import os
from typing import Dict, List, Tuple

# 算法配置
ALGORITHMS = {
    "TF-01": {
        "name": "SMA 交叉",
        "type": "trend",
        "params": {
            "fast_period": 20,
            "slow_period": 50,
            "signal_threshold": 0.0005,
        }
    },
    "TF-02": {
        "name": "EMA 交叉",
        "type": "trend",
        "params": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_threshold": 0.0005,
        }
    },
    "TF-03": {
        "name": "MACD 趋势",
        "type": "trend",
        "params": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "signal_threshold": 0.0005,
        }
    },
    "TF-04": {
        "name": "ADX 趋势",
        "type": "trend",
        "params": {
            "adx_threshold": 25,
            "di_period": 14,
            "signal_threshold": 0.0005,
        }
    },
    "TF-05": {
        "name": "通道突破",
        "type": "trend",
        "params": {
            "channel_period": 20,
            "signal_threshold": 0.0005,
        }
    },
    "TF-06": {
        "name": "自适应均线",
        "type": "trend",
        "params": {
            "ama_fast": 2,
            "ama_slow": 30,
            "signal_threshold": 0.0005,
        }
    }
}

# 测试配置
TEST_CONFIG = {
    "initial_capital": 10000,  # 每个算法虚拟账户$10,000
    "risk_per_trade": 0.001,   # 0.1% 风险
    "stop_loss_pips": 30,
    "take_profit_pips": 60,
    "test_start": "2026-03-27",
    "test_end": "2026-04-03",
}


class AlgorithmPKTester:
    """多算法 PK 测试器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.algorithms = ALGORITHMS
        self.results = {}
        
        # 初始化每个算法的虚拟账户
        for algo_id in self.algorithms:
            self.results[algo_id] = {
                "name": self.algorithms[algo_id]["name"],
                "capital": config["initial_capital"],
                "trades": [],
                "winning_trades": 0,
                "losing_trades": 0,
                "total_profit": 0,
                "total_loss": 0,
                "max_drawdown": 0,
                "current_drawdown": 0,
                "status": "ACTIVE"
            }
    
    def record_trade(self, algo_id: str, trade: Dict):
        """记录交易"""
        if algo_id not in self.results:
            print(f"[ERROR] 算法 {algo_id} 不存在")
            return
        
        result = self.results[algo_id]
        result["trades"].append(trade)
        
        # 更新统计
        profit = trade.get("profit", 0)
        if profit > 0:
            result["winning_trades"] += 1
            result["total_profit"] += profit
        else:
            result["losing_trades"] += 1
            result["total_loss"] += abs(profit)
        
        # 更新资金
        result["capital"] += profit
        
        # 更新回撤
        result["current_drawdown"] = max(0, result["current_drawdown"] - profit)
        result["max_drawdown"] = max(result["max_drawdown"], result["current_drawdown"])
        
        print(f"[OK] {algo_id} 记录交易：{trade.get('symbol', 'N/A')} {trade.get('direction', 'N/A')} 盈亏：${profit:.2f}")
    
    def calculate_kpi(self, algo_id: str) -> Dict:
        """计算 KPI"""
        if algo_id not in self.results:
            return {}
        
        result = self.results[algo_id]
        total_trades = len(result["trades"])
        
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "roi": 0,
                "profit_factor": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "score": 0
            }
        
        win_rate = result["winning_trades"] / total_trades if total_trades > 0 else 0
        roi = (result["capital"] - self.config["initial_capital"]) / self.config["initial_capital"]
        profit_factor = result["total_profit"] / result["total_loss"] if result["total_loss"] > 0 else float('inf')
        max_drawdown = result["max_drawdown"] / self.config["initial_capital"]
        
        # 简化夏普比率 (假设无风险利率 0)
        sharpe_ratio = roi / 0.1 if roi > 0 else 0  # 简化计算
        
        # 综合得分
        score = (
            roi * 25 +
            sharpe_ratio * 20 +
            (1 - max_drawdown) * 15 +
            min(profit_factor, 3) * 10 +
            win_rate * 15 +
            min(total_trades / 20, 1) * 10 +
            5  # 基础分
        )
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "roi": roi,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "score": score
        }
    
    def generate_report(self) -> str:
        """生成 PK 报告"""
        report = []
        report.append("=" * 80)
        report.append("多算法 PK 测试报告")
        report.append("=" * 80)
        report.append(f"测试周期：{self.config['test_start']} 至 {self.config['test_end']}")
        report.append(f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 计算所有算法的 KPI
        kpi_table = []
        for algo_id in self.algorithms:
            kpi = self.calculate_kpi(algo_id)
            kpi_table.append((algo_id, self.algorithms[algo_id]["name"], kpi))
        
        # 按得分排序
        kpi_table.sort(key=lambda x: x[2]["score"], reverse=True)
        
        # 表格
        report.append("┌─────────┬──────────────┬────────┬────────┬─────────┬──────────┬────────┬────────┐")
        report.append("│ 算法编号 │ 算法名称      │ 交易数 │ 胜率   │ ROI     │ 盈利因子 │ 回撤   │ 得分   │")
        report.append("├─────────┼──────────────┼────────┼────────┼─────────┼──────────┼────────┼────────┤")
        
        for algo_id, name, kpi in kpi_table:
            report.append(
                f"│ {algo_id:7} │ {name:12} │ {kpi['total_trades']:6} │ {kpi['win_rate']*100:5.1f}% │ {kpi['roi']*100:7.2f}% │ {kpi['profit_factor']:8.2f} │ {kpi['max_drawdown']*100:5.1f}% │ {kpi['score']:5.1f} │"
            )
        
        report.append("└─────────┴──────────────┴────────┴────────┴─────────┴──────────┴────────┴────────┘")
        report.append("")
        
        # Top 3
        report.append("Top 3 算法:")
        for i, (algo_id, name, kpi) in enumerate(kpi_table[:3], 1):
            report.append(f"  {i}. {algo_id} - {name} (得分：{kpi['score']:.1f}, ROI: {kpi['roi']*100:.2f}%)")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, filepath: str):
        """保存结果到 JSON"""
        data = {
            "test_config": self.config,
            "algorithms": self.algorithms,
            "results": {},
            "kpi": {}
        }
        
        for algo_id in self.algorithms:
            data["results"][algo_id] = self.results[algo_id]
            data["kpi"][algo_id] = self.calculate_kpi(algo_id)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 结果已保存：{filepath}")
    
    def load_results(self, filepath: str):
        """从 JSON 加载结果"""
        if not os.path.exists(filepath):
            print(f"[WARN] 文件不存在：{filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.results = data.get("results", {})
        print(f"[OK] 结果已加载：{filepath}")
        return True


def main():
    """主函数"""
    print("=" * 80)
    print("多算法 PK 测试框架 v1.0")
    print("=" * 80)
    print("")
    
    # 创建测试器
    tester = AlgorithmPKTester(TEST_CONFIG)
    
    # 初始化
    print("初始化算法:")
    for algo_id, algo in ALGORITHMS.items():
        print(f"  - {algo_id}: {algo['name']} ({algo['type']})")
    print("")
    
    print(f"测试配置:")
    print(f"  初始资金：${TEST_CONFIG['initial_capital']}")
    print(f"  单笔风险：{TEST_CONFIG['risk_per_trade']*100}%")
    print(f"  止损：{TEST_CONFIG['stop_loss_pips']} pips")
    print(f"  止盈：{TEST_CONFIG['take_profit_pips']} pips")
    print(f"  测试周期：{TEST_CONFIG['test_start']} 至 {TEST_CONFIG['test_end']}")
    print("")
    
    # 示例：记录模拟交易
    print("示例交易记录:")
    tester.record_trade("TF-01", {
        "date": "2026-03-27",
        "symbol": "EURUSD",
        "direction": "SELL",
        "profit": 50.00
    })
    
    tester.record_trade("TF-02", {
        "date": "2026-03-27",
        "symbol": "GBPUSD",
        "direction": "BUY",
        "profit": -30.00
    })
    
    tester.record_trade("TF-06", {
        "date": "2026-03-27",
        "symbol": "AUDUSD",
        "direction": "SELL",
        "profit": 0.00  # 持仓中
    })
    
    print("")
    
    # 生成报告
    report = tester.generate_report()
    print(report)
    
    # 保存结果
    import sys
    import os
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv[0] else os.getcwd()
    tester.save_results(os.path.join(script_dir, "algo_pk_results.json"))
    
    print("")
    print("[OK] 测试框架已就绪，等待实盘数据...")


if __name__ == "__main__":
    main()
