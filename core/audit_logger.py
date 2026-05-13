"""
增强审计日志系统
记录所有修复操作的详细信息，支持倒查根源

功能：
1. 记录每次修复会话的完整操作链
2. 支持按时间、Agent、操作类型查询
3. 提供根源分析工具
4. 导出审计报告
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import platform

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """操作类型"""
    SCAN = "scan"                    # 扫描
    BACKUP = "backup"                # 备份
    RESTORE = "restore"              # 恢复
    CACHE_CLEAN = "cache_clean"      # 清理缓存
    CONFIG_FIX = "config_fix"        # 修复配置
    PLUGIN_FIX = "plugin_fix"        # 修复插件
    FILE_READ = "file_read"          # 读取文件
    FILE_WRITE = "file_write"        # 写入文件
    FILE_DELETE = "file_delete"      # 删除文件
    VALIDATION = "validation"        # 验证操作
    SECURITY_BLOCK = "security_block" # 安全拦截


class OperationStatus(Enum):
    """操作状态"""
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class OperationRecord:
    """单条操作记录"""
    op_id: str                       # 操作唯一ID
    session_id: str                  # 所属会话ID
    timestamp: str                   # 时间戳
    operation: str                   # 操作类型
    agent_id: Optional[str]          # 目标Agent
    target_path: Optional[str]       # 目标路径
    status: str                      # 状态
    details: Dict[str, Any]          # 详细信息
    error_message: Optional[str]     # 错误信息
    stack_trace: Optional[str]       # 堆栈跟踪
    user_consent: Optional[bool]     # 用户是否确认
    duration_ms: Optional[int]       # 耗时(毫秒)


@dataclass
class SessionRecord:
    """修复会话记录"""
    session_id: str                  # 会话ID
    start_time: str                  # 开始时间
    end_time: Optional[str]          # 结束时间
    system_info: Dict[str, str]      # 系统信息
    operations: List[OperationRecord] # 操作列表
    summary: Dict[str, Any]          # 摘要统计


class AuditLogger:
    """增强审计日志管理器"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".ai_agent_repair" / "audit_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionRecord] = None
        self._operation_counter = 0
        
    def _generate_id(self) -> str:
        """生成唯一ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        random_suffix = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        return f"{timestamp}_{random_suffix}"
    
    def start_session(self) -> str:
        """开始新的修复会话"""
        session_id = self._generate_id()
        self.current_session = SessionRecord(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            system_info={
                "platform": platform.system(),
                "platform_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
            },
            operations=[],
            summary={}
        )
        self._operation_counter = 0
        logger.info(f"[审计] 开始会话: {session_id}")
        return session_id
    
    def log_operation(
        self,
        operation: OperationType,
        agent_id: Optional[str] = None,
        target_path: Optional[Path] = None,
        status: OperationStatus = OperationStatus.SUCCESS,
        details: Optional[Dict] = None,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        user_consent: Optional[bool] = None,
        duration_ms: Optional[int] = None
    ) -> str:
        """
        记录操作
        
        Returns:
            操作ID
        """
        if self.current_session is None:
            self.start_session()
        
        self._operation_counter += 1
        op_id = f"{self.current_session.session_id}_{self._operation_counter:04d}"
        
        record = OperationRecord(
            op_id=op_id,
            session_id=self.current_session.session_id,
            timestamp=datetime.now().isoformat(),
            operation=operation.value,
            agent_id=agent_id,
            target_path=str(target_path) if target_path else None,
            status=status.value,
            details=details or {},
            error_message=error_message,
            stack_trace=stack_trace,
            user_consent=user_consent,
            duration_ms=duration_ms
        )
        
        self.current_session.operations.append(record)
        
        # 实时记录到文件（便于崩溃时恢复）
        self._append_operation_log(record)
        
        return op_id
    
    def _append_operation_log(self, record: OperationRecord):
        """追加操作记录到日志文件"""
        if self.current_session is None:
            return
        
        session_file = self.log_dir / f"session_{self.current_session.session_id}.jsonl"
        try:
            with open(session_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"[审计] 写入操作日志失败: {e}")
    
    def end_session(self, summary: Optional[Dict] = None):
        """结束当前会话"""
        if self.current_session is None:
            return
        
        self.current_session.end_time = datetime.now().isoformat()
        
        # 计算摘要
        ops = self.current_session.operations
        self.current_session.summary = {
            "total_operations": len(ops),
            "success_count": sum(1 for op in ops if op.status == OperationStatus.SUCCESS.value),
            "failed_count": sum(1 for op in ops if op.status == OperationStatus.FAILED.value),
            "blocked_count": sum(1 for op in ops if op.status == OperationStatus.BLOCKED.value),
            "warning_count": sum(1 for op in ops if op.status == OperationStatus.WARNING.value),
            **(summary or {})
        }
        
        # 保存完整会话记录
        session_file = self.log_dir / f"session_{self.current_session.session_id}.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dumps(asdict(self.current_session), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[审计] 保存会话日志失败: {e}")
        
        logger.info(f"[审计] 结束会话: {self.current_session.session_id}")
        self.current_session = None
    
    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """获取指定会话记录"""
        session_file = self.log_dir / f"session_{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return SessionRecord(**data)
            except Exception as e:
                logger.error(f"[审计] 读取会话日志失败: {e}")
        return None
    
    def query_operations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent_id: Optional[str] = None,
        operation_type: Optional[OperationType] = None,
        status: Optional[OperationStatus] = None,
        limit: int = 100
    ) -> List[OperationRecord]:
        """
        查询操作记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            agent_id: 过滤特定Agent
            operation_type: 过滤操作类型
            status: 过滤状态
            limit: 返回数量限制
        """
        results = []
        
        # 遍历所有会话文件
        for session_file in sorted(self.log_dir.glob("session_*.json"), reverse=True):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = SessionRecord(**data)
                
                # 检查时间范围
                session_time = datetime.fromisoformat(session.start_time)
                if start_time and session_time < start_time:
                    continue
                if end_time and session_time > end_time:
                    continue
                
                # 过滤操作
                for op in session.operations:
                    if agent_id and op.agent_id != agent_id:
                        continue
                    if operation_type and op.operation != operation_type.value:
                        continue
                    if status and op.status != status.value:
                        continue
                    
                    results.append(op)
                    if len(results) >= limit:
                        return results
                        
            except Exception as e:
                logger.warning(f"[审计] 读取会话文件失败 {session_file}: {e}")
        
        return results
    
    def analyze_failure_root_cause(self, session_id: str) -> Optional[Dict]:
        """
        分析失败根源
        
        Returns:
            根源分析报告
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        failed_ops = [op for op in session.operations if op.status == OperationStatus.FAILED.value]
        blocked_ops = [op for op in session.operations if op.status == OperationStatus.BLOCKED.value]
        
        if not failed_ops and not blocked_ops:
            return {"status": "no_failures", "message": "会话中没有失败或拦截的操作"}
        
        analysis = {
            "session_id": session_id,
            "analysis_time": datetime.now().isoformat(),
            "total_operations": len(session.operations),
            "failed_count": len(failed_ops),
            "blocked_count": len(blocked_ops),
            "root_causes": [],
            "recommendations": []
        }
        
        # 分析失败模式
        for op in failed_ops:
            cause = {
                "operation_id": op.op_id,
                "operation_type": op.operation,
                "agent_id": op.agent_id,
                "target_path": op.target_path,
                "error": op.error_message,
                "timestamp": op.timestamp
            }
            analysis["root_causes"].append(cause)
        
        # 分析安全拦截
        for op in blocked_ops:
            cause = {
                "operation_id": op.op_id,
                "operation_type": op.operation,
                "agent_id": op.agent_id,
                "target_path": op.target_path,
                "reason": op.details.get("block_reason", "未知"),
                "timestamp": op.timestamp
            }
            analysis["root_causes"].append(cause)
        
        # 生成建议
        if any(op.operation == OperationType.CONFIG_FIX.value for op in failed_ops):
            analysis["recommendations"].append("配置文件修复失败，建议检查文件权限或磁盘空间")
        
        if any(op.operation == OperationType.BACKUP.value for op in failed_ops):
            analysis["recommendations"].append("备份操作失败，建议检查备份目录权限和磁盘空间")
        
        if blocked_ops:
            analysis["recommendations"].append("存在安全拦截操作，建议检查配置是否包含危险路径或操作")
        
        return analysis
    
    def generate_audit_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        生成审计报告
        
        Returns:
            报告文件路径
        """
        if output_path is None:
            output_path = self.log_dir / f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 查询所有操作
        operations = self.query_operations(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # 统计
        stats = {
            "total_operations": len(operations),
            "by_type": {},
            "by_status": {},
            "by_agent": {},
            "failed_operations": [],
            "blocked_operations": []
        }
        
        for op in operations:
            # 按类型统计
            stats["by_type"][op.operation] = stats["by_type"].get(op.operation, 0) + 1
            # 按状态统计
            stats["by_status"][op.status] = stats["by_status"].get(op.status, 0) + 1
            # 按Agent统计
            if op.agent_id:
                stats["by_agent"][op.agent_id] = stats["by_agent"].get(op.agent_id, 0) + 1
            
            # 收集失败和拦截
            if op.status == OperationStatus.FAILED.value:
                stats["failed_operations"].append({
                    "op_id": op.op_id,
                    "operation": op.operation,
                    "agent_id": op.agent_id,
                    "error": op.error_message
                })
            elif op.status == OperationStatus.BLOCKED.value:
                stats["blocked_operations"].append({
                    "op_id": op.op_id,
                    "operation": op.operation,
                    "agent_id": op.agent_id,
                    "reason": op.details.get("block_reason")
                })
        
        report = {
            "report_time": datetime.now().isoformat(),
            "period": {
                "start": start_time.isoformat() if start_time else "all",
                "end": end_time.isoformat() if end_time else "all"
            },
            "statistics": stats,
            "recent_operations": [
                {
                    "op_id": op.op_id,
                    "timestamp": op.timestamp,
                    "operation": op.operation,
                    "agent_id": op.agent_id,
                    "status": op.status,
                    "error": op.error_message
                }
                for op in operations[:50]  # 最近50条
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[审计] 报告已生成: {output_path}")
        return output_path
    
    def get_recent_sessions(self, count: int = 10) -> List[Dict]:
        """获取最近的会话列表"""
        sessions = []
        
        for session_file in sorted(self.log_dir.glob("session_*.json"), reverse=True)[:count]:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "start_time": data.get("start_time"),
                        "end_time": data.get("end_time"),
                        "summary": data.get("summary", {})
                    })
            except:
                pass
        
        return sessions


# 全局审计日志实例
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger() -> AuditLogger:
    """获取全局审计日志实例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_repair_operation(
    operation: OperationType,
    agent_id: Optional[str] = None,
    target_path: Optional[Path] = None,
    status: OperationStatus = OperationStatus.SUCCESS,
    **kwargs
) -> str:
    """便捷函数：记录修复操作"""
    return get_audit_logger().log_operation(
        operation=operation,
        agent_id=agent_id,
        target_path=target_path,
        status=status,
        **kwargs
    )
