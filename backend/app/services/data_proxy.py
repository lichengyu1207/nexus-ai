from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.agent import Agent
from app.models.data_access import DataAccessLog
from app.models.audit import AuditLog

class DataProxy:
    """统一数据访问代理"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def read(
        self,
        dataset_name: str,
        agent_id: int,
        resource: str,
        trace_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        读取数据
        
        Args:
            dataset_name: 数据集名称
            agent_id: 智能体ID
            resource: 资源路径
            trace_id: 跟踪ID
            user_id: 用户ID
            
        Returns:
            数据内容
        """
        # 检查权限
        if not self._check_permission(dataset_name, agent_id, "read"):
            # 记录访问日志
            self._log_access(
                dataset_name=dataset_name,
                agent_id=agent_id,
                operation="read",
                resource=resource,
                trace_id=trace_id,
                user_id=user_id,
                success=False,
                error_message="权限不足"
            )
            
            # 记录审计日志
            self._log_audit(
                action="data_access_denied",
                resource_type="dataset",
                resource_id=dataset_name,
                agent_id=agent_id,
                trace_id=trace_id,
                status="failure",
                error_message=f"智能体{agent_id}无权读取数据集{dataset_name}"
            )
            
            raise PermissionError(f"智能体{agent_id}无权读取数据集{dataset_name}")
        
        # 获取数据集
        dataset = self.db.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"数据集{dataset_name}不存在")
        
        # 模拟数据读取
        data = self._fetch_data(dataset, resource)
        
        # 数据脱敏（如果需要）
        if dataset.sensitivity == "high":
            data = self._mask_sensitive_data(data, agent_id)
        
        # 记录访问日志
        self._log_access(
            dataset_name=dataset_name,
            agent_id=agent_id,
            operation="read",
            resource=resource,
            trace_id=trace_id,
            user_id=user_id,
            success=True
        )
        
        # 记录审计日志
        self._log_audit(
            action="data_read",
            resource_type="dataset",
            resource_id=dataset_name,
            agent_id=agent_id,
            trace_id=trace_id,
            status="success",
            details={"resource": resource}
        )
        
        return data
    
    def write(
        self,
        dataset_name: str,
        agent_id: int,
        resource: str,
        data: Dict[str, Any],
        trace_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        写入数据
        
        Args:
            dataset_name: 数据集名称
            agent_id: 智能体ID
            resource: 资源路径
            data: 数据内容
            trace_id: 跟踪ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        # 检查权限
        if not self._check_permission(dataset_name, agent_id, "write"):
            # 记录访问日志
            self._log_access(
                dataset_name=dataset_name,
                agent_id=agent_id,
                operation="write",
                resource=resource,
                trace_id=trace_id,
                user_id=user_id,
                success=False,
                error_message="权限不足"
            )
            
            # 记录审计日志
            self._log_audit(
                action="data_access_denied",
                resource_type="dataset",
                resource_id=dataset_name,
                agent_id=agent_id,
                trace_id=trace_id,
                status="failure",
                error_message=f"智能体{agent_id}无权写入数据集{dataset_name}"
            )
            
            raise PermissionError(f"智能体{agent_id}无权写入数据集{dataset_name}")
        
        # 获取数据集
        dataset = self.db.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"数据集{dataset_name}不存在")
        
        # 模拟数据写入
        self._store_data(dataset, resource, data)
        
        # 记录访问日志
        self._log_access(
            dataset_name=dataset_name,
            agent_id=agent_id,
            operation="write",
            resource=resource,
            trace_id=trace_id,
            user_id=user_id,
            success=True
        )
        
        # 记录审计日志
        self._log_audit(
            action="data_write",
            resource_type="dataset",
            resource_id=dataset_name,
            agent_id=agent_id,
            trace_id=trace_id,
            status="success",
            details={"resource": resource}
        )
        
        return True
    
    def _check_permission(
        self,
        dataset_name: str,
        agent_id: int,
        operation: str
    ) -> bool:
        """
        检查权限
        
        Args:
            dataset_name: 数据集名称
            agent_id: 智能体ID
            operation: 操作类型
            
        Returns:
            是否有权限
        """
        # 获取数据集
        dataset = self.db.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not dataset or not dataset.policy:
            return False
        
        # 获取智能体
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
        
        # 检查策略
        policy = dataset.policy
        agents_policy = policy.get("agents", {})
        agent_permission = agents_policy.get(agent.name, "none")
        
        # 检查权限
        if operation == "read":
            return agent_permission in ["read", "write"]
        elif operation == "write":
            return agent_permission == "write"
        
        return False
    
    def _fetch_data(self, dataset: Dataset, resource: str) -> Dict[str, Any]:
        """
        获取数据（模拟）
        
        Args:
            dataset: 数据集对象
            resource: 资源路径
            
        Returns:
            数据内容
        """
        # 模拟数据返回
        return {
            "dataset": dataset.name,
            "resource": resource,
            "data": {
                "sample": "这是一个示例数据",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _store_data(self, dataset: Dataset, resource: str, data: Dict[str, Any]) -> None:
        """
        存储数据（模拟）
        
        Args:
            dataset: 数据集对象
            resource: 资源路径
            data: 数据内容
        """
        # 模拟数据存储
        pass
    
    def _mask_sensitive_data(self, data: Dict[str, Any], agent_id: int) -> Dict[str, Any]:
        """
        数据脱敏
        
        Args:
            data: 原始数据
            agent_id: 智能体ID
            
        Returns:
            脱敏后的数据
        """
        # 简单的脱敏处理
        masked_data = data.copy()
        if "data" in masked_data:
            masked_data["data"]["sample"] = "***已脱敏***"
        return masked_data
    
    def _log_access(
        self,
        dataset_name: str,
        agent_id: int,
        operation: str,
        resource: str,
        trace_id: str,
        user_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        记录访问日志
        
        Args:
            dataset_name: 数据集名称
            agent_id: 智能体ID
            operation: 操作类型
            resource: 资源路径
            trace_id: 跟踪ID
            user_id: 用户ID
            success: 是否成功
            error_message: 错误信息
        """
        # 获取数据集ID
        dataset = self.db.query(Dataset).filter(Dataset.name == dataset_name).first()
        dataset_id = dataset.id if dataset else None
        
        access_log = DataAccessLog(
            dataset_id=dataset_id,
            agent_id=agent_id,
            user_id=user_id,
            operation=operation,
            resource=resource,
            success=success,
            error_message=error_message,
            trace_id=trace_id
        )
        self.db.add(access_log)
        self.db.commit()
    
    def _log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        agent_id: int,
        trace_id: str,
        status: str,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录审计日志
        
        Args:
            action: 操作
            resource_type: 资源类型
            resource_id: 资源ID
            agent_id: 智能体ID
            trace_id: 跟踪ID
            status: 状态
            error_message: 错误信息
            details: 详细信息
        """
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            agent_id=agent_id,
            trace_id=trace_id,
            status=status,
            error_message=error_message,
            details=details
        )
        self.db.add(audit_log)
        self.db.commit()
