@echo off
chcp 65001 >nul
title AI Agent Repair Tool - 操控界面
echo ============================================================
echo AI Agent 智能修复工具 - 操控界面
echo ============================================================
echo 启动后将自动打开浏览器...
echo 如未打开，请手动访问显示的地址
echo ============================================================
echo.

python gui.py

if errorlevel 1 (
    echo.
    echo [错误] Python未安装或未添加到PATH
    echo 请安装Python: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
)
