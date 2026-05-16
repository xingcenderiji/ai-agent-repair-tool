"""
测试缺口检测器
"""

import re
from pathlib import Path
from typing import List

from .code_analyzer import CodeAnalyzer
from .git_analyzer import GitAnalyzer
from .types import (
    HIGH_RISK_PATTERNS,
    MEDIUM_RISK_PATTERNS,
    SKIP_FILE_PATTERNS,
    CommitInfo,
    CoverageGap,
    FileChange,
    RiskLevel,
)


class GapDetector:
    """测试缺口检测器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.code_analyzer = CodeAnalyzer()
        self.git_analyzer = GitAnalyzer(str(self.project_root))

    def detect_gaps(self, commits: List[CommitInfo]) -> List[CoverageGap]:
        """检测所有提交中的测试覆盖缺口"""
        gaps = []
        skipped = []

        for commit in commits:
            for file_change in commit.files:
                if self._should_skip_file(file_change.file_path):
                    skipped.append(f"跳过: {file_change.file_path}")
                    continue

                file_gaps = self._analyze_file_gaps(file_change, commit)
                gaps.extend(file_gaps)

        # 按风险级别排序
        gaps.sort(
            key=lambda g: {
                RiskLevel.HIGH: 0,
                RiskLevel.MEDIUM: 1,
                RiskLevel.LOW: 2,
            }[g.risk_level]
        )

        return gaps

    def _should_skip_file(self, file_path: str) -> bool:
        """检查是否应该跳过文件"""
        if not file_path.endswith(".py"):
            return True

        for pattern in SKIP_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True

        return False

    def _analyze_file_gaps(
        self, file_change: FileChange, commit: CommitInfo
    ) -> List[CoverageGap]:
        """分析单个文件的覆盖缺口"""
        gaps = []

        full_path = self.project_root / file_change.file_path
        if not full_path.exists():
            return gaps

        try:
            file_analysis = self.code_analyzer.analyze_file(str(full_path))
            if not file_analysis:
                return gaps

            existing_tests = self.code_analyzer.find_existing_tests(
                str(self.project_root), str(full_path)
            )

            # 分析文件中的高风险模式
            pattern_gaps = self._detect_pattern_gaps(
                str(full_path), file_analysis.content, file_change, commit
            )
            gaps.extend(pattern_gaps)

            # 分析函数覆盖
            for func in file_analysis.functions:
                if not self.code_analyzer.has_function_test(
                    existing_tests, func.name
                ):
                    risk_level = self._calculate_function_risk(
                        func, file_analysis.content
                    )

                    gap = CoverageGap(
                        file_path=file_change.file_path,
                        function_name=func.name,
                        line_number=func.start_line,
                        risk_level=risk_level,
                        reason=self._generate_reason(
                            func, risk_level, commit.message
                        ),
                        code_snippet=self._extract_function_code(
                            file_analysis.content, func
                        ),
                        affected_lines=list(
                            range(func.start_line, func.end_line + 1)
                        ),
                    )
                    gaps.append(gap)

            # 检查整体复杂度
            if file_analysis.complexity > 20 and len(existing_tests) == 0:
                gaps.append(
                    CoverageGap(
                        file_path=file_change.file_path,
                        line_number=1,
                        risk_level=RiskLevel.MEDIUM,
                        reason=f"高复杂度文件 (复杂度: {file_analysis.complexity})，但没有对应的测试文件",
                        code_snippet=file_analysis.content[:500],
                        affected_lines=[],
                    )
                )

        except Exception as e:
            print(f"分析文件 {file_change.file_path} 出错: {e}")

        return gaps

    def _detect_pattern_gaps(
        self,
        file_path: str,
        content: str,
        file_change: FileChange,
        commit: CommitInfo,
    ) -> List[CoverageGap]:
        """检测代码中的风险模式"""
        gaps = []

        lines = content.split("\n")

        # 检查高风险模式
        for i, line in enumerate(lines, 1):
            for pattern, reason in HIGH_RISK_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    gaps.append(
                        CoverageGap(
                            file_path=file_path,
                            line_number=i,
                            risk_level=RiskLevel.HIGH,
                            reason=reason,
                            code_snippet=line.strip(),
                            affected_lines=[i],
                        )
                    )

        # 检查中等风险模式（只在新增或修改的文件中）
        if file_change.change_type in ["added", "modified"]:
            for i, line in enumerate(lines, 1):
                for pattern, reason in MEDIUM_RISK_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        gaps.append(
                            CoverageGap(
                                file_path=file_path,
                                line_number=i,
                                risk_level=RiskLevel.MEDIUM,
                                reason=reason,
                                code_snippet=line.strip(),
                                affected_lines=[i],
                            )
                        )

        return gaps

    def _calculate_function_risk(self, func, content: str) -> RiskLevel:
        """计算函数的风险级别"""
        func_content = self._extract_function_code(content, func)

        for pattern, _ in HIGH_RISK_PATTERNS:
            if re.search(pattern, func_content, re.IGNORECASE):
                return RiskLevel.HIGH

        if len(func.parameters) > 4:
            return RiskLevel.MEDIUM

        if func.is_async:
            return RiskLevel.MEDIUM

        if func.complexity > 10:
            return RiskLevel.MEDIUM

        for pattern, _ in MEDIUM_RISK_PATTERNS:
            if re.search(pattern, func_content, re.IGNORECASE):
                return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _generate_reason(
        self, func, risk_level: RiskLevel, commit_msg: str
    ) -> str:
        """生成缺口原因描述"""
        reasons = []

        if func.is_async:
            reasons.append("异步函数")

        if len(func.parameters) > 4:
            reasons.append(f"{len(func.parameters)} 个参数")

        if "fix" in commit_msg.lower() or "bug" in commit_msg.lower():
            reasons.append("Bug 修复提交 - 关键行为变更")

        if risk_level == RiskLevel.HIGH:
            reasons.append("包含高风险操作模式")

        if reasons:
            return "，".join(reasons)

        return "函数被修改但没有对应的测试"

    def _extract_function_code(self, content: str, func) -> str:
        """提取函数代码片段"""
        lines = content.split("\n")
        start = max(0, func.start_line - 1)
        end = min(len(lines), func.end_line)
        return "\n".join(lines[start:end])
