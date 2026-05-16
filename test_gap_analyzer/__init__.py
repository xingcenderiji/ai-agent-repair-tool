"""
Test Gap Analyzer - 自动化测试缺口分析工具
用于加固回归测试安全网
"""

__version__ = "1.0.0"
__author__ = "Test Gap Analyzer Team"

from .analyzer import TestGapAnalyzer
from .detector import GapDetector
from .generator import TestGenerator

__all__ = ["TestGapAnalyzer", "GapDetector", "TestGenerator"]
