"""
多元化智能体招募系统API路由
实现招募、保底、概率等功能
"""
import json
import logging
import random
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..database_pg import get_db

logger = logging.getLogger(__name__)


@dataclass
class RecruitResult:
    """招募结果"""
    success: bool
    user_agent_id: Optional[str] = None
    template_id: Optional[str] = None
    name: Optional[str] = None
    rarity: Optional[str] = None
    department: Optional[str] = None
    skills: Optional[List] = None
    cost: int = 0
    is_new: bool = False
    guarantee_triggered: Optional[str] = None
    error: Optional[str] = None

    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "user_agent_id": self.user_agent_id,
            "template_id": self.template_id,
            "name": self.name,
            "rarity": self.rarity,
            "department": self.department,
            "skills": self.skills,
            "cost": self.cost,
            "is_new": self.is_new,
            "guarantee_triggered": self.guarantee_triggered,
            "error": self.error,
        }


    
    def __str__(self) -> str:
        if self.success:
            return f"✅ {self.name} ({self.rarity}) - {self.department}"
        return f"❌ {self.error}"


    

@dataclass
class RecruitStats:
    """招募统计"""
    total_recruits: int
    sr_guarantee_count: int
    ssr_guarantee_count: int
    sr_guarantee_max: int = 10
    ssr_guarantee_max: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_recruits": self.total_recruits,
            "sr_guarantee_count": self.sr_guarantee_count,
            "ssr_guarantee_count": self.ssr_guarantee_count,
            "sr_guarantee_progress": f"{self.sr_guarantee_count}/{self.sr_guarantee_max}",
            "ssr_guarantee_progress": f"{self.ssr_guarantee_count}/{self.ssr_guarantee_max}",
            "sr_guarantee_percent": round((self.sr_guarantee_count / self.sr_guarantee_max) * 100, 1),
            "ssr_guarantee_percent": round((self.ssr_guarantee_count / self.ssr_guarantee_max) * 100, 1),
        }


    

class RecruitSystem:
    """
    招募系统
    
    功能：
    - 基础招募（100积分）
    - 高级招募（1000积分）
    - 保底机制（10次SR保底，50次SSR保底）
    - 概率系统
    """
    
    BASIC_COST = 100
    PREMIUM_COST = 1000
    
    BASIC_PROBABILITY = {
        "N": 0.60,
        "R": 0.30,
        "SR": 0.08,
        "SSR": 0.015,
        "UR": 0.005,
    }
    
    PREMIUM_PROBABILITY = {
        "N": 0.30,
        "R": 0.40,
        "SR": 0.20,
        "SSR": 0.08,
        "UR": 0.02,
    }
    
    RARITY_LEVEL_CAP = {
        "N": 30,
        "R": 50,
        "SR": 70,
        "SSR": 90,
        "UR": 100,
    }
    
    RARITY_COLORS = {
        "N": "#9e9e9e",
        "R": "#3498db",
        "SR": "#9b59b6",
        "SSR": "#f39c12",
        "UR": "#e74c3c",
    }
    
    SKILL_UNLOCK_LEVELS = {
        1: 1,
        2: 20,
        3: 50,
    }
    
    BREAKTHROUGH_COST = {
        "N": {"integral": 5000, "material": "晋升令N"},
        "R": {"integral": 10000, "material": "晋升令R"},
        "SR": {"integral": 30000, "material": "晋升令SR"},
        "SSR": {"integral": 100000, "material": "晋升令SSR"},
    }
    
    RARITY_ORDER = ["N", "R", "SR", "SSR", "UR"]
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("RecruitSystem initialized")
    
    async def get_probability_info(self, recruit_type: str = "basic") -> Dict[str, Any]:
        """获取招募概率信息"""
        probability = self.BASIC_PROBABILITY if recruit_type == "basic" else self.PREMIUM_PROBABILITY
        
        return {
            "recruit_type": recruit_type,
            "cost": self.BASIC_COST if recruit_type == "basic" else self.PREMIUM_COST,
            "probability": probability,
            "guarantee": {
                "sr_guarantee": 10,
                "ssr_guarantee": 50,
            }
        }
    
    async def recruit(
        self,
        user_id: str,
        recruit_type: str = "basic"
    ) -> RecruitResult:
        """
        执行招募
        
        Args:
            user_id: 用户ID
            recruit_type: 招募类型 (basic/premium)
            
        Returns:
            招募结果
        """
        if not self._initialized:
            await self.initialize()
        
        cost = self.BASIC_COST if recruit_type == "basic" else self.PREMIUM_COST
        probability = self.BASIC_PROBABILITY if recruit_type == "basic" else self.PREMIUM_PROBABILITY
        
        async with get_db() as db:
            user_row = await db.fetchone(
                "SELECT integral, total_recruit_count, sr_guarantee_count, ssr_guarantee_count FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row:
                return RecruitResult(success=False, error="用户不存在")
            
            current_integral = user_row["integral"] or 0
            if current_integral < cost:
                return RecruitResult(success=False, error=f"积分不足，需要 {cost} 积分")
            
            sr_count = user_row["sr_guarantee_count"] or 0
            ssr_count = user_row["ssr_guarantee_count"] or 0
            total_count = user_row["total_recruit_count"] or 0
            
            rarity = self._determine_rarity(probability, sr_count, ssr_count)
            
            guarantee_triggered = None
            if sr_count >= 9 and rarity in ["SR", "SSR", "UR"]:
                guarantee_triggered = "sr_guarantee"
                sr_count = 0
            else:
                sr_count += 1
            
            if ssr_count >= 49 and rarity in ["SSR", "UR"]:
                guarantee_triggered = "ssr_guarantee"
                ssr_count = 0
            else:
                ssr_count += 1
            
            template = await self._get_random_template_by_rarity(db, rarity)
            if not template:
                return RecruitResult(success=False, error="没有可用的智能体模板")
            
            user_agent_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            await db.execute(
                """INSERT INTO user_agents 
                   (id, user_id, agent_id, name, department, level, salary, performance, status, skills, 
                    recruited_at, template_id, exp, current_skills, assigned_department, rarity)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
                user_agent_id,
                user_id,
                user_agent_id,
                template["name"],
                template["department"],
                1,
                template["base_salary"],
                100,
                "idle",
                template["skills"],
                now,
                template["id"],
                0,
                "{}",
                template["department"],
                template["rarity"],
            )
            
            await db.execute(
                """INSERT INTO recruit_logs 
                   (id, user_id, recruit_type, cost_integral, obtained_agent_id, obtained_rarity, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                str(uuid.uuid4()),
                user_id,
                recruit_type,
                cost,
                user_agent_id,
                rarity,
                now
            )
            
            await db.execute(
                """UPDATE users 
                   SET integral = integral - $1,
                       total_recruit_count = $2,
                       sr_guarantee_count = $3,
                       ssr_guarantee_count = $4
                   WHERE id = $5""",
                cost,
                total_count + 1,
                sr_count,
                ssr_count,
                user_id
            )
            
            await self._check_and_activate_bonds(db, user_id)
            
            logger.info(f"User {user_id} recruited {template['name']} ({rarity})")
            
            return RecruitResult(
                success=True,
                user_agent_id=user_agent_id,
                template_id=template["id"],
                name=template["name"],
                rarity=template["rarity"],
                department=template["department"],
                skills=json.loads(template["skills"]) if isinstance(template["skills"], str) else template["skills"],
                cost=cost,
                is_new=True,
                guarantee_triggered=guarantee_triggered,
            )
    
    def _determine_rarity(
        self,
        probability: Dict[str, float],
        sr_count: int,
        ssr_count: int
    ) -> str:
        """确定稀有度（考虑保底）"""
        if sr_count >= 9:
            return random.choice(["SR", "SSR", "UR"])
        
        if ssr_count >= 49:
            return random.choice(["SSR", "UR"])
        
        roll = random.random()
        cumulative = 0
        
        for rarity, prob in probability.items():
            cumulative += prob
            if roll < cumulative:
                return rarity
        
        return "N"
    
    async def _get_random_template_by_rarity(self, db, rarity: str) -> Optional[Dict]:
        """根据稀有度随机获取模板"""
        templates = await db.fetch(
            "SELECT * FROM agent_templates WHERE rarity = $1 AND available = $2",
            rarity, True
        )
        
        if not templates:
            templates = await db.fetch(
                "SELECT * FROM agent_templates WHERE available = $1",
                True
            )
        
        if not templates:
            return None
        
        template = random.choice(templates)
        return dict(template)
    
    async def _check_and_activate_bonds(self, db, user_id: str):
        """检查并激活羁绊"""
        user_agent_ids = await db.fetch(
            "SELECT template_id FROM user_agents WHERE user_id = $1",
            user_id
        )
        
        user_template_ids = [row["template_id"] for row in user_agent_ids]
        
        bonds = await db.fetch("SELECT * FROM bonds")
        
        for bond in bonds:
            required = json.loads(bond["required_agents"]) if isinstance(bond["required_agents"], str) else bond["required_agents"]
            
            if all(tid in user_template_ids for tid in required):
                existing = await db.fetchone(
                    "SELECT id FROM user_bonds WHERE user_id = $1 AND bond_id = $2",
                    user_id, bond["id"]
                )
                
                if not existing:
                    await db.execute(
                        """INSERT INTO user_bonds (id, user_id, bond_id, activated_at)
                           VALUES ($1, $2, $3, $4)""",
                        str(uuid.uuid4()),
                        user_id,
                        bond["id"],
                        datetime.utcnow()
                    )
                    logger.info(f"Activated bond {bond['name']} for user {user_id}")
    
    async def get_user_agents(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有智能体"""
        async with get_db() as db:
            rows = await db.fetch(
                """SELECT ua.*, at.name, at.department, at.skills, at.stats, at.description
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.user_id = $1
                   ORDER BY ua.recruited_at DESC""",
                user_id
            )
            
            agents = []
            for row in rows:
                agents.append({
                    "id": row["id"],
                    "template_id": row["template_id"],
                    "name": row["name"],
                    "rarity": row["rarity"],
                    "department": row["department"],
                    "level": row["level"],
                    "exp": row["exp"],
                    "current_skills": json.loads(row["current_skills"]) if isinstance(row["current_skills"], str) else row["current_skills"],
                    "skills": json.loads(row["skills"]) if isinstance(row["skills"], str) else row["skills"],
                    "stats": json.loads(row["stats"]) if isinstance(row["stats"], str) else row["stats"],
                    "assigned_department": row["assigned_department"],
                    "status": row["status"],
                    "recruited_at": row["recruited_at"].isoformat() if row["recruited_at"] else None,
                    "description": row["description"],
                    "level_cap": self.RARITY_LEVEL_CAP.get(row["rarity"], 30),
                    "rarity_color": self.RARITY_COLORS.get(row["rarity"], "#9e9e9e"),
                })
            
            return agents
    
    async def get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有智能体模板"""
        async with get_db() as db:
            rows = await db.fetch(
                "SELECT * FROM agent_templates WHERE available = $1 ORDER BY rarity, name",
                True
            )
            
            templates = []
            for row in rows:
                templates.append({
                    "id": row["id"],
                    "name": row["name"],
                    "rarity": row["rarity"],
                    "department": row["department"],
                    "base_salary": row["base_salary"],
                    "recruit_cost": row["recruit_cost"],
                    "skills": json.loads(row["skills"]) if isinstance(row["skills"], str) else row["skills"],
                    "stats": json.loads(row["stats"]) if isinstance(row["stats"], str) else row["stats"],
                    "description": row["description"],
                    "level_cap": self.RARITY_LEVEL_CAP.get(row["rarity"], 30),
                    "rarity_color": self.RARITY_COLORS.get(row["rarity"], "#9e9e9e"),
                })
            
            return templates
    
    async def get_user_bonds(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户已激活的羁绊"""
        async with get_db() as db:
            rows = await db.fetch(
                """SELECT b.*, ub.activated_at
                   FROM user_bonds ub
                   JOIN bonds b ON ub.bond_id = b.id
                   WHERE ub.user_id = $1
                   ORDER BY ub.activated_at DESC""",
                user_id
            )
            
            bonds = []
            for row in rows:
                bonds.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "required_agents": json.loads(row["required_agents"]) if isinstance(row["required_agents"], str) else row["required_agents"],
                    "effect": row["effect"],
                    "bonus": json.loads(row["bonus"]) if isinstance(row["bonus"], str) else row["bonus"],
                    "activated_at": row["activated_at"].isoformat() if row["activated_at"] else None,
                })
            
            return bonds
    
    async def get_recruit_stats(self, user_id: str) -> RecruitStats:
        """获取用户招募统计"""
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT total_recruit_count, sr_guarantee_count, ssr_guarantee_count FROM users WHERE id = $1",
                user_id
            )
            
            if not row:
                return RecruitStats(
                    total_recruits=0,
                    sr_guarantee_count=0,
                    ssr_guarantee_count=0,
                )
            
            return RecruitStats(
                total_recruits=row["total_recruit_count"] or 0,
                sr_guarantee_count=row["sr_guarantee_count"] or 0,
                ssr_guarantee_count=row["ssr_guarantee_count"] or 0,
            )
    
    async def get_agent_detail(self, user_id: str, user_agent_id: str) -> Optional[Dict[str, Any]]:
        """获取单个智能体详情"""
        async with get_db() as db:
            row = await db.fetchone(
                """SELECT ua.*, at.name, at.department, at.skills, at.stats, at.description, at.base_salary
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.id = $1 AND ua.user_id = $2""",
                user_agent_id, user_id
            )
            
            if not row:
                return None
            
            rarity = row["rarity"]
            level_cap = self.RARITY_LEVEL_CAP.get(rarity, 30)
            current_skills = json.loads(row["current_skills"]) if isinstance(row["current_skills"], str) else row["current_skills"]
            template_skills = json.loads(row["skills"]) if isinstance(row["skills"], str) else row["skills"]
            
            unlocked_skills = []
            for i, skill in enumerate(template_skills):
                skill_slot = i + 1
                unlock_level = self.SKILL_UNLOCK_LEVELS.get(skill_slot, 999)
                skill_info = {
                    "slot": skill_slot,
                    "name": skill.get("name", f"技能{skill_slot}"),
                    "description": skill.get("description", ""),
                    "effect": skill.get("effect", {}),
                    "unlock_level": unlock_level,
                    "unlocked": row["level"] >= unlock_level,
                    "level": current_skills.get(f"skill_{skill_slot}", 1) if row["level"] >= unlock_level else 0,
                }
                unlocked_skills.append(skill_info)
            
            return {
                "id": row["id"],
                "template_id": row["template_id"],
                "name": row["name"],
                "rarity": rarity,
                "rarity_color": self.RARITY_COLORS.get(rarity, "#9e9e9e"),
                "department": row["department"],
                "level": row["level"],
                "exp": row["exp"],
                "level_cap": level_cap,
                "can_upgrade": row["level"] < level_cap,
                "upgrade_cost": row["level"] * 10 if row["level"] < level_cap else 0,
                "skills": unlocked_skills,
                "stats": json.loads(row["stats"]) if isinstance(row["stats"], str) else row["stats"],
                "base_salary": row["base_salary"],
                "current_salary": int(row["base_salary"] * (1 + row["level"] * 0.05)),
                "assigned_department": row["assigned_department"],
                "status": row["status"],
                "recruited_at": row["recruited_at"].isoformat() if row["recruited_at"] else None,
                "description": row["description"],
                "can_breakthrough": rarity != "UR" and row["level"] >= level_cap,
                "breakthrough_cost": self.BREAKTHROUGH_COST.get(rarity, {}),
                "next_rarity": self._get_next_rarity(rarity),
            }
    
    def _get_next_rarity(self, current_rarity: str) -> Optional[str]:
        """获取下一级稀有度"""
        try:
            idx = self.RARITY_ORDER.index(current_rarity)
            if idx < len(self.RARITY_ORDER) - 1:
                return self.RARITY_ORDER[idx + 1]
        except ValueError:
            pass
        return None
    
    async def upgrade_agent(self, user_id: str, user_agent_id: str) -> Dict[str, Any]:
        """升级智能体"""
        async with get_db() as db:
            agent = await db.fetchone(
                """SELECT ua.*, at.name, at.base_salary
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.id = $1 AND ua.user_id = $2""",
                user_agent_id, user_id
            )
            
            if not agent:
                return {"success": False, "error": "智能体不存在"}
            
            rarity = agent["rarity"]
            level_cap = self.RARITY_LEVEL_CAP.get(rarity, 30)
            
            if agent["level"] >= level_cap:
                return {"success": False, "error": "已达到等级上限，请先突破"}
            
            upgrade_cost = agent["level"] * 10
            
            user = await db.fetchone("SELECT integral FROM users WHERE id = $1", user_id)
            if not user or (user["integral"] or 0) < upgrade_cost:
                return {"success": False, "error": f"积分不足，需要 {upgrade_cost} 积分"}
            
            new_level = agent["level"] + 1
            
            await db.execute(
                "UPDATE user_agents SET level = $1 WHERE id = $2",
                new_level, user_agent_id
            )
            
            await db.execute(
                "UPDATE users SET integral = integral - $1 WHERE id = $2",
                upgrade_cost, user_id
            )
            
            new_salary = int(agent["base_salary"] * (1 + new_level * 0.05))
            
            return {
                "success": True,
                "old_level": agent["level"],
                "new_level": new_level,
                "cost": upgrade_cost,
                "new_salary": new_salary,
                "message": f"{agent['name']} 升级到 {new_level} 级",
            }
    
    async def learn_skill(
        self, 
        user_id: str, 
        user_agent_id: str, 
        skill_slot: int
    ) -> Dict[str, Any]:
        """学习/升级技能"""
        async with get_db() as db:
            agent = await db.fetchone(
                """SELECT ua.*, at.name, at.skills
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.id = $1 AND ua.user_id = $2""",
                user_agent_id, user_id
            )
            
            if not agent:
                return {"success": False, "error": "智能体不存在"}
            
            template_skills = json.loads(agent["skills"]) if isinstance(agent["skills"], str) else agent["skills"]
            
            if skill_slot < 1 or skill_slot > len(template_skills):
                return {"success": False, "error": "无效的技能槽位"}
            
            unlock_level = self.SKILL_UNLOCK_LEVELS.get(skill_slot, 999)
            if agent["level"] < unlock_level:
                return {"success": False, "error": f"需要达到 {unlock_level} 级才能学习此技能"}
            
            current_skills = json.loads(agent["current_skills"]) if isinstance(agent["current_skills"], str) else agent["current_skills"]
            current_skill_level = current_skills.get(f"skill_{skill_slot}", 0)
            
            if current_skill_level >= 10:
                return {"success": False, "error": "技能已达到最高等级"}
            
            skill_cost = (current_skill_level + 1) * 100
            
            user = await db.fetchone("SELECT integral FROM users WHERE id = $1", user_id)
            if not user or (user["integral"] or 0) < skill_cost:
                return {"success": False, "error": f"积分不足，需要 {skill_cost} 积分"}
            
            current_skills[f"skill_{skill_slot}"] = current_skill_level + 1
            
            await db.execute(
                "UPDATE user_agents SET current_skills = $1 WHERE id = $2",
                json.dumps(current_skills), user_agent_id
            )
            
            await db.execute(
                "UPDATE users SET integral = integral - $1 WHERE id = $2",
                skill_cost, user_id
            )
            
            skill_name = template_skills[skill_slot - 1].get("name", f"技能{skill_slot}")
            
            return {
                "success": True,
                "skill_slot": skill_slot,
                "skill_name": skill_name,
                "old_level": current_skill_level,
                "new_level": current_skill_level + 1,
                "cost": skill_cost,
                "message": f"{agent['name']} 的 {skill_name} 升级到 {current_skill_level + 1} 级",
            }
    
    async def breakthrough(self, user_id: str, user_agent_id: str) -> Dict[str, Any]:
        """突破稀有度"""
        async with get_db() as db:
            agent = await db.fetchone(
                """SELECT ua.*, at.name
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.id = $1 AND ua.user_id = $2""",
                user_agent_id, user_id
            )
            
            if not agent:
                return {"success": False, "error": "智能体不存在"}
            
            rarity = agent["rarity"]
            
            if rarity == "UR":
                return {"success": False, "error": "已达最高稀有度，无法突破"}
            
            level_cap = self.RARITY_LEVEL_CAP.get(rarity, 30)
            if agent["level"] < level_cap:
                return {"success": False, "error": f"需要达到 {level_cap} 级才能突破"}
            
            breakthrough_info = self.BREAKTHROUGH_COST.get(rarity, {})
            required_integral = breakthrough_info.get("integral", 0)
            
            user = await db.fetchone("SELECT integral FROM users WHERE id = $1", user_id)
            if not user or (user["integral"] or 0) < required_integral:
                return {"success": False, "error": f"积分不足，需要 {required_integral} 积分"}
            
            next_rarity = self._get_next_rarity(rarity)
            if not next_rarity:
                return {"success": False, "error": "无法突破"}
            
            await db.execute(
                "UPDATE user_agents SET rarity = $1 WHERE id = $2",
                next_rarity, user_agent_id
            )
            
            await db.execute(
                "UPDATE users SET integral = integral - $1 WHERE id = $2",
                required_integral, user_id
            )
            
            new_level_cap = self.RARITY_LEVEL_CAP.get(next_rarity, 100)
            
            return {
                "success": True,
                "old_rarity": rarity,
                "new_rarity": next_rarity,
                "new_rarity_name": {"N": "普通", "R": "稀有", "SR": "史诗", "SSR": "传说", "UR": "神话"}.get(next_rarity, next_rarity),
                "new_level_cap": new_level_cap,
                "cost": required_integral,
                "message": f"{agent['name']} 突破成功！稀有度提升为 {next_rarity}",
            }
    
    async def get_all_bonds(self, user_id: str) -> List[Dict[str, Any]]:
        """获取所有羁绊（含激活状态）"""
        async with get_db() as db:
            user_template_ids = await db.fetch(
                "SELECT DISTINCT template_id FROM user_agents WHERE user_id = $1",
                user_id
            )
            owned_template_ids = {row["template_id"] for row in user_template_ids}
            
            bonds = await db.fetch("SELECT * FROM bonds ORDER BY name")
            
            result = []
            for bond in bonds:
                required = json.loads(bond["required_agents"]) if isinstance(bond["required_agents"], str) else bond["required_agents"]
                owned_count = sum(1 for tid in required if tid in owned_template_ids)
                is_activated = owned_count == len(required)
                
                result.append({
                    "id": bond["id"],
                    "name": bond["name"],
                    "description": bond["description"],
                    "required_agents": required,
                    "required_count": len(required),
                    "owned_count": owned_count,
                    "is_activated": is_activated,
                    "progress": f"{owned_count}/{len(required)}",
                    "effect": bond["effect"],
                    "bonus": json.loads(bond["bonus"]) if isinstance(bond["bonus"], str) else bond["bonus"],
                })
            
            return result


recruit_system = RecruitSystem()
