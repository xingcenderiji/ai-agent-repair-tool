# AI Agent Repair Tool

全自动识别并修复 AI 开发工具（OpenCode、Claude Code、Cursor 等）的崩溃、配置损坏、数据丢失问题。

## 功能特性

- 🔍 **自动扫描** - 自动检测已安装的 AI 工具
- 🖥️ **操控界面** - Web 界面引导式操作，实时查看进度
- 🛠️ **一键修复** - 配置文件修复、缓存清理、插件修复
- 💾 **自动备份** - 修复前自动创建完整备份
- 📊 **修复报告** - 详细的成功/失败/警告统计
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

### 方式一：可执行文件（推荐）

1. 前往 [Releases](../../releases) 页面
2. 下载对应平台的文件：
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. **Windows**: 双击运行，自动打开浏览器界面
4. **Mac/Linux**: 终端运行 `./AI-Agent-Repair`

### 方式二：Python 脚本

```bash
# 克隆仓库
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool

# 运行（GUI 操控界面）
python gui.py

# 或命令行模式
python repair_tool.py
```

## 使用说明

### GUI 操控界面（推荐）

双击运行后自动打开浏览器，按以下流程操作：

```
① 扫描 → ② 审查 → ③ 确认 → ④ 修复 → ⑤ 完成
```

1. **扫描** - 点击"开始扫描"，自动检测已安装的 AI 工具
2. **审查** - 查看扫描结果，了解哪些工具有问题
3. **确认** - 查看修复方案，确认后点击"全部执行"
4. **修复** - 实时观察修复进度和日志
5. **完成** - 查看修复统计报告

### 命令行模式

```bash
python repair_tool.py
```

运行后自动扫描 → 3秒倒计时 → 自动修复 → 显示报告

## 修复内容

- ✅ 配置文件 JSON 格式修复
- ✅ 缓存文件清理（释放磁盘空间）
- ✅ 损坏插件检测与移除
- ✅ 数据完整性验证
- ✅ 修复后自动验证确认

## 备份位置

修复前会自动创建备份，保存在：
- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS**: `~/.ai_agent_backups`
- **Linux**: `~/.ai_agent_backups`

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/ -v

# 打包成可执行文件
pyinstaller --onefile --name AI-Agent-Repair --noconsole gui.py
```

## 许可证

MIT License
