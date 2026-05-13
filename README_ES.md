# Herramienta de Reparación de Agentes IA

[English](README_EN.md) | [中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md) | [Français](README_FR.md) | [Deutsch](README_DE.md)

---

Detecta y repara automáticamente herramientas de desarrollo de IA - fallos, configuraciones corruptas y pérdida de datos.

## Características

- 🔍 **Escaneo Automático** - Detecta herramientas IA instaladas
- 🖥️ **Interfaz GUI** - Flujo de trabajo guiado basado en web
- 🛠️ **Reparación con Un Clic** - Repara configs, limpia caché, repara plugins
- 💾 **Backup Automático** - Backup completo antes de cualquier reparación
- 📊 **Informes Detallados** - Estadísticas de éxito/fallo/advertencia
- 🔄 **Actualización Automática** - Configs de herramientas contribuidas por la comunidad
- 🌍 **Multiplataforma** - Windows, macOS, Linux
- 🔒 **Seguridad** - Validación de rutas, verificación de configs, registro de auditoría
- 🌐 **i18n** - 8 idiomas soportados (EN, ZH, JA, ES, FR, DE, KO, RU)

## Herramientas IA Soportadas (11)

### Plugins IDE
| Herramienta | Windows | macOS | Linux |
|-------------|---------|-------|-------|
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Cline | ✅ | ✅ | ✅ |
| Continue | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |

### Herramientas Independientes
| Herramienta | Windows | macOS | Linux |
|-------------|---------|-------|-------|
| Claude Code | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Aider | ✅ | ✅ | ✅ |
| Roo Code | ✅ | ✅ | ✅ |
| Augment Code | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

## Inicio Rápido

### Opción 1: Instalación con Un Clic (Recomendado)

**Windows** (cmd o PowerShell):
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux**:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

### Opción 2: Descargar Ejecutable

1. Ir a la página [Releases](../../releases)
2. Descargar para tu plataforma:
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. Ejecutar el archivo

### Opción 3: Instalación Manual

```bash
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool
python gui.py
```

## Uso

### Modo GUI (Recomendado)

```
① Escanear → ② Revisar → ③ Confirmar → ④ Reparar → ⑤ Completar
```

### Modo Línea de Comandos

```bash
python repair_tool.py
```

## Qué se Repara

- ✅ Formato de archivos de configuración JSON
- ✅ Limpieza de caché (liberar espacio en disco)
- ✅ Detección de plugins corruptos
- ✅ Verificación de integridad de datos
- ✅ Validación post-reparación

## Ubicación de Backup

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS/Linux**: `~/.ai_agent_backups`

## Registros de Auditoría

Todas las operaciones se registran:
- **Ubicación**: `~/.ai_agent_repair/audit_logs`
- **Herramienta de consulta**: `python audit_analyzer.py --list`

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para las directrices.

## Licencia

MIT License
