@echo off
chcp 65001 >nul
echo ========================================
echo     班级管理系统 - 测试环境
echo ========================================
echo.
set FLASK_ENV=testing
python app.py
pause
