"""
A/B测试框架
A/B Testing Framework

提供完整的A/B测试功能，支持多变量测试和统计分析
"""

import os
import json
import logging
import time
import random
import hashlib
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class Variant:
    id: str
    name: str
    type: VariantType
    traffic_allocation: float
    config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class ExperimentMetrics:
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    latency_sum: float = 0.0
    latency_count: int = 0
    errors: int = 0
    
    @property
    def ctr(self) -> float:
        return self.clicks / self.impressions if self.impressions > 0 else 0.0
    
    @property
    def cvr(self) -> float:
        return self.conversions / self.clicks if self.clicks > 0 else 0.0
    
    @property
    def avg_latency(self) -> float:
        return self.latency_sum / self.latency_count if self.latency_count > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        return self.errors / self.impressions if self.impressions > 0 else 0.0


@dataclass
class StatisticalResult:
    metric_name: str
    control_value: float
    treatment_value: float
    absolute_lift: float
    relative_lift: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    confidence_level: float = 0.95


class ABTestingFramework:
    """
    A/B测试框架
    
    功能：
    1. 多变量测试 (A/B/n测试)
    2. 统计显著性分析
    3. 多指标综合评估
    4. 自动流量分配
    5. 实时监控和告警
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.experiments: Dict[str, Dict] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = defaultdict(dict)
        
        self.metrics_handlers: Dict[str, Callable] = {}
        
        self.significance_level = self.config.get("significance_level", 0.05)
        self.min_sample_size = self.config.get("min_sample_size", 1000)
        self.min_detectable_effect = self.config.get("min_detectable_effect", 0.05)
        
        logger.info("ABTestingFramework initialized")
    
    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        variants: List[Variant],
        description: str = "",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        target_metrics: Optional[List[str]] = None,
        audience_rules: Optional[Dict] = None
    ) -> Dict:
        """创建实验"""
        if experiment_id in self.experiments:
            raise ValueError(f"Experiment {experiment_id} already exists")
        
        total_allocation = sum(v.traffic_allocation for v in variants)
        if abs(total_allocation - 1.0) > 0.001:
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total_allocation}")
        
        control_variants = [v for v in variants if v.type == VariantType.CONTROL]
        if len(control_variants) != 1:
            raise ValueError("Experiment must have exactly one control variant")
        
        experiment = {
            "experiment_id": experiment_id,
            "name": name,
            "description": description,
            "status": ExperimentStatus.DRAFT.value,
            "variants": {
                v.id: {
                    "id": v.id,
                    "name": v.name,
                    "type": v.type.value,
                    "traffic_allocation": v.traffic_allocation,
                    "config": v.config,
                    "description": v.description,
                }
                for v in variants
            },
            "variant_order": [v.id for v in variants],
            "metrics": {v.id: ExperimentMetrics().__dict__ for v in variants},
            "start_time": start_time,
            "end_time": end_time,
            "target_metrics": target_metrics or ["ctr", "cvr"],
            "audience_rules": audience_rules or {},
            "created_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "results": None,
        }
        
        self.experiments[experiment_id] = experiment
        logger.info(f"Created experiment {experiment_id}: {name}")
        
        return experiment
    
    def start_experiment(self, experiment_id: str) -> Dict:
        """启动实验"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        if experiment["status"] not in [ExperimentStatus.DRAFT.value, ExperimentStatus.PAUSED.value]:
            raise ValueError(f"Cannot start experiment in {experiment['status']} status")
        
        experiment["status"] = ExperimentStatus.RUNNING.value
        experiment["started_at"] = time.time()
        
        logger.info(f"Started experiment {experiment_id}")
        return experiment
    
    def pause_experiment(self, experiment_id: str) -> Dict:
        """暂停实验"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        if experiment["status"] != ExperimentStatus.RUNNING.value:
            raise ValueError(f"Cannot pause experiment in {experiment['status']} status")
        
        experiment["status"] = ExperimentStatus.PAUSED.value
        logger.info(f"Paused experiment {experiment_id}")
        
        return experiment
    
    def complete_experiment(self, experiment_id: str) -> Dict:
        """完成实验"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        experiment["status"] = ExperimentStatus.COMPLETED.value
        experiment["completed_at"] = time.time()
        
        experiment["results"] = self.analyze_experiment(experiment_id)
        
        logger.info(f"Completed experiment {experiment_id}")
        return experiment
    
    def assign_variant(
        self,
        experiment_id: str,
        user_id: str,
        force_variant: Optional[str] = None
    ) -> str:
        """
        为用户分配变体
        
        使用一致性哈希确保用户始终分配到同一变体
        """
        if experiment_id not in self.experiments:
            return "control"
        
        experiment = self.experiments[experiment_id]
        
        if experiment["status"] != ExperimentStatus.RUNNING.value:
            return "control"
        
        if user_id in self.user_assignments and experiment_id in self.user_assignments[user_id]:
            return self.user_assignments[user_id][experiment_id]
        
        if force_variant and force_variant in experiment["variants"]:
            variant_id = force_variant
        else:
            hash_value = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16)
            random.seed(hash_value)
            rand = random.random()
            random.seed()
            
            cumulative = 0.0
            variant_id = "control"
            
            for vid in experiment["variant_order"]:
                allocation = experiment["variants"][vid]["traffic_allocation"]
                cumulative += allocation
                if rand < cumulative:
                    variant_id = vid
                    break
        
        self.user_assignments[user_id][experiment_id] = variant_id
        
        return variant_id
    
    def get_variant_config(self, experiment_id: str, variant_id: str) -> Dict:
        """获取变体配置"""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment["variants"]:
            return {}
        
        return experiment["variants"][variant_id]["config"]
    
    def record_impression(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ):
        """记录曝光"""
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment["metrics"]:
            return
        
        experiment["metrics"][variant_id]["impressions"] += 1
    
    def record_click(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ):
        """记录点击"""
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment["metrics"]:
            return
        
        experiment["metrics"][variant_id]["clicks"] += 1
    
    def record_conversion(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        value: float = 1.0,
        metadata: Optional[Dict] = None
    ):
        """记录转化"""
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment["metrics"]:
            return
        
        experiment["metrics"][variant_id]["conversions"] += 1
        experiment["metrics"][variant_id]["revenue"] += value
    
    def record_latency(
        self,
        experiment_id: str,
        variant_id: str,
        latency_ms: float
    ):
        """记录延迟"""
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment["metrics"]:
            return
        
        experiment["metrics"][variant_id]["latency_sum"] += latency_ms
        experiment["metrics"][variant_id]["latency_count"] += 1
    
    def record_error(
        self,
        experiment_id: str,
        variant_id: str,
        error_type: str = "unknown"
    ):
        """记录错误"""
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment["metrics"]:
            return
        
        experiment["metrics"][variant_id]["errors"] += 1
    
    def _calculate_p_value(
        self,
        control_success: int,
        control_total: int,
        treatment_success: int,
        treatment_total: int
    ) -> float:
        """
        计算p值 (双样本比例检验)
        
        使用Z检验
        """
        if control_total == 0 or treatment_total == 0:
            return 1.0
        
        p1 = control_success / control_total
        p2 = treatment_success / treatment_total
        
        p_pooled = (control_success + treatment_success) / (control_total + treatment_total)
        
        if p_pooled == 0 or p_pooled == 1:
            return 1.0
        
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))
        
        if se == 0:
            return 1.0
        
        z = (p2 - p1) / se
        
        p_value = 2 * (1 - self._normal_cdf(abs(z)))
        
        return p_value
    
    def _normal_cdf(self, x: float) -> float:
        """标准正态分布累积分布函数"""
        return (1 + math.erf(x / math.sqrt(2))) / 2
    
    def _calculate_confidence_interval(
        self,
        proportion: float,
        n: int,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """计算置信区间"""
        if n == 0:
            return (0.0, 1.0)
        
        z = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
        
        se = math.sqrt(proportion * (1 - proportion) / n)
        
        margin = z * se
        
        lower = max(0.0, proportion - margin)
        upper = min(1.0, proportion + margin)
        
        return (lower, upper)
    
    def analyze_experiment(self, experiment_id: str) -> Dict:
        """分析实验结果"""
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}
        
        experiment = self.experiments[experiment_id]
        
        control_id = None
        for vid, v in experiment["variants"].items():
            if v["type"] == VariantType.CONTROL.value:
                control_id = vid
                break
        
        if control_id is None:
            return {"error": "No control variant found"}
        
        control_metrics = experiment["metrics"][control_id]
        
        results = {
            "experiment_id": experiment_id,
            "status": experiment["status"],
            "analysis_time": datetime.now().isoformat(),
            "variants": {},
            "statistical_results": {},
            "recommendation": None,
        }
        
        for variant_id, variant in experiment["variants"].items():
            metrics = experiment["metrics"][variant_id]
            
            results["variants"][variant_id] = {
                "name": variant["name"],
                "type": variant["type"],
                "impressions": metrics["impressions"],
                "clicks": metrics["clicks"],
                "conversions": metrics["conversions"],
                "ctr": metrics["clicks"] / metrics["impressions"] if metrics["impressions"] > 0 else 0,
                "cvr": metrics["conversions"] / metrics["clicks"] if metrics["clicks"] > 0 else 0,
                "avg_latency": metrics["latency_sum"] / metrics["latency_count"] if metrics["latency_count"] > 0 else 0,
                "error_rate": metrics["errors"] / metrics["impressions"] if metrics["impressions"] > 0 else 0,
                "revenue": metrics["revenue"],
            }
        
        for variant_id in experiment["variants"]:
            if variant_id == control_id:
                continue
            
            treatment_metrics = experiment["metrics"][variant_id]
            
            ctr_result = self._analyze_metric(
                "ctr",
                control_metrics["clicks"],
                control_metrics["impressions"],
                treatment_metrics["clicks"],
                treatment_metrics["impressions"]
            )
            
            cvr_result = self._analyze_metric(
                "cvr",
                control_metrics["conversions"],
                control_metrics["clicks"],
                treatment_metrics["conversions"],
                treatment_metrics["clicks"]
            )
            
            results["statistical_results"][variant_id] = {
                "ctr": ctr_result.__dict__,
                "cvr": cvr_result.__dict__,
            }
        
        results["recommendation"] = self._generate_recommendation(results)
        
        return results
    
    def _analyze_metric(
        self,
        metric_name: str,
        control_success: int,
        control_total: int,
        treatment_success: int,
        treatment_total: int
    ) -> StatisticalResult:
        """分析单个指标"""
        control_value = control_success / control_total if control_total > 0 else 0
        treatment_value = treatment_success / treatment_total if treatment_total > 0 else 0
        
        absolute_lift = treatment_value - control_value
        relative_lift = absolute_lift / control_value if control_value > 0 else 0
        
        p_value = self._calculate_p_value(
            control_success, control_total,
            treatment_success, treatment_total
        )
        
        ci = self._calculate_confidence_interval(treatment_value, treatment_total)
        
        is_significant = p_value < self.significance_level
        
        return StatisticalResult(
            metric_name=metric_name,
            control_value=control_value,
            treatment_value=treatment_value,
            absolute_lift=absolute_lift,
            relative_lift=relative_lift,
            p_value=p_value,
            confidence_interval=ci,
            is_significant=is_significant,
        )
    
    def _generate_recommendation(self, results: Dict) -> Dict:
        """生成推荐"""
        significant_improvements = []
        significant_degradations = []
        
        for variant_id, stats in results.get("statistical_results", {}).items():
            for metric_name, metric_result in stats.items():
                if metric_result["is_significant"]:
                    if metric_result["relative_lift"] > 0:
                        significant_improvements.append({
                            "variant_id": variant_id,
                            "metric": metric_name,
                            "lift": metric_result["relative_lift"],
                        })
                    else:
                        significant_degradations.append({
                            "variant_id": variant_id,
                            "metric": metric_name,
                            "lift": metric_result["relative_lift"],
                        })
        
        if significant_degradations:
            return {
                "action": "abort",
                "reason": f"发现显著退化指标: {significant_degradations}",
                "suggested_variant": "control",
            }
        
        if significant_improvements:
            best_improvement = max(significant_improvements, key=lambda x: x["lift"])
            return {
                "action": "adopt",
                "reason": f"发现显著改进指标: {best_improvement}",
                "suggested_variant": best_improvement["variant_id"],
            }
        
        total_impressions = sum(
            v["impressions"] for v in results.get("variants", {}).values()
        )
        
        if total_impressions < self.min_sample_size:
            return {
                "action": "continue",
                "reason": f"样本量不足 ({total_impressions}/{self.min_sample_size})",
                "suggested_variant": None,
            }
        
        return {
            "action": "inconclusive",
            "reason": "未发现显著差异",
            "suggested_variant": None,
        }
    
    def get_experiment_status(self, experiment_id: str) -> Dict:
        """获取实验状态"""
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}
        
        experiment = self.experiments[experiment_id]
        
        total_impressions = sum(
            m["impressions"] for m in experiment["metrics"].values()
        )
        
        return {
            "experiment_id": experiment_id,
            "name": experiment["name"],
            "status": experiment["status"],
            "total_impressions": total_impressions,
            "variant_count": len(experiment["variants"]),
            "created_at": datetime.fromtimestamp(experiment["created_at"]).isoformat(),
            "started_at": datetime.fromtimestamp(experiment["started_at"]).isoformat() if experiment["started_at"] else None,
        }
    
    def list_experiments(self, status: Optional[str] = None) -> List[Dict]:
        """列出实验"""
        experiments = []
        
        for exp_id, exp in self.experiments.items():
            if status is None or exp["status"] == status:
                experiments.append(self.get_experiment_status(exp_id))
        
        return experiments
    
    def calculate_sample_size(
        self,
        baseline_rate: float,
        min_detectable_effect: float,
        significance_level: float = 0.05,
        power: float = 0.8
    ) -> int:
        """
        计算所需样本量
        
        Args:
            baseline_rate: 基线转化率
            min_detectable_effect: 最小可检测效应 (相对)
            significance_level: 显著性水平
            power: 统计功效
        """
        p1 = baseline_rate
        p2 = baseline_rate * (1 + min_detectable_effect)
        
        z_alpha = 1.96 if significance_level == 0.05 else 2.576
        z_beta = 0.84 if power == 0.8 else 1.28 if power == 0.9 else 0.52
        
        pooled_p = (p1 + p2) / 2
        
        numerator = (z_alpha * math.sqrt(2 * pooled_p * (1 - pooled_p)) + 
                    z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2
        
        sample_size = int(math.ceil(numerator / denominator))
        
        return sample_size


_global_framework: Optional[ABTestingFramework] = None


def get_framework() -> ABTestingFramework:
    """获取全局框架实例"""
    global _global_framework
    if _global_framework is None:
        _global_framework = ABTestingFramework()
    return _global_framework
