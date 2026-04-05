"""
智能体人才市场与技能成长系统
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """技能"""
    id: str  # 技能ID
    name: str  # 技能名称
    description: str  # 技能描述
    price: int  # 价格（积分）
    required_level: int  # 所需等级
    required_exp: int  # 所需经验值
    applicable_agents: List[str]  # 适用智能体类型
    effect: Dict[str, Any]  # 技能效果


@dataclass
class AgentLevel:
    """智能体等级"""
    level: int  # 等级
    exp_required: int  # 升级所需经验值
    skill_slots: int  # 技能槽位
    bonuses: Dict[str, Any]  # 等级奖励


@dataclass
class Bond:
    """羁绊"""
    id: str  # 羁绊ID
    name: str  # 羁绊名称
    description: str  # 羁绊描述
    required_agents: List[str]  # 所需智能体
    required_tasks: int  # 所需共同完成任务次数
    effects: Dict[str, Any]  # 羁绊效果
    is_active: bool = False  # 是否激活
    progress: int = 0  # 进度


@dataclass
class AgentGrowth:
    """智能体成长"""
    agent_id: str  # 智能体ID
    agent_type: str  # 智能体类型
    level: int  # 当前等级
    exp: int  # 当前经验值
    skills: List[str]  # 已学技能
    bonds: List[str]  # 已激活羁绊


@dataclass
class MarketListing:
    """市场 listing"""
    id: str  # listing ID
    agent_id: str  # 智能体ID
    agent_type: str  # 智能体类型
    seller_id: str  # 卖家ID
    price: int  # 价格（积分）
    level: int  # 智能体等级
    skills: List[str]  # 已学技能
    exp: int  # 当前经验值
    status: str  # 状态（active, sold, cancelled）
    created_at: float  # 创建时间


class SkillStore:
    """技能商店"""
    
    def __init__(self):
        self.skills = self._load_skills()
    
    def _load_skills(self) -> Dict[str, Skill]:
        """加载技能"""
        # 预定义技能
        skills = {
            "advanced_data_collection": Skill(
                id="advanced_data_collection",
                name="高级数据采集",
                description="提升数据采集能力，可采集更丰富的数据源",
                price=1000,
                required_level=1,
                required_exp=0,
                applicable_agents=["hu_bu"],
                effect={"collection_speed": 0.2, "data_quality": 0.15}
            ),
            "policy_interpretation": Skill(
                id="policy_interpretation",
                name="政策解读",
                description="提升政策解读能力，更准确理解政策影响",
                price=1500,
                required_level=2,
                required_exp=500,
                applicable_agents=["zhongshu", "li_bu"],
                effect={"policy_accuracy": 0.25, "analysis_depth": 0.2}
            ),
            "emotion_analysis": Skill(
                id="emotion_analysis",
                name="情绪分析",
                description="提升情绪分析能力，更好理解用户情绪",
                price=1200,
                required_level=1,
                required_exp=0,
                applicable_agents=["li_bu2"],
                effect={"emotion_detection": 0.3, "response_appropriateness": 0.2}
            ),
            "risk_prediction": Skill(
                id="risk_prediction",
                name="风险预测",
                description="提升风险预测能力，提前预警市场风险",
                price=2000,
                required_level=3,
                required_exp=1500,
                applicable_agents=["bing_bu"],
                effect={"risk_detection": 0.35, "warning_accuracy": 0.3}
            )
        }
        return skills
    
    def get_skills(self) -> List[Skill]:
        """获取所有技能"""
        return list(self.skills.values())
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_id)
    
    def get_skills_by_agent_type(self, agent_type: str) -> List[Skill]:
        """根据智能体类型获取技能"""
        return [skill for skill in self.skills.values() if agent_type in skill.applicable_agents]
    
    def add_skill(self, skill: Skill):
        """添加技能"""
        self.skills[skill.id] = skill
        logger.info(f"添加技能: {skill.name}")


class ExperienceManager:
    """经验值管理"""
    
    def __init__(self):
        self.agent_growth = {}
        self.level_settings = self._load_level_settings()
    
    def _load_level_settings(self) -> List[AgentLevel]:
        """加载等级设置"""
        return [
            AgentLevel(level=1, exp_required=0, skill_slots=2, bonuses={}),
            AgentLevel(level=2, exp_required=500, skill_slots=3, bonuses={"collection_speed": 0.1}),
            AgentLevel(level=3, exp_required=1500, skill_slots=4, bonuses={"analysis_depth": 0.15}),
            AgentLevel(level=4, exp_required=3000, skill_slots=5, bonuses={"response_quality": 0.2}),
            AgentLevel(level=5, exp_required=5000, skill_slots=6, bonuses={"all_stats": 0.25})
        ]
    
    def get_agent_growth(self, agent_id: str) -> Optional[AgentGrowth]:
        """获取智能体成长信息"""
        return self.agent_growth.get(agent_id)
    
    def add_experience(self, agent_id: str, agent_type: str, base_exp: int, difficulty: float = 1.0, timeliness: float = 1.0, rating: float = 1.0):
        """添加经验值
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            base_exp: 基础经验值
            difficulty: 难度系数
            timeliness: 时效系数
            rating: 评价系数
        """
        # 计算经验值
        exp = int(base_exp * difficulty * timeliness * rating)
        
        # 获取或创建智能体成长信息
        if agent_id not in self.agent_growth:
            self.agent_growth[agent_id] = AgentGrowth(
                agent_id=agent_id,
                agent_type=agent_type,
                level=1,
                exp=0,
                skills=[],
                bonds=[]
            )
        
        growth = self.agent_growth[agent_id]
        growth.exp += exp
        
        # 检查是否升级
        self._check_level_up(growth)
        
        logger.info(f"智能体 {agent_id} 获得 {exp} 经验值，当前经验: {growth.exp}")
        return exp
    
    def _check_level_up(self, growth: AgentGrowth):
        """检查是否升级"""
        current_level = growth.level
        
        # 查找下一级
        for level_setting in self.level_settings:
            if level_setting.level > current_level and growth.exp >= level_setting.exp_required:
                growth.level = level_setting.level
                logger.info(f"智能体 {growth.agent_id} 升级到 {growth.level} 级")
                break
    
    def get_level_settings(self) -> List[AgentLevel]:
        """获取等级设置"""
        return self.level_settings


class BondManager:
    """羁绊管理"""
    
    def __init__(self):
        self.bonds = self._load_bonds()
        self.agent_tasks = {}
    
    def _load_bonds(self) -> Dict[str, Bond]:
        """加载羁绊"""
        return {
            "li_hu_bond": Bond(
                id="li_hu_bond",
                name="礼户联动",
                description="礼部和户部协同工作，提升用户满意度",
                required_agents=["li_bu2", "hu_bu"],
                required_tasks=5,
                effects={"user_satisfaction": 0.1}
            ),
            "li_bing_bond": Bond(
                id="li_bing_bond",
                name="礼兵联动",
                description="礼部和兵部协同工作，提升用户体验",
                required_agents=["li_bu2", "bing_bu"],
                required_tasks=3,
                effects={"emotion_handling": 0.15, "risk_warning": 0.2}
            )
        }
    
    def get_bonds(self) -> List[Bond]:
        """获取所有羁绊"""
        return list(self.bonds.values())
    
    def get_bond(self, bond_id: str) -> Optional[Bond]:
        """获取羁绊"""
        return self.bonds.get(bond_id)
    
    def record_task(self, agent_ids: List[str]):
        """记录任务完成
        
        Args:
            agent_ids: 参与任务的智能体ID列表
        """
        # 排序智能体ID，确保一致性
        sorted_agents = sorted(agent_ids)
        key = "_&".join(sorted_agents)
        
        # 更新任务计数
        if key not in self.agent_tasks:
            self.agent_tasks[key] = 0
        self.agent_tasks[key] += 1
        
        # 检查是否激活羁绊
        self._check_bond_activation(sorted_agents)
    
    def _check_bond_activation(self, agent_types: List[str]):
        """检查是否激活羁绊"""
        for bond in self.bonds.values():
            # 检查是否拥有所有必需的智能体
            if all(agent_type in agent_types for agent_type in bond.required_agents):
                # 检查任务完成次数
                key = "_&".join(sorted(bond.required_agents))
                task_count = self.agent_tasks.get(key, 0)
                
                bond.progress = task_count
                if task_count >= bond.required_tasks and not bond.is_active:
                    bond.is_active = True
                    logger.info(f"激活羁绊: {bond.name}")
    
    def get_available_bonds(self, agent_types: List[str]) -> List[Bond]:
        """获取可用的羁绊"""
        available = []
        for bond in self.bonds.values():
            # 检查是否拥有所有必需的智能体
            if all(agent_type in agent_types for agent_type in bond.required_agents):
                available.append(bond)
        return available


class TalentMarket:
    """人才市场"""
    
    def __init__(self):
        self.listings = {}
        self.transaction_fee = 0.1  # 交易手续费
    
    def create_listing(self, agent_id: str, agent_type: str, seller_id: str, price: int, level: int, skills: List[str], exp: int) -> str:
        """创建listing
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            seller_id: 卖家ID
            price: 价格
            level: 智能体等级
            skills: 已学技能
            exp: 当前经验值
            
        Returns:
            listing ID
        """
        listing_id = f"listing_{int(time.time() * 1000)}"
        self.listings[listing_id] = MarketListing(
            id=listing_id,
            agent_id=agent_id,
            agent_type=agent_type,
            seller_id=seller_id,
            price=price,
            level=level,
            skills=skills,
            exp=exp,
            status="active",
            created_at=time.time()
        )
        logger.info(f"创建listing: {listing_id} - 智能体 {agent_id} 售价 {price} 积分")
        return listing_id
    
    def get_listings(self, agent_type: Optional[str] = None) -> List[MarketListing]:
        """获取listings
        
        Args:
            agent_type: 智能体类型（可选）
            
        Returns:
            listing列表
        """
        listings = [listing for listing in self.listings.values() if listing.status == "active"]
        if agent_type:
            listings = [listing for listing in listings if listing.agent_type == agent_type]
        return listings
    
    def purchase_listing(self, listing_id: str, buyer_id: str) -> Optional[MarketListing]:
        """购买listing
        
        Args:
            listing_id: listing ID
            buyer_id: 买家ID
            
        Returns:
            购买的listing
        """
        if listing_id not in self.listings:
            return None
        
        listing = self.listings[listing_id]
        if listing.status != "active":
            return None
        
        # 计算手续费
        fee = int(listing.price * self.transaction_fee)
        
        # 更新listing状态
        listing.status = "sold"
        logger.info(f"智能体 {listing.agent_id} 已售出，售价 {listing.price} 积分，手续费 {fee} 积分")
        
        return listing
    
    def cancel_listing(self, listing_id: str) -> bool:
        """取消listing
        
        Args:
            listing_id: listing ID
            
        Returns:
            是否取消成功
        """
        if listing_id not in self.listings:
            return False
        
        listing = self.listings[listing_id]
        if listing.status != "active":
            return False
        
        listing.status = "cancelled"
        logger.info(f"取消listing: {listing_id}")
        return True


class TalentSystem:
    """智能体人才市场与技能成长系统"""
    
    def __init__(self):
        self.skill_store = SkillStore()
        self.experience_manager = ExperienceManager()
        self.bond_manager = BondManager()
        self.talent_market = TalentMarket()
        logger.info("智能体人才市场与技能成长系统初始化完成")
    
    def purchase_skill(self, agent_id: str, agent_type: str, skill_id: str, user_id: str) -> bool:
        """购买技能
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            skill_id: 技能ID
            user_id: 用户ID
            
        Returns:
            是否购买成功
        """
        # 获取技能
        skill = self.skill_store.get_skill(skill_id)
        if not skill:
            return False
        
        # 检查是否适用
        if agent_type not in skill.applicable_agents:
            return False
        
        # 获取智能体成长信息
        growth = self.experience_manager.get_agent_growth(agent_id)
        if not growth:
            # 创建智能体成长信息
            growth = AgentGrowth(
                agent_id=agent_id,
                agent_type=agent_type,
                level=1,
                exp=0,
                skills=[],
                bonds=[]
            )
            self.experience_manager.agent_growth[agent_id] = growth
        
        # 检查等级和经验值要求
        if growth.level < skill.required_level or growth.exp < skill.required_exp:
            return False
        
        # 检查技能槽位
        level_settings = self.experience_manager.get_level_settings()
        skill_slots = 0
        for level_setting in level_settings:
            if level_setting.level == growth.level:
                skill_slots = level_setting.skill_slots
                break
        
        if len(growth.skills) >= skill_slots:
            return False
        
        # 添加技能
        if skill_id not in growth.skills:
            growth.skills.append(skill_id)
            logger.info(f"用户 {user_id} 为智能体 {agent_id} 购买技能 {skill.name}")
            return True
        
        return False
    
    def add_experience(self, agent_id: str, agent_type: str, base_exp: int, difficulty: float = 1.0, timeliness: float = 1.0, rating: float = 1.0) -> int:
        """添加经验值
        
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
        return self.experience_manager.add_experience(
            agent_id=agent_id,
            agent_type=agent_type,
            base_exp=base_exp,
            difficulty=difficulty,
            timeliness=timeliness,
            rating=rating
        )
    
    def record_task(self, agent_ids: List[str], agent_types: List[str]):
        """记录任务完成
        
        Args:
            agent_ids: 参与任务的智能体ID列表
            agent_types: 参与任务的智能体类型列表
        """
        # 记录任务
        self.bond_manager.record_task(agent_types)
    
    def get_agent_growth(self, agent_id: str) -> Optional[AgentGrowth]:
        """获取智能体成长信息"""
        return self.experience_manager.get_agent_growth(agent_id)
    
    def get_skills(self, agent_type: Optional[str] = None) -> List[Skill]:
        """获取技能列表"""
        if agent_type:
            return self.skill_store.get_skills_by_agent_type(agent_type)
        return self.skill_store.get_skills()
    
    def get_bonds(self, agent_types: Optional[List[str]] = None) -> List[Bond]:
        """获取羁绊列表"""
        if agent_types:
            return self.bond_manager.get_available_bonds(agent_types)
        return self.bond_manager.get_bonds()
    
    def create_market_listing(self, agent_id: str, agent_type: str, seller_id: str, price: int) -> Optional[str]:
        """创建市场listing
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            seller_id: 卖家ID
            price: 价格
            
        Returns:
            listing ID
        """
        # 获取智能体成长信息
        growth = self.experience_manager.get_agent_growth(agent_id)
        if not growth:
            return None
        
        return self.talent_market.create_listing(
            agent_id=agent_id,
            agent_type=agent_type,
            seller_id=seller_id,
            price=price,
            level=growth.level,
            skills=growth.skills,
            exp=growth.exp
        )
    
    def get_market_listings(self, agent_type: Optional[str] = None) -> List[MarketListing]:
        """获取市场listings"""
        return self.talent_market.get_listings(agent_type)
    
    def purchase_market_listing(self, listing_id: str, buyer_id: str) -> Optional[MarketListing]:
        """购买市场listing
        
        Args:
            listing_id: listing ID
            buyer_id: 买家ID
            
        Returns:
            购买的listing
        """
        return self.talent_market.purchase_listing(listing_id, buyer_id)


# 全局系统实例
talent_system: Optional[TalentSystem] = None


def get_talent_system() -> TalentSystem:
    """获取智能体人才市场与技能成长系统实例"""
    global talent_system
    if talent_system is None:
        talent_system = TalentSystem()
    return talent_system


def purchase_skill(agent_id: str, agent_type: str, skill_id: str, user_id: str) -> bool:
    """购买技能"""
    system = get_talent_system()
    return system.purchase_skill(agent_id, agent_type, skill_id, user_id)


def add_experience(agent_id: str, agent_type: str, base_exp: int, difficulty: float = 1.0, timeliness: float = 1.0, rating: float = 1.0) -> int:
    """添加经验值"""
    system = get_talent_system()
    return system.add_experience(agent_id, agent_type, base_exp, difficulty, timeliness, rating)


def record_task(agent_ids: List[str], agent_types: List[str]):
    """记录任务完成"""
    system = get_talent_system()
    system.record_task(agent_ids, agent_types)


def get_agent_growth(agent_id: str) -> Optional[AgentGrowth]:
    """获取智能体成长信息"""
    system = get_talent_system()
    return system.get_agent_growth(agent_id)


def get_skills(agent_type: Optional[str] = None) -> List[Skill]:
    """获取技能列表"""
    system = get_talent_system()
    return system.get_skills(agent_type)


def get_bonds(agent_types: Optional[List[str]] = None) -> List[Bond]:
    """获取羁绊列表"""
    system = get_talent_system()
    return system.get_bonds(agent_types)


def create_market_listing(agent_id: str, agent_type: str, seller_id: str, price: int) -> Optional[str]:
    """创建市场listing"""
    system = get_talent_system()
    return system.create_market_listing(agent_id, agent_type, seller_id, price)


def get_market_listings(agent_type: Optional[str] = None) -> List[MarketListing]:
    """获取市场listings"""
    system = get_talent_system()
    return system.get_market_listings(agent_type)


def purchase_market_listing(listing_id: str, buyer_id: str) -> Optional[MarketListing]:
    """购买市场listing"""
    system = get_talent_system()
    return system.purchase_market_listing(listing_id, buyer_id)
