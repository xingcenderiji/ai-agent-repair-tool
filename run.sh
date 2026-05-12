#!/bin/bash
# AI Agent Repair Tool - 启动脚本

echo "============================================================"
echo "AI Agent 智能修复工具"
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
fi

echo ""
echo "============================================================"
echo "按回车键退出..."
read
