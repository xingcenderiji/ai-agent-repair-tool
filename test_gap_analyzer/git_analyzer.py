"""
Git 分析器 - 获取和分析代码变更
"""
import os
import re
import subprocess
from typing import List, Optional, Tuple
from pathlib import Path
from .types import CommitInfo, FileChange


class GitAnalyzer:
    """Git 仓库分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def is_git_repo(self) -> bool:
        """检查是否是 Git 仓库"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_recent_commits(self, max_count: int = 10) -> List[CommitInfo]:
        """获取最近的提交"""
        if not self.is_git_repo():
            return []

        try:
            # 获取提交列表
            log_args = [
                "git", "log", "-n", str(max_count),
                "--format=%H|%an|%ad|%s",
                "--date=iso8601", "-n", str(max_count)
            ]
            
            result = subprocess.run(
                log_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            commits = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '|' in line:
                        parts = line.split('|', 3)
                        if len(parts) >= 3:
                            commit_hash = parts[0]
                            author = parts[1]
                            date = parts[2]
                            message = parts[3] if len(parts) > 3 else ''
                            
                            files = self._get_files_for_commit(commit_hash)
                            
                            commits.append(CommitInfo(
                                hash=commit_hash,
                                message=message,
                                author=author,
                                date=date,
                                files=files
                            ))
            return commits
        except Exception as e:
            print(f"Error: {e}")
            return []

    def _get_files_for_commit(self, commit_hash: str) -> List[FileChange]:
        """获取某次提交的文件变更"""
        try:
            # 先获取有多少行变更
            stats_args = ["git", "show", "--stat", commit_hash]
            stats_result = subprocess.run(
                stats_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            changes = []
            if stats_result.returncode == 0:
                for line in stats_result.stdout.split('\n'):
                    if '|' in line:
                        # 类似 "filename.py | 10 +++++-----"
                        parts = line.split('|')
                        if len(parts) >= 2:
                            filename = parts[0].strip()
                            stat_part = parts[1].strip()
                            
                            added = stat_part.count('+')
                            removed = stat_part.count('-')
                            
                            changes.append(FileChange(
                                file_path=filename,
                                change_type='modified',
                                lines_added=added,
                                lines_removed=removed
                            ))

            # 获取具体的变更类型
            for i in range(len(changes)):
                diff_args = [
                    "git", "diff", f"{commit_hash}^", commit_hash, 
                    "--name-status", "--", changes[i].file_path
                ]
                diff_result = subprocess.run(
                    diff_args,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if diff_result.returncode == 0 and diff_result.stdout.strip():
                    first_line = diff_result.stdout.split('\n')[0]
                    if first_line.startswith('A'):
                        changes[i].change_type = 'added'
                    elif first_line.startswith('D'):
                        changes[i].change_type = 'deleted'

            return changes
        except Exception:
            return []

    def get_changed_files_between(self, 
                                  start_ref: str, 
                                  end_ref: str = "HEAD") -> List[FileChange]:
        """获取两个提交之间的变更"""
        try:
            args = [
                "git", "diff", "--name-status", 
                f"{start_ref}..{end_ref}"
            ]
            result = subprocess.run(
                args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            files = []
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        status = line[0]
                        filename = line[2:].strip()
                        change_type = {
                            'A': 'added',
                            'M': 'modified',
                            'D': 'deleted'
                        }.get(status, 'modified')
                        
                        files.append(FileChange(
                            file_path=filename,
                            change_type=change_type,
                            lines_added=0,
                            lines_removed=0
                        ))
            return files
        except Exception:
            return []

    def get_diff(self, commit_hash: str, file_path: str) -> str:
        """获取文件的差异内容"""
        try:
            args = ["git", "show", f"{commit_hash}:{file_path}"]
            result = subprocess.run(
                args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""
