"""
配置变更管理系统
实现配置备份、健康检查、监控和回滚机制
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigStatus(Enum):
    """配置状态"""
    ACTIVE = "active"
    PENDING = "pending"
    ROLLBACK = "rollback"
    FAILED = "failed"


class HealthCheckStatus(Enum):
    """健康检查状态"""
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


class RollbackStatus(Enum):
    """回滚状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConfigVersion:
    """配置版本"""
    version_id: str
    config_data: Dict[str, Any]
    created_at: datetime
    status: ConfigStatus
    description: str = ""
    change_summary: Dict[str, Any] = field(default_factory=dict)
    health_check_status: Optional[HealthCheckStatus] = None
    health_check_details: Dict[str, Any] = field(default_factory=dict)
    rollback_reason: Optional[str] = None


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthCheckStatus
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class RollbackOperation:
    """回滚操作"""
    rollback_id: str
    target_version_id: str
    status: RollbackStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    affected_agents: List[str] = field(default_factory=list)


@dataclass
class MonitoringWindow:
    """监控窗口"""
    window_id: str
    start_time: datetime
    end_time: datetime
    error_rate: float
    success_rate: float
    response_time: float


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config/versions"):
        self.config_dir = os.path.join(os.path.dirname(__file__), "..", config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        
        self._config_versions: Dict[str, ConfigVersion] = {}
        self._current_version: Optional[str] = None
        self._health_check_results: Dict[str, HealthCheckResult] = {}
        self._rollback_history: List[RollbackOperation] = []
        self._monitoring_windows: List[MonitoringWindow] = []
        
        # 监控配置
        self.monitoring_window_seconds = 10
        self.error_rate_threshold = 0.05  # 5%
        self.consecutive_error_windows = 3
        
        # 加载现有配置版本
        self._load_existing_versions()
    
    def _load_existing_versions(self):
        """加载现有配置版本"""
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".json"):
                version_id = filename[:-5]  # 移除 .json 后缀
                file_path = os.path.join(self.config_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    version = ConfigVersion(
                        version_id=version_id,
                        config_data=data["config_data"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        status=ConfigStatus(data["status"]),
                        description=data.get("description", ""),
                        change_summary=data.get("change_summary", {}),
                        health_check_status=HealthCheckStatus(data["health_check_status"]) if "health_check_status" in data else None,
                        health_check_details=data.get("health_check_details", {}),
                        rollback_reason=data.get("rollback_reason", None)
                    )
                    self._config_versions[version_id] = version
                    
                    if version.status == ConfigStatus.ACTIVE:
                        self._current_version = version_id
                        
                except Exception as e:
                    logger.error(f"Failed to load config version {version_id}: {e}")
    
    def _save_version(self, version: ConfigVersion):
        """保存配置版本"""
        file_path = os.path.join(self.config_dir, f"{version.version_id}.json")
        data = {
            "version_id": version.version_id,
            "config_data": version.config_data,
            "created_at": version.created_at.isoformat(),
            "status": version.status.value,
            "description": version.description,
            "change_summary": version.change_summary,
            "health_check_status": version.health_check_status.value if version.health_check_status else None,
            "health_check_details": version.health_check_details,
            "rollback_reason": version.rollback_reason
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_config_version(self, config_data: Dict[str, Any], description: str = "") -> ConfigVersion:
        """创建新的配置版本"""
        # 生成版本号
        version_num = len(self._config_versions) + 1
        version_id = f"v{version_num}.0"
        
        # 计算变更摘要
        change_summary = {}
        if self._current_version:
            current_config = self._config_versions[self._current_version].config_data
            for key, value in config_data.items():
                if key not in current_config or current_config[key] != value:
                    change_summary[key] = {
                        "old_value": current_config.get(key),
                        "new_value": value
                    }
        
        # 创建新版本
        version = ConfigVersion(
            version_id=version_id,
            config_data=config_data,
            created_at=datetime.now(),
            status=ConfigStatus.PENDING,
            description=description,
            change_summary=change_summary
        )
        
        # 保存版本
        self._config_versions[version_id] = version
        self._save_version(version)
        
        logger.info(f"Created config version {version_id}: {description}")
        return version
    
    async def apply_config(self, version_id: str) -> bool:
        """应用配置版本"""
        if version_id not in self._config_versions:
            logger.error(f"Config version {version_id} not found")
            return False
        
        version = self._config_versions[version_id]
        
        # 标记当前版本为非活跃
        if self._current_version:
            current_version = self._config_versions[self._current_version]
            current_version.status = ConfigStatus.ROLLBACK if current_version.status == ConfigStatus.ACTIVE else current_version.status
            self._save_version(current_version)
        
        # 执行健康检查
        health_check = await self._perform_health_check(version.config_data)
        version.health_check_status = health_check.status
        version.health_check_details = health_check.details
        
        if health_check.status == HealthCheckStatus.PASS:
            # 应用配置
            version.status = ConfigStatus.ACTIVE
            self._current_version = version_id
            self._save_version(version)
            
            # 启动监控
            asyncio.create_task(self._start_monitoring())
            
            logger.info(f"Applied config version {version_id} successfully")
            return True
        else:
            # 健康检查失败，回滚
            version.status = ConfigStatus.FAILED
            self._save_version(version)
            
            if self._current_version:
                await self.rollback_to_version(self._current_version, "Health check failed")
            
            logger.error(f"Failed to apply config version {version_id}: health check failed")
            return False
    
    async def _perform_health_check(self, config_data: Dict[str, Any]) -> HealthCheckResult:
        """执行健康检查"""
        details = {}
        all_passed = True
        
        # 检查户部智能体心跳
        hubu_status = await self._check_agent_heartbeat("hubu")
        details["hubu_heartbeat"] = hubu_status
        if not hubu_status:
            all_passed = False
        
        # 模拟数据采集请求
        data_collection_status = await self._check_data_collection()
        details["data_collection"] = data_collection_status
        if not data_collection_status:
            all_passed = False
        
        # 检查数据库连接
        db_status = await self._check_database_connection()
        details["database_connection"] = db_status
        if not db_status:
            all_passed = False
        
        status = HealthCheckStatus.PASS if all_passed else HealthCheckStatus.FAIL
        return HealthCheckResult(
            status=status,
            details=details,
            timestamp=datetime.now()
        )
    
    async def _check_agent_heartbeat(self, agent_id: str) -> bool:
        """检查智能体心跳"""
        # 模拟心跳检查
        await asyncio.sleep(0.5)
        return True  # 假设心跳正常
    
    async def _check_data_collection(self) -> bool:
        """检查数据采集"""
        # 模拟数据采集检查
        await asyncio.sleep(0.5)
        return True  # 假设数据采集正常
    
    async def _check_database_connection(self) -> bool:
        """检查数据库连接"""
        # 模拟数据库连接检查
        await asyncio.sleep(0.5)
        return True  # 假设数据库连接正常
    
    async def _start_monitoring(self):
        """启动监控"""
        consecutive_error_count = 0
        
        while True:
            # 计算当前窗口的错误率
            error_rate = await self._calculate_error_rate()
            success_rate = 1.0 - error_rate
            response_time = await self._calculate_response_time()
            
            # 创建监控窗口
            window = MonitoringWindow(
                window_id=f"window_{int(time.time())}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_rate=error_rate,
                success_rate=success_rate,
                response_time=response_time
            )
            self._monitoring_windows.append(window)
            
            # 检查错误率
            if error_rate > self.error_rate_threshold:
                consecutive_error_count += 1
                logger.warning(f"High error rate detected: {error_rate:.2f}%, consecutive errors: {consecutive_error_count}")
                
                if consecutive_error_count >= self.consecutive_error_windows:
                    logger.error(f"Consecutive error windows ({consecutive_error_count}) exceeded threshold, triggering rollback")
                    # 执行回滚
                    if self._current_version:
                        # 找到上一个有效版本
                        previous_version = self._find_previous_valid_version()
                        if previous_version:
                            await self.rollback_to_version(previous_version, f"Error rate exceeded threshold: {error_rate:.2f}%")
                    consecutive_error_count = 0
            else:
                consecutive_error_count = 0
            
            # 等待下一个窗口
            await asyncio.sleep(self.monitoring_window_seconds)
    
    async def _calculate_error_rate(self) -> float:
        """计算错误率"""
        # 模拟错误率计算
        import random
        return random.uniform(0.0, 0.1)  # 0-10% 错误率
    
    async def _calculate_response_time(self) -> float:
        """计算响应时间"""
        # 模拟响应时间计算
        import random
        return random.uniform(0.1, 1.0)  # 0.1-1.0 秒
    
    def _find_previous_valid_version(self) -> Optional[str]:
        """找到上一个有效版本"""
        versions = sorted(self._config_versions.values(), key=lambda v: v.created_at, reverse=True)
        for version in versions:
            if version.version_id != self._current_version and version.status in [ConfigStatus.ACTIVE, ConfigStatus.ROLLBACK]:
                return version.version_id
        return None
    
    async def rollback_to_version(self, version_id: str, reason: str) -> RollbackOperation:
        """回滚到指定版本"""
        if version_id not in self._config_versions:
            logger.error(f"Config version {version_id} not found for rollback")
            return RollbackOperation(
                rollback_id=f"rollback_{int(time.time())}",
                target_version_id=version_id,
                status=RollbackStatus.FAILED,
                started_at=datetime.now(),
                error_message="Version not found"
            )
        
        rollback = RollbackOperation(
            rollback_id=f"rollback_{int(time.time())}",
            target_version_id=version_id,
            status=RollbackStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            # 标记当前版本为回滚
            if self._current_version:
                current_version = self._config_versions[self._current_version]
                current_version.status = ConfigStatus.ROLLBACK
                current_version.rollback_reason = reason
                self._save_version(current_version)
            
            # 激活目标版本
            target_version = self._config_versions[version_id]
            target_version.status = ConfigStatus.ACTIVE
            self._current_version = version_id
            self._save_version(target_version)
            
            # 通知所有智能体热加载配置
            await self._notify_agents_reload_config(target_version.config_data)
            
            rollback.status = RollbackStatus.COMPLETED
            rollback.completed_at = datetime.now()
            
            # 发送通知
            await self._send_rollback_notification(current_version.version_id if self._current_version else "unknown", version_id, reason)
            
            logger.info(f"Rolled back to config version {version_id}: {reason}")
            
        except Exception as e:
            rollback.status = RollbackStatus.FAILED
            rollback.error_message = str(e)
            logger.error(f"Failed to rollback to version {version_id}: {e}")
        
        self._rollback_history.append(rollback)
        return rollback
    
    async def _notify_agents_reload_config(self, config_data: Dict[str, Any]):
        """通知智能体重新加载配置"""
        # 模拟通知智能体
        agents = ["hubu", "libu", "bingbu", "libu", "gongbu"]
        for agent in agents:
            logger.info(f"Notifying agent {agent} to reload config")
            await asyncio.sleep(0.1)
    
    async def _send_rollback_notification(self, old_version: str, new_version: str, reason: str):
        """发送回滚通知"""
        # 模拟发送飞书通知
        notification = f"配置变更（{old_version}）导致异常，已自动回滚至{new_version}。异常指标：任务成功率降至92%。请检查变更内容。"
        logger.info(f"Sending Feishu notification: {notification}")
    
    def get_current_version(self) -> Optional[ConfigVersion]:
        """获取当前配置版本"""
        if self._current_version:
            return self._config_versions.get(self._current_version)
        return None
    
    def list_versions(self) -> List[ConfigVersion]:
        """列出所有配置版本"""
        return sorted(self._config_versions.values(), key=lambda v: v.created_at, reverse=True)
    
    def get_rollback_history(self) -> List[RollbackOperation]:
        """获取回滚历史"""
        return self._rollback_history
    
    def get_monitoring_windows(self) -> List[MonitoringWindow]:
        """获取监控窗口"""
        return self._monitoring_windows


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


async def submit_config_change(config_data: Dict[str, Any], description: str = "") -> ConfigVersion:
    """提交配置变更"""
    manager = get_config_manager()
    version = manager.create_config_version(config_data, description)
    await manager.apply_config(version.version_id)
    return version


async def rollback_config(version_id: str, reason: str) -> RollbackOperation:
    """回滚配置"""
    manager = get_config_manager()
    return await manager.rollback_to_version(version_id, reason)


def get_current_config() -> Optional[Dict[str, Any]]:
    """获取当前配置"""
    manager = get_config_manager()
    current_version = manager.get_current_version()
    if current_version:
        return current_version.config_data
    return None
