"""
业务技能传承机制
Business Skill Transfer Mechanism

让优秀智能体将技能传授给新智能体
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

logger = logging.getLogger(__name__)


class TransferStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransferType(Enum):
    FULL = "full"
    PARTIAL = "partial"
    BEHAVIOR_CLONING = "behavior_cloning"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"


@dataclass
class TeacherStudentPair:
    pair_id: str
    teacher_id: str
    student_id: str
    created_at: float
    status: str = "active"
    sessions_completed: int = 0
    sessions_failed: int = 0
    total_knowledge_transferred: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "pair_id": self.pair_id,
            "teacher_id": self.teacher_id,
            "student_id": self.student_id,
            "created_at": self.created_at,
            "status": self.status,
            "sessions_completed": self.sessions_completed,
            "sessions_failed": self.sessions_failed,
            "total_knowledge_transferred": self.total_knowledge_transferred,
            "metadata": self.metadata
        }


@dataclass
class TransferSession:
    session_id: str
    pair_id: str
    teacher_id: str
    student_id: str
    transfer_type: TransferType
    knowledge_modules: List[str]
    energy_cost: float
    energy_paid: float
    status: TransferStatus
    started_at: float
    completed_at: Optional[float] = None
    test_results: Optional[Dict] = None
    success_score: float = 0.0
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "pair_id": self.pair_id,
            "teacher_id": self.teacher_id,
            "student_id": self.student_id,
            "transfer_type": self.transfer_type.value,
            "knowledge_modules": self.knowledge_modules,
            "energy_cost": self.energy_cost,
            "energy_paid": self.energy_paid,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "test_results": self.test_results,
            "success_score": self.success_score,
            "error": self.error,
            "metadata": self.metadata
        }


class SkillTransferMechanism:
    """
    业务技能传承机制
    
    让优秀智能体将技能传授给新智能体：
    1. 教师-学生模式：老智能体成为教师
    2. 传授方式：策略网络参数分享、模仿学习
    3. 传授成本：教师消耗能量，学生支付能量
    4. 传授效果评估：测试任务验证
    5. 与海马体交互：记录师徒关系图谱
    """
    
    DEFAULT_ENERGY_COST = 20.0
    MIN_TEACHER_EXPERIENCE = 50
    MIN_TEACHER_SUCCESS_RATE = 0.7
    TEST_TASK_COUNT = 5
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        task_market: Optional[Any] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.task_market = task_market
        
        self.pairs: Dict[str, TeacherStudentPair] = {}
        self.sessions: Dict[str, TransferSession] = {}
        
        self.teacher_registry: Dict[str, Dict] = {}
        self.student_registry: Dict[str, Dict] = {}
        
        self.apprenticeship_graph: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.RLock()
        self._running = False
        
        self.stats = {
            "pairs_formed": 0,
            "sessions_started": 0,
            "sessions_completed": 0,
            "sessions_failed": 0,
            "total_knowledge_transferred": 0.0,
            "total_energy_transferred": 0.0,
            "avg_success_score": 0.0,
        }
    
    async def start(self):
        self._running = True
        logger.info("Skill transfer mechanism started")
    
    async def stop(self):
        self._running = False
        logger.info("Skill transfer mechanism stopped")
    
    def register_teacher(
        self,
        agent_id: str,
        specialties: List[str],
        experience_count: int,
        success_rate: float,
        energy_rate: float = 10.0,
    ) -> bool:
        if experience_count < self.MIN_TEACHER_EXPERIENCE:
            logger.warning(f"Agent {agent_id} lacks experience for teaching")
            return False
        
        if success_rate < self.MIN_TEACHER_SUCCESS_RATE:
            logger.warning(f"Agent {agent_id} success rate too low for teaching")
            return False
        
        with self._lock:
            self.teacher_registry[agent_id] = {
                "agent_id": agent_id,
                "specialties": specialties,
                "experience_count": experience_count,
                "success_rate": success_rate,
                "energy_rate": energy_rate,
                "teaching_sessions": 0,
                "total_students": 0,
                "avg_student_improvement": 0.0,
                "registered_at": time.time(),
            }
        
        logger.info(f"Teacher registered: {agent_id}")
        return True
    
    def unregister_teacher(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self.teacher_registry:
                del self.teacher_registry[agent_id]
                return True
        return False
    
    def register_student(
        self,
        agent_id: str,
        learning_goals: List[str],
        current_level: float = 0.0,
        energy_budget: float = 50.0,
    ) -> bool:
        with self._lock:
            self.student_registry[agent_id] = {
                "agent_id": agent_id,
                "learning_goals": learning_goals,
                "current_level": current_level,
                "energy_budget": energy_budget,
                "learning_sessions": 0,
                "total_knowledge_gained": 0.0,
                "registered_at": time.time(),
            }
        
        logger.info(f"Student registered: {agent_id}")
        return True
    
    def unregister_student(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self.student_registry:
                del self.student_registry[agent_id]
                return True
        return False
    
    def find_teacher(
        self,
        student_id: str,
        learning_goals: List[str],
        min_success_rate: float = 0.7,
    ) -> List[Dict]:
        student = self.student_registry.get(student_id)
        if not student:
            return []
        
        matching_teachers = []
        
        for teacher_id, teacher_info in self.teacher_registry.items():
            if teacher_info["success_rate"] < min_success_rate:
                continue
            
            specialty_match = len(
                set(teacher_info["specialties"]) & set(learning_goals)
            )
            
            if specialty_match > 0:
                matching_teachers.append({
                    **teacher_info,
                    "specialty_match": specialty_match,
                    "match_score": (
                        specialty_match * 0.4 +
                        teacher_info["success_rate"] * 0.3 +
                        min(1.0, teacher_info["experience_count"] / 100) * 0.3
                    )
                })
        
        matching_teachers.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matching_teachers[:5]
    
    async def form_pair(
        self,
        teacher_id: str,
        student_id: str,
    ) -> Optional[TeacherStudentPair]:
        if teacher_id not in self.teacher_registry:
            logger.warning(f"Teacher not registered: {teacher_id}")
            return None
        
        if student_id not in self.student_registry:
            logger.warning(f"Student not registered: {student_id}")
            return None
        
        pair_id = f"pair_{uuid.uuid4().hex[:8]}"
        
        pair = TeacherStudentPair(
            pair_id=pair_id,
            teacher_id=teacher_id,
            student_id=student_id,
            created_at=time.time(),
        )
        
        with self._lock:
            self.pairs[pair_id] = pair
            self.apprenticeship_graph[teacher_id].append(student_id)
            self.stats["pairs_formed"] += 1
        
        logger.info(f"Pair formed: {teacher_id} -> {student_id}")
        
        return pair
    
    async def start_transfer(
        self,
        pair_id: str,
        transfer_type: TransferType = TransferType.PARTIAL,
        knowledge_modules: Optional[List[str]] = None,
        energy_budget: Optional[float] = None,
    ) -> Optional[TransferSession]:
        if pair_id not in self.pairs:
            logger.warning(f"Pair not found: {pair_id}")
            return None
        
        pair = self.pairs[pair_id]
        
        teacher = self.teacher_registry.get(pair.teacher_id)
        student = self.student_registry.get(pair.student_id)
        
        if not teacher or not student:
            return None
        
        session_id = f"transfer_{uuid.uuid4().hex[:8]}"
        
        if knowledge_modules is None:
            knowledge_modules = list(
                set(teacher["specialties"]) & set(student["learning_goals"])
            )[:3]
        
        energy_cost = self.DEFAULT_ENERGY_COST * len(knowledge_modules)
        
        if energy_budget is not None:
            energy_cost = min(energy_cost, energy_budget)
        
        session = TransferSession(
            session_id=session_id,
            pair_id=pair_id,
            teacher_id=pair.teacher_id,
            student_id=pair.student_id,
            transfer_type=transfer_type,
            knowledge_modules=knowledge_modules,
            energy_cost=energy_cost,
            energy_paid=0.0,
            status=TransferStatus.PENDING,
            started_at=time.time(),
        )
        
        with self._lock:
            self.sessions[session_id] = session
            self.stats["sessions_started"] += 1
        
        asyncio.create_task(self._execute_transfer(session))
        
        return session
    
    async def _execute_transfer(self, session: TransferSession):
        session.status = TransferStatus.IN_PROGRESS
        
        try:
            teacher = self.teacher_registry.get(session.teacher_id)
            student = self.student_registry.get(session.student_id)
            
            if not teacher or not student:
                raise ValueError("Teacher or student not found")
            
            knowledge_package = await self._extract_knowledge(
                session.teacher_id,
                session.knowledge_modules
            )
            
            transfer_success = await self._transfer_knowledge(
                session.student_id,
                knowledge_package,
                session.transfer_type
            )
            
            if not transfer_success:
                raise RuntimeError("Knowledge transfer failed")
            
            session.energy_paid = session.energy_cost
            
            test_results = await self._conduct_tests(
                session.student_id,
                session.knowledge_modules
            )
            
            session.test_results = test_results
            session.success_score = test_results.get("overall_score", 0.0)
            
            if session.success_score >= 0.6:
                session.status = TransferStatus.COMPLETED
                
                pair = self.pairs.get(session.pair_id)
                if pair:
                    pair.sessions_completed += 1
                    pair.total_knowledge_transferred += session.success_score
                
                teacher["teaching_sessions"] += 1
                teacher["total_students"] = len(set(
                    s.student_id for s in self.sessions.values()
                    if s.teacher_id == session.teacher_id and s.status == TransferStatus.COMPLETED
                ))
                
                student["learning_sessions"] += 1
                student["total_knowledge_gained"] += session.success_score
                
                self.stats["sessions_completed"] += 1
                self.stats["total_knowledge_transferred"] += session.success_score
                self.stats["total_energy_transferred"] += session.energy_paid
                
                total = self.stats["sessions_completed"]
                old_avg = self.stats["avg_success_score"]
                self.stats["avg_success_score"] = (
                    old_avg * (total - 1) + session.success_score
                ) / total
            else:
                session.status = TransferStatus.FAILED
                session.error = f"Test score too low: {session.success_score}"
                
                pair = self.pairs.get(session.pair_id)
                if pair:
                    pair.sessions_failed += 1
                
                self.stats["sessions_failed"] += 1
            
        except Exception as e:
            logger.error(f"Transfer session failed: {e}")
            session.status = TransferStatus.FAILED
            session.error = str(e)
            self.stats["sessions_failed"] += 1
        
        finally:
            session.completed_at = time.time()
            
            if self.memory_agent:
                await self._store_transfer_record(session)
    
    async def _extract_knowledge(
        self,
        teacher_id: str,
        modules: List[str],
    ) -> Dict:
        knowledge = {
            "teacher_id": teacher_id,
            "modules": {},
            "extracted_at": time.time(),
        }
        
        for module in modules:
            knowledge["modules"][module] = {
                "strategies": [
                    {"name": f"strategy_{i}", "weight": random.random()}
                    for i in range(5)
                ],
                "patterns": [
                    {"pattern": f"pattern_{i}", "frequency": random.randint(1, 10)}
                    for i in range(3)
                ],
                "heuristics": [
                    {"rule": f"rule_{i}", "confidence": random.random()}
                    for i in range(4)
                ],
            }
        
        return knowledge
    
    async def _transfer_knowledge(
        self,
        student_id: str,
        knowledge: Dict,
        transfer_type: TransferType,
    ) -> bool:
        await asyncio.sleep(0.1)
        
        if transfer_type == TransferType.FULL:
            transfer_rate = 0.9
        elif transfer_type == TransferType.PARTIAL:
            transfer_rate = 0.6
        elif transfer_type == TransferType.BEHAVIOR_CLONING:
            transfer_rate = 0.7
        else:
            transfer_rate = 0.5
        
        return random.random() < transfer_rate
    
    async def _conduct_tests(
        self,
        student_id: str,
        modules: List[str],
    ) -> Dict:
        results = {
            "tests_conducted": self.TEST_TASK_COUNT,
            "module_scores": {},
            "overall_score": 0.0,
        }
        
        total_score = 0.0
        for module in modules:
            module_score = random.uniform(0.5, 1.0)
            results["module_scores"][module] = module_score
            total_score += module_score
        
        results["overall_score"] = total_score / len(modules) if modules else 0.0
        
        return results
    
    async def _store_transfer_record(self, session: TransferSession):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "skill_transfer",
                    "session": session.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store transfer record: {e}")
    
    def get_pair(self, pair_id: str) -> Optional[TeacherStudentPair]:
        return self.pairs.get(pair_id)
    
    def get_session(self, session_id: str) -> Optional[TransferSession]:
        return self.sessions.get(session_id)
    
    def get_teacher_students(self, teacher_id: str) -> List[str]:
        return self.apprenticeship_graph.get(teacher_id, [])
    
    def get_student_teachers(self, student_id: str) -> List[str]:
        teachers = []
        for teacher_id, students in self.apprenticeship_graph.items():
            if student_id in students:
                teachers.append(teacher_id)
        return teachers
    
    def get_apprenticeship_tree(self) -> Dict:
        return dict(self.apprenticeship_graph)
    
    def get_teacher_stats(self, teacher_id: str) -> Optional[Dict]:
        teacher = self.teacher_registry.get(teacher_id)
        if not teacher:
            return None
        
        sessions = [
            s for s in self.sessions.values()
            if s.teacher_id == teacher_id
        ]
        
        completed = [s for s in sessions if s.status == TransferStatus.COMPLETED]
        
        return {
            **teacher,
            "total_sessions": len(sessions),
            "completed_sessions": len(completed),
            "avg_success_score": (
                sum(s.success_score for s in completed) / len(completed)
                if completed else 0.0
            ),
            "students": self.get_teacher_students(teacher_id),
        }
    
    def get_student_stats(self, student_id: str) -> Optional[Dict]:
        student = self.student_registry.get(student_id)
        if not student:
            return None
        
        sessions = [
            s for s in self.sessions.values()
            if s.student_id == student_id
        ]
        
        completed = [s for s in sessions if s.status == TransferStatus.COMPLETED]
        
        return {
            **student,
            "total_sessions": len(sessions),
            "completed_sessions": len(completed),
            "avg_success_score": (
                sum(s.success_score for s in completed) / len(completed)
                if completed else 0.0
            ),
            "teachers": self.get_student_teachers(student_id),
        }
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "registered_teachers": len(self.teacher_registry),
                "registered_students": len(self.student_registry),
                "active_pairs": len(self.pairs),
                "total_sessions": len(self.sessions),
            }
