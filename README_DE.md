# KI-Agent Reparatur-Tool

[English](README_EN.md) | [中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md) | [Français](README_FR.md) | [Deutsch](README_DE.md)

---

Erkennt und repariert automatisch KI-Entwicklungstools - Abstürze, beschädigte Konfigurationen und Datenverlust.

## Funktionen

- 🔍 **Automatischer Scan** - Erkennt installierte KI-Tools
- 🖥️ **GUI-Oberfläche** - Web-basierter geführter Workflow
- 🛠️ **Ein-Klick-Reparatur** - Repariert Configs, bereinigt Cache, repariert Plugins
- 💾 **Automatisches Backup** - Vollständiges Backup vor jeder Reparatur
- 📊 **Detaillierte Berichte** - Erfolgs/Fehler/Warnungs-Statistiken
- 🔄 **Auto-Update** - Community-beigesteuerte Tool-Konfigurationen
- 🌍 **Plattformübergreifend** - Windows, macOS, Linux
- 🔒 **Sicherheit** - Pfadvalidierung, Config-Überprüfung, Audit-Protokollierung
- 🌐 **i18n** - 8 Sprachen unterstützt (EN, ZH, JA, ES, FR, DE, KO, RU)

## Unterstützte KI-Tools (11)

### IDE-Plugins
| Tool | Windows | macOS | Linux |
|------|---------|-------|-------|
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Cline | ✅ | ✅ | ✅ |
| Continue | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |

### Eigenständige Tools
| Tool | Windows | macOS | Linux |
|------|---------|-------|-------|
| Claude Code | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Aider | ✅ | ✅ | ✅ |
| Roo Code | ✅ | ✅ | ✅ |
| Augment Code | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

## Schnellstart

### Option 1: Ein-Klick-Installation (Empfohlen)

**Windows** (cmd oder PowerShell):
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux**:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

### Option 2: Ausführbare Datei herunterladen

1. Zur [Releases](../../releases) Seite gehen
2. Für Ihre Plattform herunterladen:
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. Datei ausführen

### Option 3: Manuelle Installation

```bash
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool
python gui.py
```

## Verwendung

### GUI-Modus (Empfohlen)

```
① Scannen → ② Überprüfen → ③ Bestätigen → ④ Reparieren → ⑤ Fertig
```

### Kommandozeilen-Modus

```bash
python repair_tool.py
```

## Was repariert wird

- ✅ JSON-Konfigurationsdateiformat
- ✅ Cache-Bereinigung (Speicherplatz freigeben)
- ✅ Erkennung beschädigter Plugins
- ✅ Datenintegritätsprüfung
- ✅ Post-Reparatur-Validierung

## Backup-Speicherort

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS/Linux**: `~/.ai_agent_backups`

## Audit-Protokolle

Alle Operationen werden protokolliert:
- **Speicherort**: `~/.ai_agent_repair/audit_logs`
- **Abfrage-Tool**: `python audit_analyzer.py --list`

## Beitragen

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Richtlinien.

## Lizenz

MIT License
