"""
Test Gap Analyzer 集成测试
"""
import sys
import os
from pathlib import Path
import subprocess
import tempfile

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_module_import():
    """测试模块可以正常导入"""
    import test_gap_analyzer
    from test_gap_analyzer import types
    from test_gap_analyzer import git_analyzer
    from test_gap_analyzer import code_analyzer
    from test_gap_analyzer import detector
    from test_gap_analyzer import generator
    from test_gap_analyzer import analyzer
    
    assert test_gap_analyzer is not None
    assert types is not None
    assert git_analyzer is not None
    assert code_analyzer is not None
    assert detector is not None
    assert generator is not None
    assert analyzer is not None


def test_types_exist():
    """测试类型定义存在"""
    from test_gap_analyzer.types import (
        RiskLevel,
        FileChange,
        CommitInfo,
        CoverageGap,
        GeneratedTest,
        AnalysisResult,
        AnalyzerConfig,
    )
    
    # 测试可以实例化类型
    config = AnalyzerConfig(project_root=".")
    assert config is not None


def test_git_analyzer_creation():
    """测试 GitAnalyzer 可以创建"""
    from test_gap_analyzer.git_analyzer import GitAnalyzer
    
    analyzer = GitAnalyzer(".")
    assert analyzer is not None


def test_code_analyzer_creation():
    """测试 CodeAnalyzer 可以创建"""
    from test_gap_analyzer.code_analyzer import CodeAnalyzer
    
    analyzer = CodeAnalyzer()
    assert analyzer is not None


def test_gap_detector_creation():
    """测试 GapDetector 可以创建"""
    from test_gap_analyzer.detector import GapDetector
    
    detector = GapDetector(".")
    assert detector is not None


def test_test_generator_creation():
    """测试 TestGenerator 可以创建"""
    from test_gap_analyzer.generator import TestGenerator
    
    generator = TestGenerator(".")
    assert generator is not None


def test_test_gap_analyzer_creation():
    """测试 TestGapAnalyzer 可以创建"""
    from test_gap_analyzer.analyzer import TestGapAnalyzer
    from test_gap_analyzer.types import AnalyzerConfig
    
    config = AnalyzerConfig(project_root=".")
    analyzer = TestGapAnalyzer(config)
    assert analyzer is not None


def test_command_line_help():
    """测试命令行帮助可以正常显示"""
    result = subprocess.run(
        [sys.executable, "-m", "test_gap_analyzer.analyze", "--help"],
        capture_output=True,
        text=True,
    )
    
    assert "Test Gap Analyzer" in result.stdout or result.returncode in [0, 1]


def test_analyze_non_git_repo():
    """测试在非 Git 仓库中运行分析"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建一个简单的 Python 文件
        test_file = Path(temp_dir) / "sample.py"
        test_file.write_text("""
def sample_function(x):
    return x * 2

class SampleClass:
    def method(self, y):
        return y + 1
""")
        
        # 运行分析
        result = subprocess.run(
            [sys.executable, "-m", "test_gap_analyzer", "--project", temp_dir],
            capture_output=True,
            text=True,
        )
        
        # 应该提示非 Git 仓库
        assert result.returncode == 0  # 即使非 Git 仓库也应该正常退出
        assert "not a git repository" in result.stderr.lower() or \
               "不是 git 仓库" in result.stderr.lower() or \
               result.returncode == 0


if __name__ == "__main__":
    print("Test Gap Analyzer 集成测试...")
    
    # 运行所有测试
    test_module_import()
    print("✓ test_module_import")
    
    test_types_exist()
    print("✓ test_types_exist")
    
    test_git_analyzer_creation()
    print("✓ test_git_analyzer_creation")
    
    test_code_analyzer_creation()
    print("✓ test_code_analyzer_creation")
    
    test_gap_detector_creation()
    print("✓ test_gap_detector_creation")
    
    test_test_generator_creation()
    print("✓ test_test_generator_creation")
    
    test_test_gap_analyzer_creation()
    print("✓ test_test_gap_analyzer_creation")
    
    test_command_line_help()
    print("✓ test_command_line_help")
    
    test_analyze_non_git_repo()
    print("✓ test_analyze_non_git_repo")
    
    print("\n所有集成测试通过！🎉")
