"""
自定义异常类
"""
from typing import Optional


class BackupGatewayError(Exception):
    base_message = "Backup gateway error"
    error_code: str = "BACKUP_GATEWAY_ERROR"

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code or self.error_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "error_code": self.error_code,
        }


class ConfigurationError(BackupGatewayError):
    base_message = "Configuration error"
    error_code: str = "CONFIGURATION_ERROR"


class HealthCheckError(BackupGatewayError):
    base_message = "Health check error"
    error_code: str = "HEALTH_CHECK_ERROR"


class FailoverError(BackupGatewayError):
    base_message = "Failover error"
    error_code: str = "FAILOVER_ERROR"


class NotificationError(BackupGatewayError):
    base_message = "Notification error"
    error_code: str = "NOTIFICATION_ERROR"
