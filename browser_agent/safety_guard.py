"""
安全护栏系统 - 控制Browser Agent的操作权限

核心功能:
1. 操作分级: 安全/需确认/禁止
2. 敏感操作拦截
3. 行为审计日志
4. 用户确认机制
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field


class OperationLevel(Enum):
    SAFE = "safe"
    CONFIRM_REQUIRED = "confirm_required"
    FORBIDDEN = "forbidden"


@dataclass
class AuditLog:
    timestamp: str
    action: str
    target: str
    level: OperationLevel
    approved: bool
    result: str
    details: Dict = field(default_factory=dict)


class SafetyGuard:
    """
    安全护栏 - 控制浏览器操作的安全性
    
    操作分级:
    - safe: 自动执行，无需确认
    - confirm_required: 需要用户确认
    - forbidden: 禁止执行
    """
    
    SAFE_OPERATIONS = {
        "navigate", "read", "scroll", "screenshot", 
        "extract", "wait", "get_title", "get_url"
    }
    
    CONFIRM_REQUIRED_OPERATIONS = {
        "click", "fill", "login", "search", 
        "submit", "select", "upload"
    }
    
    FORBIDDEN_OPERATIONS = {
        "payment", "delete", "publish", "modify_settings",
        "download_file", "execute_script", "install_extension"
    }
    
    SENSITIVE_SELECTORS = {
        "payment", "checkout", "buy", "purchase", "pay",
        "delete", "remove", "trash",
        "submit", "post", "publish", "send",
        "settings", "config", "admin"
    }
    
    MAX_URL_LENGTH = 2048
    MAX_INPUT_LENGTH = 10000
    
    def __init__(self, audit_log_path: str = "browser_agent/audit_logs"):
        self.audit_log_path = audit_log_path
        self.session_confirmations: Dict[str, bool] = {}
        self.audit_logs: List[AuditLog] = []
        
        os.makedirs(audit_log_path, exist_ok=True)
    
    def classify_operation(self, action: str, target: str = "", value: str = "") -> OperationLevel:
        action_lower = action.lower()
        
        if action_lower in self.FORBIDDEN_OPERATIONS:
            return OperationLevel.FORBIDDEN
        
        for forbidden in self.FORBIDDEN_OPERATIONS:
            if forbidden in action_lower or forbidden in target.lower():
                return OperationLevel.FORBIDDEN
        
        if action_lower in self.SAFE_OPERATIONS:
            return OperationLevel.SAFE
        
        if action_lower in self.CONFIRM_REQUIRED_OPERATIONS:
            return OperationLevel.CONFIRM_REQUIRED
        
        for sensitive in self.SENSITIVE_SELECTORS:
            if sensitive in target.lower() or sensitive in value.lower():
                return OperationLevel.CONFIRM_REQUIRED
        
        return OperationLevel.CONFIRM_REQUIRED
    
    def check_operation(
        self, 
        action: str, 
        target: str = "", 
        value: str = "",
        auto_confirm: bool = False,
        confirmation_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        level = self.classify_operation(action, target, value)
        
        validation_result = self._validate_inputs(action, target, value)
        if not validation_result["valid"]:
            return {
                "allowed": False,
                "level": level.value,
                "reason": validation_result["reason"],
                "requires_confirmation": False
            }
        
        if level == OperationLevel.FORBIDDEN:
            self._log_audit(action, target, level, False, "操作被禁止")
            return {
                "allowed": False,
                "level": level.value,
                "reason": f"操作 '{action}' 被安全策略禁止",
                "requires_confirmation": False
            }
        
        if level == OperationLevel.SAFE:
            self._log_audit(action, target, level, True, "安全操作，自动批准")
            return {
                "allowed": True,
                "level": level.value,
                "reason": "安全操作",
                "requires_confirmation": False
            }
        
        if level == OperationLevel.CONFIRM_REQUIRED:
            session_key = f"{action}:{target}"
            
            if session_key in self.session_confirmations:
                self._log_audit(action, target, level, True, "会话内已确认")
                return {
                    "allowed": True,
                    "level": level.value,
                    "reason": "会话内已确认",
                    "requires_confirmation": False
                }
            
            if auto_confirm:
                self._log_audit(action, target, level, True, "自动确认模式")
                return {
                    "allowed": True,
                    "level": level.value,
                    "reason": "自动确认",
                    "requires_confirmation": False
                }
            
            if confirmation_callback:
                user_confirmed = confirmation_callback(action, target, value)
                if user_confirmed:
                    self.session_confirmations[session_key] = True
                    self._log_audit(action, target, level, True, "用户确认通过")
                    return {
                        "allowed": True,
                        "level": level.value,
                        "reason": "用户已确认",
                        "requires_confirmation": False
                    }
                else:
                    self._log_audit(action, target, level, False, "用户拒绝")
                    return {
                        "allowed": False,
                        "level": level.value,
                        "reason": "用户拒绝操作",
                        "requires_confirmation": False
                    }
            
            self._log_audit(action, target, level, False, "等待确认")
            return {
                "allowed": False,
                "level": level.value,
                "reason": "需要用户确认",
                "requires_confirmation": True,
                "confirmation_message": self._generate_confirmation_message(action, target, value)
            }
        
        return {
            "allowed": False,
            "level": level.value,
            "reason": "未知操作级别",
            "requires_confirmation": False
        }
    
    def _validate_inputs(self, action: str, target: str, value: str) -> Dict[str, Any]:
        if len(target) > self.MAX_URL_LENGTH:
            return {"valid": False, "reason": f"目标长度超过限制 ({self.MAX_URL_LENGTH})"}
        
        if len(value) > self.MAX_INPUT_LENGTH:
            return {"valid": False, "reason": f"输入值长度超过限制 ({self.MAX_INPUT_LENGTH})"}
        
        if action.lower() == "navigate":
            if target and not self._is_safe_url(target):
                return {"valid": False, "reason": "URL不安全或协议不被允许"}
        
        return {"valid": True}
    
    def _is_safe_url(self, url: str) -> bool:
        allowed_schemes = {"http", "https"}
        dangerous_patterns = {
            "javascript:", "data:", "vbscript:",
            "file://", "ftp://"
        }
        
        url_lower = url.lower().strip()
        
        for pattern in dangerous_patterns:
            if url_lower.startswith(pattern):
                return False
        
        if not any(url_lower.startswith(scheme + "://") for scheme in allowed_schemes):
            if not url_lower.startswith("/") and not url_lower.startswith("."):
                return False
        
        return True
    
    def _generate_confirmation_message(self, action: str, target: str, value: str) -> str:
        action_descriptions = {
            "click": f"点击元素: {target}",
            "fill": f"在 {target} 中输入内容",
            "login": f"登录到网站",
            "search": f"搜索: {target}",
            "submit": f"提交表单: {target}",
            "select": f"选择选项: {target}",
            "upload": f"上传文件到: {target}"
        }
        
        desc = action_descriptions.get(action.lower(), f"执行操作: {action}")
        if value and len(value) < 100:
            desc += f" (内容: {value[:50]}...)" if len(value) > 50 else f" (内容: {value})"
        
        return f"⚠️ Browser Agent 请求确认:\n{desc}\n\n是否允许此操作？"
    
    def _log_audit(
        self, 
        action: str, 
        target: str, 
        level: OperationLevel, 
        approved: bool, 
        result: str
    ):
        log = AuditLog(
            timestamp=datetime.now().isoformat(),
            action=action,
            target=target[:200],
            level=level,
            approved=approved,
            result=result
        )
        self.audit_logs.append(log)
    
    def save_audit_logs(self, filename: str = None) -> str:
        if not filename:
            filename = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.audit_log_path, filename)
        
        logs_data = [
            {
                "timestamp": log.timestamp,
                "action": log.action,
                "target": log.target,
                "level": log.level.value,
                "approved": log.approved,
                "result": log.result,
                "details": log.details
            }
            for log in self.audit_logs
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_session_summary(self) -> Dict[str, Any]:
        if not self.audit_logs:
            return {"total_operations": 0}
        
        safe_count = sum(1 for log in self.audit_logs if log.level == OperationLevel.SAFE)
        confirmed_count = sum(1 for log in self.audit_logs if log.level == OperationLevel.CONFIRM_REQUIRED)
        forbidden_count = sum(1 for log in self.audit_logs if log.level == OperationLevel.FORBIDDEN)
        approved_count = sum(1 for log in self.audit_logs if log.approved)
        
        return {
            "total_operations": len(self.audit_logs),
            "safe_operations": safe_count,
            "confirmed_operations": confirmed_count,
            "forbidden_attempts": forbidden_count,
            "approved_operations": approved_count,
            "approval_rate": approved_count / len(self.audit_logs) if self.audit_logs else 0
        }
    
    def clear_session_confirmations(self):
        self.session_confirmations.clear()
    
    def add_safe_operation(self, operation: str):
        self.SAFE_OPERATIONS.add(operation.lower())
    
    def add_forbidden_operation(self, operation: str):
        self.FORBIDDEN_OPERATIONS.add(operation.lower())
