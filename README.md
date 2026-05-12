# AI Agent Repair Tool

全自动识别并修复 AI 开发工具（OpenCode、Claude Code、Cursor 等）的崩溃、配置损坏、数据丢失问题。

## 功能特性

- 🔍 **自动扫描** - 自动检测已安装的 AI 工具
- 🛠️ **一键修复** - 配置文件修复、缓存清理、插件修复
- 💾 **自动备份** - 修复前自动创建完整备份
- 🖥️ **跨平台** - 支持 Windows、macOS、Linux

## 支持的 AI 工具

| 工具 | Windows | macOS | Linux |
|------|---------|-------|-------|
| OpenCode | ✅ | ✅ | ✅ |
| Claude Code | ✅ | ✅ | ✅ |
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

## 快速开始

### 方式一：Python 脚本（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/ai-agent-repair-tool.git
cd ai-agent-repair-tool

# 运行修复工具
python repair_tool.py
```

### 方式二：Windows 可执行文件

下载 `AI-Agent-Repair.exe`，双击运行即可。

## 使用说明

1. **自动扫描**：运行后自动检测已安装的 AI 工具
2. **查看问题**：显示检测到的配置损坏、缓存膨胀等问题
3. **一键修复**：输入 `y` 自动修复所有问题
4. **备份恢复**：所有操作前自动创建备份，可随时恢复

## 修复内容

- ✅ 配置文件 JSON 格式修复
- ✅ 缓存文件清理（释放磁盘空间）
- ✅ 损坏插件检测与移除
- ✅ 数据完整性验证

## 备份位置

修复前会自动创建备份，保存在：
- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS**: `~/.ai_agent_backups`
- **Linux**: `~/.ai_agent_backups`

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 打包成可执行文件
pyinstaller --onefile --name AI-Agent-Repair repair_tool.py
```

## 许可证

MIT License
