"""
会话管理器 - 管理浏览器会话和凭证存储

核心功能:
1. Cookie/Session持久化
2. 凭证管理（加密存储）
3. 会话状态追踪
4. 多账号支持
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class SessionState:
    session_id: str
    site_domain: str
    created_at: datetime
    last_active: datetime
    cookies: list = field(default_factory=list)
    local_storage: dict = field(default_factory=dict)
    is_logged_in: bool = False
    username: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass 
class Credential:
    site_domain: str
    username: str
    password_encrypted: str
    created_at: datetime
    last_used: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


class SessionManager:
    """
    会话管理器
    
    功能:
    - 持久化浏览器会话（Cookie、LocalStorage）
    - 安全存储凭证
    - 会话过期管理
    - 多站点会话支持
    """
    
    DEFAULT_SESSION_DIR = "browser_agent/sessions"
    DEFAULT_CREDENTIALS_FILE = "browser_agent/credentials.enc"
    SESSION_EXPIRE_DAYS = 7
    
    def __init__(
        self, 
        session_dir: str = None,
        credentials_file: str = None,
        encryption_key: str = None
    ):
        self.session_dir = Path(session_dir or self.DEFAULT_SESSION_DIR)
        self.credentials_file = Path(credentials_file or self.DEFAULT_CREDENTIALS_FILE)
        
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.encryption_key = encryption_key or os.environ.get("NEO_BROWSER_KEY", "default-key-change-me")
        
        self.active_sessions: Dict[str, SessionState] = {}
        self.credentials: Dict[str, Credential] = {}
        
        self._load_credentials()
    
    def _derive_key(self, key: str) -> bytes:
        return hashlib.sha256(key.encode()).digest()
    
    def _encrypt(self, data: str) -> str:
        key = self._derive_key(self.encryption_key)
        encoded = data.encode('utf-8')
        xored = bytes(a ^ b for a, b in zip(encoded, key * (len(encoded) // len(key) + 1)))
        return base64.b64encode(xored).decode('ascii')
    
    def _decrypt(self, encrypted: str) -> str:
        key = self._derive_key(self.encryption_key)
        encoded = base64.b64decode(encrypted.encode('ascii'))
        xored = bytes(a ^ b for a, b in zip(encoded, key * (len(encoded) // len(key) + 1)))
        return xored.decode('utf-8')
    
    def _get_domain_key(self, url: str) -> str:
        match = re.search(r'://([^/]+)', url)
        if match:
            domain = match.group(1)
            return domain.split('.')[-2] if len(domain.split('.')) > 1 else domain
        return "default"
    
    def _get_session_file(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"
    
    def create_session(self, site_url: str) -> SessionState:
        domain = self._get_domain_key(site_url)
        session_id = f"{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = SessionState(
            session_id=session_id,
            site_domain=domain,
            created_at=datetime.now(),
            last_active=datetime.now(),
            expires_at=datetime.now() + timedelta(days=self.SESSION_EXPIRE_DAYS)
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        session = self.active_sessions.get(session_id)
        if session:
            if session.expires_at and datetime.now() > session.expires_at:
                self.delete_session(session_id)
                return None
            session.last_active = datetime.now()
        return session
    
    def get_session_for_site(self, site_url: str) -> Optional[SessionState]:
        domain = self._get_domain_key(site_url)
        for session in self.active_sessions.values():
            if session.site_domain == domain and session.is_logged_in:
                if session.expires_at and datetime.now() > session.expires_at:
                    continue
                return session
        return None
    
    def update_session(
        self, 
        session_id: str, 
        cookies: list = None,
        local_storage: dict = None,
        is_logged_in: bool = None,
        username: str = None
    ) -> bool:
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        if cookies is not None:
            session.cookies = cookies
        if local_storage is not None:
            session.local_storage = local_storage
        if is_logged_in is not None:
            session.is_logged_in = is_logged_in
        if username is not None:
            session.username = username
        
        session.last_active = datetime.now()
        self._save_session(session)
        return True
    
    def _save_session(self, session: SessionState):
        session_file = self._get_session_file(session.session_id)
        
        data = {
            "session_id": session.session_id,
            "site_domain": session.site_domain,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "cookies": session.cookies,
            "local_storage": session.local_storage,
            "is_logged_in": session.is_logged_in,
            "username": session.username,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_session(self, session_id: str) -> Optional[SessionState]:
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = SessionState(
                session_id=data["session_id"],
                site_domain=data["site_domain"],
                created_at=datetime.fromisoformat(data["created_at"]),
                last_active=datetime.fromisoformat(data["last_active"]),
                cookies=data.get("cookies", []),
                local_storage=data.get("local_storage", {}),
                is_logged_in=data.get("is_logged_in", False),
                username=data.get("username"),
                expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            )
            
            if session.expires_at and datetime.now() > session.expires_at:
                self.delete_session(session_id)
                return None
            
            self.active_sessions[session_id] = session
            return session
            
        except Exception as e:
            print(f"[SessionManager] 加载会话失败: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            session_file.unlink()
        
        return True
    
    def save_credentials(self, site_url: str, username: str, password: str, metadata: dict = None):
        domain = self._get_domain_key(site_url)
        encrypted_password = self._encrypt(password)
        
        credential = Credential(
            site_domain=domain,
            username=username,
            password_encrypted=encrypted_password,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.credentials[domain] = credential
        self._save_credentials()
    
    def get_credentials(self, site_url: str) -> Optional[Dict[str, str]]:
        domain = self._get_domain_key(site_url)
        credential = self.credentials.get(domain)
        
        if not credential:
            return None
        
        try:
            password = self._decrypt(credential.password_encrypted)
            credential.last_used = datetime.now()
            return {
                "username": credential.username,
                "password": password
            }
        except Exception:
            return None
    
    def has_credentials(self, site_url: str) -> bool:
        domain = self._get_domain_key(site_url)
        return domain in self.credentials
    
    def _save_credentials(self):
        data = {}
        for domain, cred in self.credentials.items():
            data[domain] = {
                "site_domain": cred.site_domain,
                "username": cred.username,
                "password_encrypted": cred.password_encrypted,
                "created_at": cred.created_at.isoformat(),
                "last_used": cred.last_used.isoformat() if cred.last_used else None,
                "metadata": cred.metadata
            }
        
        with open(self.credentials_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_credentials(self):
        if not self.credentials_file.exists():
            return
        
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for domain, cred_data in data.items():
                credential = Credential(
                    site_domain=cred_data["site_domain"],
                    username=cred_data["username"],
                    password_encrypted=cred_data["password_encrypted"],
                    created_at=datetime.fromisoformat(cred_data["created_at"]),
                    last_used=datetime.fromisoformat(cred_data["last_used"]) if cred_data.get("last_used") else None,
                    metadata=cred_data.get("metadata", {})
                )
                self.credentials[domain] = credential
                
        except Exception as e:
            print(f"[SessionManager] 加载凭证失败: {e}")
    
    def delete_credentials(self, site_url: str) -> bool:
        domain = self._get_domain_key(site_url)
        if domain in self.credentials:
            del self.credentials[domain]
            self._save_credentials()
            return True
        return False
    
    def list_saved_sites(self) -> list:
        return [
            {
                "domain": domain,
                "username": cred.username,
                "has_session": any(s.site_domain == domain and s.is_logged_in for s in self.active_sessions.values()),
                "last_used": cred.last_used.isoformat() if cred.last_used else None
            }
            for domain, cred in self.credentials.items()
        ]
    
    def cleanup_expired_sessions(self) -> int:
        expired = []
        for session_id, session in self.active_sessions.items():
            if session.expires_at and datetime.now() > session.expires_at:
                expired.append(session_id)
        
        for session_id in expired:
            self.delete_session(session_id)
        
        return len(expired)
