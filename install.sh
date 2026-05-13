#!/bin/bash
# AI Agent Repair Tool - 一键安装脚本 (macOS/Linux)
# 支持: bash, zsh, fish

set -e

echo "============================================================"
echo " AI Agent 智能修复工具 - 一键安装"
echo "============================================================"
echo ""

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    *)      PLATFORM="unknown" ;;
esac

# 检查 git
if ! command -v git &> /dev/null; then
    echo "[!] 未检测到 Git，正在安装..."
    if [ "$PLATFORM" = "macos" ]; then
        xcode-select --install 2>/dev/null || brew install git
    elif [ "$PLATFORM" = "linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y -qq git
        elif command -v yum &> /dev/null; then
            sudo yum install -y git
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm git
        fi
    fi
fi

# 检查 python3
if ! command -v python3 &> /dev/null; then
    echo "[!] 未检测到 Python3，正在安装..."
    if [ "$PLATFORM" = "macos" ]; then
        brew install python3
    elif [ "$PLATFORM" = "linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y -qq python3 python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm python python-pip
        fi
    fi
fi

# 确定安装位置
if [ "$PLATFORM" = "macos" ]; then
    INSTALL_DIR="$HOME/Desktop/ai-agent-repair-tool"
else
    INSTALL_DIR="$HOME/ai-agent-repair-tool"
fi

# 克隆项目
echo "[1/3] 正在下载项目..."
if [ ! -d "$INSTALL_DIR" ]; then
    git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git "$INSTALL_DIR"
else
    echo "[OK] 项目已存在，跳过下载"
fi

# 进入项目目录
cd "$INSTALL_DIR"

# 安装依赖
echo "[2/3] 正在安装依赖..."
python3 -m pip install -r requirements.txt --quiet 2>/dev/null || true

# 设置执行权限
chmod +x run.sh gui.py repair_tool.py 2>/dev/null || true

# 创建桌面快捷方式 (Linux)
echo "[3/3] 创建启动快捷方式..."
if [ "$PLATFORM" = "linux" ] && command -v xdg-desktop-menu &> /dev/null; then
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/ai-agent-repair.desktop" << EOF
[Desktop Entry]
Name=AI Agent Repair Tool
Comment=AI Agent 智能修复工具
Exec=python3 $INSTALL_DIR/gui.py
Icon=python3
Terminal=false
Type=Application
Categories=Utility;
EOF
    xdg-desktop-menu install --novendor "$HOME/.local/share/applications/ai-agent-repair.desktop" 2>/dev/null || true
    echo "[OK] 已添加到应用程序菜单"
elif [ "$PLATFORM" = "macos" ]; then
    # macOS 创建 Automator App
    osacompile -o "$HOME/Desktop/AI修复工具.app" << EOF
on run
    do shell script "cd \"$INSTALL_DIR\" && python3 gui.py"
end run
EOF
    echo "[OK] 已在桌面创建 AI修复工具.app"
fi

echo ""
echo "============================================================"
echo " 安装完成！"
echo "============================================================"
echo ""
echo " 启动方式："
if [ "$PLATFORM" = "macos" ]; then
    echo "   1. 双击桌面 [AI修复工具] 图标"
    echo "   2. 或终端运行: cd \"$INSTALL_DIR\" && python3 gui.py"
else
    echo "   1. 在应用程序菜单中找到 [AI Agent Repair Tool]"
    echo "   2. 或终端运行: cd \"$INSTALL_DIR\" && python3 gui.py"
fi
echo ""
echo " 项目位置：$INSTALL_DIR"
echo "============================================================"
