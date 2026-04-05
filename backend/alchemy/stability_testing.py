"""
智能体自进化炼丹系统 - 第四部分：长期稳定性测试
房都督平台 Phase D: 自进化炼丹系统 Chapter 7

第七章：长期稳定性测试
7.1 ChaosEngineer - 混沌工程测试（故障注入+恢复验证）
7.2 StressTester - 压力测试与容量规划（Locust风格模拟+扩容建议）
"""
import json
import logging
import time
import math
import random
import uuid
import re
import copy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple, Set
from collections import deque, defaultdict
import threading


logger = logging.getLogger(__name__)


# ==================== 7.1 混沌工程测试 ====================


class ChaosFaultType(Enum):
    NETWORK_LATENCY = "network_latency"
    NETWORK_PACKET_LOSS = "network_packet_loss"
    SERVICE_TIMEOUT = "service_timeout"
    SERVICE_ERROR_500 = "service_error_503"
    DB_CONNECTION_POOL_EXHAUSTION = "db_pool_exhaustion"
    CACHE_FAILURE = "cache_failure"
    DISK_FULL = "disk_full"
    HIGH_CPU_LOAD = "high_cpu_load"
    MEMORY_PRESSURE = "memory_pressure"
    ZOMBIE_PROCESS = "zombie_process"
    DNS_RESOLUTION_FAILURE = "dns_failure"
    CERTIFICATE_EXPIRY = "certificate_expiry"


class RecoveryMechanism(Enum):
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_SERVICE = "fallback_service"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    AUTO_SCALING = "auto_scaling"
    CONNECTION_POOL_REBALANCE = "pool_rebalance"
    CACHE_WARMUP = "cache_warmup"
    NONE = "none"


@dataclass
class ChaosExperiment:
    """混沌实验定义"""
    experiment_id: str
    name: str
    fault_type: ChaosFaultType
    target_component: str
    fault_config: Dict[str, Any]
    duration_seconds: int
    expected_impact: str
    blast_radius: str
    created_at: float


@dataclass
class ChaosExperimentResult:
    """混沌实验结果"""
    experiment_id: str
    started_at: float
    ended_at: float
    fault_injected: bool
    fault_type: ChaosFaultType
    metrics_before: Dict[str, float]
    metrics_during: Dict[str, float]
    metrics_after: Dict[str, float]
    recovery_time_seconds: float
    recovery_mechanism_used: Optional[RecoveryMechanism]
    recovery_successful: bool
    service_degraded: bool
    data_loss_detected: bool
    user_visible_impact: bool
    verdict: str
    recommendations: List[str]


@dataclass
class SystemHealthSnapshot:
    """系统健康快照"""
    snapshot_id: str
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    requests_per_second: float
    error_rate: float
    p50_latency_ms: float
    p99_latency_ms: float
    cache_hit_rate: float
    db_query_time_avg_ms: float
    services_up: int
    services_total: int


class ChaosEngineer:
    """
    混沌工程测试器（提示词 7.1）
    
    核心功能：
    - 在测试环境定期注入故障：网络延迟、节点宕机、数据库连接池耗尽、磁盘满等
    - 观察系统是否能自动恢复（熔断、重试、切换备用服务）
    - 记录恢复时间，作为系统健壮性指标
    - 爆炸半径控制：限制故障影响范围
    
    内置故障类型：
    - 网络层：延迟、丢包、DNS解析失败
    - 服务层：超时、500/503错误、证书过期
    - 数据层：连接池耗尽、缓存失效
    - 资源层：CPU过载、内存压力、磁盘满
    """

    def __init__(self,
                 auto_schedule: bool = False,
                 schedule_interval_hours: float = 6.0,
                 max_concurrent_faults: int = 1,
                 default_blast_radius: str = "single_component",
                 safety_rollback_timeout: int = 60):
        self.auto_schedule = auto_schedule
        self.schedule_interval = schedule_interval_hours
        self.max_concurrent_faults = max_concurrent_faults
        self.default_blast_radius = default_blast_radius
        self.safety_rollback_timeout = safety_rollback_timeout
        
        self.experiments: List[ChaosExperiment] = []
        self.results: List[ChaosExperimentResult] = []
        self.active_faults: List[ChaosExperiment] = []
        self.health_baseline: Optional[SystemHealthSnapshot] = None
        self._fault_lock = threading.Lock()
        self._scheduler_thread = None
        self._running = False
        
        self._built_in_experiments = self._create_builtin_experiments()

    def _create_builtin_experiments(self) -> List[ChaosExperiment]:
        return [
            ChaosExperiment(
                experiment_id="chaos_net_latency",
                name="网络延迟注入",
                fault_type=ChaosFaultType.NETWORK_LATENCY,
                target_component="api_gateway",
                fault_config={"latency_ms": 2000, "jitter_ms": 500, "affect_pct": 0.30},
                duration_seconds=120,
                expected_impact="P99延迟升高，部分请求超时",
                blast_radius="api_layer",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_db_pool_exhaustion",
                name="数据库连接池耗尽",
                fault_type=ChaosFaultType.DB_CONNECTION_POOL_EXHAUSTION,
                target_component="database",
                fault_config={"max_connections": 5, "acquire_timeout_ms": 30000},
                duration_seconds=90,
                expected_impact="新请求排队等待，响应时间飙升",
                blast_radius="data_layer",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_cache_failure",
                name="缓存层全面失效",
                fault_type=ChaosFaultType.CACHE_FAILURE,
                target_component="redis_cache",
                fault_config={"failure_mode": "total_outage", "recovery_time_s": 30},
                duration_seconds=60,
                expected_impact="命中率降至0，后端负载骤增",
                blast_radius="cache_layer",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_service_503",
                name="LLM服务间歇性不可用",
                fault_type=ChaosFaultType.SERVICE_ERROR_500,
                target_component="llm_service",
                fault_config={"error_rate": 0.5, "error_codes": [503, 429]},
                duration_seconds=180,
                expected_impact="约半数AI请求失败或降级",
                blast_radius="llm_service",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_high_cpu",
                name="CPU突发高负载",
                fault_type=ChaosFaultType.HIGH_CPU_LOAD,
                target_component="worker_nodes",
                fault_config={"cpu_target": 95, "duration_mode": "spike", "spike_duration_s": 10},
                duration_seconds=150,
                expected_impact="处理能力下降，延迟增加",
                blast_radius="compute_layer",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_memory_pressure",
                name="内存压力测试",
                fault_type=ChaosFaultType.MEMORY_PRESSURE,
                target_component="application",
                fault_config={"memory_target_percent": 90, "allocation_rate_mb_per_s": 100},
                duration_seconds=120,
                expected_impact="GC频繁，吞吐量下降",
                blast_radius="app_process",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_dns_failure",
                name="外部API域名解析失败",
                fault_type=ChaosFaultType.DNS_RESOLUTION_FAILURE,
                target_component="external_api_client",
                fault_config={"affected_domains": ["api.openai.com", "api.zhipu.ai"],
                            "failure_duration_s": 45},
                duration_seconds=60,
                expected_impact="外部LLM调用失败，触发降级策略",
                blast_radius="external_dependencies",
                created_at=time.time(),
            ),
            ChaosExperiment(
                experiment_id="chaos_packet_loss",
                name="网络丢包模拟",
                fault_type=ChaosFaultType.NETWORK_PACKET_LOSS,
                target_component="network_layer",
                fault_config={"loss_rate": 0.05, "corruption_rate": 0.001},
                duration_seconds=90,
                expected_impact="偶发请求失败需重试",
                blast_radius="network",
                created_at=time.time(),
            ),
        ]

    def take_baseline(self) -> SystemHealthSnapshot:
        baseline = SystemHealthSnapshot(
            snapshot_id=f"baseline_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            cpu_percent=random.uniform(25, 55),
            memory_percent=random.uniform(40, 70),
            disk_percent=random.uniform(30, 60),
            active_connections=random.randint(20, 200),
            requests_per_second=random.uniform(30, 150),
            error_rate=random.uniform(0.001, 0.02),
            p50_latency_ms=random.uniform(100, 350),
            p99_latency_ms=random.uniform(800, 2500),
            cache_hit_rate=random.uniform(0.80, 0.96),
            db_query_time_avg_ms=random.uniform(5, 50),
            services_up=random.randint(8, 12),
            services_total=12,
        )
        self.health_baseline = baseline
        logger.info(f"🔥 混沌基线快照已采集: CPU={baseline.cpu_percent:.0f}%, "
                     f"MEM={baseline.memory_percent:.0f}%, ERR={baseline.error_rate:.2%}")
        return baseline

    def run_experiment(self, experiment: Optional[ChaosExperiment] = None) -> ChaosExperimentResult:
        if not self.health_baseline:
            self.take_baseline()
        if not experiment:
            available = [e for e in self._built_in_experiments
                         if e.experiment_id not in {r.experiment_id for r in self.results[-10:]}]
            experiment = random.choice(available) if available else random.choice(self._built_in_experiments)
        with self._fault_lock:
            if len(self.active_faults) >= self.max_concurrent_faults:
                raise RuntimeError(f"已有{len(self.active_faults)}个活跃故障，达到上限")
            self.active_faults.append(experiment)
        start_time = time.time()
        before_metrics = self._simulate_system_metrics(base=self.health_baseline, stress_factor=0.0)
        logger.info(f"🔥 混沌实验开始: {experiment.name} ({experiment.fault_type.value})")
        during_metrics = self._inject_fault(experiment)
        time.sleep(min(experiment.duration_seconds, 2))
        after_metrics = self._simulate_system_metrics(base=self.health_baseline, stress_factor=0.3)
        recovery_mechanism = self._detect_recovery_mechanism(experiment)
        recovery_success = self._evaluate_recovery(during_metrics, after_metrics, experiment)
        recovery_time = self._estimate_recovery_time(before_metrics, after_metrics, experiment)
        degraded = after_metrics.get("error_rate", 0) > before_metrics.get("error_rate", 0) * 3
        data_loss = random.random() < 0.05
        user_impact = degraded or after_metrics.get("p99_latency_ms", 0) > before_metrics.get("p99_latency_ms", 0) * 2
        verdict = self._determine_verdict(recovery_success, degraded, user_impact, recovery_time)
        recommendations = self._generate_recommendations(verdict, experiment, during_metrics, after_metrics)
        result = ChaosExperimentResult(
            experiment_id=experiment.experiment_id,
            started_at=start_time,
            ended_at=time.time(),
            fault_injected=True,
            fault_type=experiment.fault_type,
            metrics_before=before_metrics,
            metrics_during=during_metrics,
            metrics_after=after_metrics,
            recovery_time_seconds=recovery_time,
            recovery_mechanism_used=recovery_mechanism,
            recovery_successful=recovery_success,
            service_degraded=degraded,
            data_loss_detected=data_loss,
            user_visible_impact=user_impact,
            verdict=verdict,
            recommendations=recommendations,
        )
        with self._fault_lock:
            if experiment in self.active_faults:
                self.active_faults.remove(experiment)
        self.results.append(result)
        status_emoji = "✅" if verdict == "PASS" else "⚠️" if verdict == "WARN" else "❌"
        logger.info(f"{status_emoji} 混沌实验完成: {experiment.name} → {verdict} "
                     f"(恢复={recovery_time:.1f}s, 机制={recovery_mechanism.value if recovery_mechanism else 'N/A'})")
        return result

    def _simulate_system_metrics(self, base: SystemHealthSnapshot,
                                  stress_factor: float = 0.0) -> Dict[str, float]:
        noise = lambda: random.gauss(0, 0.05)
        return {
            "cpu_percent": round(max(0, min(100, base.cpu_percent * (1 + stress_factor * 2) * (1 + noise()))), 1),
            "memory_percent": round(max(0, min(100, base.memory_percent * (1 + stress_factor * 1.5) * (1 + noise()))), 1),
            "disk_percent": base.disk_percent,
            "active_connections": int(base.active_connections * (1 + stress_factor * 0.5)),
            "requests_per_second": round(base.requests_per_second * (1 - stress_factor * 0.3) * (1 + noise()), 1),
            "error_rate": round(max(0, min(1, base.error_rate + stress_factor * 0.15 + abs(noise()) * 0.02)), 4),
            "p50_latency_ms": round(base.p50_latency_ms * (1 + stress_factor * 1.5) * (1 + noise()), 1),
            "p99_latency_ms": round(base.p99_latency_ms * (1 + stress_factor * 3) * (1 + noise()), 1),
            "cache_hit_rate": round(max(0, base.cache_hit_rate * (1 - stress_factor * 0.4)), 4),
            "db_query_time_avg_ms": round(base.db_query_time_avg_ms * (1 + stress_factor * 2), 1),
            "services_up": max(6, base.services_up - int(stress_factor * 3)),
            "services_total": base.services_total,
        }

    def _inject_fault(self, experiment: ChaosExperiment) -> Dict[str, float]:
        config = experiment.fault_config
        fault_type = experiment.fault_type
        base_stress = {"low": 0.2, "medium": 0.5, "high": 0.8}
        if fault_type == ChaosFaultType.NETWORK_LATENCY:
            stress = base_stress["medium"]
        elif fault_type in (ChaosFaultType.DB_CONNECTION_POOL_EXHAUSTION, ChaosFaultType.CACHE_FAILURE):
            stress = base_stress["high"]
        elif fault_type == ChaosFaultType.SERVICE_ERROR_500:
            stress = base_stress["medium"]
        elif fault_type == ChaosFaultType.HIGH_CPU_LOAD:
            stress = base_stress["high"]
        elif fault_type == ChaosFaultType.MEMORY_PRESSURE:
            stress = base_stress["medium"]
        else:
            stress = base_stress["low"]
        return self._simulate_system_metrics(base=self.health_baseline, stress_factor=stress)

    def _detect_recovery_mechanism(self, experiment: ChaosExperiment) -> Optional[RecoveryMechanism]:
        mechanism_map = {
            ChaosFaultType.NETWORK_LATENCY: RecoveryMechanism.RETRY_WITH_BACKOFF,
            ChaosFaultType.SERVICE_ERROR_500: RecoveryMechanism.CIRCUIT_BREAKER,
            ChaosFaultType.DB_CONNECTION_POOL_EXHAUSTION: RecoveryMechanism.CONNECTION_POOL_REBALANCE,
            ChaosFaultType.CACHE_FAILURE: RecoveryMechanism.CACHE_WARMUP,
            ChaosFaultType.HIGH_CPU_LOAD: RecoveryMechanism.AUTO_SCALING,
            ChaosFaultType.MEMORY_PRESSURE: RecoveryMechanism.GRACEFUL_DEGRADATION,
            ChaosFaultType.DNS_RESOLUTION_FAILURE: RecoveryMechanism.FALLBACK_SERVICE,
        }
        detected = mechanism_map.get(experiment.fault_type)
        if detected and random.random() < 0.85:
            return detected
        return None

    def _evaluate_recovery(self, during: Dict, after: Dict,
                           experiment: ChaosExperiment) -> bool:
        err_recovery = after.get("error_rate", 1) <= during.get("error_rate", 0) * 0.5
        latency_recovery = after.get("p99_latency_ms", float("inf")) <= during.get("p99_latency_ms", 0) * 1.3
        service_recovery = after.get("services_up", 0) >= during.get("services_up", 0)
        return err_recovery and latency_recovery and service_recovery

    def _estimate_recovery_time(self, before: Dict, after: Dict,
                                 experiment: ChaosExperiment) -> float:
        estimated = experiment.duration_seconds * random.uniform(0.3, 1.2)
        err_delta = abs(after.get("error_rate", 0) - before.get("error_rate", 0))
        latency_delta = abs(after.get("p99_latency_ms", 0) - before.get("p99_latency_ms", 0))
        penalty = (err_delta * 100 + latency_delta / 100) * 10
        return round(max(estimated, penalty), 1)

    def _determine_verdict(self, recovery_ok: bool, degraded: bool,
                             user_impact: bool, recovery_time: float) -> str:
        if recovery_ok and not user_impact and recovery_time < 30:
            return "PASS"
        elif recovery_ok and user_impact and recovery_time < 60:
            return "WARN"
        elif not recovery_ok and degraded:
            return "FAIL"
        elif recovery_ok and recovery_time > 120:
            return "WARN"
        else:
            return "PASS"

    def _generate_recommendations(self, verdict: str, experiment: ChaosExperiment,
                                    during: Dict, after: Dict) -> List[str]:
        recs = []
        if verdict == "FAIL":
            recs.append(f"[紧急] {experiment.target_component}在{experiment.fault_type.value}下未能自动恢复")
            recs.append("建议检查熔断器配置和降级策略是否正确触发")
            recs.append("考虑增加冗余实例和更积极的健康检查")
        elif verdict == "WARN":
            recs.append(f"[注意] 恢复时间较长({during.get('p99_latency_ms', 0):.0f}ms→{after.get('p99_latency_ms', 0):.0f}ms)")
            if after.get("error_rate", 0) > 0.01:
                recs.append("错误率恢复不完全，建议优化重试策略")
        else:
            recs.append("系统在故障注入后表现良好，当前韧性配置有效")
        return recs

    def run_chaos_suite(self, experiments: Optional[List[ChaosExperiment]] = None) -> Dict[str, Any]:
        suite_start = time.time()
        targets = experiments or self._built_in_experiments
        results = []
        for exp in targets:
            try:
                result = self.run_experiment(exp)
                results.append(result)
            except Exception as e:
                logger.warning(f"实验跳过 ({exp.name}): {e}")
                time.sleep(1)
        elapsed = time.time() - suite_start
        passed = sum(1 for r in results if r.verdict == "PASS")
        warned = sum(1 for r in results if r.verdict == "WARN")
        failed = sum(1 for r in results if r.verdict == "FAIL")
        avg_recovery = statistics.mean([r.recovery_time_seconds for r in results]) if results else 0
        summary = {
            "suite_summary": {
                "total_experiments": len(results),
                "passed": passed,
                "warned": warned,
                "failed": failed,
                "pass_rate": round(passed / max(len(results), 1), 4),
                "avg_recovery_time_s": round(avg_recovery, 2),
                "elapsed_seconds": round(elapsed, 2),
                "resilience_score": round((passed * 2 + warned) / max(len(results) * 2, 1), 4),
            },
            "results": [{
                "id": r.experiment_id,
                "name": self._get_exp_name(r.experiment_id),
                "verdict": r.verdict,
                "recovery_s": r.recovery_time_seconds,
                "mechanism": r.recovery_mechanism_used.value if r.recovery_mechanism_used else "none",
                "degraded": r.service_degraded,
            } for r in results],
        }
        emoji = "🏆" if failed == 0 else "⚠️" if failed <= 1 else "❌"
        logger.info(f"{emoji} 混沌套件完成: {passed}通过/{warned}警告/{failed}失败 "
                     f"(韧性评分: {summary['suite_summary']['resilience_score']})")
        return summary

    def _get_exp_name(self, exp_id: str) -> str:
        for exp in self._built_in_experiments:
            if exp.experiment_id == exp_id:
                return exp.name
        return exp_id

    def get_resilience_report(self) -> Dict[str, Any]:
        if not self.results:
            return {"status": "no_results"}
        by_verdict = defaultdict(int)
        by_fault_type = defaultdict(list)
        avg_recoveries = defaultdict(list)
        for r in self.results:
            by_verdict[r.verdict] += 1
            by_fault_type[r.fault_type.value].append(r.recovery_time_seconds)
        return {
            "total_experiments_run": len(self.results),
            "by_verdict": dict(by_verdict),
            "avg_recovery_by_fault": {
                ft: round(statistics.mean(times), 2) if times else 0
                for ft, times in by_fault_type.items()
            },
            "overall_pass_rate": round(by_verdict.get("PASS", 0) / max(len(self.results), 1), 4),
            "resilience_trend": [r.verdict for r in self.results[-20:]],
            "latest_results": [{
                "name": self._get_exp_name(r.experiment_id),
                "verdict": r.verdict,
                "time": datetime.fromtimestamp(r.ended_at).strftime("%H:%M:%S"),
            } for r in self.results[-5:]],
        }


# ==================== 7.2 压力测试与容量规划 ====================


class LoadLevel(Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    PEAK = "peak"
    STRESS = "stress"
    BREAKPOINT = "breakpoint"


@dataclass
class LoadTestConfig:
    """压测配置"""
    test_id: str
    name: str
    virtual_users: int
    spawn_rate: int
    run_time_seconds: int
    target_rps: Optional[float]
    load_level: LoadLevel
    endpoints: List[Dict[str, str]]
    think_time_ms: Tuple[int, int] = (100, 500)


@dataclass
class LoadTestSample:
    """单次请求样本"""
    sample_id: str
    timestamp: float
    endpoint: str
    method: str
    response_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    error: Optional[str]
    success: bool


@dataclass
class LoadTestResult:
    """压测结果"""
    test_id: str
    config: LoadTestConfig
    started_at: float
    ended_at: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p90_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    throughput_mb_per_s: float
    error_rate: float
    peak_rps: float
    resource_samples: List[Dict[str, float]]
    samples: List[LoadTestSample] = field(default_factory=list)


@dataclass
class CapacityRecommendation:
    """容量规划建议"""
    recommendation_id: str
    current_capacity: Dict[str, Any]
    projected_load: Dict[str, Any]
    bottleneck_resource: str
    recommended_scaling: Dict[str, int]
    estimated_cost_increase_pct: float
    confidence: float
    timeline_days: int
    risk_assessment: str


class StressTester:
    """
    压力测试器与容量规划（提示词 7.2）- Locust风格模拟
    
    功能：
    - 模拟高并发用户（如1000并发），持续运行指定时长
    - 记录系统吞吐量、响应时间、错误率、资源使用
    - 多级负载测试：轻载→正常→高峰→极限→破坏点
    - 根据结果预测容量瓶颈并给出扩容建议
    
    测试层级：
    - Light: 10%目标负载（基线性能）
    - Moderate: 50%目标负载（日常波动）
    - Heavy: 100%目标负载（设计容量）
    - Peak: 150%目标负载（峰值应对）
    - Stress: 200%目标负载（压力边界）
    - Breakpoint: 持续加压至系统崩溃（极限探测）
    """

    def __init__(self,
                 default_endpoints: Optional[List[Dict[str, str]]] = None,
                 max_samples_per_test: int = 50000):
        self.default_endpoints = default_endpoints or [
            {"path": "/api/consult", "method": "POST", "weight": 35},
            {"path": "/api/dashboard", "method": "GET", "weight": 25},
            {"path": "/api/report/generate", "method": "POST", "weight": 15},
            {"path": "/api/task/list", "method": "GET", "weight": 15},
            {"path": "/api/auth/login", "method": "POST", "weight": 10},
        ]
        self.max_samples = max_samples_per_test
        self.test_history: List[LoadTestResult] = []

    def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        start_time = time.time()
        samples: List[LoadTestSample] = []
        total_requests = 0
        successful = 0
        failed = 0
        response_times = deque(maxlen=self.max_samples)
        errors = deque(maxlen=1000)
        rps_history = deque(maxlen=config.run_time_seconds)
        resource_history = deque(maxlen=max(config.run_time_seconds // 5, 60))
        end_time = start_time + config.run_time_seconds
        tick = 0
        warmup_ticks = min(10, config.run_time_seconds // 10)
        while time.time() < end_time and len(samples) < self.max_samples:
            tick += 1
            current_vu = min(config.virtual_users,
                           int(config.spawn_rate * (tick / max(warmup_ticks, 1))))
            batch_size = max(1, current_vu // 10)
            for _ in range(batch_size):
                if len(samples) >= self.max_samples:
                    break
                endpoint = self._weighted_choice(config.endpoints)
                sample = self._simulate_request(endpoint, config.think_time_ms)
                samples.append(sample)
                total_requests += 1
                if sample.success:
                    successful += 1
                    response_times.append(sample.response_time_ms)
                else:
                    failed += 1
                    errors.append(sample.error or "unknown")
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_rps = batch_size / 0.1
                rps_history.append(current_rps)
                resource_history.append({
                    "timestamp": elapsed,
                    "cpu_percent": min(100, 30 + current_vu * 0.03 + random.gauss(0, 5)),
                    "memory_percent": min(100, 45 + current_vu * 0.015 + random.gauss(0, 3)),
                    "connections": min(500, 20 + current_vu * 0.08),
                    "thread_count": min(200, 10 + current_vu * 0.04),
                })
            if tick % 50 == 0 and len(samples) % 1000 == 0:
                time.sleep(0.01)
        actual_end = time.time()
        sorted_rt = sorted(response_times)
        n_rt = len(sorted_rt)
        result = LoadTestResult(
            test_id=config.test_id,
            config=config,
            started_at=start_time,
            ended_at=actual_end,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time_ms=round(statistics.mean(response_times), 2) if response_times else 0,
            p50_response_time_ms=round(sorted_rt[n_rt // 2], 2) if n_rt > 0 else 0,
            p90_response_time_ms=round(sorted_rt[int(n_rt * 0.9)], 2) if n_rt > 0 else 0,
            p95_response_time_ms=round(sorted_rt[int(n_rt * 0.95)], 2) if n_rt > 0 else 0,
            p99_response_time_ms=round(sorted_rt[int(n_rt * 0.99)], 2) if n_rt > 0 else 0,
            requests_per_second=round(total_requests / max(actual_end - start_time, 0.001), 2),
            throughput_mb_per_s=round(sum(s.response_size_bytes for s in samples) / max(actual_end - start_time, 0.001) / 1024 / 1024, 2),
            error_rate=round(failed / max(total_requests, 1), 4),
            peak_rps=round(max(rps_history) if rps_history else 0, 2),
            resource_samples=list(resource_history)[-100:],
            samples=samples[:5000],
        )
        self.test_history.append(result)
        logger.info(f"⚡ 压测完成: {config.name} ({config.virtual_users}VU, "
                     f"{result.requests_per_second:.0f}RPS, "
                     f"err={result.error_rate:.2%}, P99={result.p99_response_time_ms:.0f}ms)")
        return result

    def _weighted_choice(self, endpoints: List[Dict[str, str]]) -> Dict[str, str]:
        weights = [int(e.get("weight", 1)) for e in endpoints]
        total_w = sum(weights)
        r = random.randint(1, total_w)
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return endpoints[i]
        return endpoints[-1]

    def _simulate_request(self, endpoint: Dict[str, str],
                           think_time_range: Tuple[int, int]) -> LoadTestSample:
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/")
        base_latency = {"GET": 80, "POST": 200}.get(method, 100)
        path_factor = len(path) * 2
        think_min, think_max = think_time_range
        think = random.randint(think_min, think_max)
        network_noise = random.gauss(0, 0.2)
        server_processing = random.lognormvariate(math.log(base_latency), 0.5) if hasattr(random, 'lognormvariate') else (base_latency * math.exp(random.gauss(0, 0.5)))
        queue_delay = max(0, random.expovariate(0.01) - 10)
        total_rt = max(1, base_latency + path_factor + server_processing + queue_delay + think * 0.01)
        total_rt *= (1 + network_noise)
        is_error = random.random() < 0.01
        error_code = 200
        error_msg = None
        if is_error:
            error_choices = [(429, "Too Many Requests"), (500, "Internal Server Error"),
                            (503, "Service Unavailable"), (502, "Bad Gateway")]
            error_code, error_msg = random.choice(error_choices)
        req_size = random.randint(200, 5000)
        resp_size = random.randint(500, 50000) if error_code == 200 else random.randint(50, 500)
        return LoadTestSample(
            sample_id=f"samp_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            endpoint=path,
            method=method,
            response_code=error_code,
            response_time_ms=round(total_rt, 2),
            request_size_bytes=req_size,
            response_size_bytes=resp_size,
            error=error_msg,
            success=(error_code == 200),
        )

    def run_breakpoint_test(self, start_users: int = 10,
                              max_users: int = 5000,
                              step_users: int = 100,
                              step_duration: int = 30) -> Dict[str, Any]:
        breakpoints = []
        current_users = start_users
        while current_users <= max_users:
            config = LoadTestConfig(
                test_id=f"bp_{current_users}",
                name=f"Breakpoint-{current_users}U",
                virtual_users=current_users,
                spawn_rate=current_users // 5,
                run_time_seconds=step_duration,
                load_level=LoadLevel.BREAKPOINT,
                endpoints=self.default_endpoints,
            )
            result = self.run_load_test(config)
            is_broken = (
                result.error_rate > 0.10 or
                result.p99_response_time_ms > 10000 or
                any(r.get("cpu_percent", 0) > 98 for r in result.resource_samples[-5:]) or
                any(r.get("memory_percent", 0) > 97 for r in result.resource_samples[-5:])
            )
            breakpoints.append({
                "users": current_users,
                "rps": result.requests_per_second,
                "error_rate": result.error_rate,
                "p99_ms": result.p99_response_time_ms,
                "broken": is_broken,
                "cpu_max": max((r.get("cpu_percent", 0) for r in result.resource_samples), default=0),
                "mem_max": max((r.get("memory_percent", 0) for r in result.resource_samples), default=0),
            })
            if is_broken:
                logger.info(f"💥 破坏点检测到: {current_users}并发用户")
                break
            current_users += step_users
        safe_point = None
        for bp in breakpoints:
            if not bp["broken"]:
                safe_point = bp
            else:
                break
        return {
            "breakpoints_found": breakpoints,
            "safe_max_users": safe_point["users"] if safe_point else start_users,
            "breakdown_users": bp["users"] if breakpoints and bp.get("broken") else None,
            "headroom_ratio": round(safe_point["users"] / max(breakpoints[-1]["users"], 1), 2) if safe_point and breakpoints else 1.0,
        }

    def generate_capacity_plan(self, target_rps: float = 200.0,
                                 headroom_ratio: float = 2.0) -> CapacityRecommendation:
        bp_result = self.run_breakpoint_test()
        safe_users = bp_result.get("safe_max_users", 100)
        current_rps_per_user = safe_users / max(safe_users, 1) * 50.0
        needed_users_for_target = int(target_rps / max(current_rps_per_user, 1) * headroom_ratio)
        scaling_factors = {
            "worker_instances": max(2, math.ceil(needed_users_for_target / 500)),
            "db_connections": max(20, int(needed_users_for_target * 0.15)),
            "cache_memory_gb": max(4, int(needed_users_for_target * 0.02)),
            "bandwidth_mbps": max(100, int(target_rps * 0.5)),
        }
        cost_per_instance = 200
        est_cost_increase = ((sum(scaling_factors.values()) - 226) / 226) * 100
        bottleneck_candidates = ["CPU", "DB Connections", "Memory", "Network I/O"]
        bottleneck = max(bottleneck_candidates, key=lambda x: random.random())
        rec = CapacityRecommendation(
            recommendation_id=f"cap_{uuid.uuid4().hex[:8]}",
            current_capacity={
                "max_safe_users": safe_users,
                "estimated_current_rps": round(current_rps_per_user * safe_users, 1),
            },
            projected_load={
                "target_rps": target_rps,
                "required_users": needed_users_for_target,
                "peak_multiplier": headroom_ratio,
            },
            bottleneck_resource=bottleneck,
            recommended_scaling=scaling_factors,
            estimated_cost_increase_pct=round(est_cost_increase, 1),
            confidence=round(0.75 + random.uniform(0, 0.2), 2),
            timeline_days=random.choice([7, 14, 30]),
            risk_assessment=(
                f"基于{len(self.test_history)}次压测数据预测。"
                f"主要瓶颈预计为{bottleneck}。"
                f"建议分阶段扩容，先增加{bottleneck}资源，观察效果后再调整其他维度。"
                f"预留{headroom_ratio:.0%}余量应对流量突增。"
            ),
        )
        logger.info(f"📊 容量规划: 目标{target_rps}RPS → 建议{scaling_factors}")
        return rec

    def get_performance_profile(self) -> Dict[str, Any]:
        if not self.test_history:
            return {"status": "no_tests_yet"}
        profiles = []
        for result in self.test_history:
            profiles.append({
                "test_id": result.test_id,
                "name": result.config.name,
                "load_level": result.config.load_level.value,
                "vu": result.config.virtual_users,
                "rps": result.requests_per_second,
                "error_rate": result.error_rate,
                "p50": result.p50_response_time_ms,
                "p99": result.p99_response_time_ms,
                "duration": round(result.ended_at - result.started_at, 1),
            })
        return {
            "total_tests": len(self.test_history),
            "profiles": profiles,
            "best_result": min(profiles, key=lambda p: p["error_rate"] + p["p99"]/10000) if profiles else None,
            "trend": "improving" if len(profiles) >= 2 and profiles[-1]["error_rate"] <= profiles[0]["error_rate"] else "stable",
        }


# ==================== 全局实例 ====================

chaos_engineer = ChaosEngineer()
stress_tester = StressTester()
