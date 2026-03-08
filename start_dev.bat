@echo off
chcp 65001
cls
echo ==========================================
echo    班级管理系统 - 开发环境启动脚本
echo ==========================================
echo.

:: 启动后端
echo [1/2] 正在启动后端服务...
start "Flask Backend" cmd /k "cd backend && python app.py"

:: 等待后端启动
timeout /t 3 /nobreak > nul

:: 启动前端
echo [2/2] 正在启动前端服务...
start "Vue Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ==========================================
echo  服务启动中...
echo  后端: http://localhost:5000
echo  前端: http://localhost:3000
echo ==========================================
pause
