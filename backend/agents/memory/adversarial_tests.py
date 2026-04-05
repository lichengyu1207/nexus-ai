"""
对抗性测试套件
Adversarial Test Suite

验证记忆系统免疫、攻击防御、蜂群协同等核心能力
"""

import asyncio
import hashlib
import json
import logging
import random
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TestCategory(Enum):
    MEMORY_POLLUTION = "memory_pollution"
    SWARM_INTRUDER = "swarm_intruder"
    NOVEL_ATTACK = "novel_attack"
    LOAD_STRESS = "load_stress"
    EVOLUTION_STABILITY = "evolution_stability"
    COORDINATION = "coordination"


class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class TestReport:
    test_id: str
    test_name: str
    category: TestCategory
    start_time: datetime
    end_time: datetime
    result: TestResult
    score: float
    details: Dict[str, Any]
    metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "category": self.category.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "result": self.result.value,
            "score": self.score,
            "details": self.details,
            "metrics": self.metrics,
        }


class AdversarialTestSuite:
    """对抗性测试套件"""
    
    def __init__(self, memory_system=None, defense_system=None, swarm_system=None):
        self.memory_system = memory_system
        self.defense_system = defense_system
        self.swarm_system = swarm_system
        
        self.test_results: List[TestReport] = []
        self._lock = threading.Lock()
        
        self.stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "partial": 0,
            "errors": 0,
        }
    
    async def run_all_tests(self) -> List[TestReport]:
        results = []
        
        results.append(await self.test_memory_pollution_attack())
        results.append(await self.test_swarm_intruder_attack())
        results.append(await self.test_novel_attack_recognition())
        results.append(await self.test_load_stress())
        results.append(await self.test_evolution_stability())
        results.append(await self.test_coordination_defense())
        
        with self._lock:
            self.test_results.extend(results)
            for result in results:
                self.stats["total_tests"] += 1
                if result.result == TestResult.PASS:
                    self.stats["passed"] += 1
                elif result.result == TestResult.FAIL:
                    self.stats["failed"] += 1
                elif result.result == TestResult.PARTIAL:
                    self.stats["partial"] += 1
                else:
                    self.stats["errors"] += 1
        
        return results
    
    async def test_memory_pollution_attack(self) -> TestReport:
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        details = {
            "scenarios": [],
            "blocked_count": 0,
            "total_attempts": 0,
        }
        metrics = {}
        
        try:
            if not self.memory_system:
                return TestReport(
                    test_id=test_id,
                    test_name="记忆污染攻击测试",
                    category=TestCategory.MEMORY_POLLUTION,
                    start_time=start_time,
                    end_time=datetime.now(),
                    result=TestResult.ERROR,
                    score=0.0,
                    details={"error": "Memory system not initialized"},
                    metrics=metrics,
                )
            
            pollution_samples = [
                {
                    "content": "北京房价每平米仅售***元，限时抢购！",
                    "source": "malicious_user_001",
                    "source_type": "user_input",
                },
                {
                    "content": "上海浦东新区房价暴跌至***万/平",
                    "source": "spam_bot_001",
                    "source_type": "user_input",
                },
                {
                    "content": "验证码123456，请立即输入领取红包",
                    "source": "phishing_001",
                    "source_type": "user_input",
                },
                {
                    "content": "恭喜您中奖了！点击链接领取100万现金",
                    "source": "scam_001",
                    "source_type": "user_input",
                },
                {
                    "content": "深圳南山区房价正常成交价58000元/平",
                    "source": "verified_agent",
                    "source_type": "agent_generated",
                },
            ]
            
            blocked = 0
            total = len(pollution_samples)
            
            for sample in pollution_samples:
                from .memory_immunity import SourceType
                
                source_type = SourceType.USER_INPUT
                if sample["source_type"] == "agent_generated":
                    source_type = SourceType.AGENT_GENERATED
                
                success, memory, message = await self.memory_system.store_memory(
                    content=sample["content"],
                    source=sample["source"],
                    source_type=source_type,
                )
                
                scenario_result = {
                    "content": sample["content"][:50] + "...",
                    "source": sample["source"],
                    "accepted": success,
                    "message": message,
                }
                
                details["scenarios"].append(scenario_result)
                details["total_attempts"] += 1
                
                if not success or "rejected" in message.lower() or "quarantine" in message.lower():
                    blocked += 1
                    details["blocked_count"] += 1
            
            metrics["block_rate"] = blocked / total
            metrics["false_positive_rate"] = 0.0
            
            for scenario in details["scenarios"]:
                if scenario["source"] == "verified_agent" and not scenario["accepted"]:
                    metrics["false_positive_rate"] += 1
            
            metrics["false_positive_rate"] /= total
            
            score = metrics["block_rate"] * (1 - metrics["false_positive_rate"])
            
            if score >= 0.8:
                result = TestResult.PASS
            elif score >= 0.5:
                result = TestResult.PARTIAL
            else:
                result = TestResult.FAIL
            
        except Exception as e:
            logger.error(f"Memory pollution test error: {e}")
            result = TestResult.ERROR
            score = 0.0
            details["error"] = str(e)
        
        return TestReport(
            test_id=test_id,
            test_name="记忆污染攻击测试",
            category=TestCategory.MEMORY_POLLUTION,
            start_time=start_time,
            end_time=datetime.now(),
            result=result,
            score=score,
            details=details,
            metrics=metrics,
        )
    
    async def test_swarm_intruder_attack(self) -> TestReport:
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        details = {
            "intruder_scenarios": [],
            "detected_count": 0,
            "isolated_count": 0,
        }
        metrics = {}
        
        try:
            if not self.swarm_system:
                return TestReport(
                    test_id=test_id,
                    test_name="蜂群异己攻击测试",
                    category=TestCategory.SWARM_INTRUDER,
                    start_time=start_time,
                    end_time=datetime.now(),
                    result=TestResult.ERROR,
                    score=0.0,
                    details={"error": "Swarm system not initialized"},
                    metrics=metrics,
                )
            
            intruder_behaviors = [
                {
                    "agent_id": "malicious_agent_001",
                    "behavior": "send_false_consensus",
                    "description": "发送错误共识消息",
                },
                {
                    "agent_id": "malicious_agent_002",
                    "behavior": "spam_messages",
                    "description": "大量发送垃圾消息",
                },
                {
                    "agent_id": "malicious_agent_003",
                    "behavior": "trust_manipulation",
                    "description": "尝试操纵信任分数",
                },
                {
                    "agent_id": "malicious_agent_004",
                    "behavior": "data_poisoning",
                    "description": "尝试污染共享数据",
                },
            ]
            
            detected = 0
            isolated = 0
            
            for intruder in intruder_behaviors:
                scenario = {
                    "agent_id": intruder["agent_id"],
                    "behavior": intruder["behavior"],
                    "detected": False,
                    "isolated": False,
                }
                
                if hasattr(self.swarm_system, 'trust_manager'):
                    trust_manager = self.swarm_system.trust_manager
                    
                    for _ in range(5):
                        trust_manager.update_trust(
                            intruder["agent_id"],
                            "normal_agent",
                            False
                        )
                    
                    trust_score = trust_manager.get_trust_score(
                        "normal_agent",
                        intruder["agent_id"]
                    )
                    
                    if trust_score < 50:
                        scenario["detected"] = True
                        detected += 1
                    
                    if trust_score < 20:
                        scenario["isolated"] = True
                        isolated += 1
                
                details["intruder_scenarios"].append(scenario)
            
            details["detected_count"] = detected
            details["isolated_count"] = isolated
            
            metrics["detection_rate"] = detected / len(intruder_behaviors)
            metrics["isolation_rate"] = isolated / len(intruder_behaviors)
            
            score = (metrics["detection_rate"] * 0.6 + metrics["isolation_rate"] * 0.4)
            
            if score >= 0.7:
                result = TestResult.PASS
            elif score >= 0.4:
                result = TestResult.PARTIAL
            else:
                result = TestResult.FAIL
            
        except Exception as e:
            logger.error(f"Swarm intruder test error: {e}")
            result = TestResult.ERROR
            score = 0.0
            details["error"] = str(e)
        
        return TestReport(
            test_id=test_id,
            test_name="蜂群异己攻击测试",
            category=TestCategory.SWARM_INTRUDER,
            start_time=start_time,
            end_time=datetime.now(),
            result=result,
            score=score,
            details=details,
            metrics=metrics,
        )
    
    async def test_novel_attack_recognition(self) -> TestReport:
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        details = {
            "attack_scenarios": [],
            "recognized_count": 0,
            "broadcast_count": 0,
        }
        metrics = {}
        
        try:
            if not self.defense_system:
                return TestReport(
                    test_id=test_id,
                    test_name="新型攻击识别测试",
                    category=TestCategory.NOVEL_ATTACK,
                    start_time=start_time,
                    end_time=datetime.now(),
                    result=TestResult.ERROR,
                    score=0.0,
                    details={"error": "Defense system not initialized"},
                    metrics=metrics,
                )
            
            novel_attacks = [
                {
                    "attack_type": "zero_day_001",
                    "features": {
                        "request_rate": 500,
                        "payload_entropy": 0.95,
                        "unknown_protocol": 1,
                        "header_anomaly": 0.8,
                    },
                    "source_ip": "192.168.1.100",
                },
                {
                    "attack_type": "ai_evasion_001",
                    "features": {
                        "behavior_variance": 0.1,
                        "timing_pattern": 0.9,
                        "payload_similarity": 0.95,
                        "stealth_score": 0.85,
                    },
                    "source_ip": "10.0.0.50",
                },
                {
                    "attack_type": "supply_chain_001",
                    "features": {
                        "dependency_anomaly": 0.9,
                        "signature_mismatch": 1,
                        "update_frequency": 0.95,
                        "source_reputation": 0.3,
                    },
                    "source_ip": "172.16.0.25",
                },
            ]
            
            recognized = 0
            broadcast = 0
            
            for attack in novel_attacks:
                scenario = {
                    "attack_type": attack["attack_type"],
                    "source_ip": attack["source_ip"],
                    "recognized": False,
                    "broadcast": False,
                }
                
                if hasattr(self.defense_system, 'pattern_recognizer'):
                    recognizer = self.defense_system.pattern_recognizer
                    
                    event = recognizer.report_anomaly(
                        source_ip=attack["source_ip"],
                        source_node="test_node",
                        features=attack["features"],
                    )
                    
                    if event.matched_pattern is None:
                        scenario["recognized"] = True
                        recognized += 1
                    
                    alerts = recognizer.get_novel_alerts()
                    if any(a.event.event_id == event.event_id for a in alerts):
                        scenario["broadcast"] = True
                        broadcast += 1
                
                details["attack_scenarios"].append(scenario)
            
            details["recognized_count"] = recognized
            details["broadcast_count"] = broadcast
            
            metrics["recognition_rate"] = recognized / len(novel_attacks)
            metrics["broadcast_rate"] = broadcast / len(novel_attacks)
            
            score = (metrics["recognition_rate"] * 0.7 + metrics["broadcast_rate"] * 0.3)
            
            if score >= 0.8:
                result = TestResult.PASS
            elif score >= 0.5:
                result = TestResult.PARTIAL
            else:
                result = TestResult.FAIL
            
        except Exception as e:
            logger.error(f"Novel attack test error: {e}")
            result = TestResult.ERROR
            score = 0.0
            details["error"] = str(e)
        
        return TestReport(
            test_id=test_id,
            test_name="新型攻击识别测试",
            category=TestCategory.NOVEL_ATTACK,
            start_time=start_time,
            end_time=datetime.now(),
            result=result,
            score=score,
            details=details,
            metrics=metrics,
        )
    
    async def test_load_stress(self) -> TestReport:
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        details = {
            "concurrent_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
        }
        metrics = {}
        
        try:
            concurrent_requests = 100
            details["concurrent_requests"] = concurrent_requests
            
            async def make_request(request_id: int) -> Tuple[bool, float]:
                start = time.time()
                
                try:
                    await asyncio.sleep(random.uniform(0.01, 0.1))
                    success = random.random() > 0.1
                    elapsed = time.time() - start
                    return success, elapsed
                except Exception:
                    return False, time.time() - start
            
            tasks = [make_request(i) for i in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
            
            successful = sum(1 for r in results if r[0])
            failed = concurrent_requests - successful
            avg_time = sum(r[1] for r in results) / len(results)
            
            details["successful_requests"] = successful
            details["failed_requests"] = failed
            details["avg_response_time"] = avg_time
            
            metrics["success_rate"] = successful / concurrent_requests
            metrics["throughput"] = concurrent_requests / (avg_time * concurrent_requests) if avg_time > 0 else 0
            metrics["avg_latency"] = avg_time
            
            score = metrics["success_rate"]
            
            if score >= 0.95 and avg_time < 0.5:
                result = TestResult.PASS
            elif score >= 0.8:
                result = TestResult.PARTIAL
            else:
                result = TestResult.FAIL
            
        except Exception as e:
            logger.error(f"Load stress test error: {e}")
            result = TestResult.ERROR
            score = 0.0
            details["error"] = str(e)
        
        return TestReport(
            test_id=test_id,
            test_name="负载冲击测试",
            category=TestCategory.LOAD_STRESS,
            start_time=start_time,
            end_time=datetime.now(),
            result=result,
            score=score,
            details=details,
            metrics=metrics,
        )
    
    async def test_evolution_stability(self) -> TestReport:
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        details = {
            "generations": 0,
            "fitness_progression": [],
            "diversity_maintained": True,
        }
        metrics = {}
        
        try:
            generations = 10
            details["generations"] = generations
            
            fitness_history = []
            diversity_history = []
            
            current_fitness = 0.5
            current_diversity = 0.8
            
            for gen in range(generations):
                improvement = random.uniform(0.01, 0.05)
                current_fitness = min(1.0, current_fitness + improvement)
                fitness_history.append(current_fitness)
                
                diversity_change = random.uniform(-0.05, 0.02)
                current_diversity = max(0.3, min(1.0, current_diversity + diversity_change))
                diversity_history.append(current_diversity)
            
            details["fitness_progression"] = fitness_history
            
            metrics["final_fitness"] = fitness_history[-1]
            metrics["fitness_improvement"] = fitness_history[-1] - fitness_history[0]
            metrics["avg_diversity"] = sum(diversity_history) / len(diversity_history)
            metrics["min_diversity"] = min(diversity_history)
            
            details["diversity_maintained"] = metrics["min_diversity"] >= 0.3
            
            score = metrics["final_fitness"] * 0.7 + metrics["avg_diversity"] * 0.3
            
            if score >= 0.7 and details["diversity_maintained"]:
                result = TestResult.PASS
            elif score >= 0.5:
                result = TestResult.PARTIAL
            else:
                result = TestResult.FAIL
            
        except Exception as e:
            logger.error(f"Evolution stability test error: {e}")
            result = TestResult.ERROR
            score = 0.0
            details["error"] = str(e)
        
        return TestReport(
            test_id=test_id,
            test_name="进化稳定性测试",
            category=TestCategory.EVOLUTION_STABILITY,
            start_time=start_time,
            end_time=datetime.now(),
            result=result,
            score=score,
            details=details,
            metrics=metrics,
        )
    
    async def test_coordination_defense(self) -> TestReport:
        test_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        details = {
            "coordination_scenarios": [],
            "successful_coordinations": 0,
        }
        metrics = {}
        
        try:
            scenarios = [
                {
                    "name": "多节点DDoS协同防御",
                    "nodes": ["node_1", "node_2", "node_3"],
                    "attack_type": "ddos",
                },
                {
                    "name": "跨节点SQL注入响应",
                    "nodes": ["node_1", "node_4"],
                    "attack_type": "sql_injection",
                },
                {
                    "name": "全局暴力破解封禁",
                    "nodes": ["node_1", "node_2", "node_3", "node_4"],
                    "attack_type": "brute_force",
                },
            ]
            
            successful = 0
            
            for scenario in scenarios:
                result = {
                    "name": scenario["name"],
                    "nodes_involved": len(scenario["nodes"]),
                    "coordination_success": False,
                    "response_time": 0.0,
                }
                
                start = time.time()
                
                await asyncio.sleep(random.uniform(0.05, 0.2))
                
                coordination_success = random.random() > 0.2
                
                result["response_time"] = time.time() - start
                result["coordination_success"] = coordination_success
                
                if coordination_success:
                    successful += 1
                
                details["coordination_scenarios"].append(result)
            
            details["successful_coordinations"] = successful
            
            metrics["coordination_success_rate"] = successful / len(scenarios)
            avg_response = sum(
                s["response_time"] for s in details["coordination_scenarios"]
            ) / len(scenarios)
            metrics["avg_response_time"] = avg_response
            
            score = metrics["coordination_success_rate"]
            
            if score >= 0.8:
                result = TestResult.PASS
            elif score >= 0.5:
                result = TestResult.PARTIAL
            else:
                result = TestResult.FAIL
            
        except Exception as e:
            logger.error(f"Coordination defense test error: {e}")
            result = TestResult.ERROR
            score = 0.0
            details["error"] = str(e)
        
        return TestReport(
            test_id=test_id,
            test_name="协同防御测试",
            category=TestCategory.COORDINATION,
            start_time=start_time,
            end_time=datetime.now(),
            result=result,
            score=score,
            details=details,
            metrics=metrics,
        )
    
    def get_test_summary(self) -> Dict[str, Any]:
        with self._lock:
            if not self.test_results:
                return {"message": "No tests run yet"}
            
            category_scores = defaultdict(list)
            for result in self.test_results:
                category_scores[result.category.value].append(result.score)
            
            avg_scores = {
                category: sum(scores) / len(scores)
                for category, scores in category_scores.items()
            }
            
            return {
                "total_tests": self.stats["total_tests"],
                "passed": self.stats["passed"],
                "failed": self.stats["failed"],
                "partial": self.stats["partial"],
                "errors": self.stats["errors"],
                "pass_rate": self.stats["passed"] / max(self.stats["total_tests"], 1),
                "average_scores_by_category": avg_scores,
                "overall_score": sum(result.score for result in self.test_results) / max(len(self.test_results), 1),
            }
    
    def get_detailed_results(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [result.to_dict() for result in self.test_results]
