# TradingAgents 下载与安装脚本
# 运行前请确保网络正常

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TradingAgents 下载与安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$workspace = "C:\Users\DELL\.openclaw-autoclaw\workspace\trading"
Set-Location $workspace

# 项目列表
$projects = @(
    @{Name="TradingAgents"; URL="https://github.com/TradingAgents/TradingAgents.git"},
    @{Name="FinRobot"; URL="https://github.com/AI4Finance-Foundation/FinRobot.git"},
    @{Name="llm-trading-agents"; URL="https://github.com/ai-trader/llm-trading-agents.git"}
)

foreach ($proj in $projects) {
    Write-Host "`n尝试下载：$($proj.Name)" -ForegroundColor Yellow
    
    if (Test-Path "$workspace\$($proj.Name)") {
        Write-Host "  已存在，跳过" -ForegroundColor Green
        continue
    }
    
    git clone $proj.URL 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  下载成功！" -ForegroundColor Green
    } else {
        Write-Host "  下载失败，继续下一个..." -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "下载完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
