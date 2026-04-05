"""
动态蜜罐智能体
Deceptive Honeypot Agent

根据攻击者特征动态生成高仿真蜜罐服务，诱敌深入
基于大模型生成动态响应内容，实时调整蜜罐指纹
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


class HoneypotType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    FTP = "ftp"
    TELNET = "telnet"
    SMTP = "smtp"
    MYSQL = "mysql"
    POSTGRES = "postgres"
    REDIS = "redis"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    RDP = "rdp"
    SMB = "smb"
    CUSTOM = "custom"


class HoneypotState(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INTERACTING = "interacting"
    CAPTURED = "captured"
    EXPIRED = "expired"
    SHUTDOWN = "shutdown"


@dataclass
class HoneypotConfig:
    honeypot_id: str
    honeypot_type: HoneypotType
    port: int
    bind_address: str = "0.0.0.0"
    service_version: str = ""
    banner: str = ""
    fake_data: Dict[str, Any] = field(default_factory=dict)
    response_templates: Dict[str, str] = field(default_factory=dict)
    interaction_timeout: int = 300
    max_interactions: int = 1000
    decoy_files: List[str] = field(default_factory=list)
    fake_users: List[Dict] = field(default_factory=list)
    fake_databases: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "honeypot_id": self.honeypot_id,
            "honeypot_type": self.honeypot_type.value,
            "port": self.port,
            "bind_address": self.bind_address,
            "service_version": self.service_version,
            "banner": self.banner,
            "fake_data": self.fake_data,
            "interaction_timeout": self.interaction_timeout,
            "max_interactions": self.max_interactions,
            "decoy_files": self.decoy_files,
            "fake_users": self.fake_users,
            "fake_databases": self.fake_databases
        }


class InteractionLog:
    def __init__(self, interaction_id: str, honeypot_id: str, source_ip: str):
        self.interaction_id = interaction_id
        self.honeypot_id = honeypot_id
        self.source_ip = source_ip
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.commands: List[Dict] = []
        self.responses: List[Dict] = []
        self.files_accessed: List[str] = []
        self.credentials_tried: List[Dict] = []
        self.payloads: List[str] = []
        self.session_data: Dict[str, Any] = {}
        self.attacker_behavior: List[str] = []
        
    def add_command(self, command: str, timestamp: Optional[datetime] = None):
        self.commands.append({
            "command": command,
            "timestamp": (timestamp or datetime.now()).isoformat()
        })
        
    def add_response(self, response: str, timestamp: Optional[datetime] = None):
        self.responses.append({
            "response": response,
            "timestamp": (timestamp or datetime.now()).isoformat()
        })
        
    def add_credential_attempt(self, username: str, password: str, success: bool = False):
        self.credentials_tried.append({
            "username": username,
            "password": password,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_payload(self, payload: str):
        self.payloads.append(payload)
        
    def end(self):
        self.end_time = datetime.now()
        
    def get_duration(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
        
    def to_dict(self) -> Dict:
        return {
            "interaction_id": self.interaction_id,
            "honeypot_id": self.honeypot_id,
            "source_ip": self.source_ip,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration(),
            "commands": self.commands,
            "responses": self.responses,
            "files_accessed": self.files_accessed,
            "credentials_tried": self.credentials_tried,
            "payloads": self.payloads,
            "attacker_behavior": self.attacker_behavior,
            "session_data": self.session_data
        }


class ResponseGenerator:
    def __init__(self):
        self.templates = self._load_templates()
        self.service_signatures = self._load_service_signatures()
        
    def _load_templates(self) -> Dict[str, Dict]:
        return {
            "http": {
                "index": """<!DOCTYPE html>
<html>
<head><title>Welcome to {server_name}</title></head>
<body>
<h1>{server_name} - Under Maintenance</h1>
<p>System is currently undergoing scheduled maintenance.</p>
<p>Please try again later.</p>
<hr>
<address>{server_signature}</address>
</body>
</html>""",
                "login": """<!DOCTYPE html>
<html>
<head><title>Login - {server_name}</title></head>
<body>
<h2>Administrator Login</h2>
<form method="POST" action="/login">
<input type="text" name="username" placeholder="Username"><br>
<input type="password" name="password" placeholder="Password"><br>
<input type="submit" value="Login">
</form>
<p style="color:red">{error_message}</p>
</body>
</html>""",
                "404": """<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body>
<h1>Not Found</h1>
<p>The requested URL was not found on this server.</p>
<address>{server_signature}</address>
</body>
</html>""",
                "api_response": """{{"status": "{status}", "data": {data}, "message": "{message}"}}"""
            },
            "ssh": {
                "banner": "SSH-2.0-{server_version}\r\n",
                "prompt": "{username}@{hostname}:~$ ",
                "motd": "Welcome to {hostname}\nLast login: {last_login}\n",
                "command_responses": {
                    "ls": "{files}",
                    "whoami": "{username}",
                    "pwd": "/home/{username}",
                    "id": "uid=1000({username}) gid=1000({username}) groups=1000({username}),27(sudo)",
                    "uname": "Linux {hostname} 5.4.0-{kernel} #1 SMP {date} x86_64 GNU/Linux",
                    "cat /etc/passwd": "{fake_passwd}",
                    "ifconfig": "{fake_ifconfig}"
                }
            },
            "mysql": {
                "greeting": "{server_version}",
                "query_responses": {
                    "SHOW DATABASES": "{databases}",
                    "SELECT * FROM users": "{users_table}",
                    "DESCRIBE {table}": "{table_schema}"
                }
            }
        }
        
    def _load_service_signatures(self) -> Dict[str, List[str]]:
        return {
            "apache": [
                "Apache/2.4.41 (Ubuntu)",
                "Apache/2.4.46 (Unix)",
                "Apache/2.4.38 (Debian)"
            ],
            "nginx": [
                "nginx/1.18.0",
                "nginx/1.19.0",
                "nginx/1.20.1"
            ],
            "openssh": [
                "OpenSSH_8.2p1 Ubuntu-4ubuntu0.5",
                "OpenSSH_7.6p1 Ubuntu-4ubuntu0.3",
                "OpenSSH_8.4p1"
            ],
            "mysql": [
                "5.7.33-0ubuntu0.18.04.1",
                "8.0.23-0ubuntu0.20.04.1",
                "5.6.51"
            ]
        }
        
    def generate_http_response(
        self,
        path: str,
        method: str,
        headers: Dict,
        attacker_profile: Optional[Dict] = None
    ) -> Tuple[str, int, Dict]:
        server_name = random.choice(["WebServer", "Application Server", "Internal Portal"])
        server_sig = random.choice(self.service_signatures["apache"])
        
        if path == "/" or path == "/index.html":
            body = self.templates["http"]["index"].format(
                server_name=server_name,
                server_signature=server_sig
            )
            return body, 200, {"Content-Type": "text/html", "Server": server_sig}
            
        elif path == "/login" or path == "/admin":
            body = self.templates["http"]["login"].format(
                server_name=server_name,
                error_message=""
            )
            return body, 200, {"Content-Type": "text/html", "Server": server_sig}
            
        elif path.startswith("/api/"):
            data = self._generate_fake_api_data(path)
            body = self.templates["http"]["api_response"].format(
                status="success",
                data=json.dumps(data),
                message="Data retrieved successfully"
            )
            return body, 200, {"Content-Type": "application/json", "Server": server_sig}
            
        else:
            body = self.templates["http"]["404"].format(
                server_signature=server_sig
            )
            return body, 404, {"Content-Type": "text/html", "Server": server_sig}
            
    def generate_ssh_response(
        self,
        command: str,
        session_data: Dict,
        attacker_profile: Optional[Dict] = None
    ) -> str:
        username = session_data.get("username", "admin")
        hostname = session_data.get("hostname", "server01")
        
        command_lower = command.strip().lower()
        
        if command_lower in self.templates["ssh"]["command_responses"]:
            template = self.templates["ssh"]["command_responses"][command_lower]
            
            if command_lower == "ls":
                files = "  ".join(self._generate_fake_file_listing())
                return template.format(files=files) + "\n"
            elif command_lower == "whoami":
                return template.format(username=username) + "\n"
            elif command_lower == "pwd":
                return template.format(username=username) + "\n"
            elif command_lower == "id":
                return template.format(username=username) + "\n"
            elif command_lower == "uname":
                return template.format(
                    hostname=hostname,
                    kernel=random.randint(100, 200),
                    date=datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")
                ) + "\n"
            else:
                return template + "\n"
                
        elif command_lower.startswith("cat"):
            return self._generate_fake_file_content(command)
        elif command_lower.startswith("cd"):
            session_data["cwd"] = command.split(None, 1)[-1] if len(command.split()) > 1 else "/home/" + username
            return ""
        else:
            return f"bash: {command.split()[0]}: command not found\n"
            
    def generate_mysql_response(self, query: str) -> Tuple[List[List], List[str]]:
        query_upper = query.upper().strip()
        
        if "SHOW DATABASES" in query_upper:
            headers = ["Database"]
            rows = [
                ["information_schema"],
                ["mysql"],
                ["performance_schema"],
                ["sys"],
                ["production_db"],
                ["users_db"]
            ]
            return rows, headers
            
        elif "SHOW TABLES" in query_upper:
            headers = ["Tables_in_database"]
            rows = [
                ["users"],
                ["accounts"],
                ["transactions"],
                ["sessions"],
                ["config"]
            ]
            return rows, headers
            
        elif "SELECT" in query_upper and "users" in query.lower():
            query_lower = query.lower()
            headers = ["id", "username", "email", "password_hash", "role", "created_at"]
            rows = [
                [1, "admin", "admin@company.com", "$2b$12$" + hashlib.md5(b"admin123").hexdigest(), "admin", "2024-01-01"],
                [2, "user1", "user1@company.com", "$2b$12$" + hashlib.md5(b"user123").hexdigest(), "user", "2024-01-15"],
                [3, "backup", "backup@company.com", "$2b$12$" + hashlib.md5(b"backup123").hexdigest(), "admin", "2024-02-01"]
            ]
            return rows, headers
            
        else:
            return [], []
            
    def _generate_fake_api_data(self, path: str) -> Dict:
        if "users" in path:
            return {
                "users": [
                    {"id": 1, "name": "John Doe", "email": "john@example.com"},
                    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                ]
            }
        elif "config" in path:
            return {
                "version": "2.1.0",
                "environment": "production",
                "debug": False
            }
        else:
            return {
                "data": "sample",
                "timestamp": datetime.now().isoformat()
            }
            
    def _generate_fake_file_listing(self) -> List[str]:
        common_files = [
            "documents", "downloads", "scripts", "config.yml",
            "README.md", "backup.sql", "notes.txt", ".bash_history",
            "credentials.json", "deploy.sh", "logs", "tmp"
        ]
        return random.sample(common_files, min(8, len(common_files)))
        
    def _generate_fake_file_content(self, command: str) -> str:
        filename = command.split(None, 1)[-1] if len(command.split()) > 1 else ""
        
        fake_contents = {
            "credentials.json": json.dumps({
                "aws_access_key": "AKIA" + hashlib.md5(b"fake").hexdigest()[:16].upper(),
                "aws_secret": hashlib.sha256(b"fake_secret").hexdigest(),
                "api_key": "sk-" + hashlib.md5(b"api").hexdigest()
            }, indent=2),
            "config.yml": """
database:
  host: internal-db.company.local
  port: 5432
  name: production
  user: admin
  password: SuperSecret123!

api:
  endpoint: https://api.internal.company.com
  key: api_key_xyz123
""",
            ".bash_history": """
cd /var/www
ls -la
cat /etc/passwd
sudo su -
mysql -u root -p
exit
""",
            "notes.txt": """
TODO:
- Update production database credentials
- Review security audit findings
- Deploy new version to staging
- Check backup schedule
"""
        }
        
        for key, content in fake_contents.items():
            if key in filename.lower():
                return content + "\n"
                
        return f"cat: {filename}: No such file or directory\n"


class DeceptiveHoneypotAgent:
    def __init__(
        self,
        agent_id: str = "honeypot_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.response_generator = ResponseGenerator()
        
        self.honeypots: Dict[str, HoneypotConfig] = {}
        self.honeypot_states: Dict[str, HoneypotState] = {}
        self.active_interactions: Dict[str, InteractionLog] = {}
        self.completed_interactions: deque = deque(maxlen=1000)
        
        self.attacker_preferences: Dict[str, Dict] = {}
        self.adaptive_configs: Dict[str, Dict] = {}
        
        self.stats = {
            "total_honeypots_created": 0,
            "total_interactions": 0,
            "total_credentials_captured": 0,
            "total_payloads_captured": 0,
            "avg_interaction_duration": 0.0,
            "successful_deceptions": 0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._maintenance_loop())
        logger.info(f"DeceptiveHoneypotAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        for honeypot_id in list(self.honeypots.keys()):
            await self.shutdown_honeypot(honeypot_id)
            
        logger.info(f"DeceptiveHoneypotAgent {self.agent_id} stopped")
        
    async def _maintenance_loop(self):
        while self._running:
            try:
                await self._expire_old_honeypots()
                await self._cleanup_interactions()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(5)
                
    async def _expire_old_honeypots(self):
        now = datetime.now()
        to_expire = []
        
        for honeypot_id, state in self.honeypot_states.items():
            if state == HoneypotState.ACTIVE:
                config = self.honeypots.get(honeypot_id)
                if config:
                    created = self.adaptive_configs.get(honeypot_id, {}).get("created_at")
                    if created:
                        age = now - created
                        if age > timedelta(hours=config.interaction_timeout // 60):
                            to_expire.append(honeypot_id)
                            
        for honeypot_id in to_expire:
            await self.shutdown_honeypot(honeypot_id)
            
    async def _cleanup_interactions(self):
        cutoff = datetime.now() - timedelta(hours=24)
        
        to_end = []
        for interaction_id, log in self.active_interactions.items():
            if log.start_time < cutoff:
                to_end.append(interaction_id)
                
        for interaction_id in to_end:
            log = self.active_interactions.pop(interaction_id)
            log.end()
            self.completed_interactions.append(log)
            
    async def create_honeypot(
        self,
        honeypot_type: HoneypotType,
        attacker_profile: Optional[Dict] = None,
        custom_config: Optional[Dict] = None
    ) -> HoneypotConfig:
        honeypot_id = self._generate_honeypot_id()
        
        port = self._select_port(honeypot_type)
        
        config = HoneypotConfig(
            honeypot_id=honeypot_id,
            honeypot_type=honeypot_type,
            port=port
        )
        
        if attacker_profile:
            config = self._customize_for_attacker(config, attacker_profile)
            
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    
        config = self._add_decoy_data(config, attacker_profile)
        
        self.honeypots[honeypot_id] = config
        self.honeypot_states[honeypot_id] = HoneypotState.INITIALIZING
        self.adaptive_configs[honeypot_id] = {
            "created_at": datetime.now(),
            "attacker_profile": attacker_profile,
            "interaction_count": 0
        }
        
        await self._deploy_honeypot(config)
        
        self.honeypot_states[honeypot_id] = HoneypotState.ACTIVE
        self.stats["total_honeypots_created"] += 1
        
        logger.info(f"Created honeypot {honeypot_id} of type {honeypot_type.value} on port {port}")
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "honeypot_created",
                {
                    "honeypot_id": honeypot_id,
                    "type": honeypot_type.value,
                    "port": port
                }
            )
            
        return config
        
    def _customize_for_attacker(
        self,
        config: HoneypotConfig,
        attacker_profile: Dict
    ) -> HoneypotConfig:
        attack_types = attacker_profile.get("attack_types", {})
        target_prefs = attacker_profile.get("target_preferences", {})
        
        if any("sql" in t for t in attack_types.keys()):
            config.fake_databases = [
                {"name": "production", "tables": ["users", "accounts", "transactions"]},
                {"name": "analytics", "tables": ["events", "sessions", "metrics"]}
            ]
            
        if any("ssh" in t or "brute" in t for t in attack_types.keys()):
            config.fake_users = [
                {"username": "admin", "password_hash": "fake_hash_1"},
                {"username": "root", "password_hash": "fake_hash_2"},
                {"username": "deploy", "password_hash": "fake_hash_3"}
            ]
            
        if any("http" in t or "web" in t for t in attack_types.keys()):
            config.decoy_files = [
                "/admin/config.php",
                "/backup/db_dump.sql",
                "/.env",
                "/config/database.yml"
            ]
            
        return config
        
    def _add_decoy_data(
        self,
        config: HoneypotConfig,
        attacker_profile: Optional[Dict] = None
    ) -> HoneypotConfig:
        if not config.fake_users:
            config.fake_users = [
                {"username": "admin", "password_hash": hashlib.md5(b"admin123").hexdigest()},
                {"username": "user", "password_hash": hashlib.md5(b"user123").hexdigest()}
            ]
            
        if not config.fake_databases:
            config.fake_databases = [
                {"name": "main", "tables": ["users", "data"]}
            ]
            
        if not config.decoy_files:
            config.decoy_files = [
                "credentials.txt",
                "config.json",
                "backup.zip"
            ]
            
        config.fake_data = {
            "api_keys": [
                "sk-" + hashlib.md5(str(time.time()).encode()).hexdigest()[:24]
                for _ in range(3)
            ],
            "session_tokens": [
                hashlib.sha256(str(time.time() + i).encode()).hexdigest()
                for i in range(5)
            ]
        }
        
        return config
        
    def _select_port(self, honeypot_type: HoneypotType) -> int:
        default_ports = {
            HoneypotType.HTTP: 8080,
            HoneypotType.HTTPS: 8443,
            HoneypotType.SSH: 2222,
            HoneypotType.FTP: 2121,
            HoneypotType.TELNET: 2323,
            HoneypotType.SMTP: 2525,
            HoneypotType.MYSQL: 3307,
            HoneypotType.POSTGRES: 5433,
            HoneypotType.REDIS: 6380,
            HoneypotType.MONGODB: 27018,
            HoneypotType.ELASTICSEARCH: 9201,
            HoneypotType.RDP: 3390,
            HoneypotType.SMB: 4450
        }
        
        base_port = default_ports.get(honeypot_type, 8000)
        
        used_ports = {h.port for h in self.honeypots.values()}
        
        port = base_port
        while port in used_ports:
            port += 1
            
        return port
        
    async def _deploy_honeypot(self, config: HoneypotConfig):
        await asyncio.sleep(0.1)
        logger.info(f"Deployed honeypot {config.honeypot_id} on port {config.port}")
        
    async def handle_interaction(
        self,
        honeypot_id: str,
        source_ip: str,
        interaction_type: str,
        data: Dict
    ) -> Dict:
        if honeypot_id not in self.honeypots:
            return {"error": "Honeypot not found"}
            
        config = self.honeypots[honeypot_id]
        state = self.honeypot_states.get(honeypot_id)
        
        if state != HoneypotState.ACTIVE:
            return {"error": "Honeypot not active"}
            
        interaction_key = f"{honeypot_id}:{source_ip}"
        
        if interaction_key not in self.active_interactions:
            interaction = InteractionLog(
                interaction_id=self._generate_interaction_id(),
                honeypot_id=honeypot_id,
                source_ip=source_ip
            )
            self.active_interactions[interaction_key] = interaction
            self.stats["total_interactions"] += 1
            self.adaptive_configs[honeypot_id]["interaction_count"] += 1
        else:
            interaction = self.active_interactions[interaction_key]
            
        response = await self._generate_response(config, interaction_type, data, interaction)
        
        if interaction_type == "command":
            interaction.add_command(data.get("command", ""))
            interaction.add_response(response.get("response", ""))
        elif interaction_type == "http_request":
            interaction.add_command(f"{data.get('method', 'GET')} {data.get('path', '/')}")
            interaction.add_response(response.get("body", "")[:500])
        elif interaction_type == "credential":
            interaction.add_credential_attempt(
                data.get("username", ""),
                data.get("password", ""),
                data.get("success", False)
            )
            self.stats["total_credentials_captured"] += 1
        elif interaction_type == "payload":
            interaction.add_payload(data.get("payload", ""))
            self.stats["total_payloads_captured"] += 1
            
        if self.communication_bus:
            await self.communication_bus.publish(
                "honeypot_interaction",
                {
                    "honeypot_id": honeypot_id,
                    "source_ip": source_ip,
                    "interaction_type": interaction_type,
                    "interaction_id": interaction.interaction_id
                }
            )
            
        return response
        
    async def _generate_response(
        self,
        config: HoneypotConfig,
        interaction_type: str,
        data: Dict,
        interaction: InteractionLog
    ) -> Dict:
        attacker_profile = self.adaptive_configs.get(config.honeypot_id, {}).get("attacker_profile")
        
        if config.honeypot_type in [HoneypotType.HTTP, HoneypotType.HTTPS]:
            body, status, headers = self.response_generator.generate_http_response(
                data.get("path", "/"),
                data.get("method", "GET"),
                data.get("headers", {}),
                attacker_profile
            )
            return {
                "status_code": status,
                "headers": headers,
                "body": body
            }
            
        elif config.honeypot_type == HoneypotType.SSH:
            response = self.response_generator.generate_ssh_response(
                data.get("command", ""),
                interaction.session_data,
                attacker_profile
            )
            return {"response": response, "prompt": interaction.session_data.get("username", "user") + "@server:~$ "}
            
        elif config.honeypot_type in [HoneypotType.MYSQL, HoneypotType.POSTGRES]:
            rows, headers = self.response_generator.generate_mysql_response(
                data.get("query", "")
            )
            return {"rows": rows, "headers": headers, "affected_rows": 0}
            
        else:
            return {"response": "OK", "status": "success"}
            
    async def shutdown_honeypot(self, honeypot_id: str) -> bool:
        if honeypot_id not in self.honeypots:
            return False
            
        self.honeypot_states[honeypot_id] = HoneypotState.SHUTDOWN
        
        for key in list(self.active_interactions.keys()):
            if key.startswith(honeypot_id + ":"):
                interaction = self.active_interactions.pop(key)
                interaction.end()
                self.completed_interactions.append(interaction)
                
        config = self.honeypots.pop(honeypot_id)
        self.honeypot_states.pop(honeypot_id, None)
        self.adaptive_configs.pop(honeypot_id, None)
        
        logger.info(f"Shutdown honeypot {honeypot_id}")
        
        return True
        
    async def get_honeypot(self, honeypot_id: str) -> Optional[Dict]:
        if honeypot_id not in self.honeypots:
            return None
            
        return {
            "config": self.honeypots[honeypot_id].to_dict(),
            "state": self.honeypot_states.get(honeypot_id, HoneypotState.SHUTDOWN).value,
            "adaptive_config": self.adaptive_configs.get(honeypot_id, {})
        }
        
    async def get_all_honeypots(self) -> List[Dict]:
        result = []
        for honeypot_id in self.honeypots:
            hp = await self.get_honeypot(honeypot_id)
            if hp:
                result.append(hp)
        return result
        
    async def get_interaction(self, interaction_id: str) -> Optional[Dict]:
        for interaction in self.active_interactions.values():
            if interaction.interaction_id == interaction_id:
                return interaction.to_dict()
                
        for interaction in self.completed_interactions:
            if interaction.interaction_id == interaction_id:
                return interaction.to_dict()
                
        return None
        
    async def get_recent_interactions(self, limit: int = 50) -> List[Dict]:
        interactions = list(self.completed_interactions)[-limit:]
        return [i.to_dict() for i in interactions]
        
    async def get_captured_credentials(self) -> List[Dict]:
        credentials = []
        for interaction in self.completed_interactions:
            credentials.extend(interaction.credentials_tried)
        for interaction in self.active_interactions.values():
            credentials.extend(interaction.credentials_tried)
        return credentials
        
    async def get_captured_payloads(self) -> List[Dict]:
        payloads = []
        for interaction in self.completed_interactions:
            for payload in interaction.payloads:
                payloads.append({
                    "interaction_id": interaction.interaction_id,
                    "source_ip": interaction.source_ip,
                    "payload": payload,
                    "timestamp": interaction.start_time.isoformat()
                })
        return payloads
        
    def _generate_honeypot_id(self) -> str:
        return f"hp_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
    def _generate_interaction_id(self) -> str:
        return f"int_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "active_honeypots": len(self.honeypots),
            "active_interactions": len(self.active_interactions),
            "completed_interactions": len(self.completed_interactions)
        }
