# AI Agent Repair Tool v1.2.0

## 🎉 What's New

16 个新功能、3 项改进、2 个修复

## 📥 Downloads

| Platform | File | Size |
|----------|------|------|
| macOS (Universal) | `AI-Agent-Repair-macOS` | ~8 MB |
| Windows | `AI-Agent-Repair-Windows.exe` | ~9 MB |
| Linux | `AI-Agent-Repair-Linux` | ~17 MB |

## ✨ New Features

- ✨ 配置扫描预览功能
- 新增 ConfigScanner 模块，扫描各AI工具的详细配置
- 可读取配置文件、插件列表、MCP服务器、技能/功能开关
- 新增配置预览界面，在修复前展示详细信息
- 支持导出扫描报告（JSON/Markdown格式）
- 🌍 环境检测与验证
- 新增 EnvironmentDetector 模块，识别虚拟化环境
- 支持检测: WSL1/WSL2、Termux、Docker、虚拟机
- 在GUI顶部显示当前环境类型和警告
- 虚拟环境中自动显示环境警告提示
- WSL2下支持访问Windows文件系统 (/mnt/c)
- 📥 下载管理器
- 支持两种模式：自动下载 / 获取链接
- 用户可选择用IDM、ADM、迅雷等工具加速下载
- 添加模态对话框显示下载项和进度
- 链接模式下一键复制所有下载链接

## 🔧 Improvements

- 优化修复流程：扫描 → 预览 → 审查 → 确认 → 修复 → 完成
- 更新GUI界面，增加流程指示器
- 改进多平台构建流程，修复文件名冲突问题

## 🐛 Bug Fixes

- 修复多平台构建文件名冲突问题，确保3个平台安装包都能正确上传
- 修复手动触发构建失败问题，添加tag输入和release更新支持

## 🚀 Usage

1. Download the file for your platform
2. Windows: Double-click `.exe`
3. Mac: `./AI-Agent-Repair-macOS` in terminal
4. Linux: `./AI-Agent-Repair-Linux` in terminal
5. Browser opens → Scan → Preview → Confirm → Repair

## 🛠️ Supported Tools (11)

Cursor, Windsurf, Cline, Continue, GitHub Copilot, Claude Code, OpenCode, Aider, Roo Code, Augment Code, Hermes-Agent

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## 🌐 Multi-language Support

- 🇺🇸 English: [README_EN.md](README_EN.md)
- 🇨🇳 中文: [README_ZH.md](README_ZH.md)
- 🇯🇵 日本語: [README_JA.md](README_JA.md)
- 🇪🇸 Español: [README_ES.md](README_ES.md)
- 🇫🇷 Français: [README_FR.md](README_FR.md)
- 🇩🇪 Deutsch: [README_DE.md](README_DE.md)

---

**Full Changelog**: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.1.0...v1.2.0
