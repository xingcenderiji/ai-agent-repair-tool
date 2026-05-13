#!/usr/bin/env python3
"""
AI Agent 修复工具 - 桌面操控界面
提供Web界面操控修复流程，引导式操作，确认每一步
新增：配置扫描预览功能
"""

import os
import sys
import json
import shutil
import platform
import stat
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field, asdict
import urllib.parse

# Windows 终端强制 UTF-8 编码
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from agent_registry import AGENT_PATHS
from core.config_scanner import ConfigScanner, AgentConfigScan


# ============================================================
# 数据模型
# ============================================================

@dataclass
class AgentStatus:
    agent_id: str
    name: str
    icon: str
    path: Optional[str] = None
    installed: bool = False
    issues: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, scanning, scanned, fixing, fixed, error
    config_scan: Optional[Dict] = None  # 配置扫描结果

@dataclass
class RepairStep:
    step_id: str
    name: str
    description: str
    status: str = "pending"  # pending, running, success, warning, error, skipped
    detail: str = ""
    requires_confirm: bool = False

@dataclass
class SessionState:
    current_phase: str = "idle"  # idle, scanning, preview, review, confirming, fixing, done
    agents: List[Dict] = field(default_factory=list)
    steps: List[Dict] = field(default_factory=list)
    current_step: int = 0
    log: List[str] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)
    config_scan_results: Dict[str, Dict] = field(default_factory=dict)  # 配置扫描结果
    scan_report_path: Optional[str] = None  # 扫描报告路径


# ============================================================
# 修复引擎
# ============================================================

class RepairEngine:
    def __init__(self):
        self.session = SessionState()
        self._lock = threading.Lock()
        self.config_scanner = ConfigScanner()

    def get_os(self):
        system = platform.system().lower()
        if system == "windows": return "win"
        elif system == "darwin": return "mac"
        return "linux"

    def expand_path(self, path):
        if not path or not path.strip():
            return Path.cwd()
        return Path(os.path.expandvars(os.path.expanduser(path.strip())))

    def find_agent(self, agent_id):
        config = AGENT_PATHS.get(agent_id)
        if not config:
            return None
        os_type = self.get_os()
        for path_template in config["paths"].get(os_type, []):
            try:
                path = self.expand_path(path_template)
                if path.exists():
                    return path
            except (OSError, ValueError):
                continue
        return None

    def check_config(self, agent_path):
        issues = []
        for cf in ["settings.json", "config.json", "config.yaml"]:
            config_file = agent_path / cf
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        if cf.endswith('.json'):
                            json.load(f)
                except json.JSONDecodeError:
                    issues.append(f"配置文件损坏: {cf}")
                except UnicodeDecodeError:
                    issues.append(f"配置文件编码错误: {cf}")
                except PermissionError:
                    issues.append(f"配置文件无读取权限: {cf}")
                except OSError as e:
                    issues.append(f"配置文件读取错误: {e.errno}): {cf}")
        return issues

    def check_cache(self, agent_path):
        issues = []
        for cd in ["cache", "Cache", "temp", "Temp", "CachedData"]:
            cache_path = agent_path / cd
            if cache_path.exists():
                try:
                    total_size = 0
                    for f in cache_path.rglob('*'):
                        if f.is_file() and not f.is_symlink():
                            try:
                                total_size += f.stat().st_size
                            except OSError:
                                pass
                    size_mb = total_size / (1024 * 1024)
                    if size_mb > 500:
                        issues.append(f"缓存过大: {size_mb:.1f}MB")
                except PermissionError:
                    issues.append(f"缓存目录无访问权限: {cd}")
        return issues

    def scan_all(self):
        """扫描所有Agent（健康检查）"""
        self.session.current_phase = "scanning"
        self.session.agents = []
        self.session.log = []

        for agent_id, config in AGENT_PATHS.items():
            status = AgentStatus(
                agent_id=agent_id,
                name=config["name"],
                icon=config["icon"],
                status="scanning"
            )
            self.session.log.append(f"正在扫描 {config['name']}...")

            path = self.find_agent(agent_id)
            if path:
                status.installed = True
                status.path = str(path)
                issues = []
                issues.extend(self.check_config(path))
                issues.extend(self.check_cache(path))
                status.issues = issues
                status.status = "scanned"
                if issues:
                    self.session.log.append(f"  发现 {len(issues)} 个问题")
                else:
                    self.session.log.append(f"  状态正常")
            else:
                status.status = "scanned"
                self.session.log.append(f"  未安装")

            self.session.agents.append(asdict(status))

        has_issues = any(a["issues"] for a in self.session.agents if a["installed"])
        # 扫描完成后进入preview阶段（配置预览）
        self.session.current_phase = "preview" if has_issues else "done"
        return asdict(self.session)

    def scan_config_details(self):
        """详细扫描配置信息"""
        self.session.log.append("\n开始详细配置扫描...")
        
        # 使用ConfigScanner扫描所有Agent的详细配置
        results = self.config_scanner.scan_all_agents(AGENT_PATHS)
        
        # 转换为字典存储
        self.session.config_scan_results = {
            agent_id: result.to_dict()
            for agent_id, result in results.items()
            if result.is_installed  # 只保存已安装的
        }
        
        # 更新agents中的config_scan
        for agent in self.session.agents:
            if agent["agent_id"] in self.session.config_scan_results:
                agent["config_scan"] = self.session.config_scan_results[agent["agent_id"]]
        
        # 统计信息
        installed_count = len(self.session.config_scan_results)
        total_plugins = sum(
            r.get("total_plugins", 0) 
            for r in self.session.config_scan_results.values()
        )
        total_mcp = sum(
            len(r.get("mcp_servers", [])) 
            for r in self.session.config_scan_results.values()
        )
        
        self.session.log.append(f"  已扫描 {installed_count} 个Agent")
        self.session.log.append(f"  发现 {total_plugins} 个插件")
        self.session.log.append(f"  发现 {total_mcp} 个MCP服务器")
        
        return asdict(self.session)

    def export_scan_report(self, format_type="json"):
        """导出扫描报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path.home() / ".ai_agent_repair" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        if format_type == "json":
            report_path = report_dir / f"config_scan_{timestamp}.json"
            self.config_scanner.export_to_json(report_path)
        else:
            report_path = report_dir / f"config_scan_{timestamp}.md"
            self.config_scanner.export_to_markdown(report_path)
        
        self.session.scan_report_path = str(report_path)
        self.session.log.append(f"扫描报告已保存: {report_path}")
        return str(report_path)

    def build_repair_plan(self):
        self.session.steps = []
        self.session.current_step = 0

        for agent in self.session.agents:
            if not agent["issues"]:
                continue

            agent_name = agent["name"]
            agent_id = agent["agent_id"]

            # Step 1: 备份
            self.session.steps.append(asdict(RepairStep(
                step_id=f"{agent_id}_backup",
                name=f"备份 {agent_name}",
                description=f"将 {agent_name} 的配置文件备份到安全位置",
                requires_confirm=True
            )))

            # Step 2: 清理缓存
            cache_issues = [i for i in agent["issues"] if "缓存" in i]
            if cache_issues:
                self.session.steps.append(asdict(RepairStep(
                    step_id=f"{agent_id}_cache",
                    name=f"清理 {agent_name} 缓存",
                    description=f"清理过大的缓存文件: {', '.join(cache_issues)}",
                    requires_confirm=True
                )))

            # Step 3: 修复配置
            config_issues = [i for i in agent["issues"] if "配置" in i]
            if config_issues:
                self.session.steps.append(asdict(RepairStep(
                    step_id=f"{agent_id}_config",
                    name=f"修复 {agent_name} 配置",
                    description=f"修复损坏的配置文件: {', '.join(config_issues)}",
                    requires_confirm=True
                )))

            # Step 4: 验证
            self.session.steps.append(asdict(RepairStep(
                step_id=f"{agent_id}_verify",
                name=f"验证 {agent_name}",
                description="重新检查确认所有问题已修复",
                requires_confirm=False
            )))

        self.session.current_phase = "confirming"
        return asdict(self.session)

    def execute_step(self, step_index):
        if step_index >= len(self.session.steps):
            return {"error": "步骤不存在"}

        step = self.session.steps[step_index]
        step["status"] = "running"
        self.session.current_step = step_index

        agent_id = step["step_id"].rsplit("_", 1)[0]
        agent = next((a for a in self.session.agents if a["agent_id"] == agent_id), None)
        if not agent:
            step["status"] = "skipped"
            return asdict(self.session)

        agent_path = Path(agent["path"])

        try:
            if "_backup" in step["step_id"]:
                backup_dir = Path.home() / ".ai_agent_backups"
                backup_dir.mkdir(exist_ok=True)
                backup_name = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = backup_dir / backup_name
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(
                    agent_path, backup_path,
                    ignore=shutil.ignore_patterns('cache', 'Cache', 'temp', 'Temp')
                )
                step["status"] = "success"
                step["detail"] = f"备份已保存: {backup_path}"
                self.session.log.append(f"  ✓ {agent['name']} 备份完成")

            elif "_cache" in step["step_id"]:
                cleaned = 0
                for cd in ["cache", "Cache", "temp", "Temp", "CachedData"]:
                    cache_path = agent_path / cd
                    if cache_path.exists():
                        for item in cache_path.iterdir():
                            try:
                                if item.is_file() or item.is_symlink():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item, onerror=self._remove_readonly)
                                cleaned += 1
                            except:
                                pass
                step["status"] = "success"
                step["detail"] = f"已清理 {cleaned} 个缓存项"
                self.session.log.append(f"  ✓ {agent['name']} 缓存清理完成")

            elif "_config" in step["step_id"]:
                fixed = 0
                for cf in ["settings.json", "config.json"]:
                    config_file = agent_path / cf
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                json.load(f)
                        except json.JSONDecodeError:
                            broken = config_file.with_suffix('.json.broken')
                            shutil.copy2(config_file, broken)
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump({"version": "1.0.0", "settings": {}}, f, indent=2)
                            fixed += 1
                step["status"] = "success"
                step["detail"] = f"已修复 {fixed} 个配置文件"
                self.session.log.append(f"  ✓ {agent['name']} 配置修复完成")

            elif "_verify" in step["step_id"]:
                issues = []
                issues.extend(self.check_config(agent_path))
                issues.extend(self.check_cache(agent_path))
                if issues:
                    step["status"] = "warning"
                    step["detail"] = f"仍有 {len(issues)} 个问题: {', '.join(issues)}"
                    self.session.log.append(f"  ⚠ {agent['name']} 验证: 仍有问题")
                else:
                    step["status"] = "success"
                    step["detail"] = "所有问题已修复"
                    self.session.log.append(f"  ✓ {agent['name']} 验证通过")

        except Exception as e:
            step["status"] = "error"
            step["detail"] = str(e)
            self.session.log.append(f"  ✗ 错误: {e}")

        # 检查是否所有步骤完成
        if all(s["status"] in ("success", "warning", "skipped") for s in self.session.steps):
            self.session.current_phase = "done"
            success = sum(1 for s in self.session.steps if s["status"] == "success")
            total = len(self.session.steps)
            self.session.summary = {
                "total_steps": total,
                "success": success,
                "warnings": sum(1 for s in self.session.steps if s["status"] == "warning"),
                "errors": sum(1 for s in self.session.steps if s["status"] == "error"),
            }

        return asdict(self.session)

    def execute_all(self):
        for i in range(len(self.session.steps)):
            self.execute_step(i)
        return asdict(self.session)

    def get_state(self):
        return asdict(self.session)

    def _remove_readonly(self, func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)


# ============================================================
# Web 服务器
# ============================================================

engine = RepairEngine()

class RepairHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def log_message(self, format, *args):
        pass  # 静默HTTP日志

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(PAGE_HTML.encode("utf-8"))
        elif parsed.path == "/api/state":
            self._json_response(engine.get_state())
        elif parsed.path == "/api/scan":
            threading.Thread(target=self._scan, daemon=True).start()
            self._json_response({"status": "scanning_started"})
        elif parsed.path == "/api/scan-config":
            threading.Thread(target=self._scan_config, daemon=True).start()
            self._json_response({"status": "config_scan_started"})
        elif parsed.path == "/api/export-report":
            format_type = urllib.parse.parse_qs(parsed.query).get("format", ["json"])[0]
            path = engine.export_scan_report(format_type)
            self._json_response({"status": "exported", "path": path})
        elif parsed.path == "/api/plan":
            state = engine.build_repair_plan()
            self._json_response(state)
        elif parsed.path == "/api/execute-step":
            idx = int(urllib.parse.parse_qs(parsed.query).get("index", ["0"])[0])
            state = engine.execute_step(idx)
            self._json_response(state)
        elif parsed.path == "/api/execute-all":
            threading.Thread(target=self._execute_all, daemon=True).start()
            self._json_response({"status": "fixing_started"})
        elif parsed.path.startswith("/api/"):
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/scan":
            threading.Thread(target=self._scan, daemon=True).start()
            self._json_response({"status": "scanning_started"})
        elif parsed.path == "/api/scan-config":
            threading.Thread(target=self._scan_config, daemon=True).start()
            self._json_response({"status": "config_scan_started"})
        elif parsed.path == "/api/execute-all":
            threading.Thread(target=self._execute_all, daemon=True).start()
            self._json_response({"status": "fixing_started"})
        else:
            self.send_error(404)

    def _scan(self):
        time.sleep(0.5)  # 模拟扫描延迟
        engine.scan_all()

    def _scan_config(self):
        time.sleep(0.3)
        engine.scan_config_details()

    def _execute_all(self):
        engine.session.current_phase = "fixing"
        for i in range(len(engine.session.steps)):
            engine.session.steps[i]["status"] = "running"
            time.sleep(0.3)
            engine.execute_step(i)

    def _json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))


# ============================================================
# 界面 HTML
# ============================================================

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agent 智能修复工具</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
  --bg: #0c0c14;
  --bg2: #13131f;
  --card: #1a1a2e;
  --card-hover: #22223a;
  --border: #2a2a44;
  --accent: #00e5a0;
  --accent2: #00b8d4;
  --danger: #ff5252;
  --warning: #ffab40;
  --success: #69f0ae;
  --text: #e8e8f0;
  --text2: #8888a8;
  --text3: #55556a;
  --radius: 12px;
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: 'Noto Sans SC', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
}

/* 背景效果 */
body::before {
  content: '';
  position: fixed;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(ellipse at 30% 20%, rgba(0,229,160,0.04) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 80%, rgba(0,184,212,0.03) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.container {
  position: relative;
  z-index: 1;
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px;
}

/* 头部 */
.header {
  text-align: center;
  margin-bottom: 48px;
}

.header h1 {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}

.header p {
  color: var(--text2);
  font-size: 14px;
}

.header .badge {
  display: inline-block;
  margin-top: 12px;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  background: rgba(0,229,160,0.1);
  color: var(--accent);
  border: 1px solid rgba(0,229,160,0.2);
}

/* 流程指示器 */
.flow-indicator {
  display: flex;
  justify-content: center;
  gap: 0;
  margin-bottom: 40px;
  padding: 0 20px;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flow-dot {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  background: var(--card);
  border: 2px solid var(--border);
  color: var(--text3);
  transition: all 0.4s;
  font-family: 'JetBrains Mono', monospace;
}

.flow-dot.active {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(0,229,160,0.1);
  box-shadow: 0 0 20px rgba(0,229,160,0.15);
}

.flow-dot.done {
  border-color: var(--success);
  color: var(--bg);
  background: var(--success);
}

.flow-line {
  width: 40px; height: 2px;
  background: var(--border);
  transition: background 0.4s;
}

.flow-line.done { background: var(--success); }
.flow-line.active { background: linear-gradient(90deg, var(--success), var(--accent)); }

.flow-label {
  font-size: 11px;
  color: var(--text3);
  margin-top: 6px;
  text-align: center;
}

.flow-label.active { color: var(--accent); }
.flow-label.done { color: var(--success); }

/* 卡片 */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 16px;
  transition: border-color 0.3s;
}

.card:hover { border-color: rgba(0,229,160,0.3); }

.card-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Agent 列表 */
.agent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 8px;
  transition: all 0.3s;
  cursor: pointer;
}

.agent-item:hover {
  border-color: rgba(0,229,160,0.3);
}

.agent-item.has-issues {
  border-color: rgba(255,82,82,0.3);
  background: rgba(255,82,82,0.03);
}

.agent-item.ok {
  border-color: rgba(105,240,174,0.2);
}

.agent-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-icon {
  font-size: 22px;
  width: 36px;
  text-align: center;
}

.agent-name { font-weight: 500; font-size: 14px; }
.agent-path { font-size: 11px; color: var(--text3); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }

.agent-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.agent-badge.ok { background: rgba(105,240,174,0.1); color: var(--success); }
.agent-badge.error { background: rgba(255,82,82,0.1); color: var(--danger); }
.agent-badge.not-installed { background: rgba(85,85,106,0.15); color: var(--text3); }

/* 问题列表 */
.issue-list {
  margin-top: 10px;
  padding-left: 48px;
}

.issue-item {
  font-size: 12px;
  color: var(--danger);
  padding: 3px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.issue-item::before {
  content: '';
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--danger);
  flex-shrink: 0;
}

/* 配置预览 */
.config-preview {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-top: 12px;
  font-size: 12px;
}

.config-section {
  margin-bottom: 16px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.config-section-title {
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 8px;
  font-size: 13px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.config-item:last-child {
  border-bottom: none;
}

.config-label {
  color: var(--text2);
}

.config-value {
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
}

/* 修复步骤 */
.step-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 8px;
  transition: all 0.3s;
}

.step-item.running {
  border-color: var(--accent);
  background: rgba(0,229,160,0.03);
}

.step-item.success { border-color: rgba(105,240,174,0.3); }
.step-item.error { border-color: rgba(255,82,82,0.3); }
.step-item.warning { border-color: rgba(255,171,64,0.3); }

.step-num {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  background: var(--card);
  border: 2px solid var(--border);
  color: var(--text3);
  flex-shrink: 0;
}

.step-item.running .step-num { border-color: var(--accent); color: var(--accent); animation: pulse 1.5s infinite; }
.step-item.success .step-num { border-color: var(--success); color: var(--bg); background: var(--success); }
.step-item.error .step-num { border-color: var(--danger); color: var(--bg); background: var(--danger); }
.step-item.warning .step-num { border-color: var(--warning); color: var(--bg); background: var(--warning); }

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0,229,160,0.3); }
  50% { box-shadow: 0 0 0 8px rgba(0,229,160,0); }
}

.step-content { flex: 1; }
.step-name { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.step-desc { font-size: 12px; color: var(--text2); margin-bottom: 6px; }
.step-detail { font-size: 11px; font-family: 'JetBrains Mono', monospace; color: var(--text3); }

.step-confirm {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

/* 按钮 */
.btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Noto Sans SC', sans-serif;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: var(--bg);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0,229,160,0.3);
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: var(--card);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }

.btn-sm {
  padding: 6px 14px;
  font-size: 12px;
  border-radius: 6px;
}

.btn-danger {
  background: rgba(255,82,82,0.1);
  color: var(--danger);
  border: 1px solid rgba(255,82,82,0.2);
}

.btn-danger:hover { background: rgba(255,82,82,0.2); }

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
  flex-wrap: wrap;
}

/* 日志 */
.log-panel {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.8;
  color: var(--text2);
}

.log-panel::-webkit-scrollbar { width: 4px; }
.log-panel::-webkit-scrollbar-track { background: transparent; }
.log-panel::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.log-line { white-space: pre-wrap; word-break: break-all; }
.log-line.success { color: var(--success); }
.log-line.error { color: var(--danger); }
.log-line.warning { color: var(--warning); }

/* 摘要 */
.summary {
  text-align: center;
  padding: 32px;
}

.summary-icon { font-size: 48px; margin-bottom: 16px; }
.summary-title { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.summary-desc { color: var(--text2); font-size: 14px; margin-bottom: 24px; }

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-item { text-align: center; }
.stat-num { font-size: 28px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.stat-label { font-size: 12px; color: var(--text2); margin-top: 4px; }

/* 隐藏 */
.hidden { display: none !important; }

/* 确认对话框 */
.confirm-box {
  background: rgba(0,229,160,0.05);
  border: 1px solid rgba(0,229,160,0.2);
  border-radius: 10px;
  padding: 16px;
  margin: 16px 0;
}

.confirm-box p {
  font-size: 13px;
  color: var(--text2);
  margin-bottom: 12px;
}

.confirm-actions {
  display: flex;
  gap: 8px;
}

/* 加载动画 */
.spinner {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 响应式 */
@media (max-width: 640px) {
  .container { padding: 20px 16px; }
  .header h1 { font-size: 22px; }
  .flow-line { width: 25px; }
  .summary-stats { gap: 20px; }
}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>AI Agent 智能修复工具</h1>
    <p>全自动扫描、诊断、修复 AI 开发工具问题</p>
    <span class="badge" id="systemInfo">检测中...</span>
  </div>

  <!-- 流程指示器 -->
  <div class="flow-indicator">
    <div style="text-align:center">
      <div class="flow-dot active" id="fd1">1</div>
      <div class="flow-label active" id="fl1">扫描</div>
    </div>
    <div class="flow-line" id="fline1"></div>
    <div style="text-align:center">
      <div class="flow-dot" id="fd2">2</div>
      <div class="flow-label" id="fl2">预览</div>
    </div>
    <div class="flow-line" id="fline2"></div>
    <div style="text-align:center">
      <div class="flow-dot" id="fd3">3</div>
      <div class="flow-label" id="fl3">审查</div>
    </div>
    <div class="flow-line" id="fline3"></div>
    <div style="text-align:center">
      <div class="flow-dot" id="fd4">4</div>
      <div class="flow-label" id="fl4">确认</div>
    </div>
    <div class="flow-line" id="fline4"></div>
    <div style="text-align:center">
      <div class="flow-dot" id="fd5">5</div>
      <div class="flow-label" id="fl5">修复</div>
    </div>
    <div class="flow-line" id="fline5"></div>
    <div style="text-align:center">
      <div class="flow-dot" id="fd6">6</div>
      <div class="flow-label" id="fl6">完成</div>
    </div>
  </div>

  <!-- Phase 1: 扫描 -->
  <div id="phase-scan">
    <div class="card">
      <div class="card-title">🔍 扫描 Agent 安装状态</div>
      <p style="font-size:13px;color:var(--text2);margin-bottom:16px;">
        点击下方按钮开始扫描，工具将自动检测已安装的 AI 开发工具及其健康状态。
      </p>
      <div class="actions">
        <button class="btn btn-primary" id="btnScan" onclick="startScan()">开始扫描</button>
      </div>
    </div>
    <div id="scanResults" class="hidden"></div>
    <div id="logPanel" class="log-panel hidden"></div>
  </div>

  <!-- Phase 2: 配置预览 -->
  <div id="phase-preview" class="hidden">
    <div class="card">
      <div class="card-title">📋 配置信息预览</div>
      <p style="font-size:13px;color:var(--text2);margin-bottom:16px;">
        正在读取各AI工具的详细配置信息，包括插件、服务器、技能等。
      </p>
      <div class="actions">
        <button class="btn btn-secondary" onclick="startScan()">重新扫描</button>
        <button class="btn btn-primary" id="btnScanConfig" onclick="startConfigScan()">
          <span class="spinner hidden" id="configSpinner"></span> 详细配置扫描
        </button>
      </div>
    </div>
    <div id="configPreview" class="hidden"></div>
    <div id="previewLogPanel" class="log-panel hidden"></div>
  </div>

  <!-- Phase 3: 审查 -->
  <div id="phase-review" class="hidden">
    <div class="card">
      <div class="card-title">📊 扫描结果审查</div>
      <div id="reviewContent"></div>
    </div>
    <div class="actions">
      <button class="btn btn-secondary" onclick="startScan()">返回扫描</button>
      <button class="btn btn-secondary" onclick="exportReport('json')">导出JSON</button>
      <button class="btn btn-secondary" onclick="exportReport('markdown')">导出Markdown</button>
      <button class="btn btn-primary" id="btnPlan" onclick="buildPlan()">查看修复方案</button>
    </div>
  </div>

  <!-- Phase 4: 确认 -->
  <div id="phase-confirm" class="hidden">
    <div class="card">
      <div class="card-title">✅ 修复方案确认</div>
      <p style="font-size:13px;color:var(--text2);margin-bottom:16px;">
        以下是建议的修复步骤，请确认后执行。修复前会自动创建备份。
      </p>
      <div id="stepsList"></div>
    </div>
    <div class="actions">
      <button class="btn btn-secondary" onclick="showReview()">返回审查</button>
      <button class="btn btn-primary" id="btnExecAll" onclick="executeAll()">确认并执行修复</button>
    </div>
  </div>

  <!-- Phase 5: 修复中 -->
  <div id="phase-fixing" class="hidden">
    <div class="card">
      <div class="card-title">🔧 正在修复... <span class="spinner"></span></div>
      <div id="fixSteps"></div>
    </div>
    <div id="fixLogPanel" class="log-panel"></div>
  </div>

  <!-- Phase 6: 完成 -->
  <div id="phase-done" class="hidden">
    <div class="card">
      <div class="summary">
        <div class="summary-icon" id="summaryIcon">✅</div>
        <div class="summary-title" id="summaryTitle">修复完成</div>
        <div class="summary-desc" id="summaryDesc">所有问题已成功修复</div>
        <div class="summary-stats" id="summaryStats"></div>
        <div class="actions">
          <button class="btn btn-secondary" onclick="startScan()">再次扫描</button>
          <button class="btn btn-primary" onclick="location.reload()">完成</button>
        </div>
      </div>
    </div>
    <div id="doneLogPanel" class="log-panel"></div>
  </div>
</div>

<script>
const API = '';
let pollTimer = null;
let currentState = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  const info = document.getElementById('systemInfo');
  info.textContent = `${navigator.platform} | ${new Date().toLocaleString('zh-CN')}`;
});

// 更新流程指示器
function updateFlow(active) {
  const phases = ['scan','preview','review','confirm','fixing','done'];
  const idx = phases.indexOf(active);
  for (let i = 0; i < 6; i++) {
    const dot = document.getElementById('fd' + (i+1));
    const label = document.getElementById('fl' + (i+1));
    dot.className = 'flow-dot';
    label.className = 'flow-label';
    if (i < idx) { dot.classList.add('done'); label.classList.add('done'); }
    else if (i === idx) { dot.classList.add('active'); label.classList.add('active'); }
    if (i < 5) {
      const line = document.getElementById('fline' + (i+1));
      line.className = 'flow-line';
      if (i < idx) line.classList.add('done');
      else if (i === idx - 1) line.classList.add('active');
    }
  }
}

// 显示阶段
function showPhase(phase) {
  ['scan','preview','review','confirm','fixing','done'].forEach(p => {
    document.getElementById('phase-' + p).classList.toggle('hidden', p !== phase);
  });
  updateFlow(phase);
}

// API 调用
async function api(path) {
  const res = await fetch(API + path);
  return res.json();
}

// 开始扫描
async function startScan() {
  showPhase('scan');
  document.getElementById('btnScan').disabled = true;
  document.getElementById('btnScan').innerHTML = '<span class="spinner"></span> 扫描中...';
  document.getElementById('logPanel').classList.remove('hidden');
  document.getElementById('logPanel').innerHTML = '<div class="log-line">开始扫描...</div>';

  await api('/api/scan');

  // 轮询状态
  pollTimer = setInterval(async () => {
    const state = await api('/api/state');
    currentState = state;
    updateLog(state.log);
    if (state.current_phase === 'preview') {
      clearInterval(pollTimer);
      document.getElementById('btnScan').disabled = false;
      document.getElementById('btnScan').textContent = '重新扫描';
      showPreview(state);
    } else if (state.current_phase === 'done') {
      clearInterval(pollTimer);
      showDone(state);
    }
  }, 500);
}

// 更新日志
function updateLog(logs) {
  const panel = document.getElementById('logPanel');
  if (!panel) return;
  panel.innerHTML = logs.map(l => {
    let cls = 'log-line';
    if (l.includes('✓') || l.includes('正常')) cls += ' success';
    else if (l.includes('✗') || l.includes('错误')) cls += ' error';
    else if (l.includes('⚠') || l.includes('发现')) cls += ' warning';
    return `<div class="${cls}">${l}</div>`;
  }).join('');
  panel.scrollTop = panel.scrollHeight;
}

// 显示配置预览阶段
function showPreview(state) {
  showPhase('preview');
  document.getElementById('previewLogPanel').classList.remove('hidden');
  updatePreviewLog(state.log);
}

// 开始详细配置扫描
async function startConfigScan() {
  document.getElementById('btnScanConfig').disabled = true;
  document.getElementById('configSpinner').classList.remove('hidden');
  
  await api('/api/scan-config');
  
  // 轮询状态
  pollTimer = setInterval(async () => {
    const state = await api('/api/state');
    currentState = state;
    updatePreviewLog(state.log);
    
    // 检查是否已完成配置扫描
    const lastLog = state.log[state.log.length - 1] || '';
    if (lastLog.includes('个MCP服务器') || lastLog.includes('扫描报告')) {
      clearInterval(pollTimer);
      document.getElementById('btnScanConfig').disabled = false;
      document.getElementById('configSpinner').classList.add('hidden');
      showConfigDetails(state);
    }
  }, 400);
}
}

function updatePreviewLog(logs) {
  const panel = document.getElementById('previewLogPanel');
  if (!panel) return;
  panel.innerHTML = logs.map(l => {
    let cls = 'log-line';
    if (l.includes('✓')) cls += ' success';
    else if (l.includes('✗')) cls += ' error';
    else if (l.includes('发现')) cls += ' warning';
    return `<div class="${cls}">${l}</div>`;
  }).join('');
  panel.scrollTop = panel.scrollHeight;
}

// 显示配置详情
function showConfigDetails(state) {
  const container = document.getElementById('configPreview');
  container.classList.remove('hidden');
  
  let html = '<div class="card">';
  html += '<div class="card-title">📋 详细配置信息</div>';
  
  const installedAgents = state.agents.filter(a => a.installed && a.config_scan);
  
  installedAgents.forEach(agent => {
    const scan = agent.config_scan;
    html += `<div class="agent-item" onclick="toggleConfigDetail('${agent.agent_id}')">`;
    html += `<div class="agent-left">`;
    html += `<div class="agent-icon">${agent.icon}</div>`;
    html += `<div>`;
    html += `<div class="agent-name">${agent.name}</div>`;
    html += `<div class="agent-path">${scan.config_files ? scan.config_files.length : 0} 个配置文件`;
    if (scan.total_plugins > 0) html += ` | ${scan.total_plugins} 个插件`;
    if (scan.mcp_servers && scan.mcp_servers.length > 0) html += ` | ${scan.mcp_servers.length} 个MCP服务器`;
    html += '</div>';
    html += '</div></div>';
    html += `<span class="agent-badge ok">查看详情</span>`;
    html += '</div>';
    
    html += `<div id="config-detail-${agent.agent_id}" class="config-preview hidden">`;
    
    if (scan.config_files && scan.config_files.length > 0) {
      html += '<div class="config-section">';
      html += '<div class="config-section-title">📄 配置文件</div>';
      scan.config_files.forEach(cf => {
        const status = cf.is_valid ? '✅' : '❌';
        html += `<div class="config-item">`;
        html += `<span class="config-label">${status} ${cf.filename}</span>`;
        html += `<span class="config-value">${(cf.size_bytes / 1024).toFixed(1)} KB</span>`;
        html += '</div>';
      });
      html += '</div>';
    }
    
    if (scan.external_plugins && scan.external_plugins.length > 0) {
      html += '<div class="config-section">';
      html += `<div class="config-section-title">🔌 插件 (${scan.external_plugins.length}个)</div>`;
      scan.external_plugins.slice(0, 5).forEach(plugin => {
        html += `<div class="config-item">`;
        html += `<span class="config-label">${plugin.name}</span>`;
        html += `<span class="config-value">v${plugin.version || '?'}</span>`;
        html += '</div>';
      });
      if (scan.external_plugins.length > 5) {
        html += `<div style="color:var(--text3);font-size:11px;margin-top:4px;">...还有 ${scan.external_plugins.length - 5} 个插件</div>`;
      }
      html += '</div>';
    }
    
    if (scan.mcp_servers && scan.mcp_servers.length > 0) {
      html += '<div class="config-section">';
      html += `<div class="config-section-title">🌐 MCP服务器 (${scan.mcp_servers.length}个)</div>`;
      scan.mcp_servers.forEach(server => {
        const enabled = server.enabled ? '✅' : '❌';
        html += `<div class="config-item">`;
        html += `<span class="config-label">${enabled} ${server.name}</span>`;
        html += `<span class="config-value">${server.type}</span>`;
        html += '</div>';
      });
      html += '</div>';
    }
    
    if (scan.skills && scan.skills.length > 0) {
      html += '<div class="config-section">';
      html += `<div class="config-section-title">⚡ 技能/功能 (${scan.skills.length}个)</div>`;
      scan.skills.slice(0, 5).forEach(skill => {
        const enabled = skill.enabled ? '✅' : '❌';
        html += `<div class="config-item">`;
        html += `<span class="config-label">${enabled} ${skill.name}</span>`;
        html += '</div>';
      });
      html += '</div>';
    }
    
    html += '</div>';
  });
  
  html += '</div>';
  container.innerHTML = html;
}

function toggleConfigDetail(agentId) {
  const detail = document.getElementById(`config-detail-${agentId}`);
  if (detail) detail.classList.toggle('hidden');
}

async function exportReport(format) {
  const result = await api(`/api/export-report?format=${format}`);
  alert(`报告已导出到:\n${result.path}`);
}

function showReview(state) {
  showPhase('review');
  const container = document.getElementById('reviewContent');
  let html = '';

  state.agents.forEach(a => {
    const hasIssues = a.issues && a.issues.length > 0;
    const cls = hasIssues ? 'has-issues' : (a.installed ? 'ok' : '');
    const badge = a.installed
      ? (hasIssues ? `<span class="agent-badge error">${a.issues.length} 个问题</span>` : `<span class="agent-badge ok">正常</span>`)
      : `<span class="agent-badge not-installed">未安装</span>`;

    html += `<div class="agent-item ${cls}">`;
    html += `<div class="agent-left">`;
    html += `<div class="agent-icon">${a.icon}</div>`;
    html += `<div>`;
    html += `<div class="agent-name">${a.name}</div>`;
    html += `<div class="agent-path">${a.installed ? a.path : '未检测到'}</div>`;
    html += `</div></div>`;
    html += `${badge}`;
    html += `</div>`;

    if (hasIssues) {
      html += '<div class="issue-list">';
      a.issues.forEach(i => { html += `<div class="issue-item">${i}</div>`; });
      html += '</div>';
    }
  });

  container.innerHTML = html;
  
  const hasAnyIssues = state.agents.some(a => a.issues && a.issues.length > 0);
  document.getElementById('btnPlan').disabled = !hasAnyIssues;
}

async function buildPlan() {
  const state = await api('/api/plan');
  currentState = state;
  showPhase('confirm');

  const container = document.getElementById('stepsList');
  let html = '';

  state.steps.forEach((s, i) => {
    html += `<div class="step-item" id="step-${i}">`;
    html += `<div class="step-num">${i + 1}</div>`;
    html += `<div class="step-content">`;
    html += `<div class="step-name">${s.name}</div>`;
    html += `<div class="step-desc">${s.description}</div>`;
    html += `<div class="step-detail" id="step-detail-${i}"></div>`;
    html += `</div></div>`;
  });

  container.innerHTML = html;
}

async function executeAll() {
  showPhase('fixing');
  document.getElementById('fixLogPanel').innerHTML = '<div class="log-line">开始修复...</div>';

  const state = currentState;
  const fixSteps = document.getElementById('fixSteps');
  let html = '';
  state.steps.forEach((s, i) => {
    html += `<div class="step-item" id="fix-step-${i}">`;
    html += `<div class="step-num">${i + 1}</div>`;
    html += `<div class="step-content">`;
    html += `<div class="step-name">${s.name}</div>`;
    html += `<div class="step-desc">${s.description}</div>`;
    html += `<div class="step-detail" id="fix-detail-${i}"></div>`;
    html += `</div></div>`;
  });
  fixSteps.innerHTML = html;

  await api('/api/execute-all');

  pollTimer = setInterval(async () => {
    const state = await api('/api/state');
    currentState = state;
    updateFixLog(state.log);

    state.steps.forEach((s, i) => {
      const el = document.getElementById('fix-step-' + i);
      if (el) {
        el.className = 'step-item ' + s.status;
        const detail = document.getElementById('fix-detail-' + i);
        if (detail && s.detail) detail.textContent = s.detail;
      }
    });

    if (state.current_phase === 'done') {
      clearInterval(pollTimer);
      setTimeout(() => showDone(state), 500);
    }
  }, 400);
}

function updateFixLog(logs) {
  const panel = document.getElementById('fixLogPanel');
  panel.innerHTML = logs.map(l => {
    let cls = 'log-line';
    if (l.includes('✓')) cls += ' success';
    else if (l.includes('✗')) cls += ' error';
    else if (l.includes('⚠')) cls += ' warning';
    return `<div class="${cls}">${l}</div>`;
  }).join('');
  panel.scrollTop = panel.scrollHeight;
}

function showDone(state) {
  showPhase('done');
  const summary = state.summary || {};
  const hasErrors = summary.errors > 0;
  const hasWarnings = summary.warnings > 0;

  document.getElementById('summaryIcon').textContent = hasErrors ? '⚠️' : (hasWarnings ? '✅' : '🎉');
  document.getElementById('summaryTitle').textContent = hasErrors ? '修复完成（部分问题）' : (hasWarnings ? '修复完成（有警告）' : '全部修复成功');
  document.getElementById('summaryDesc').textContent = hasErrors
    ? `${summary.errors} 个步骤失败，请查看日志了解详情`
    : (hasWarnings ? `${summary.warnings} 个步骤有警告，建议关注` : '所有检测到的问题已成功修复');

  document.getElementById('summaryStats').innerHTML = `
    <div class="stat-item">
      <div class="stat-num" style="color:var(--accent)">${summary.total_steps || 0}</div>
      <div class="stat-label">总步骤</div>
    </div>
    <div class="stat-item">
      <div class="stat-num" style="color:var(--success)">${summary.success || 0}</div>
      <div class="stat-label">成功</div>
    </div>
    <div class="stat-item">
      <div class="stat-num" style="color:var(--warning)">${summary.warnings || 0}</div>
      <div class="stat-label">警告</div>
    </div>
    <div class="stat-item">
      <div class="stat-num" style="color:var(--danger)">${summary.errors || 0}</div>
      <div class="stat-label">失败</div>
    </div>
  `;

  const doneLog = document.getElementById('doneLogPanel');
  doneLog.innerHTML = state.log.map(l => {
    let cls = 'log-line';
    if (l.includes('✓')) cls += ' success';
    else if (l.includes('✗')) cls += ' error';
    else if (l.includes('⚠')) cls += ' warning';
    return `<div class="${cls}">${l}</div>`;
  }).join('');
  doneLog.classList.remove('hidden');
}
</script>
</body>
</html>"""


def find_free_port(start=8080, end=8100):
    for port in range(start, end):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', port))
            s.close()
            return port
        except OSError:
            continue
    return start


def main():
    port = find_free_port()
    server = HTTPServer(('127.0.0.1', port), RepairHandler)
    
    print("=" * 60)
    print("AI Agent 智能修复工具 - 操控界面")
    print("=" * 60)
    print(f"系统: {platform.system()} {platform.release()}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"地址: http://127.0.0.1:{port}")
    print("=" * 60)
    print("正在打开浏览器...")
    
    webbrowser.open(f'http://127.0.0.1:{port}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务")
        server.server_close()


if __name__ == "__main__":
    main()
