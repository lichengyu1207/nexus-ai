"""
伪造响应智能体
Forged Response Agent

根据攻击者请求，动态构造逼真的伪造响应
基于大模型生成逼真的网页、API响应、数据库返回结果
支持协议仿真和慢速响应策略
"""

import asyncio
import time
import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class ResponseType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    FTP = "ftp"
    SMTP = "smtp"
    MYSQL = "mysql"
    POSTGRES = "postgres"
    REDIS = "redis"
    MONGODB = "mongodb"
    CUSTOM = "custom"


class DelayStrategy(Enum):
    NONE = "none"
    SLOW = "slow"
    VARIABLE = "variable"
    PROGRESSIVE = "progressive"
    RANDOM = "random"


@dataclass
class ForgedResponse:
    response_id: str
    response_type: ResponseType
    timestamp: datetime
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    delay_ms: float
    attacker_ip: str
    success: bool = True
    deception_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "response_id": self.response_id,
            "response_type": self.response_type.value,
            "timestamp": self.timestamp.isoformat(),
            "request_data": self.request_data,
            "response_data": self.response_data,
            "delay_ms": self.delay_ms,
            "attacker_ip": self.attacker_ip,
            "success": self.success,
            "deception_score": self.deception_score
        }


class ContentGenerator:
    def __init__(self):
        self.templates = self._load_templates()
        self.fake_data_generators = self._init_fake_data_generators()
        
    def _load_templates(self) -> Dict[str, Dict]:
        return {
            "login_pages": {
                "admin": """<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f0f0; }
        .login-box { width: 300px; margin: 100px auto; padding: 20px; background: white; border-radius: 5px; }
        input { width: 100%; padding: 10px; margin: 10px 0; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Administrator Login</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p style="color: red; font-size: 12px;">{error_message}</p>
    </div>
</body>
</html>""",
                "cms": """<!DOCTYPE html>
<html>
<head>
    <title>Content Management System</title>
</head>
<body>
    <div id="login-form">
        <h1>CMS Login</h1>
        <form action="/admin/login" method="post">
            <label>Username: <input type="text" name="user"></label><br>
            <label>Password: <input type="password" name="pass"></label><br>
            <input type="submit" value="Sign In">
        </form>
    </div>
</body>
</html>"""
            },
            "api_responses": {
                "users": {
                    "status": "success",
                    "data": [
                        {"id": 1, "name": "John Admin", "email": "admin@company.com", "role": "admin"},
                        {"id": 2, "name": "Jane User", "email": "jane@company.com", "role": "user"},
                        {"id": 3, "name": "Bob Manager", "email": "bob@company.com", "role": "manager"}
                    ],
                    "total": 3
                },
                "config": {
                    "status": "success",
                    "data": {
                        "version": "2.5.1",
                        "environment": "production",
                        "debug": False,
                        "database": {
                            "host": "internal-db.local",
                            "port": 5432,
                            "name": "production"
                        },
                        "api_keys": {
                            "stripe": "sk_live_xxx",
                            "sendgrid": "SG.xxx"
                        }
                    }
                },
                "error": {
                    "status": "error",
                    "message": "Internal server error",
                    "code": 500
                }
            },
            "database_dumps": {
                "users_table": """id,username,email,password_hash,role,created_at
1,admin,admin@company.com,{admin_hash},admin,2024-01-01 00:00:00
2,root,root@company.com,{root_hash},admin,2024-01-02 00:00:00
3,backup,backup@company.com,{backup_hash},admin,2024-01-03 00:00:00
4,developer,dev@company.com,{dev_hash},developer,2024-02-01 00:00:00
5,tester,test@company.com,{test_hash},tester,2024-02-15 00:00:00""",
                "credentials": """service,username,password,notes
mysql,root,SuperSecret123!,Production database
redis,default,redis_pass_456,Cache server
aws,admin,AKIAIOSFODNN7EXAMPLE,AWS console
github,deploy,ghp_xxxxxxxxxxxx,Deploy token"""
            },
            "error_pages": {
                "500": """<!DOCTYPE html>
<html>
<head><title>500 Internal Server Error</title></head>
<body>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your request.</p>
<p>Please try again later.</p>
<hr>
<address>Apache/2.4.41 (Ubuntu) Server at {server_name} Port 80</address>
</body>
</html>""",
                "403": """<!DOCTYPE html>
<html>
<head><title>403 Forbidden</title></head>
<body>
<h1>Forbidden</h1>
<p>You don't have permission to access this resource.</p>
</body>
</html>"""
            }
        }
        
    def _init_fake_data_generators(self) -> Dict[str, callable]:
        return {
            "password_hash": self._generate_fake_bcrypt_hash,
            "api_key": self._generate_fake_api_key,
            "session_token": self._generate_fake_session_token,
            "credit_card": self._generate_fake_credit_card,
            "ssn": self._generate_fake_ssn,
            "email": self._generate_fake_email
        }
        
    def _generate_fake_bcrypt_hash(self) -> str:
        fake_hashes = [
            "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYqVqxqZ",
            "$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG",
            "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga",
        ]
        return random.choice(fake_hashes)
        
    def _generate_fake_api_key(self) -> str:
        prefixes = ["sk-", "pk-", "api-", "key-"]
        return random.choice(prefixes) + hashlib.md5(str(time.time()).encode()).hexdigest()[:32]
        
    def _generate_fake_session_token(self) -> str:
        return hashlib.sha256(str(time.time()).encode()).hexdigest()
        
    def _generate_fake_credit_card(self) -> str:
        prefixes = ["4", "51", "52", "53", "54", "55"]
        prefix = random.choice(prefixes)
        remaining = "".join([str(random.randint(0, 9)) for _ in range(16 - len(prefix))])
        return prefix + remaining
        
    def _generate_fake_ssn(self) -> str:
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        
    def _generate_fake_email(self) -> str:
        names = ["john", "jane", "admin", "user", "support", "info"]
        domains = ["company.com", "example.org", "test.net", "internal.local"]
        return f"{random.choice(names)}@{random.choice(domains)}"
        
    def generate_login_page(self, style: str = "admin", error_message: str = "") -> str:
        template = self.templates["login_pages"].get(style, self.templates["login_pages"]["admin"])
        return template.format(error_message=error_message)
        
    def generate_api_response(self, endpoint: str, status: str = "success") -> Dict:
        if endpoint in self.templates["api_responses"]:
            response = self.templates["api_responses"][endpoint].copy()
            if status == "error":
                response["status"] = "error"
            return response
            
        return {
            "status": status,
            "data": self._generate_dynamic_data(endpoint),
            "timestamp": datetime.now().isoformat()
        }
        
    def _generate_dynamic_data(self, endpoint: str) -> Any:
        if "user" in endpoint.lower():
            return {
                "id": random.randint(1, 1000),
                "name": self._generate_fake_email().split("@")[0],
                "email": self._generate_fake_email(),
                "created_at": datetime.now().isoformat()
            }
        elif "config" in endpoint.lower():
            return {
                "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
                "environment": random.choice(["production", "staging", "development"]),
                "debug": random.choice([True, False])
            }
        else:
            return {"data": "sample", "id": random.randint(1, 100)}
            
    def generate_database_dump(self, table_type: str = "users_table") -> str:
        template = self.templates["database_dumps"].get(table_type, "")
        
        if table_type == "users_table":
            template = template.format(
                admin_hash=self._generate_fake_bcrypt_hash(),
                root_hash=self._generate_fake_bcrypt_hash(),
                backup_hash=self._generate_fake_bcrypt_hash(),
                dev_hash=self._generate_fake_bcrypt_hash(),
                test_hash=self._generate_fake_bcrypt_hash()
            )
            
        return template
        
    def generate_error_page(self, error_code: int, server_name: str = "localhost") -> str:
        template = self.templates["error_pages"].get(str(error_code), self.templates["error_pages"]["500"])
        return template.format(server_name=server_name)
        
    def generate_ssh_banner(self, version: str = "OpenSSH_8.2p1") -> str:
        return f"SSH-2.0-{version}\r\n"
        
    def generate_ssh_response(self, command: str, session: Dict) -> str:
        responses = {
            "whoami": session.get("username", "root"),
            "pwd": session.get("cwd", "/root"),
            "ls": "documents  downloads  scripts  config.yml  backup.sql",
            "id": "uid=0(root) gid=0(root) groups=0(root)",
            "uname -a": f"Linux {session.get('hostname', 'server01')} 5.4.0-80-generic #90-Ubuntu SMP x86_64 GNU/Linux",
            "cat /etc/passwd": self._generate_fake_passwd(),
            "ifconfig": self._generate_fake_ifconfig(),
            "netstat -tlnp": self._generate_fake_netstat()
        }
        
        cmd_lower = command.strip().lower()
        
        for key, response in responses.items():
            if cmd_lower.startswith(key):
                return response + "\n"
                
        return f"bash: {command.split()[0]}: command not found\n"
        
    def _generate_fake_passwd(self) -> str:
        return """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
mysql:x:112:117:MySQL Server,,,:/nonexistent:/bin/false
"""
        
    def _generate_fake_ifconfig(self) -> str:
        return """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.1.100  netmask 255.255.255.0  broadcast 10.0.1.255
        inet6 fe80::a00:27ff:fe8e:8aaa  prefixlen 64  scopeid 0x20<link>
        ether 08:00:27:8e:8a:aa  txqueuelen 1000  (Ethernet)
        RX packets 1234567  bytes 987654321 (987.6 MB)
        TX packets 7654321  bytes 1234567890 (1.2 GB)

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
"""
        
    def _generate_fake_netstat(self) -> str:
        return """Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1234/sshd
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      2345/nginx
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN      2345/nginx
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      3456/mysqld
tcp        0      0 127.0.0.1:6379          0.0.0.0:*               LISTEN      4567/redis-server
"""


class DelayEngine:
    def __init__(self):
        self.strategies = {
            DelayStrategy.NONE: self._no_delay,
            DelayStrategy.SLOW: self._slow_delay,
            DelayStrategy.VARIABLE: self._variable_delay,
            DelayStrategy.PROGRESSIVE: self._progressive_delay,
            DelayStrategy.RANDOM: self._random_delay
        }
        
        self.session_delays: Dict[str, List[float]] = defaultdict(list)
        
    async def apply_delay(
        self,
        strategy: DelayStrategy,
        attacker_ip: str,
        base_delay_ms: float = 100
    ) -> float:
        delay_func = self.strategies.get(strategy, self._no_delay)
        actual_delay = await delay_func(attacker_ip, base_delay_ms)
        
        self.session_delays[attacker_ip].append(actual_delay)
        
        return actual_delay
        
    async def _no_delay(self, attacker_ip: str, base_delay: float) -> float:
        return 0.0
        
    async def _slow_delay(self, attacker_ip: str, base_delay: float) -> float:
        delay = base_delay * 5
        await asyncio.sleep(delay / 1000)
        return delay
        
    async def _variable_delay(self, attacker_ip: str, base_delay: float) -> float:
        delay = base_delay * random.uniform(0.5, 3.0)
        await asyncio.sleep(delay / 1000)
        return delay
        
    async def _progressive_delay(self, attacker_ip: str, base_delay: float) -> float:
        request_count = len(self.session_delays[attacker_ip])
        multiplier = min(1 + request_count * 0.5, 10)
        delay = base_delay * multiplier
        await asyncio.sleep(delay / 1000)
        return delay
        
    async def _random_delay(self, attacker_ip: str, base_delay: float) -> float:
        delay = random.uniform(0, base_delay * 10)
        await asyncio.sleep(delay / 1000)
        return delay


class ForgedResponseAgent:
    def __init__(
        self,
        agent_id: str = "forged_response_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.content_generator = ContentGenerator()
        self.delay_engine = DelayEngine()
        
        self.responses: deque = deque(maxlen=1000)
        self.attacker_sessions: Dict[str, Dict] = {}
        self.attacker_preferences: Dict[str, Dict] = {}
        
        self.delay_strategy: DelayStrategy = DelayStrategy.VARIABLE
        self.base_delay_ms: float = 100
        
        self.stats = {
            "total_responses": 0,
            "http_responses": 0,
            "ssh_responses": 0,
            "db_responses": 0,
            "total_delay_ms": 0,
            "avg_deception_score": 0.0
        }
        
        self._running = False
        
    async def start(self):
        self._running = True
        logger.info(f"ForgedResponseAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        logger.info(f"ForgedResponseAgent {self.agent_id} stopped")
        
    async def generate_response(
        self,
        response_type: ResponseType,
        request_data: Dict,
        attacker_ip: str,
        apply_delay: bool = True
    ) -> ForgedResponse:
        start_time = time.time()
        
        session = self._get_or_create_session(attacker_ip)
        preferences = self.attacker_preferences.get(attacker_ip, {})
        
        response_data = await self._generate_typed_response(
            response_type, request_data, session, preferences
        )
        
        delay_ms = 0.0
        if apply_delay:
            delay_ms = await self.delay_engine.apply_delay(
                self.delay_strategy,
                attacker_ip,
                self.base_delay_ms
            )
            
        deception_score = self._calculate_deception_score(response_data, request_data)
        
        response = ForgedResponse(
            response_id=self._generate_response_id(),
            response_type=response_type,
            timestamp=datetime.now(),
            request_data=request_data,
            response_data=response_data,
            delay_ms=delay_ms,
            attacker_ip=attacker_ip,
            success=True,
            deception_score=deception_score
        )
        
        self.responses.append(response)
        self._update_stats(response_type, delay_ms, deception_score)
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "forged_response",
                response.to_dict()
            )
            
        return response
        
    async def _generate_typed_response(
        self,
        response_type: ResponseType,
        request_data: Dict,
        session: Dict,
        preferences: Dict
    ) -> Dict:
        if response_type == ResponseType.HTTP or response_type == ResponseType.HTTPS:
            return await self._generate_http_response(request_data, session, preferences)
        elif response_type == ResponseType.SSH:
            return await self._generate_ssh_response(request_data, session, preferences)
        elif response_type in [ResponseType.MYSQL, ResponseType.POSTGRES]:
            return await self._generate_db_response(request_data, session, preferences)
        else:
            return {"response": "OK"}
            
    async def _generate_http_response(
        self,
        request_data: Dict,
        session: Dict,
        preferences: Dict
    ) -> Dict:
        path = request_data.get("path", "/")
        method = request_data.get("method", "GET")
        
        if path in ["/", "/index.html"]:
            return {
                "status_code": 200,
                "headers": {"Content-Type": "text/html", "Server": "Apache/2.4.41 (Ubuntu)"},
                "body": self.content_generator.generate_login_page("admin")
            }
        elif path in ["/login", "/admin", "/admin/login"]:
            if method == "POST":
                username = request_data.get("body", {}).get("username", "")
                session["username"] = username
                return {
                    "status_code": 302,
                    "headers": {
                        "Location": "/dashboard",
                        "Set-Cookie": f"session={self.content_generator._generate_fake_session_token()}; HttpOnly"
                    },
                    "body": ""
                }
            else:
                return {
                    "status_code": 200,
                    "headers": {"Content-Type": "text/html"},
                    "body": self.content_generator.generate_login_page("admin", "Invalid credentials")
                }
        elif path.startswith("/api/"):
            endpoint = path.replace("/api/", "")
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(self.content_generator.generate_api_response(endpoint))
            }
        elif path in ["/dump", "/backup", "/db.sql"]:
            return {
                "status_code": 200,
                "headers": {"Content-Type": "text/plain"},
                "body": self.content_generator.generate_database_dump("users_table")
            }
        elif path in ["/config", "/.env", "/settings"]:
            return {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(self.content_generator.generate_api_response("config"))
            }
        else:
            return {
                "status_code": 404,
                "headers": {"Content-Type": "text/html"},
                "body": self.content_generator.generate_error_page(404)
            }
            
    async def _generate_ssh_response(
        self,
        request_data: Dict,
        session: Dict,
        preferences: Dict
    ) -> Dict:
        request_type = request_data.get("type", "command")
        
        if request_type == "banner":
            return {
                "banner": self.content_generator.generate_ssh_banner(),
                "prompt": ""
            }
        elif request_type == "auth":
            username = request_data.get("username", "root")
            password = request_data.get("password", "")
            session["username"] = username
            session["cwd"] = f"/home/{username}" if username != "root" else "/root"
            
            return {
                "success": True,
                "message": f"Welcome to Ubuntu 20.04.3 LTS",
                "prompt": f"{username}@{session.get('hostname', 'server01')}:~$ "
            }
        elif request_type == "command":
            command = request_data.get("command", "")
            response = self.content_generator.generate_ssh_response(command, session)
            
            return {
                "response": response,
                "prompt": f"{session.get('username', 'root')}@{session.get('hostname', 'server01')}:~$ "
            }
        else:
            return {"response": ""}
            
    async def _generate_db_response(
        self,
        request_data: Dict,
        session: Dict,
        preferences: Dict
    ) -> Dict:
        query = request_data.get("query", "")
        query_upper = query.upper()
        
        if "SHOW DATABASES" in query_upper:
            return {
                "columns": ["Database"],
                "rows": [
                    ["information_schema"],
                    ["mysql"],
                    ["performance_schema"],
                    ["sys"],
                    ["production"],
                    ["users_db"]
                ],
                "affected_rows": 0
            }
        elif "SHOW TABLES" in query_upper:
            return {
                "columns": ["Tables_in_production"],
                "rows": [
                    ["users"],
                    ["accounts"],
                    ["transactions"],
                    ["sessions"],
                    ["api_keys"]
                ],
                "affected_rows": 0
            }
        elif "SELECT" in query_upper and "users" in query.lower():
            return {
                "columns": ["id", "username", "email", "password_hash", "role"],
                "rows": [
                    [1, "admin", "admin@company.com", self.content_generator._generate_fake_bcrypt_hash(), "admin"],
                    [2, "root", "root@company.com", self.content_generator._generate_fake_bcrypt_hash(), "admin"],
                    [3, "backup", "backup@company.com", self.content_generator._generate_fake_bcrypt_hash(), "admin"]
                ],
                "affected_rows": 0
            }
        else:
            return {
                "columns": [],
                "rows": [],
                "affected_rows": 0,
                "message": "Query OK"
            }
            
    def _get_or_create_session(self, attacker_ip: str) -> Dict:
        if attacker_ip not in self.attacker_sessions:
            self.attacker_sessions[attacker_ip] = {
                "created_at": datetime.now().isoformat(),
                "hostname": f"server{random.randint(1, 99):02d}",
                "username": "root",
                "cwd": "/root",
                "request_count": 0
            }
            
        session = self.attacker_sessions[attacker_ip]
        session["request_count"] = session.get("request_count", 0) + 1
        session["last_request"] = datetime.now().isoformat()
        
        return session
        
    def _calculate_deception_score(self, response_data: Dict, request_data: Dict) -> float:
        score = 0.5
        
        if response_data.get("status_code") in [200, 302]:
            score += 0.1
        if response_data.get("body") and len(str(response_data.get("body", ""))) > 100:
            score += 0.1
        if "Set-Cookie" in response_data.get("headers", {}):
            score += 0.1
        if response_data.get("rows") and len(response_data.get("rows", [])) > 0:
            score += 0.1
        if response_data.get("banner"):
            score += 0.1
            
        return min(score, 1.0)
        
    def set_delay_strategy(self, strategy: DelayStrategy, base_delay_ms: float = 100):
        self.delay_strategy = strategy
        self.base_delay_ms = base_delay_ms
        logger.info(f"Set delay strategy to {strategy.value} with base delay {base_delay_ms}ms")
        
    def set_attacker_preferences(self, attacker_ip: str, preferences: Dict):
        self.attacker_preferences[attacker_ip] = preferences
        
    def _update_stats(self, response_type: ResponseType, delay_ms: float, deception_score: float):
        self.stats["total_responses"] += 1
        self.stats["total_delay_ms"] += delay_ms
        
        if response_type in [ResponseType.HTTP, ResponseType.HTTPS]:
            self.stats["http_responses"] += 1
        elif response_type == ResponseType.SSH:
            self.stats["ssh_responses"] += 1
        elif response_type in [ResponseType.MYSQL, ResponseType.POSTGRES]:
            self.stats["db_responses"] += 1
            
        current_avg = self.stats["avg_deception_score"]
        count = self.stats["total_responses"]
        self.stats["avg_deception_score"] = (current_avg * (count - 1) + deception_score) / count
        
    async def get_response(self, response_id: str) -> Optional[Dict]:
        for response in self.responses:
            if response.response_id == response_id:
                return response.to_dict()
        return None
        
    async def get_recent_responses(self, limit: int = 50) -> List[Dict]:
        responses = list(self.responses)[-limit:]
        return [r.to_dict() for r in responses]
        
    async def get_attacker_session(self, attacker_ip: str) -> Optional[Dict]:
        return self.attacker_sessions.get(attacker_ip)
        
    async def get_all_sessions(self) -> Dict[str, Dict]:
        return self.attacker_sessions.copy()
        
    def _generate_response_id(self) -> str:
        return f"resp_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "active_sessions": len(self.attacker_sessions),
            "avg_delay_ms": self.stats["total_delay_ms"] / max(self.stats["total_responses"], 1)
        }
