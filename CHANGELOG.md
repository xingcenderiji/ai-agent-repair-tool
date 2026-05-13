# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 自动安装功能：监控下载目录，识别用户自行下载的安装包
- 文件类型识别：支持 EXE/MSI/DMG/DEB/RPM/AppImage 等安装包
- 文件名模式匹配，自动识别目标 Agent
- 后台监控模式，每5秒扫描下载目录

## [1.2.0] - 2026-05-13

### Added
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

### Changed
- 优化修复流程：扫描 → 预览 → 审查 → 确认 → 修复 → 完成
- 更新GUI界面，增加流程指示器
- 改进多平台构建流程，修复文件名冲突问题

### Fixed
- 修复多平台构建文件名冲突问题，确保3个平台安装包都能正确上传
- 修复手动触发构建失败问题，添加tag输入和release更新支持

## [1.1.0] - 2026-05-13

### Added
- 🔒 安全验证系统
  - 添加安全验证模块，防止恶意修复操作
  - 实现操作白名单机制
- 📝 审计日志
  - 添加审计日志功能，记录所有修复操作
  - 支持日志导出和分析
- 🌐 国际化支持
  - 支持6种语言：中文、英文、日文、西班牙文、法文、德文
  - 添加语言切换功能
- 🔧 多架构构建支持
  - 支持 macOS、Windows、Linux 三大平台
  - 自动化GitHub Actions构建流程

### Changed
- 重构核心修复引擎
- 优化GUI界面响应速度

## [1.0.0] - 2026-05-12

### Added
- 🎉 初始版本发布
- 支持11种AI开发工具检测：Cursor, Windsurf, Cline, Continue, GitHub Copilot, Claude Code, OpenCode, Aider, Roo Code, Augment Code, Hermes-Agent
- 自动扫描Agent安装状态
- 配置文件损坏检测
- 缓存清理功能
- Web-based GUI界面
- 修复前自动备份
- 修复进度实时显示

---

[Unreleased]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/releases/tag/v1.0.0
