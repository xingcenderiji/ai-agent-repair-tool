"""
AI Agent 修复工具 - Agent 注册表
集中管理所有支持的 AI 开发工具及其路径配置

社区贡献指南：
  如需添加新的 AI 工具支持，请按以下格式添加到 AGENT_REGISTRY 中：
  {
      "agent_id": {
          "name": "显示名称",
          "icon": "emoji图标",
          "category": "IDE插件/独立工具/CLI工具",
          "paths": {
              "win": ["Windows路径1", "Windows路径2"],
              "mac": ["macOS路径1", "macOS路径2"],
              "linux": ["Linux路径1", "Linux路径2"]
          }
  }
"""

from pathlib import Path
from datetime import datetime

AGENT_REGISTRY = {
    # ============================================================
    # IDE 插件类
    # ============================================================
    "cursor": {
        "name": "Cursor",
        "icon": "🔵",
        "category": "IDE插件",
        "paths": {
            "win": ["%APPDATA%/Cursor", "%USERPROFILE%/.cursor"],
            "mac": ["~/Library/Application Support/Cursor", "~/.cursor"],
            "linux": ["~/.config/Cursor", "~/.cursor"]
        }
    },
    "windsurf": {
        "name": "Windsurf",
        "icon": "🟣",
        "category": "IDE插件",
        "paths": {
            "win": ["%APPDATA%/Windsurf", "%USERPROFILE%/.windsurf"],
            "mac": ["~/Library/Application Support/Windsurf", "~/.windsurf"],
            "linux": ["~/.config/Windsurf", "~/.windsurf"]
        }
    },
    "cline": {
        "name": "Cline",
        "icon": "🟤",
        "category": "IDE插件",
        "paths": {
            "win": ["%USERPROFILE%/.cline", "%APPDATA%/Cline"],
            "mac": ["~/.cline", "~/Library/Application Support/Cline"],
            "linux": ["~/.cline", "~/.config/cline"]
        }
    },
    "continue": {
        "name": "Continue",
        "icon": "🟤",
        "category": "IDE插件",
        "paths": {
            "win": ["%USERPROFILE%/.continue", "%APPDATA%/Continue"],
            "mac": ["~/.continue", "~/Library/Application Support/Continue"],
            "linux": ["~/.continue", "~/.config/continue"]
        }
    },
    "copilot": {
        "name": "GitHub Copilot",
        "icon": "⚫",
        "category": "IDE插件",
        "paths": {
            "win": ["%APPDATA%/GitHub Copilot", "%USERPROFILE%/.copilot"],
            "mac": ["~/Library/Application Support/GitHub Copilot", "~/.copilot"],
            "linux": ["~/.config/github-copilot", "~/.copilot"]
        }
    },

    # ============================================================
    # 独立工具类
    # ============================================================
    "claude": {
        "name": "Claude Code",
        "icon": "🟠",
        "category": "独立工具",
        "paths": {
            "win": ["%USERPROFILE%/.claude", "%APPDATA%/Claude"],
            "mac": ["~/.claude", "~/Library/Application Support/Claude"],
            "linux": ["~/.claude", "~/.config/claude"]
        }
    },
    "opencode": {
        "name": "OpenCode",
        "icon": "🟢",
        "category": "独立工具",
        "paths": {
            "win": ["%USERPROFILE%/.opencode", "%APPDATA%/OpenCode"],
            "mac": ["~/.opencode", "~/Library/Application Support/OpenCode"],
            "linux": ["~/.opencode", "~/.config/opencode"]
        }
    },
    "aider": {
        "name": "Aider",
        "icon": "🤖",
        "category": "独立工具",
        "paths": {
            "win": ["%USERPROFILE%/.aider", "%APPDATA%/Aider"],
            "mac": ["~/.aider", "~/.config/aider"],
            "linux": ["~/.aider", "~/.config/aider"]
        }
    },
    "hermes": {
        "name": "Hermes-Agent",
        "icon": "🟡",
        "category": "独立工具",
        "paths": {
            "win": ["%USERPROFILE%/.hermes", "%APPDATA%/Hermes"],
            "mac": ["~/.hermes", "~/Library/Application Support/Hermes"],
            "linux": ["~/.hermes", "~/.config/hermes"]
        }
    },
    "roo": {
        "name": "Roo Code",
        "icon": "🦘",
        "category": "独立工具",
        "paths": {
            "win": ["%USERPROFILE%/.roo", "%APPDATA%/Roo"],
            "mac": ["~/.roo", "~/.config/roo"],
            "linux": ["~/.roo", "~/.config/roo"]
        }
    },
    "augment": {
        "name": "Augment Code",
        "icon": "🔮",
        "category": "独立工具",
        "paths": {
            "win": ["%USERPROFILE%/.augment", "%APPDATA%/Augment"],
            "mac": ["~/.augment", "~/.config/augment"],
            "linux": ["~/.augment", "~/.config/augment"]
        }
    },
}

# 兼容旧代码
AGENT_PATHS = AGENT_REGISTRY

# 远程配置仓库地址
REMOTE_REGISTRY_URL = "https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/agent_registry.py"

# 本地缓存
_CACHE_DIR = Path.home() / ".ai_agent_repair" / "cache"
_CACHE_FILE = _CACHE_DIR / "remote_agents.json"
_CACHE_MAX_AGE_HOURS = 24


def _load_remote_agents() -> dict:
    """
    从远程仓库加载社区贡献的新Agent配置
    返回额外的Agent字典
    安全: 加载后进行安全验证，拒绝不安全配置
    """
    import json as _json
    import urllib.request
    import urllib.error

    extra_agents = {}

    # 检查缓存
    if _CACHE_FILE.exists():
        try:
            age = datetime.now().timestamp() - _CACHE_FILE.stat().st_mtime
            if age < _CACHE_MAX_AGE_HOURS * 3600:
                with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return _json.load(f)
        except (OSError, _json.JSONDecodeError):
            pass

    # 从远程加载社区配置
    community_url = "https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/configs/community_agents.json"
    try:
        req = urllib.request.Request(
            community_url,
            headers={'User-Agent': 'AI-Agent-Repair-Tool/1.0', 'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                raw_data = _json.loads(resp.read().decode('utf-8'))

                # === 安全验证 ===
                try:
                    from core.security import ConfigValidator
                    validator = ConfigValidator()
                    is_safe, issues = validator.validate_community_config(raw_data)
                    if not is_safe:
                        # 拒绝不安全配置，只保留安全的
                        print(f"[安全警告] 社区配置中发现 {len(issues)} 个安全问题:")
                        for issue in issues:
                            print(f"  - {issue}")
                        # 过滤掉不安全的agent
                        safe_agents = {}
                        for agent_id, agent_config in raw_data.items():
                            if agent_id.startswith("_"):
                                continue
                            agent_safe, agent_issues = validator.validate_agent_config(agent_id, agent_config)
                            if agent_safe:
                                safe_agents[agent_id] = agent_config
                        extra_agents = safe_agents
                    else:
                        extra_agents = raw_data
                except ImportError:
                    # 安全模块不可用时，只加载已知安全的配置
                    extra_agents = {}

                # 保存缓存
                _CACHE_DIR.mkdir(parents=True, exist_ok=True)
                with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
                    _json.dump(extra_agents, f, indent=2)
    except (urllib.error.URLError, urllib.error.HTTPError, _json.JSONDecodeError, TimeoutError, OSError):
        pass

    return extra_agents


def load_all_agents() -> dict:
    """
    加载所有Agent（内置 + 社区贡献）
    """
    all_agents = dict(AGENT_REGISTRY)
    extra = _load_remote_agents()
    all_agents.update(extra)
    return all_agents


def get_agents_by_category():
    """按分类获取Agent列表"""
    categories = {}
    all_agents = load_all_agents()
    for agent_id, config in all_agents.items():
        cat = config.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "id": agent_id,
            "name": config["name"],
            "icon": config["icon"]
        })
    return categories


def get_all_agent_ids():
    """获取所有Agent ID列表"""
    return list(load_all_agents().keys())


def get_agent_count():
    """获取支持的Agent总数"""
    return len(load_all_agents())
