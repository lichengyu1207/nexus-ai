"""
五端统一认证中心
Five-End Unified Authentication Center

实现OAuth2.0/OIDC统一认证，支持跨端单点登录
"""

import asyncio
import json
import uuid
import time
import hashlib
import secrets
import base64
import hmac
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EndType(Enum):
    GOV = "gov"
    ENTERPRISE = "enterprise"
    EDU = "edu"
    STD = "std"
    PUBLIC = "public"


class TokenType(Enum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
    AUTHORIZATION_CODE = "authorization_code"


class GrantType(Enum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    PASSWORD = "password"


class AuthScope(Enum):
    OPENID = "openid"
    PROFILE = "profile"
    EMAIL = "email"
    VALUATION = "valuation"
    REPORT = "report"
    EDUCATION = "education"
    GOVERNMENT = "government"
    STANDARD = "standard"
    ADMIN = "admin"


END_PERMISSIONS = {
    EndType.GOV: [AuthScope.OPENID, AuthScope.PROFILE, AuthScope.GOVERNMENT, AuthScope.ADMIN],
    EndType.ENTERPRISE: [AuthScope.OPENID, AuthScope.PROFILE, AuthScope.VALUATION, AuthScope.REPORT],
    EndType.EDU: [AuthScope.OPENID, AuthScope.PROFILE, AuthScope.EDUCATION],
    EndType.STD: [AuthScope.OPENID, AuthScope.PROFILE, AuthScope.STANDARD],
    EndType.PUBLIC: [AuthScope.OPENID, AuthScope.PROFILE],
}


@dataclass
class UserIdentity:
    user_id: str
    username: str
    email: str
    phone: Optional[str] = None
    display_name: str = ""
    avatar_url: str = ""
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    end_access: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "roles": self.roles,
            "permissions": self.permissions,
            "end_access": self.end_access,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def has_end_access(self, end_type: EndType) -> bool:
        return end_type.value in self.end_access
    
    def get_end_permissions(self, end_type: EndType) -> List[str]:
        return self.end_access.get(end_type.value, {}).get("permissions", [])


@dataclass
class OAuthClient:
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    allowed_grants: List[GrantType]
    allowed_scopes: List[AuthScope]
    end_type: EndType
    is_trusted: bool = False
    token_lifetime: int = 3600
    refresh_lifetime: int = 86400 * 30
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_name": self.client_name,
            "redirect_uris": self.redirect_uris,
            "allowed_grants": [g.value for g in self.allowed_grants],
            "allowed_scopes": [s.value for s in self.allowed_scopes],
            "end_type": self.end_type.value,
            "is_trusted": self.is_trusted,
            "token_lifetime": self.token_lifetime,
            "refresh_lifetime": self.refresh_lifetime,
        }
    
    def validate_redirect_uri(self, redirect_uri: str) -> bool:
        return redirect_uri in self.redirect_uris
    
    def validate_grant(self, grant_type: GrantType) -> bool:
        return grant_type in self.allowed_grants
    
    def validate_scope(self, scopes: List[AuthScope]) -> bool:
        return all(s in self.allowed_scopes for s in scopes)


@dataclass
class Token:
    token_id: str
    token_type: TokenType
    user_id: str
    client_id: str
    scopes: List[AuthScope]
    value: str
    expires_at: float
    issued_at: float = field(default_factory=time.time)
    revoked: bool = False
    revoked_at: Optional[float] = None
    end_type: Optional[EndType] = None
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "token_type": self.token_type.value,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "scopes": [s.value for s in self.scopes],
            "value": self.value,
            "expires_at": self.expires_at,
            "issued_at": self.issued_at,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at,
            "end_type": self.end_type.value if self.end_type else None,
            "session_id": self.session_id,
        }
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired()


@dataclass
class AuthSession:
    session_id: str
    user_id: str
    client_id: str
    end_type: EndType
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    expires_at: float = 0
    ip_address: str = ""
    user_agent: str = ""
    device_fingerprint: str = ""
    tokens: List[str] = field(default_factory=list)
    cross_end_sessions: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.expires_at == 0:
            self.expires_at = self.created_at + 86400
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "end_type": self.end_type.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "expires_at": self.expires_at,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "tokens": self.tokens,
            "cross_end_sessions": self.cross_end_sessions,
        }
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def update_activity(self) -> None:
        self.last_activity = time.time()


@dataclass
class AuthorizationCode:
    code_id: str
    code: str
    user_id: str
    client_id: str
    redirect_uri: str
    scopes: List[AuthScope]
    code_challenge: Optional[str] = None
    code_challenge_method: str = "S256"
    nonce: str = ""
    state: str = ""
    expires_at: float = 0
    issued_at: float = field(default_factory=time.time)
    used: bool = False
    used_at: Optional[float] = None
    
    def __post_init__(self):
        if self.expires_at == 0:
            self.expires_at = self.issued_at + 600
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def is_valid(self) -> bool:
        return not self.used and not self.is_expired()
    
    def verify_code_verifier(self, code_verifier: str) -> bool:
        if not self.code_challenge:
            return True
        
        if self.code_challenge_method == "S256":
            expected = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip("=")
            return expected == self.code_challenge
        return code_verifier == self.code_challenge


class TokenGenerator:
    JWT_SECRET = "five-end-jwt-secret-key-change-in-production"
    
    @classmethod
    def generate_access_token(cls) -> str:
        return secrets.token_urlsafe(32)
    
    @classmethod
    def generate_refresh_token(cls) -> str:
        return secrets.token_urlsafe(48)
    
    @classmethod
    def generate_authorization_code(cls) -> str:
        return secrets.token_urlsafe(24)
    
    @classmethod
    def generate_code_challenge(cls, code_verifier: str) -> str:
        return base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip("=")
    
    @classmethod
    def generate_id_token(cls, payload: Dict[str, Any], secret: str) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")
        
        signature = hmac.new(
            secret.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"


class UnifiedAuthCenter:
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client
        
        self._users: Dict[str, UserIdentity] = {}
        self._clients: Dict[str, OAuthClient] = {}
        self._tokens: Dict[str, Token] = {}
        self._sessions: Dict[str, AuthSession] = {}
        self._auth_codes: Dict[str, AuthorizationCode] = {}
        
        self._token_index: Dict[str, str] = {}
        self._code_index: Dict[str, str] = {}
        self._user_sessions: Dict[str, Set[str]] = defaultdict(set)
        
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        self._initialize_default_clients()
    
    def _initialize_default_clients(self) -> None:
        default_clients = [
            {
                "client_id": "gov_client",
                "client_secret": secrets.token_urlsafe(32),
                "client_name": "政府监管端",
                "redirect_uris": ["http://localhost:3000/callback", "http://localhost:5173/callback"],
                "allowed_grants": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
                "allowed_scopes": END_PERMISSIONS[EndType.GOV],
                "end_type": EndType.GOV,
            },
            {
                "client_id": "enterprise_client",
                "client_secret": secrets.token_urlsafe(32),
                "client_name": "企业经营端",
                "redirect_uris": ["http://localhost:3001/callback", "http://localhost:5174/callback"],
                "allowed_grants": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
                "allowed_scopes": END_PERMISSIONS[EndType.ENTERPRISE],
                "end_type": EndType.ENTERPRISE,
            },
            {
                "client_id": "edu_client",
                "client_secret": secrets.token_urlsafe(32),
                "client_name": "院校实训端",
                "redirect_uris": ["http://localhost:3002/callback", "http://localhost:5175/callback"],
                "allowed_grants": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
                "allowed_scopes": END_PERMISSIONS[EndType.EDU],
                "end_type": EndType.EDU,
            },
            {
                "client_id": "std_client",
                "client_secret": secrets.token_urlsafe(32),
                "client_name": "行业标准端",
                "redirect_uris": ["http://localhost:3003/callback", "http://localhost:5176/callback"],
                "allowed_grants": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
                "allowed_scopes": END_PERMISSIONS[EndType.STD],
                "end_type": EndType.STD,
            },
            {
                "client_id": "public_client",
                "client_secret": secrets.token_urlsafe(32),
                "client_name": "公众服务端",
                "redirect_uris": ["http://localhost:3004/callback", "http://localhost:5177/callback"],
                "allowed_grants": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN, GrantType.IMPLICIT],
                "allowed_scopes": END_PERMISSIONS[EndType.PUBLIC],
                "end_type": EndType.PUBLIC,
            },
        ]
        
        for client_data in default_clients:
            client = OAuthClient(**client_data)
            self._clients[client.client_id] = client
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._cleanup_expired()))
        logger.info("UnifiedAuthCenter started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("UnifiedAuthCenter stopped")
    
    async def register_user(self, username: str, email: str,
                             password: str = None,
                             roles: List[str] = None,
                             end_access: Dict[str, Dict[str, Any]] = None) -> UserIdentity:
        async with self._lock:
            user_id = str(uuid.uuid4())
            
            user = UserIdentity(
                user_id=user_id,
                username=username,
                email=email,
                roles=roles or ["user"],
                end_access=end_access or {"public": {"permissions": ["read"]}},
            )
            
            self._users[user_id] = user
            logger.info(f"User {username} registered with id {user_id}")
            return user
    
    async def get_user(self, user_id: str) -> Optional[UserIdentity]:
        return self._users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[UserIdentity]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None
    
    async def update_user_end_access(self, user_id: str, 
                                       end_type: EndType,
                                       permissions: List[str]) -> bool:
        async with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False
            
            user.end_access[end_type.value] = {
                "permissions": permissions,
                "granted_at": time.time(),
            }
            user.updated_at = time.time()
            return True
    
    async def create_authorization_code(self, client_id: str, user_id: str,
                                         redirect_uri: str, scopes: List[AuthScope],
                                         code_challenge: str = None,
                                         code_challenge_method: str = "S256",
                                         nonce: str = "", state: str = "") -> str:
        async with self._lock:
            client = self._clients.get(client_id)
            if not client:
                raise ValueError(f"Client {client_id} not found")
            
            if not client.validate_redirect_uri(redirect_uri):
                raise ValueError(f"Invalid redirect_uri: {redirect_uri}")
            
            if not client.validate_scope(scopes):
                raise ValueError(f"Invalid scopes: {scopes}")
            
            code = TokenGenerator.generate_authorization_code()
            code_id = str(uuid.uuid4())
            
            auth_code = AuthorizationCode(
                code_id=code_id,
                code=code,
                user_id=user_id,
                client_id=client_id,
                redirect_uri=redirect_uri,
                scopes=scopes,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                nonce=nonce,
                state=state,
            )
            
            self._auth_codes[code_id] = auth_code
            self._code_index[code] = code_id
            
            logger.info(f"Authorization code created for user {user_id}")
            return code
    
    async def exchange_code_for_token(self, code: str, client_id: str,
                                       redirect_uri: str, code_verifier: str = None) -> Dict[str, Any]:
        async with self._lock:
            code_id = self._code_index.get(code)
            if not code_id:
                raise ValueError("Invalid authorization code")
            
            auth_code = self._auth_codes.get(code_id)
            if not auth_code:
                raise ValueError("Authorization code not found")
            
            if auth_code.client_id != client_id:
                raise ValueError("Client ID mismatch")
            
            if auth_code.redirect_uri != redirect_uri:
                raise ValueError("Redirect URI mismatch")
            
            if not auth_code.is_valid():
                raise ValueError("Authorization code expired or already used")
            
            if code_verifier and not auth_code.verify_code_verifier(code_verifier):
                raise ValueError("Invalid code_verifier")
            
            auth_code.used = True
            auth_code.used_at = time.time()
            
            client = self._clients.get(client_id)
            if not client:
                raise ValueError(f"Client {client_id} not found")
            
            return await self._issue_tokens(
                user_id=auth_code.user_id,
                client=client,
                scopes=auth_code.scopes,
                nonce=auth_code.nonce,
            )
    
    async def refresh_token(self, refresh_token_value: str,
                             client_id: str, client_secret: str = None,
                             scopes: List[AuthScope] = None) -> Dict[str, Any]:
        async with self._lock:
            token_id = self._token_index.get(refresh_token_value)
            if not token_id:
                raise ValueError("Invalid refresh token")
            
            token = self._tokens.get(token_id)
            if not token:
                raise ValueError("Refresh token not found")
            
            if token.token_type != TokenType.REFRESH_TOKEN:
                raise ValueError("Not a refresh token")
            
            if not token.is_valid():
                raise ValueError("Refresh token expired or revoked")
            
            if token.client_id != client_id:
                raise ValueError("Client ID mismatch")
            
            client = self._clients.get(client_id)
            if not client:
                raise ValueError(f"Client {client_id} not found")
            
            new_scopes = scopes or token.scopes
            if not client.validate_scope(new_scopes):
                raise ValueError("Invalid scopes")
            
            token.revoked = True
            token.revoked_at = time.time()
            
            return await self._issue_tokens(
                user_id=token.user_id,
                client=client,
                scopes=new_scopes,
            )
    
    async def client_credentials(self, client_id: str, client_secret: str,
                                  scopes: List[AuthScope]) -> Dict[str, Any]:
        client = self._clients.get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        if client.client_secret != client_secret:
            raise ValueError("Invalid client secret")
        
        if GrantType.CLIENT_CREDENTIALS not in client.allowed_grants:
            raise ValueError("Client credentials grant not allowed")
        
        if not client.validate_scope(scopes):
            raise ValueError("Invalid scopes")
        
        return await self._issue_tokens(
            user_id=f"client:{client_id}",
            client=client,
            scopes=scopes,
            is_client_credentials=True,
        )
    
    async def _issue_tokens(self, user_id: str, client: OAuthClient,
                             scopes: List[AuthScope],
                             nonce: str = "",
                             is_client_credentials: bool = False) -> Dict[str, Any]:
        now = time.time()
        
        access_token_value = TokenGenerator.generate_access_token()
        refresh_token_value = TokenGenerator.generate_refresh_token()
        
        access_token = Token(
            token_id=str(uuid.uuid4()),
            token_type=TokenType.ACCESS_TOKEN,
            user_id=user_id,
            client_id=client.client_id,
            scopes=scopes,
            value=access_token_value,
            expires_at=now + client.token_lifetime,
            end_type=client.end_type,
        )
        
        refresh_token = Token(
            token_id=str(uuid.uuid4()),
            token_type=TokenType.REFRESH_TOKEN,
            user_id=user_id,
            client_id=client.client_id,
            scopes=scopes,
            value=refresh_token_value,
            expires_at=now + client.refresh_lifetime,
            end_type=client.end_type,
        )
        
        self._tokens[access_token.token_id] = access_token
        self._tokens[refresh_token.token_id] = refresh_token
        self._token_index[access_token_value] = access_token.token_id
        self._token_index[refresh_token_value] = refresh_token.token_id
        
        id_token_value = None
        if AuthScope.OPENID in scopes and not is_client_credentials:
            user = self._users.get(user_id)
            if user:
                id_token_payload = {
                    "iss": "five-end-auth-center",
                    "sub": user_id,
                    "aud": client.client_id,
                    "exp": int(now + client.token_lifetime),
                    "iat": int(now),
                    "nonce": nonce,
                    "name": user.display_name or user.username,
                    "email": user.email,
                    "end_type": client.end_type.value,
                }
                id_token_value = TokenGenerator.generate_id_token(
                    id_token_payload, TokenGenerator.JWT_SECRET
                )
        
        session_id = str(uuid.uuid4())
        session = AuthSession(
            session_id=session_id,
            user_id=user_id,
            client_id=client.client_id,
            end_type=client.end_type,
            tokens=[access_token.token_id, refresh_token.token_id],
        )
        self._sessions[session_id] = session
        self._user_sessions[user_id].add(session_id)
        
        logger.info(f"Tokens issued for user {user_id} on {client.end_type.value}")
        
        result = {
            "access_token": access_token_value,
            "token_type": "Bearer",
            "expires_in": client.token_lifetime,
            "refresh_token": refresh_token_value,
            "scope": " ".join(s.value for s in scopes),
            "session_id": session_id,
        }
        
        if id_token_value:
            result["id_token"] = id_token_value
        
        return result
    
    async def validate_token(self, token_value: str) -> Optional[Token]:
        token_id = self._token_index.get(token_value)
        if not token_id:
            return None
        
        token = self._tokens.get(token_id)
        if not token:
            return None
        
        if not token.is_valid():
            return None
        
        return token
    
    async def revoke_token(self, token_value: str) -> bool:
        async with self._lock:
            token_id = self._token_index.get(token_value)
            if not token_id:
                return False
            
            token = self._tokens.get(token_id)
            if not token:
                return False
            
            token.revoked = True
            token.revoked_at = time.time()
            
            logger.info(f"Token {token_id} revoked")
            return True
    
    async def end_session(self, session_id: str) -> bool:
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if not session:
                return False
            
            for token_id in session.tokens:
                token = self._tokens.get(token_id)
                if token:
                    token.revoked = True
                    token.revoked_at = time.time()
                    self._token_index.pop(token.value, None)
            
            self._user_sessions[session.user_id].discard(session_id)
            
            logger.info(f"Session {session_id} ended")
            return True
    
    async def get_cross_end_sessions(self, user_id: str) -> Dict[str, AuthSession]:
        sessions = {}
        for session_id in self._user_sessions.get(user_id, []):
            session = self._sessions.get(session_id)
            if session and not session.is_expired():
                sessions[session.end_type.value] = session
        return sessions
    
    async def link_cross_end_session(self, user_id: str, source_end: EndType,
                                      target_end: EndType, target_session_id: str) -> bool:
        for session_id in self._user_sessions.get(user_id, []):
            session = self._sessions.get(session_id)
            if session and session.end_type == source_end:
                session.cross_end_sessions[target_end.value] = target_session_id
                return True
        return False
    
    async def _cleanup_expired(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                
                async with self._lock:
                    now = time.time()
                    
                    expired_tokens = [
                        tid for tid, token in self._tokens.items()
                        if token.is_expired() or token.revoked
                    ]
                    for tid in expired_tokens:
                        token = self._tokens.pop(tid)
                        self._token_index.pop(token.value, None)
                    
                    expired_sessions = [
                        sid for sid, session in self._sessions.items()
                        if session.is_expired()
                    ]
                    for sid in expired_sessions:
                        session = self._sessions.pop(sid)
                        self._user_sessions[session.user_id].discard(sid)
                    
                    expired_codes = [
                        cid for cid, code in self._auth_codes.items()
                        if code.is_expired() or code.used
                    ]
                    for cid in expired_codes:
                        code = self._auth_codes.pop(cid)
                        self._code_index.pop(code.code, None)
                    
                    if expired_tokens or expired_sessions or expired_codes:
                        logger.info(f"Cleaned up: {len(expired_tokens)} tokens, "
                                   f"{len(expired_sessions)} sessions, "
                                   f"{len(expired_codes)} codes")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_users": len(self._users),
            "total_clients": len(self._clients),
            "active_tokens": len([t for t in self._tokens.values() if t.is_valid()]),
            "active_sessions": len([s for s in self._sessions.values() if not s.is_expired()]),
            "users_by_end": {
                end.value: len([u for u in self._users.values() if u.has_end_access(end)])
                for end in EndType
            },
        }
    
    def get_client(self, client_id: str) -> Optional[OAuthClient]:
        return self._clients.get(client_id)
    
    def get_all_clients(self) -> List[OAuthClient]:
        return list(self._clients.values())


class AuthMonitor:
    def __init__(self, auth_center: UnifiedAuthCenter):
        self.auth_center = auth_center
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.auth_center.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_active_sessions_by_end(self) -> Dict[str, int]:
        by_end = defaultdict(int)
        for session in self.auth_center._sessions.values():
            if not session.is_expired():
                by_end[session.end_type.value] += 1
        return dict(by_end)
    
    async def get_token_usage(self) -> Dict[str, int]:
        by_type = defaultdict(int)
        for token in self.auth_center._tokens.values():
            if token.is_valid():
                by_type[token.token_type.value] += 1
        return dict(by_type)
