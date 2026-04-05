"""
LangGraph工作流节点
将现有代理封装为LangGraph节点
"""
from typing import Dict, Any
from app.workflow.state import AgentState
from app.ai_agents.requirement_analyzer import RequirementAnalyzerAgent
from app.ai_agents.data_collector import DataCollectorAgent
from app.ai_agents.market_analyst import MarketAnalystAgent
from app.ai_agents.report_generator import ReportGeneratorAgent
import logging

logger = logging.getLogger(__name__)


async def requirement_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    需求分析节点
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("Executing requirement_node")
    
    try:
        agent = RequirementAnalyzerAgent()
        result = await agent.execute({"query": state.get("query", "")})
        
        state["requirement"] = result
        state["current_step"] = "requirement_completed"
        
        logger.info(f"Requirement analysis completed: {result}")
        
    except Exception as e:
        logger.error(f"Requirement node failed: {str(e)}")
        state["errors"].append(f"Requirement analysis failed: {str(e)}")
    
    return state


async def collector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    数据采集节点
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("Executing collector_node")
    
    try:
        agent = DataCollectorAgent()
        
        requirement = state.get("requirement", {})
        query = requirement.get("query", state.get("query", ""))
        
        result = await agent.execute({"query": query})
        
        state["collected_data"] = result
        state["current_step"] = "collection_completed"
        
        logger.info(f"Data collection completed")
        
    except Exception as e:
        logger.error(f"Collector node failed: {str(e)}")
        state["errors"].append(f"Data collection failed: {str(e)}")
    
    return state


async def analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    市场分析节点
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("Executing analyst_node")
    
    try:
        agent = MarketAnalystAgent()
        
        collected_data = state.get("collected_data", {})
        requirement = state.get("requirement", {})
        
        result = await agent.execute({
            "data": collected_data,
            "requirement": requirement
        })
        
        state["analysis_result"] = result
        state["current_step"] = "analysis_completed"
        
        logger.info(f"Market analysis completed")
        
    except Exception as e:
        logger.error(f"Analyst node failed: {str(e)}")
        state["errors"].append(f"Market analysis failed: {str(e)}")
    
    return state


async def report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    报告生成节点
    
    Args:
        state: 当前状态
        
    Returns:
        Dict: 更新后的状态
    """
    logger.info("Executing report_node")
    
    try:
        agent = ReportGeneratorAgent()
        
        analysis_result = state.get("analysis_result", {})
        collected_data = state.get("collected_data", {})
        requirement = state.get("requirement", {})
        
        result = await agent.execute({
            "analysis": analysis_result,
            "data": collected_data,
            "requirement": requirement
        })
        
        state["final_report"] = result
        state["current_step"] = "report_completed"
        
        logger.info(f"Report generation completed")
        
    except Exception as e:
        logger.error(f"Report node failed: {str(e)}")
        state["errors"].append(f"Report generation failed: {str(e)}")
    
    return state


def should_collect_more(state: Dict[str, Any]) -> str:
    """
    判断是否需要补充数据采集
    
    Args:
        state: 当前状态
        
    Returns:
        str: "continue" 或 "skip"
    """
    collected_data = state.get("collected_data", {})
    confidence = collected_data.get("confidence", 0)
    
    if confidence < 0.7:
        logger.info(f"Data confidence {confidence} < 0.7, collecting more data")
        return "continue"
    
    logger.info(f"Data confidence {confidence} >= 0.7, skipping additional collection")
    return "skip"
