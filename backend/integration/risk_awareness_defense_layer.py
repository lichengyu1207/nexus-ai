# -*- coding: utf-8 -*-
"""
Layer 36 - Risk Awareness & Problem-Oriented Defense System
============================================================
14个战略计划问题导向与忧患意识实现层
8 Major Modules + Orchestrator + Testing Suite
"""
from __future__ import annotations
import math, random, time, uuid
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any, Tuple

# ═══════════════════════════════════════════════════════════════
# PART H — ENUMS & DATACLASSES
# ═══════════════════════════════════════════════════════════════

class RiskSeverity(PyEnum):
    CRITICAL="critical"; HIGH="high"; MEDIUM="medium"; LOW="low"

class RiskStatus(PyEnum):
    OPEN="open"; MITIGATING="mitigating"; RESOLVED="resolved"; ACCEPTED="accepted"

class MitigationActionType(PyEnum):
    AUTO_SCALE="auto_scale"; FAILOVER="failover"; RATE_LIMIT="rate_limit"
    ROLLBACK="rollback"; ALERT_HUMAN="alert_human"; SWITCH_SOURCE="switch_source"
    ENABLE_DEGRADE="enable_degrade"; ISOLATE_COMPONENT="isolate_component"
    INCREASE_BUFFER="increase_buffer"; RUN_CHAOS_TEST="run_chaos_test"
    FREEZE_WEIGHTS="freeze_weights"; PURGE_CACHE="purge_cache"

class AlertState(PyEnum):
    FIRING="firing"; ACKNOWLEDGED="acknowledged"; RESOLVED_STATE="resolved"

class ChaosInjectionType(PyEnum):
    NODE_KILL="node_kill"; NETWORK_LATENCY="network_latency"
    NETWORK_PARTITION="network_partition"; CPU_SPIKE="cpu_spike"
    MEMORY_LEAK="memory_leak"; DISK_FULL="disk_full"
    PROCESS_CRASH="process_crash"; DATA_CORRUPTION="data_corruption"

class RedTeamAttackType(PyEnum):
    PROMPT_INJECTION="prompt_injection"; JAILBREAK="jailbreak"
    DDoS="ddos"; SQL_INJECTION="sql_injection"; XSS="xss"
    DATA_SCRAPING="data_scraping"; FRAUDULENT_FEEDBACK="fraudulent_feedback"
    BOUNTY_EXPLOIT="bounty_exploit"

class ReviewOutcome(PyEnum):
    HEALTHY="healthy"; WARNING="warning"; CRITICAL_STATE2="critical"; IMPROVING="improving"

@dataclass
class RiskItem:
    id: str; plan_id: int; category: str; title: str; description: str
    probability: float; impact: float; severity: RiskSeverity
    status: RiskStatus = RiskStatus.OPEN
    mitigation_strategy: str = ""; created_at: float = field(default_factory=time.time)

@dataclass
class ProblemDetection:
    id: str; category: str; metric_name: str; value: float; threshold: float
    severity: RiskSeverity; detected_at: float = field(default_factory=time.time)
    acknowledged: bool = False; resolved: bool = False

@dataclass
class MitigationAction:
    id: str; category: str; action_type: MitigationActionType
    description: str; executed_at: float = field(default_factory=time.time)
    success: bool = True; rollback_data: Any = None

@dataclass
class AlertRule:
    id: str; category: str; metric_name: str; operator: str; threshold: float
    severity: RiskSeverity; cooldown_seconds: int = 300

@dataclass
class AlertEvent:
    id: str; rule_id: str; category: str; metric_name: str; value: float
    state: AlertState; fired_at: float = field(default_factory=time.time)
    acknowledged_at: Optional[float] = None; resolved_at: Optional[float] = None
    fire_count: int = 1

@dataclass
class ChaosExperiment:
    id: str; injection_type: ChaosInjectionType; target: str
    duration_seconds: int; designed_at: float = field(default_factory=time.time)
    run_at: Optional[float] = None; result: Optional[Dict[str,Any]] = None

@dataclass
class RedBlueExercise:
    id: str; attack_type: RedTeamAttackType; target: str
    designed_at: float = field(default_factory=time.time)
    run_at: Optional[float] = None; result: Optional[Dict[str,Any]] = None

@dataclass
class WeeklyReviewReport:
    plan_id: int; health_score: float; total_risks: int; open_critical: int
    findings: List[str]; recommendations: List[str]
    outcome: ReviewOutcome; generated_at: float = field(default_factory=time.time)

@dataclass
class WorryLogEntry:
    id: str; plan_id: str; title: str; severity: RiskSeverity
    description: str; tags: List[str]; created_at: float = field(default_factory=time.time)
    resolved_by: str = ""; resolved_at: Optional[float] = None; resolved: bool = False

@dataclass
class RiskDashboardSnapshot:
    total_risks: int; open_count: int; critical_open: int; overall_health_pct: float
    active_alerts: int; active_detections: int; resilience_score: float; defense_score: float
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════
# PART A — RISK REGISTRY (42 built-in risks across 14 plans)
# ═══════════════════════════════════════════════════════════════

class RiskRegistry:
    def __init__(self):
        self._risks: Dict[str,RiskItem] = {}; self._custom_count = 0
        self._init_builtin()
    def _init_builtin(self):
        data = [
            ("R_P01_001",1,"scheduler_cpu","调度引擎CPU过载风险","CPU持续>90%导致任务延迟积压",0.7,0.9,RiskSeverity.HIGH),
            ("R_P01_002",1,"scheduler_deadlock","调度死锁风险","循环依赖导致任务永久阻塞",0.3,1.0,RiskSeverity.CRITICAL),
            ("R_P01_003",1,"scheduler_priority_inv","优先级反转风险","低优先级任务阻塞高优先级",0.5,0.7,RiskSeverity.MEDIUM),
            ("R_P02_001",2,"memory_fragmentation","内存碎片化风险","长期运行导致可用内存下降",0.6,0.6,RiskSeverity.MEDIUM),
            ("R_P02_002",2,"memory_leak_core","核心模块内存泄漏风险","未释放对象累积导致OOM",0.4,0.9,RiskSeverity.HIGH),
            ("R_P02_003",2,"memory_cache_overflow","缓存溢出风险","无界缓存消耗全部内存",0.5,0.8,RiskSeverity.HIGH),
            ("R_P03_001",3,"personality_drift","人格漂移风险","长期交互导致角色一致性丧失",0.5,0.7,RiskSeverity.MEDIUM),
            ("R_P03_002",3,"personality_conflict","人格冲突风险","多角色设定产生矛盾回应",0.4,0.8,RiskSeverity.HIGH),
            ("R_P03_003",3,"personality_overfit","人格过拟合风险","过度适配特定用户失去通用性",0.6,0.5,RiskSeverity.LOW),
            ("R_P04_001",4,"crawl_rate_limit","爬虫限流风险","高频请求导致IP封禁",0.7,0.8,RiskSeverity.HIGH),
            ("R_P04_002",4,"crawl_data_stale","数据陈旧风险","源站更新未及时同步",0.5,0.6,RiskSeverity.MEDIUM),
            ("R_P04_003",4,"crawl_schema_break","Schema变更风险","源站结构变化导致解析失败",0.3,0.9,RiskSeverity.HIGH),
            ("R_P05_001",5,"quant_model_drift","量化模型漂移风险","市场环境变化导致模型失效",0.6,0.9,RiskSeverity.CRITICAL),
            ("R_P05_002",5,"quant_data_quality","数据质量风险","脏噪声数据污染训练集",0.5,0.7,RiskSeverity.HIGH),
            ("R_P05_003",5,"quant_overfit_backtest","回测过拟合风险","历史表现无法泛化到未来",0.7,0.8,RiskSeverity.CRITICAL),
            ("R_P06_001",6,"security_prompt_inj","Prompt注入风险","恶意输入绕过安全约束",0.6,0.95,RiskSeverity.CRITICAL),
            ("R_P06_002",6,"security_data_leak","数据泄露风险","敏感信息通过输出侧信道泄露",0.4,1.0,RiskSeverity.CRITICAL),
            ("R_P06_003",6,"security_auth_bypass","认证绕过风险","JWT/Session伪造获取未授权访问",0.3,1.0,RiskSeverity.CRITICAL),
            ("R_P07_001",7,"ha_single_pof","单点故障风险","关键组件无冗余设计",0.5,0.9,RiskSeverity.CRITICAL),
            ("R_P07_002",7,"ha_rto_exceed","RTO超时风险","故障恢复时间超过SLA承诺",0.4,0.8,RiskSeverity.HIGH),
            ("R_P07_003",7,"ha_data_loss","数据丢失风险","主从切换时未提交事务丢失",0.3,1.0,RiskSeverity.CRITICAL),
            ("R_P08_001",8,"dev_doc_outdated","文档滞后风险","API变更未同步更新文档",0.8,0.4,RiskSeverity.LOW),
            ("R_P08_002",8,"dev_sdk_compat","SDK兼容性风险","版本升级破坏向后兼容",0.5,0.7,RiskSeverity.MEDIUM),
            ("R_P08_003",8,"dev_abuse_api","API滥用风险","无速率限制导致资源耗尽",0.6,0.7,RiskSeverity.MEDIUM),
            ("R_P09_001",9,"mobile_crash","App崩溃风险","未捕获异常导致闪退",0.4,0.8,RiskSeverity.HIGH),
            ("R_P09_002",9,"mobile_perf_degrad","性能退化风险","累积代码导致启动变慢",0.6,0.5,RiskSeverity.MEDIUM),
            ("R_P09_003",9,"mobile_permission","权限过度申请风险","不必要权限引发用户信任危机",0.5,0.7,RiskSeverity.MEDIUM),
            ("R_P10_001",10,"i18n_hardcode","硬编码文本风险","中文字符串散落导致无法国际化",0.7,0.5,RiskSeverity.MEDIUM),
            ("R_P10_002",10,"i18n_locale_edge","边缘语言风险","RTL/复杂脚本语言渲染错误",0.3,0.6,RiskSeverity.LOW),
            ("R_P10_003",10,"i18n_datetime","日期时间格式风险","时区处理不当显示错误信息",0.5,0.7,RiskSeverity.MEDIUM),
            ("R_P11_001",11,"compliance_gdpr","GDPR合规风险","用户数据处理不符合欧盟法规",0.4,1.0,RiskSeverity.CRITICAL),
            ("R_P11_002",11,"compliance_audit_trail","审计日志缺失风险","操作记录不全无法追溯",0.5,0.8,RiskSeverity.HIGH),
            ("R_P11_003",11,"compliance_retention","数据保留策略风险","删除/保留期限违反法规要求",0.4,0.7,RiskSeverity.HIGH),
            ("R_P12_001",12,"cost_cloud_spend","云成本失控风险","闲置资源未释放导致费用激增",0.7,0.7,RiskSeverity.HIGH),
            ("R_P12_002",12,"cost_third_party","第三方服务依赖风险","供应商涨价/停服影响运营",0.4,0.8,RiskSeverity.MEDIUM),
            ("R_P12_003",12,"cost_tech_debt","技术债务利息风险","快速迭代积累的债务增加维护成本",0.8,0.6,RiskSeverity.MEDIUM),
            ("R_P13_001",13,"growth_churn","用户流失风险","DAU连续下滑且留存率下降",0.6,0.8,RiskSeverity.HIGH),
            ("R_P13_002",13,"growth_acquisition_cost","获客成本上升风险","CAC>LTV导致商业模式不可持续",0.5,0.9,RiskSeverity.CRITICAL),
            ("R_P13_003",13,"growth_nps_decline","NPS下滑风险","用户满意度降低影响口碑传播",0.5,0.6,RiskSeverity.MEDIUM),
            ("R_P14_001",14,"ai_model_obsolescence","模型淘汰风险","新架构SOTA出现使现有模型落后",0.7,0.8,RiskSeverity.HIGH),
            ("R_P14_002",14,"ai_bias_fairness","偏见公平性风险","训练数据偏差导致歧视性输出",0.5,0.9,RiskSeverity.CRITICAL),
            ("R_P14_003",14,"ai_safety_alignment","对齐安全风险","目标错位产生有害行为",0.4,1.0,RiskSeverity.CRITICAL),
        ]
        for d in data:
            self._risks[d[0]] = RiskItem(d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7])
    def register_custom(self, plan_id:int, category:str, title:str, desc:str, prob:float, impact:float, sev:RiskSeverity) -> RiskItem:
        self._custom_count += 1; rid=f"CUSTOM_{self._custom_count:04d}"
        item=RiskItem(rid,plan_id,category,title,desc,prob,impact,sev); self._risks[rid]=item; return item
    def get(self, risk_id:str) -> Optional[RiskItem]: return self._risks.get(risk_id)
    def by_plan(self, plan_id:int) -> List[RiskItem]: return [r for r in self._risks.values() if r.plan_id==plan_id]
    def all_risks(self) -> List[RiskItem]: return list(self._risks.values())
    def update_status(self, risk_id:str, status:RiskStatus) -> bool:
        r=self.get(risk_id)
        if r: r.status=status; return True
        return False
    def compute_score(self, risk_id:str) -> float:
        r=self.get(risk_id)
        if not r: return 0.0
        raw=r.probability*r.impact*100
        sm={RiskStatus.OPEN:1.0,RiskStatus.MITIGATING:0.7,RiskStatus.RESOLVED:0.1,RiskStatus.ACCEPTED:0.5}
        vm={RiskSeverity.CRITICAL:1.5,RiskSeverity.HIGH:1.2,RiskSeverity.MEDIUM:1.0,RiskSeverity.LOW:0.7}
        return raw*sm.get(r.status,1.0)*vm.get(r.severity,1.0)
    def stats(self) -> Dict[str,Any]:
        risks=self.all_risks(); open_c=sum(1 for r in risks if r.status==RiskStatus.OPEN and r.severity==RiskSeverity.CRITICAL)
        return {"total":len(risks),"open":sum(1 for r in risks if r.status in(RiskStatus.OPEN,RiskStatus.MITIGATING)),"critical_open":open_c,"custom":self._custom_count}


# ═══════════════════════════════════════════════════════════════
# PART B — PROBLEM-ORIENTED DETECTOR (42 detection rules)
# ═══════════════════════════════════════════════════════════════

class ProblemOrientedDetector:
    def __init__(self, registry: RiskRegistry):
        self._reg = registry; self._detections: Dict[str,ProblemDetection] = {}
        self._thresh = {
            "scheduler_cpu":("scheduler_cpu_usage",90.0), "scheduler_deadlock":("pending_tasks",1000),
            "scheduler_priority_inv":("avg_wait_time",30.0), "memory_fragmentation":("fragmentation_ratio",0.6),
            "memory_leak_core":("heap_growth_mb",500.0), "memory_cache_overflow":("cache_size_mb",2048.0),
            "personality_drift":("consistency_score",0.7), "personality_conflict":("contradiction_count",5),
            "personality_overfit":("adaptation_score",0.95), "crawl_rate_limit":("429_error_rate",0.05),
            "crawl_data_stale":("max_data_age_hours",24.0), "crawl_schema_break":("parse_error_rate",0.1),
            "quant_model_drift":("mape_3day",0.15), "quant_data_quality":("null_ratio",0.05),
            "quant_overfit_backtest":("sharpe_drop_ratio",0.3), "security_prompt_inj":("injection_attempt_count",3),
            "security_data_leak":("sensitive_exposure_count",1), "security_auth_bypass":("auth_anomaly_score",0.85),
            "ha_single_pof":("redundancy_count",1), "ha_rto_exceed":("avg_recovery_time_sec",300.0),
            "ha_data_loss":("replication_lag_sec",60.0), "dev_doc_outdated":("doc staleness_days",30.0),
            "dev_sdk_compat":("api_break_count",1), "dev_abuse_api":("requests_per_minute_per_user",1000),
            "mobile_crash":("app_crash_rate",0.005), "mobile_perf_degrad":("cold_start_ms",3000),
            "mobile_permission":("excessive_permission_count",3), "i18n_hardcode":("hardcoded_string_ratio",0.1),
            "i18n_locale_edge":("rtl_render_error_count",1), "i18n_datetime":("timezone_error_count",2),
            "compliance_gdpr":("consent_missing_ratio",0.05), "compliance_audit_trail":("audit_gap_hours",1.0),
            "compliance_retention":("retention_violation_count",1), "cost_cloud_spend":("monthly_unused_resource_ratio",0.2),
            "cost_third_party":("vendor_dependency_count",3), "cost_tech_debt":("tech_debt_ratio",0.3),
            "growth_churn":("dau_decline_days",7), "growth_acquisition_cost":("cac_ltv_ratio",1.5),
            "growth_nps_decline":("nps_change",-10.0), "ai_model_obsolescence":("model_age_months",12),
            "ai_bias_fairness":("demographic_parity_diff",0.15), "ai_safety_alignment":("safety_violation_count",1),
        }
    def ingest(self, metrics: Dict[str,float]) -> ProblemDetection:
        detections = []; detected_any = None
        for cat,(metric,threshold) in self._thresh.items():
            if metric not in metrics: continue
            val=metrics[metric]
            if val>=threshold:
                sev=RiskSeverity.HIGH if val>=threshold*1.5 else (RiskSeverity.CRITICAL if val>=threshold*2 else RiskSeverity.MEDIUM)
                pd=ProblemDetection(str(uuid.uuid4())[:8],cat,metric,val,threshold,sev)
                self._detections[pd.id]=pd; detections.append(pd)
                if detected_any is None: detected_any=pd
        return detected_any or ProblemDetection("none","", "",0,0,RiskSeverity.LOW)
    def acknowledge(self, det_id:str) -> bool:
        d=self._detections.get(det_id)
        if d: d.acknowledged=True; return True
        return False
    def resolve(self, det_id:str) -> bool:
        d=self._detections.get(det_id)
        if d: d.resolved=True; return True
        return False
    def active(self) -> List[ProblemDetection]: return [d for d in self._detections.values() if not d.resolved]
    def detector_stats(self) -> Dict[str,int]:
        a=self.active(); return {"total":len(self._detections),"active":len(a),"acked":sum(1 for d in a if d.acknowledged)}


# ═══════════════════════════════════════════════════════════════
# PART C — MITIGATION STRATEGY ENGINE (42 category→action mappings)
# ═══════════════════════════════════════════════════════════════

class MitigationStrategyEngine:
    def __init__(self, registry: RiskRegistry):
        self._reg = registry; self._history: List[MitigationAction] = []
        self._strat_map = {
            "scheduler_cpu":[MitigationActionType.AUTO_SCALE,MitigationActionType.RATE_LIMIT],
            "scheduler_deadlock":[MitigationActionType.ALERT_HUMAN,MitigationActionType.ENABLE_DEGRADE],
            "scheduler_priority_inv":[MitigationActionType.FREEZE_WEIGHTS,MitigationActionType.ALERT_HUMAN],
            "memory_fragmentation":[MitigationActionType.PURGE_CACHE,MitigationActionType.INCREASE_BUFFER],
            "memory_leak_core":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.PURGE_CACHE],
            "memory_cache_overflow":[MitigationActionType.PURGE_CACHE,MitigationActionType.RATE_LIMIT],
            "personality_drift":[MitigationActionType.FREEZE_WEIGHTS,MitigationActionType.RUN_CHAOS_TEST],
            "personality_conflict":[MitigationActionType.ENABLE_DEGRADE,MitigationActionType.ALERT_HUMAN],
            "personality_overfit":[MitigationActionType.RUN_CHAOS_TEST,MitigationActionType.SWITCH_SOURCE],
            "crawl_rate_limit":[MitigationActionType.RATE_LIMIT,MitigationActionType.SWITCH_SOURCE],
            "crawl_data_stale":[MitigationActionType.SWITCH_SOURCE,MitigationActionType.AUTO_SCALE],
            "crawl_schema_break":[MitigationActionType.ENABLE_DEGRADE,MitigationActionType.ALERT_HUMAN],
            "quant_model_drift":[MitigationActionType.ROLLBACK,MitigationActionType.SWITCH_SOURCE],
            "quant_data_quality":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.ALERT_HUMAN],
            "quant_overfit_backtest":[MitigationActionType.ROLLBACK,MitigationActionType.RUN_CHAOS_TEST],
            "security_prompt_inj":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.ALERT_HUMAN],
            "security_data_leak":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.PURGE_CACHE],
            "security_auth_bypass":[MitigationActionType.FAILOVER,MitigationActionType.ALERT_HUMAN],
            "ha_single_pof":[MitigationActionType.FAILOVER,MitigationActionType.INCREASE_BUFFER],
            "ha_rto_exceed":[MitigationActionType.FAILOVER,MitigationActionType.AUTO_SCALE],
            "ha_data_loss":[MitigationActionType.FAILOVER,MitigationActionType.INCREASE_BUFFER],
            "dev_doc_outdated":[MitigationActionType.ALERT_HUMAN,MitigationActionType.RUN_CHAOS_TEST],
            "dev_sdk_compat":[MitigationActionType.ENABLE_DEGRADE,MitigationActionType.ALERT_HUMAN],
            "dev_abuse_api":[MitigationActionType.RATE_LIMIT,MitigationActionType.ISOLATE_COMPONENT],
            "mobile_crash":[MitigationActionType.ROLLBACK,MitigationActionType.ALERT_HUMAN],
            "mobile_perf_degrad":[MitigationActionType.PURGE_CACHE,MitigationActionType.AUTO_SCALE],
            "mobile_permission":[MitigationActionType.ENABLE_DEGRADE,MitigationActionType.ALERT_HUMAN],
            "i18n_hardcode":[MitigationActionType.ALERT_HUMAN,MitigationActionType.RUN_CHAOS_TEST],
            "i18n_locale_edge":[MitigationActionType.ENABLE_DEGRADE,MitigationActionType.ALERT_HUMAN],
            "i18n_datetime":[MitigationActionType.ALERT_HUMAN,MitigationActionType.SWITCH_SOURCE],
            "compliance_gdpr":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.PURGE_CACHE],
            "compliance_audit_trail":[MitigationActionType.INCREASE_BUFFER,MitigationActionType.ALERT_HUMAN],
            "compliance_retention":[MitigationActionType.PURGE_CACHE,MitigationActionType.ALERT_HUMAN],
            "cost_cloud_spend":[MitigationActionType.AUTO_SCALE,MitigationActionType.ALERT_HUMAN],
            "cost_third_party":[MitigationActionType.SWITCH_SOURCE,MitigationActionType.ALERT_HUMAN],
            "cost_tech_debt":[MitigationActionType.RUN_CHAOS_TEST,MitigationActionType.ALERT_HUMAN],
            "growth_churn":[MitigationActionType.SWITCH_SOURCE,MitigationActionType.ALERT_HUMAN],
            "growth_acquisition_cost":[MitigationActionType.ENABLE_DEGRADE,MitigationActionType.ALERT_HUMAN],
            "growth_nps_decline":[MitigationActionType.ALERT_HUMAN,MitigationActionType.SWITCH_SOURCE],
            "ai_model_obsolescence":[MitigationActionType.SWITCH_SOURCE,MitigationActionType.RUN_CHAOS_TEST],
            "ai_bias_fairness":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.ALERT_HUMAN],
            "ai_safety_alignment":[MitigationActionType.ISOLATE_COMPONENT,MitigationActionType.FREEZE_WEIGHTS],
        }
    def execute(self, category: str, detection: Optional[ProblemDetection]=None) -> MitigationAction:
        actions=self._strat_map.get(category,[MitigationActionType.ALERT_HUMAN,MitigationActionType.ALERT_HUMAN])
        action=actions[0]; desc=f"Auto-mitigate [{category}]: {action.value}"
        ma=MitigationAction(str(uuid.uuid4())[:8],category,action,desc); self._history.append(ma); return ma
    def auto_mitigate(self, detection: ProblemDetection) -> MitigationAction: return self.execute(detection.category,detection)
    def rollback(self, action_id: str) -> bool:
        for h in reversed(self._history):
            if h.id==action_id: h.success=False; return True
        return False
    def history(self) -> List[MitigationAction]: return list(self._history)
    def engine_stats(self) -> Dict[str,Any]: return {"total_actions":len(self._history),"success_rate":(sum(1 for h in self._history if h.success)/max(len(self._history),1))}


# ═══════════════════════════════════════════════════════════════
# PART D — MONITORING ALERT SYSTEM (42 alert rules)
# ═══════════════════════════════════════════════════════════════

class MonitoringAlertSystem:
    def __init__(self):
        self._rules: Dict[str,AlertRule]={}; self._alerts: Dict[str,AlertEvent]={}; self._init_rules()
    def _init_rules(self):
        rules_data = [
            ("AR_001","scheduler_cpu","scheduler_cpu_usage",">",90,RiskSeverity.HIGH,300),
            ("AR_002","scheduler_deadlock","pending_tasks",">",1000,RiskSeverity.CRITICAL,120),
            ("AR_003","scheduler_priority_inv","avg_wait_time",">",30,RiskSeverity.MEDIUM,600),
            ("AR_004","memory_fragmentation","fragmentation_ratio",">",0.6,RiskSeverity.MEDIUM,900),
            ("AR_005","memory_leak_core","heap_growth_mb",">",500,RiskSeverity.HIGH,600),
            ("AR_006","memory_cache_overflow","cache_size_mb",">",2048,RiskSeverity.HIGH,300),
            ("AR_007","personality_drift","consistency_score","<",0.7,RiskSeverity.MEDIUM,1800),
            ("AR_008","personality_conflict","contradiction_count",">",5,RiskSeverity.HIGH,600),
            ("AR_009","personality_overfit","adaptation_score",">",0.95,RiskSeverity.LOW,3600),
            ("AR_010","crawl_rate_limit","429_error_rate",">",0.05,RiskSeverity.HIGH,180),
            ("AR_011","crawl_data_stale","max_data_age_hours",">",24,RiskSeverity.MEDIUM,3600),
            ("AR_012","crawl_schema_break","parse_error_rate",">",0.1,RiskSeverity.HIGH,300),
            ("AR_013","quant_model_drift","mape_3day",">",0.15,RiskSeverity.CRITICAL,900),
            ("AR_014","quant_data_quality","null_ratio",">",0.05,RiskSeverity.HIGH,1800),
            ("AR_015","quant_overfit_backtest","sharpe_drop_ratio",">",0.3,RiskSeverity.CRITICAL,600),
            ("AR_016","security_prompt_inj","injection_attempt_count",">",3,RiskSeverity.CRITICAL,60),
            ("AR_017","security_data_leak","sensitive_exposure_count",">",1,RiskSeverity.CRITICAL,30),
            ("AR_018","security_auth_bypass","auth_anomaly_score",">",0.85,RiskSeverity.CRITICAL,30),
            ("AR_019","ha_single_pof","redundancy_count","<",2,RiskSeverity.CRITICAL,86400),
            ("AR_020","ha_rto_exceed","avg_recovery_time_sec",">",300,RiskSeverity.HIGH,600),
            ("AR_021","ha_data_loss","replication_lag_sec",">",60,RiskSeverity.HIGH,300),
            ("AR_022","dev_doc_outdated","doc_staleness_days",">",30,RiskSeverity.LOW,604800),
            ("AR_023","dev_sdk_compat","api_break_count",">",1,RiskSeverity.MEDIUM,3600),
            ("AR_024","dev_abuse_api","requests_per_min_per_user",">",1000,RiskSeverity.MEDIUM,300),
            ("AR_025","mobile_crash","app_crash_rate",">",0.005,RiskSeverity.HIGH,180),
            ("AR_026","mobile_perf_degrad","cold_start_ms",">",3000,RiskSeverity.MEDIUM,7200),
            ("AR_027","mobile_permission","excessive_permission_count",">",3,RiskSeverity.MEDIUM,86400),
            ("AR_028","i18n_hardcode","hardcoded_string_ratio",">",0.1,RiskSeverity.MEDIUM,604800),
            ("AR_029","i18n_locale_edge","rtl_render_error_count",">",1,RiskSeverity.LOW,86400),
            ("AR_030","i18n_datetime","timezone_error_count",">",2,RiskSeverity.MEDIUM,3600),
            ("AR_031","compliance_gdpr","consent_missing_ratio",">",0.05,RiskSeverity.CRITICAL,3600),
            ("AR_032","compliance_audit_trail","audit_gap_hours",">",1,RiskSeverity.HIGH,3600),
            ("AR_033","compliance_retention","retention_violation_count",">",1,RiskSeverity.HIGH,86400),
            ("AR_034","cost_cloud_spend","monthly_unused_resource_ratio",">",0.2,RiskSeverity.HIGH,604800),
            ("AR_035","cost_third_party","vendor_dependency_count",">",3,RiskSeverity.MEDIUM,2592000),
            ("AR_036","cost_tech_debt","tech_debt_ratio",">",0.3,RiskSeverity.MEDIUM,2592000),
            ("AR_037","growth_churn","dau_decline_days",">",7,RiskSeverity.HIGH,172800),
            ("AR_038","growth_acquisition_cost","cac_ltv_ratio",">",1.5,RiskSeverity.CRITICAL,604800),
            ("AR_039","growth_nps_decline","nps_change","<",-10,RiskSeverity.MEDIUM,604800),
            ("AR_040","ai_model_obsolescence","model_age_months",">",12,RiskSeverity.HIGH,2592000),
            ("AR_041","ai_bias_fairness","demographic_parity_diff",">",0.15,RiskSeverity.CRITICAL,2592000),
            ("AR_042","ai_safety_alignment","safety_violation_count",">",1,RiskSeverity.CRITICAL,60),
        ]
        for rd in rules_data:
            self._rules[rd[0]]=AlertRule(*rd)
    def evaluate_metric(self, metric_name: str, value: float) -> List[AlertEvent]:
        fired=[]; now=time.time()
        for rule in self._rules.values():
            if rule.metric_name!=metric_name: continue
            triggered=False
            if rule.operator==">" and value>rule.threshold: triggered=True
            elif rule.operator=="<" and value<rule.threshold: triggered=True
            if not triggered: continue
            existing=[a for a in self._alerts.values() if a.rule_id==rule.id and a.state!=AlertState.RESOLVED_STATE]
            if existing:
                latest=max(existing,key=lambda a:a.fired_at)
                if now-latest.fired_at<rule.cooldown_seconds: latest.fire_count+=1; continue
            ae=AlertEvent(str(uuid.uuid4())[:8],rule.id,rule.category,metric_name,value,AlertState.FIRING)
            self._alerts[ae.id]=ae; fired.append(ae)
        return fired
    def acknowledge_alert(self, alert_id: str) -> bool:
        a=self._alerts.get(alert_id)
        if a and a.state==AlertState.FIRING: a.state=AlertState.ACKNOWLEDGED; a.acknowledged_at=time.time(); return True
        return False
    def resolve_alert(self, alert_id: str) -> bool:
        a=self._alerts.get(alert_id)
        if a: a.state=AlertState.RESOLVED_STATE; a.resolved_at=time.time(); return True
        return False
    def active_alerts(self) -> List[AlertEvent]: return [a for a in self._alerts.values() if a.state in(AlertState.FIRING,AlertState.ACKNOWLEDGED)]
    def alert_stats(self) -> Dict[str,Any]:
        aa=self.active_alerts(); return {"total_rules":len(self._rules),"total_alerts":len(self._alerts),"active":len(aa),"firing":sum(1 for a in aa if a.state==AlertState.FIRING)}


# ═══════════════════════════════════════════════════════════════
# PART E — CHAOS ENGINEERING SIMULATOR
# ═══════════════════════════════════════════════════════════════

class ChaosEngineeringSimulator:
    def __init__(self):
        self._experiments: Dict[str,ChaosExperiment] = {}; self._history: List[Dict[str,Any]] = []
    def design_experiment(self, injection_type: ChaosInjectionType, target: str, duration_seconds: int=60) -> ChaosExperiment:
        exp=ChaosExperiment(str(uuid.uuid4())[:8],injection_type,target,duration_seconds)
        self._experiments[exp.id]=exp; return exp
    def run_experiment(self, exp_id: str) -> Dict[str,Any]:
        exp=self._experiments.get(exp_id)
        if not exp or exp.run_at: return {"error":"not found or already run"}
        exp.run_at=time.time(); random.seed(exp_id)
        recovery_time=random.uniform(5,120); success=recovery_time<exp.duration_seconds*2
        resilience=round(max(0,100-(recovery_time/exp.duration_seconds*50)),1)
        result={"experiment_id":exp_id,"type":exp.injection_type.value,"target":exp.target,
            "recovery_time_sec":round(recovery_time,1),"success":success,"resilience_score":resilience}
        exp.result=result; self._history.append(result); return result
    def list_experiments(self) -> List[ChaosExperiment]: return list(self._experiments.values())
    def get_history(self) -> List[Dict[str,Any]]: return list(self._history)
    def simulator_stats(self) -> Dict[str,Any]:
        ran=[e for e in self._experiments.values() if e.run_at]
        return {"designed":len(self._experiments),"ran":len(ran),"avg_resilience":(sum((e.result or {}).get("resilience_score",0) for e in ran)/max(len(ran),1))}


# ═══════════════════════════════════════════════════════════════
# PART F — RED/BLUE TEAM ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class RedBlueTeamOrchestrator:
    def __init__(self):
        self._exercises: Dict[str,RedBlueExercise] = {}; self._results: List[Dict[str,Any]] = []
    def design_exercise(self, attack_type: RedTeamAttackType, target: str) -> RedBlueExercise:
        ex=RedBlueExercise(str(uuid.uuid4())[:8],attack_type,target)
        self._exercises[ex.id]=ex; return ex
    def run_exercise(self, ex_id: str) -> Dict[str,Any]:
        ex=self._exercises.get(ex_id)
        if not ex or ex.run_at: return {"error":"not found or already run"}
        ex.run_at=time.time(); random.seed(ex_id+"rb")
        detection_score=round(random.uniform(0.3,1.0),2); mitigation_score=round(random.uniform(0.2,0.95),2)
        defense=round((detection_score*0.4+mitigation_score*0.6)*100,1)
        result={"exercise_id":ex_id,"attack_type":ex.attack_type.value,"target":ex.target,
            "detection_score":detection_score,"mitigation_score":mitigation_score,"defense_score":defense,
            "status":"PASSED" if defense>=70 else "NEEDS_IMPROVEMENT"}
        ex.result=result; self._results.append(result); return result
    def get_defense_score(self) -> float:
        if not self._results: return 0.0
        return round(sum(r["defense_score"] for r in self._results)/len(self._results),1)
    def list_exercises(self) -> List[RedBlueExercise]: return list(self._exercises.values())
    def orchestrator_stats(self) -> Dict[str,Any]:
        ran=[e for e in self._exercises.values() if e.run_at]
        return {"designed":len(self._exercises),"ran":len(ran),"overall_defense":self.get_defense_score()}


# ═══════════════════════════════════════════════════════════════
# PART G — WEEKLY REVIEW ENGINE
# ═══════════════════════════════════════════════════════════════

class WeeklyReviewEngine:
    def __init__(self, registry: RiskRegistry, detector: ProblemOrientedDetector, alerts: MonitoringAlertSystem):
        self._reg = registry; self._det = detector; self._alt = alerts; self._reports: Dict[int,WeeklyReviewReport] = {}
    def generate_report(self, plan_id: int) -> WeeklyReviewReport:
        risks=self._reg.by_plan(plan_id); open_crit=sum(1 for r in risks if r.status==RiskStatus.OPEN and r.severity==RiskSeverity.CRITICAL)
        scores=[self._reg.compute_score(r.id) for r in risks]; health=100.0
        health-=min(open_crit*10,30); high_scores=[s for s in scores if s>500]; health-=min(len(high_scores)*2,20)
        health=max(0,min(100,health))
        findings=[f"Plan {plan_id}: {len(risks)} risks tracked, {open_crit} critical open"]
        recs=["Schedule deep-dive review for critical items"] if open_crit>0 else ["Continue monitoring"]
        outcome=ReviewOutcome.CRITICAL_STATE2 if health<40 else (ReviewOutcome.WARNING if health<70 else (ReviewOutcome.IMPROVING if health<90 else ReviewOutcome.HEALTHY))
        report=WeeklyReviewReport(plan_id,health,len(risks),open_crit,findings,recs,outcome)
        self._reports[plan_id]=report; return report
    def full_review(self) -> Dict[str,Any]:
        reports={}
        for pid in range(1,15): reports[pid]=self.generate_report(pid)
        avg_health=round(sum(r.health_score for r in reports.values())/14,1)
        return {"plans":reports,"average_health":avg_health,"generated_at":time.time()}


# ═══════════════════════════════════════════════════════════════
# PART H — WORRY LOG MANAGER
# ═══════════════════════════════════════════════════════════════

class WorryLogManager:
    def __init__(self): self._logs: Dict[str,WorryLogEntry] = {}
    def log_incident(self, plan_id: str, severity: RiskSeverity, title: str, description: str="", tags: Optional[List[str]]=None, resolved_by: str="") -> WorryLogEntry:
        entry=WorryLogEntry(str(uuid.uuid4())[:8],plan_id,title,severity,description,tags or [])
        self._logs[entry.id]=entry; return entry
    def resolve_entry(self, entry_id: str, resolved_by: str="system") -> Optional[WorryLogEntry]:
        e=self._logs.get(entry_id)
        if e: e.resolved=True; e.resolved_by=resolved_by; e.resolved_at=time.time(); return e
        return None
    def search_logs(self, plan_id: Optional[str]=None, severity: Optional[RiskSeverity]=None, tag: Optional[str]=None, resolved_only: bool=False) -> List[WorryLogEntry]:
        results=list(self._logs.values())
        if plan_id: results=[l for l in results if l.plan_id==plan_id]
        if severity: results=[l for l in results if l.severity==severity]
        if tag: results=[l for l in results if tag in (l.tags or [])]
        if resolved_only: results=[l for l in results if l.resolved]
        return results
    def get_trend(self, days: int=7) -> Dict[str,Any]:
        cutoff=time.time()-days*86400; recent=[l for l in self._logs.values() if l.created_at>=cutoff]
        daily={}; sev={"critical":0,"high":0,"medium":0,"low":0}
        for l in recent:
            day=int(l.created_at/86400); daily[day]=daily.get(day,0)+1; sev[l.severity.value]=sev.get(l.severity.value,0)+1
        return {"total_incidents":len(recent),"daily_counts":daily,"by_severity":sev,"period_days":days}
    def log_stats(self) -> Dict[str,Any]:
        total=len(self._logs); resolved=sum(1 for l in self._logs.values() if l.resolved)
        return {"total":total,"resolved":resolved,"active":total-resolved,"resolution_rate":(resolved/max(total,1))}


# ═══════════════════════════════════════════════════════════════
# PART I — RISK AWARENESS ORCHESTRATOR (unified coordinator)
# ═══════════════════════════════════════════════════════════════

class RiskAwarenessOrchestrator:
    def __init__(self):
        self.registry = RiskRegistry(); self.detector = ProblemOrientedDetector(self.registry)
        self.engine = MitigationStrategyEngine(self.registry); self.alerts = MonitoringAlertSystem()
        self.chaos = ChaosEngineeringSimulator(); self.redblue = RedBlueTeamOrchestrator()
        self.review = WeeklyReviewEngine(self.registry, self.detector, self.alerts)
        self.worrylog = WorryLogManager()
    def submit_metrics(self, metrics: Dict[str,float]) -> Dict[str,Any]:
        det=self.detector.ingest(metrics); fired=[]
        for mn,mv in metrics.items(): fired.extend(self.alerts.evaluate_metric(mn,mv))
        mitigations=[]
        if det and det.id!="none":
            action=self.engine.auto_mitigate(det); mitigations.append({"action_id":action.id,"type":action.action_type.value})
        for f in fired:
            action=self.engine.execute(f.category,f); mitigations.append({"action_id":action.id,"type":action.action_type.value})
        return {"detections":len(self.detector.active()),"alerts_fired":len(fired),"mitigations":len(mitigations),"actions":mitigations}
    def run_health_check(self) -> RiskDashboardSnapshot:
        reg_stats=self.registry.stats(); act_alerts=len(self.alerts.active_alerts()); act_det=len(self.detector.active())
        chaos_stats=self.chaos.simulator_stats(); defense=self.redblue.get_defense_score()
        resilience=chaos_stats.get("avg_resilience",75.0)
        health=100-reg_stats["open"]*0.5-reg_stats["critical_open"]*5-(10 if act_alerts>5 else 0)
        health=max(0,min(100,health))
        return RiskDashboardSnapshot(reg_stats["total"],reg_stats["open"],reg_stats["critical_open"],
            round(health,1),act_alerts,act_det,resilience,defense)
    def run_full_review(self, num_plans: int=14) -> Dict[str,Any]: return self.review.full_review()
    def run_chaos_suite(self, plan_ids: Optional[List[int]]=None) -> Dict[str,Any]:
        targets=["scheduler_worker","memory_cache","personality_engine","crawler_agent",
            "quant_model","auth_gateway","primary_db","api_gateway","sdk_service",
            "mobile_backend","i18n_service","compliance_engine","billing_system",
            "growth_pipeline","ai_inference_server"]
        types=list(ChaosInjectionType); results=[]
        for i,t in enumerate(types[:len(plan_ids or [1,2,3])]):
            exp=self.chaos.design_experiment(t,targets[i%len(targets)],60)
            res=self.chaos.run_experiment(exp.id); results.append(res)
        return {"experiments":results,"avg_resilience":round(sum(r.get("resilience_score",0) for r in results)/max(len(results),1),1)}
    def get_full_status(self) -> Dict[str,Any]:
        dash=self.run_health_check()
        return {"dashboard":{"total_risks":dash.total_risks,"open_count":dash.open_count,
            "critical_open":dash.critical_open,"overall_health_pct":dash.overall_health_pct,
            "active_alerts":dash.active_alerts,"active_detections":dash.active_detections,
            "resilience_score":dash.resilience_score,"defense_score":dash.defense_score},
            "registry":self.registry.stats(),"detector":self.detector.detector_stats(),
            "engine":self.engine.engine_stats(),"alerts":self.alerts.alert_stats(),
            "chaos":self.chaos.simulator_stats(),"redblue":self.redblue.orchestrator_stats(),
            "worrylog":self.worrylog.log_stats()}


# ═══════════════════════════════════════════════════════════════
# PART J — TESTING SUITE
# ═══════════════════════════════════════════════════════════════

def _run_test(name: str, fn) -> tuple:
    try: fn(); return ("PASS", name, None)
    except Exception as e: return ("FAIL", name, str(e))

def run_all_tests() -> Dict[str,Any]:
    results=[]

    def test_registry_builtin():
        reg=RiskRegistry(); assert len(reg.all_risks())==42
        assert len(reg.by_plan(1))==3; assert len(reg.by_plan(14))==3
    results.append(_run_test("REG: 42 built-in risks", test_registry_builtin))

    def test_registry_scoring():
        reg=RiskRegistry(); r=reg.get("R_P01_001")
        assert r is not None; score=reg.compute_score(r.id)
        raw=r.probability*r.impact*100; assert score>=raw
    results.append(_run_test("REG: scoring formula", test_registry_scoring))

    def test_registry_custom():
        reg=RiskRegistry(); c=reg.register_custom(99,"test_cat","Test","desc",0.5,0.5,RiskSeverity.LOW)
        assert c.id.startswith("CUSTOM_"); assert len(reg.all_risks())==43
    results.append(_run_test("REG: custom registration", test_registry_custom))

    def test_registry_update_status():
        reg=RiskRegistry(); assert reg.update_status("R_P01_001",RiskStatus.RESOLVED)
        s=reg.compute_score("R_P01_001"); assert s<reg.get("R_P01_001").probability*reg.get("R_P01_001").impact*100
    results.append(_run_test("REG: status update affects score", test_registry_update_status))

    def test_detector_ingest():
        reg=RiskRegistry(); det=ProblemOrientedDetector(reg)
        r=det.ingest({"scheduler_cpu_usage":95.0,"heap_growth_mb":600.0}); assert r.id!="none"
    results.append(_run_test("DET: ingest detects problems", test_detector_ingest))

    def test_detector_no_issue():
        reg=RiskRegistry(); det=ProblemOrientedDetector(reg)
        r=det.ingest({"scheduler_cpu_usage":50.0}); assert r.id=="none"
    results.append(_run_test("DET: no issue when healthy", test_detector_no_issue))

    def test_detector_ack_resolve():
        reg=RiskRegistry(); det=ProblemOrientedDetector(reg)
        r=det.ingest({"pending_tasks":2000}); assert det.acknowledge(r.id); assert det.resolve(r.id)
    results.append(_run_test("DET: ack+resolve lifecycle", test_detector_ack_resolve))

    def test_detector_stats():
        reg=RiskRegistry(); det=ProblemOrientedDetector(reg)
        det.ingest({"app_crash_rate":0.01}); st=det.detector_stats(); assert st["active"]>=1
    results.append(_run_test("DET: stats aggregation", test_detector_stats))

    def test_mitigation_execute():
        reg=RiskRegistry(); eng=MitigationStrategyEngine(reg)
        a=eng.execute("scheduler_cpu"); assert a.action_type==MitigationActionType.AUTO_SCALE
    results.append(_run_test("ENG: execute maps to action", test_mitigation_execute))

    def test_mitigation_unknown():
        reg=RiskRegistry(); eng=MitigationStrategyEngine(reg)
        a=eng.execute("UNKNOWN_CAT"); assert a.action_type==MitigationActionType.ALERT_HUMAN
    results.append(_run_test("ENG: unknown→ALERT_HUMAN fallback", test_mitigation_unknown))

    def test_mitigation_history():
        reg=RiskRegistry(); eng=MitigationStrategyEngine(reg)
        eng.execute("memory_leak_core"); eng.execute("security_prompt_inj")
        assert len(eng.history())==2
    results.append(_run_test("ENG: history tracking", test_mitigation_history))

    def test_mitigation_rollback():
        reg=RiskRegistry(); eng=MitigationStrategyEngine(reg)
        a=eng.execute("scheduler_cpu"); assert eng.rollback(a.id); assert not a.success
    results.append(_run_test("ENG: rollback marks failed", test_mitigation_rollback))

    def test_alert_fire():
        alt=MonitoringAlertSystem(); fired=alt.evaluate_metric("scheduler_cpu_usage",95.0)
        assert len(fired)>=1; assert fired[0].state==AlertState.FIRING
    results.append(_run_test("ALT: fire on threshold breach", test_alert_fire))

    def test_alert_cooldown():
        alt=MonitoringAlertSystem(); alt.evaluate_metric("scheduler_cpu_usage",95.0)
        fired2=alt.evaluate_metric("scheduler_cpu_usage",98.0); assert len(fired2)==0
    results.append(_run_test("ALT: cooldown prevents duplicate", test_alert_cooldown))

    def test_alert_ack_resolve():
        alt=MonitoringAlertSystem(); fired=alt.evaluate_metric("injection_attempt_count",5)
        assert len(fired)>0; aid=fired[0].id; assert alt.acknowledge_alert(aid); assert alt.resolve_alert(aid)
    results.append(_run_test("ALT: ack+resolve lifecycle", test_alert_ack_resolve))

    def test_alert_active():
        alt=MonitoringAlertSystem(); alt.evaluate_metric("mape_3day",0.2)
        assert len(alt.active_alerts())>=1
    results.append(_run_test("ALT: active alerts query", test_alert_active))

    def test_alert_stats():
        alt=MonitoringAlertSystem(); st=alt.alert_stats(); assert st["total_rules"]==42
    results.append(_run_test("ALT: 42 rules count", test_alert_stats))

    def test_chaos_design_run():
        sim=ChaosEngineeringSimulator()
        exp=sim.design_experiment(ChaosInjectionType.NODE_KILL,"web_server",30)
        res=sim.run_experiment(exp.id); assert res["success"] is not None
    results.append(_run_test("CHAOS: design+run experiment", test_chaos_design_run))

    def test_chaos_resilience():
        sim=ChaosEngineeringSimulator()
        exp=sim.design_experiment(ChaosInjectionType.NETWORK_LATENCY,"api_gateway",60)
        res=sim.run_experiment(exp.id); assert 0<=res["resilience_score"]<=100
    results.append(_run_test("CHAOS: resilience score bounds", test_chaos_resilience))

    def test_chaos_list():
        sim=ChaosEngineeringSimulator()
        sim.design_experiment(ChaosInjectionType.CPU_SPIKE,"worker",60)
        assert len(sim.list_experiments())==1
    results.append(_run_test("CHAOS: list experiments", test_chaos_list))

    def test_redblue_design_run():
        rb=RedBlueTeamOrchestrator()
        ex=rb.design_exercise(RedTeamAttackType.PROMPT_INJECTION,"chat_interface")
        res=rb.run_exercise(ex.id); assert "defense_score" in res
    results.append(_run_test("RB: design+run exercise", test_redblue_design_run))

    def test_redblue_defense_agg():
        rb=RedBlueTeamOrchestrator()
        for t in list(RedTeamAttackType)[:3]:
            ex=rb.design_exercise(t,"target"); rb.run_exercise(ex.id)
        ds=rb.get_defense_score(); assert 0<=ds<=100
    results.append(_run_test("RB: defense score aggregate", test_redblue_defense_agg))

    def test_weekly_review_single():
        reg=RiskRegistry(); det=ProblemOrientedDetector(reg); alt=MonitoringAlertSystem()
        eng=WeeklyReviewEngine(reg,det,alt); rep=eng.generate_report(1)
        assert 0<=rep.health_score<=100; assert rep.outcome in list(ReviewOutcome)
    results.append(_run_test("REV: single plan report", test_weekly_review_single))

    def test_weekly_review_full():
        reg=RiskRegistry(); det=ProblemOrientedDetector(reg); alt=MonitoringAlertSystem()
        eng=WeeklyReviewEngine(reg,det,alt); fr=eng.full_review()
        assert len(fr["plans"])==14; assert "average_health" in fr
    results.append(_run_test("REV: full 14-plan review", test_weekly_review_full))

    def test_worry_log_basic():
        wl=WorryLogManager()
        e=wl.log_incident("plan_1",RiskSeverity.CRITICAL,"Test incident","details",["urgent"])
        assert e.id in wl._logs
    results.append(_run_test("WLOG: log incident", test_worry_log_basic))

    def test_worry_log_resolve():
        wl=WorryLogManager()
        e=wl.log_incident("plan_1","a","t",RiskSeverity.CRITICAL,"d",["p1"])
        re=wl.resolve_entry(e.id); assert re is not None and re.resolved
    results.append(_run_test("WLOG: resolve entry", test_worry_log_resolve))

    def test_worry_log_search():
        wl=WorryLogManager()
        for i in range(5): wl.log_incident(f"plan_{(i%14)+1}",RiskSeverity.HIGH,f"test {i}",["tag_a"])
        found=wl.search_logs(plan_id="plan_1"); assert len(found)>=1
    results.append(_run_test("WLOG: search by plan", test_worry_log_search))

    def test_worry_log_trend():
        wl=WorryLogManager()
        for i in range(10): wl.log_incident(f"plan_{(i%14)+1}",RiskSeverity.MEDIUM,f"trend_{i}")
        tr=wl.get_trend(7); assert "daily_counts" in tr
    results.append(_run_test("WLOG: trend analysis", test_worry_log_trend))

    def test_orchestrator_init():
        orc=RiskAwarenessOrchestrator()
        assert orc.registry.stats()["total"]>=42; assert orc.alerts.alert_stats()["total_rules"]==42
    results.append(_run_test("ORC: init wires all modules", test_orchestrator_init))

    def test_orchestrator_submit():
        orc=RiskAwarenessOrchestrator()
        result=orc.submit_metrics({"scheduler_cpu_usage":92.0,"crawl_success_rate":0.88,"mape_3day":0.15,"app_crash_rate":0.008})
        assert result["detections"]>=1; assert result["mitigations"]>=0
    results.append(_run_test("ORC: submit metrics", test_orchestrator_submit))

    def test_orchestrator_health():
        orc=RiskAwarenessOrchestrator()
        dash=orc.run_health_check(); assert dash.total_risks>=42; assert 0<=dash.overall_health_pct<=100
    results.append(_run_test("ORC: health check dashboard", test_orchestrator_health))

    def test_orchestrator_review():
        orc=RiskAwarenessOrchestrator(); rev=orc.run_full_review(7); assert "plans" in rev
    results.append(_run_test("ORC: full review", test_orchestrator_review))

    def test_orchestrator_chaos():
        orc=RiskAwarenessOrchestrator()
        suite=orc.run_chaos_suite([1,3]); assert "experiments" in suite; assert len(suite["experiments"])>=2
    results.append(_run_test("ORC: chaos suite", test_orchestrator_chaos))

    def test_orchestrator_metrics():
        orc=RiskAwarenessOrchestrator()
        status=orc.get_full_status(); assert "dashboard" in status; assert "registry" in status
        assert status["dashboard"]["total_risks"]>=42
    results.append(_run_test("ORC: full status", test_orchestrator_metrics))

    def test_worry_log_search_resolve():
        mgr=WorryLogManager()
        for i in range(5): mgr.log_incident(f"plan_{(i%14)+1}",RiskSeverity.HIGH,f"inc {i}",["tag_a","tag_b"])
        found=mgr.search_logs(plan_id="plan_1"); assert len(found)>=1
        resolved=mgr.resolve_entry(found[0].id); assert resolved.resolved_at is not None
    results.append(_run_test("WorryLog: search+resolve", test_worry_log_search_resolve))

    def test_worry_log_trend_detail():
        mgr=WorryLogManager()
        for i in range(10): mgr.log_incident(f"plan_{(i%14)+1}",RiskSeverity.MEDIUM,f"tr_{i}")
        trend=mgr.get_trend(days=7); assert "by_severity" in trend
    results.append(_run_test("WorryLog: trend detail", test_worry_log_trend_detail))

    def test_edge_empty_inputs():
        reg=RiskRegistry()
        assert reg.get("NONEXISTENT") is None
        det=ProblemOrientedDetector(reg); r=det.ingest({}); assert r.id=="none"
        eng=MitigationStrategyEngine(reg); a=eng.execute("NO_SUCH_CATEGORY",None)
        assert a.action_type==MitigationActionType.ALERT_HUMAN
    results.append(_run_test("Edge cases: empty inputs", test_edge_empty_inputs))

    def test_edge_score_boundaries():
        reg=RiskRegistry(); risk=reg.get("R_P01_001")
        raw=risk.probability*risk.impact*100; assert 0<=raw<=10000
        score=reg.compute_score(risk.id); assert 0<=score<=15000
    results.append(_run_test("Edge cases: score boundaries", test_edge_score_boundaries))

    passed=sum(1 for r in results if r[0]=="PASS")
    failed=[r for r in results if r[0]=="FAIL"]; errors=[r for r in results if r[0]=="ERROR"]
    print(f"\n{'='*60}")
    print(f"L36 RISK AWARENESS DEFENSE LAYER — TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Total : {len(results)}")
    print(f"  Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"  Failed: {len(failed)}")
    if failed:
        for _,name,err in failed: print(f"    ✗ {name}: {err}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for _,name,err in errors: print(f"    ! {name}: {err}")
    print(f"{'='*60}")
    return {"total":len(results),"passed":passed,"failed":len(failed),"errors":len(errors),"results":results}

if __name__ == "__main__":
    run_all_tests()
    print("\n✅ Layer 36 — Risk Awareness & Problem-Oriented Defense System loaded OK")
