#!/usr/bin/env python3
"""
生成Release说明脚本
根据CHANGELOG和模板生成完整的Release说明
"""

import re
import sys
from pathlib import Path


def parse_changelog(version: str) -> dict:
    """解析CHANGELOG，提取指定版本的信息"""
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"

    if not changelog_path.exists():
        return {}

    content = changelog_path.read_text(encoding="utf-8")

    # 查找版本章节
    pattern = rf"## \[{re.escape(version)}\].*?(?=## \[|$)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return {}

    version_content = match.group(0)

    # 提取各部分
    sections = {
        "added": [],
        "changed": [],
        "fixed": [],
        "deprecated": [],
        "removed": [],
        "security": [],
    }

    current_section = None
    for line in version_content.split("\n"):
        line = line.strip()

        if line.startswith("### Added"):
            current_section = "added"
        elif line.startswith("### Changed"):
            current_section = "changed"
        elif line.startswith("### Fixed"):
            current_section = "fixed"
        elif line.startswith("### Deprecated"):
            current_section = "deprecated"
        elif line.startswith("### Removed"):
            current_section = "removed"
        elif line.startswith("### Security"):
            current_section = "security"
        elif line.startswith("- ") and current_section:
            sections[current_section].append(line[2:])

    return sections


def generate_release_notes(version: str, prev_version: str = None) -> str:
    """生成Release说明"""

    sections = parse_changelog(version)

    # 构建新功能部分
    new_features = []
    if sections.get("added"):
        for item in sections["added"]:
            new_features.append(f"- {item}")

    # 构建改进部分
    improvements = []
    if sections.get("changed"):
        for item in sections["changed"]:
            improvements.append(f"- {item}")

    # 构建修复部分
    bug_fixes = []
    if sections.get("fixed"):
        for item in sections["fixed"]:
            bug_fixes.append(f"- {item}")

    # 版本摘要
    summary_items = []
    if new_features:
        summary_items.append(f"{len(new_features)} 个新功能")
    if improvements:
        summary_items.append(f"{len(improvements)} 项改进")
    if bug_fixes:
        summary_items.append(f"{len(bug_fixes)} 个修复")

    version_summary = "、".join(summary_items) if summary_items else "常规更新"

    # 读取模板
    template_path = Path(__file__).parent.parent / "RELEASE_TEMPLATE.md"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        # 默认模板
        template = """# AI Agent Repair Tool v{VERSION}

## 🎉 What's New

{VERSION_SUMMARY}

## 📥 Downloads

| Platform | File |
|----------|------|
| macOS (Universal) | `AI-Agent-Repair-macOS` |
| Windows | `AI-Agent-Repair-Windows.exe` |
| Linux | `AI-Agent-Repair-Linux` |

## ✨ New Features

{NEW_FEATURES}

## 🔧 Improvements

{IMPROVEMENTS}

## 🐛 Bug Fixes

{BUG_FIXES}

## 🚀 Usage

1. Download the file for your platform
2. Windows: Double-click `.exe`
3. Mac: `./AI-Agent-Repair-macOS` in terminal
4. Linux: `./AI-Agent-Repair-Linux` in terminal
5. Browser opens → Scan → Preview → Confirm → Repair

## 🛠️ Supported Tools (11)

Cursor, Windsurf, Cline, Continue, GitHub Copilot, Claude Code, OpenCode, Aider, Roo Code, Augment Code, Hermes-Agent

---

**Full Changelog**: https://github.com/xingcenderiji/ai-agent-repair-tool/compare/v{PREV_VERSION}...v{VERSION}
"""

    # 填充模板
    release_notes = template.format(
        VERSION=version,
        PREV_VERSION=prev_version
        or f"{int(version.split('.')[0])}.{int(version.split('.')[1])-1}.0",
        VERSION_SUMMARY=version_summary,
        NEW_FEATURES="\n".join(new_features) if new_features else "- 无新功能",
        IMPROVEMENTS="\n".join(improvements) if improvements else "- 无改进",
        BUG_FIXES="\n".join(bug_fixes) if bug_fixes else "- 无修复",
        MAC_SIZE="~8 MB",
        WIN_SIZE="~9 MB",
        LINUX_SIZE="~17 MB",
    )

    return release_notes


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_release_notes.py <version> [prev_version]"
        )
        print("Example: python generate_release_notes.py 1.3.0 1.2.0")
        sys.exit(1)

    version = sys.argv[1]
    prev_version = sys.argv[2] if len(sys.argv) > 2 else None

    notes = generate_release_notes(version, prev_version)
    print(notes)

    # 保存到文件
    output_path = Path(__file__).parent.parent / f"RELEASE_v{version}.md"
    output_path.write_text(notes, encoding="utf-8")
    print(f"\n✅ Release说明已保存到: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
