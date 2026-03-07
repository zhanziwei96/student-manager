# 班级管理系统启动脚本
# 默认启动生产环境

param(
    [switch]$Test,
    [switch]$Dev
)

# 设置环境变量
if ($Test) {
    $env:FLASK_ENV = "testing"
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "    班级管理系统 - 测试环境" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
} else {
    $env:FLASK_ENV = "production"
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "    班级管理系统 - 生产环境" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}

Write-Host ""
Write-Host "使用说明:"
Write-Host "  .\start_server.ps1       # 启动生产环境"
Write-Host "  .\start_server.ps1 -Test # 启动测试环境"
Write-Host ""

# 检查 Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Error "找不到 Python，请确保已安装 Python 并添加到 PATH"
    exit 1
}

# 安装依赖
Write-Host "检查依赖..." -ForegroundColor Cyan
& $pythonCmd.Source -m pip install -q flask openpyxl

# 启动服务
Write-Host "启动服务..." -ForegroundColor Cyan
Write-Host ""
& $pythonCmd.Source app.py
