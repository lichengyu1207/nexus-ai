from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.tool import Tool
from app.models.agent import Agent
from app.models.audit import AuditLog

class ToolInvoker:
    """工具调用器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def invoke(
        self,
        tool_name: str,
        agent_id: int,
        params: Dict[str, Any],
        trace_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            agent_id: 智能体ID
            params: 参数
            trace_id: 跟踪ID
            user_id: 用户ID
            
        Returns:
            调用结果
        """
        # 检查工具是否存在
        tool = self.db.query(Tool).filter(Tool.name == tool_name).first()
        if not tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        # 检查工具状态
        if tool.status != "active":
            raise ValueError(f"工具已禁用: {tool_name}")
        
        # 检查权限
        if not self._check_permission(agent_id, tool.id):
            # 记录权限违规事件
            self._log_permission_violation(
                agent_id=agent_id,
                tool_name=tool_name,
                trace_id=trace_id,
                user_id=user_id
            )
            
            raise PermissionError(f"智能体{agent_id}无权调用工具{tool_name}")
        
        # 调用工具
        result = await self._execute_tool(tool, params)
        
        # 记录审计日志
        self._log_audit(
            action="tool_invoke",
            resource_type="tool",
            resource_id=tool_name,
            agent_id=agent_id,
            trace_id=trace_id,
            status="success",
            details={"params": params, "result": result}
        )
        
        return result
    
    def _check_permission(self, agent_id: int, tool_id: int) -> bool:
        """
        检查权限
        
        Args:
            agent_id: 智能体ID
            tool_id: 工具ID
            
        Returns:
            是否有权限
        """
        # 获取智能体
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
        
        # 检查工具白名单
        allowed_tools = agent.allowed_tools or []
        return tool_id in allowed_tools
    
    async def _execute_tool(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool: 工具对象
            params: 参数
            
        Returns:
            执行结果
        """
        # 根据工具类型执行不同的调用方式
        if tool.call_type == "http":
            return await self._execute_http_tool(tool, params)
        elif tool.call_type == "local":
            return await self._execute_local_tool(tool, params)
        elif tool.call_type == "grpc":
            return await self._execute_grpc_tool(tool, params)
        else:
            raise ValueError(f"未知的工具类型: {tool.call_type}")
    
    async def _execute_http_tool(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行HTTP工具调用
        
        Args:
            tool: 工具对象
            params: 参数
            
        Returns:
            执行结果
        """
        # 模拟HTTP调用
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                tool.endpoint,
                json=params,
                headers=tool.auth_config.get("headers", {})
            ) as response:
                return {
                    "status_code": response.status,
                    "body": await response.json() if response.content_type == "application/json" else await response.text()
                }
    
    async def _execute_local_tool(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行本地工具调用
        
        Args:
            tool: 工具对象
            params: 参数
            
        Returns:
            执行结果
        """
        # 模拟本地调用
        return {
            "success": True,
            "result": "本地工具执行成功"
        }
    
    async def _execute_grpc_tool(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行gRPC工具调用
        
        Args:
            tool: 工具对象
            params: 参数
            
        Returns:
            执行结果
        """
        # 模拟gRPC调用
        return {
            "success": True,
            "result": "gRPC工具执行成功"
        }
    
    def _log_permission_violation(
        self,
        agent_id: int,
        tool_name: str,
        trace_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        记录权限违规事件
        
        Args:
            agent_id: 智能体ID
            tool_name: 工具名称
            trace_id: 跟踪ID
            user_id: 用户ID
        """
        audit_log = AuditLog(
            action="tool_permission_violation",
            resource_type="tool",
            resource_id=tool_name,
            agent_id=agent_id,
            user_id=user_id,
            trace_id=trace_id,
            status="failure",
            error_message=f"智能体{agent_id}尝试调用未授权的工具{tool_name}"
        )
        self.db.add(audit_log)
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
