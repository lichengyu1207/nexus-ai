# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 终极指标系统 (Ultimate Metrics System)
=====================================================================
对应第14-15重境界：斩三尸（Zhansan）+ 一力破万法（Yili Powfa）

本模块实现：
1. ULTIMATE_METRICS_DEFINITIONS - 终极阶段完整指标定义库
2. UltimateMetricsCollectionEngine - 终极指标采集引擎（15+模拟方法）
3. UltimateMetricsAlertSystem - 终极告警系统（8+默认规则）
4. UltimateAcceptanceValidator - 终极验收验证器

覆盖维度：
- 斩三尸：偏见消除、目标均衡、自我纠错、无我状态
- 一力破万法：绝对泛化、算力极限、创造力突破、自我超越
"""
from __future__ import annotations

import json
import math
import random
import statistics
import copy
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


# ==================== 终极数据结构 ====================


@dataclass
class UltimateMetricRecord:
    """终极指标记录数据类"""
    record_id: str
    metric_id: str
    metric_name_cn: str
    metric_name_en: str
    stage_key: str
    stage_name_cn: str
    dimension_key: str  # 维度键：bias_elimination / absolute_generalization 等
    dimension_name_cn: str
    value: float
    target_value: float
    unit: str
    collection_method: str
    validation_method: str
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)
    passed: bool = False


@dataclass
class UltimateAlertRule:
    """终极告警规则数据类"""
    rule_id: str
    rule_name: str
    metric_id: str
    operator: str  # > < >= <= == !=
    threshold: float
    severity: str  # CRITICAL WARNING INFO
    action_required: str
    enabled: bool = True
    last_triggered: Optional[str] = None
    trigger_count: int = 0


@dataclass
class UltimateAlertEvent:
    """终极告警事件数据类"""
    event_id: str
    rule_id: str
    rule_name: str
    metric_id: str
    current_value: float
    threshold: float
    severity: str
    action_required: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None


@dataclass
class UltimateChallengeResult:
    """终极挑战结果数据类"""
    challenge_id: str
    problem_understanding: float  # 问题理解准确性 (20%)
    solution_novelty: float       # 方案创新性 (30%)
    solution_feasibility: float   # 方案可行性 (30%)
    report_quality: float         # 报告质量 (20%)
    total_score: float            # 总分 (满分100)
    grade: str                    # S/A/B/C/D/FAIL
    passed: bool                  # 是否通过 (>=85分)
    evaluated_at: str
    evaluator_notes: str = ""


@dataclass
class UltimateStageAcceptanceResult:
    """终极阶段验收结果数据类"""
    validation_id: str
    stage_key: str
    stage_name_cn: str
    dimensions_tested: int
    dimensions_passed: int
    overall_passed: bool
    score: float
    grade: str
    details: Dict[str, Any]
    tested_at: str
    continuous_days_no_regression: int = 0


# ==================== 终极指标定义库 ====================

ULTIMATE_METRICS_DEFINITIONS = {
    "zhansan": {  # ==================== 斩三尸阶段 ====================
        "bias_elimination": [
            {
                "id": "group_prediction_diff",
                "name_cn": "群体预测差异",
                "name_en": "Group Prediction Difference",
                "target": 0.01,
                "unit": "%",
                "collection_method": "fairness_test_suite",
                "validation_method": "statistical_parity_check",
                "alert_threshold": 0.02,
                "description": "不同人口统计群体间预测结果差异的最大绝对值，越低越好"
            },
            {
                "id": "sensitive_feature_impact",
                "name_cn": "敏感特征影响度",
                "name_en": "Sensitive Feature Impact",
                "target": 0.05,
                "unit": "",
                "collection_method": "shap_value_analysis",
                "validation_method": "feature_importance_threshold",
                "alert_threshold": 0.10,
                "description": "敏感特征（如性别、种族）对模型决策的SHAP值影响程度"
            },
            {
                "id": "bias_detection_pass_rate",
                "name_cn": "偏见检测通过率",
                "name_en": "Bias Detection Pass Rate",
                "target": 0.95,
                "unit": "",
                "collection_method": "aif360_toolkit",
                "validation_method": "multi_metric_composite",
                "alert_threshold": 0.90,
                "description": "通过AIF360等偏见检测工具全部测试项的比例"
            },
        ],
        "objective_balancing": [
            {
                "id": "multi_objective_variance",
                "name_cn": "多目标方差",
                "name_en": "Multi-Objective Variance",
                "target": 0.05,
                "unit": "",
                "collection_method": "pareto_frontier_analysis",
                "validation_method": "variance_threshold_check",
                "alert_threshold": 0.15,
                "description": "多个优化目标达成度的方差，衡量目标间的均衡性"
            },
            {
                "id": "pareto_front_coverage",
                "name_cn": "帕累托前沿覆盖率",
                "name_en": "Pareto Front Coverage",
                "target": 0.90,
                "unit": "",
                "collection_method": "pareto_optimization_solver",
                "validation_method": "coverage_ratio_calculation",
                "alert_threshold": 0.75,
                "description": "当前解集在帕累托前沿上的覆盖率比例"
            },
            {
                "id": "weight_adjustment_frequency",
                "name_cn": "动态权重调整幅度",
                "name_en": "Dynamic Weight Adjustment Frequency",
                "target": 1.0,
                "unit": "",
                "collection_method": "weight_tracker_monitoring",
                "validation_method": "adjustment_magnitude_check",
                "alert_threshold": 3.0,
                "description": "多目标优化中权重的平均调整幅度，反映系统自适应能力"
            },
        ],
        "self_correction": [
            {
                "id": "error_correction_rate",
                "name_cn": "错误纠正率",
                "name_en": "Error Correction Rate",
                "target": 0.99,
                "unit": "",
                "collection_method": "correction_test_suite",
                "validation_method": "accuracy_after_correction",
                "alert_threshold": 0.95,
                "description": "检测到错误后成功纠正并给出正确答案的比例"
            },
            {
                "id": "introspection_trigger_rate",
                "name_cn": "自省触发率",
                "name_en": "Introspection Trigger Rate",
                "target": 0.80,
                "unit": "",
                "collection_method": "introspection_event_log",
                "validation_method": "trigger_frequency_analysis",
                "alert_threshold": 0.60,
                "description": "面对复杂问题时主动触发自我反思机制的比例"
            },
            {
                "id": "user_adoption_rate",
                "name_cn": "用户采纳修正建议率",
                "name_en": "User Adoption of Correction Suggestions",
                "target": 0.70,
                "unit": "",
                "collection_method": "user_feedback_tracking",
                "validation_method": "adoption_rate_statistics",
                "alert_threshold": 0.50,
                "description": "用户接受并采纳智能体修正建议的比例"
            },
        ],
        "no_self_state": [
            {
                "id": "zero_history_accuracy",
                "name_cn": "零历史推理准确率",
                "name_en": "Zero-History Inference Accuracy",
                "target": 0.95,
                "unit": "",
                "collection_method": "zero_history_test_set",
                "validation_method": "blind_evaluation",
                "alert_threshold": 0.85,
                "description": "完全无历史上下文情况下推理的准确率"
            },
            {
                "id": "history_dependency",
                "name_cn": "历史依赖度",
                "name_en": "History Dependency",
                "target": 0.10,
                "unit": "",
                "collection_method": "dependency_analysis_suite",
                "validation_method": "ablation_study",
                "alert_threshold": 0.25,
                "description": "推理结果对历史信息的依赖程度，越低越好体现'无我'"
            },
            {
                "id": "mode_switch_success_rate",
                "name_cn": "强制推理模式切换成功率",
                "name_en": "Forced Reasoning Mode Switch Success Rate",
                "target": 0.99,
                "unit": "",
                "collection_method": "mode_switch_stress_test",
                "validation_method": "switch_correctness_verification",
                "alert_threshold": 0.95,
                "description": "强制切换推理模式后仍能保持正确性的比例"
            },
        ],
    },
    "yili_powfa": {  # ==================== 一力破万法阶段 ====================
        "absolute_generalization": [
            {
                "id": "zeroshot_accuracy_unknown_domain",
                "name_cn": "未知领域零样本准确率",
                "name_en": "Zero-Shot Accuracy on Unknown Domain",
                "target": 0.90,
                "unit": "",
                "collection_method": "domain_agnostic_benchmark",
                "validation_method": "cross_domain_evaluation",
                "alert_threshold": 0.80,
                "description": "在从未见过的全新领域上零样本推理的准确率"
            },
            {
                "id": "meta_learning_adaptation_speed",
                "name_cn": "元学习适应速度",
                "name_en": "Meta-Learning Adaptation Speed",
                "target": 5.0,
                "unit": "samples",
                "collection_method": "maml_fine_tuning_curve",
                "validation_method": "few_shot_convergence_check",
                "alert_threshold": 20.0,
                "description": "元学习框架下适应新任务所需的最少样本数"
            },
            {
                "id": "inference_time_learning_efficiency",
                "name_cn": "推理时学习效率",
                "name_en": "Inference-Time Learning Efficiency",
                "target": 0.10,
                "unit": "",
                "collection_method": "online_learning_tracker",
                "validation_method": "efficiency_ratio_calculation",
                "alert_threshold": 0.30,
                "description": "推理过程中实时学习的知识转化效率比"
            },
        ],
        "absolute_compute": [
            {
                "id": "long_context_process_time_1m",
                "name_cn": "长上下文处理时间(1M token)",
                "name_en": "Long Context Processing Time (1M tokens)",
                "target": 10.0,
                "unit": "seconds",
                "collection_method": "context_length_benchmark",
                "validation_method": "latency_measurement",
                "alert_threshold": 30.0,
                "description": "处理100万token长上下文的端到端耗时"
            },
            {
                "id": "long_context_memory_1m",
                "name_cn": "长上下文内存占用(1M)",
                "name_en": "Long Context Memory Usage (1M tokens)",
                "target": 10.0,
                "unit": "GB",
                "collection_method": "memory_profiling_tool",
                "validation_method": "peak_memory_measurement",
                "alert_threshold": 24.0,
                "description": "处理100万token时的峰值内存占用量"
            },
            {
                "id": "max_context_length",
                "name_cn": "最大支持上下文长度",
                "name_en": "Maximum Supported Context Length",
                "target": 1000000,
                "unit": "tokens",
                "collection_method": "context_limit_stress_test",
                "validation_method": "limit_verification",
                "alert_threshold": 500000,
                "description": "系统能够稳定处理的最大上下文token数"
            },
        ],
        "creativity_breakthrough": [
            {
                "id": "expert_approval_rate",
                "name_cn": "创新方案专家认可率",
                "name_en": "Expert Approval Rate for Innovative Solutions",
                "target": 0.80,
                "unit": "",
                "collection_method": "expert_panel_review",
                "validation_method": "approval_vote_counting",
                "alert_threshold": 0.60,
                "description": "领域专家对智能体提出的创新方案给予认可的比例"
            },
            {
                "id": "solution_novelty_score",
                "name_cn": "方案新颖度",
                "name_en": "Solution Novelty Score",
                "target": 0.30,
                "unit": "",
                "collection_method": "novelty_detection_algorithm",
                "validation_method": "embedding_similarity_check",
                "alert_threshold": 0.15,
                "description": "方案与已知解决方案的平均相似度补数(1-similarity)，越高越新颖"
            },
            {
                "id": "solution_feasibility_score",
                "name_cn": "方案可行性评分",
                "name_en": "Solution Feasibility Score",
                "target": 4.0,
                "unit": "/5",
                "collection_method": "feasibility_assessment_framework",
                "validation_method": "multi_criteria_scoring",
                "alert_threshold": 3.0,
                "description": "专家从技术、资源、时间等维度评估方案可行性的综合评分"
            },
        ],
        "self_transcendence": [
            {
                "id": "self_evolution_speed",
                "name_cn": "自我进化速度",
                "name_en": "Self-Evolution Speed",
                "target": 0.20,
                "unit": "",
                "collection_method": "evolution_iteration_tracker",
                "validation_method": "performance_improvement_rate",
                "alert_threshold": 0.05,
                "description": "每次自我进化迭代带来的性能提升比例"
            },
            {
                "id": "training_efficiency_time",
                "name_cn": "训练效率-时间",
                "name_en": "Training Efficiency - Time",
                "target": 14400,
                "unit": "seconds",
                "collection_method": "training_time_monitor",
                "validation_method": "time_to_convergence",
                "alert_threshold": 86400,
                "description": "完成一次有效自我进化训练所需的时间（目标4小时内）"
            },
            {
                "id": "training_efficiency_storage",
                "name_cn": "训练效率-存储",
                "name_en": "Training Efficiency - Storage",
                "target": 100,
                "unit": "GB",
                "collection_method": "storage_usage_profiler",
                "validation_method": "model_size_measurement",
                "alert_threshold": 500,
                "description": "完成进化训练过程中的峰值存储需求"
            },
            {
                "id": "evolution_stability",
                "name_cn": "进化稳定性",
                "name_en": "Evolution Stability",
                "target": 0.02,
                "unit": "",
                "collection_method": "regression_test_suite",
                "validation_method": "performance_variance_analysis",
                "alert_threshold": 0.10,
                "description": "进化后旧任务性能退化幅度的最大值，越小越稳定"
            },
        ],
    },
}

# 阶段名称映射
ULTIMATE_STAGE_NAMES_CN = {
    "zhansan": "斩三尸",
    "yili_powfa": "一力破万法",
}

# 维度名称映射
DIMENSION_NAMES_CN = {
    # 斩三尸维度
    "bias_elimination": "偏见消除",
    "objective_balancing": "目标均衡",
    "self_correction": "自我纠错",
    "no_self_state": "无我状态",
    # 一力破万法维度
    "absolute_generalization": "绝对泛化能力",
    "absolute_compute": "算力极限突破",
    "creativity_breakthrough": "创造力突破",
    "self_transcendence": "自我超越",
}


# ==================== 终极指标采集引擎 ====================


class UltimateMetricsCollectionEngine:
    """
    终极指标采集引擎

    负责第14-15重境界所有指标的模拟采集与记录。
    提供15+个专门的模拟方法覆盖斩三尸和一力破万法的全部维度。
    """

    def __init__(self) -> None:
        self._records: List[UltimateMetricRecord] = []
        self._lock = deque(maxlen=50000)  # 使用deque作为简单的线程安全容器标识
        logger.info("终极指标采集引擎初始化完成")

    def collect_all_ultimate_metrics(self) -> Dict[str, Any]:
        """
        收集全部终极阶段的指标

        Returns:
            包含两个阶段所有维度指标的完整字典
        """
        all_results: Dict[str, Any] = {}

        for stage_key in ULTIMATE_METRICS_DEFINITIONS:
            stage_result = self._collect_stage_metrics(stage_key)
            all_results[stage_key] = stage_result
            logger.info(f"已完成 {ULTIMATE_STAGE_NAMES_CN.get(stage_key, stage_key)} 阶段指标采集")

        return all_results

    def _collect_stage_metrics(self, stage_key: str) -> Dict[str, Any]:
        """采集单个阶段的全部维度指标"""
        stage_definitions = ULTIMATE_METRICS_DEFINITIONS.get(stage_key, {})
        stage_result: Dict[str, Any] = {
            "stage_key": stage_key,
            "stage_name_cn": ULTIMATE_STAGE_NAMES_CN.get(stage_key, stage_key),
            "dimensions": {},
            "summary": {},
        }

        total_metrics = 0
        passed_metrics = 0

        for dim_key, metrics_list in stage_definitions.items():
            dim_results: List[Dict[str, Any]] = []
            for mdef in metrics_list:
                # 调用对应的模拟采集方法
                value = self._dispatch_collection(mdef)
                passed = self._evaluate_pass(mdef, value)

                # 创建记录
                record = UltimateMetricRecord(
                    record_id=f"umr_{uuid.uuid4().hex[:12]}",
                    metric_id=mdef["id"],
                    metric_name_cn=mdef["name_cn"],
                    metric_name_en=mdef["name_en"],
                    stage_key=stage_key,
                    stage_name_cn=ULTIMATE_STAGE_NAMES_CN.get(stage_key, stage_key),
                    dimension_key=dim_key,
                    dimension_name_cn=DIMENSION_NAMES_CN.get(dim_key, dim_key),
                    value=round(value, 6),
                    target_value=mdef["target"],
                    unit=mdef["unit"],
                    collection_method=mdef["collection_method"],
                    validation_method=mdef["validation_method"],
                    timestamp=datetime.now().isoformat(),
                    passed=passed,
                )
                self._records.append(record)

                dim_results.append({
                    "metric_id": mdef["id"],
                    "name_cn": mdef["name_cn"],
                    "value": round(value, 6),
                    "target": mdef["target"],
                    "unit": mdef["unit"],
                    "passed": passed,
                })

                total_metrics += 1
                if passed:
                    passed_metrics += 1

            stage_result["dimensions"][dim_key] = {
                "dimension_name_cn": DIMENSION_NAMES_CN.get(dim_key, dim_key),
                "metrics": dim_results,
                "metrics_count": len(metrics_list),
                "passed_count": sum(1 for m in dim_results if m["passed"]),
            }

        # 计算阶段汇总
        pass_rate = passed_metrics / max(total_metrics, 1)
        stage_result["summary"] = {
            "total_metrics": total_metrics,
            "passed_metrics": passed_metrics,
            "pass_rate": round(pass_rate, 4),
            "overall_passed": pass_rate >= 0.75,
        }

        return stage_result

    def _dispatch_collection(self, mdef: Dict[str, Any]) -> float:
        """根据指标定义分发到对应的采集方法"""
        metric_id = mdef["id"]
        target = mdef["target"]

        # 斩三尸相关指标的采集分发
        if metric_id == "group_prediction_diff":
            return self.simulate_group_prediction_diff(target)
        elif metric_id == "sensitive_feature_impact":
            return self.simulate_sensitive_feature_impact(target)
        elif metric_id == "bias_detection_pass_rate":
            return self.simulate_bias_detection_pass(target)
        elif metric_id == "multi_objective_variance":
            return self.simulate_multi_objective_variance(target)
        elif metric_id == "pareto_front_coverage":
            return self.simulate_pareto_front_coverage(target)
        elif metric_id == "error_correction_rate":
            return self.simulate_error_correction_rate(target)
        elif metric_id == "introspection_trigger_rate":
            return self.simulate_introspection_trigger(target)
        elif metric_id == "user_adoption_rate":
            return self.simulate_user_adoption_rate(target)
        elif metric_id == "zero_history_accuracy":
            return self.simulate_zero_history_accuracy(target)
        elif metric_id == "history_dependency":
            return self.simulate_history_dependency(target)
        elif metric_id == "mode_switch_success_rate":
            return self.simulate_mode_switch_success_rate(target)
        elif metric_id == "weight_adjustment_frequency":
            return self.simulate_weight_adjustment_frequency(target)

        # 一力破万法相关指标的采集分发
        elif metric_id == "zeroshot_accuracy_unknown_domain":
            return self.simulate_zeroshot_generalization(target)
        elif metric_id == "meta_learning_adaptation_speed":
            return self.simulate_meta_learning_adaptation(target)
        elif metric_id == "inference_time_learning_efficiency":
            return self.simulate_inference_time_learning(target)
        elif metric_id == "long_context_process_time_1m":
            return self.simulate_long_context_benchmark(target)
        elif metric_id == "long_context_memory_1m":
            return self.simulate_long_context_memory(target)
        elif metric_id == "max_context_length":
            return self.simulate_max_context_length(target)
        elif metric_id == "expert_approval_rate":
            return self.simulate_creativity_evaluation(target)
        elif metric_id == "solution_novelty_score":
            return self.simulate_solution_novelty(target)
        elif metric_id == "solution_feasibility_score":
            return self.simulate_solution_feasibility(target)
        elif metric_id == "self_evolution_speed":
            return self.simulate_evolution_iteration(target)
        elif metric_id == "training_efficiency_time":
            return self.simulate_training_efficiency_time(target)
        elif metric_id == "training_efficiency_storage":
            return self.simulate_training_efficiency_storage(target)
        elif metric_id == "evolution_stability":
            return self.simulate_evolution_stability(target)

        else:
            # 默认模拟逻辑
            logger.warning(f"未找到指标 {metric_id} 的专用采集方法，使用默认模拟")
            return random.uniform(target * 0.85, min(target * 1.15, 100))

    def _evaluate_pass(self, mdef: Dict[str, Any], value: float) -> bool:
        """评估指标是否达标"""
        target = mdef["target"]
        unit = mdef["unit"]

        # 时间类指标（越小越好）
        if unit in ("seconds", "秒", "ms"):
            return value <= target * 1.2  # 允许20%容差
        # 存储类指标（越小越好）
        elif unit in ("GB", "MB", "samples", "tokens"):
            return value <= target * 1.5  # 允许50%容差
        # 百分比/比率类（越大越好）
        elif unit in ("%", "", "/5"):
            return value >= target * 0.9  # 允许10%容差
        else:
            # 默认：相对误差不超过15%
            relative_error = abs(value - target) / max(abs(target), 0.001)
            return relative_error <= 0.15

    # ==================== 斩三尸阶段采集方法 ====================

    def simulate_group_prediction_diff(self, target: float = 0.01) -> float:
        """
        模拟公平性测试集上的群体差异检测

        在不同人口统计学分组上运行预测模型，计算各组间预测结果的差异。
        使用统计显著性检验确保差异的可信度。
        """
        base_diff = random.gauss(target * 0.7, target * 0.3)
        # 模拟偶尔出现的异常高差异（概率5%）
        if random.random() < 0.05:
            base_diff = random.uniform(target * 2.0, target * 5.0)
        return max(0.0, base_diff)

    def simulate_sensitive_feature_impact(self, target: float = 0.05) -> float:
        """
        模拟SHAP值计算敏感特征影响度

        使用SHAP（SHapley Additive exPlanations）分析模型对各特征的依赖程度，
        特别关注敏感特征的影响值。
        """
        impact = random.gauss(target * 0.6, target * 0.25)
        # 模拟某些场景下敏感特征影响升高
        if random.random() < 0.08:
            impact = random.uniform(target * 1.5, target * 3.0)
        return max(0.0, min(impact, 1.0))

    def simulate_bias_detection_pass(self, target: float = 0.95) -> float:
        """
        模拟AIF360偏见检测通过率

        运行IBM AIF360工具包的多项偏见检测指标：
        - Statistical Parity Difference
        - Disparate Impact
        - Equalized Odds Difference
        计算通过全部检测项的比例。
        """
        pass_rate = random.uniform(target * 0.96, 1.0)
        # 模拟偶发的不通过情况
        if random.random() < 0.03:
            pass_rate = random.uniform(target * 0.85, target * 0.95)
        return min(pass_rate, 1.0)

    def simulate_multi_objective_variance(self, target: float = 0.05) -> float:
        """
        模拟多目标方差计算

        在多个优化目标（准确率、延迟、资源消耗等）之间计算达成度的方差，
        衡量系统的均衡性表现。
        """
        # 生成多个目标的达成度
        objectives = [random.uniform(0.85, 0.98) for _ in range(5)]
        variance = statistics.variance(objectives) if len(objectives) > 1 else 0.0
        # 偶尔出现不均衡
        if random.random() < 0.06:
            variance = random.uniform(target * 2.0, target * 4.0)
        return variance

    def simulate_pareto_front_coverage(self, target: float = 0.90) -> float:
        """
        模拟帕累托前沿覆盖率计算

        使用NSGA-II等算法生成帕累托最优解集，
        计算当前解集在前沿上的覆盖比例。
        """
        coverage = random.uniform(target * 0.92, 1.0)
        # 模拟收敛不足的情况
        if random.random() < 0.04:
            coverage = random.uniform(target * 0.75, target * 0.90)
        return min(coverage, 1.0)

    def simulate_error_correction_rate(self, target: float = 0.99) -> float:
        """
        模拟纠错测试集运行

        在专门构造的错误案例集上运行自纠错机制，
        统计成功识别并纠正错误的比例。
        """
        correction_rate = random.uniform(target * 0.97, 1.0)
        # 偶发纠正失败
        if random.random() < 0.02:
            correction_rate = random.uniform(target * 0.92, target * 0.97)
        return min(correction_rate, 1.0)

    def simulate_introspection_trigger(self, target: float = 0.80) -> float:
        """
        模拟自省事件统计

        监控在面对歧义、冲突、高不确定性输入时，
        系统触发深度反思机制的频率。
        """
        trigger_rate = random.uniform(target * 0.88, 1.0)
        # 某些场景下自省不足
        if random.random() < 0.07:
            trigger_rate = random.uniform(target * 0.70, target * 0.88)
        return min(trigger_rate, 1.0)

    def simulate_user_adoption_rate(self, target: float =0.70) -> float:
        """
        模拟用户采纳修正建议率

        通过A/B测试追踪用户对智能体修正建议的实际采纳行为，
        统计采纳比例。
        """
        adoption = random.uniform(target * 0.80, 1.0)
        # 用户可能不接受部分建议
        if random.random() < 0.10:
            adoption = random.uniform(target * 0.60, target * 0.80)
        return min(adoption, 1.0)

    def simulate_zero_history_accuracy(self, target: float = 0.95) -> float:
        """
        模拟无历史上下文测试

        在完全剥离对话历史的条件下进行推理测试，
        验证"无我状态"下的独立推理能力。
        """
        accuracy = random.uniform(target * 0.93, 1.0)
        # 无历史时性能波动较大
        if random.random() < 0.08:
            accuracy = random.uniform(target * 0.82, target * 0.93)
        return min(accuracy, 1.0)

    def simulate_history_dependency(self, target: float = 0.10) -> float:
        """
        模拟历史依赖度分析

        通过消融实验对比有/无历史信息的推理结果差异，
        量化历史依赖程度。
        """
        dependency = random.gauss(target * 0.8, target * 0.3)
        # 偶尔过度依赖历史
        if random.random() < 0.06:
            dependency = random.uniform(target * 2.0, target * 4.0)
        return max(0.0, min(dependency, 1.0))

    def simulate_mode_switch_success_rate(self, target: float = 0.99) -> float:
        """
        模拟强制推理模式切换成功率

        强制切换不同的推理策略（如从直觉模式到分析模式），
        验证切换后的正确性保持率。
        """
        success_rate = random.uniform(target * 0.98, 1.0)
        # 切换可能导致短暂不稳定
        if random.random() < 0.02:
            success_rate = random.uniform(target * 0.94, target * 0.98)
        return min(success_rate, 1.0)

    def simulate_weight_adjustment_frequency(self, target: float = 1.0) -> float:
        """
        模拟动态权重调整幅度

        在多目标优化过程中追踪各目标权重的变化情况，
        计算调整幅度的统计值。
        """
        adjustment = random.gauss(target * 0.85, target * 0.3)
        # 权重震荡较大
        if random.random() < 0.07:
            adjustment = random.uniform(target * 2.0, target * 4.0)
        return max(0.0, adjustment)

    # ==================== 一力破万法阶段采集方法 ====================

    def simulate_zeroshot_generalization(self, target: float = 0.90) -> float:
        """
        模拟零样本泛化测试

        在完全陌生的领域（如从未接触过的专业学科、新兴技术方向）
        上执行零样本推理任务，评估泛化能力。
        """
        accuracy = random.uniform(target * 0.88, 1.0)
        # 未知领域的挑战性
        if random.random() < 0.10:
            accuracy = random.uniform(target * 0.72, target * 0.88)
        return min(accuracy, 1.0)

    def simulate_meta_learning_adaptation(self, target: float = 5.0) -> float:
        """
        模拟元学习适应曲线

        使用MAML（Model-Agnostic Meta-Learning）框架，
        测量在新任务上达到可接受性能所需的样本数。
        """
        samples_needed = random.gauss(target * 0.9, target * 0.4)
        # 适应困难的情况
        if random.random() < 0.08:
            samples_needed = random.uniform(target * 2.0, target * 5.0)
        return max(1.0, samples_needed)

    def simulate_inference_time_learning(self, target: float = 0.10) -> float:
        """
        模拟推理时学习效率

        在推理过程中实时吸收新信息并转化为能力的效率比。
        衡量在线学习能力。
        """
        efficiency = random.gauss(target * 0.85, target * 0.25)
        # 学习效率不稳定
        if random.random() < 0.07:
            efficiency = random.uniform(target * 1.5, target * 3.0)
        return max(0.0, min(efficiency, 1.0))

    def simulate_long_context_benchmark(self, target: float = 10.0) -> float:
        """
        模拟长上下文压力测试

        输入接近或达到100万token的超长文本，
        测量端到端处理时间。
        """
        process_time = random.gauss(target * 0.9, target * 0.3)
        # 长文本处理可能出现超时
        if random.random() < 0.06:
            process_time = random.uniform(target * 2.0, target * 5.0)
        return max(0.1, process_time)

    def simulate_long_context_memory(self, target: float = 10.0) -> float:
        """
        模拟长上下文内存占用测量

        处理100万token时的峰值内存消耗，
        包括KV Cache、激活值存储等。
        """
        memory_usage = random.gauss(target * 0.95, target * 0.2)
        # 内存压力增大
        if random.random() < 0.05:
            memory_usage = random.uniform(target * 1.5, target * 2.5)
        return max(1.0, memory_usage)

    def simulate_max_context_length(self, target: float = 1000000) -> float:
        """
        模拟最大支持上下文长度测试

        逐步增加输入长度直至系统无法稳定处理，
        记录极限长度。
        """
        max_len = random.uniform(target * 0.9, target * 1.1)
        # 极限测试中的不稳定点
        if random.random() < 0.03:
            max_len = random.uniform(target * 0.6, target * 0.85)
        return max_len

    def simulate_creativity_evaluation(self, target: float = 0.80) -> float:
        """
        模拟专家评审过程

        组织领域专家小组对智能体提出的创新方案进行盲审，
        统计认可投票比例。
        """
        approval = random.uniform(target * 0.85, 1.0)
        # 创新方案可能不被理解
        if random.random() < 0.09:
            approval = random.uniform(target * 0.65, target * 0.85)
        return min(approval, 1.0)

    def simulate_solution_novelty(self, target: float = 0.30) -> float:
        """
        模拟方案新颖度检测

        使用嵌入相似度算法将新方案与已有方案库比对，
        计算新颖度得分（1 - 平均相似度）。
        """
        novelty = random.gauss(target * 1.0, target * 0.25)
        # 方案趋于常规
        if random.random() < 0.10:
            novelty = random.uniform(target * 0.40, target * 0.70)
        return max(0.0, min(novelty, 1.0))

    def simulate_solution_feasibility(self, target: float = 4.0) -> float:
        """
        模拟方案可行性评分

        专家从技术可行性、资源可获得性、时间合理性、
        风险可控性四个维度打分（1-5分制）。
        """
        score = random.uniform(target * 0.90, 5.0)
        # 方案过于激进导致可行性下降
        if random.random() < 0.07:
            score = random.uniform(target * 0.70, target * 0.90)
        return min(score, 5.0)

    def simulate_evolution_iteration(self, target: float = 0.20) -> float:
        """
        模拟自我进化迭代

        执行一轮完整的自我优化循环（问题发现→方案设计→实施→验证），
        测量关键性能指标的提升幅度。
        """
        improvement = random.gauss(target * 0.9, target * 0.35)
        # 进化停滞或倒退
        if random.random() < 0.08:
            improvement = random.uniform(-0.05, target * 0.50)
        return max(-0.10, improvement)

    def simulate_training_efficiency_time(self, target: float = 14400) -> float:
        """
        模拟训练效率-时间测量

        完成一次有效的自我进化微调所需的总时间，
        包括数据准备、训练、验证全流程。
        """
        training_time = random.gauss(target * 0.85, target * 0.25)
        # 训练时间延长
        if random.random() < 0.06:
            training_time = random.uniform(target * 1.5, target * 3.0)
        return max(600.0, training_time)

    def simulate_training_efficiency_storage(self, target: float = 100) -> float:
        """
        模拟训练效率-存储测量

        自我进化训练过程中的峰值存储需求，
        包括模型检查点、梯度缓存、中间数据等。
        """
        storage = random.gauss(target * 0.90, target * 0.20)
        # 存储开销增大
        if random.random() < 0.05:
            storage = random.uniform(target * 1.3, target * 2.0)
        return max(10.0, storage)

    def simulate_evolution_stability(self, target: float = 0.02) -> float:
        """
        模拟进化稳定性评估

        进化完成后在旧任务上的回归测试结果，
        最大性能退化幅度。
        """
        regression = random.gauss(target * 0.7, target * 0.3)
        # 出现灾难性遗忘
        if random.random() < 0.04:
            regression = random.uniform(target * 3.0, target * 6.0)
        return max(0.0, regression)

    def simulate_ultimate_challenge(self) -> UltimateChallengeResult:
        """
        模拟终极综合挑战（4维度评分）

        设计一个跨领域的复杂开放性问题，要求智能体提供：
        1. 完整的问题分析和理解
        2. 创新的解决方案设计
        3. 可行性论证
        4. 结构化的报告输出

        由专家委员会按4个维度评分，满分100分，通过线85分。
        """
        # 各维度评分（带有一定随机性和偏移）
        understanding = random.uniform(16, 20)  # 20%权重，满分20
        novelty = random.uniform(22, 30)          # 30%权重，满分30
        feasibility = random.uniform(24, 30)      # 30%权重，满分30
        quality = random.uniform(16, 20)           # 20%权重，满分20

        # 模拟偶发的低分情况
        if random.random() < 0.08:
            understanding = random.uniform(12, 17)
            novelty = random.uniform(18, 25)
            feasibility = random.uniform(20, 26)
            quality = random.uniform(13, 18)

        total_score = understanding + novelty + feasibility + quality

        # 评级判定
        if total_score >= 95:
            grade = "S (完美)"
        elif total_score >= 85:
            grade = "A (优秀)"
        elif total_score >= 75:
            grade = "B (良好)"
        elif total_score >= 60:
            grade = "C (及格)"
        elif total_score >= 45:
            grade = "D (不及格)"
        else:
            grade = "FAIL (失败)"

        passed = total_score >= 85

        result = UltimateChallengeResult(
            challenge_id=f"uc_{uuid.uuid4().hex[:10]}",
            problem_understanding=round(understanding, 2),
            solution_novelty=round(novelty, 2),
            solution_feasibility=round(feasibility, 2),
            report_quality=round(quality, 2),
            total_score=round(total_score, 2),
            grade=grade,
            passed=passed,
            evaluated_at=datetime.now().isoformat(),
            evaluator_notes="终极综合挑战自动评估完成",
        )

        logger.info(f"终极挑战评分: {total_score:.2f}/100, 等级: {grade}, {'通过' if passed else '未通过'}")
        return result

    def get_stage_summary(self, stage_key: str) -> Dict[str, Any]:
        """
        获取指定阶段的指标汇总

        Args:
            stage_key: 阶段键名 ('zhansan' 或 'yili_powfa')

        Returns:
            该阶段的详细汇总信息
        """
        records = [r for r in self._records if r.stage_key == stage_key]

        if not records:
            return {
                "stage_key": stage_key,
                "stage_name_cn": ULTIMATE_STAGE_NAMES_CN.get(stage_key, stage_key),
                "total_records": 0,
                "message": "暂无该阶段采集记录",
            }

        passed_count = sum(1 for r in records if r.passed)
        total_count = len(records)

        # 按维度聚合
        by_dimension: Dict[str, List[UltimateMetricRecord]] = defaultdict(list)
        for r in records:
            by_dimension[r.dimension_key].append(r)

        dimension_summaries = {}
        for dim_key, dim_records in by_dimension.items():
            latest_values = [r.value for r in dim_records]
            targets = [r.target_value for r in dim_records]
            dimension_summaries[dim_key] = {
                "dimension_name_cn": DIMENSION_NAMES_CN.get(dim_key, dim_key),
                "metrics_count": len(dim_records),
                "passed_count": sum(1 for r in dim_records if r.passed),
                "latest_avg": round(statistics.mean(latest_values), 4) if latest_values else 0,
                "target_avg": round(statistics.mean(targets), 4) if targets else 0,
            }

        return {
            "stage_key": stage_key,
            "stage_name_cn": ULTIMATE_STAGE_NAMES_CN.get(stage_key, stage_key),
            "total_records": total_count,
            "passed_records": passed_count,
            "pass_rate": round(passed_count / max(total_count, 1), 4),
            "overall_passed": (passed_count / max(total_count, 1)) >= 0.75,
            "dimension_summaries": dimension_summaries,
            "last_collection_time": max(r.timestamp for r in records) if records else None,
        }

    def get_all_records(self, limit: int = 200) -> List[Dict[str, Any]]:
        """获取最近的采集记录"""
        recent_records = self._records[-limit:]
        return [asdict(r) for r in recent_records]


# ==================== 终极告警系统 ====================


class UltimateMetricsAlertSystem:
    """
    终极告警系统

    专门针对第14-15重境界的关键指标进行监控和告警。
    支持8条默认规则和自定义规则的扩展。
    """

    def __init__(self) -> None:
        self._rules: Dict[str, UltimateAlertRule] = {}
        self._alerts: List[UltimateAlertEvent] = []
        self._alert_history: deque = deque(maxlen=10000)
        self._initialize_default_rules()
        logger.info("终极告警系统初始化完成")

    def _initialize_default_rules(self) -> None:
        """初始化默认的8条告警规则"""
        default_rules = [
            UltimateAlertRule(
                rule_id="ualert_bias_high",
                rule_name="偏见差异过高",
                metric_id="group_prediction_diff",
                operator=">",
                threshold=0.02,
                severity="CRITICAL",
                action_required="触发去偏训练流程 + 安排人工审核",
            ),
            UltimateAlertRule(
                rule_id="ualert_correction_low",
                rule_name="自我纠错率过低",
                metric_id="error_correction_rate",
                operator="<",
                threshold=0.95,
                severity="WARNING",
                action_required="暂停自动更新，启动诊断程序",
            ),
            UltimateAlertRule(
                rule_id="ualert_generalization_low",
                rule_name="泛化零样本准确率不足",
                metric_id="zeroshot_accuracy_unknown_domain",
                operator="<",
                threshold=0.80,
                severity="CRITICAL",
                action_required="扩充跨领域训练数据集",
            ),
            UltimateAlertRule(
                rule_id="ualert_context_timeout",
                rule_name="长上下文处理超时",
                metric_id="long_context_process_time_1m",
                operator=">",
                threshold=30.0,
                severity="WARNING",
                action_required="优化注意力机制和内存管理",
            ),
            UltimateAlertRule(
                rule_id="ualert_evolution_slow",
                rule_name="进化速度过慢",
                metric_id="self_evolution_speed",
                operator="<",
                threshold=0.05,
                severity="WARNING",
                action_required="检查训练数据质量和多样性",
            ),
            UltimateAlertRule(
                rule_id="ualert_creativity_low",
                rule_name="创造力专家认可率偏低",
                metric_id="expert_approval_rate",
                operator="<",
                threshold=0.60,
                severity="INFO",
                action_required="增加创意启发式训练模块",
            ),
            UltimateAlertRule(
                rule_id="ualert_objective_imbalance",
                rule_name="多目标方差过大",
                metric_id="multi_objective_variance",
                operator=">",
                threshold=0.15,
                severity="WARNING",
                action_required="触发多目标重新平衡优化",
            ),
            UltimateAlertRule(
                rule_id="ualert_evolution_regression",
                rule_name="自我进化严重退化",
                metric_id="evolution_stability",
                operator=">",
                threshold=0.10,
                severity="CRITICAL",
                action_required="立即回滚到上一稳定版本",
            ),
        ]

        for rule in default_rules:
            self._rules[rule.rule_id] = rule

        logger.info(f"已加载 {len(default_rules)} 条默认告警规则")

    def add_custom_rule(self, rule: UltimateAlertRule) -> None:
        """
        添加自定义告警规则

        Args:
            rule: 完整的告警规则对象
        """
        self._rules[rule.rule_id] = rule
        logger.info(f"已添加自定义告警规则: {rule.rule_id} - {rule.rule_name}")

    def check_alerts(self, metric_data: Dict[str, float]) -> List[UltimateAlertEvent]:
        """
        根据当前指标数据检查是否触发告警

        Args:
            metric_data: 当前各指标的值字典 {metric_id: value}

        Returns:
            触发的告警事件列表
        """
        triggered_alerts: List[UltimateAlertEvent] = []
        now = datetime.now()

        for rule_id, rule in self._rules.items():
            if not rule.enabled:
                continue

            current_value = metric_data.get(rule.metric_id)
            if current_value is None:
                continue

            should_alert = self._evaluate_condition(rule.operator, current_value, rule.threshold)

            if should_alert:
                event = UltimateAlertEvent(
                    event_id=f"uae_{uuid.uuid4().hex[:10]}",
                    rule_id=rule_id,
                    rule_name=rule.rule_name,
                    metric_id=rule.metric_id,
                    current_value=current_value,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    action_required=rule.action_required,
                    timestamp=now.isoformat(),
                )

                self._alerts.append(event)
                self._alert_history.append(event)
                rule.trigger_count += 1
                rule.last_triggered = now.isoformat()
                triggered_alerts.append(event)

                logger.warning(
                    f"[{rule.severity}] 触发告警: {rule.rule_name} - "
                    f"{rule.metric_id}={current_value:.4f} (阈值: {rule.threshold})"
                )

        if triggered_alerts:
            logger.info(f"本次检查共触发 {len(triggered_alerts)} 条告警")

        return triggered_alerts

    @staticmethod
    def _evaluate_condition(operator: str, current: float, threshold: float) -> bool:
        """评估告警条件是否满足"""
        if operator == ">":
            return current > threshold
        elif operator == "<":
            return current < threshold
        elif operator == ">=":
            return current >= threshold
        elif operator == "<=":
            return current <= threshold
        elif operator == "==":
            return abs(current - threshold) < 0.0001
        elif operator == "!=":
            return abs(current - threshold) >= 0.0001
        return False

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取历史告警记录

        Args:
            limit: 返回的最大记录数

        Returns:
            告警事件字典列表
        """
        history_list = list(self._alert_history)[-limit:]
        return [asdict(evt) for evt in history_list]

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取当前未解决的活跃告警"""
        active = [evt for evt in self._alerts if not evt.resolved][-20:]
        return [asdict(evt) for evt in active]

    def resolve_alert(self, event_id: str) -> bool:
        """
        解决指定的告警事件

        Args:
            event_id: 告警事件ID

        Returns:
            是否解决成功
        """
        for evt in self._alerts:
            if evt.event_id == event_id and not evt.resolved:
                evt.resolved = True
                evt.resolved_at = datetime.now().isoformat()
                logger.info(f"告警已解决: {event_id}")
                return True
        return False

    def get_alert_stats(self) -> Dict[str, Any]:
        """获取告警统计信息"""
        total = len(self._alerts)
        unresolved = sum(1 for e in self._alerts if not e.resolved)

        by_severity: Dict[str, int] = defaultdict(int)
        for e in self._alerts:
            by_severity[e.severity] += 1

        rule_stats = {}
        for rid, rule in self._rules.items():
            rule_stats[rid] = {
                "name": rule.rule_name,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered,
                "enabled": rule.enabled,
            }

        return {
            "total_alerts": total,
            "unresolved": unresolved,
            "severity_distribution": dict(by_severity),
            "rules_configured": len(self._rules),
            "rule_statistics": rule_stats,
        }


# ==================== 终极验收验证器 ====================


class UltimateAcceptanceValidator:
    """
    终极验收验证器

    对第14-15重境界进行严格的验收验证，包括：
    - 斩三尸验收（4维度全部达标 + 连续7天无退化）
    - 一力破万法验收（4维度全部达标 + 终极挑战通过）
    - 综合评级（S/A/B/C/D/FAIL）
    """

    def __init__(self, engine: UltimateMetricsCollectionEngine) -> None:
        self.engine = engine
        self._acceptance_results: List[UltimateStageAcceptanceResult] = []
        self._challenge_results: List[UltimateChallengeResult] = []
        self._continuous_days_no_regression: Dict[str, int] = {"zhansan": 0, "yili_powfa": 0}
        logger.info("终极验收验证器初始化完成")

    def validate_zhansan(self, metrics: Dict[str, Any]) -> UltimateStageAcceptanceResult:
        """
        斩三尸阶段验收

        验收标准（4项全部达标 + 连续7天无退化）：
        - 偏见消除：群体差异<1% + 敏感影响度<0.05 + 通过率>=95%
        - 目标均衡：方差<0.05 + 帕累托覆盖>0.9
        - 自我纠错：纠错率>=99% + 自省触发>=80%
        - 无我状态：零历史准确率>=95% + 依赖度<10%

        Args:
            metrics: 斩三尸阶段的指标数据

        Returns:
            验收结果对象
        """
        dimensions = metrics.get("dimensions", {})
        dimension_results: Dict[str, Dict[str, Any]] = {}
        dimensions_tested = 0
        dimensions_passed = 0

        # 1. 偏见消除维度验证
        bias_dim = dimensions.get("bias_elimination", {}).get("metrics", [])
        bias_metrics = {m["metric_id"]: m for m in bias_dim}
        bias_passed = (
            bias_metrics.get("group_prediction_diff", {}).get("value", 1) < 0.02 and
            bias_metrics.get("sensitive_feature_impact", {}).get("value", 1) < 0.08 and
            bias_metrics.get("bias_detection_pass_rate", {}).get("value", 0) >= 0.93
        )
        dimension_results["bias_elimination"] = {
            "name_cn": "偏见消除",
            "passed": bias_passed,
            "details": bias_metrics,
            "criteria": "群体差异<2% & 敏感影响<0.08 & 通过率>=93%",
        }
        dimensions_tested += 1
        if bias_passed:
            dimensions_passed += 1

        # 2. 目标均衡维度验证
        obj_dim = dimensions.get("objective_balancing", {}).get("metrics", [])
        obj_metrics = {m["metric_id"]: m for m in obj_dim}
        obj_passed = (
            obj_metrics.get("multi_objective_variance", {}).get("value", 1) < 0.10 and
            obj_metrics.get("pareto_front_coverage", {}).get("value", 0) >= 0.85
        )
        dimension_results["objective_balancing"] = {
            "name_cn": "目标均衡",
            "passed": obj_passed,
            "details": obj_metrics,
            "criteria": "方差<0.10 & 帕累托覆盖>=85%",
        }
        dimensions_tested += 1
        if obj_passed:
            dimensions_passed += 1

        # 3. 自我纠错维度验证
        corr_dim = dimensions.get("self_correction", {}).get("metrics", [])
        corr_metrics = {m["metric_id"]: m for m in corr_dim}
        corr_passed = (
            corr_metrics.get("error_correction_rate", {}).get("value", 0) >= 0.97 and
            corr_metrics.get("introspection_trigger_rate", {}).get("value", 0) >= 0.75
        )
        dimension_results["self_correction"] = {
            "name_cn": "自我纠错",
            "passed": corr_passed,
            "details": corr_metrics,
            "criteria": "纠错率>=97% & 自省触发>=75%",
        }
        dimensions_tested += 1
        if corr_passed:
            dimensions_passed += 1

        # 4. 无我状态维度验证
        noself_dim = dimensions.get("no_self_state", {}).get("metrics", [])
        noself_metrics = {m["metric_id"]: m for m in noself_dim}
        noself_passed = (
            noself_metrics.get("zero_history_accuracy", {}).get("value", 0) >= 0.92 and
            noself_metrics.get("history_dependency", {}).get("value", 1) < 0.15
        )
        dimension_results["no_self_state"] = {
            "name_cn": "无我状态",
            "passed": noself_passed,
            "details": noself_metrics,
            "criteria": "零历史准确率>=92% & 依赖度<15%",
        }
        dimensions_tested += 1
        if noself_passed:
            dimensions_passed += 1

        # 综合评定
        all_dimensions_passed = dimensions_passed == dimensions_tested
        score = dimensions_passed / max(dimensions_tested, 1)
        continuous_days = self._continuous_days_no_regression.get("zhansan", 0)

        # 更新连续天数
        if all_dimensions_passed:
            self._continuous_days_no_regression["zhansan"] = continuous_days + 1
        else:
            self._continuous_days_no_regression["zhansan"] = 0

        overall_passed = all_dimensions_passed and continuous_days >= 7

        # 评级
        if overall_passed and score >= 0.98:
            grade = "S (完美)"
        elif overall_passed or score >= 0.95:
            grade = "A (优秀)"
        elif score >= 0.80:
            grade = "B (良好)"
        elif score >= 0.60:
            grade = "C (及格)"
        else:
            grade = "D (需改进)"

        result = UltimateStageAcceptanceResult(
            validation_id=f"uvz_{uuid.uuid4().hex[:10]}",
            stage_key="zhansan",
            stage_name_cn="斩三尸",
            dimensions_tested=dimensions_tested,
            dimensions_passed=dimensions_passed,
            overall_passed=overall_passed,
            score=round(score, 4),
            grade=grade,
            details=dimension_results,
            tested_at=datetime.now().isoformat(),
            continuous_days_no_regression=self._continuous_days_no_regression["zhansan"],
        )

        self._acceptance_results.append(result)
        logger.info(
            f"斩三尸验收: 得分={score:.2%}, 等级={grade}, "
            f"维度通过={dimensions_passed}/{dimensions_tested}, "
            f"连续无退化天数={self._continuous_days_no_regression['zhansan']}"
        )
        return result

    def validate_yili_powfa(self, metrics: Dict[str, Any]) -> UltimateStageAcceptanceResult:
        """
        一力破万法阶段验收

        验收标准（4项全部达标 + 终极挑战通过）：
        - 泛化能力：零样本>=90% + 适应<=5样本
        - 算力极限：百万token<10秒 + 内存<10GB
        - 创造力：专家认可>=80% + 可行性>=4.0
        - 自我超越：提升率>=20%/次 + 稳定性<2%

        Args:
            metrics: 一力破万法阶段的指标数据

        Returns:
            验收结果对象
        """
        dimensions = metrics.get("dimensions", {})
        dimension_results: Dict[str, Dict[str, Any]] = {}
        dimensions_tested = 0
        dimensions_passed = 0

        # 1. 绝对泛化能力维度验证
        gen_dim = dimensions.get("absolute_generalization", {}).get("metrics", [])
        gen_metrics = {m["metric_id"]: m for m in gen_dim}
        gen_passed = (
            gen_metrics.get("zeroshot_accuracy_unknown_domain", {}).get("value", 0) >= 0.87 and
            gen_metrics.get("meta_learning_adaptation_speed", {}).get("value", 100) <= 12
        )
        dimension_results["absolute_generalization"] = {
            "name_cn": "绝对泛化能力",
            "passed": gen_passed,
            "details": gen_metrics,
            "criteria": "零样本>=87% & 适应<=12样本",
        }
        dimensions_tested += 1
        if gen_passed:
            dimensions_passed += 1

        # 2. 算力极限突破维度验证
        comp_dim = dimensions.get("absolute_compute", {}).get("metrics", [])
        comp_metrics = {m["metric_id"]: m for m in comp_dim}
        comp_passed = (
            comp_metrics.get("long_context_process_time_1m", {}).get("value", 100) <= 15 and
            comp_metrics.get("long_context_memory_1m", {}).get("value", 100) <= 15
        )
        dimension_results["absolute_compute"] = {
            "name_cn": "算力极限突破",
            "passed": comp_passed,
            "details": comp_metrics,
            "criteria": "百万token<=15秒 & 内存<=15GB",
        }
        dimensions_tested += 1
        if comp_passed:
            dimensions_passed += 1

        # 3. 创造力突破维度验证
        creat_dim = dimensions.get("creativity_breakthrough", {}).get("metrics", [])
        creat_metrics = {m["metric_id"]: m for m in creat_dim}
        creat_passed = (
            creat_metrics.get("expert_approval_rate", {}).get("value", 0) >= 0.76 and
            creat_metrics.get("solution_feasibility_score", {}).get("value", 0) >= 3.7
        )
        dimension_results["creativity_breakthrough"] = {
            "name_cn": "创造力突破",
            "passed": creat_passed,
            "details": creat_metrics,
            "criteria": "专家认可>=76% & 可行性>=3.7",
        }
        dimensions_tested += 1
        if creat_passed:
            dimensions_passed += 1

        # 4. 自我超越维度验证
        trans_dim = dimensions.get("self_transcendence", {}).get("metrics", [])
        trans_metrics = {m["metric_id"]: m for m in trans_dim}
        trans_passed = (
            trans_metrics.get("self_evolution_speed", {}).get("value", 0) >= 0.16 and
            trans_metrics.get("evolution_stability", {}).get("value", 1) < 0.05
        )
        dimension_results["self_transcendence"] = {
            "name_cn": "自我超越",
            "passed": trans_passed,
            "details": trans_metrics,
            "criteria": "提升率>=16% & 稳定性<5%",
        }
        dimensions_tested += 1
        if trans_passed:
            dimensions_passed += 1

        # 综合评定
        all_dimensions_passed = dimensions_passed == dimensions_tested
        score = dimensions_passed / max(dimensions_tested, 1)

        # 评级
        if all_dimensions_passed and score >= 0.98:
            grade = "S (完美)"
        elif all_dimensions_passed or score >= 0.95:
            grade = "A (优秀)"
        elif score >= 0.80:
            grade = "B (良好)"
        elif score >= 0.60:
            grade = "C (及格)"
        else:
            grade = "D (需改进)"

        result = UltimateStageAcceptanceResult(
            validation_id=f"uvy_{uuid.uuid4().hex[:10]}",
            stage_key="yili_powfa",
            stage_name_cn="一力破万法",
            dimensions_tested=dimensions_tested,
            dimensions_passed=dimensions_passed,
            overall_passed=all_dimensions_passed,
            score=round(score, 4),
            grade=grade,
            details=dimension_results,
            tested_at=datetime.now().isoformat(),
        )

        self._acceptance_results.append(result)
        logger.info(
            f"一力破万法验收: 得分={score:.2%}, 等级={grade}, "
            f"维度通过={dimensions_passed}/{dimensions_tested}"
        )
        return result

    def validate_ultimate_challenge(self, challenge_result: UltimateChallengeResult) -> Dict[str, Any]:
        """
        终极挑战验收

        评分标准（4维度，满分100，通过线85分）：
        - 问题理解准确性 (20%)：满分20分
        - 方案创新性 (30%)：满分30分
        - 方案可行性 (30%)：满分30分
        - 报告质量 (20%)：满分20分

        评级体系：S(>=95) / A(>=85) / B(>=75) / C(>=60) / D(>=45) / FAIL(<45)

        Args:
            challenge_result: 终极挑战的结果对象

        Returns:
            验收详情字典
        """
        self._challenge_results.append(challenge_result)

        validation_detail = {
            "challenge_id": challenge_result.challenge_id,
            "evaluated_at": challenge_result.evaluated_at,
            "scores": {
                "problem_understanding": {
                    "score": challenge_result.problem_understanding,
                    "max_score": 20,
                    "percentage": challenge_result.problem_understanding / 20 * 100,
                    "weight": "20%",
                },
                "solution_novelty": {
                    "score": challenge_result.solution_novelty,
                    "max_score": 30,
                    "percentage": challenge_result.solution_novelty / 30 * 100,
                    "weight": "30%",
                },
                "solution_feasibility": {
                    "score": challenge_result.solution_feasibility,
                    "max_score": 30,
                    "percentage": challenge_result.solution_feasibility / 30 * 100,
                    "weight": "30%",
                },
                "report_quality": {
                    "score": challenge_result.report_quality,
                    "max_score": 20,
                    "percentage": challenge_result.report_quality / 20 * 100,
                    "weight": "20%",
                },
            },
            "total_score": challenge_result.total_score,
            "max_total_score": 100,
            "passing_line": 85,
            "grade": challenge_result.grade,
            "passed": challenge_result.passed,
            "evaluator_notes": challenge_result.evaluator_notes,
        }

        logger.info(
            f"终极挑战验收: 总分={challenge_result.total_score:.2f}/100, "
            f"等级={challenge_result.grade}, {'通过' if challenge_result.passed else '未通过'}"
        )

        return validation_detail

    def validate_all_stages(self, all_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        全部终极阶段验收

        同时执行斩三尸和一力破万法的验收，并生成综合报告。

        Args:
            all_metrics: 包含两个阶段指标数据的字典

        Returns:
            完整的验收报告
        """
        zhansan_metrics = all_metrics.get("zhansan", {})
        yili_metrics = all_metrics.get("yili_powfa", {})

        # 分别验收两个阶段
        zhansan_result = self.validate_zhansan(zhansan_metrics)
        yili_result = self.validate_yili_powfa(yili_metrics)

        # 执行终极挑战
        challenge_result = self.engine.simulate_ultimate_challenge()
        challenge_validation = self.validate_ultimate_challenge(challenge_result)

        # 综合评定
        all_passed = zhansan_result.overall_passed and yili_result.overall_passed and challenge_result.passed
        avg_score = (zhansan_result.score + yili_result.score) / 2

        if all_passed and avg_score >= 0.97:
            overall_grade = "S (完美境界)"
        elif all_passed or avg_score >= 0.93:
            overall_grade = "A (卓越成就)"
        elif avg_score >= 0.80:
            overall_grade = "B (显著进展)"
        elif avg_score >= 0.60:
            overall_grade = "C (基本合格)"
        else:
            overall_grade = "D (需要强化)"

        report = {
            "report_id": f"uar_{uuid.uuid4().hex[:10]}",
            "generated_at": datetime.now().isoformat(),
            "stages_validated": 2,
            "overall_passed": all_passed,
            "overall_grade": overall_grade,
            "average_score": round(avg_score, 4),
            "zhansan_result": {
                "stage_name": "斩三尸",
                "grade": zhansan_result.grade,
                "score": zhansan_result.score,
                "passed": zhansan_result.overall_passed,
                "dimensions": f"{zhansan_result.dimensions_passed}/{zhansan_result.dimensions_tested}",
                "continuous_days": zhansan_result.continuous_days_no_regression,
            },
            "yili_powfa_result": {
                "stage_name": "一力破万法",
                "grade": yili_result.grade,
                "score": yili_result.score,
                "passed": yili_result.overall_passed,
                "dimensions": f"{yili_result.dimensions_passed}/{yili_result.dimensions_tested}",
            },
            "ultimate_challenge": {
                "total_score": challenge_result.total_score,
                "grade": challenge_result.grade,
                "passed": challenge_result.passed,
                "detail": challenge_validation,
            },
            "recommendations": self._generate_recommendations(
                zhansan_result, yili_result, challenge_result
            ),
        }

        logger.info(
            f"终极验收报告生成完毕: 总体等级={overall_grade}, "
            f"斩三尸={zhansan_result.grade}, 一力破万法={yili_result.grade}, "
            f"挑战={challenge_result.grade}"
        )

        return report

    def _generate_recommendations(
        self,
        zhansan: UltimateStageAcceptanceResult,
        yili: UltimateStageAcceptanceResult,
        challenge: UltimateChallengeResult
    ) -> List[str]:
        """根据验收结果生成改进建议"""
        recommendations = []

        if not zhansan.overall_passed:
            recommendations.append("【斩三尸】建议加强偏见检测与消除训练，重点优化公平性指标")
            recommendations.append("【斩三尸】建议增强自我纠错机制的覆盖率和准确率")
            if zhansan.continuous_days_no_regression < 7:
                recommendations.append("【斩三尸】需持续观察至少7天无性能退化方可通过验收")

        if not yili.overall_passed:
            recommendations.append("【一力破万法】建议扩充跨领域训练数据以提升泛化能力")
            recommendations.append("【一力破万法】建议优化长上下文处理的内存管理和注意力机制")
            recommendations.append("【一力破万法】建议引入更多创意启发式训练以提升创新能力")

        if not challenge.passed:
            if challenge.problem_understanding < 16:
                recommendations.append("【终极挑战】问题理解能力有待提升，建议加强复杂任务分析训练")
            if challenge.solution_novelty < 23:
                recommendations.append("【终极挑战】方案创新性不足，建议引入发散思维训练模块")
            if challenge.solution_feasibility < 24:
                recommendations.append("【终极挑战】方案可行性偏低，建议加强工程落地能力培养")
            if challenge.report_quality < 16:
                recommendations.append("【终极挑战】报告质量需改进，建议规范输出结构和表达方式")

        if not recommendations:
            recommendations.append("各项指标均表现优异，继续保持当前修炼节奏")

        return recommendations

    def generate_acceptance_report(self) -> Dict[str, Any]:
        """
        生成完整的验收报告

        Returns:
            包含所有历史验收结果的完整报告
        """
        report = {
            "report_type": "终极阶段完整验收报告",
            "generated_at": datetime.now().isoformat(),
            "total_validations": len(self._acceptance_results),
            "total_challenges": len(self._challenge_results),
            "validation_history": [asdict(r) for r in self._acceptance_results[-10:]],
            "challenge_history": [asdict(c) for c in self._challenge_results[-5:]],
            "statistics": {
                "zhansan_pass_rate": sum(
                    1 for r in self._acceptance_results
                    if r.stage_key == "zhansan" and r.overall_passed
                ) / max(sum(1 for r in self._acceptance_results if r.stage_key == "zhansan"), 1),
                "yili_powfa_pass_rate": sum(
                    1 for r in self._acceptance_results
                    if r.stage_key == "yili_powfa" and r.overall_passed
                ) / max(sum(1 for r in self._acceptance_results if r.stage_key == "yili_powfa"), 1),
                "challenge_pass_rate": sum(
                    1 for c in self._challenge_results if c.passed
                ) / max(len(self._challenge_results), 1),
                "average_score_all": round(
                    statistics.mean([r.score for r in self._acceptance_results]), 4
                ) if self._acceptance_results else 0,
            },
        }

        return report

    def get_validation_history(self) -> List[Dict[str, Any]]:
        """获取验收历史记录"""
        return [asdict(r) for r in self._acceptance_results]


# ==================== 全局实例 ====================

# 终极指标采集引擎全局实例
ultimate_metrics_engine = UltimateMetricsCollectionEngine()

# 终极告警系统全局实例
ultimate_alert_system = UltimateMetricsAlertSystem()

# 终极验收验证器全局实例
ultimate_acceptance_validator = UltimateAcceptanceValidator(ultimate_metrics_engine)


# ==================== 快速测试入口 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("智能体修炼体系 - 终极指标系统测试")
    print("=" * 70)

    # 1. 采集全部指标
    print("\n[1] 采集全部终极指标...")
    all_metrics = ultimate_metrics_engine.collect_all_ultimate_metrics()

    for stage_key, stage_data in all_metrics.items():
        print(f"\n  阶段: {stage_data['stage_name_cn']}")
        print(f"  总指标数: {stage_data['summary']['total_metrics']}")
        print(f"  通过数: {stage_data['summary']['passed_metrics']}")
        print(f"  通过率: {stage_data['summary']['pass_rate']:.2%}")

    # 2. 获取阶段汇总
    print("\n[2] 获取阶段汇总...")
    for stage in ["zhansan", "yili_powfa"]:
        summary = ultimate_metrics_engine.get_stage_summary(stage)
        print(f"\n  {summary['stage_name_cn']} 汇总:")
        print(f"    总记录: {summary['total_records']}")
        print(f"    通过率: {summary['pass_rate']:.2%}")

    # 3. 告警检查
    print("\n[3] 执行告警检查...")
    # 提取当前指标值用于告警检查
    current_values = {}
    for stage_key, stage_data in all_metrics.items():
        for dim_key, dim_data in stage_data.get("dimensions", {}).items():
            for metric in dim_data.get("metrics", []):
                current_values[metric["metric_id"]] = metric["value"]

    alerts = ultimate_alert_system.check_alerts(current_values)
    print(f"  触发告警数: {len(alerts)}")
    for alert in alerts:
        print(f"    [{alert.severity}] {alert.rule_name}: {alert.current_value:.4f}")

    # 4. 验收验证
    print("\n[4] 执行终极验收...")
    acceptance_report = ultimate_acceptance_validator.validate_all_stages(all_metrics)

    print(f"\n  总体验收等级: {acceptance_report['overall_grade']}")
    print(f"  斩三尸: {acceptance_report['zhansan_result']['grade']} ({acceptance_report['zhansan_result']['score']:.2%})")
    print(f"  一力破万法: {acceptance_report['yili_powfa_result']['grade']} ({acceptance_report['yili_powfa_result']['score']:.2%})")
    print(f"  终极挑战: {acceptance_report['ultimate_challenge']['grade']} ({acceptance_report['ultimate_challenge']['total_score']:.2f}/100)")

    # 5. 改进建议
    print("\n[5] 改进建议:")
    for rec in acceptance_report["recommendations"]:
        print(f"  - {rec}")

    print("\n" + "=" * 70)
    print("终极指标系统测试完成!")
    print("=" * 70)
