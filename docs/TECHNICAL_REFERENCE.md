# AI 工具技术资料与修复方案

本文档整理了各 AI 开发工具的官方配置结构、常见问题及修复方案。

---

## 1. Cursor IDE

### 配置文件
- **主配置**: `%APPDATA%/Cursor/User/settings.json`
- **缓存目录**: `CachedData/`, `Cache/`, `GPUCache/`
- **日志**: `cursor_logs/`

### 常见问题与修复

| 问题 | 原因 | 修复方案 |
|------|------|---------|
| AI模式不工作 | GPU加速冲突 | 设置 `gpuAcceleration: "off"` |
| 界面冻结 | 后台进程冲突 | 清理缓存，禁用 `cursor.autoUpdate` |
| MCP服务器连接失败 | 配置格式错误 | 验证 mcpServers JSON 格式 |

### 推荐配置
```json
{
  "gpuAcceleration": "off",
  "cursor.autoUpdate": false,
  "cursor.logLevel": "verbose"
}
```

### 修复操作
1. 清理 `CachedData/` 目录
2. 重置 `settings.json` 中的 GPU 设置
3. 验证 MCP 配置格式

---

## 2. Claude Code

### 配置文件
- **用户配置**: `~/.claude/settings.json`
- **项目配置**: `./settings.json`
- **MCP配置**: `./.mcp.json`
- **环境变量**: `ANTHROPIC_API_KEY`

### 常见问题与修复

| 问题 | 原因 | 修复方案 |
|------|------|---------|
| API Key 无效 | 环境变量未设置 | 设置 `ANTHROPIC_API_KEY` |
| 配置加载失败 | JSON 格式错误 | 修复 settings.json |
| MCP服务器无法连接 | 配置路径错误 | 验证 .mcp.json |

### 诊断命令
```bash
claude config list
claude config get model
claude config get mcpServers
```

### 修复操作
1. 验证 `~/.claude.json` 格式
2. 检查 API Key 格式 (`sk-ant-api03-...`)
3. 修复 MCP 配置语法

---

## 3. Windsurf IDE

### 配置文件
- **主配置**: `%APPDATA%/Windsurf/User/settings.json`
- **状态数据库**: `state.vscdb`
- **缓存**: `CachedData/`, `Cache/`

### 常见问题与修复

| 问题 | 原因 | 修复方案 |
|------|------|---------|
| 会话状态不同步 | state.vscdb 损坏 | 删除 state.vscdb 重启 |
| 代码补全失效 | 索引损坏 | Invalidate Caches |
| Cascade 不工作 | MCP 配置错误 | 验证 mcpServers |

### 快速修复
- **快捷键**: `Ctrl+Alt+F10` (Windows/Linux) / `Cmd+Alt+F10` (macOS)
- **菜单**: File → Invalidate Caches and Restart

### 修复操作
1. 删除 `state.vscdb`
2. 清理 `CachedData/`
3. 重启 Windsurf

---

## 4. Cline (VS Code Extension)

### 配置文件
- **扩展数据**: `%APPDATA%/Code/User/globalStorage/saoudrizwanclaude-dev.claude-dev/`
- **设置**: VS Code settings.json 中的 `cline.*`

### 常见问题与修复

| 问题 | 原因 | 修复方案 |
|------|------|---------|
| 终端集成失败 | Shell 配置错误 | 设置 Default Terminal Profile |
| API 配置错误 | Base URL 格式错误 | 使用正确的 API 端点 |
| 模型不兼容 | 不支持的模型 | 选择兼容的模型 |

### 推荐设置
```json
{
  "cline.terminalReuse": true,
  "cline.terminalTimeout": 10000
}
```

### 修复操作
1. 重启 VS Code
2. 验证 API Provider 设置
3. 检查 temperature 值 (0-2)

---

## 5. Aider

### 配置文件
- **YAML配置**: `.aider.conf.yml`
- **环境变量**: `.env`
- **查找顺序**: home → git root → cwd

### 常见问题与修复

| 问题 | 原因 | 修复方案 |
|------|------|---------|
| API Key 未找到 | .env 文件缺失 | 创建 .env 文件 |
| 配置加载失败 | YAML 语法错误 | 修复 .aider.conf.yml |
| 模型不可用 | API 配置错误 | 验证模型名称 |

### 配置示例 (.aider.conf.yml)
```yaml
model: claude-sonnet-4
api-key: ${ANTHROPIC_API_KEY}
```

### 修复操作
1. 验证 `.aider.conf.yml` 语法
2. 检查 `.env` 文件存在
3. 验证 API Key 环境变量

---

## 6. GitHub Copilot

### 配置文件
- **扩展数据**: `~/Library/Application Support/Code/User/globalStorage/github.copilot/`
- **设置**: VS Code settings.json 中的 `github.copilot.*`

### 常见问题与修复

| 问题 | 原因 | 修复方案 |
|------|------|---------|
| 认证失败 | Token 过期 | 删除 globalStorage 重新登录 |
| 连接失败 | 网络问题 | 检查网络/代理设置 |
| 建议重复/卡顿 | 缓存损坏 | 清理 globalStorage |

### 修复命令
```bash
# macOS/Linux
rm -rf ~/Library/Application\ Support/Code/User/globalStorage/github.copilot

# Windows
rmdir /s "%APPDATA%\Code\User\globalStorage\github.copilot"
```

### 修复操作
1. 删除 `globalStorage/github.copilot`
2. 重启 VS Code
3. 重新登录 GitHub

---

## 7. Continue

### 配置文件
- **配置**: `~/.continue/config.json`
- **扩展数据**: VS Code globalStorage

### 常见问题与修复
- 配置文件损坏 → 重置 config.json
- 模型连接失败 → 验证 API Key

---

## 8. OpenCode

### 配置文件
- **主配置**: `~/.opencode/settings.json`
- **缓存**: `~/.opencode/cache/`

### 常见问题与修复
- 配置损坏 → 修复 settings.json
- 缓存过大 → 清理 cache 目录

---

## 9. Roo Code

### 配置文件
- **配置**: `~/.roo/settings.json`
- **扩展数据**: VS Code globalStorage

### 常见问题与修复
- 与 Cline 类似的配置结构
- 状态同步问题 → 清理状态文件

---

## 10. Augment Code

### 配置文件
- **配置**: `~/.augment/config.json`

### 常见问题与修复
- 配置加载失败 → 验证 JSON 格式
- API 连接问题 → 检查认证配置

---

## 11. Hermes-Agent

### 配置文件
- **配置**: `~/.hermes/config.json`

### 常见问题与修复
- 配置损坏 → 重置配置文件
- 插件加载失败 → 清理插件缓存

---

## 通用修复策略

### 配置文件修复
1. 备份原文件
2. 验证 JSON/YAML 语法
3. 如损坏则用默认配置替换

### 缓存清理
1. 识别缓存目录
2. 保留必要文件
3. 清理过期/损坏数据

### 权限修复
1. 检查文件权限
2. 修复只读文件
3. 验证目录可写
