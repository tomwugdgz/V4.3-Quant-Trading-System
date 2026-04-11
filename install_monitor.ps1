# 自动监控系统安装脚本
# 创建 Windows 定时任务，每 15 分钟运行一次

$taskName = "MT5-AutoMonitor"
$taskPath = "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\auto_monitor.py"
$pythonPath = "py"
$logPath = "C:\Users\DELL\.openclaw-autoclaw\workspace\trading\monitor_output.log"

# 检查任务是否已存在
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "删除已存在的任务..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# 创建触发器（每 15 分钟）
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15)

# 创建操作
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-3 `"$taskPath`"" -WorkingDirectory "C:\Users\DELL\.openclaw-autoclaw\workspace\trading"

# 创建设置
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 创建任务
Write-Host "创建定时任务：$taskName" -ForegroundColor Cyan
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Description "MT5 自动监控系统 - 每 15 分钟扫描市场并自动平仓"

Write-Host "`n安装完成！" -ForegroundColor Green
Write-Host "任务名称：$taskName"
Write-Host "运行频率：每 15 分钟"
Write-Host "日志文件：$logPath"
Write-Host "`n查看任务状态：Get-ScheduledTask -TaskName $taskName"
Write-Host "手动运行任务：Start-ScheduledTask -TaskName $taskName"
Write-Host "删除任务：Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false"
