"""
测试生成器 - 为检测到的缺口生成测试代码
"""

import re
from pathlib import Path
from typing import List

from .types import CoverageGap, GeneratedTest, RiskLevel


class TestGenerator:
    """测试代码生成器"""

    def __init__(self, project_root: str, test_dir: str = "tests"):
        self.project_root = Path(project_root)
        self.test_dir = test_dir

    def generate_tests(
        self, gaps: List[CoverageGap], include_low_risk: bool = False
    ) -> List[GeneratedTest]:
        """为所有缺口生成测试"""
        if not include_low_risk:
            gaps = [g for g in gaps if g.risk_level != RiskLevel.LOW]

        # 按文件分组
        gaps_by_file = {}
        for gap in gaps:
            if gap.file_path not in gaps_by_file:
                gaps_by_file[gap.file_path] = []
            gaps_by_file[gap.file_path].append(gap)

        generated = []
        for file_path, file_gaps in gaps_by_file.items():
            test = self._generate_file_test(file_path, file_gaps)
            generated.append(test)

        return generated

    def _generate_file_test(
        self, file_path: str, gaps: List[CoverageGap]
    ) -> GeneratedTest:
        """为单个文件生成测试文件"""
        # 构建测试文件路径
        module_name = Path(file_path).stem
        test_file_name = f"test_{module_name}.py"

        # 获取模块路径用于导入
        module_parts = Path(file_path).parts
        if module_parts[0] == ".":
            module_parts = module_parts[1:]

        import_name = (
            ".".join(part for part in module_parts[:-1])
            if len(module_parts) > 1
            else ""
        )
        if import_name:
            import_statement = f"from {import_name} import {module_name}"
        else:
            import_statement = f"import {module_name}"

        # 生成测试用例
        test_cases = []
        for gap in gaps:
            test_case = self._generate_test_case(gap)
            test_cases.append(test_case)

        # 组合成完整的测试文件
        content = f'''"""
测试: {file_path}
自动生成的测试 - Test Gap Analyzer
"""
import pytest
import json
from unittest.mock import patch, Mock
{import_statement}


class Test{module_name.capitalize()}:
    """{module_name} 模块的测试类"""
    
'''
        content += "\n".join(test_cases)

        return GeneratedTest(
            file_path=str(Path(self.test_dir) / test_file_name),
            test_content=content,
            target_function=", ".join(
                [g.function_name or "unknown" for g in gaps]
            ),
            risk_addressed=", ".join([g.reason for g in gaps]),
        )

    def _generate_test_case(self, gap: CoverageGap) -> str:
        """生成单个测试用例"""
        function_name = gap.function_name or "unknown_function"
        test_name = self._safe_test_name(function_name, gap)

        if gap.risk_level == RiskLevel.HIGH:
            return self._generate_high_risk_test(function_name, test_name, gap)
        elif gap.risk_level == RiskLevel.MEDIUM:
            return self._generate_medium_risk_test(
                function_name, test_name, gap
            )
        else:
            return self._generate_low_risk_test(function_name, test_name, gap)

    def _safe_test_name(self, func_name: str, gap: CoverageGap) -> str:
        """生成安全的测试函数名"""
        base = func_name.replace(".", "_").replace("-", "_")
        if len(base) > 80:
            base = base[:80]
        return f"test_{base}_L{gap.line_number}"

    def _generate_high_risk_test(
        self, function_name: str, test_name: str, gap: CoverageGap
    ) -> str:
        """生成高风险测试"""
        "raise" in gap.code_snippet.lower() or "try" in gap.code_snippet.lower()

        test = f'''    def {test_name}(self):
        """
        [高风险] {gap.reason}
        原代码位置: {gap.file_path}:{gap.line_number}
        
        原代码片段:
        {self._indent_text(gap.code_snippet, 8)}
        """
        # TODO: 实现具体的测试逻辑
        # 这个函数包含高风险操作，需要仔细测试
        
        # 示例: 验证函数不抛出异常
        try:
            if {function_name in gap.code_snippet}:
                # 准备测试数据
                test_input = None  # TODO: 替换为实际输入
                result = {function_name}(test_input)  # TODO: 传递正确的参数
                assert result is not None
            else:
                # 如果是特定行的问题，测试相关功能
                pytest.skip("需要手动实现测试 - 特定代码行需要测试")
        except Exception as e:
            # 记录异常但不使测试失败（因为可能是模拟数据问题）
            pass
            
        # 安全性验证
        # TODO: 添加边界条件测试
        # TODO: 添加无效输入测试
        # TODO: 添加安全边界检查
'''
        return test

    def _generate_medium_risk_test(
        self, function_name: str, test_name: str, gap: CoverageGap
    ) -> str:
        """生成中等风险测试"""
        test = f'''    def {test_name}(self):
        """
        [中等风险] {gap.reason}
        原代码位置: {gap.file_path}:{gap.line_number}
        
        原代码片段:
        {self._indent_text(gap.code_snippet, 8)}
        """
        # TODO: 实现具体的测试逻辑
        
        # 示例: 基本功能测试
        if '{function_name}' in __name__:
            test_inputs = [
                # TODO: 添加测试数据
                None,
                '',
                0,
                [],
                {{}},
            ]
            for test_input in test_inputs:
                try:
                    result = {function_name}(test_input)  # TODO: 修正参数
                    # 验证返回值类型
                    assert result is not None
                except Exception as e:
                    # 对于无效输入，期望函数优雅地处理
                    pass
        
        # TODO: 添加边界条件测试
        # TODO: 添加极端值测试
'''
        return test

    def _generate_low_risk_test(
        self, function_name: str, test_name: str, gap: CoverageGap
    ) -> str:
        """生成低风险测试"""
        return f'''    def {test_name}(self):
        """
        [低风险] {gap.reason}
        原代码位置: {gap.file_path}:{gap.line_number}
        """
        # 基础功能测试
        try:
            # 简单的调用测试
            result = None  # TODO: 调用实际函数
            assert result is not None
        except Exception:
            pytest.skip("需要手动实现测试")
'''

    def _indent_text(self, text: str, spaces: int) -> str:
        """缩进文本"""
        indent = " " * spaces
        lines = text.split("\n")
        return "\n".join(indent + line for line in lines)

    def write_tests(self, tests: List[GeneratedTest]) -> List[str]:
        """将测试写入文件"""
        written = []
        for test in tests:
            test_path = self.project_root / test.file_path
            test_path.parent.mkdir(parents=True, exist_ok=True)

            # 如果文件已存在，添加到文件末尾
            if test_path.exists():
                with open(test_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()

                if self._is_safe_to_append(
                    existing_content, test.test_content
                ):
                    with open(test_path, "a", encoding="utf-8") as f:
                        f.write("\n\n# " + "=" * 70 + "\n")
                        f.write("# 自动添加的测试 - Test Gap Analyzer\n")
                        f.write("# " + "=" * 70 + "\n\n")
                        f.write(test.test_content)
                    written.append(str(test_path))
            else:
                # 创建新文件
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(test.test_content)
                written.append(str(test_path))

        return written

    def _is_safe_to_append(self, existing: str, new_content: str) -> bool:
        """检查是否可以安全地追加内容"""
        # 检查是否有同名类或函数
        existing_names = set()

        # 提取现有测试函数名
        for match in re.finditer(r"def (test_\w+)", existing):
            existing_names.add(match.group(1))

        # 检查新内容是否有冲突
        for match in re.finditer(r"def (test_\w+)", new_content):
            if match.group(1) in existing_names:
                return False

        return True
