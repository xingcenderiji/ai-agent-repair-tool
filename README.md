# AI Agent Repair Tool

全自动识别并修复 AI 开发工具的崩溃、配置损坏、数据丢失问题。

## 功能特性

- 🔍 **自动扫描** - 自动检测已安装的 AI 工具
- 🖥️ **操控界面** - Web 界面引导式操作，实时查看进度
- 🛠️ **一键修复** - 配置文件修复、缓存清理、插件修复
- 💾 **自动备份** - 修复前自动创建完整备份
- 📊 **修复报告** - 详细的成功/失败/警告统计
- 🔄 **自动更新** - 自动获取社区贡献的新工具配置
- 🌍 **跨平台** - 支持 Windows、macOS、Linux
- 👥 **社区驱动** - 欢迎贡献新工具支持

## 支持的 AI 工具（11个）

### IDE 插件类
| 工具 | Windows | macOS | Linux |
|------|---------|-------|-------|
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Cline | ✅ | ✅ | ✅ |
| Continue | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |

### 独立工具类
| 工具 | Windows | macOS | Linux |
|------|---------|-------|-------|
| Claude Code | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Aider | ✅ | ✅ | ✅ |
| Roo Code | ✅ | ✅ | ✅ |
| Augment Code | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

> 💡 通过社区贡献机制，支持的工具数量会持续增加

## 快速开始

### 方式一：一键安装（推荐，零基础）

只需一条命令，自动安装所有依赖并启动：

**Windows** (在 cmd 或 PowerShell 中运行)：
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux** (在终端中运行)：
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

安装脚本会自动：
1. 检测并安装 Git 和 Python（如未安装）
2. 下载项目到桌面
3. 安装依赖
4. 创建桌面快捷方式

### 方式二：下载可执行文件

1. 前往 [Releases](../../releases) 页面
2. 下载对应平台的文件：
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. **Windows**: 双击运行，自动打开浏览器界面
4. **Mac/Linux**: 终端运行 `./AI-Agent-Repair`

### 方式三：手动安装

```bash
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool
python gui.py
```

## 使用说明

### GUI 操控界面（推荐）

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

自动扫描 → 3秒倒计时 → 自动修复 → 显示报告

## 修复内容

- ✅ 配置文件 JSON 格式修复
- ✅ 缓存文件清理（释放磁盘空间）
- ✅ 损坏插件检测与移除
- ✅ 数据完整性验证
- ✅ 修复后自动验证确认

## 备份位置

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS**: `~/.ai_agent_backups`
- **Linux**: `~/.ai_agent_backups`

## 贡献新工具

欢迎为更多 AI 工具添加支持！请查看 [贡献指南](CONTRIBUTING.md)。

快速步骤：
1. 在 `agent_registry.py` 中注册新工具
2. 在 `configs/` 下创建默认配置
3. 添加测试用例
4. 提交 Pull Request

## 开发

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
pyinstaller --onefile --name AI-Agent-Repair --noconsole gui.py
```

## 许可证

MIT License
