@echo off
chcp 65001 >nul
title AI Agent Repair Tool - 全自动模式
echo ============================================================
echo AI Agent 智能修复工具 - 全自动模式
echo ============================================================
echo 本工具将自动扫描并修复以下Agent：
echo   - OpenCode
echo   - Claude Code
echo   - Cursor
echo   - Windsurf
echo   - Hermes-Agent
echo ============================================================
echo.

python repair_tool.py

if errorlevel 1 (
    echo.
    echo [错误] Python未安装或未添加到PATH
    echo 请安装Python: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
)
