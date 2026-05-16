#!/usr/bin/env python3
"""
测试 GUI API 是否正常工作
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import AGENT_PATHS, RepairEngine

print("=" * 60)
print("测试 RepairEngine 扫描功能")
print("=" * 60)

engine = RepairEngine()

print(f"\n环境信息:")
print(f"  类型: {engine.env_detector.info.type}")
print(f"  显示名称: {engine.env_detector.info.type_display}")
print(f"  是否虚拟环境: {engine.env_detector.is_virtual_environment()}")

print(f"\n支持的工具 ({len(AGENT_PATHS)} 个):")
for agent_id, config in AGENT_PATHS.items():
    print(f"  - {config['icon']} {config['name']} ({agent_id})")

print(f"\n开始扫描...")
result = engine.scan_all()

print(f"\n扫描结果:")
print(f"  阶段: {result['current_phase']}")
print(f"  发现工具: {len([a for a in result['agents'] if a['installed']])}")

for agent in result["agents"]:
    if agent["installed"]:
        print(f"\n  ✓ {agent['icon']} {agent['name']}")
        print(f"    路径: {agent['path']}")
        print(f"    问题: {len(agent['issues'])} 个")
        for issue in agent["issues"]:
            print(f"      - {issue}")
    else:
        print(f"  ✗ {agent['icon']} {agent['name']} - 未安装")

print("\n" + "=" * 60)
print("扫描完成!")
print("=" * 60)
