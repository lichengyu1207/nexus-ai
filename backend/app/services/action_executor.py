import asyncio
import redis
from datetime import datetime
from typing import Dict, Any, Optional
from app.services.atomic_actions import AtomicAction, HttpAction
from app.models.atomic_action import AtomicAction as AtomicActionModel, ActionStatus
from app.models.audit import AuditLog
from sqlalchemy.orm import Session

class ActionExecutor:
    """原子动作执行器"""
    
    def __init__(self, db: Session, redis_client: redis.Redis = None):
        self.db = db
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.actions = {
            "http_request": HttpAction()
        }
    
    async def execute(
        self,
        action_name: str,
        params: Dict[str, Any],
        trace_id: str,
        agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        执行原子动作
        
        Args:
            action_name: 动作名称
            params: 参数
            trace_id: 跟踪ID
            agent_id: 智能体ID
            
        Returns:
            执行结果
        """
        # 获取动作
        action = self.actions.get(action_name)
        if not action:
            raise ValueError(f"未知的动作类型: {action_name}")
        
        # 创建执行记录
        db_action = AtomicActionModel(
            action_name=action_name,
            params=params,
            status=ActionStatus.PENDING,
            max_attempts=action.retry_policy.get("max_attempts", 3),
            agent_id=agent_id,
            trace_id=trace_id
        )
        self.db.add(db_action)
        self.db.commit()
        self.db.refresh(db_action)
        
        # 执行动作（带重试）
        max_attempts = action.retry_policy.get("max_attempts", 3)
        delay = action.retry_policy.get("delay", 1)
        
        for attempt in range(1, max_attempts + 1):
            try:
                # 更新状态为运行中
                db_action.status = ActionStatus.RUNNING
                db_action.attempts = attempt
                self.db.commit()
                
                # 执行动作
                result = await action.execute(params)
                
                # 更新状态为完成
                db_action.status = ActionStatus.COMPLETED
                db_action.result = result
                self.db.commit()
                
                # 记录审计日志
                self._log_audit(
                    action=f"execute_{action_name}",
                    resource_type="atomic_action",
                    resource_id=str(db_action.id),
                    agent_id=agent_id,
                    trace_id=trace_id,
                    status="success",
                    details={"attempt": attempt, "result": result}
                )
                
                return result
                
            except Exception as e:
                # 记录错误
                error_message = str(e)
                
                if attempt < max_attempts:
                    # 等待后重试
                    await asyncio.sleep(delay)
                else:
                    # 达到最大重试次数，标记为失败
                    db_action.status = ActionStatus.FAILED
                    db_action.error = error_message
                    self.db.commit()
                    
                    # 如果动作有补偿，推入补偿队列
                    if hasattr(action, 'compensate') and callable(action.compensate):
                        self._push_compensation(action_name, params, trace_id, agent_id)
                    
                    # 记录审计日志
                    self._log_audit(
                        action=f"execute_{action_name}",
                        resource_type="atomic_action",
                        resource_id=str(db_action.id),
                        agent_id=agent_id,
                        trace_id=trace_id,
                        status="failure",
                        error_message=error_message,
                        details={"attempt": attempt}
                    )
                    
                    raise Exception(f"动作执行失败，已重试{max_attempts}次: {error_message}")
        
        return {}
    
    def _push_compensation(
        self,
        action_name: str,
        params: Dict[str, Any],
        trace_id: str,
        agent_id: Optional[int] = None
    ) -> None:
        """
        推入补偿队列
        
        Args:
            action_name: 动作名称
            params: 参数
            trace_id: 跟踪ID
            agent_id: 智能体ID
        """
        compensation_data = {
            "action_name": action_name,
            "params": params,
            "trace_id": trace_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.redis_client.lpush("compensation_queue", str(compensation_data))
    
    def _log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        agent_id: Optional[int],
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
