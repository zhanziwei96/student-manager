@echo off
chcp 65001 >nul
echo ========================================
echo     班级管理系统 - 生产环境
echo ========================================
echo.
set FLASK_ENV=production
python app.py
pause
