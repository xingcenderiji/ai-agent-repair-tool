"""
测试缺口分析器 - 主入口
"""

import sys
from typing import List

from .detector import GapDetector
from .generator import TestGenerator
from .git_analyzer import GitAnalyzer
from .types import AnalysisResult, AnalyzerConfig, RiskLevel


class TestGapAnalyzer:
    """测试缺口分析器"""

    def __init__(self, config: AnalyzerConfig):
        self.config = config
        self.git_analyzer = GitAnalyzer(config.project_root)
        self.gap_detector = GapDetector(config.project_root)
        self.test_generator = TestGenerator(
            config.project_root, config.test_dir
        )

    def analyze(self) -> AnalysisResult:
        """分析项目的测试缺口"""
        result = AnalysisResult()

        is_git = self.git_analyzer.is_git_repo()

        if not is_git:
            print("⚠️  警告: 不是 Git 仓库，无法分析提交历史")
            result.recommendations.append(
                "建议初始化 Git 仓库以便跟踪代码变更"
            )
            return result

        # 获取最近的提交
        commits = self.git_analyzer.get_recent_commits(self.config.max_commits)
        result.analyzed_commits = len(commits)

        if len(commits) == 0:
            print("没有找到最近的提交")
            return result

        print(f"📊 正在分析 {len(commits)} 个提交...")

        # 检测缺口
        gaps = self.gap_detector.detect_gaps(commits)
        result.detected_gaps = gaps

        # 生成测试
        tests = self.test_generator.generate_tests(gaps)
        result.generated_tests = tests

        # 生成建议
        self._generate_recommendations(result)

        return result

    def _generate_recommendations(self, result: AnalysisResult):
        """生成建议"""
        high_risk = [
            g for g in result.detected_gaps if g.risk_level == RiskLevel.HIGH
        ]
        medium_risk = [
            g for g in result.detected_gaps if g.risk_level == RiskLevel.MEDIUM
        ]

        if high_risk:
            result.recommendations.append(
                f"⚠️  发现 {len(high_risk)} 个高风险测试缺口，强烈建议补充测试"
            )

        if medium_risk:
            result.recommendations.append(
                f"📝 发现 {len(medium_risk)} 个中等风险测试缺口，建议补充测试"
            )

        if len(result.generated_tests) > 0:
            result.recommendations.append(
                f"✅ 已生成 {len(result.generated_tests)} 个测试文件，请检查并完善测试逻辑"
            )

    def print_report(self, result: AnalysisResult):
        """打印分析报告"""
        print("\n" + "=" * 80)
        print("📊 测试缺口分析报告")
        print("=" * 80)
        print(f"\n📈 分析统计:")
        print(f"  提交数量: {result.analyzed_commits}")
        print(f"  发现缺口: {len(result.detected_gaps)}")
        print(f"  生成测试: {len(result.generated_tests)}")

        if result.detected_gaps:
            high_risk = [
                g
                for g in result.detected_gaps
                if g.risk_level == RiskLevel.HIGH
            ]
            medium_risk = [
                g
                for g in result.detected_gaps
                if g.risk_level == RiskLevel.MEDIUM
            ]
            low_risk = [
                g
                for g in result.detected_gaps
                if g.risk_level == RiskLevel.LOW
            ]

            print(f"  高风险: {len(high_risk)}")
            print(f"  中风险: {len(medium_risk)}")
            print(f"  低风险: {len(low_risk)}")

            if high_risk:
                print(f"\n🔴 高风险缺口 (前 {min(5, len(high_risk))} 个):")
                for i, gap in enumerate(high_risk[:5], 1):
                    print(f"  {i}. {gap.file_path}:{gap.line_number}")
                    print(f"     {gap.reason}")

        if result.generated_tests:
            print(f"\n📝 生成的测试文件:")
            for test in result.generated_tests:
                print(f"  - {test.file_path}")
                print(f"    目标函数: {test.target_function}")

        if result.recommendations:
            print(f"\n💡 建议:")
            for rec in result.recommendations:
                print(f"  {rec}")

        print("\n" + "=" * 80)

    def write_tests(self, result: AnalysisResult) -> List[str]:
        """将生成的测试写入文件"""
        return self.test_generator.write_tests(result.generated_tests)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="测试缺口分析工具 - 自动检测并补充测试覆盖",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析当前项目的最近 10 个提交
  python -m test_gap_analyzer.analyze
  
  # 分析特定目录，最近 20 个提交
  python -m test_gap_analyzer.analyze --project /path/to/project --commits 20
  
  # 分析并生成测试文件
  python -m test_gap_analyzer.analyze --write
        """,
    )

    parser.add_argument(
        "--project", "-p", default=".", help="项目根目录 (默认: 当前目录)"
    )
    parser.add_argument(
        "--commits",
        "-c",
        type=int,
        default=10,
        help="分析的最近提交数量 (默认: 10)",
    )
    parser.add_argument(
        "--test-dir", "-t", default="tests", help="测试文件目录 (默认: tests)"
    )
    parser.add_argument(
        "--write", "-w", action="store_true", help="是否将生成的测试写入文件"
    )
    parser.add_argument(
        "--include-low-risk",
        "-l",
        action="store_true",
        help="包含低风险的测试缺口",
    )
    parser.add_argument(
        "--fail-on-high-risk",
        action="store_true",
        help="发现高风险缺口时返回非零退出码",
    )

    args = parser.parse_args()

    # 创建配置
    config = AnalyzerConfig(
        project_root=args.project,
        max_commits=args.commits,
        test_dir=args.test_dir,
    )

    # 运行分析
    analyzer = TestGapAnalyzer(config)
    result = analyzer.analyze()

    # 打印报告
    analyzer.print_report(result)

    # 写入测试
    if args.write and result.generated_tests:
        written = analyzer.write_tests(result)
        if written:
            print(f"\n✓ 已写入 {len(written)} 个测试文件:")
            for f in written:
                print(f"  - {f}")

    # 退出码
    has_high_risk = any(
        g.risk_level == RiskLevel.HIGH for g in result.detected_gaps
    )
    if args.fail_on_high_risk and has_high_risk:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
