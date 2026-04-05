# -*- coding: utf-8 -*-
"""
Layer 41 - Cultivation Mechanism & Full Module Deep Fusion
============================================================
修仙机制与全模块深度融合层 — 10大模块+编排器+测试套件
礼部境界风格适配+修炼任务引擎+功能境界门控+分析经验奖励+市场境界门禁
+智能体修为共鸣+团队境界体系+积分兑换+合规隐私融合+能力随境界缩放+统一编排器
"""
from __future__ import annotations
import os, sys, time, uuid, hashlib, json, re, ast, textwrap, copy, threading, random, math, traceback
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# PART H — ENUMS & DATACLASSES
# ═══════════════════════════════════════════════════════════════

class RealmTier(PyEnum):
    LIANQI="lianqi"; ZHUJI="zhuji"; JINDAN="jindan"
    YUANYING="yuanying"; HUASHEN="huashen"; DACHENG="dacheng"

class StyleComplexity(PyEnum):
    SIMPLE="simple"; NORMAL="normal"; PROFESSIONAL="professional"; EXPERT="expert"

class FeatureUnlockStatus(PyEnum):
    LOCKED="locked"; AVAILABLE="available"; UNLOCKED="unlocked"

class PrivacyVisibility(PyEnum): PUBLIC="public"; FRIENDS_ONLY="friends_only"; PRIVATE="private"

@dataclass
class RealmProfile:
    user_id: str; realm: RealmTier; exp: int; level: int
    total_exp_earned: int; streak_days: int; last_login: float
    unlocked_features: List[str]=field(default_factory=list)
    style_complexity: StyleComplexity=StyleComplexity.NORMAL

@dataclass
class CultivationTask:
    task_id: str; name: str; description: str; category: str
    target_count: int; current_progress: int; exp_reward: int
    realm_requirement: Optional[RealmTier]
    status: str="active"; created_at: float=field(default_factory=time.time)
    completed_at: Optional[float]=None

@dataclass
class StyleAdaptationResult:
    original_text: str; adapted_text: str; realm: RealmTier
    complexity: StyleComplexity; terminology_level: float
    encouragement_added: bool; greeting_adjusted: bool

@dataclass
class ExpTransaction:
    tx_id: str; user_id: str; amount: int; source: str
    reason: str; timestamp: float=field(default_factory=time.time)
    balance_after: int=0

@dataclass
class TeamRealmData:
    team_id: str; team_realm: RealmTier; avg_member_realm_value: float
    member_count: int; skill_points: int; total_exp_contributed: int
    realm_bonus_active: bool=False

@dataclass
class ComplianceEvent:
    event_id: str; user_id: str; event_type: str; severity: str
    description: str; penalty_exp: int=0; is_violation: bool=False
    timestamp: float=field(default_factory=time.time); resolved: bool=False


# ═══════════════════════════════════════════════════════════════
# PART A — REALM STYLE ADAPTER (礼部境界风格适配器)
# ═══════════════════════════════════════════════════════════════

class RealmStyleAdapter:
    def __init__(self):
        self._realm_styles={
            RealmTier.LIANQI: {"complexity":StyleComplexity.SIMPLE,"terminology":0.2,
                "encourage":"加油！","greeting":"你好呀~","avoid_terms":["夏普比率","最大回撤","VaR"],
                "sentence_max":15,"use_emoji":True},
            RealmTier.ZHUJI: {"complexity":StyleComplexity.NORMAL,"terminology":0.4,
                "encourage":"做得不错！","greeting":"您好，有什么可以帮您？",
                "avoid_terms":["条件风险价值","GARCH模型","蒙特卡洛模拟"],
                "sentence_max":25,"use_emoji":False},
            RealmTier.JINDAN: {"complexity":StyleComplexity.PROFESSIONAL,"terminology":0.6,
                "encourage":"分析到位。","greeting":"您好，请说明需求。",
                "avoid_terms":[],"sentence_max":40,"use_emoji":False},
            RealmTier.YUANYING: {"complexity":StyleComplexity.EXPERT,"terminology":0.8,
                "encourage":"","greeting":"",
                "avoid_terms":[],"sentence_max":None,"use_emoji":False},
            RealmTier.HUASHEN: {"complexity":StyleComplexity.EXPERT,"terminology":1.0,
                "encourage":"","greeting":"",
                "avoid_terms":[],"sentence_max":None,"use_emoji":False}}
        self._breakthrough_messages={
            (RealmTier.LIANQI,RealmTier.ZHUJI):"恭喜突破筑基期！已解锁：量化分析摘要功能",
            (RealmTier.ZHUJI,RealmTier.JINDAN):"恭喜突破金丹期！已解锁：完整量化报告、多板块对比分析",
            (RealmTier.JINDAN,RealmTier.YUANYING):"恭喜突破元婴期！已解锁：自定义因子、情景模拟、压力测试",
            (RealmTier.YUANYING,RealmTier.HUASHEN):"恭喜突破化神期！已解锁：网络访问权限、高级API接口"}

    def adapt_response(self, response_text: str, realm: RealmTier,
                        previous_realm: Optional[RealmTier]=None) -> StyleAdaptationResult:
        style=self._realm_styles.get(realm,self._realm_styles[RealmTier.ZHUJI])
        adapted=response_text
        if previous_realm and previous_realm!=realm:
            msg=self._breakthrough_messages.get((previous_realm,realm))
            if msg: adapted=f"[系统提示] {msg}\n\n{adapted}"
        if style["avoid_terms"]:
            for term in style["avoid_terms"]:
                adapted=re.sub(term,"[专业术语]",adapted)
        if style["use_emoji"] and not any(c in adapted for c in ["🏠","💰","📊"]):
            adapted="🏠 "+adapted
        return StyleAdaptationResult(response_text,adapted,realm,
            style["complexity"],style["terminology"],
            bool(style["encourage"]),bool(style["greeting"]))

    def get_realm_greeting(self, realm: RealmTier) -> str:
        return self._realm_styles.get(realm,{}).get("greeting","您好")

    def should_unlock_feature(self, feature: str, new_realm: RealmTier) -> bool:
        feature_gates={"quant_summary":RealmTier.ZHUJI,"full_report":RealmTier.JINDAN,
            "multi_panel_compare":RealmTier.YUANYING,"custom_factors":RealmTier.JINDAN,
            "scenario_sim":RealmTier.YUANYING,"stress_test":RealmTier.YUANYING}
        required=feature_gates.get(feature)
        if not required: return True
        realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        return realm_order.index(new_realm)>=realm_order.index(required)


# ═══════════════════════════════════════════════════════════════
# PART B — CULTIVATION TASK ENGINE (修炼任务引擎)
# ═══════════════════════════════════════════════════════════════

class CultivationTaskEngine:
    def __init__(self):
        self._task_templates=[
            CultivationTask("ct_001","每日问答","完成3次智能咨询提问","daily",3,0,10,None),
            CultivationTask("ct_002","量化入门","连续使用量化分析5天","weekly",5,0,50,RealmTier.ZHUJI),
            CultivationTask("ct_003","报告大师","生成10份房产分析报告","milestone",10,0,30,RealmTier.ZHUJI),
            CultivationTask("ct_004","对比专家","生成5份多板块对比报告","milestone",5,0,30,RealmTier.JINDAN),
            CultivationTask("ct_005","深度分析","使用高级功能(政策影响/因子)20次","milestone",20,0,20,RealmTier.JINDAN)]
        self._user_tasks: Dict[str,List[CultivationTask]] = defaultdict(list)
        self._exp_history: Dict[str,List[ExpTransaction]] = defaultdict(list)
        self._streak_tracker: Dict[str,Dict[str,Any]] = {}

    def generate_tasks_for_user(self, user_id: str, realm: RealmTier) -> List[CultivationTask]:
        eligible=[t for t in self._task_templates
                   if t.realm_requirement is None or self._is_realm_sufficient(realm,t.realm_requirement)]
        active=self._user_tasks.get(user_id,[])
        active_ids={t.task_id for t in active if t.status=="active"}
        new_tasks=[]
        for t in eligible:
            if t.task_id not in active_ids:
                nt=CultivationTask(f"{t.task_id}_{uuid.uuid4().hex[:6]}",t.name,t.description,
                    t.category,t.target_count,0,t.exp_reward,t.realm_requirement)
                new_tasks.append(nt); self._user_tasks[user_id].append(nt)
        return new_tasks

    def record_action(self, user_id: str, action_type: str, count: int=1) -> ExpTransaction:
        exp_map={"consult_asked":2,"analysis_report_simple":10,"analysis_report_complex":30,
            "advanced_feature_used":20,"code_exec_success":5,"code_shared":20,"review_helpful":3}
        base_exp=exp_map.get(action_type,1)*count
        tid=f"tx_{uuid.uuid4().hex[:12]}"
        tx=ExpTransaction(tid,user_id,base_exp,action_type,f"Action: {action_type} x{count}")
        current_total=sum(t.amount for t in self._exp_history[user_id])
        tx.balance_after=current_total+base_exp
        self._exp_history[user_id].append(tx)
        for task in self._user_tasks.get(user_id,[]):
            if task.status=="active" and action_type in task.description.lower():
                task.current_progress=min(task.current_progress+count,task.target_count*2)
                if task.current_progress>=task.target_count:
                    task.status="completed"; task.completed_at=time.time()
                    bonus_tx=ExpTransaction(f"tx_{uuid.uuid4().hex[:12]}",user_id,task.exp_reward,
                        f"task_complete:{task.task_id}",f"完成任务: {task.name}")
                    current_total+=task.exp_reward; bonus_tx.balance_after=current_total
                    self._exp_history[user_id].append(bonus_tx)
        return tx

    def _is_realm_sufficient(self, user_realm: RealmTier, required: RealmTier) -> bool:
        order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        return order.index(user_realm)>=order.index(required)

    def get_user_exp_total(self, user_id: str) -> int:
        return sum(t.amount for t in self._exp_history.get(user_id,[]))

    def get_user_tasks(self, user_id: str, status_filter: Optional[str]=None) -> List[CultivationTask]:
        tasks=self._user_tasks.get(user_id,[])
        if status_filter: tasks=[t for t in tasks if t.status==status_filter]
        return tasks

    def engine_stats(self) -> Dict[str,Any]:
        total_users=len(self._user_tasks); total_tasks=sum(len(v) for v in self._user_tasks.values())
        completed=sum(1 for ts in self._user_tasks.values() for t in ts if t.status=="completed")
        return {"users_with_tasks":total_users,"total_task_instances":total_tasks,
            "completed":completed,"templates":len(self._task_templates)}


# ═══════════════════════════════════════════════════════════════
# PART C — REALM FEATURE GATE (功能境界门控)
# ═══════════════════════════════════════════════════════════════

class RealmFeatureGate:
    def __init__(self):
        self._feature_registry={
            "basic_qa":{"min_realm":RealmTier.LIANQI,"description":"基础房产问答"},
            "quant_summary":{"min_realm":RealmTier.ZHUJI,"description":"量化分析摘要"},
            "full_report":{"min_realm":RealmTier.JINDAN,"description":"完整量化报告"},
            "multi_panel_compare":{"min_realm":RealmTier.YUANYING,"description":"多板块对比分析"},
            "custom_indicators":{"min_realm":RealmTier.ZHUJI,"description":"自定义指标"},
            "quant_prediction":{"min_realm":RealmTier.JINDAN,"description":"量化预测模型"},
            "scenario_simulation":{"min_realm":RealmTier.YUANYING,"description":"情景模拟"},
            "stress_test":{"min_realm":RealmTier.YUANYING,"description":"压力测试"},
            "network_access":{"min_realm":RealmTier.HUASHEN,"description":"网络访问权限"},
            "advanced_api":{"min_realm":RealmTier.HUASHEN,"description":"高级API接口"}}
        self._unlock_log: List[Dict[str,Any]] = []

    def check_access(self, user_id: str, feature: str, realm: RealmTier) -> Tuple[bool,str,Optional[RealmTier]]:
        reg=self._feature_registry.get(feature)
        if not reg: return True,"Feature unknown, allowed by default",None
        min_realm=reg["min_realm"]
        realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        if realm_order.index(realm)>=realm_order.index(min_realm):
            return True,f"Access granted: {reg['description']}",None
        return False,f"需要突破至{self._realm_name_zh(min_realm)}期可解锁此功能: {reg['description']}",min_realm

    def list_unlocked_features(self, realm: RealmTier) -> List[Dict[str,Any]]:
        unlocked=[]
        for fid,reg in self._feature_registry.items():
            realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
            if realm_order.index(realm)>=realm_order.index(reg["min_realm"]):
                unlocked.append({"feature_id":fid,**reg})
        return unlocked

    def list_locked_features(self, realm: RealmTier) -> List[Dict[str,Any]]:
        locked=[]
        for fid,reg in self._feature_registry.items():
            realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
            if realm_order.index(realm)<realm_order.index(reg["min_realm"]):
                locked.append({"feature_id":fid,**reg,"required_realm":self._realm_name_zh(reg["min_realm"])})
        return locked

    def _realm_name_zh(self, r: RealmTier) -> str:
        return {RealmTier.LIANQI:"炼气",RealmTier.ZHUJI:"筑基",RealmTier.JINDAN:"金丹",
            RealmTier.YUANYING:"元婴",RealmTier.HUASHEN:"化神"}.get(r,r.value)

    def gate_stats(self) -> Dict[str,Any]:
        return {"total_features":len(self._feature_registry),"unlock_logs":len(self._unlock_log)}


# ═══════════════════════════════════════════════════════════════
# PART D — ANALYSIS EXP REWARD (分析经验值奖励)
# ═══════════════════════════════════════════════════════════════

class AnalysisExpReward:
    def __init__(self):
        self._reward_rules={"single_panel_report":10,"multi_panel_report":30,
            "policy_impact_analysis":20,"deep_dive":15,"comparison_report":25}
        self._reward_history: List[Dict[str,Any]] = []
        self._daily_limits: Dict[str,Dict[str,Any]] = {}
        self._DAILY_CAP=200

    def calculate_reward(self, report_type: str, complexity: str="normal",
                          user_id: str="", used_advanced: bool=False) -> Dict[str,Any]:
        base=self._reward_rules.get(report_type,5)
        mult={"simple":1.0,"normal":1.0,"advanced":1.5}.get(complexity,1.0)
        bonus=20 if used_advanced else 0
        total=int(base*mult)+bonus
        today_key=time.strftime("%Y-%m-%d")
        if user_id:
            daily=self._daily_limits.setdefault(user_id,{"date":today_key,"spent":0})
            if daily["date"]!=today_key: daily={"date":today_key,"spent":0}
            remaining=max(0,self._DAILY_CAP-daily["spent"])
            actual=min(total,remaining); daily["spent"]+=actual
        else: actual=total
        entry={"reward_id":uuid.uuid4().hex[:10],"user_id":user_id or "anonymous",
            "report_type":report_type,"base_exp":base,"multiplier":mult,
            "bonus":bonus,"total_actual":actual,"timestamp":time.time()}
        self._reward_history.append(entry)
        return {"exp_gained":actual,"base":base,"multiplier":mult,"bonus":bonus,
            "remaining_daily":max(0,self._DAILY_CAP-self._daily_limits.get(user_id,{}).get("spent",0)) if user_id else None}

    def get_progress_bar(self, user_id: str, current_realm_exp: int,
                           next_realm_exp: int) -> Dict[str,Any]:
        pct=min(100,current_realm_exp/max(next_realm_exp,1)*100)
        return {"current":current_realm_exp,"required":next_realm_exp,"percentage":round(pct,1),
            "remaining":max(0,next_realm_exp-current_realm_exp)}

    def reward_stats(self) -> Dict[str,Any]:
        return {"total_rewards":len(self._reward_history),"daily_cap":self._DAILY_CAP,
            "rules":len(self._reward_rules)}


# ═══════════════════════════════════════════════════════════════
# PART E — MARKET REALM GATE (市场境界门禁)
# ═══════════════════════════════════════════════════════════════

class MarketRealmGate:
    def __init__(self):
        self._agent_requirements={
            "量化分析师":{"min_realm":RealmTier.JINDAN,"price_points":500,"desc":"金丹期智能体"},
            "政策研究员":{"min_realm":RealmTier.YUANYING,"price_points":1000,"desc":"元婴期智能体"},
            "策略回测师":{"min_realm":RealmTier.YUANYING,"price_points":800,"desc":"元婴期智能体"},
            "数据架构师":{"min_realm":RealmTier.HUASHEN,"price_points":2000,"desc":"化神期智能体"}}
        self._skill_tiers={
            "基础数据清洗":{"tier":1,"min_realm":RealmTier.LIANQI,"price":50},
            "板块对比分析":{"tier":2,"min_realm":RealmTier.ZHUJI,"price":150},
            "多因子预测":{"tier":3,"min_realm":RealmTier.JINDAN,"price":400},
            "策略回测优化":{"tier":4,"min_realm":RealmTier.YUANYING,"price":800}}

    def can_recruit_agent(self, agent_name: str, user_realm: RealmTier,
                            user_points: int) -> Tuple[bool,str]:
        req=self._agent_requirements.get(agent_name)
        if not req: return True,"无境界限制",None
        realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        realm_ok=realm_order.index(user_realm)>=realm_order.index(req["min_realm"])
        points_ok=user_points>=req["price_points"]
        if realm_ok and points_ok: return True,"招募成功",None
        reasons=[]
        if not realm_ok: reasons.append(f"需{req['min_realm'].value}期")
        if not points_ok: reasons.append(f"需{req['price_points']}积分")
        return False,"; ".join(reasons),req["min_realm"]

    def can_buy_skill(self, skill_name: str, user_realm: RealmTier,
                       user_points: int) -> Tuple[bool,str]:
        skill=self._skill_tiers.get(skill_name)
        if not skill: return True,"无限制",None
        realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        realm_ok=realm_order.index(user_realm)>=realm_order.index(skill["min_realm"])
        points_ok=user_points>=skill["price"]
        if realm_ok and points_ok: return True,"购买成功",None
        reasons=[]
        if not realm_ok: reasons.append(f"需{skill['min_realm'].value}期解锁")
        if not points_ok: reasons.append(f"需{skill['price']}积分")
        return False,"; ".join(reasons),None

    def market_stats(self) -> Dict[str,Any]:
        return {"agents":len(self._agent_requirements),"skills":len(self._skill_tiers)}


# ═══════════════════════════════════════════════════════════════
# PART F — AGENT RESONANCE (智能体修为共鸣)
# ═══════════════════════════════════════════════════════════════

class AgentResonance:
    def __init__(self):
        self._resonance_events: List[Dict[str,Any]] = []
        self._agent_levels: Dict[str,int] = {}  # agent_id -> level (1-10)
        self._resonance_multipliers = {1:0.5,2:0.75,3:1.0,4:1.25,5:1.5,
            6:1.75,7:2.0,8:2.5,9:3.0,10:5.0}

    def on_agent_upgrade(self, agent_id: str, agent_name: str, old_level: int,
                         new_level: int, owner_id: str) -> Dict[str,Any]:
        base_exp=50*(new_level-old_level)
        milestone_bonus=200 if new_level>=5 else 0
        total_exp=base_exp+milestone_bonus
        multiplier=self._resonance_multipliers.get(new_level,1.0)
        final_exp=int(total_exp*multiplier)
        event={"event_id":uuid.uuid4().hex[:10],"agent_id":agent_id,"agent_name":agent_name,
            "old_level":old_level,"new_level":new_level,"owner_id":owner_id,
            "base_exp":base_exp,"milestone_bonus":milestone_bonus,
            "multiplier":multiplier,"final_exp":final_exp,"timestamp":time.time(),
            "triggered_resonance":new_level in(5,8,10)}
        self._resonance_events.append(event)
        self._agent_levels[agent_id]=new_level
        return event

    def get_resonance_history(self, owner_id: str, limit: int=20) -> List[Dict[str,Any]]:
        return [e for e in self._resonance_events[-limit:] if e["owner_id"]==owner_id]

    def resonance_stats(self) -> Dict[str,Any]:
        resonances=sum(1 for e in self._resonance_events if e.get("triggered_resonance"))
        total_exp=sum(e["final_exp"] for e in self._resonance_events)
        return {"total_events":len(self._resonance_events),"resonances_triggered":resonances,
            "total_exp_granted":total_exp,"tracked_agents":len(self._agent_levels)}


# ═══════════════════════════════════════════════════════════════
# PART G — TEAM REALM SYSTEM (团队境界体系)
# ═══════════════════════════════════════════════════════════════

class TeamRealmSystem:
    def __init__(self):
        self._teams: Dict[str,TeamRealmData] = {}
        self._team_skills: Dict[str,List[Dict[str,Any]]] = {}
        self._team_tasks: List[Dict[str,Any]] = []
        self._realm_thresholds={RealmTier.LIANQI:0,RealmTier.ZHUJI:15,
            RealmTier.JINDAN:35,RealmTier.YUANYING:60,RealmTier.HUASHEN:85}

    def create_or_update_team(self, team_id: str, members: List[Dict[str,Any]]) -> TeamRealmData:
        realm_values=[]; total_exp=0
        for m in members:
            rv=list(self._realm_thresholds.values())
            ri=rv.index(m.get("realm_value",0)) if m.get("realm_value",0) in rv else 0
            realm_values.append(ri); total_exp+=m.get("exp",0)
        avg_rv=sum(realm_values)/max(len(realm_values),1)
        realm_list=list(self._realm_thresholds.keys())
        team_realm=realm_list[min(int(avg_rv),len(realm_list)-1)] if avg_rv< len(realm_list) else realm_list[-1]
        sp=int(avg_rv)*2
        data=TeamRealmData(team_id,team_realm,avg_rv,len(members),sp,total_exp)
        self._teams[team_id]=data
        return data

    def add_team_skill(self, team_id: str, skill_name: str, effect: str,
                       cost_sp: int, requires_realm: RealmTier) -> bool:
        team=self._teams.get(team_id)
        if not team: return False
        realm_order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        if realm_order.index(team.team_realm)<realm_order.index(requires_realm): return False
        if team.skill_points<cost_sp: return False
        skills=self._team_skills.setdefault(team_id,[])
        skills.append({"name":skill_name,"effect":effect,"cost":cost_sp,"active":True})
        team.skill_points-=cost_sp
        return True

    def create_team_cultivation_task(self, team_id: str, name: str, target: str,
                                      exp_per_member: int) -> Dict[str,Any]:
        task={"task_id":uuid.uuid4().hex[:8],"team_id":team_id,"name":name,
            "target":target,"progress":0,"exp_per_member":exp_per_member,
            "status":"active","created_at":time.time()}
        self._team_tasks.append(task); return task

    def complete_team_task(self, task_id: str, contributing_members: List[str]) -> Dict[str,Any]:
        task=None
        for t in self._team_tasks:
            if t["task_id"]==task_id: task=t; break
        if not task: return {"error":"Task not found"}
        task["status"]="completed"; task["completed_at"]=time.time()
        return {"task_id":task_id,"exp_granted":task["exp_per_member"],"members":contributing_members}

    def team_stats(self, team_id: str) -> Optional[Dict[str,Any]]:
        team=self._teams.get(team_id)
        if not team: return None
        skills=self._team_skills.get(team_id,[])
        active_tasks=sum(1 for t in self._team_tasks if t["team_id"]==team_id and t["status"]=="active")
        return {"realm":team.team_realm.value,"avg_realm_value":round(team.avg_member_realm_value,1),
            "members":team.member_count,"skill_points":team.skill_points,
            "skills":len(skills),"active_tasks":active_tasks}


# ═══════════════════════════════════════════════════════════════
# PART H — POINTS EXCHANGE (积分兑换系统)
# ═══════════════════════════════════════════════════════════════

class PointsExchange:
    def __init__(self):
        self._exchange_rate=100  # 100 points = 10 exp
        self._daily_exp_cap=500
        self._breakthrough_rewards={RealmTier.ZHUJI:500,RealmTier.JINDAN:1000,
            RealmTier.YUANYING:2000,RealmTier.HUASHEN:5000}
        self._exchange_log: List[Dict[str,Any]] = []
        self._daily_spent: Dict[str,Dict[str,int]] = {}

    def exchange_points_for_exp(self, user_id: str, points_to_exchange: int,
                                  current_points: int) -> Dict[str,Any]:
        today=time.strftime("%Y-%m-%d")
        daily=self._daily_spent.setdefault(user_id,{"date":today,"exp_granted":0})
        if daily["date"]!=today: daily={"date":today,"exp_granted":0}
        remaining=max(0,self._daily_exp_cap-daily["exp_granted"])
        exp_gained=int(points_to_exchange/self._exchange_rate*10)
        actual=min(exp_gained,remaining)
        if actual<=0: return {"success":False,"reason":"已达每日上限","exp_granted":0}
        daily["exp_granted"]+=actual
        entry={"exchange_id":uuid.uuid4().hex[:10],"user_id":user_id,
            "points_spent":points_to_exchange,"exp_gained":actual,"timestamp":time.time()}
        self._exchange_log.append(entry)
        return {"success":True,"points_spent":points_to_exchange,"exp_gained":actual,
            "remaining_today":max(0,self._daily_exp_cap-daily["exp_granted"])}

    def grant_breakthrough_reward(self, user_id: str, from_realm: RealmTier,
                                   to_realm: RealmTier) -> int:
        reward=self._breakthrough_rewards.get(to_realm,0)
        entry={"type":"breakthrough","user_id":user_id,"from":from_realm.value,
            "to":to_realm.value,"points_reward":reward,"timestamp":time.time()}
        self._exchange_log.append(entry)
        return reward

    def check_purchase_dual_req(self, user_id: str, item_points: int,
                                  item_realm: RealmTier, user_realm: RealmTier,
                                  user_points: int) -> Tuple[bool,str]:
        realm_ok=self._is_realm_ok(user_realm,item_realm)
        points_ok=user_points>=item_points
        if realm_ok and points_ok: return True,"购买成功"
        reasons=[]
        if not realm_ok: reasons.append(f"需{item_realm.value}期")
        if not points_ok: reasons.append(f"需{item_points}积分")
        return False,"; ".join(reasons)

    def _is_realm_ok(self, user: RealmTier, required: RealmTier) -> bool:
        order=[RealmTier.LIANQI,RealmTier.ZHUJI,RealmTier.JINDAN,RealmTier.YUANYING,RealmTier.HUASHEN]
        return order.index(user)>=order.index(required)

    def exchange_stats(self) -> Dict[str,Any]:
        return {"rate":f"{self._exchange_rate}pts→{self._exchange_rate//10}exp",
            "daily_cap":self._daily_exp_cap,"total_exchanges":len(self._exchange_log),
            "breakthrough_tiers":len(self._breakthrough_rewards)}


# ═══════════════════════════════════════════════════════════════
# PART I — COMPLIANCE PRIVACY FUSION (合规隐私融合)
# ═══════════════════════════════════════════════════════════════

class CompliancePrivacyFusion:
    def __init__(self):
        self._privacy_settings: Dict[str,Dict[str,Any]] = {}
        self._compliance_events: List[ComplianceEvent] = []
        self._anomaly_patterns=["short_time_many_reports","identical_queries_burst",
            "unusual_high_volume","suspicious_pattern_match"]
        self._exemption_requests: List[Dict[str,Any]] = []

    def set_privacy_visibility(self, user_id: str, visibility: PrivacyVisibility) -> Dict[str,Any]:
        old=self._privacy_settings.get(user_id,{}).get("visibility","private")
        self._privacy_settings.setdefault(user_id,{})["visibility"]=visibility
        return {"user_id":user_id,"old_visibility":old,"new_visibility":visibility.value}

    def get_visibility(self, user_id: str, viewer_id: str) -> bool:
        settings=self._privacy_settings.get(user_id,{"visibility":PrivacyVisibility.PRIVATE})
        vis=settings["visibility"]
        if vis==PrivacyVisibility.PUBLIC: return True
        if vis==PrivacyVisibility.FRIENDS_ONLY:
            friends=settings.get("friends",[])
            return viewer_id in friends
        return viewer_id==user_id

    def audit_behavior(self, user_id: str, behavior_data: Dict[str,Any]) -> ComplianceEvent:
        risk_score=0; violations=[]
        if behavior_data.get("reports_per_minute",0)>10:
            risk_score+=40; violations.append("高频报告生成异常")
        if behavior_data.get("identical_queries",0)>5:
            risk_score+=30; violations.append("重复查询异常")
        if behavior_data.get("night_activity",False) and behavior_data.get("volume",0)>50:
            risk_score+=20; violations.append("非常规时段大量操作")
        is_violation=risk_score>50
        penalty=-int(risk_score/10) if is_violation else 0
        event=ComplianceEvent(uuid.uuid4().hex[:10],user_id,"behavior_audit",
            "HIGH" if risk_score>50 else "MEDIUM" if risk_score>20 else "LOW",
            "; ".join(violations) if violations else "Normal",abs(penalty),is_violation)
        self._compliance_events.append(event)
        return event

    def request_privacy_exemption(self, user_id: str, realm: RealmTier) -> Dict[str,Any]:
        if realm!=RealmTier.HUASHEN:
            return {"approved":False,"reason":"仅化神期以上可申请隐私豁免"}
        req={"request_id":uuid.uuid4().hex[:8],"user_id":user_id,"status":"pending",
            "requested_at":time.time(),"approved_by":None}
        self._exemption_requests.append(req)
        return req

    def fusion_stats(self) -> Dict[str,Any]:
        violations=sum(1 for e in self._compliance_events if e.is_violation)
        return {"privacy_users":len(self._privacy_settings),
            "audit_events":len(self._compliance_events),"violations":violations,
            "exemption_requests":len(self._exemption_requests)}


# ═══════════════════════════════════════════════════════════════
# PART J — AGENT CAPABILITY SCALING (能力随境界缩放)
# ═══════════════════════════════════════════════════════════════

class AgentCapabilityScaling:
    def __init__(self):
        self._bingbu_scaling={RealmTier.LIANQI:{"risk_levels":1,"timeout":10},
            RealmTier.ZHUJI:{"risk_levels":2,"timeout":20},
            RealmTier.JINDAN:{"risk_levels":3,"timeout":30},
            RealmTier.YUANYING:{"risk_levels":4,"timeout":60},
            RealmTier.HUASHEN:{"risk_levels":5,"timeout":120}}
        self._hubu_scaling={RealmTier.LIANQI:{"concurrency":1,"cache_hit_bonus":0},
            RealmTier.ZHUJI:{"concurrency":1,"cache_hit_bonus":0.05},
            RealmTier.JINDAN:{"concurrency":2,"cache_hit_bonus":0.10},
            RealmTier.YUANYING:{"concurrency":5,"cache_hit_bonus":0.15},
            RealmTier.HUASHEN:{"concurrency":999,"cache_hit_bonus":0.25}}
        self._xingbu_tolerance={RealmTier.LIANQI:1.0,RealmTier.ZHUJI:0.95,
            RealmTier.JINDAN:0.85,RealmTier.YUANYING:0.70,RealmTier.HUASHEN:0.50}
        self._liscaling_memory={RealmTier.LIANQI:1000,RealmTier.ZHUJI:5000,
            RealmTier.JINDAN:20000,RealmTier.YUANYING:999999}

    def get_bingbu_config(self, realm: RealmTier) -> Dict[str,Any]:
        return self._bingbu_scaling.get(realm,self._bingbu_scaling[RealmTier.LIANQI])

    def get_hubu_config(self, realm: RealmTier) -> Dict[str,Any]:
        return self._hubu_scaling.get(realm,self._hubu_scaling[RealmTier.LIANQI])

    def get_xingbu_tolerance(self, realm: RealmTier) -> float:
        return self._xingbu_tolerance.get(realm,1.0)

    def get_liscaling_memory_limit(self, realm: RealmTier) -> int:
        return self._liscaling_memory.get(realm,1000)

    def scaling_stats(self) -> Dict[str,Any]:
        return {"bingbu_tiers":len(self._bingbu_scaling),"hubu_tiers":len(self._hubu_scaling),
            "xingbu_tiers":len(self._xingbu_tolerance),"li_tiers":len(self._liscaling_memory)}


# ═══════════════════════════════════════════════════════════════
# PART K — CULTIVATION DEEP ORCHESTRATOR (统一编排器)
# ═══════════════════════════════════════════════════════════════

class CultivationDeepOrchestrator:
    def __init__(self):
        self.style_adapter=RealmStyleAdapter()
        self.task_engine=CultivationTaskEngine()
        self.feature_gate=RealmFeatureGate()
        self.analysis_reward=AnalysisExpReward()
        self.market_gate=MarketRealmGate()
        self.agent_resonance=AgentResonance()
        self.team_system=TeamRealmSystem()
        self.points_exchange=PointsExchange()
        self.compliance_fusion=CompliancePrivacyFusion()
        self.capability_scaling=AgentCapabilityScaling()

    def process_consultation(self, user_input: str, user_id: str,
                                realm: RealmTier) -> Dict[str,Any]:
        access,msg,req=self.feature_gate.check_access(user_id,"basic_qa",realm)
        if not access: return {"error":msg,"requires_realm":req.value if req else None}
        adapted=self.style_adapter.adapt_response(user_input,realm)
        exp_tx=self.task_engine.record_action(user_id,"consult_asked")
        tasks=self.task_engine.generate_tasks_for_user(user_id,realm)
        pending=[t.name for t in tasks if t.status=="active"]
        total_exp=self.task_engine.get_user_exp_total(user_id)
        return {"adapted_input":adapted.adapted_text,"style":adapted.complexity.value,
            "exp_gained":exp_tx.amount,"total_exp":total_exp,
            "new_tasks":len(tasks),"pending_tasks":pending}

    def process_analysis(self, analysis_type: str, user_id: str, realm: RealmTier,
                          used_advanced: bool=False) -> Dict[str,Any]:
        feature_map={"single":"basic_qa","summary":"quant_summary",
            "full":"full_report","compare":"multi_panel_compare",
            "prediction":"quant_prediction","sim":"scenario_simulation",
            "stress":"stress_test"}
        feat=feature_map.get(analysis_type,"basic_qa")
        access,msg,req=self.feature_gate.check_access(user_id,feat,realm)
        if not access: return {"error":msg,"requires_realm":req.value if req else None}
        reward=self.analysis_reward.calculate_reward(
            {"single_panel_report":"single","multi_panel_report":"compare"}.get(analysis_type,"full_report"),
            "advanced" if used_advanced else "normal",user_id,used_advanced)
        exp_tx=self.task_engine.record_action(user_id,
            "analysis_report_complex" if used_advanced else "analysis_report_simple")
        progress=self.analysis_reward.get_progress_bar(user_id,
            self.task_engine.get_user_exp_total(user_id),1000)
        return {"reward":reward,"action_exp":exp_tx.amount,"progress":progress,
            "access_granted":True}

    def handle_agent_upgrade(self, agent_id: str, agent_name: str, old_lvl: int,
                              new_lvl: int, owner_id: str, owner_realm: RealmTier) -> Dict[str,Any]:
        event=self.agent_resonance.on_agent_upgrade(agent_id,agent_name,old_lvl,new_lvl,owner_id)
        base=event["final_exp"]
        if new_lvl>=5: base+=200
        exp_tx=ExpTransaction(uuid.uuid4().hex[:12],owner_id,base,
            f"agent_resonance:{agent_name}_L{new_lvl}",f"智能体共鸣+突破奖励")
        current=self.task_engine.get_user_exp_total(owner_id)
        exp_tx.balance_after=current+base
        self.task_engine._exp_history[owner_id].append(exp_tx)
        return {**event,"total_exp_granted":base,"new_balance":exp_tx.balance_after}

    def get_full_dashboard(self, user_id: str, realm: RealmTier) -> Dict[str,Any]:
        total_exp=self.task_engine.get_user_exp_total(user_id)
        unlocked=self.feature_gate.list_unlocked_features(realm)
        locked=self.feature_gate.list_locked_features(realm)
        tasks=self.task_engine.get_user_tasks(user_id)
        active_tasks=[t.name for t in tasks if t.status=="active"]
        completed_tasks=[t.name for t in tasks if t.status=="completed"]
        bingbu_cfg=self.capability_scaling.get_bingbu_config(realm)
        hubu_cfg=self.capability_scaling.get_hubu_config(realm)
        li_limit=self.capability_scaling.get_liscaling_memory_limit(realm)
        xing_tol=self.capability_scaling.get_xingbu_tolerance(realm)
        privacy_vis=self.compliance_fusion._privacy_settings.get(user_id,{}).get("visibility")
        privacy=privacy_vis.value if hasattr(privacy_vis,'value') else str(privacy_vis or "private")
        return {"user_id":user_id,"realm":realm.value,"total_exp":total_exp,
            "unlocked_features":len(unlocked),"locked_features":len(locked),
            "unlocked_list":[f["feature_id"] for f in unlocked],
            "locked_list":[{"id":f["feature_id"],"need":f.get("required_realm","?")} for f in locked],
            "active_tasks":active_tasks,"completed_tasks":len(completed_tasks),
            "bingbu_config":bingbu_cfg,"hubu_config":hubu_cfg,
            "memory_limit":li_limit,"xingbu_tolerance":xing_tol,
            "privacy_visibility":privacy}


# ═══════════════════════════════════════════════════════════════
# PART L — TESTING SUITE
# ═══════════════════════════════════════════════════════════════

def _run_test(name: str, fn) -> tuple:
    try: fn(); return ("PASS", name, None)
    except Exception as e: return ("FAIL", name, str(e))

def run_all_tests() -> Dict[str,Any]:
    results=[]

    def test_style_adapt():
        rsa=RealmStyleAdapter(); r=rsa.adapt_response("这是夏普比率和最大回撤分析",RealmTier.LIANQI)
        assert r.terminology_level<0.5; assert "[专业术语]" in r.adapted_text
    results.append(_run_test("STYLE: adapt low realm", test_style_adapt))

    def test_style_greeting():
        rsa=RealmStyleAdapter(); g=rsa.get_realm_greeting(RealmTier.LIANQI)
        assert len(g)>0
    results.append(_run_test("STYLE: greeting", test_style_greeting))

    def test_feature_unlock():
        rfg=RealmFeatureGate(); ok,_,req=rfg.check_access("u1","full_report",RealmTier.JINDAN)
        assert ok==True; ok2,_,r2=rfg.check_access("u1","stress_test",RealmTier.LIANQI)
        assert ok2==False
    results.append(_run_test("FEATURE: unlock check", test_feature_unlock))

    def test_feature_lists():
        rfg=RealmFeatureGate(); ul=rfg.list_unlocked_features(RealmTier.JINDAN)
        ll=rfg.list_locked_features(RealmTier.JINDAN); assert len(ul)>0; assert len(ll)>0
    results.append(_run_test("FEATURE: lists", test_feature_lists))

    def test_task_engine():
        cte=CultivationTaskEngine(); tasks=cte.generate_tasks_for_user("u1",RealmTier.JINDAN)
        assert len(tasks)>=1; tx=cte.record_action("u1","consult_asked"); assert tx.amount>0
    results.append(_run_test("TASK: engine basic", test_task_engine))

    def test_task_completion():
        cte=CultivationTaskEngine(); tasks=cte.generate_tasks_for_user("u1",RealmTier.LIANQI)
        for t in tasks[:1]:
            for _ in range(t.target_count): cte.record_action("u1","智能咨询")
        completed=cte.get_user_tasks("u1","completed"); assert len(completed)>=1
    results.append(_run_test("TASK: completion", test_task_completion))

    def test_analysis_reward():
        aer=AnalysisExpReward(); r=aer.calculate_reward("multi_panel_report","advanced","u1",True)
        assert r["exp_gained"]>=30; assert r["bonus"]==20
    results.append(_run_test("REWARD: analysis calc", test_analysis_reward))

    def test_market_agent():
        mg=MarketRealmGate(); ok,_,_=mg.can_recruit_agent("量化分析师",RealmTier.JINDAN,600)
        assert ok==True; ok2,_,_=mg.can_recruit_agent("策略回测师",RealmTier.LIANQI,9999)
        assert ok2==False
    results.append(_run_test("MARKET: agent recruit", test_market_agent))

    def test_market_skill():
        mg=MarketRealmGate(); ok,_,_=mg.can_buy_skill("数据清洗",RealmTier.LIANQI,100)
        assert ok==True; ok2,_,_=mg.can_buy_skill("策略回测优化",RealmTier.LIANQI,9999)
        assert ok2==False
    results.append(_run_test("MARKET: skill buy", test_market_skill))

    def test_resonance():
        ar=AgentResonance(); ev=ar.on_agent_upgrade("a1","户部助手",2,3,"u1")
        assert ev["final_exp"]>0; assert ev["old_level"]==2; assert ev["new_level"]==3
    results.append(_run_test("RESONANCE: upgrade", test_resonance))

    def test_team_realm():
        trs=TeamRealmSystem(); td=trs.create_or_update_team("t1",[{"realm_value":20,"exp":100},
            {"realm_value":35,"exp":200},{"realm_value":15,"exp":50}])
        assert td.member_count==3; assert td.avg_member_realm_value>0
    results.append(_run_test("TEAM: realm calc", test_team_realm))

    def test_team_skill():
        trs=TeamRealmSystem(); trs.create_or_update_team("ts1",[{"realm_value":60,"exp":500}])
        ok=trs.add_team_skill("ts1","修炼加速","全体+10%EXP",5,RealmTier.LIANQI)
        assert ok==True
    results.append(_run_test("TEAM: skill add", test_team_skill))

    def test_points_exchange():
        pe=PointsExchange(); r=pe.exchange_points_for_exp("u1",200,500)
        assert r["success"]==True; assert r["exp_gained"]>0
    results.append(_run_test("POINTS: exchange", test_points_exchange))

    def test_breakthrough():
        pe=PointsExchange(); rw=pe.grant_breakthrough_reward("u1",RealmTier.ZHUJI,RealmTier.JINDAN)
        assert rw==1000
    results.append(_run_test("POINTS: breakthrough", test_breakthrough))

    def test_privacy_set():
        cpf=CompliancePrivacyFusion(); r=cpf.set_privacy_visibility("u1",PrivacyVisibility.PUBLIC)
        assert r["new_visibility"]=="public"; assert cpf.get_visibility("u1","other")==True
    results.append(_run_test("PRIVACY: visibility", test_privacy_set))

    def test_compliance_audit():
        cpf=CompliancePrivacyFusion(); ev=cpf.audit_behavior("u1",
            {"reports_per_minute":15,"identical_queries":8,"night_activity":True,"volume":80})
        assert ev.is_violation==True; assert ev.penalty_exp>0
    results.append(_run_test("COMPLIANCE: audit", test_compliance_audit))

    def test_scaling_bingbu():
        acs=AgentCapabilityScaling(); cfg=acs.get_bingbu_config(RealmTier.YUANYING)
        assert cfg["risk_levels"]>=3; assert cfg["timeout"]>=30
    results.append(_run_test("SCALING: bingbu", test_scaling_bingbu))

    def test_scaling_li():
        acs=AgentCapabilityScaling(); lim=acs.get_liscaling_memory_limit(RealmTier.JINDAN)
        assert lim>=5000
    results.append(_run_test("SCALING: memory limit", test_scaling_li))

    def test_orchestrator_consult():
        orc=CultivationDeepOrchestrator(); r=orc.process_consultation("房价怎么样","u1",RealmTier.JINDAN)
        assert "exp_gained" in r; assert "total_exp" in r
    results.append(_run_test("ORC: consultation", test_orchestrator_consult))

    def test_orchestrator_analysis():
        orc=CultivationDeepOrchestrator(); r=orc.process_analysis("full","u1",RealmTier.JINDAN,True)
        assert r.get("access_granted")==True
    results.append(_run_test("ORC: analysis", test_orchestrator_analysis))

    def test_orchestrator_dashboard():
        orc=CultivationDeepOrchestrator(); d=orc.get_full_dashboard("u1",RealmTier.JINDAN)
        assert "realm" in d; assert "total_exp" in d; assert "unlocked_features" in d
    results.append(_run_test("ORC: dashboard", test_orchestrator_dashboard))

    passed=sum(1 for r in results if r[0]=="PASS")
    failed=[r for r in results if r[0]=="FAIL"]; errors=[r for r in results if r[0]=="ERROR"]
    print(f"\n{'='*60}")
    print(f"L41 CULTIVATION DEEP FUSION — TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Total : {len(results)}")
    print(f"  Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"  Failed: {len(failed)}")
    if failed:
        for _,name,err in failed: print(f"    [X] {name}: {err}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for _,name,err in errors: print(f"    [!] {name}: {err}")
    print(f"{'='*60}")
    return {"total":len(results),"passed":passed,"failed":len(failed),"errors":len(errors),"results":results}

if __name__ == "__main__":
    run_all_tests()
    print("\n[OK] Layer 41 — Cultivation Deep Fusion loaded OK")
