"""
统一日志模块 - 规范化日志记录

特性:
1. 统一的日志格式
2. 支持多输出目标（控制台、文件）
3. 按模块配置日志级别
4. 支持结构化日志

借鉴 OpenClaw 设计哲学:
- 日志应该有用，而非冗余
- 关键操作必须记录
- 错误信息要包含上下文
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from functools import wraps


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_DIR = Path("./logs")


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（控制台用）"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


_loggers: Dict[str, logging.Logger] = {}
_handlers_configured = False


def setup_logging(
    level: int = logging.INFO,
    log_dir: str = None,
    enable_file: bool = True,
    enable_structured: bool = False
):
    """
    配置全局日志
    
    Args:
        level: 日志级别
        log_dir: 日志目录
        enable_file: 是否启用文件日志
        enable_structured: 是否使用结构化格式
    """
    global _handlers_configured
    
    if _handlers_configured:
        return
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if sys.stdout.isatty():
        console_formatter = ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT)
    else:
        console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    if enable_file:
        log_path = Path(log_dir) if log_dir else LOG_DIR
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / f"neo_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        
        if enable_structured:
            file_formatter = StructuredFormatter()
        else:
            file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    _handlers_configured = True


def get_logger(name: str, level: int = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称
        level: 日志级别（可选）
        
    Returns:
        配置好的日志器
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    
    _loggers[name] = logger
    return logger


def log_execution(logger: logging.Logger, level: int = logging.INFO):
    """
    函数执行日志装饰器
    
    Args:
        logger: 日志器
        level: 日志级别
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.log(level, f"开始执行: {func_name}")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(level, f"执行完成: {func_name} (耗时: {elapsed:.3f}s)")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"执行失败: {func_name} (耗时: {elapsed:.3f}s) - {e}")
                raise
        
        return wrapper
    return decorator


def log_skill_call(skill_name: str, args: Dict, result: Dict = None, error: str = None):
    """
    记录技能调用
    
    Args:
        skill_name: 技能名称
        args: 调用参数
        result: 执行结果
        error: 错误信息
    """
    logger = get_logger("neo.skills")
    
    log_data = {
        "skill": skill_name,
        "args_preview": str(args)[:200] if args else None,
        "success": error is None,
        "error": error
    }
    
    if error:
        logger.error(f"技能调用失败: {skill_name} - {error}", extra={"extra_data": log_data})
    else:
        logger.info(f"技能调用成功: {skill_name}", extra={"extra_data": log_data})


def log_tool_execution(tool_name: str, iteration: int, success: bool, message: str = ""):
    """
    记录工具执行
    
    Args:
        tool_name: 工具名称
        iteration: 迭代次数
        success: 是否成功
        message: 附加消息
    """
    logger = get_logger("neo.tools")
    
    status = "✅" if success else "❌"
    logger.info(f"[迭代 {iteration}] {status} 工具: {tool_name} - {message}")


def log_llm_request(messages_count: int, tools_count: int, model: str):
    """
    记录 LLM 请求
    
    Args:
        messages_count: 消息数量
        tools_count: 工具数量
        model: 模型名称
    """
    logger = get_logger("neo.llm")
    logger.debug(f"LLM 请求: {messages_count} 条消息, {tools_count} 个工具, 模型: {model}")


def log_llm_response(has_tool_calls: bool, content_preview: str = None):
    """
    记录 LLM 响应
    
    Args:
        has_tool_calls: 是否有工具调用
        content_preview: 内容预览
    """
    logger = get_logger("neo.llm")
    
    if has_tool_calls:
        logger.debug(f"LLM 响应: 包含工具调用")
    else:
        preview = content_preview[:100] if content_preview else ""
        logger.debug(f"LLM 响应: {preview}...")


def log_memory_operation(operation: str, key: str = None, details: Dict = None):
    """
    记录记忆操作
    
    Args:
        operation: 操作类型
        key: 记忆键
        details: 详细信息
    """
    logger = get_logger("neo.memory")
    logger.debug(f"记忆操作: {operation}" + (f" - {key}" if key else ""))


def log_security_event(event_type: str, details: Dict):
    """
    记录安全事件
    
    Args:
        event_type: 事件类型
        details: 详细信息
    """
    logger = get_logger("neo.security")
    logger.warning(f"安全事件: {event_type}", extra={"extra_data": details})


def log_browser_action(action: str, target: str = None, success: bool = True):
    """
    记录浏览器操作
    
    Args:
        action: 操作类型
        target: 目标
        success: 是否成功
    """
    logger = get_logger("neo.browser")
    status = "成功" if success else "失败"
    logger.info(f"浏览器操作: {action}" + (f" -> {target}" if target else "") + f" [{status}]")


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"开始: {self.operation}", extra={"extra_data": self.context})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"失败: {self.operation} (耗时: {elapsed:.3f}s) - {exc_val}",
                extra={"extra_data": self.context}
            )
        else:
            self.logger.info(
                f"完成: {self.operation} (耗时: {elapsed:.3f}s)",
                extra={"extra_data": self.context}
            )
        
        return False


setup_logging()
