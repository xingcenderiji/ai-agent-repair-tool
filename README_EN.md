# Tiangong

> **天工** — Named after the ancient Chinese scientific classic *"Tiangong Kaiwu"* (天工开物), symbolizing the fusion of craftsmanship and technology. *Technology serves people.*

[English](README_EN.md) | [中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md) | [Français](README_FR.md) | [Deutsch](README_DE.md)

---

**AI Agent Repair Tool** — Automatically detect and repair AI development tools. Fixes crashes, corrupted configs, and data loss issues across 11 AI tools.

## Features

- 🔍 **Auto Scan** — Automatically detect installed AI tools
- 🖥️ **GUI Interface** — Web-based guided workflow with real-time progress
- 🛠️ **One-Click Repair** — Fix configs, clean cache, repair plugins
- 💾 **Auto Backup** — Full backup before any repair
- 📊 **Detailed Reports** — Success/failure/warning statistics
- 🔄 **Auto Update** — Community-contributed tool configs
- 🌍 **Cross Platform** — Windows, macOS, Linux
- 🔒 **Security** — Path validation, config verification, audit logging
- 🌐 **i18n** — 8 languages supported (EN, ZH, JA, ES, FR, DE, KO, RU)

## Supported AI Tools (11)

### IDE Plugins
| Tool | Windows | macOS | Linux |
|------|---------|-------|-------|
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Cline | ✅ | ✅ | ✅ |
| Continue | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |

### Standalone Tools
| Tool | Windows | macOS | Linux |
|------|---------|-------|-------|
| Claude Code | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Aider | ✅ | ✅ | ✅ |
| Roo Code | ✅ | ✅ | ✅ |
| Augment Code | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

## Quick Start

### Option 1: One-Click Install (Recommended)

**Windows** (cmd or PowerShell):
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux**:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

### Option 2: Download Executable

1. Go to [Releases](../../releases) page
2. Download for your platform:
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. Run the executable

### Option 3: Manual Install

```bash
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool
python gui.py
```

## Usage

### GUI Mode (Recommended)

```
① Scan → ② Review → ③ Confirm → ④ Repair → ⑤ Complete
```

### Command Line Mode

```bash
python repair_tool.py
```

### Batch Mode (CI/CD)

```bash
python repair_tool.py --batch
```

## What Gets Repaired

- ✅ JSON config file format
- ✅ Cache cleanup (free disk space)
- ✅ Corrupted plugin detection
- ✅ Data integrity verification
- ✅ Post-repair validation

## Backup Location

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS/Linux**: `~/.ai_agent_backups`

## Audit Logs

All operations are logged for root cause analysis:
- **Location**: `~/.ai_agent_repair/audit_logs`
- **Query Tool**: `python audit_analyzer.py --list`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License
