# 添加新 AI 工具支持指南

感谢你对 AI Agent Repair Tool 的贡献！本文档说明如何为新 AI 开发工具添加支持。

## 快速步骤

### 1. 在 `agent_registry.py` 中注册新工具

在 `AGENT_REGISTRY` 字典中添加新条目：

```python
"your_agent_id": {
    "name": "显示名称",
    "icon": "🔤",
    "category": "IDE插件",  # 可选: IDE插件 / 独立工具 / CLI工具
    "paths": {
        "win": ["%USERPROFILE%/.your-agent", "%APPDATA%/YourAgent"],
        "mac": ["~/.your-agent", "~/Library/Application Support/YourAgent"],
        "linux": ["~/.your-agent", "~/.config/your-agent"]
    }
},
```

**注意事项：**
- `agent_id` 使用小写字母和下划线
- `icon` 使用单个 emoji
- `paths` 按操作系统分别列出常见安装路径（支持环境变量和 `~` 展开）
- 每个系统至少提供 2 个常见路径

### 2. 创建默认配置文件

在 `configs/` 目录下创建对应的配置：

```
configs/
└── your_agent_id/
    └── default.json
```

配置文件格式：

```json
{
  "agent_name": "Your Agent Name",
  "min_supported_version": "1.0.0",
  "config_files": ["settings.json", "config.json", "your_agent.json"],
  "cache_dirs": ["cache", "Cache", "temp", "Temp"],
  "log_files": ["*.log", "logs/*.log"],
  "critical_files": ["settings.json"],
  "default_config": {
    "version": "1.0.0",
    "settings": {}
  },
  "repair_strategies": {
    "config_corrupted": "replace_with_default",
    "cache_oversized": "clean_all",
    "permission_denied": "skip_and_report"
  }
}
```

### 3. 添加测试

在 `tests/test_repair_tool.py` 中添加测试用例：

```python
def test_scan_your_agent(self):
    """测试扫描 Your Agent"""
    # 创建模拟目录
    agent_dir = self.temp_dir / ".your-agent"
    agent_dir.mkdir()
    
    # 测试扫描
    path = find_agent("your_agent")
    # ... 断言
```

### 4. 提交 PR

1. Fork 本仓库
2. 创建分支: `git checkout -b add-your-agent`
3. 提交更改
4. 创建 Pull Request

## 配置文件字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_name` | string | 工具的显示名称 |
| `min_supported_version` | string | 最低支持的版本号 |
| `config_files` | array | 需要检查的配置文件列表 |
| `cache_dirs` | array | 缓存目录名称列表 |
| `log_files` | array | 日志文件匹配模式 |
| `critical_files` | array | 关键文件列表（修复时优先处理） |
| `default_config` | object | 默认配置内容（用于替换损坏文件） |
| `repair_strategies` | object | 修复策略配置 |

## 修复策略选项

| 策略 | 说明 |
|------|------|
| `replace_with_default` | 用默认配置替换损坏文件 |
| `clean_all` | 清理全部缓存 |
| `clean_keep_recent` | 只清理旧缓存 |
| `skip_and_report` | 跳过并报告 |
| `manual_fix_required` | 需要手动修复 |

## 版本特定配置

如果工具的不同版本有不同的路径或配置，可以创建版本特定配置：

```
configs/
└── your_agent/
    ├── default.json      # 默认配置
    ├── v1.x.json         # 1.x 版本
    └── v2.x.json         # 2.x 版本
```

## 当前支持的分类

| 分类 | 说明 | 示例 |
|------|------|------|
| `IDE插件` | VS Code / JetBrains 插件 | Cursor, Cline, Continue, Copilot |
| `独立工具` | 独立运行的桌面/终端工具 | Claude Code, OpenCode, Aider |
| `CLI工具` | 命令行工具 | Aider |
