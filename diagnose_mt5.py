import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))

print('=== MT5 调用频率诊断 ===')
print()

# 统计 today 的 history_deals_get 调用次数
# 通过计算 deal 总数变化来推断调用频率
mt5.initialize(login=52797683, server='ICMarketsSC-Demo', timeout=10000)

# 检查 cron job 调用模式
print('【Cron Jobs】')
print('  自动巡查: */30 10-23 * * 1-5 (工作日每30分钟)')
print('  上次运行: 2026-05-10 08:30 (约27万ms)')
print()

# 统计历史交易记录
now = datetime.now(tz)
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

# 计算过去24小时内的新成交
deals_24h = mt5.history_deals_get(int((now.timestamp() - 86400)), int(now.timestamp()))
deals_today = [d for d in deals_24h if d.time >= int(today_start.timestamp())]
deals_open = [d for d in deals_today if d.entry in (0,1)]

print('【过去24小时】')
print('  总成交: {}笔'.format(len(deals_24h)))
print('  今日成交: {}笔'.format(len(deals_today)))
print('  今日开仓: {}笔'.format(len(deals_open)))
print()

# 检查 patrol.py 的 MT5 调用次数（模拟一次巡查）
print('【patrol.py 单次巡查 MT5 调用统计】')
print('  初始化: 1x mt5.initialize()')
print('  账户信息: 1x mt5.account_info()')
print('  持仓查询: 1x mt5.positions_get()')
print('  候选符号 tick: ~22x mt5.symbol_info_tick()')
print('  每个候选通过Kelly的: ~3x mt5.copy_rates_from_pos() (D1+H4+H1)')
print('  假设10个通过Kelly过滤: 10x3=30x copy_rates')
print('  手动检查相关持仓: ~5x mt5.symbol_info_tick()')
print('  ===================')
print('  单次巡查合计: ~60次 MT5 API 调用')
print()

# 计算每天最大调用量
print('【每日最大调用量估算】')
workday_scans = 26  # 10:00-23:00, 每30分钟
calls_per_scan = 60
heartbeat_per_day = 8  # 每2小时一次
manual_calls = 5  # 每次我手动查询

total_daily = (workday_scans * calls_per_scan) + (heartbeat_per_day * 5) + manual_calls
print('  工作日: {}次巡查 x {}调用 = {}'.format(workday_scans, calls_per_scan, workday_scans*calls_per_scan))
print('  Heartbeat: {}次 x ~5调用 = {}'.format(heartbeat_per_day, heartbeat_per_day*5))
print('  手动查询: ~{}次 x ~8调用'.format(manual_calls, manual_calls*8))
print('  每日总计: ~{}次 MT5 API 调用'.format(total_daily))
print()

# 诊断：是否过度调用
print('【诊断结论】')
if total_daily > 2000:
    print('  ⚠️ 调用过度 (每天{}次)'.format(total_daily))
else:
    print('  ✅ 调用正常 (每天{}次)'.format(total_daily))

print()
print('【实际观察】')
print('  系统运行: 24小时不间断（cron heartbeat常驻）')
print('  巡查频率: 工作日每30分钟')
print('  MT5连接: 每次patrol都是完整初始化+查询')
print()
print('  问题: patrol.py 每次运行都完整初始化MT5连接')
print('  优化: 可以在cron层面加调用间隔，或减少heartbeat的MT5查询')
print()

# 当前连接状态
info = mt5.account_info()
print('【当前连接状态】')
print('  MT5连接: OK')
print('  账户: #52797683')
print('  余额: ${:.2f}'.format(float(info.balance)))
print('  净值: ${:.2f}'.format(float(info.equity)))

mt5.shutdown()
print()
print('建议：heartbeat中减少MT5查询，只有patrol才连MT5。')