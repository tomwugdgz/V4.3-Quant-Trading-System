# 旺财交易系统备份脚本
# 功能：打包所有交易相关文件到 zip 文件
# 使用：.\backup_trading_system.ps1

$backupDate = Get-Date -Format "yyyyMMdd_HHmm"
$backupFolder = "C:\Users\DELL\.openclaw-autoclaw\workspace\trading"
$backupDest = "C:\Users\DELL\Desktop\旺财交易系统备份_$backupDate"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  旺财交易系统备份" -ForegroundColor Cyan
Write-Host "  备份时间：$backupDate" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 创建备份目录
if (Test-Path $backupDest) {
    Remove-Item $backupDest -Recurse -Force
}
New-Item -ItemType Directory -Path $backupDest | Out-Null
Write-Host "[1/8] 创建备份目录..." -ForegroundColor Green
Write-Host "      $backupDest" -ForegroundColor Gray

# 复制核心配置文件
Write-Host "[2/8] 复制核心配置文件..." -ForegroundColor Green
$memoryDest = Join-Path $backupDest "memory"
New-Item -ItemType Directory -Path $memoryDest -Force | Out-Null
Copy-Item (Join-Path $backupFolder "memory\*.md") -Destination $memoryDest -Force

# 复制 MT5 工具
Write-Host "[3/8] 复制 MT5 工具..." -ForegroundColor Green
$mt5Dest = Join-Path $backupDest "mt5_tools"
New-Item -ItemType Directory -Path $mt5Dest -Force | Out-Null
Copy-Item (Join-Path $backupFolder "mt5_tools\*") -Destination $mt5Dest -Recurse -Force

# 复制知识库
Write-Host "[4/8] 复制知识库..." -ForegroundColor Green
$kbDest = Join-Path $backupDest "knowledge_base"
Copy-Item (Join-Path $backupFolder "knowledge_base") -Destination $kbDest -Recurse -Force

# 复制策略文件
Write-Host "[5/8] 复制策略和复盘..." -ForegroundColor Green
$strategiesDest = Join-Path $backupDest "strategies"
$reviewsDest = Join-Path $backupDest "reviews"
$journalDest = Join-Path $backupDest "journal"
$lessonsDest = Join-Path $backupDest "lessons"
$statsDest = Join-Path $backupDest "stats"

if (Test-Path (Join-Path $backupFolder "strategies")) {
    New-Item -ItemType Directory -Path $strategiesDest -Force | Out-Null
    Copy-Item (Join-Path $backupFolder "strategies\*") -Destination $strategiesDest -Recurse -Force
}

New-Item -ItemType Directory -Path $reviewsDest -Force | Out-Null
Copy-Item (Join-Path $backupFolder "reviews\*") -Destination $reviewsDest -Recurse -Force

New-Item -ItemType Directory -Path $journalDest -Force | Out-Null
Copy-Item (Join-Path $backupFolder "journal\*") -Destination $journalDest -Recurse -Force

New-Item -ItemType Directory -Path $lessonsDest -Force | Out-Null
if (Test-Path (Join-Path $backupFolder "lessons")) {
    Copy-Item (Join-Path $backupFolder "lessons\*") -Destination $lessonsDest -Recurse -Force
}

New-Item -ItemType Directory -Path $statsDest -Force | Out-Null
if (Test-Path (Join-Path $backupFolder "stats")) {
    Copy-Item (Join-Path $backupFolder "stats\*") -Destination $statsDest -Recurse -Force
}

# 复制 Python 脚本
Write-Host "[6/8] 复制 Python 脚本..." -ForegroundColor Green
$pyFiles = Get-ChildItem -Path $backupFolder -Filter "*.py"
foreach ($file in $pyFiles) {
    Copy-Item $file.FullName -Destination $backupDest -Force
}

# 复制配置文件
Write-Host "[7/8] 复制配置文件..." -ForegroundColor Green
$configFiles = @(".env.trading", "BACKUP_SUMMARY.md", "DEPLOYMENT.md", "README.md")
foreach ($file in $configFiles) {
    $src = Join-Path $backupFolder $file
    if (Test-Path $src) {
        Copy-Item $src -Destination $backupDest -Force
    }
}

# 创建压缩包
Write-Host "[8/8] 创建压缩包..." -ForegroundColor Green
$zipFile = "C:\Users\DELL\Desktop\旺财交易系统备份_$backupDate.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$compression = [System.IO.Compression.CompressionLevel]::Optimal
$includeBaseDir = $false
[System.IO.Compression.ZipFile]::CreateFromDirectory($backupDest, $zipFile, $compression, $includeBaseDir)

# 清理临时文件夹
Remove-Item $backupDest -Recurse -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ 备份完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "备份文件：$zipFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "备份内容:" -ForegroundColor Cyan
Write-Host "  - memory/          交易目标/规则/画像" -ForegroundColor Gray
Write-Host "  - mt5_tools/       MT5 工具脚本" -ForegroundColor Gray
Write-Host "  - knowledge_base/  知识库 (10 个分类)" -ForegroundColor Gray
Write-Host "  - strategies/      交易策略" -ForegroundColor Gray
Write-Host "  - reviews/         复盘记录 (日/周/月)" -ForegroundColor Gray
Write-Host "  - journal/         交易日志" -ForegroundColor Gray
Write-Host "  - lessons/         经验教训" -ForegroundColor Gray
Write-Host "  - stats/           绩效统计" -ForegroundColor Gray
Write-Host "  - *.py             Python 脚本 ($(($pyFiles).Count) 个)" -ForegroundColor Gray
Write-Host "  - config files     配置文件" -ForegroundColor Gray
Write-Host ""
Write-Host "部署说明:" -ForegroundColor Cyan
Write-Host "  1. 解压 zip 文件到新电脑" -ForegroundColor Gray
Write-Host "  2. 阅读 DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "  3. 安装 Python 和依赖" -ForegroundColor Gray
Write-Host "  4. 配置 MT5 和 API keys" -ForegroundColor Gray
Write-Host "  5. 测试连接" -ForegroundColor Gray
Write-Host "  6. 开始交易" -ForegroundColor Gray
Write-Host ""
Write-Host "旺财 🎯 - 数据 > 直觉，风控 > 收益，纪律 > 情绪" -ForegroundColor Magenta
Write-Host ""
