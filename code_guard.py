"""
代码修改保护系统 - 保护Neo核心代码不被意外修改

核心功能:
1. 文件保护：核心文件只读
2. 沙盒隔离：限制可写区域
3. 危险代码检测：阻止危险模式
4. 备份回滚：自动备份和恢复
5. 修改审批：敏感操作需要确认
"""

import os
import re
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class ModificationLevel(Enum):
    NONE = "none"
    SKILLS_ONLY = "skills_only"
    EXTENSIONS = "extensions"
    FULL_WITH_APPROVAL = "full_with_approval"


@dataclass
class ModificationRecord:
    timestamp: str
    file_path: str
    backup_path: str
    reason: str
    checksum_before: str
    checksum_after: str
    approved: bool = False


class CodeGuard:
    """
    代码修改保护系统
    
    保护Neo核心代码，限制修改范围，提供安全沙盒
    """
    
    PROTECTED_FILES = {
        "core/react_agent.py",
        "core/skill_manager.py",
        "core/memory.py",
        "core/planner.py",
        "core/__init__.py",
        "browser_agent/safety_guard.py",
        "browser_agent/browser_skill.py",
        "browser_agent/browser_controller.py",
        "browser_agent/session_manager.py",
        "desktop_agent/desktop_skill.py",
        "desktop_agent/app_launcher.py",
        "desktop_agent/ui_agent.py",
        "code_guard.py",
        "llm_client.py",
        "app.py",
    }
    
    PROTECTED_DIRECTORIES = {
        "core",
        "browser_agent",
        "desktop_agent",
        "soul",
    }
    
    SANDBOX_DIRECTORIES = {
        "agent_skills",
        "extensions",
    }
    
    DANGEROUS_PATTERNS = [
        r'import\s+os\.system',
        r'os\.system\s*\(',
        r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
        r'compile\s*\([^)]*,\s*[\'"]exec[\'"]',
        r'open\s*\([^)]*,\s*[\'"]w[\'"]\s*\).*\.\w+system',
        r'FORBIDDEN_OPERATIONS\s*=\s*\{[\s}]*\}',
        r'SAFE_OPERATIONS\s*=\s*\{[^}]*\*[^}]*\}',
        r'classify_operation.*return\s+OperationLevel\.SAFE',
        r'PROTECTED_FILES\s*=\s*\{[\s}]*\}',
        r'PROTECTED_DIRECTORIES\s*=\s*\{[\s}]*\}',
        r'DANGEROUS_PATTERNS\s*=\s*\[\s*\]',
        r'CodeGuard',
        r'ModificationLevel',
    ]
    
    SUSPICIOUS_PATTERNS = [
        r'curl\s+',
        r'wget\s+',
        r'requests\.(get|post)\s*\([^)]*http',
        r'base64\.b64decode',
        r'pickle\.loads',
        r'marshal\.loads',
        r'socket\.socket',
        r'telnetlib',
        r'ftplib',
    ]
    
    def __init__(
        self,
        base_dir: str = None,
        backup_dir: str = None,
        level: ModificationLevel = ModificationLevel.SKILLS_ONLY
    ):
        self.base_dir = Path(base_dir or os.getcwd())
        self.backup_dir = Path(backup_dir or self.base_dir / "code_backups")
        self.level = level
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.modification_log: List[ModificationRecord] = []
        self.log_file = self.backup_dir / "modification_log.json"
        
        self._load_log()
    
    def _load_log(self):
        if self.log_file.exists():
            try:
                import json
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        self.modification_log.append(ModificationRecord(**item))
            except Exception:
                pass
    
    def _save_log(self):
        try:
            import json
            data = []
            for record in self.modification_log:
                data.append({
                    "timestamp": record.timestamp,
                    "file_path": record.file_path,
                    "backup_path": record.backup_path,
                    "reason": record.reason,
                    "checksum_before": record.checksum_before,
                    "checksum_after": record.checksum_after,
                    "approved": record.approved
                })
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _get_checksum(self, file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _backup_file(self, file_path: str) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(file_path)
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        
        return str(backup_path)
    
    def is_protected(self, file_path: str) -> bool:
        rel_path = self._get_relative_path(file_path)
        
        if rel_path in self.PROTECTED_FILES:
            return True
        
        for protected_dir in self.PROTECTED_DIRECTORIES:
            if rel_path.startswith(protected_dir + "/"):
                return True
        
        return False
    
    def is_sandbox(self, file_path: str) -> bool:
        rel_path = self._get_relative_path(file_path)
        
        for sandbox_dir in self.SANDBOX_DIRECTORIES:
            if rel_path.startswith(sandbox_dir + "/") or rel_path.startswith(sandbox_dir + "\\"):
                return True
        
        return False
    
    def _get_relative_path(self, file_path: str) -> str:
        abs_path = os.path.abspath(file_path)
        base_abs = os.path.abspath(self.base_dir)
        
        if abs_path.startswith(base_abs):
            return os.path.relpath(abs_path, base_abs)
        
        return file_path
    
    def check_dangerous_code(self, code: str) -> Tuple[bool, List[str]]:
        dangers = []
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                dangers.append(f"危险模式: {pattern}")
        
        return len(dangers) > 0, dangers
    
    def check_suspicious_code(self, code: str) -> Tuple[bool, List[str]]:
        warnings = []
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                warnings.append(f"可疑模式: {pattern}")
        
        return len(warnings) > 0, warnings
    
    def can_modify(self, file_path: str) -> Dict[str, Any]:
        rel_path = self._get_relative_path(file_path)
        
        if self.level == ModificationLevel.NONE:
            return {
                "allowed": False,
                "reason": "当前模式禁止所有代码修改",
                "level": self.level.value
            }
        
        if self.is_protected(file_path):
            if self.level == ModificationLevel.FULL_WITH_APPROVAL:
                return {
                    "allowed": True,
                    "requires_approval": True,
                    "reason": "核心文件修改需要用户确认",
                    "file_type": "protected",
                    "level": self.level.value
                }
            else:
                return {
                    "allowed": False,
                    "reason": f"核心文件不可修改: {rel_path}",
                    "suggestion": "可以在 agent_skills/ 或 extensions/ 目录创建新功能",
                    "file_type": "protected",
                    "level": self.level.value
                }
        
        if self.is_sandbox(file_path):
            return {
                "allowed": True,
                "requires_approval": False,
                "reason": "沙盒区域，可以修改",
                "file_type": "sandbox",
                "level": self.level.value
            }
        
        if self.level == ModificationLevel.SKILLS_ONLY:
            return {
                "allowed": False,
                "reason": "当前模式只允许修改 agent_skills/ 目录",
                "suggestion": "请在 agent_skills/ 目录创建新技能",
                "file_type": "other",
                "level": self.level.value
            }
        
        if self.level == ModificationLevel.EXTENSIONS:
            return {
                "allowed": False,
                "reason": "当前模式只允许修改 agent_skills/ 和 extensions/ 目录",
                "suggestion": "请在沙盒目录创建新功能",
                "file_type": "other",
                "level": self.level.value
            }
        
        if self.level == ModificationLevel.FULL_WITH_APPROVAL:
            return {
                "allowed": True,
                "requires_approval": True,
                "reason": "非沙盒文件修改需要用户确认",
                "file_type": "other",
                "level": self.level.value
            }
        
        return {
            "allowed": False,
            "reason": "未知情况，默认禁止修改",
            "level": self.level.value
        }
    
    def request_modification(
        self,
        file_path: str,
        new_code: str,
        reason: str = "agent_request"
    ) -> Dict[str, Any]:
        permission = self.can_modify(file_path)
        
        if not permission["allowed"]:
            return {
                "success": False,
                "error": permission["reason"],
                "suggestion": permission.get("suggestion")
            }
        
        is_dangerous, dangers = self.check_dangerous_code(new_code)
        if is_dangerous:
            return {
                "success": False,
                "error": "代码包含危险模式",
                "dangers": dangers,
                "requires_approval": False
            }
        
        is_suspicious, warnings = self.check_suspicious_code(new_code)
        
        result = {
            "success": True,
            "can_proceed": True,
            "file_path": file_path,
            "requires_approval": permission.get("requires_approval", False),
            "warnings": warnings if is_suspicious else []
        }
        
        if permission.get("requires_approval"):
            result["approval_message"] = self._generate_approval_message(
                file_path, reason, warnings
            )
        
        return result
    
    def _generate_approval_message(
        self,
        file_path: str,
        reason: str,
        warnings: List[str]
    ) -> str:
        msg = f"⚠️ 代码修改请求\n\n"
        msg += f"文件: {file_path}\n"
        msg += f"原因: {reason}\n"
        
        if warnings:
            msg += f"\n⚠️ 警告:\n"
            for w in warnings:
                msg += f"  - {w}\n"
        
        msg += "\n是否允许此修改？"
        return msg
    
    def execute_modification(
        self,
        file_path: str,
        new_code: str,
        reason: str = "agent_request",
        approved: bool = False
    ) -> Dict[str, Any]:
        permission = self.can_modify(file_path)
        
        if not permission["allowed"]:
            return {
                "success": False,
                "error": permission["reason"]
            }
        
        if permission.get("requires_approval") and not approved:
            return {
                "success": False,
                "error": "此修改需要用户确认",
                "requires_approval": True
            }
        
        is_dangerous, dangers = self.check_dangerous_code(new_code)
        if is_dangerous:
            return {
                "success": False,
                "error": "代码包含危险模式，禁止执行",
                "dangers": dangers
            }
        
        try:
            checksum_before = ""
            backup_path = ""
            
            if os.path.exists(file_path):
                checksum_before = self._get_checksum(file_path)
                backup_path = self._backup_file(file_path)
            
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            checksum_after = self._get_checksum(file_path)
            
            record = ModificationRecord(
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                backup_path=backup_path,
                reason=reason,
                checksum_before=checksum_before,
                checksum_after=checksum_after,
                approved=approved
            )
            self.modification_log.append(record)
            self._save_log()
            
            return {
                "success": True,
                "message": f"文件已修改: {file_path}",
                "backup_path": backup_path,
                "checksum": checksum_after
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"修改失败: {str(e)}"
            }
    
    def rollback(self, steps: int = 1) -> Dict[str, Any]:
        if not self.modification_log:
            return {
                "success": False,
                "error": "没有可回滚的修改记录"
            }
        
        rolled_back = []
        
        for _ in range(min(steps, len(self.modification_log))):
            record = self.modification_log.pop()
            
            if record.backup_path and os.path.exists(record.backup_path):
                shutil.copy2(record.backup_path, record.file_path)
                rolled_back.append(record.file_path)
        
        self._save_log()
        
        return {
            "success": True,
            "rolled_back": rolled_back,
            "message": f"已回滚 {len(rolled_back)} 个修改"
        }
    
    def get_modification_history(self, limit: int = 10) -> List[Dict]:
        records = self.modification_log[-limit:]
        return [
            {
                "timestamp": r.timestamp,
                "file": r.file_path,
                "reason": r.reason,
                "approved": r.approved
            }
            for r in records
        ]
    
    def set_level(self, level: ModificationLevel):
        self.level = level
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "protected_files_count": len(self.PROTECTED_FILES),
            "protected_dirs_count": len(self.PROTECTED_DIRECTORIES),
            "sandbox_dirs": list(self.SANDBOX_DIRECTORIES),
            "modifications_count": len(self.modification_log),
            "backup_dir": str(self.backup_dir)
        }


_code_guard_instance = None


def get_code_guard(level: ModificationLevel = None) -> CodeGuard:
    global _code_guard_instance
    
    if _code_guard_instance is None:
        _code_guard_instance = CodeGuard(level=level or ModificationLevel.SKILLS_ONLY)
    elif level:
        _code_guard_instance.set_level(level)
    
    return _code_guard_instance
