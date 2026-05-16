#!/usr/bin/env python3
"""
审计日志分析工具
用于倒查修复失败根源

用法:
    python audit_analyzer.py --list              # 列出最近会话
    python audit_analyzer.py --session <ID>      # 分析指定会话
    python audit_analyzer.py --report            # 生成审计报告
    python audit_analyzer.py --failed            # 查看所有失败操作
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from core.audit_logger import OperationStatus, get_audit_logger


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def cmd_list_sessions(args):
    """列出最近会话"""
    print_header("最近修复会话")

    audit = get_audit_logger()
    sessions = audit.get_recent_sessions(args.count)

    if not sessions:
        print("暂无会话记录")
        return

    for i, session in enumerate(sessions, 1):
        sid = session.get("session_id", "unknown")[:20] + "..."
        start = session.get("start_time", "unknown")
        summary = session.get("summary", {})

        print(f"\n[{i}] 会话ID: {sid}")
        print(f"    开始时间: {start}")
        if summary:
            total = summary.get("total_operations", 0)
            failed = summary.get("failed_count", 0)
            success = summary.get("success_count", 0)
            print(f"    操作统计: 总计{total} | 成功{success} | 失败{failed}")


def cmd_analyze_session(args):
    """分析指定会话的失败根源"""
    audit = get_audit_logger()

    # 如果提供了完整ID，直接使用
    session_id = args.session_id

    # 否则尝试匹配部分ID
    if not session_id.endswith("..."):
        sessions = audit.get_recent_sessions(100)
        for s in sessions:
            if s.get("session_id", "").startswith(session_id):
                session_id = s["session_id"]
                break

    print_header(f"会话根源分析: {session_id[:30]}...")

    analysis = audit.analyze_failure_root_cause(session_id)

    if not analysis:
        print(f"未找到会话: {args.session_id}")
        return

    if analysis.get("status") == "no_failures":
        print("✓ 该会话中没有失败或拦截的操作")
        return

    print(f"\n会话统计:")
    print(f"  总操作数: {analysis.get('total_operations', 0)}")
    print(f"  失败数: {analysis.get('failed_count', 0)}")
    print(f"  拦截数: {analysis.get('blocked_count', 0)}")

    causes = analysis.get("root_causes", [])
    if causes:
        print(f"\n失败根源 ({len(causes)}个):")
        for i, cause in enumerate(causes, 1):
            print(f"\n  [{i}] 操作: {cause.get('operation_type')}")
            print(f"      Agent: {cause.get('agent_id')}")
            print(f"      路径: {cause.get('target_path')}")
            print(f"      时间: {cause.get('timestamp')}")
            if cause.get("error"):
                print(f"      错误: {cause.get('error')}")
            if cause.get("reason"):
                print(f"      原因: {cause.get('reason')}")

    recommendations = analysis.get("recommendations", [])
    if recommendations:
        print(f"\n修复建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")


def cmd_generate_report(args):
    """生成审计报告"""
    print_header("生成审计报告")

    audit = get_audit_logger()

    # 解析时间范围
    start_time = None
    end_time = None

    if args.days:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=args.days)

    output_path = Path(args.output) if args.output else None

    report_path = audit.generate_audit_report(
        start_time=start_time, end_time=end_time, output_path=output_path
    )

    print(f"✓ 报告已生成: {report_path}")

    # 显示报告摘要
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        stats = report.get("statistics", {})
        print(f"\n报告摘要:")
        print(f"  总操作数: {stats.get('total_operations', 0)}")
        print(f"  按状态: {stats.get('by_status', {})}")
        print(f"  失败操作: {len(stats.get('failed_operations', []))}")
        print(f"  拦截操作: {len(stats.get('blocked_operations', []))}")


def cmd_show_failed(args):
    """显示所有失败操作"""
    print_header("失败操作记录")

    audit = get_audit_logger()

    failed_ops = audit.query_operations(
        status=OperationStatus.FAILED, limit=args.count
    )

    if not failed_ops:
        print("暂无失败操作记录")
        return

    print(f"\n最近 {len(failed_ops)} 个失败操作:\n")

    for i, op in enumerate(failed_ops, 1):
        print(f"[{i}] 操作ID: {op.op_id}")
        print(f"    类型: {op.operation}")
        print(f"    Agent: {op.agent_id or 'N/A'}")
        print(f"    路径: {op.target_path or 'N/A'}")
        print(f"    时间: {op.timestamp}")
        print(f"    错误: {op.error_message or 'N/A'}")
        if op.details:
            print(f"    详情: {json.dumps(op.details, ensure_ascii=False)}")
        print()


def cmd_show_agent_history(args):
    """显示特定Agent的操作历史"""
    print_header(f"Agent 操作历史: {args.agent_id}")

    audit = get_audit_logger()

    ops = audit.query_operations(agent_id=args.agent_id, limit=args.count)

    if not ops:
        print(f"暂无 {args.agent_id} 的操作记录")
        return

    print(f"\n最近 {len(ops)} 个操作:\n")

    for i, op in enumerate(ops, 1):
        status_icon = (
            "✓"
            if op.status == "success"
            else "✗" if op.status == "failed" else "⚠"
        )
        print(f"[{i}] {status_icon} {op.operation}")
        print(f"    时间: {op.timestamp}")
        print(f"    路径: {op.target_path or 'N/A'}")
        print(f"    状态: {op.status}")
        if op.error_message:
            print(f"    错误: {op.error_message}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="审计日志分析工具 - 倒查修复失败根源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list                    # 列出最近10个会话
  %(prog)s --session abc123          # 分析指定会话
  %(prog)s --report --days 7         # 生成最近7天报告
  %(prog)s --failed                  # 查看所有失败操作
  %(prog)s --agent cursor --count 20 # 查看Cursor的最近20个操作
        """,
    )

    parser.add_argument("--list", action="store_true", help="列出最近会话")
    parser.add_argument(
        "--session", dest="session_id", metavar="ID", help="分析指定会话ID"
    )
    parser.add_argument("--report", action="store_true", help="生成审计报告")
    parser.add_argument("--failed", action="store_true", help="显示失败操作")
    parser.add_argument(
        "--agent",
        dest="agent_id",
        metavar="ID",
        help="显示指定Agent的操作历史",
    )

    parser.add_argument(
        "--count", type=int, default=10, help="显示数量 (默认: 10)"
    )
    parser.add_argument("--days", type=int, help="报告时间范围 (天)")
    parser.add_argument("--output", metavar="PATH", help="报告输出路径")

    args = parser.parse_args()

    # 如果没有参数，显示帮助
    if not any(
        [args.list, args.session_id, args.report, args.failed, args.agent_id]
    ):
        parser.print_help()
        return

    try:
        if args.list:
            cmd_list_sessions(args)
        elif args.session_id:
            cmd_analyze_session(args)
        elif args.report:
            cmd_generate_report(args)
        elif args.failed:
            cmd_show_failed(args)
        elif args.agent_id:
            cmd_show_agent_history(args)
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
