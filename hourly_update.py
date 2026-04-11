# Hourly update script for 24h trading challenge
# Sends position update to Feishu every hour
import MetaTrader5 as mt5
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding='utf-8')

def get_hourly_update():
    if not mt5.initialize():
        return "ERROR: Failed to initialize MT5"
    
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M GMT+8")
    
    # Account info
    account = mt5.account_info()
    positions = mt5.positions_get()
    
    # Build report - use plain ASCII to avoid encoding issues
    report = []
    report.append("=== 小时交易更新 - " + update_time + " ===")
    report.append("")
    
    # Account summary
    report.append("【账户状态】")
    report.append("- 账户ID: %s" % account.login)
    report.append("- 服务器: %s" % account.server)
    report.append("- 余额: $%.2f USD" % account.balance)
    report.append("- 权益: $%.2f USD" % account.equity)
    report.append("- 可用保证金: $%.2f USD" % account.margin_free)
    report.append("")
    
    # Positions
    if positions:
        report.append("【当前持仓】")
        report.append("")
        report.append("品种 | 方向 | 手数 | 入场价 | 当前价 | 止损 | 止盈 | 浮盈")
        report.append("-----|------|------|--------|--------|------|------|------")
        
        total_pl = 0.0
        total_volume = 0.0
        
        for pos in sorted(positions, key=lambda x: x.symbol):
            direction = "BUY" if pos.type == 0 else "SELL"
            pl = pos.profit
            total_pl += pl
            total_volume += pos.volume
            pl_sign = "+" if pl >= 0 else ""
            report.append("%s | %s | %.2f | %.5f | %.5f | %.5f | %.5f | %s$%.2f" % (
                pos.symbol, direction, pos.volume, 
                pos.price_open, pos.price_current, 
                pos.sl, pos.tp, pl_sign, pl
            ))
        
        report.append("")
        report.append("* 总持仓: %d 单 / %.2f 手" % (len(positions), total_volume))
        total_pl_sign = "+" if total_pl >= 0 else ""
        report.append("* 总浮动盈亏: %s$%.2f USD" % (total_pl_sign, total_pl))
        report.append("")
    else:
        report.append("【当前持仓】")
        report.append("")
        report.append("当前无持仓")
        report.append("")
    
    # Calculate performance
    initial_balance = 10000.00
    current_balance = account.balance
    total_profit = current_balance - initial_balance
    pct = (total_profit / initial_balance) * 100
    pct_sign = "+" if total_profit >= 0 else ""
    
    report.append("【累计业绩】(初始 $10,000)")
    report.append("- 总盈利: %s$%.2f USD" % (pct_sign, total_profit))
    report.append("- 收益率: %s%.2f%%" % (pct_sign, pct))
    report.append("")
    
    report.append("----------------------------------------")
    report.append("自动每小时更新，24小时到期后出最终结果")
    
    mt5.shutdown()
    
    return "\n".join(report)

if __name__ == "__main__":
    report = get_hourly_update()
    print(report)
