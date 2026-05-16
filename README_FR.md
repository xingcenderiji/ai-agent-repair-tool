# Outil de Réparation d'Agents IA

[English](README_EN.md) | [中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md) | [Français](README_FR.md) | [Deutsch](README_DE.md)

---

Détecte et répare automatiquement les outils de développement IA - plantages, configurations corrompues et perte de données.

## Fonctionnalités

- 🔍 **Scan Automatique** - Détecte les outils IA installés
- 🖥️ **Interface GUI** - Flux de travail guidé basé sur le web
- 🛠️ **Réparation en Un Clic** - Répare configs, nettoie cache, répare plugins
- 💾 **Backup Automatique** - Backup complet avant toute réparation
- 📊 **Rapports Détaillés** - Statistiques de succès/échec/avertissement
- 🔄 **Mise à Jour Auto** - Configs d'outils contribuées par la communauté
- 🌍 **Multiplateforme** - Windows, macOS, Linux
- 🔒 **Sécurité** - Validation de chemins, vérification de configs, journal d'audit
- 🌐 **i18n** - 8 langues supportées (EN, ZH, JA, ES, FR, DE, KO, RU)

## Outils IA Supportés (11)

### Plugins IDE
| Outil | Windows | macOS | Linux |
|-------|---------|-------|-------|
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Cline | ✅ | ✅ | ✅ |
| Continue | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |

### Outils Autonomes
| Outil | Windows | macOS | Linux |
|-------|---------|-------|-------|
| Claude Code | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Aider | ✅ | ✅ | ✅ |
| Roo Code | ✅ | ✅ | ✅ |
| Augment Code | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

## Démarrage Rapide

### Option 1: Installation en Un Clic (Recommandé)

**Windows** (cmd ou PowerShell):
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux**:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

### Option 2: Télécharger l'Exécutable

1. Aller à la page [Releases](../../releases)
2. Télécharger pour votre plateforme:
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. Exécuter le fichier

### Option 3: Installation Manuelle

```bash
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool
python gui.py
```

## Utilisation

### Mode GUI (Recommandé)

```
① Scanner → ② Examiner → ③ Confirmer → ④ Réparer → ⑤ Terminer
```

### Mode Ligne de Commande

```bash
python repair_tool.py
```

## Ce qui est Réparé

- ✅ Format des fichiers de configuration JSON
- ✅ Nettoyage du cache (libérer l'espace disque)
- ✅ Détection de plugins corrompus
- ✅ Vérification d'intégrité des données
- ✅ Validation post-réparation

## Emplacement du Backup

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS/Linux**: `~/.ai_agent_backups`

## Journaux d'Audit

Toutes les opérations sont journalisées:
- **Emplacement**: `~/.ai_agent_repair/audit_logs`
- **Outil de requête**: `python audit_analyzer.py --list`

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les directives.

## Licence

MIT License
