"""
配置管理模块 - 使用 pydantic-settings 管理环境变量和配置
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict, Optional


def find_env_file() -> Optional[Path]:
    current = Path(__file__).resolve().parent
    env_path = current / ".env"
    if env_path.exists():
        return env_path
    cwd_env = Path.cwd() / "gatekeeper" / ".env"
    if cwd_env.exists():
        return cwd_env
    return None


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    scan_interval: int = 10
    heartbeat_timeout: int = 30
    restart_cooling: int = 60
    restart_command_template: str = "systemctl restart agent-{agent_id}"
    audit_log_type: str = "file"
    audit_log_path: str = "./logs/restart.log"
    database_url: str = "postgresql://user:pass@localhost/gatekeeper"
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    agent_restart_commands: Dict[str, str] = {}

    model_config = {
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_restart_command(self, agent_id: str) -> str:
        if agent_id in self.agent_restart_commands:
            return self.agent_restart_commands[agent_id]
        return self.restart_command_template.format(agent_id=agent_id)


_env_file = find_env_file()
if _env_file:
    settings = Settings(_env_file=str(_env_file))
else:
    settings = Settings()
