import json
import uuid
from typing import Optional, Dict, Any
import asyncio
from app.task_engine.dag_schema import DAG, DAGNode, Edge
from app.task_engine.dag_parser import DAGParser


class LLMPlanner:
    def __init__(self, llm_api_config: Dict[str, Any]):
        """初始化LLMPlanner
        
        Args:
            llm_api_config: LLM API配置，包含api_key、base_url等
        """
        self.llm_api_config = llm_api_config
        self.dag_parser = DAGParser()  # 用于fallback机制
    
    async def plan(self, user_query: str) -> DAG:
        """使用LLM规划任务执行流程
        
        Args:
            user_query: 用户查询字符串
            
        Returns:
            DAG: 生成的任务执行计划
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 构造System Prompt
                system_prompt = self._construct_system_prompt()
                
                # 构造用户查询
                user_message = f"用户查询: {user_query}"
                
                # 调用LLM API
                llm_response = await self._call_llm_api(system_prompt, user_message)
                
                # 解析LLM返回的JSON
                dag_dict = self._parse_llm_response(llm_response)
                
                # 转换为DAG对象
                dag = self._convert_to_dag(dag_dict)
                
                return dag
            
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    # 达到最大重试次数，使用fallback机制
                    print(f"LLM规划失败，使用fallback机制: {str(e)}")
                    return self._fallback_mechanism(user_query)
                
                # 等待后重试
                wait_time = 2 ** retry_count  # 指数退避
                print(f"LLM规划失败，{wait_time}秒后重试 ({retry_count}/{max_retries}): {str(e)}")
                await asyncio.sleep(wait_time)
    
    def _construct_system_prompt(self) -> str:
        """构造System Prompt
        
        Returns:
            str: 完整的System Prompt
        """
        return """你是一个智能任务规划器，负责为用户查询创建最优的执行计划。

## 可用的 AI 智能体团队

### 1. 房产分析师 (property_analyzer)
- **角色**：专业房产市场分析师
- **能力**：
  - 分析房产市场趋势
  - 评估房产价值
  - 提供房产投资建议
  - 处理与房产相关的查询

### 2. 数据收集员 (data_collector)
- **角色**：专业数据采集专家
- **能力**：
  - 从多个数据源收集房产数据
  - 爬取房产网站信息
  - 整合政府公开数据
  - 处理数据格式转换

### 3. 数据清洗员 (data_cleaner)
- **角色**：数据预处理专家
- **能力**：
  - 清理和标准化原始数据
  - 处理缺失值和异常值
  - 数据去重和验证
  - 转换数据为可用格式

### 4. 报告生成器 (report_generator)
- **角色**：专业报告撰写专家
- **能力**：
  - 生成结构化分析报告
  - 整合多源数据洞察
  - 提供可视化建议
  - 输出专业格式的结果

## 任务要求

根据用户查询，创建一个执行计划，包含：
1. 选择合适的智能体组合
2. 定义智能体执行顺序和依赖关系
3. 为每个智能体分配适当的输入/输出

## 输出格式

请严格按照以下 JSON 格式输出执行计划：

{
  "id": "唯一标识符",
  "name": "计划名称",
  "description": "计划描述",
  "nodes": [
    {
      "id": "节点ID",
      "agent_name": "智能体名称",
      "input_mapping": {
        "智能体输入参数": "DAG上下文中的键名"
      },
      "output_key": "输出在DAG上下文中的键名",
      "description": "节点描述"
    }
  ],
  "edges": [
    {
      "source": "源节点ID",
      "target": "目标节点ID"
    }
  ]
}

## 示例

用户查询："长沙某某小区房价"

输出：

{
  "id": "plan_1",
  "name": "房产价格分析计划",
  "description": "分析长沙某某小区的房价情况",
  "nodes": [
    {
      "id": "data_collection",
      "agent_name": "data_collector",
      "input_mapping": {
        "query": "user_query"
      },
      "output_key": "raw_property_data",
      "description": "收集长沙某某小区的房产数据"
    },
    {
      "id": "data_cleaning",
      "agent_name": "data_cleaner",
      "input_mapping": {
        "data": "raw_property_data"
      },
      "output_key": "cleaned_property_data",
      "description": "清理和标准化房产数据"
    },
    {
      "id": "price_analysis",
      "agent_name": "property_analyzer",
      "input_mapping": {
        "data": "cleaned_property_data",
        "query": "user_query"
      },
      "output_key": "price_analysis_result",
      "description": "分析房产价格趋势和价值"
    },
    {
      "id": "report_generation",
      "agent_name": "report_generator",
      "input_mapping": {
        "analysis_result": "price_analysis_result"
      },
      "output_key": "final_report",
      "description": "生成房产价格分析报告"
    }
  ],
  "edges": [
    {
      "source": "data_collection",
      "target": "data_cleaning"
    },
    {
      "source": "data_cleaning",
      "target": "price_analysis"
    },
    {
      "source": "price_analysis",
      "target": "report_generation"
    }
  ]
}

请确保输出严格符合JSON格式，不要包含任何额外的文本或解释。"""
    
    async def _call_llm_api(self, system_prompt: str, user_message: str) -> str:
        """调用LLM API
        
        Args:
            system_prompt: System Prompt
            user_message: 用户消息
            
        Returns:
            str: LLM API返回的文本
        """
        # 这里实现具体的LLM API调用
        # 例如使用OpenAI API
        # 暂时返回模拟数据
        return '''{
  "id": "plan_'''+str(uuid.uuid4())+'''",
  "name": "房产价格分析计划",
  "description": "分析用户查询的房产价格情况",
  "nodes": [
    {
      "id": "data_collection",
      "agent_name": "data_collector",
      "input_mapping": {
        "query": "user_query"
      },
      "output_key": "raw_property_data",
      "description": "收集房产数据"
    },
    {
      "id": "data_cleaning",
      "agent_name": "data_cleaner",
      "input_mapping": {
        "data": "raw_property_data"
      },
      "output_key": "cleaned_property_data",
      "description": "清理和标准化房产数据"
    },
    {
      "id": "price_analysis",
      "agent_name": "property_analyzer",
      "input_mapping": {
        "data": "cleaned_property_data",
        "query": "user_query"
      },
      "output_key": "price_analysis_result",
      "description": "分析房产价格趋势和价值"
    },
    {
      "id": "report_generation",
      "agent_name": "report_generator",
      "input_mapping": {
        "analysis_result": "price_analysis_result"
      },
      "output_key": "final_report",
      "description": "生成房产价格分析报告"
    }
  ],
  "edges": [
    {
      "source": "data_collection",
      "target": "data_cleaning"
    },
    {
      "source": "data_cleaning",
      "target": "price_analysis"
    },
    {
      "source": "price_analysis",
      "target": "report_generation"
    }
  ]
}'''
    
    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """解析LLM返回的响应
        
        Args:
            llm_response: LLM API返回的文本
            
        Returns:
            Dict[str, Any]: 解析后的JSON字典
        """
        # 提取JSON部分
        # 简单实现：假设返回的就是纯JSON
        return json.loads(llm_response)
    
    def _convert_to_dag(self, dag_dict: Dict[str, Any]) -> DAG:
        """将字典转换为DAG对象
        
        Args:
            dag_dict: DAG的字典表示
            
        Returns:
            DAG: DAG对象
        """
        # 创建节点列表
        nodes = []
        for node_dict in dag_dict.get("nodes", []):
            node = DAGNode(
                id=node_dict["id"],
                agent_name=node_dict["agent_name"],
                input_mapping=node_dict.get("input_mapping", {}),
                output_key=node_dict["output_key"],
                description=node_dict.get("description")
            )
            nodes.append(node)
        
        # 创建边列表
        edges = []
        for edge_dict in dag_dict.get("edges", []):
            edge = Edge(
                source=edge_dict["source"],
                target=edge_dict["target"]
            )
            edges.append(edge)
        
        # 创建DAG对象
        dag = DAG(
            id=dag_dict["id"],
            name=dag_dict["name"],
            nodes=nodes,
            edges=edges,
            description=dag_dict.get("description")
        )
        
        return dag
    
    def _fallback_mechanism(self, user_query: str) -> DAG:
        """当LLM规划失败时的fallback机制
        
        Args:
            user_query: 用户查询字符串
            
        Returns:
            DAG: 使用基于规则的解析器生成的计划
        """
        # 使用现有的DAGParser作为fallback
        return self.dag_parser.parse(user_query)


def create_llm_planner(llm_api_config: Dict[str, Any]) -> LLMPlanner:
    """创建LLMPlanner实例
    
    Args:
        llm_api_config: LLM API配置
        
    Returns:
        LLMPlanner: LLMPlanner实例
    """
    return LLMPlanner(llm_api_config)
