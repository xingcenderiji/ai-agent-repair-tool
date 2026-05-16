"""
类型定义和常量
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevel(Enum):
    """风险级别"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FileChange:
    """文件变更"""

    file_path: str
    change_type: str  # added, modified, deleted
    lines_added: int
    lines_removed: int
    content: Optional[str] = None


@dataclass
class CommitInfo:
    """提交信息"""

    hash: str
    message: str
    author: str
    date: str
    files: List[FileChange] = field(default_factory=list)


@dataclass
class CoverageGap:
    """覆盖缺口"""

    file_path: str
    function_name: Optional[str] = None
    line_number: int = 1
    risk_level: RiskLevel = RiskLevel.MEDIUM
    reason: str = ""
    code_snippet: str = ""
    affected_lines: List[int] = field(default_factory=list)


@dataclass
class GeneratedTest:
    """生成的测试"""

    file_path: str
    test_content: str
    target_function: str
    risk_addressed: str


@dataclass
class AnalysisResult:
    """分析结果"""

    analyzed_commits: int = 0
    detected_gaps: List[CoverageGap] = field(default_factory=list)
    generated_tests: List[GeneratedTest] = field(default_factory=list)
    skipped_items: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AnalyzerConfig:
    """分析器配置"""

    project_root: str
    test_pattern: str = "**/test*.py"
    src_pattern: str = "**/*.py"
    max_commits: int = 10
    skip_patterns: List[str] = field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
            "**/venv/**",
            "**/.venv/**",
        ]
    )
    include_patterns: List[str] = field(default_factory=list)
    test_framework: str = "pytest"
    test_dir: str = "tests"


# 高风险模式 - 需要立即生成测试
HIGH_RISK_PATTERNS = [
    (r"json\.loads", "JSON 解析 - 可能有运行时错误"),
    (r"\beval\s*\(", "eval 使用 - 代码注入风险"),
    (r"\bexec\s*\(", "exec 使用 - 代码执行风险"),
    (
        r"\beval\s*\(.*(?:req|request|input|body|params|query)",
        "使用用户输入执行代码 - 高安全风险",
    ),
    (r"\.execute\(|\.query\(|\.execute_query", "SQL 执行 - 可能有 SQL 注入"),
    (r"select.*from.*where.*\+", "SQL 查询拼接 - SQL 注入风险"),
    (r"insert.*values.*\+", "SQL 插入拼接 - SQL 注入风险"),
    (r"update.*set.*\+", "SQL 更新拼接 - SQL 注入风险"),
    (r"delete.*where.*\+", "SQL 删除拼接 - SQL 注入风险"),
    (r"await.*\.then", "异步操作链式调用 - 潜在竞态条件"),
    (r"Promise\.all|asyncio\.gather", "并发异步操作 - 竞态条件"),
    (
        r"\bmutual_exclusion\b|\block\b|\bsemaphore\b",
        "锁和互斥 - 并发控制逻辑",
    ),
    (
        r"\bauthenticate\b|\bauthorize\b|\bverify_permission\b",
        "认证和授权 - 安全关键模块",
    ),
    (
        r"\bcheck_access\b|\bvalidate_token\b|\bverify_signature\b",
        "权限验证和签名 - 安全关键模块",
    ),
    (r"\bencrypt\b|\bdecrypt\b|\bcipher\b", "加密解密 - 安全关键模块"),
    (r"\bre\.(match|search|findall|sub).*\+", "正则表达式动态构建"),
    (r"\bre.compile.*\+", "动态正则表达式 - ReDoS 风险"),
    (r"float\(|int\(|complex\(", "类型转换 - 可能有数据解析错误"),
    (r"parse.*\(|\bparse\w*\(", "数据解析 - 边界情况"),
    (r"\bparse_csv\b|\bparse_xml\b|\bparse_yaml\b", "数据格式解析"),
]

# 中等风险模式 - 建议生成测试
MEDIUM_RISK_PATTERNS = [
    (r"\bif\s*\(|\bif\s*:", "条件分支 - 需要边界测试"),
    (r"\bswitch\s*|\bcase\s*:", "多分支 - 需要覆盖所有情况"),
    (r"\btry\s*:|\bexcept\s*:", "异常处理 - 需要测试异常情况"),
    (r"\braise\s", "抛出异常 - 需要验证错误处理"),
    (r"\breturn\s", "返回点 - 需要不同返回路径"),
    (r"\bfor\s+.*in", "循环 - 需要测试边界条件"),
    (r"\bwhile\s*", "循环 - 需要测试退出条件"),
    (r"\bbreak\s*$|\bcontinue\s*$", "循环控制 - 需要测试不同路径"),
    (r"\?[^:]+:", "三元运算符 - 两个分支"),
    (r"\bor\s|\band\s", "逻辑运算 - 需要测试不同组合"),
    (r"\b==\b|\b!=\b", "比较运算 - 边界值测试"),
]

# 跳过的文件模式
SKIP_FILE_PATTERNS = [
    r"__pycache__",
    r"\.pyc$",
    r"__init__\.py$",
    r"conftest\.py$",
    r"test.*\.py$",
    r"_test\.py$",
    r"^\.",
    r"node_modules",
    r"venv",
    r"\.venv",
    r"dist",
    r"build",
]
