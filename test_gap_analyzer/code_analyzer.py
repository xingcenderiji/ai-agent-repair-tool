"""
代码分析器 - 分析 Python 代码结构
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CodeFunction:
    """函数信息"""

    name: str
    start_line: int
    end_line: int
    parameters: List[str]
    is_async: bool = False
    decorators: List[str] = None
    complexity: int = 0


@dataclass
class FileAnalysis:
    """文件分析结果"""

    file_path: str
    functions: List[CodeFunction]
    imports: List[str]
    exports: List[str]
    complexity: int
    content: str = ""


class CodeAnalyzer:
    """Python 代码分析器"""

    def __init__(self):
        pass

    def analyze_file(self, file_path: str) -> Optional[FileAnalysis]:
        """分析单个文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"无法读取文件 {file_path}: {e}")
            return None

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"语法错误 {file_path}: {e}")
            return None

        # 提取函数
        functions = []
        imports = []
        exports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                params = [arg.arg for arg in node.args.args]
                is_async = isinstance(node, ast.AsyncFunctionDef)
                decorators = [
                    (
                        d.id
                        if isinstance(d, ast.Name)
                        else (
                            d.attr if isinstance(d, ast.Attribute) else str(d)
                        )
                    )
                    for d in node.decorator_list
                ]

                func = CodeFunction(
                    name=node.name,
                    start_line=node.lineno,
                    end_line=self._find_end_line(node, content),
                    parameters=params,
                    is_async=is_async,
                    decorators=decorators or [],
                    complexity=self._calculate_cyclomatic_complexity(node),
                )
                functions.append(func)
            elif isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    imports.append(f"{module}.{name.name}")

        # 找出导出的符号
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(
                        target, ast.Name
                    ) and not target.name.startswith("_"):
                        exports.append(target.name)
            elif (
                isinstance(node, ast.ClassDef)
                or isinstance(node, ast.FunctionDef)
                or isinstance(node, ast.AsyncFunctionDef)
            ):
                if not node.name.startswith("_"):
                    exports.append(node.name)

        # 计算整体复杂度
        total_complexity = sum(f.complexity for f in functions)

        return FileAnalysis(
            file_path=file_path,
            functions=functions,
            imports=imports,
            exports=exports,
            complexity=total_complexity,
            content=content,
        )

    def _find_end_line(self, node: ast.AST, content: str) -> int:
        """查找函数的结束行"""
        if hasattr(node, "end_lineno"):
            return node.end_lineno or node.lineno

        # 如果没有 end_lineno，手动查找
        lines = content.split("\n")
        current_line = node.lineno - 1
        indent_level = self._get_indent_level(lines[current_line])

        for i in range(current_line + 1, len(lines)):
            line = lines[i].rstrip()
            if line:
                line_indent = self._get_indent_level(line)
                if line_indent <= indent_level and not line.strip().startswith(
                    "#"
                ):
                    return i
        return len(lines)

    def _get_indent_level(self, line: str) -> int:
        """计算缩进级别"""
        level = 0
        for char in line:
            if char == " ":
                level += 1
            elif char == "\t":
                level += 4
            else:
                break
        return level

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1

        class ComplexityVisitor(ast.NodeVisitor):
            def visit_If(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_For(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_While(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_With(self, node):
                nonlocal complexity
                complexity += 1
                self.generic_visit(node)

            def visit_Try(self, node):
                nonlocal complexity
                complexity += len(node.handlers)
                self.generic_visit(node)

            def visit_BoolOp(self, node):
                nonlocal complexity
                complexity += len(node.values) - 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(node)
        return complexity

    def find_existing_tests(
        self, project_root: str, file_path: str
    ) -> List[str]:
        """查找现有测试文件"""
        src_path = Path(file_path)
        relative_path = src_path.relative_to(Path(project_root))
        base_name = relative_path.stem
        tests = []

        # 常见的测试文件模式
        test_patterns = [
            f"test_{base_name}.py",
            f"{base_name}_test.py",
            f"tests/test_{base_name}.py",
            f"tests/{base_name}_test.py",
        ]

        project = Path(project_root)
        for pattern in test_patterns:
            test_file = project / pattern
            if test_file.exists():
                tests.append(str(test_file))

        return tests

    def has_function_test(
        self, test_files: List[str], function_name: str
    ) -> bool:
        """检查某个函数是否有测试"""
        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查测试函数是否存在
                if f"test_{function_name}" in content:
                    return True

                # 检查函数是否在测试中被调用
                if re.search(rf"\b{function_name}\s*\(", content):
                    return True

            except Exception:
                continue
        return False
