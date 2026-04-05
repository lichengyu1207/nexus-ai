from typing import Dict, Type, Optional
from app.ai_agents.base_agent import BaseAgent
from app.ai_agents.property_analyzer import PropertyAnalyzerAgent
from app.ai_agents.data_collector import DataCollectorAgent
from app.ai_agents.data_cleaner import DataCleanerAgent
from app.ai_agents.data_verifier import DataVerifierAgent
from app.ai_agents.report_generator import ReportGeneratorAgent
from app.ai_agents.requirement_analyzer import RequirementAnalyzerAgent
from app.ai_agents.market_analyst import MarketAnalystAgent


class AgentFactory:
    """Factory class for creating AI agents based on type"""
    
    _agent_registry: Dict[str, Type[BaseAgent]] = {}
    
    @classmethod
    def register_agent(cls, agent_type: str, agent_class: Type[BaseAgent]):
        """Register a new agent type"""
        cls._agent_registry[agent_type] = agent_class
    
    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> Optional[BaseAgent]:
        """Create an agent instance based on type"""
        agent_class = cls._agent_registry.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class(**kwargs)
    
    @classmethod
    def get_available_agents(cls) -> list:
        """Get list of available agent types"""
        return list(cls._agent_registry.keys())


# Register default agents
AgentFactory.register_agent("property_analyzer", PropertyAnalyzerAgent)
AgentFactory.register_agent("data_collector", DataCollectorAgent)
AgentFactory.register_agent("data_cleaner", DataCleanerAgent)
AgentFactory.register_agent("data_verifier", DataVerifierAgent)
AgentFactory.register_agent("report_generator", ReportGeneratorAgent)
AgentFactory.register_agent("requirement_analyzer", RequirementAnalyzerAgent)
AgentFactory.register_agent("market_analyst", MarketAnalystAgent)