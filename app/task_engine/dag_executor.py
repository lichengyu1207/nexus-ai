import asyncio
from typing import Dict, Any, Optional
import uuid
from app.task_engine.dag_schema import DAG, DAGNode
from app.ai_agents.agent_factory import AgentFactory
from app.ai_agents.event_system import (
    event_manager, WorkflowStartEvent, WorkflowProgressEvent, WorkflowCompleteEvent, WorkflowErrorEvent
)


class DAGExecutor:
    """DAG执行器，负责执行工作流"""
    
    def __init__(self, max_retries: int = 2):
        """
        初始化DAG执行器
        
        Args:
            max_retries: 节点执行失败时的最大重试次数
        """
        self.max_retries = max_retries
        self.agent_factory = AgentFactory()
        self.executor_id = str(uuid.uuid4())
    
    async def execute(self, dag: DAG, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行DAG工作流
        
        Args:
            dag: 要执行的DAG
            initial_data: 初始数据
        
        Returns:
            执行结果，包含所有节点的输出
        """
        # 发布工作流开始事件
        workflow_start_event = WorkflowStartEvent(
            self.executor_id, 
            dag.name, 
            initial_data
        )
        event_manager.publish(workflow_start_event)
        
        try:
            # 计算每个节点的依赖关系
            dependencies = self._calculate_dependencies(dag)
            
            # 初始化执行上下文
            context = initial_data.copy()
            
            # 初始化节点状态
            node_status = {node.id: "pending" for node in dag.nodes}
            node_results = {}
        
        # 执行节点
        total_nodes = len(dag.nodes)
        while any(status != "completed" for status in node_status.values()):
            # 找到所有可执行的节点（依赖已完成）
            executable_nodes = [
                node for node in dag.nodes 
                if node_status[node.id] == "pending" 
                and all(node_status[dep] == "completed" for dep in dependencies[node.id])
            ]
            
            if not executable_nodes:
                # 没有可执行的节点，但还有未完成的节点，说明存在循环依赖
                raise ValueError("DAG contains circular dependencies")
            
            # 并行执行可执行节点
            tasks = []
            for node in executable_nodes:
                # 发布工作流进度事件
                completed_nodes = sum(1 for status in node_status.values() if status == "completed")
                progress = (completed_nodes + len(executable_nodes)) / total_nodes
                
                workflow_progress_event = WorkflowProgressEvent(
                    self.executor_id, 
                    dag.name, 
                    progress, 
                    node.id
                )
                event_manager.publish(workflow_progress_event)
                
                tasks.append(self._execute_node(node, context.copy(), node_status, node_results))
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks)
            
            # 更新上下文
            for result in results:
                if result:
                    context.update(result)
            
            # 检查是否所有节点都已完成
            completed_nodes = sum(1 for status in node_status.values() if status == "completed")
            if completed_nodes == total_nodes:
                # 发布工作流完成事件
                workflow_complete_event = WorkflowCompleteEvent(
                    self.executor_id, 
                    dag.name, 
                    context
                )
                event_manager.publish(workflow_complete_event)
        
        return context
        except Exception as e:
            # 发布工作流错误事件
            workflow_error_event = WorkflowErrorEvent(
                self.executor_id, 
                dag.name, 
                str(e)
            )
            event_manager.publish(workflow_error_event)
            raise
    
    def _calculate_dependencies(self, dag: DAG) -> Dict[str, list]:
        """
        计算每个节点的依赖关系
        
        Args:
            dag: DAG对象
        
        Returns:
            每个节点的依赖节点ID列表
        """
        dependencies = {node.id: [] for node in dag.nodes}
        
        for edge in dag.edges:
            dependencies[edge.target].append(edge.source)
        
        return dependencies
    
    async def _execute_node(self, node: DAGNode, context: Dict[str, Any], 
                          node_status: Dict[str, str], node_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个节点
        
        Args:
            node: 要执行的节点
            context: 当前执行上下文
            node_status: 节点状态字典
            node_results: 节点结果字典
        
        Returns:
            节点执行结果
        """
        print(f"开始执行节点: {node.id} - {node.agent_name}")
        node_status[node.id] = "running"
        
        # 准备节点输入
        node_input = {}
        for input_key, context_key in node.input_mapping.items():
            if context_key in context:
                node_input[input_key] = context[context_key]
        
        # 执行节点，带重试机制
        retries = 0
        while retries <= self.max_retries:
            try:
                # 创建智能体并执行
                agent = self.agent_factory.create_agent(node.agent_name)
                if not agent:
                    raise ValueError(f"Agent not found: {node.agent_name}")
                
                # 执行智能体
                result = await agent.execute(node_input)
                
                # 处理结果
                if result.get("success"):
                    output = {node.output_key: result.get("result", {})}
                    node_results[node.id] = output
                    node_status[node.id] = "completed"
                    print(f"节点执行成功: {node.id} - 输出键: {node.output_key}")
                    print(f"节点输出: {output[node.output_key]}")
                    return output
                else:
                    raise Exception(f"Agent execution failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"节点执行失败: {node.id} - 错误: {str(e)}")
                retries += 1
                if retries > self.max_retries:
                    node_status[node.id] = "failed"
                    raise
                print(f"重试执行节点: {node.id} (尝试 {retries}/{self.max_retries})")
                # 等待一段时间后重试
                await asyncio.sleep(1)
        
        return {}


# 示例智能体，用于测试
from app.ai_agents.base_agent import BaseAgent

class DataCollectorAgent(BaseAgent):
    """数据收集智能体"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "data_collector"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据收集任务"""
        print("执行数据收集智能体")
        # 模拟数据收集
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "result": {
                "address": "北京市朝阳区建国路88号",
                "type": "apartment",
                "area": 120,
                "age": 5,
                "description": "豪华公寓，交通便利"
            }
        }


class PropertyAnalyzerAgent(BaseAgent):
    """房产分析智能体"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "property_analyzer"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行房产分析任务"""
        print("执行房产分析智能体")
        # 模拟分析
        await asyncio.sleep(2)
        
        property_data = task.get("property_data", {})
        
        return {
            "success": True,
            "result": {
                "market_value": 15000000,
                "price_per_square": 125000,
                "analysis": "该房产位于核心区域，交通便利，价值较高",
                "recommendations": ["适合投资", "建议保持现状"]
            }
        }


# 注册测试智能体
AgentFactory.register_agent("data_collector", DataCollectorAgent)
AgentFactory.register_agent("property_analyzer", PropertyAnalyzerAgent)


if __name__ == "__main__":
    """示例：执行一个简单的两节点DAG"""
    import asyncio
    from app.task_engine.dag_parser import generate_simple_collect_analyze_dag
    
    async def main():
        print("===== 任务编排引擎示例 =====")
        
        # 生成简单的两节点DAG
        dag = generate_simple_collect_analyze_dag()
        print(f"生成DAG: {dag.name}")
        print(f"节点数量: {len(dag.nodes)}")
        print(f"边数量: {len(dag.edges)}")
        
        # 打印DAG结构
        print("\nDAG结构:")
        for node in dag.nodes:
            print(f"  节点: {node.id} - {node.agent_name} -> 输出键: {node.output_key}")
        for edge in dag.edges:
            print(f"  边: {edge.source} -> {edge.target}")
        
        # 执行DAG
        print("\n开始执行DAG...")
        executor = DAGExecutor(max_retries=2)
        initial_data = {}
        
        try:
            result = await executor.execute(dag, initial_data)
            
            print("\n===== 执行结果 =====")
            print(f"最终输出:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"执行失败: {str(e)}")
    
    # 运行示例
    asyncio.run(main())