"""
跨物种合作模块
Cross-Species Cooperation Module

实现跨部门任务分解、组合策略网络、全局经验回放等功能
"""

import asyncio
import hashlib
import json
import logging
import math
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class Department(Enum):
    LI = "li"
    GONG = "gong"
    HU = "hu"
    BING = "bing"
    LI2 = "li2"
    XING = "xing"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SubTask:
    task_id: str
    task_type: str
    department: Department
    params: Dict[str, Any]
    depends_on: List[str]
    status: TaskStatus
    assigned_agent: Optional[str]
    result: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "department": self.department.value,
            "params": self.params,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class TaskGraph:
    graph_id: str
    root_request: str
    subtasks: List[SubTask]
    created_at: datetime
    status: TaskStatus
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "root_request": self.root_request,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
        }
    
    def get_ready_tasks(self) -> List[SubTask]:
        ready = []
        completed_ids = {
            st.task_id for st in self.subtasks
            if st.status == TaskStatus.COMPLETED
        }
        
        for subtask in self.subtasks:
            if subtask.status != TaskStatus.PENDING:
                continue
            
            if all(dep_id in completed_ids for dep_id in subtask.depends_on):
                ready.append(subtask)
        
        return ready


@dataclass
class DepartmentCapability:
    department: Department
    task_types: List[str]
    max_concurrent: int
    current_load: int
    avg_completion_time: float
    success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "department": self.department.value,
            "task_types": self.task_types,
            "max_concurrent": self.max_concurrent,
            "current_load": self.current_load,
            "avg_completion_time": self.avg_completion_time,
            "success_rate": self.success_rate,
        }


class DepartmentCapabilityRegistry:
    """部门能力注册表"""
    
    def __init__(self):
        self.capabilities: Dict[Department, DepartmentCapability] = {}
        self._lock = threading.Lock()
        
        self._init_default_capabilities()
    
    def _init_default_capabilities(self):
        default_caps = [
            (Department.LI, ["policy_analysis", "decision_making", "coordination"], 5),
            (Department.GONG, ["analysis", "report_generation", "data_processing"], 10),
            (Department.HU, ["user_management", "data_storage", "statistics"], 8),
            (Department.BING, ["data_collection", "data_cleaning", "monitoring"], 15),
            (Department.LI2, ["scheduling", "resource_allocation", "audit"], 6),
            (Department.XING, ["enforcement", "violation_detection", "penalty"], 4),
        ]
        
        for dept, task_types, max_concurrent in default_caps:
            self.capabilities[dept] = DepartmentCapability(
                department=dept,
                task_types=task_types,
                max_concurrent=max_concurrent,
                current_load=0,
                avg_completion_time=1.0,
                success_rate=0.95,
            )
    
    def get_department_for_task(self, task_type: str) -> Optional[Department]:
        with self._lock:
            for dept, cap in self.capabilities.items():
                if task_type in cap.task_types and cap.current_load < cap.max_concurrent:
                    return dept
            return None
    
    def update_load(self, department: Department, delta: int):
        with self._lock:
            if department in self.capabilities:
                self.capabilities[department].current_load = max(
                    0,
                    self.capabilities[department].current_load + delta
                )
    
    def get_available_departments(self) -> List[DepartmentCapability]:
        with self._lock:
            return [
                cap for cap in self.capabilities.values()
                if cap.current_load < cap.max_concurrent
            ]
    
    def update_performance(
        self,
        department: Department,
        completion_time: float,
        success: bool
    ):
        with self._lock:
            if department in self.capabilities:
                cap = self.capabilities[department]
                alpha = 0.1
                cap.avg_completion_time = (
                    (1 - alpha) * cap.avg_completion_time + alpha * completion_time
                )
                
                if success:
                    cap.success_rate = min(1.0, cap.success_rate + 0.01)
                else:
                    cap.success_rate = max(0.0, cap.success_rate - 0.05)


class TaskDecomposer:
    """任务分解器"""
    
    def __init__(self, capability_registry: DepartmentCapabilityRegistry):
        self.capability_registry = capability_registry
        
        self.task_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        
        self._init_default_patterns()
        
        self.stats = {
            "total_decompositions": 0,
            "successful_decompositions": 0,
            "avg_subtasks": 0.0,
        }
    
    def _init_default_patterns(self):
        self.task_patterns = {
            "房价分析报告": [
                {"type": "data_collection", "params_key": "region"},
                {"type": "data_cleaning", "depends_on": [0]},
                {"type": "analysis", "depends_on": [1]},
                {"type": "report_generation", "depends_on": [2]},
            ],
            "用户画像分析": [
                {"type": "data_collection", "params_key": "user_data"},
                {"type": "data_processing", "depends_on": [0]},
                {"type": "analysis", "depends_on": [1]},
            ],
            "市场趋势预测": [
                {"type": "data_collection", "params_key": "market_data"},
                {"type": "statistics", "depends_on": [0]},
                {"type": "analysis", "depends_on": [1]},
                {"type": "report_generation", "depends_on": [2]},
            ],
            "违规检测": [
                {"type": "monitoring", "params_key": "target"},
                {"type": "violation_detection", "depends_on": [0]},
                {"type": "penalty", "depends_on": [1], "condition": "violation_found"},
            ],
        }
    
    def decompose(
        self,
        user_request: str,
        context: Dict[str, Any] = None
    ) -> TaskGraph:
        self.stats["total_decompositions"] += 1
        
        graph_id = f"tg_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        matched_pattern = self._match_pattern(user_request)
        
        if not matched_pattern:
            matched_pattern = [
                {"type": "data_collection"},
                {"type": "analysis", "depends_on": [0]},
                {"type": "report_generation", "depends_on": [1]},
            ]
        
        subtasks = []
        for i, pattern_item in enumerate(matched_pattern):
            task_type = pattern_item["type"]
            department = self.capability_registry.get_department_for_task(task_type)
            
            if not department:
                department = Department.GONG
            
            params = {}
            if "params_key" in pattern_item and context:
                params = context.get(pattern_item["params_key"], {})
            
            subtask = SubTask(
                task_id=f"st_{graph_id}_{i}",
                task_type=task_type,
                department=department,
                params=params,
                depends_on=[f"st_{graph_id}_{j}" for j in pattern_item.get("depends_on", [])],
                status=TaskStatus.PENDING,
                assigned_agent=None,
                result=None,
                created_at=datetime.now(),
                completed_at=None,
            )
            subtasks.append(subtask)
        
        graph = TaskGraph(
            graph_id=graph_id,
            root_request=user_request,
            subtasks=subtasks,
            created_at=datetime.now(),
            status=TaskStatus.PENDING,
        )
        
        self.stats["avg_subtasks"] = (
            (self.stats["avg_subtasks"] * (self.stats["total_decompositions"] - 1) + len(subtasks))
            / self.stats["total_decompositions"]
        )
        
        return graph
    
    def _match_pattern(self, request: str) -> Optional[List[Dict[str, Any]]]:
        request_lower = request.lower()
        
        for pattern_name, pattern in self.task_patterns.items():
            if pattern_name in request_lower:
                return pattern
        
        keywords = {
            "分析": ["analysis", "report_generation"],
            "报告": ["report_generation"],
            "预测": ["data_collection", "analysis", "report_generation"],
            "检测": ["monitoring", "violation_detection"],
            "收集": ["data_collection"],
        }
        
        matched_types = []
        for keyword, types in keywords.items():
            if keyword in request_lower:
                matched_types.extend(types)
        
        if matched_types:
            unique_types = list(dict.fromkeys(matched_types))
            return [{"type": t} for t in unique_types]
        
        return None
    
    def add_pattern(self, pattern_name: str, pattern: List[Dict[str, Any]]):
        with self._lock:
            self.task_patterns[pattern_name] = pattern


@dataclass
class TeamMember:
    agent_id: str
    department: Department
    role: str
    joined_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "department": self.department.value,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
        }


class TemporaryTeam:
    """临时团队"""
    
    def __init__(self, task_graph: TaskGraph):
        self.team_id = f"team_{task_graph.graph_id}"
        self.task_graph = task_graph
        self.members: Dict[str, TeamMember] = {}
        self.shared_context: Dict[str, Any] = {}
        self.message_log: List[Dict[str, Any]] = []
        
        self.created_at = datetime.now()
        self.status = TaskStatus.PENDING
        
        self._lock = threading.Lock()
        
        self.stats = {
            "messages_exchanged": 0,
            "tasks_completed": 0,
        }
    
    def add_member(
        self,
        agent_id: str,
        department: Department,
        role: str = "worker"
    ) -> bool:
        with self._lock:
            if agent_id in self.members:
                return False
            
            self.members[agent_id] = TeamMember(
                agent_id=agent_id,
                department=department,
                role=role,
                joined_at=datetime.now(),
            )
            
            return True
    
    def remove_member(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self.members:
                del self.members[agent_id]
                return True
            return False
    
    def update_shared_context(self, key: str, value: Any, source_agent: str):
        with self._lock:
            self.shared_context[key] = {
                "value": value,
                "source": source_agent,
                "timestamp": datetime.now().isoformat(),
            }
    
    def get_shared_context(self, key: str = None) -> Any:
        with self._lock:
            if key:
                return self.shared_context.get(key, {}).get("value")
            return self.shared_context
    
    def broadcast_message(
        self,
        sender_id: str,
        message_type: str,
        content: Dict[str, Any]
    ):
        with self._lock:
            message = {
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "sender_id": sender_id,
                "message_type": message_type,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.message_log.append(message)
            self.stats["messages_exchanged"] += 1
            
            return message
    
    def assign_task(self, subtask: SubTask, agent_id: str) -> bool:
        if agent_id not in self.members:
            return False
        
        subtask.assigned_agent = agent_id
        subtask.status = TaskStatus.ASSIGNED
        
        return True
    
    def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
        success: bool = True
    ):
        for subtask in self.task_graph.subtasks:
            if subtask.task_id == task_id:
                subtask.result = result
                subtask.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
                subtask.completed_at = datetime.now()
                
                self.stats["tasks_completed"] += 1
                
                if success:
                    self.update_shared_context(
                        f"result_{task_id}",
                        result,
                        subtask.assigned_agent
                    )
                
                break
    
    def is_complete(self) -> bool:
        return all(
            st.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for st in self.task_graph.subtasks
        )
    
    def get_final_result(self) -> Dict[str, Any]:
        results = {}
        for subtask in self.task_graph.subtasks:
            if subtask.status == TaskStatus.COMPLETED and subtask.result:
                results[subtask.task_type] = subtask.result
        
        return {
            "team_id": self.team_id,
            "status": "completed" if self.is_complete() else "in_progress",
            "results": results,
            "shared_context": self.shared_context,
            "stats": self.stats,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "task_graph": self.task_graph.to_dict(),
            "members": {aid: m.to_dict() for aid, m in self.members.items()},
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "stats": self.stats,
        }


@dataclass
class CrossSpeciesExperience:
    experience_id: str
    state: Dict[str, Any]
    actions: Dict[str, Any]
    reward: float
    next_state: Dict[str, Any]
    done: bool
    departments_involved: List[str]
    task_type: str
    timestamp: datetime
    priority: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "state": self.state,
            "actions": self.actions,
            "reward": self.reward,
            "next_state": self.next_state,
            "done": self.done,
            "departments_involved": self.departments_involved,
            "task_type": self.task_type,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
        }


class GlobalReplayBuffer:
    """全局经验回放池"""
    
    def __init__(
        self,
        max_size: int = 100000,
        priority_alpha: float = 0.6,
        priority_beta: float = 0.4
    ):
        self.max_size = max_size
        self.priority_alpha = priority_alpha
        self.priority_beta = priority_beta
        
        self.experiences: deque = deque(maxlen=max_size)
        self.priorities: deque = deque(maxlen=max_size)
        self.department_index: Dict[str, List[int]] = defaultdict(list)
        self.task_type_index: Dict[str, List[int]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_experiences": 0,
            "total_samples": 0,
            "avg_priority": 0.0,
        }
    
    def add(
        self,
        state: Dict[str, Any],
        actions: Dict[str, Any],
        reward: float,
        next_state: Dict[str, Any],
        done: bool,
        departments: List[str],
        task_type: str,
        td_error: float = None
    ) -> str:
        experience_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        experience = CrossSpeciesExperience(
            experience_id=experience_id,
            state=state,
            actions=actions,
            reward=reward,
            next_state=next_state,
            done=done,
            departments_involved=departments,
            task_type=task_type,
            timestamp=datetime.now(),
            priority=1.0,
        )
        
        priority = abs(td_error) if td_error is not None else 1.0
        priority = (priority + 1e-6) ** self.priority_alpha
        
        with self._lock:
            idx = len(self.experiences)
            self.experiences.append(experience)
            self.priorities.append(priority)
            
            for dept in departments:
                self.department_index[dept].append(idx)
            
            self.task_type_index[task_type].append(idx)
            
            self.stats["total_experiences"] += 1
        
        return experience_id
    
    def sample(
        self,
        batch_size: int,
        department_filter: List[str] = None,
        task_type_filter: str = None
    ) -> Tuple[List[CrossSpeciesExperience], List[int], List[float]]:
        with self._lock:
            if not self.experiences:
                return [], [], []
            
            if department_filter or task_type_filter:
                candidate_indices = set(range(len(self.experiences)))
                
                if department_filter:
                    dept_indices = set()
                    for dept in department_filter:
                        dept_indices.update(self.department_index.get(dept, []))
                    candidate_indices &= dept_indices
                
                if task_type_filter:
                    task_indices = set(self.task_type_index.get(task_type_filter, []))
                    candidate_indices &= task_indices
                
                candidate_indices = list(candidate_indices)
            else:
                candidate_indices = list(range(len(self.experiences)))
            
            if not candidate_indices:
                return [], [], []
            
            priorities = [self.priorities[i] for i in candidate_indices]
            total_priority = sum(priorities)
            
            if total_priority == 0:
                probs = [1.0 / len(priorities)] * len(priorities)
            else:
                probs = [p / total_priority for p in priorities]
            
            sample_size = min(batch_size, len(candidate_indices))
            sampled_positions = random.choices(
                range(len(candidate_indices)),
                weights=probs,
                k=sample_size
            )
            
            indices = [candidate_indices[pos] for pos in sampled_positions]
            experiences = [self.experiences[i] for i in indices]
            
            max_priority = max(self.priorities) if self.priorities else 1.0
            weights = [
                (len(self.experiences) * probs[pos]) ** (-self.priority_beta)
                for pos in sampled_positions
            ]
            max_weight = max(weights) if weights else 1.0
            weights = [w / max_weight for w in weights]
            
            self.stats["total_samples"] += 1
            
            return experiences, indices, weights
    
    def update_priorities(self, indices: List[int], td_errors: List[float]):
        with self._lock:
            for idx, td_error in zip(indices, td_errors):
                if 0 <= idx < len(self.priorities):
                    priority = (abs(td_error) + 1e-6) ** self.priority_alpha
                    self.priorities[idx] = priority
    
    def get_department_experiences(
        self,
        department: str,
        limit: int = 100
    ) -> List[CrossSpeciesExperience]:
        with self._lock:
            indices = self.department_index.get(department, [])[-limit:]
            return [self.experiences[i] for i in indices if i < len(self.experiences)]
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self.stats,
                "buffer_size": len(self.experiences),
                "departments_tracked": len(self.department_index),
                "task_types_tracked": len(self.task_type_index),
            }


class SharedFeatureNet:
    """共享特征网络"""
    
    def __init__(
        self,
        state_dim: int = 128,
        hidden_dim: int = 256,
        shared_dim: int = 128
    ):
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim
        self.shared_dim = shared_dim
        
        self.shared_weights: Dict[str, List[float]] = {}
        self.department_heads: Dict[str, Dict[str, List[float]]] = {}
        
        self._init_networks()
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_forward_passes": 0,
            "total_backward_passes": 0,
            "shared_updates": 0,
        }
    
    def _init_networks(self):
        for i in range(self.hidden_dim):
            self.shared_weights[f"fc1_{i}"] = [random.gauss(0, 0.1) for _ in range(self.state_dim)]
        
        for i in range(self.shared_dim):
            self.shared_weights[f"fc2_{i}"] = [random.gauss(0, 0.1) for _ in range(self.hidden_dim)]
        
        for dept in Department:
            self.department_heads[dept.value] = {
                f"head_{i}": [random.gauss(0, 0.1) for _ in range(self.shared_dim)]
                for i in range(32)
            }
    
    def forward(
        self,
        state: List[float],
        department: str
    ) -> List[float]:
        self.stats["total_forward_passes"] += 1
        
        hidden1 = []
        for i in range(self.hidden_dim):
            weights = self.shared_weights.get(f"fc1_{i}", [0.0] * len(state))
            activation = sum(w * s for w, s in zip(weights, state))
            hidden1.append(max(0, activation))
        
        shared_features = []
        for i in range(self.shared_dim):
            weights = self.shared_weights.get(f"fc2_{i}", [0.0] * len(hidden1))
            activation = sum(w * h for w, h in zip(weights, hidden1))
            shared_features.append(max(0, activation))
        
        if department not in self.department_heads:
            department = Department.GONG.value
        
        output = []
        head_weights = self.department_heads[department]
        for i in range(32):
            weights = head_weights.get(f"head_{i}", [0.0] * len(shared_features))
            activation = sum(w * f for w, f in zip(weights, shared_features))
            output.append(activation)
        
        return output
    
    def update_shared(
        self,
        gradients: Dict[str, List[float]],
        learning_rate: float = 0.001
    ):
        with self._lock:
            for key, grad in gradients.items():
                if key in self.shared_weights:
                    weights = self.shared_weights[key]
                    for i in range(min(len(weights), len(grad))):
                        weights[i] -= learning_rate * grad[i]
            
            self.stats["shared_updates"] += 1
    
    def update_department_head(
        self,
        department: str,
        gradients: Dict[str, List[float]],
        learning_rate: float = 0.001
    ):
        with self._lock:
            if department in self.department_heads:
                head = self.department_heads[department]
                for key, grad in gradients.items():
                    if key in head:
                        weights = head[key]
                        for i in range(min(len(weights), len(grad))):
                            weights[i] -= learning_rate * grad[i]
    
    def get_shared_features(self, state: List[float]) -> List[float]:
        hidden1 = []
        for i in range(self.hidden_dim):
            weights = self.shared_weights.get(f"fc1_{i}", [0.0] * len(state))
            activation = sum(w * s for w, s in zip(weights, state))
            hidden1.append(max(0, activation))
        
        shared_features = []
        for i in range(self.shared_dim):
            weights = self.shared_weights.get(f"fc2_{i}", [0.0] * len(hidden1))
            activation = sum(w * h for w, h in zip(weights, hidden1))
            shared_features.append(max(0, activation))
        
        return shared_features
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "state_dim": self.state_dim,
            "hidden_dim": self.hidden_dim,
            "shared_dim": self.shared_dim,
            "departments": list(self.department_heads.keys()),
        }


class DepartmentAgent:
    """部门智能体"""
    
    def __init__(
        self,
        agent_id: str,
        department: Department,
        shared_net: SharedFeatureNet
    ):
        self.agent_id = agent_id
        self.department = department
        self.shared_net = shared_net
        
        self.local_experience_buffer: deque = deque(maxlen=10000)
        self.current_task: Optional[SubTask] = None
        
        self._lock = threading.Lock()
        
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_completion_time": 0.0,
        }
    
    def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state_vector = self._state_to_vector(state)
        
        output = self.shared_net.forward(state_vector, self.department.value)
        
        action = self._output_to_action(output, state)
        
        return action
    
    def _state_to_vector(self, state: Dict[str, Any]) -> List[float]:
        vector = [0.0] * self.shared_net.state_dim
        
        for i, (key, value) in enumerate(state.items()):
            if i >= self.shared_net.state_dim:
                break
            if isinstance(value, (int, float)):
                vector[i] = float(value)
            elif isinstance(value, bool):
                vector[i] = 1.0 if value else 0.0
        
        return vector
    
    def _output_to_action(
        self,
        output: List[float],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        action_type = "execute"
        
        if output and output[0] > 0:
            action_type = "execute"
        elif len(output) > 1 and output[1] > 0:
            action_type = "delegate"
        elif len(output) > 2 and output[2] > 0:
            action_type = "wait"
        
        return {
            "action_type": action_type,
            "department": self.department.value,
            "confidence": abs(output[0]) if output else 0.5,
        }
    
    def learn(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        next_state: Dict[str, Any],
        done: bool
    ):
        self.local_experience_buffer.append({
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "timestamp": datetime.now().isoformat(),
        })
    
    def assign_task(self, task: SubTask):
        with self._lock:
            self.current_task = task
    
    def complete_task(self, result: Dict[str, Any], success: bool = True):
        with self._lock:
            if self.current_task:
                if success:
                    self.stats["tasks_completed"] += 1
                else:
                    self.stats["tasks_failed"] += 1
                
                self.current_task = None
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "department": self.department.value,
            **self.stats,
            "buffer_size": len(self.local_experience_buffer),
        }
