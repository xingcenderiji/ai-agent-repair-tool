#!/bin/bash
# AI Agent Repair Tool - 操控界面启动脚本

echo "============================================================"
echo "AI Agent 智能修复工具 - 操控界面"
echo "============================================================"
echo "启动后将自动打开浏览器..."
echo "如未打开，请手动访问显示的地址"
echo "============================================================"
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    python3 gui.py
elif command -v python &> /dev/null; then
    python gui.py
else
    echo "[错误] Python未安装"
    echo "请安装Python: https://www.python.org/downloads/"
    echo ""
    read -p "按回车键退出..."
fi
