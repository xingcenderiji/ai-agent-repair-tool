# AI Agent 修復ツール

[English](README_EN.md) | [中文](README_ZH.md) | [日本語](README_JA.md) | [Español](README_ES.md) | [Français](README_FR.md) | [Deutsch](README_DE.md)

---

AI 開発ツールのクラッシュ、設定破損、データ損失問題を自動検出・修復します。

## 機能

- 🔍 **自動スキャン** - インストール済み AI ツールを自動検出
- 🖥️ **GUI インターフェース** - Web ベースのガイド付きワークフロー
- 🛠️ **ワンクリック修復** - 設定修正、キャッシュ削除、プラグイン修復
- 💾 **自動バックアップ** - 修復前に完全バックアップ作成
- 📊 **詳細レポート** - 成功/失敗/警告の統計
- 🔄 **自動更新** - コミュニティ投稿のツール設定
- 🌍 **クロスプラットフォーム** - Windows、macOS、Linux
- 🔒 **セキュリティ** - パス検証、設定確認、監査ログ
- 🌐 **国際化** - 8言語対応 (EN, ZH, JA, ES, FR, DE, KO, RU)

## 対応 AI ツール (11)

### IDE プラグイン
| ツール | Windows | macOS | Linux |
|--------|---------|-------|-------|
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Cline | ✅ | ✅ | ✅ |
| Continue | ✅ | ✅ | ✅ |
| GitHub Copilot | ✅ | ✅ | ✅ |

### スタンドアロン ツール
| ツール | Windows | macOS | Linux |
|--------|---------|-------|-------|
| Claude Code | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Aider | ✅ | ✅ | ✅ |
| Roo Code | ✅ | ✅ | ✅ |
| Augment Code | ✅ | ✅ | ✅ |
| Hermes-Agent | ✅ | ✅ | ✅ |

## クイックスタート

### 方法1: ワンクリックインストール (推奨)

**Windows** (cmd または PowerShell):
```cmd
powershell -Command "iwr https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.bat -OutFile install.bat"; start install.bat
```

**macOS / Linux**:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/install.sh)
```

### 方法2: 実行ファイルをダウンロード

1. [Releases](../../releases) ページへ
2. プラットフォーム用のファイルをダウンロード:
   - Windows: `AI-Agent-Repair.exe`
   - macOS: `AI-Agent-Repair-macOS`
   - Linux: `AI-Agent-Repair-Linux`
3. 実行してください

### 方法3: 手動インストール

```bash
git clone https://github.com/xingcenderiji/ai-agent-repair-tool.git
cd ai-agent-repair-tool
python gui.py
```

## 使用方法

### GUI モード (推奨)

```
① スキャン → ② レビュー → ③ 確認 → ④ 修復 → ⑤ 完了
```

### コマンドライン モード

```bash
python repair_tool.py
```

## 修復内容

- ✅ JSON 設定ファイル形式
- ✅ キャッシュ削除 (ディスク空間確保)
- ✅ 破損プラグイン検出
- ✅ データ整合性検証
- ✅ 修復後検証

## バックアップ場所

- **Windows**: `%USERPROFILE%\.ai_agent_backups`
- **macOS/Linux**: `~/.ai_agent_backups`

## 監査ログ

すべての操作がログに記録されます:
- **場所**: `~/.ai_agent_repair/audit_logs`
- **クエリツール**: `python audit_analyzer.py --list`

## 貢献

[CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

## ライセンス

MIT License
