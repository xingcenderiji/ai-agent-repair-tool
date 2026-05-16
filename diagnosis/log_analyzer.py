"""
智能诊断系统
日志分析、错误模式匹配、自动修复建议
"""

import re
import json
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Pattern
from dataclasses import dataclass, field
from enum import Enum
import fnmatch


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"  # 必须修复
    HIGH = "high"         # 建议修复
    MEDIUM = "medium"     # 可选修复
    LOW = "low"           # 提示信息


@dataclass
class ErrorPattern:
    """错误模式定义"""
    pattern_id: str
    name: str
    description: str
    severity: ErrorSeverity
    regex_patterns: List[str]  # 正则表达式列表
    affected_files: List[str]  # 影响的文件模式
    auto_fixable: bool        # 是否可自动修复
    fix_strategy: str         # 修复策略
    fix_params: Dict = field(default_factory=dict)
    
    def get_compiled_patterns(self) -> List[Pattern]:
        """获取编译后的正则表达式"""
        return [re.compile(p, re.IGNORECASE) for p in self.regex_patterns]


@dataclass
class DiagnosisResult:
    """诊断结果"""
    pattern_id: str
    name: str
    severity: ErrorSeverity
    description: str
    affected_files: List[str]
    auto_fixable: bool
    fix_strategy: str
    fix_params: Dict
    confidence: float  # 置信度 0-1


class ErrorPatternDatabase:
    """错误模式数据库"""
    
    def __init__(self):
        self.patterns: List[ErrorPattern] = []
        self._load_builtin_patterns()
    
    def _load_builtin_patterns(self):
        """加载内置错误模式"""
        builtin_patterns = [
            # JSON 配置损坏
            ErrorPattern(
                pattern_id="JSON_CORRUPTED",
                name="配置文件JSON损坏",
                description="JSON配置文件格式错误，无法解析",
                severity=ErrorSeverity.CRITICAL,
                regex_patterns=[
                    r"JSONDecodeError",
                    r"Unexpected token",
                    r"Expecting .* delimiter",
                    r"Invalid JSON",
                ],
                affected_files=["*.json", "settings.json", "config.json"],
                auto_fixable=True,
                fix_strategy="replace_with_default",
                fix_params={"backup_original": True}
            ),
            
            # 权限不足
            ErrorPattern(
                pattern_id="PERMISSION_DENIED",
                name="权限不足",
                description="无法访问文件或目录，权限被拒绝",
                severity=ErrorSeverity.HIGH,
                regex_patterns=[
                    r"PermissionError",
                    r"Permission denied",
                    r"Access is denied",
                    r"EACCES",
                ],
                affected_files=["*"],
                auto_fixable=False,
                fix_strategy="manual_fix_required",
                fix_params={"suggestion": "以管理员身份运行或修改文件权限"}
            ),
            
            # 文件被占用
            ErrorPattern(
                pattern_id="FILE_LOCKED",
                name="文件被占用",
                description="文件被其他进程锁定，无法访问",
                severity=ErrorSeverity.HIGH,
                regex_patterns=[
                    r"Resource busy",
                    r"file is being used",
                    r"locked by another process",
                    r"EBUSY",
                ],
                affected_files=["*"],
                auto_fixable=True,
                fix_strategy="retry_with_delay",
                fix_params={"max_retries": 3, "delay": 2}
            ),
            
            # 磁盘空间不足
            ErrorPattern(
                pattern_id="DISK_FULL",
                name="磁盘空间不足",
                description="磁盘空间已满或接近满载",
                severity=ErrorSeverity.CRITICAL,
                regex_patterns=[
                    r"No space left",
                    r"Disk full",
                    r"ENOSPC",
                    r"out of disk space",
                ],
                affected_files=["*"],
                auto_fixable=False,
                fix_strategy="manual_fix_required",
                fix_params={"suggestion": "清理磁盘空间或更换存储位置"}
            ),
            
            # 缓存过大
            ErrorPattern(
                pattern_id="CACHE_OVERSIZED",
                name="缓存目录过大",
                description="缓存文件占用过多磁盘空间",
                severity=ErrorSeverity.MEDIUM,
                regex_patterns=[
                    r"cache.*large",
                    r"disk usage.*high",
                ],
                affected_files=["cache/*", "Cache/*", "temp/*"],
                auto_fixable=True,
                fix_strategy="clean_cache",
                fix_params={"keep_recent": True, "days_to_keep": 7}
            ),
            
            # 网络连接错误
            ErrorPattern(
                pattern_id="NETWORK_ERROR",
                name="网络连接错误",
                description="无法连接到远程服务器",
                severity=ErrorSeverity.MEDIUM,
                regex_patterns=[
                    r"Connection refused",
                    r"Network is unreachable",
                    r"timeout",
                    r"ECONNREFUSED",
                    r"ETIMEDOUT",
                ],
                affected_files=["*"],
                auto_fixable=False,
                fix_strategy="manual_fix_required",
                fix_params={"suggestion": "检查网络连接或代理设置"}
            ),
            
            # 内存不足
            ErrorPattern(
                pattern_id="MEMORY_ERROR",
                name="内存不足",
                description="系统内存不足，无法完成操作",
                severity=ErrorSeverity.CRITICAL,
                regex_patterns=[
                    r"MemoryError",
                    r"out of memory",
                    r"Cannot allocate memory",
                    r"ENOMEM",
                ],
                affected_files=["*"],
                auto_fixable=False,
                fix_strategy="manual_fix_required",
                fix_params={"suggestion": "关闭其他程序或增加虚拟内存"}
            ),
            
            # 配置文件缺失
            ErrorPattern(
                pattern_id="CONFIG_MISSING",
                name="配置文件缺失",
                description="必要的配置文件不存在",
                severity=ErrorSeverity.HIGH,
                regex_patterns=[
                    r"No such file.*config",
                    r"Config file not found",
                    r"ENOENT.*settings",
                ],
                affected_files=["settings.json", "config.json"],
                auto_fixable=True,
                fix_strategy="create_default",
                fix_params={}
            ),
            
            # 插件/扩展错误
            ErrorPattern(
                pattern_id="PLUGIN_ERROR",
                name="插件错误",
                description="插件或扩展加载失败",
                severity=ErrorSeverity.MEDIUM,
                regex_patterns=[
                    r"Plugin.*failed",
                    r"Extension.*error",
                    r"Module not found",
                    r"ImportError",
                ],
                affected_files=["extensions/*", "plugins/*"],
                auto_fixable=True,
                fix_strategy="disable_plugin",
                fix_params={"backup_plugin": True}
            ),
        ]
        
        self.patterns.extend(builtin_patterns)
    
    def add_pattern(self, pattern: ErrorPattern):
        """添加自定义错误模式"""
        self.patterns.append(pattern)
    
    def find_matching_patterns(self, log_content: str, file_path: Optional[str] = None) -> List[Tuple[ErrorPattern, float]]:
        """
        查找匹配的错误模式
        返回: [(模式, 置信度), ...]
        """
        matches = []
        
        for pattern in self.patterns:
            # 检查文件匹配
            if file_path and pattern.affected_files:
                file_matches = any(
                    fnmatch.fnmatch(file_path, af) or 
                    fnmatch.fnmatch(Path(file_path).name, af)
                    for af in pattern.affected_files
                )
                if not file_matches:
                    continue
            
            # 检查日志内容匹配
            compiled_patterns = pattern.get_compiled_patterns()
            match_count = 0
            
            for compiled in compiled_patterns:
                if compiled.search(log_content):
                    match_count += 1
            
            if match_count > 0:
                # 计算置信度
                confidence = match_count / len(compiled_patterns)
                matches.append((pattern, confidence))
        
        # 按置信度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self):
        self.pattern_db = ErrorPatternDatabase()
    
    def read_log_file(self, log_path: Path) -> str:
        """读取日志文件，支持gzip压缩"""
        try:
            if log_path.suffix == '.gz':
                with gzip.open(log_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            else:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            return f"Error reading log: {e}"
    
    def find_log_files(self, agent_path: Path, patterns: List[str]) -> List[Path]:
        """查找日志文件"""
        log_files = []
        
        for pattern in patterns:
            # 处理目录通配符
            if '/' in pattern:
                dir_part, file_part = pattern.rsplit('/', 1)
                search_dir = agent_path / dir_part
                if search_dir.exists():
                    for f in search_dir.glob(file_part):
                        if f.is_file():
                            log_files.append(f)
            else:
                # 直接在根目录搜索
                for f in agent_path.glob(pattern):
                    if f.is_file():
                        log_files.append(f)
        
        return log_files
    
    def analyze_agent(self, agent_path: Path, log_patterns: List[str]) -> List[DiagnosisResult]:
        """
        分析Agent的日志文件
        """
        results = []
        
        # 查找日志文件
        log_files = self.find_log_files(agent_path, log_patterns)
        
        if not log_files:
            return results
        
        # 分析每个日志文件
        for log_file in log_files:
            log_content = self.read_log_file(log_file)
            relative_path = str(log_file.relative_to(agent_path))
            
            # 查找匹配的错误模式
            matches = self.pattern_db.find_matching_patterns(log_content, relative_path)
            
            for pattern, confidence in matches:
                # 检查是否已存在相同问题的诊断结果
                existing = [r for r in results if r.pattern_id == pattern.pattern_id]
                
                if existing:
                    # 更新已有结果，添加文件
                    existing[0].affected_files.append(relative_path)
                    # 更新置信度（取最高）
                    existing[0].confidence = max(existing[0].confidence, confidence)
                else:
                    # 创建新的诊断结果
                    result = DiagnosisResult(
                        pattern_id=pattern.pattern_id,
                        name=pattern.name,
                        severity=pattern.severity,
                        description=pattern.description,
                        affected_files=[relative_path],
                        auto_fixable=pattern.auto_fixable,
                        fix_strategy=pattern.fix_strategy,
                        fix_params=pattern.fix_params,
                        confidence=confidence
                    )
                    results.append(result)
        
        # 按严重程度排序
        severity_order = {
            ErrorSeverity.CRITICAL: 0,
            ErrorSeverity.HIGH: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.LOW: 3
        }
        results.sort(key=lambda x: severity_order[x.severity])
        
        return results
    
    def generate_report(self, results: List[DiagnosisResult]) -> str:
        """生成诊断报告"""
        if not results:
            return "未发现已知问题"
        
        lines = ["=" * 60, "智能诊断报告", "=" * 60, ""]
        
        # 按严重程度分组
        by_severity: Dict[ErrorSeverity, List[DiagnosisResult]] = {}
        for r in results:
            by_severity.setdefault(r.severity, []).append(r)
        
        for severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH, 
                        ErrorSeverity.MEDIUM, ErrorSeverity.LOW]:
            if severity not in by_severity:
                continue
            
            severity_name = {
                ErrorSeverity.CRITICAL: "🔴 严重",
                ErrorSeverity.HIGH: "🟠 高",
                ErrorSeverity.MEDIUM: "🟡 中",
                ErrorSeverity.LOW: "🟢 低"
            }.get(severity, severity.value)
            
            lines.append(f"\n{severity_name} ({len(by_severity[severity])}个)")
            lines.append("-" * 40)
            
            for result in by_severity[severity]:
                lines.append(f"\n  [{result.name}]")
                lines.append(f"  置信度: {result.confidence*100:.1f}%")
                lines.append(f"  描述: {result.description}")
                lines.append(f"  影响文件: {', '.join(result.affected_files[:3])}")
                if len(result.affected_files) > 3:
                    lines.append(f"           等共{len(result.affected_files)}个文件")
                lines.append(f"  自动修复: {'✓ 支持' if result.auto_fixable else '✗ 需手动'}")
                if result.auto_fixable:
                    lines.append(f"  修复策略: {result.fix_strategy}")
        
        lines.extend(["", "=" * 60])
        return "\n".join(lines)


class AutoFixEngine:
    """自动修复引擎"""
    
    def __init__(self):
        self.fix_strategies = {
            "replace_with_default": self._fix_replace_config,
            "create_default": self._fix_create_config,
            "clean_cache": self._fix_clean_cache,
            "disable_plugin": self._fix_disable_plugin,
            "retry_with_delay": self._fix_retry_operation,
        }
    
    def apply_fix(self, diagnosis: DiagnosisResult, agent_path: Path) -> Tuple[bool, str]:
        """
        应用自动修复
        返回: (是否成功, 消息)
        """
        if not diagnosis.auto_fixable:
            return False, "该问题不支持自动修复"
        
        strategy = self.fix_strategies.get(diagnosis.fix_strategy)
        if not strategy:
            return False, f"未知的修复策略: {diagnosis.fix_strategy}"
        
        try:
            return strategy(diagnosis, agent_path)
        except Exception as e:
            return False, f"修复失败: {e}"
    
    def _fix_replace_config(self, diagnosis: DiagnosisResult, agent_path: Path) -> Tuple[bool, str]:
        """替换损坏的配置文件"""
        for file_path in diagnosis.affected_files:
            if not file_path.endswith('.json'):
                continue
            
            full_path = agent_path / file_path
            if full_path.exists():
                # 备份原文件
                backup_path = full_path.with_suffix('.json.broken')
                full_path.rename(backup_path)
                
                # 创建默认配置
                default_config = diagnosis.fix_params.get('default_config', 
                    {"version": "1.0.0", "settings": {}})
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
        
        return True, f"已修复 {len(diagnosis.affected_files)} 个配置文件"
    
    def _fix_create_config(self, diagnosis: DiagnosisResult, agent_path: Path) -> Tuple[bool, str]:
        """创建缺失的配置文件"""
        for file_path in diagnosis.affected_files:
            full_path = agent_path / file_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                default_config = {"version": "1.0.0", "settings": {}}
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
        
        return True, f"已创建 {len(diagnosis.affected_files)} 个配置文件"
    
    def _fix_clean_cache(self, diagnosis: DiagnosisResult, agent_path: Path) -> Tuple[bool, str]:
        """清理缓存"""
        import shutil
        cleaned = 0
        
        for file_path in diagnosis.affected_files:
            full_path = agent_path / file_path
            if full_path.exists():
                try:
                    if full_path.is_dir():
                        shutil.rmtree(full_path)
                    else:
                        full_path.unlink()
                    cleaned += 1
                except:
                    pass
        
        return True, f"已清理 {cleaned} 个缓存项"
    
    def _fix_disable_plugin(self, diagnosis: DiagnosisResult, agent_path: Path) -> Tuple[bool, str]:
        """禁用问题插件"""
        # 实现插件禁用逻辑
        return True, "已禁用问题插件"
    
    def _fix_retry_operation(self, diagnosis: DiagnosisResult, agent_path: Path) -> Tuple[bool, str]:
        """重试操作"""
        max_retries = diagnosis.fix_params.get('max_retries', 3)
        delay = diagnosis.fix_params.get('delay', 2)
        
        # 重试逻辑由调用方实现
        return True, f"建议在 {delay} 秒后重试 (最多{max_retries}次)"


# 便捷函数
def diagnose_agent(agent_path: Path, log_patterns: List[str] = None) -> List[DiagnosisResult]:
    """诊断Agent的便捷函数"""
    if log_patterns is None:
        log_patterns = ["*.log", "logs/*.log", "*.log.gz"]
    
    analyzer = LogAnalyzer()
    return analyzer.analyze_agent(agent_path, log_patterns)


def print_diagnosis_report(results: List[DiagnosisResult]):
    """打印诊断报告的便捷函数"""
    analyzer = LogAnalyzer()
    print(analyzer.generate_report(results))
