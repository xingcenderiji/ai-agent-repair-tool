# AI Agent 修复工具

[English](README_EN.md) | [中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md) | [Français](README_FR.md) | [Deutsch](README_DE.md)

---

全自动识别并修复 AI 开发工具的崩溃、配置损坏、数据丢失问题。

## 功能特性

- 🔍 **自动扫描** - 自动检测已安装的 AI 工具
- 🖥️ **操控界面** - Web 界面引导式操作，实时查看进度
- 🛠️ **一键修复** - 配置文件修复、缓存清理、插件修复
- 💾 **自动备份** - 修复前自动创建完整备份
- 📊 **修复报告** - 详细的成功/失败/警告统计
- 🔄 **自动更新** - 自动获取社区贡献的新工具配置
- 🌍 **跨平台** - 支持 Windows、macOS、Linux
- 🔒 **安全防护** - 路径验证、配置审核、操作审计
- 🌐 **国际化** - 支持 8 种语言 (EN, ZH, JA, ES, FR, DE, KO, RU)

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

## 快速开始

### 方式一：一键安装（推荐）

**Windows** (cmd 或 PowerShell):
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux**:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

### 方式二：下载可执行文件

1. 前往 [Releases](../../releases) 页面
2. 下载对应平台的文件：
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. 双击运行即可

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

### 命令行模式

```bash
python repair_tool.py
```

## 修复内容

- ✅ 配置文件 JSON 格式修复
- ✅ 缓存文件清理（释放磁盘空间）
- ✅ 损坏插件检测与移除
- ✅ 数据完整性验证
- ✅ 修复后自动验证确认

## 备份位置

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS/Linux**: `~/.ai_agent_backups`

## 审计日志

所有操作都会记录日志，支持根源分析：
- **位置**: `~/.ai_agent_repair/audit_logs`
- **查询工具**: `python audit_analyzer.py --list`

## 贡献指南

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT License
