#!/bin/bash
# AI Agent Repair Tool - 全自动模式启动脚本

echo "============================================================"
echo "AI Agent 智能修复工具 - 全自动模式"
echo "============================================================"
echo "本工具将自动扫描并修复以下Agent："
echo "  - OpenCode"
echo "  - Claude Code"
echo "  - Cursor"
echo "  - Windsurf"
echo "  - Hermes-Agent"
echo "============================================================"
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    python3 repair_tool.py
elif command -v python &> /dev/null; then
    python repair_tool.py
else
    echo "[错误] Python未安装"
    echo "请安装Python: https://www.python.org/downloads/"
    echo ""
    read -p "按回车键退出..."
fi
