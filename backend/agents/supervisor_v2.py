"""
优化后的主管代理
实现智能任务分解、动态调度、依赖管理、错误处理和Token集成
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from .base import BaseAgent
from .task_graph import TaskGraph, TaskNode, TaskGraphBuilder, SubtaskStatus
from ..database import get_db_connection
from ..services.token_service import token_service
from ..services.notification_service import notification_service

logger = logging.getLogger(__name__)


class SupervisorAgentV2(BaseAgent):
    """
    优化后的主管代理V2
    
    特性：
    - 智能任务分解（DAG）
    - 并行执行无依赖任务
    - 错误处理与重试
    - Token预扣/确认/回滚
    - 详细步骤记录
    """
    
    def __init__(self, agent_name: str, task_id: str, bus, user_id: str = None):
        super().__init__(agent_name, task_id, bus)
        self.user_id = user_id
        self.task_graph: Optional[TaskGraph] = None
        self.subtask_results: Dict[str, Any] = {}
        self.completed_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()
        self.token_reservation_id: Optional[str] = None
        self.estimated_tokens: int = 100
        self.max_workflow_timeout: int = 300  # 5分钟总超时
    
    async def work(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        主工作流程
        
        1. 记录开始
        2. 预扣Token
        3. 解析任务并生成任务图
        4. 执行任务图
        5. 汇总结果
        6. 确认/回滚Token
        """
        context = context or {}
        
        try:
            await self.record_step('workflow_start', '开始处理用户请求', 'completed', {
                'query_preview': user_query[:100]
            })
            
            await self._reserve_tokens(user_query)
            
            await self.record_step('task_decomposition', '正在分析需求并生成任务图...', 'running')
            self.task_graph = await self._decompose_task(user_query, context)
            
            if not self.task_graph or not self.task_graph.nodes:
                raise ValueError("任务分解失败：无法生成有效的任务图")
            
            await self._save_task_graph()
            
            await self.record_step('task_graph_created', f'任务图已生成，共{len(self.task_graph.nodes)}个子任务', 'completed', {
                'execution_order': self.task_graph.get_execution_order()
            })
            
            success = await self._execute_graph()
            
            if success:
                final_result = await self._synthesize_results(user_query)
                
                await self._confirm_tokens()
                
                await self.record_step('workflow_completed', '工作流执行完成', 'completed', {
                    'completed_nodes': list(self.completed_nodes),
                    'failed_nodes': list(self.failed_nodes)
                })
                
                return {
                    'status': 'success',
                    'result': final_result,
                    'task_graph': self.task_graph.to_dict()
                }
            else:
                raise Exception("工作流执行失败")
                
        except Exception as e:
            logger.error(f"Supervisor workflow failed: {e}")
            
            if self.token_reservation_id:
                await self._rollback_tokens(str(e))
            
            await self.record_step('workflow_failed', f'工作流执行失败: {str(e)}', 'failed', {
                'error': str(e),
                'completed_nodes': list(self.completed_nodes),
                'failed_nodes': list(self.failed_nodes)
            })
            
            return {
                'status': 'error',
                'message': str(e),
                'task_graph': self.task_graph.to_dict() if self.task_graph else None
            }
    
    async def _reserve_tokens(self, user_query: str) -> None:
        """
        预扣Token
        """
        self.estimated_tokens = self._estimate_tokens(user_query)
        
        if not self.user_id:
            logger.warning("No user_id, skipping token reservation")
            return
        
        try:
            result = await token_service.reserve_tokens(
                user_id=self.user_id,
                action_type="supervisor_task",
                estimated_tokens=self.estimated_tokens,
                metadata={
                    "task_id": self.task_id,
                    "query_preview": user_query[:100]
                }
            )
            
            if result.get("success"):
                self.token_reservation_id = result.get("reservation_id")
                await self.record_step('token_reserved', f'预扣 {self.estimated_tokens} Token', 'completed', {
                    'reservation_id': self.token_reservation_id,
                    'cost_integral': result.get('cost_integral', 0)
                })
            else:
                raise Exception(f"Token预扣失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            logger.error(f"Token reservation failed: {e}")
            raise
    
    async def _confirm_tokens(self) -> None:
        """
        确认Token消耗
        """
        if not self.token_reservation_id:
            return
        
        actual_tokens = self._calculate_actual_tokens()
        
        try:
            result = await token_service.confirm_consumption(
                reservation_id=self.token_reservation_id,
                actual_tokens=actual_tokens
            )
            
            await self.record_step('token_confirmed', f'实际消耗 {actual_tokens} Token', 'completed', {
                'actual_tokens': actual_tokens,
                'actual_cost': result.get('actual_cost', 0)
            })
            
        except Exception as e:
            logger.error(f"Token confirmation failed: {e}")
    
    async def _rollback_tokens(self, reason: str) -> None:
        """
        回滚Token
        """
        if not self.token_reservation_id:
            return
        
        try:
            await token_service.rollback_reservation(
                reservation_id=self.token_reservation_id,
                reason=reason
            )
            
            await self.record_step('token_rolled_back', f'Token已退还: {reason}', 'completed')
            
            if self.user_id:
                try:
                    await notification_service.send_notification(
                        user_id=self.user_id,
                        type="refund",
                        title="任务执行失败，积分已退还",
                        content=f"您的任务执行失败，已退还 {self.estimated_tokens} Token（{self.estimated_tokens/100:.2f}积分）。原因：{reason}",
                        metadata={"task_id": self.task_id}
                    )
                except Exception as e:
                    logger.warning(f"Failed to send refund notification: {e}")
                    
        except Exception as e:
            logger.error(f"Token rollback failed: {e}")
    
    def _estimate_tokens(self, query: str) -> int:
        """
        估算Token消耗
        """
        base_tokens = 50
        
        query_length = len(query) // 2
        
        task_count = len(self.task_graph.nodes) if self.task_graph else 3
        
        estimated = base_tokens + query_length + task_count * 30
        
        return max(estimated, 50)
    
    def _calculate_actual_tokens(self) -> int:
        """
        计算实际Token消耗
        """
        total_tokens = 0
        
        for node_id, result in self.subtask_results.items():
            if isinstance(result, dict):
                input_text = str(result.get('input', ''))
                output_text = str(result.get('output', ''))
                total_tokens += len(input_text) // 2 + len(output_text) // 2
        
        total_tokens += len(self.completed_nodes) * 10
        
        return max(total_tokens, 20)
    
    async def _decompose_task(self, user_query: str, context: Dict[str, Any]) -> TaskGraph:
        """
        任务分解
        
        根据用户请求类型选择合适的任务图模板
        """
        query_lower = user_query.lower()
        
        if any(kw in query_lower for kw in ['对比', '比较', 'vs', '区别']):
            locations = self._extract_locations(user_query, context)
            if len(locations) >= 2:
                return TaskGraphBuilder.build_comparison_analysis(user_query, locations)
        
        if any(kw in query_lower for kw in ['批量', '多个', '所有']):
            queries = self._extract_batch_queries(user_query, context)
            if len(queries) > 1:
                return TaskGraphBuilder.build_batch_analysis(queries)
        
        location = context.get('location') or self._extract_single_location(user_query)
        return TaskGraphBuilder.build_simple_analysis(user_query, location)
    
    def _extract_locations(self, query: str, context: Dict[str, Any]) -> List[str]:
        """
        从查询中提取多个位置
        """
        locations = []
        
        if 'locations' in context:
            locations.extend(context['locations'])
        
        import re
        patterns = [
            r'([\u4e00-\u9fa5]+[市区县])',
            r'([\u4e00-\u9fa5]+小区)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query)
            locations.extend(matches)
        
        return list(set(locations))[:5]
    
    def _extract_single_location(self, query: str) -> Optional[str]:
        """
        从查询中提取单个位置
        """
        import re
        match = re.search(r'([\u4e00-\u9fa5]+[市区县])', query)
        if match:
            return match.group(1)
        return None
    
    def _extract_batch_queries(self, query: str, context: Dict[str, Any]) -> List[str]:
        """
        从查询中提取批量查询
        """
        if 'queries' in context:
            return context['queries']
        
        return [query]
    
    async def _save_task_graph(self) -> None:
        """
        保存任务图到数据库
        """
        if not self.task_graph:
            return
        
        conn = await get_db_connection()
        try:
            graph_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO task_graphs (id, supervisor_task_id, graph_definition, status, created_at)
                VALUES ($1, $2, $3, 'running', $4)
                """,
                (graph_id, self.task_id, self.task_graph.to_json(), datetime.utcnow().isoformat())
            )
            
            for node_id, node in self.task_graph.nodes.items():
                await conn.execute(
                    """
                    INSERT INTO subtask_executions (id, task_graph_id, subtask_id, agent_name, status, input_data, created_at)
                    VALUES ($1, $2, $3, $4, 'pending', $5, $6)
                    """,
                    (
                        str(uuid.uuid4()),
                        graph_id,
                        node_id,
                        node.agent_name,
                        json.dumps(node.input_data, ensure_ascii=False),
                        datetime.utcnow().isoformat()
                    )
                )
            
            await conn.commit()
            self.graph_id = graph_id
            
        finally:
            await conn.close()
    
    async def _execute_graph(self) -> bool:
        """
        执行任务图
        
        使用拓扑排序并行执行
        """
        max_iterations = len(self.task_graph.nodes) * 3
        iteration = 0
        
        while not self.task_graph.is_completed() and iteration < max_iterations:
            iteration += 1
            
            if self.task_graph.has_failed_critical():
                logger.error("Critical task failed, terminating workflow")
                return False
            
            ready_nodes = self.task_graph.get_ready_nodes(self.completed_nodes, self.failed_nodes)
            
            if not ready_nodes:
                await asyncio.sleep(0.5)
                continue
            
            tasks = [self._execute_subtask(node) for node in ready_nodes]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for node, result in zip(ready_nodes, results):
                await self._handle_subtask_result(node, result)
        
        return self.task_graph.is_completed() and not self.task_graph.has_failed_critical()
    
    async def _execute_subtask(self, node: TaskNode) -> Any:
        """
        执行单个子任务
        """
        node.status = SubtaskStatus.RUNNING
        node.started_at = datetime.utcnow().isoformat()
        
        await self._update_subtask_status(node.id, 'running')
        
        await self.record_step(f'subtask_start_{node.id}', f'开始执行子任务: {node.id}', 'running', {
            'agent': node.agent_name,
            'input': node.input_data
        })
        
        try:
            result = await asyncio.wait_for(
                self._dispatch_to_agent(node),
                timeout=node.timeout_seconds
            )
            
            node.status = SubtaskStatus.COMPLETED
            node.completed_at = datetime.utcnow().isoformat()
            node.output_data = result
            
            await self._update_subtask_status(node.id, 'completed', output_data=result)
            
            await self.record_step(f'subtask_complete_{node.id}', f'子任务完成: {node.id}', 'completed', {
                'output_preview': str(result)[:200] if result else None
            })
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"子任务超时: {node.id}"
            node.status = SubtaskStatus.FAILED
            node.error_message = error_msg
            await self._update_subtask_status(node.id, 'failed', error_message=error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = str(e)
            node.status = SubtaskStatus.FAILED
            node.error_message = error_msg
            await self._update_subtask_status(node.id, 'failed', error_message=error_msg)
            raise
    
    async def _dispatch_to_agent(self, node: TaskNode) -> Any:
        """
        将子任务分发给对应的代理
        """
        if self.bus:
            await self.send(
                recipient=node.agent_name,
                type='request',
                content={
                    'subtask_id': node.id,
                    'input': node.input_data,
                    'task_id': self.task_id
                }
            )
            
            response = await self._wait_for_agent_response(node.id, timeout=node.timeout_seconds)
            return response
        
        return {"status": "mock", "message": "No message bus configured"}
    
    async def _wait_for_agent_response(self, subtask_id: str, timeout: int = 60) -> Any:
        """
        等待代理响应
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                messages = await self.receive(timeout=1)
                if messages:
                    for msg in messages:
                        content = msg.get('content', {})
                        if content.get('subtask_id') == subtask_id:
                            return content.get('result')
            except asyncio.TimeoutError:
                continue
        
        raise TimeoutError(f"Agent response timeout for subtask {subtask_id}")
    
    async def _handle_subtask_result(self, node: TaskNode, result: Any) -> None:
        """
        处理子任务结果
        """
        if isinstance(result, Exception):
            await self._handle_subtask_failure(node, result)
        else:
            self.subtask_results[node.id] = result
            self.completed_nodes.add(node.id)
            self.task_graph.update_node_status(node.id, SubtaskStatus.COMPLETED)
    
    async def _handle_subtask_failure(self, node: TaskNode, error: Exception) -> None:
        """
        处理子任务失败
        """
        logger.error(f"Subtask {node.id} failed: {error}")
        
        if node.retry_count < node.max_retries:
            node.retry_count += 1
            node.status = SubtaskStatus.RETRYING
            
            await self.record_step(f'subtask_retry_{node.id}', f'子任务重试: {node.id} (第{node.retry_count}次)', 'running', {
                'error': str(error)
            })
            
            await self._update_subtask_status(node.id, 'retrying', error_message=str(error))
            
            await asyncio.sleep(2 ** node.retry_count)
            
            try:
                result = await self._execute_subtask(node)
                await self._handle_subtask_result(node, result)
                return
            except Exception as retry_error:
                error = retry_error
        
        node.status = SubtaskStatus.FAILED
        node.error_message = str(error)
        self.failed_nodes.add(node.id)
        self.task_graph.update_node_status(node.id, SubtaskStatus.FAILED)
        
        await self._update_subtask_status(node.id, 'failed', error_message=str(error))
        
        await self.record_step(f'subtask_failed_{node.id}', f'子任务失败: {node.id}', 'failed', {
            'error': str(error),
            'critical': node.critical
        })
        
        if node.critical:
            dependents = self.task_graph.get_dependents(node.id)
            for dep_id in dependents:
                dep_node = self.task_graph.get_node(dep_id)
                if dep_node:
                    dep_node.status = SubtaskStatus.SKIPPED
                    self.failed_nodes.add(dep_id)
                    await self._update_subtask_status(dep_id, 'skipped', error_message="依赖任务失败")
    
    async def _update_subtask_status(
        self, 
        subtask_id: str, 
        status: str, 
        output_data: Any = None,
        error_message: str = None
    ) -> None:
        """
        更新子任务状态到数据库
        """
        if not hasattr(self, 'graph_id'):
            return
        
        conn = await get_db_connection()
        try:
            update_fields = ["status = ?", "started_at = ?"]
            params = [status, datetime.utcnow().isoformat()]
            
            if output_data is not None:
                update_fields.append("output_data = ?")
                params.append(json.dumps(output_data, ensure_ascii=False))
            
            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            if status in ['completed', 'failed', 'skipped']:
                update_fields.append("completed_at = ?")
                params.append(datetime.utcnow().isoformat())
            
            params.extend([self.graph_id, subtask_id])
            
            await conn.execute(
                f"""
                UPDATE subtask_executions 
                SET {', '.join(update_fields)}
                WHERE task_graph_id = ? AND subtask_id = ?
                """,
                params
            )
            await conn.commit()
            
        finally:
            await conn.close()
    
    async def _synthesize_results(self, user_query: str) -> Dict[str, Any]:
        """
        汇总所有子任务结果
        """
        synthesized = {
            'query': user_query,
            'completed_subtasks': list(self.completed_nodes),
            'failed_subtasks': list(self.failed_nodes),
            'results': {}
        }
        
        for node_id, result in self.subtask_results.items():
            node = self.task_graph.get_node(node_id)
            if node:
                synthesized['results'][node.agent_name] = result
        
        return synthesized
