from typing import List, Dict, Any
from app.task_engine.dag_schema import DAG, DAGNode, Edge


def parse_workflow_from_intent(user_query: str, available_agents: List[str]) -> DAG:
    """
    从用户意图解析工作流，生成DAG
    
    Args:
        user_query: 用户查询字符串
        available_agents: 可用智能体列表
    
    Returns:
        生成的DAG对象
    """
    # 转换为小写以便匹配
    query_lower = user_query.lower()
    
    # 关键词匹配
    has_price = any(keyword in query_lower for keyword in ['房价', '价格', '价值', '市值'])
    has_analysis = any(keyword in query_lower for keyword in ['分析', '评估', '研究', '调研'])
    has_market = any(keyword in query_lower for keyword in ['市场', '趋势', '行情'])
    
    # 生成DAG
    nodes = []
    edges = []
    node_id_counter = 1
    
    # 初始数据收集节点
    data_collector_node = DAGNode(
        id=f"node_{node_id_counter}",
        agent_name="data_collector",
        input_mapping={},
        output_key="property_data",
        description="收集房产基本数据"
    )
    nodes.append(data_collector_node)
    node_id_counter += 1
    
    # 价格收集节点
    if has_price:
        price_node = DAGNode(
            id=f"node_{node_id_counter}",
            agent_name="price_collector",
            input_mapping={"property_data": "property_data"},
            output_key="price_data",
            description="收集房产价格数据"
        )
        nodes.append(price_node)
        # 添加依赖边
        edges.append(Edge(source=data_collector_node.id, target=price_node.id))
        node_id_counter += 1
    
    # 市场分析节点
    if has_market:
        market_node = DAGNode(
            id=f"node_{node_id_counter}",
            agent_name="market_analyzer",
            input_mapping={"property_data": "property_data"},
            output_key="market_data",
            description="分析房产市场趋势"
        )
        nodes.append(market_node)
        # 添加依赖边
        edges.append(Edge(source=data_collector_node.id, target=market_node.id))
        node_id_counter += 1
    
    # 综合分析节点
    if has_analysis:
        analysis_node = DAGNode(
            id=f"node_{node_id_counter}",
            agent_name="property_analyzer",
            input_mapping={
                "property_data": "property_data",
                "price_data": "price_data" if has_price else "",
                "market_data": "market_data" if has_market else ""
            },
            output_key="analysis_result",
            description="综合分析房产数据"
        )
        nodes.append(analysis_node)
        # 添加依赖边
        edges.append(Edge(source=data_collector_node.id, target=analysis_node.id))
        if has_price:
            edges.append(Edge(source=price_node.id, target=analysis_node.id))
        if has_market:
            edges.append(Edge(source=market_node.id, target=analysis_node.id))
    
    # 创建DAG
    dag = DAG(
        id=f"dag_{hash(user_query)}",
        name="Generated Workflow",
        nodes=nodes,
        edges=edges,
        description=f"Based on user query: {user_query}"
    )
    
    return dag


def generate_simple_collect_analyze_dag() -> DAG:
    """
    生成一个简单的两节点DAG：收集 -> 分析
    
    Returns:
        生成的DAG对象
    """
    # 创建节点
    collect_node = DAGNode(
        id="collect_node",
        agent_name="data_collector",
        input_mapping={},
        output_key="property_data",
        description="收集房产数据"
    )
    
    analyze_node = DAGNode(
        id="analyze_node",
        agent_name="property_analyzer",
        input_mapping={"property_data": "property_data"},
        output_key="analysis_result",
        description="分析房产数据"
    )
    
    # 创建边
    edge = Edge(source="collect_node", target="analyze_node")
    
    # 创建DAG
    dag = DAG(
        id="simple_collect_analyze",
        name="Collect and Analyze Workflow",
        nodes=[collect_node, analyze_node],
        edges=[edge],
        description="A simple workflow with two nodes: collect data -> analyze data"
    )
    
    return dag