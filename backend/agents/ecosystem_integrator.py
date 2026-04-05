"""
智能体生态系统集成器
将所有智能体系统整合为一个完整的生态系统
"""

import logging
from typing import Dict, Any, List, Optional

from .talent_market import (
    get_talent_system, purchase_skill, add_experience, record_task,
    get_agent_growth, get_skills, get_bonds, create_market_listing,
    get_market_listings, purchase_market_listing
)
from .integrated_system import (
    process_integrated_request, get_integrated_status,
    simulate_integrated_failure, optimize_integrated_system,
    shutdown_integrated_system
)

logger = logging.getLogger(__name__)


class EcosystemIntegrator:
    """智能体生态系统集成器"""
    
    def __init__(self):
        self.talent_system = get_talent_system()
        logger.info("智能体生态系统集成器初始化完成")
    
    def process_user_request(self, query: str, user_id: str, agent_ids: List[str] = None) -> Dict[str, Any]:
        """处理用户请求
        
        Args:
            query: 用户查询
            user_id: 用户ID
            agent_ids: 参与处理的智能体ID列表（可选）
            
        Returns:
            处理结果
        """
        # 步骤1: 处理集成请求
        integrated_result = process_integrated_request(query)
        
        # 步骤2: 为参与任务的智能体添加经验值
        if agent_ids:
            for agent_id in agent_ids:
                # 假设智能体类型为hu_bu，实际应根据agent_id解析
                agent_type = "hu_bu"
                # 添加经验值（基础经验50，难度系数1.0，时效系数1.0，评价系数1.0）
                add_experience(agent_id, agent_type, 50, 1.0, 1.0, 1.0)
        
        # 步骤3: 记录任务完成，用于羁绊系统
        if agent_ids and len(agent_ids) >= 2:
            # 假设智能体类型列表
            agent_types = ["hu_bu" if "hu_bu" in id else "li_bu2" for id in agent_ids]
            record_task(agent_ids, agent_types)
        
        # 步骤4: 整合结果
        result = {
            "query": query,
            "integrated_result": integrated_result,
            "user_id": user_id,
            "agent_ids": agent_ids,
            "timestamp": "2026-04-01"
        }
        
        logger.info(f"处理用户请求: {query}，用户: {user_id}")
        return result
    
    def get_ecosystem_status(self) -> Dict[str, Any]:
        """获取生态系统状态
        
        Returns:
            生态系统状态
        """
        # 获取集成系统状态
        integrated_status = get_integrated_status()
        
        # 获取技能列表
        skills = get_skills()
        
        # 获取羁绊列表
        bonds = get_bonds()
        
        # 获取市场listings
        listings = get_market_listings()
        
        status = {
            "integrated_system": integrated_status,
            "skill_store": {
                "total_skills": len(skills),
                "skill_names": [skill.name for skill in skills]
            },
            "bonds": {
                "total_bonds": len(bonds),
                "active_bonds": [bond.name for bond in bonds if bond.is_active]
            },
            "talent_market": {
                "total_listings": len(listings),
                "listings": [{
                    "id": listing.id,
                    "agent_type": listing.agent_type,
                    "price": listing.price,
                    "level": listing.level
                } for listing in listings]
            }
        }
        
        return status
    
    def purchase_agent_skill(self, agent_id: str, agent_type: str, skill_id: str, user_id: str) -> bool:
        """为智能体购买技能
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            skill_id: 技能ID
            user_id: 用户ID
            
        Returns:
            是否购买成功
        """
        return purchase_skill(agent_id, agent_type, skill_id, user_id)
    
    def add_agent_experience(self, agent_id: str, agent_type: str, base_exp: int, 
                           difficulty: float = 1.0, timeliness: float = 1.0, rating: float = 1.0) -> int:
        """为智能体添加经验值
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            base_exp: 基础经验值
            difficulty: 难度系数
            timeliness: 时效系数
            rating: 评价系数
            
        Returns:
            获得的经验值
        """
        return add_experience(agent_id, agent_type, base_exp, difficulty, timeliness, rating)
    
    def create_agent_listing(self, agent_id: str, agent_type: str, seller_id: str, price: int) -> Optional[str]:
        """在人才市场创建智能体listing
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            seller_id: 卖家ID
            price: 价格
            
        Returns:
            listing ID
        """
        return create_market_listing(agent_id, agent_type, seller_id, price)
    
    def purchase_agent(self, listing_id: str, buyer_id: str) -> Optional[Dict[str, Any]]:
        """购买智能体
        
        Args:
            listing_id: listing ID
            buyer_id: 买家ID
            
        Returns:
            购买结果
        """
        listing = purchase_market_listing(listing_id, buyer_id)
        if listing:
            return {
                "success": True,
                "agent_id": listing.agent_id,
                "agent_type": listing.agent_type,
                "price": listing.price,
                "level": listing.level,
                "skills": listing.skills
            }
        return None
    
    def get_agent_growth_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体成长信息
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            智能体成长信息
        """
        growth = get_agent_growth(agent_id)
        if growth:
            return {
                "agent_id": growth.agent_id,
                "agent_type": growth.agent_type,
                "level": growth.level,
                "exp": growth.exp,
                "skills": growth.skills,
                "bonds": growth.bonds
            }
        return None
    
    def optimize_ecosystem(self):
        """优化生态系统"""
        optimize_integrated_system()
        logger.info("生态系统优化完成")
    
    def shutdown_ecosystem(self):
        """关闭生态系统"""
        shutdown_integrated_system()
        logger.info("生态系统已关闭")


# 全局生态系统实例
ecosystem_integrator: Optional[EcosystemIntegrator] = None


def get_ecosystem_integrator() -> EcosystemIntegrator:
    """获取智能体生态系统集成器实例"""
    global ecosystem_integrator
    if ecosystem_integrator is None:
        ecosystem_integrator = EcosystemIntegrator()
    return ecosystem_integrator


def process_ecosystem_request(query: str, user_id: str, agent_ids: List[str] = None) -> Dict[str, Any]:
    """处理生态系统请求"""
    integrator = get_ecosystem_integrator()
    return integrator.process_user_request(query, user_id, agent_ids)


def get_ecosystem_status() -> Dict[str, Any]:
    """获取生态系统状态"""
    integrator = get_ecosystem_integrator()
    return integrator.get_ecosystem_status()


def purchase_agent_skill(agent_id: str, agent_type: str, skill_id: str, user_id: str) -> bool:
    """为智能体购买技能"""
    integrator = get_ecosystem_integrator()
    return integrator.purchase_agent_skill(agent_id, agent_type, skill_id, user_id)


def add_agent_experience(agent_id: str, agent_type: str, base_exp: int, 
                       difficulty: float = 1.0, timeliness: float = 1.0, rating: float = 1.0) -> int:
    """为智能体添加经验值"""
    integrator = get_ecosystem_integrator()
    return integrator.add_agent_experience(agent_id, agent_type, base_exp, difficulty, timeliness, rating)


def create_agent_listing(agent_id: str, agent_type: str, seller_id: str, price: int) -> Optional[str]:
    """在人才市场创建智能体listing"""
    integrator = get_ecosystem_integrator()
    return integrator.create_agent_listing(agent_id, agent_type, seller_id, price)


def purchase_agent(listing_id: str, buyer_id: str) -> Optional[Dict[str, Any]]:
    """购买智能体"""
    integrator = get_ecosystem_integrator()
    return integrator.purchase_agent(listing_id, buyer_id)


def get_agent_growth_info(agent_id: str) -> Optional[Dict[str, Any]]:
    """获取智能体成长信息"""
    integrator = get_ecosystem_integrator()
    return integrator.get_agent_growth_info(agent_id)


def optimize_ecosystem():
    """优化生态系统"""
    integrator = get_ecosystem_integrator()
    integrator.optimize_ecosystem()


def shutdown_ecosystem():
    """关闭生态系统"""
    integrator = get_ecosystem_integrator()
    integrator.shutdown_ecosystem()
