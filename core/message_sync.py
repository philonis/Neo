"""
消息同步服务 - 实现 Web 端与 Telegram 机器人的对话同步

功能:
1. 统一消息存储：所有对话消息（Web/Telegram）存储在同一队列
2. 消息来源标识：区分消息来源（web/telegram）
3. 实时同步：Web 端可实时查看 Telegram 消息
4. 双向发送：Web 端可向 Telegram 发送消息

使用方式:
- Web 端通过 Streamlit session_state 访问消息
- Telegram 端通过回调函数更新消息队列
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
from collections import deque


class MessageSource(Enum):
    """消息来源"""
    WEB = "web"
    TELEGRAM = "telegram"
    SYSTEM = "system"


class MessageType(Enum):
    """消息类型"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class SyncMessage:
    """同步消息"""
    id: str
    source: str  # web, telegram, system
    type: str    # user, assistant, system
    content: str
    timestamp: float
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SyncMessage':
        return cls(**data)


class MessageSyncService:
    """
    消息同步服务（单例模式）
    
    核心功能:
    - 统一消息队列：所有平台消息存储在一起
    - 消息持久化：保存到文件，重启后恢复
    - 回调通知：新消息时通知订阅者
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, storage_dir: str = "./sync_messages"):
        if self._initialized:
            return
        
        self._initialized = True
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.messages_file = self.storage_dir / "messages.json"
        self.config_file = self.storage_dir / "config.json"
        
        self._messages: deque = deque(maxlen=1000)
        self._subscribers: List[Callable] = []
        self._lock = threading.Lock()
        
        self.telegram_service = None
        self.agent = None
        
        self._load_messages()
    
    @classmethod
    def get_instance(cls) -> 'MessageSyncService':
        return cls()
    
    def _load_messages(self):
        if self.messages_file.exists():
            try:
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for msg_data in data.get('messages', []):
                        self._messages.append(SyncMessage.from_dict(msg_data))
            except (json.JSONDecodeError, IOError, OSError):
                pass
    
    def _save_messages(self):
        try:
            data = {
                'messages': [msg.to_dict() for msg in self._messages],
                'updated_at': datetime.now().isoformat()
            }
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def _generate_id(self) -> str:
        return f"{int(time.time() * 1000)}_{threading.current_thread().ident}"
    
    def add_message(
        self,
        content: str,
        source: str,
        msg_type: str,
        metadata: Dict = None
    ) -> SyncMessage:
        """
        添加消息到队列
        
        Args:
            content: 消息内容
            source: 来源 (web/telegram/system)
            msg_type: 类型 (user/assistant/system)
            metadata: 额外元数据
            
        Returns:
            创建的消息对象
        """
        message = SyncMessage(
            id=self._generate_id(),
            source=source,
            type=msg_type,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self._messages.append(message)
            self._save_messages()
        
        self._notify_subscribers(message)
        
        return message
    
    def add_user_message(self, content: str, source: str = "web", metadata: Dict = None) -> SyncMessage:
        """添加用户消息"""
        return self.add_message(content, source, "user", metadata)
    
    def add_assistant_message(self, content: str, source: str = "web", metadata: Dict = None) -> SyncMessage:
        """添加助手消息"""
        return self.add_message(content, source, "assistant", metadata)
    
    def add_system_message(self, content: str, metadata: Dict = None) -> SyncMessage:
        """添加系统消息"""
        return self.add_message(content, "system", "system", metadata)
    
    def get_messages(
        self,
        limit: int = 50,
        source: str = None,
        since_timestamp: float = None
    ) -> List[Dict]:
        """
        获取消息列表
        
        Args:
            limit: 最大数量
            source: 过滤来源
            since_timestamp: 获取此时间戳之后的消息
            
        Returns:
            消息字典列表
        """
        with self._lock:
            messages = list(self._messages)
        
        if source:
            messages = [m for m in messages if m.source == source]
        
        if since_timestamp:
            messages = [m for m in messages if m.timestamp > since_timestamp]
        
        messages = messages[-limit:]
        
        return [m.to_dict() for m in messages]
    
    def get_all_messages(self) -> List[Dict]:
        """获取所有消息"""
        with self._lock:
            return [m.to_dict() for m in self._messages]
    
    def clear_messages(self):
        """清空消息"""
        with self._lock:
            self._messages.clear()
            self._save_messages()
    
    def subscribe(self, callback: Callable):
        """订阅新消息通知"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self, message: SyncMessage):
        """通知所有订阅者"""
        for callback in self._subscribers:
            try:
                callback(message.to_dict())
            except Exception:
                pass
    
    def set_telegram_service(self, telegram_service):
        """设置 Telegram 服务实例"""
        self.telegram_service = telegram_service
    
    def set_agent(self, agent):
        """设置 Agent 实例"""
        self.agent = agent
    
    def process_user_message(
        self,
        content: str,
        source: str = "web",
        metadata: Dict = None
    ) -> Dict:
        """
        处理用户消息（统一入口）
        
        流程:
        1. 添加用户消息到队列
        2. 调用 Agent 处理
        3. 添加助手回复到队列
        4. 如果来源是 Web，同步发送到 Telegram
        5. 如果来源是 Telegram，回复到 Telegram
        
        Args:
            content: 用户消息内容
            source: 消息来源
            metadata: 额外元数据
            
        Returns:
            处理结果
        """
        self.add_user_message(content, source, metadata)
        
        if self.agent:
            try:
                result = self.agent.run(content, context=[])
                response = result.get('response', '') if result.get('success') else f"处理失败: {result.get('response', '未知错误')}"
            except Exception as e:
                response = f"处理出错: {e}"
        else:
            response = "Agent 未初始化"
        
        self.add_assistant_message(response, source, metadata)
        
        if source == "web" and self.telegram_service:
            sync_to_telegram = metadata.get('sync_to_telegram', True) if metadata else True
            if sync_to_telegram:
                self.telegram_service.send_rich_message(f"💬 [Web] 用户: {content}\n\n🤖 助手: {response}")
        
        return {
            'success': True,
            'response': response,
            'source': source
        }
    
    def process_telegram_message(
        self,
        chat_id: str,
        text: str,
        username: str = None
    ) -> str:
        """
        处理 Telegram 消息
        
        Args:
            chat_id: Telegram Chat ID
            text: 消息内容
            username: 用户名
            
        Returns:
            回复内容
        """
        metadata = {
            'chat_id': chat_id,
            'username': username,
            'sync_to_telegram': False
        }
        
        result = self.process_user_message(text, "telegram", metadata)
        response = result.get('response', '')
        
        return response
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            messages = list(self._messages)
        
        source_counts = {}
        type_counts = {}
        
        for msg in messages:
            source_counts[msg.source] = source_counts.get(msg.source, 0) + 1
            type_counts[msg.type] = type_counts.get(msg.type, 0) + 1
        
        return {
            'total_messages': len(messages),
            'source_distribution': source_counts,
            'type_distribution': type_counts,
            'telegram_connected': self.telegram_service is not None,
            'agent_connected': self.agent is not None
        }


_sync_service_instance: Optional[MessageSyncService] = None


def get_sync_service() -> MessageSyncService:
    """获取消息同步服务单例"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = MessageSyncService()
    return _sync_service_instance
