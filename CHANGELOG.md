# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.1] - 2026-05-16

### Fixed
- 🐛 修复审计日志写入失败问题
  - `core/audit_logger.py` 中 `json.dumps` 误用为 `json.dump`，导致会话日志保存失败
  - 修复人: Claude Code (mimo-v2.5-pro)
- 🐛 修复命令执行异常处理
  - `core/env_detector.py` 添加 `FileNotFoundError` 和 `subprocess.TimeoutExpired` 专用异常处理
  - 修复"命令不存在"和"命令超时"错误信息本地化
  - 修复人: Claude Code (mimo-v2.5-pro)
- 🐛 修复下载管理器 mock 测试兼容性
  - `core/download_manager.py` 将 `urllib.request` 提升为模块级导入
  - 解决 Python 3.13 下 unittest.mock 无法 patch 局部导入的问题
  - 修复人: Claude Code (mimo-v2.5-pro)
- 🐛 修复测试套件兼容性问题
  - `tests/test_env_detector.py` 修复 `Path.exists` mock 签名，适配 Python 3.13
  - `tests/test_security.py` 从 pytest 风格迁移至 unittest.TestCase，移除 pytest 依赖
  - 修复人: Claude Code (mimo-v2.5-pro)

### Added
- ✨ CLI 批量模式支持
  - 添加 `--batch` / `--no-wait` 命令行参数
  - 批量模式跳过倒计时和"按任意键退出"提示
  - 适用于 CI/CD 管道和自动化脚本
  - 修复人: Claude Code (mimo-v2.5-pro)

### Changed
- 📦 补全缺失依赖
  - `requirements.txt` 添加 `aiohttp>=3.9.0` 和 `aiohttp-cors>=0.7.0`
  - 修复 API Server 因缺少依赖无法启动的问题
  - 修复人: Claude Code (mimo-v2.5-pro)
- ✅ 测试套件从 227 个测试扩展至 252 个，全部通过（1 个跳过）

## [1.4.0] - 2026-05-15

### Added
- 🔒 安全审计工具：自动化安全漏洞扫描
  - 检测高危风险：命令注入、动态代码执行、路径遍历
  - 检测中危风险：弱哈希算法、不安全的加密实践
  - 生成详细的安全审计报告（Markdown格式）
  - 集成到 CI/CD 流程，自动在 PR 时运行
- 🧪 测试缺口分析工具：自动化测试覆盖分析
  - 分析 Git 提交历史，识别缺少测试的代码变更
  - 按风险级别分类：高/中/低风险缺口
  - 自动生成 pytest 测试文件框架
  - 支持 CI 集成，发现高风险缺口时阻断构建

### Changed
- 增强代码质量保障体系
- 完善 CI/CD 工作流配置

## [1.3.0] - 2026-05-15

### Added
- 📦 自动安装功能：监控下载目录，识别用户自行下载的安装包
  - 支持 EXE/MSI/DMG/DEB/RPM/AppImage 等多种安装包格式
  - 智能文件名模式匹配，自动识别目标 Agent
  - 后台监控模式，每5秒自动扫描下载目录
  - 安装前自动备份现有版本

### Changed
- 优化下载管理器，支持与自动安装功能联动
- 更新 GUI 界面，新增自动安装控制面板
- 增强错误处理和用户提示

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

[Unreleased]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.4.1...HEAD
[1.4.1]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/xingcenderiji/ai-agent-repair-tool/releases/tag/v1.0.0
