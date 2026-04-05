"""
反击指挥中心
Counter Strike Command Center

协调所有反击智能体，实现OODA循环
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class SystemState(Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    ALERTED = "alerted"
    RESPONDING = "responding"
    COUNTER_STRIKING = "counter_striking"
    STAND_DOWN = "stand_down"


class OODAPhase(Enum):
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"


@dataclass
class ThreatAssessment:
    assessment_id: str
    threat_level: int
    confidence: float
    attacker_identity: Optional[str]
    attack_type: str
    target_assets: List[str]
    recommended_actions: List[str]
    created_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            "assessment_id": self.assessment_id,
            "threat_level": self.threat_level,
            "confidence": self.confidence,
            "attacker_identity": self.attacker_identity,
            "attack_type": self.attack_type,
            "target_assets": self.target_assets,
            "recommended_actions": self.recommended_actions,
            "created_at": self.created_at.isoformat()
        }


class CounterStrikeCommandCenter:
    def __init__(
        self,
        center_id: str = "command_center_001",
        redis_client: Optional[Any] = None,
        db_client: Optional[Any] = None
    ):
        self.center_id = center_id
        self.redis_client = redis_client
        self.db_client = db_client
        
        self.system_state = SystemState.IDLE
        self.current_ooda_phase = OODAPhase.OBSERVE
        
        self.agents: Dict[str, Any] = {}
        self.agent_status: Dict[str, str] = {}
        
        self.active_threats: Dict[str, Dict] = {}
        self.threat_assessments: deque = deque(maxlen=200)
        self.operation_log: deque = deque(maxlen=1000)
        
        self.stats = {
            "threats_detected": 0,
            "threats_neutralized": 0,
            "counter_strikes_executed": 0,
            "avg_response_time_ms": 0.0,
            "system_uptime_seconds": 0
        }
        
        self._start_time = time.time()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._command_loop())
        logger.info(f"CounterStrikeCommandCenter {self.center_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'stop'):
                await agent.stop()
                
        logger.info(f"CounterStrikeCommandCenter {self.center_id} stopped")
        
    async def _command_loop(self):
        while self._running:
            try:
                await self._run_ooda_cycle()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in command loop: {e}")
                await asyncio.sleep(5)
                
    async def _run_ooda_cycle(self):
        if self.current_ooda_phase == OODAPhase.OBSERVE:
            await self._observe_phase()
        elif self.current_ooda_phase == OODAPhase.ORIENT:
            await self._orient_phase()
        elif self.current_ooda_phase == OODAPhase.DECIDE:
            await self._decide_phase()
        elif self.current_ooda_phase == OODAPhase.ACT:
            await self._act_phase()
            
    async def _observe_phase(self):
        recon_agent = self.agents.get("recon")
        if not recon_agent:
            self.current_ooda_phase = OODAPhase.OBSERVE
            return
            
        recent_reports = await recon_agent.get_recent_reports(limit=5)
        
        if recent_reports:
            for report in recent_reports:
                threat_id = report.get("report_id")
                if threat_id and threat_id not in self.active_threats:
                    self.active_threats[threat_id] = report
                    self.stats["threats_detected"] += 1
                    self.system_state = SystemState.ALERTED
                    
        if self.active_threats:
            self.current_ooda_phase = OODAPhase.ORIENT
        else:
            self.system_state = SystemState.MONITORING
            
    async def _orient_phase(self):
        trace_agent = self.agents.get("trace")
        attribution_agent = self.agents.get("attribution")
        
        for threat_id, threat in list(self.active_threats.items()):
            if threat.get("assessed"):
                continue
                
            attacker_profile = threat.get("attacker_profile", {})
            
            assessment = ThreatAssessment(
                assessment_id=self._generate_assessment_id(),
                threat_level=threat.get("threat_level", 1),
                confidence=threat.get("confidence", 0.5),
                attacker_identity=attacker_profile.get("attacker_id"),
                attack_type=threat.get("detected_attack_types", ["unknown"])[0] if threat.get("detected_attack_types") else "unknown",
                target_assets=list(attacker_profile.get("target_preferences", {}).keys())[:5],
                recommended_actions=threat.get("recommended_actions", []),
                created_at=datetime.now()
            )
            
            self.threat_assessments.append(assessment.to_dict())
            threat["assessment"] = assessment.to_dict()
            threat["assessed"] = True
            
        if any(t.get("assessed") for t in self.active_threats.values()):
            self.current_ooda_phase = OODAPhase.DECIDE
            self.system_state = SystemState.RESPONDING
            
    async def _decide_phase(self):
        tactical_library = self.agents.get("tactical_library")
        boundary_controller = self.agents.get("boundary")
        
        for threat_id, threat in list(self.active_threats.items()):
            if threat.get("action_decided"):
                continue
                
            assessment = threat.get("assessment", {})
            
            if tactical_library:
                recommended = await tactical_library.recommend_tactics({
                    "attack_type": assessment.get("attack_type"),
                    "threat_level": assessment.get("threat_level"),
                    "confidence": assessment.get("confidence")
                })
                
                if recommended:
                    threat["recommended_tactics"] = [
                        {"tactic_id": t.tactic_id, "score": s}
                        for t, s in recommended
                    ]
                    
            threat["action_decided"] = True
            
        if any(t.get("action_decided") for t in self.active_threats.values()):
            self.current_ooda_phase = OODAPhase.ACT
            
    async def _act_phase(self):
        executor = self.agents.get("executor")
        
        for threat_id, threat in list(self.active_threats.items()):
            if threat.get("action_executed"):
                continue
                
            tactics = threat.get("recommended_tactics", [])
            
            if tactics and executor:
                tactic = tactics[0]
                
                result = await executor.execute_tactic(
                    tactic_id=tactic["tactic_id"],
                    target_identity=threat.get("attacker_profile", {}).get("attacker_id", "unknown"),
                    custom_params={"threat_id": threat_id}
                )
                
                threat["execution_result"] = result.to_dict() if hasattr(result, 'to_dict') else result
                self.stats["counter_strikes_executed"] += 1
                
            threat["action_executed"] = True
            
            if threat.get("execution_result", {}).get("effectiveness_score", 0) > 0.5:
                self.stats["threats_neutralized"] += 1
                
        self.current_ooda_phase = OODAPhase.OBSERVE
        self.system_state = SystemState.MONITORING
        
        completed_threats = [
            tid for tid, t in self.active_threats.items()
            if t.get("action_executed")
        ]
        
        for tid in completed_threats:
            self._log_operation(self.active_threats[tid])
            del self.active_threats[tid]
            
    def register_agent(self, agent_type: str, agent: Any):
        self.agents[agent_type] = agent
        self.agent_status[agent_type] = "registered"
        logger.info(f"Registered agent: {agent_type}")
        
    async def process_traffic(self, traffic_data: Dict) -> Optional[Dict]:
        recon_agent = self.agents.get("recon")
        if not recon_agent:
            return None
            
        report = await recon_agent.process_traffic(traffic_data)
        
        if report:
            self.system_state = SystemState.ALERTED
            self._log_operation({
                "type": "traffic_processed",
                "report_id": report.report_id,
                "timestamp": datetime.now().isoformat()
            })
            
        return report.to_dict() if report else None
        
    async def get_system_status(self) -> Dict:
        return {
            "center_id": self.center_id,
            "system_state": self.system_state.value,
            "current_ooda_phase": self.current_ooda_phase.value,
            "active_threats": len(self.active_threats),
            "registered_agents": list(self.agents.keys()),
            "agent_status": self.agent_status,
            "uptime_seconds": time.time() - self._start_time,
            "stats": self.stats
        }
        
    async def get_active_threats(self) -> List[Dict]:
        return list(self.active_threats.values())
        
    async def get_recent_assessments(self, limit: int = 20) -> List[Dict]:
        return list(self.threat_assessments)[-limit:]
        
    def _log_operation(self, operation: Dict):
        self.operation_log.append({
            **operation,
            "logged_at": datetime.now().isoformat()
        })
        
    def _generate_assessment_id(self) -> str:
        return f"assess_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "system_uptime_seconds": time.time() - self._start_time,
            "active_threats": len(self.active_threats)
        }
