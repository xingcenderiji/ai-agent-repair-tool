@echo off
chcp 65001 >nul
title AI Agent Repair Tool
echo ============================================================
echo AI Agent 智能修复工具
echo ============================================================
echo.
python repair_tool.py
if errorlevel 1 (
    echo.
    echo [错误] Python未安装或未添加到PATH
    echo 请安装Python: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
)
echo.
echo ============================================================
echo 按任意键退出...
pause >nul
