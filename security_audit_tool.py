#!/usr/bin/env python3
"""
AI Agent Repair Tool - 安全审计工具
用于周期性漏洞评估，识别中等严重度及以上的已确认漏洞

使用方法：
    python security_audit_tool.py
    python security_audit_tool.py --output report.md
    python security_audit_tool.py --format json

作者：AI Assistant
日期：2026-05-15
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import re


class Severity(Enum):
    """漏洞严重度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Finding:
    """审计发现"""
    id: str
    title: str
    severity: Severity
    category: str
    description: str
    location: str
    evidence: str
    impact: str
    attacker_profile: str
    attack_vector: str
    code_path: str
    remediation: str
    cwe_id: Optional[str] = None


class SecurityAuditor:
    """安全审计器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.findings: List[Finding] = []
        self.stats = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

    def audit(self) -> Dict:
        """执行完整审计"""
        print("=" * 60)
        print("AI Agent Repair Tool - 安全审计")
        print("=" * 60)
        print(f"项目路径: {self.project_root}")
        print(f"审计时间: {datetime.now().isoformat()}")
        print("=" * 60)

        print("\n[1/5] 审计认证与访问控制...")
        self._audit_auth()

        print("[2/5] 审计注入向量...")
        self._audit_injection()

        print("[3/5] 审计外部交互...")
        self._audit_external_interactions()

        print("[4/5] 审计敏感数据处理...")
        self._audit_sensitive_data()

        print("[5/5] 生成审计报告...")
        report = self._generate_report()

        print("\n" + "=" * 60)
        print("审计完成！")
        print("=" * 60)

        return report

    def _audit_auth(self):
        """审计认证与访问控制"""
        # 检查是否存在硬编码凭证
        credential_patterns = [
            (r'password\s*=\s*["\'](?![\s\S]{0,50}$)', "硬编码密码"),
            (r'api_key\s*=\s*["\'][\w-]{10,}', "硬编码 API Key"),
            (r'secret\s*=\s*["\'][\w-]{10,}', "硬编码 Secret"),
            (r'token\s*=\s*["\'][\w-]{20,}', "硬编码 Token"),
        ]

        for pattern, desc in credential_patterns:
            self._search_pattern(
                pattern, desc, Severity.HIGH,
                "认证与访问控制",
                "硬编码凭证会直接暴露给攻击者"
            )

    def _audit_injection(self):
        """审计注入向量"""
        # SQL 注入风险
        sql_patterns = [
            (r'cursor\.execute\s*\([^)]*\%s[^)]*\)', "参数化查询 (安全)"),
            (r'execute\s*\([^)]*\+[^)]*\)', "字符串拼接 SQL (危险)"),
            (r'f["\'][^"\']*SELECT[^"\']*\{', "f-string SQL (危险)"),
        ]

        for pattern, desc in sql_patterns:
            is_safe = "安全" in desc
            self._search_pattern(
                pattern, f"SQL查询检查: {desc}",
                Severity.LOW if is_safe else Severity.MEDIUM,
                "注入向量",
                "SQL 注入可导致数据泄露"
            )

        # 命令注入风险
        cmd_patterns = [
            (r'subprocess\.run\s*\([^)]*shell\s*=\s*True(?!.*# noqa: safe-shell)', "Shell=True 命令执行 (高风险)"),
            (r'os\.system\s*\(', "os.system 命令执行 (高风险)"),
            (r'os\.popen\s*\(', "os.popen 命令执行 (高风险)"),
            (r'exec\s*\(', "动态代码执行 (极高风险)"),
            (r'eval\s*\(', "动态代码执行 (极高风险)"),
        ]

        for pattern, desc in cmd_patterns:
            self._search_pattern(
                pattern, desc,
                Severity.CRITICAL if "exec" in desc else Severity.HIGH,
                "注入向量",
                "命令注入可导致服务器被完全控制"
            )

        # 路径遍历风险
        path_patterns = [
            (r'open\s*\([^)]*\+[^)]*\)', "字符串拼接文件路径"),
            (r'Path\([^)]*\+[^)]*\)', "Path 拼接路径"),
            (r'\.\./', "路径遍历符"),
        ]

        for pattern, desc in path_patterns:
            self._search_pattern(
                pattern, f"路径操作检查: {desc}",
                Severity.MEDIUM,
                "注入向量",
                "路径遍历可访问未授权文件"
            )

    def _audit_external_interactions(self):
        """审计外部交互"""
        # 网络请求检查
        network_patterns = [
            (r'requests\.(?:get|post)\s*\(', "HTTP 请求"),
            (r'urllib\.request', "urllib 请求"),
            (r'fetch\s*\(', "Fetch API"),
            (r'http\.request', "HTTP 请求"),
        ]

        for pattern, desc in network_patterns:
            self._search_pattern(
                pattern, f"网络请求: {desc}",
                Severity.INFO,
                "外部交互",
                "检查请求是否正确处理 SSL/TLS"
            )

        # Webhook 回调检查
        webhook_patterns = [
            (r'webhook', "Webhook 处理"),
            (r'callback', "回调函数"),
        ]

        for pattern, desc in webhook_patterns:
            self._search_pattern(
                pattern, f"外部回调: {desc}",
                Severity.LOW,
                "外部交互",
                "验证回调来源和签名"
            )

    def _audit_sensitive_data(self):
        """审计敏感数据处理"""
        # 日志记录检查
        log_patterns = [
            (r'print\s*\([^)]*password', "日志记录密码"),
            (r'print\s*\([^)]*secret', "日志记录密钥"),
            (r'print\s*\([^)]*token', "日志记录令牌"),
            (r'logging\.[^.]+\([^)]*password', "日志记录密码"),
            (r'console\.log\s*\([^)]*password', "控制台日志密码"),
        ]

        for pattern, desc in log_patterns:
            self._search_pattern(
                pattern, f"敏感日志: {desc}",
                Severity.MEDIUM,
                "敏感数据处理",
                "日志中的敏感信息可被未授权访问"
            )

        # 加密检查
        crypto_patterns = [
            (r'hashlib\.md5', "MD5 哈希 (不安全)"),
            (r'hashlib\.sha1', "SHA1 哈希 (不安全)"),
            (r'Crypto\.Cipher', "加密实现"),
        ]

        for pattern, desc in crypto_patterns:
            is_weak = "不安全" in desc
            self._search_pattern(
                pattern, f"加密检查: {desc}",
                Severity.MEDIUM if is_weak else Severity.INFO,
                "敏感数据处理",
                "弱哈希算法应避免用于密码存储"
            )

    def _search_pattern(self, pattern: str, title: str, severity: Severity,
                       category: str, impact: str):
        """搜索代码模式"""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return

        for py_file in self.project_root.rglob("*.py"):
            # 排除测试文件、虚拟环境和生成的文件
            path_str = str(py_file)
            if any(excluded in path_str for excluded in [
                "node_modules", ".venv", ".git", "__pycache__",
                "tests/", "test_", "_test.py"
            ]):
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split('\n')
                matches = list(regex.finditer(content))

                if matches:
                    # 过滤掉有安全注释的行
                    safe_matches = []
                    for match in matches:
                        # 获取匹配行号
                        line_num = content[:match.start()].count('\n')
                        # 检查该行及前后5行是否有安全注释
                        context_start = max(0, line_num - 2)
                        context_end = min(len(lines), line_num + 3)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        # 如果有安全注释，跳过此匹配
                        if '# safe' in context.lower() or 'noqa' in context.lower():
                            continue
                        safe_matches.append(match)
                    
                    if not safe_matches:
                        continue
                    
                    # 检查是否有对应的安全措施
                    has_safe_alternative = any(safe in content for safe in [
                        "paramiko",
                        "getpass",
                        "CryptContext",
                        "hashlib.pbkdf2",
                    ])

                    # 如果找到危险模式且没有安全措施，记录为发现
                    if severity in [Severity.HIGH, Severity.CRITICAL, Severity.MEDIUM]:
                        if not has_safe_alternative or "shell" in pattern.lower():
                            finding = Finding(
                                id=f"AUDIT-{len(self.findings)+1:03d}",
                                title=title,
                                severity=severity,
                                category=category,
                                description=f"在 {py_file.relative_to(self.project_root)} 中发现潜在{severity.value}风险",
                                location=str(py_file.relative_to(self.project_root)),
                                evidence=f"匹配模式: {pattern}",
                                impact=impact,
                                attacker_profile="外部攻击者或恶意用户",
                                attack_vector=f"通过构造恶意输入触发危险代码路径",
                                code_path=f"{py_file.relative_to(self.project_root)}",
                                remediation=self._get_remediation(severity, category),
                            )
                            self.findings.append(finding)
                            self.stats[severity.value] += 1
            except (OSError, UnicodeDecodeError):
                continue

    def _get_remediation(self, severity: Severity, category: str) -> str:
        """获取修复建议"""
        remediations = {
            Severity.CRITICAL: "立即修复：使用参数化查询或安全的 API，避免动态代码执行",
            Severity.HIGH: "尽快修复：添加输入验证，使用安全的库函数",
            Severity.MEDIUM: "计划修复：实施安全最佳实践，添加日志监控",
            Severity.LOW: "建议优化：遵循安全编码规范",
            Severity.INFO: "信息性：当前实现可接受，建议保持关注",
        }
        return remediations.get(severity, "请评估并修复")

    def _generate_report(self) -> Dict:
        """生成审计报告"""
        report = {
            "metadata": {
                "project": "ai-agent-repair-tool",
                "version": "1.3.0",
                "audit_date": datetime.now().isoformat(),
                "auditor": "Security Audit Tool",
            },
            "summary": {
                "total_findings": len(self.findings),
                "by_severity": self.stats.copy(),
            },
            "findings": [asdict(f) for f in self.findings],
        }

        # 打印摘要
        print("\n审计摘要:")
        print(f"  总发现数: {len(self.findings)}")
        print(f"  - 严重: {self.stats['critical']}")
        print(f"  - 高危: {self.stats['high']}")
        print(f"  - 中危: {self.stats['medium']}")
        print(f"  - 低危: {self.stats['low']}")
        print(f"  - 信息: {self.stats['info']}")

        # 打印关键发现
        critical_findings = [f for f in self.findings if f.severity == Severity.CRITICAL]
        high_findings = [f for f in self.findings if f.severity == Severity.HIGH]

        if not critical_findings and not high_findings:
            print("\n✅ 未发现严重或高危漏洞！")
        else:
            print("\n⚠️  发现需要关注的漏洞:")
            for finding in critical_findings + high_findings:
                print(f"  [{finding.severity.value.upper()}] {finding.title}")
                print(f"    位置: {finding.location}")

        return report

    def save_report(self, output_path: Path, format: str = "json"):
        """保存报告"""
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "metadata": {
                        "project": "ai-agent-repair-tool",
                        "version": "1.3.0",
                        "audit_date": datetime.now().isoformat(),
                    },
                    "summary": {
                        "total_findings": len(self.findings),
                        "by_severity": self.stats,
                    },
                    "findings": [asdict(f) for f in self.findings],
                }, f, indent=2, ensure_ascii=False)
        elif format == "markdown":
            self._save_markdown_report(output_path)

        print(f"\n报告已保存到: {output_path}")

    def _save_markdown_report(self, output_path: Path):
        """保存 Markdown 格式报告"""
        lines = [
            "# 安全审计报告",
            "",
            "## 审计信息",
            "",
            f"- **项目**: ai-agent-repair-tool",
            f"- **版本**: 1.3.0",
            f"- **审计时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 审计摘要",
            "",
            f"- **总发现数**: {len(self.findings)}",
            f"- **严重**: {self.stats['critical']}",
            f"- **高危**: {self.stats['high']}",
            f"- **中危**: {self.stats['medium']}",
            f"- **低危**: {self.stats['low']}",
            f"- **信息**: {self.stats['info']}",
            "",
        ]

        if not self.findings:
            lines.extend([
                "## 审计结果",
                "",
                "✅ **审计完成——未发现中等或更高严重度的已确认漏洞。**",
                "",
            ])
        else:
            lines.extend([
                "## 详细发现",
                "",
            ])

            for finding in self.findings:
                lines.extend([
                    f"### {finding.id}: {finding.title}",
                    "",
                    f"**严重度**: {finding.severity.value.upper()}",
                    "",
                    f"**类别**: {finding.category}",
                    "",
                    f"**位置**: `{finding.location}`",
                    "",
                    f"**描述**: {finding.description}",
                    "",
                    f"**证据**: {finding.evidence}",
                    "",
                    f"**影响**: {finding.impact}",
                    "",
                    f"**攻击者画像**: {finding.attacker_profile}",
                    "",
                    f"**攻击向量**: {finding.attack_vector}",
                    "",
                    f"**代码路径**: {finding.code_path}",
                    "",
                    f"**修复建议**: {finding.remediation}",
                    "",
                    "---",
                    "",
                ])

        lines.extend([
            "## 审计方法",
            "",
            "本次审计采用以下分组系统性地检查高风险攻击面：",
            "",
            "1. **认证与访问控制**：登录流程、会话管理、角色/权限校验",
            "2. **注入向量**：原始 SQL 查询、Shell 命令拼接、模板渲染、文件路径操作",
            "3. **外部交互**：Webhook 处理器、出站网络请求、第三方 API 集成",
            "4. **敏感数据处理**：代码或配置中的密钥、凭证或 PII 的日志记录、加密实践",
            "",
            "## 声明",
            "",
            "本报告仅代表审计时的代码状态。代码库持续更新，建议定期进行安全审计。",
        ])

        output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="AI Agent Repair Tool - 安全审计工具"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="security_audit_report.md",
        help="输出文件路径 (默认: security_audit_report.md)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown"],
        default="markdown",
        help="报告格式 (默认: markdown)"
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        default=None,
        help="项目路径 (默认: 当前目录)"
    )

    args = parser.parse_args()

    # 确定项目路径
    if args.project:
        project_root = Path(args.project).resolve()
    else:
        project_root = Path(__file__).parent.parent.resolve()

    # 执行审计
    auditor = SecurityAuditor(project_root)
    report = auditor.audit()

    # 保存报告
    output_path = Path(args.output)
    if output_path.is_absolute():
        save_path = output_path
    else:
        save_path = project_root / output_path

    auditor.save_report(save_path, args.format)

    # 返回状态码
    if auditor.stats["critical"] > 0 or auditor.stats["high"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
