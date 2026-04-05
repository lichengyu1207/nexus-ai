"""
模型验证器
Model Validator

提供模型训练后的验证功能，确保模型质量符合上线标准
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import hashlib

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ValidationResult:
    name: str
    status: ValidationStatus
    score: float = 0.0
    threshold: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    severity: ValidationSeverity = ValidationSeverity.HIGH
    duration: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModelMetrics:
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


class ValidationRule:
    def __init__(
        self,
        name: str,
        validator: Callable,
        threshold: float,
        severity: ValidationSeverity = ValidationSeverity.HIGH,
        description: str = ""
    ):
        self.name = name
        self.validator = validator
        self.threshold = threshold
        self.severity = severity
        self.description = description
    
    def validate(self, metrics: ModelMetrics, **kwargs) -> ValidationResult:
        start_time = time.time()
        try:
            score, message, details = self.validator(metrics, self.threshold, **kwargs)
            status = ValidationStatus.PASSED if score >= self.threshold else ValidationStatus.FAILED
        except Exception as e:
            score = 0.0
            message = f"Validation error: {str(e)}"
            details = {"error": str(e)}
            status = ValidationStatus.FAILED
        
        return ValidationResult(
            name=self.name,
            status=status,
            score=score,
            threshold=self.threshold,
            message=message,
            details=details,
            severity=self.severity,
            duration=time.time() - start_time
        )


class ModelValidator:
    """
    模型验证器
    
    功能：
    1. 准确性验证 - 确保模型准确率达标
    2. 性能验证 - 确保延迟和吞吐量达标
    3. 稳定性验证 - 确保模型输出稳定
    4. 安全性验证 - 确保模型输出安全
    5. 兼容性验证 - 确保与现有系统兼容
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.rules: List[ValidationRule] = []
        self.validation_history: List[Dict] = []
        
        self._setup_default_rules()
        logger.info("ModelValidator initialized")
    
    def _setup_default_rules(self):
        """设置默认验证规则"""
        
        def validate_accuracy(metrics: ModelMetrics, threshold: float) -> Tuple[float, str, Dict]:
            score = metrics.accuracy
            if score >= threshold:
                return score, f"准确率 {score:.2%} 达标", {"accuracy": score}
            return score, f"准确率 {score:.2%} 低于阈值 {threshold:.2%}", {"accuracy": score}
        
        def validate_f1_score(metrics: ModelMetrics, threshold: float) -> Tuple[float, str, Dict]:
            score = metrics.f1_score
            if score >= threshold:
                return score, f"F1分数 {score:.4f} 达标", {"f1_score": score}
            return score, f"F1分数 {score:.4f} 低于阈值 {threshold:.4f}", {"f1_score": score}
        
        def validate_latency_p95(metrics: ModelMetrics, threshold: float) -> Tuple[float, str, Dict]:
            score = 1.0 - (metrics.latency_p95 / threshold) if threshold > 0 else 0.0
            score = max(0.0, min(1.0, score))
            if metrics.latency_p95 <= threshold:
                return score, f"P95延迟 {metrics.latency_p95:.2f}ms 达标", {"latency_p95": metrics.latency_p95}
            return score, f"P95延迟 {metrics.latency_p95:.2f}ms 超过阈值 {threshold:.2f}ms", {"latency_p95": metrics.latency_p95}
        
        def validate_error_rate(metrics: ModelMetrics, threshold: float) -> Tuple[float, str, Dict]:
            score = 1.0 - metrics.error_rate
            if metrics.error_rate <= threshold:
                return score, f"错误率 {metrics.error_rate:.2%} 达标", {"error_rate": metrics.error_rate}
            return score, f"错误率 {metrics.error_rate:.2%} 超过阈值 {threshold:.2%}", {"error_rate": metrics.error_rate}
        
        def validate_throughput(metrics: ModelMetrics, threshold: float) -> Tuple[float, str, Dict]:
            score = metrics.throughput / threshold if threshold > 0 else 0.0
            score = min(1.0, score)
            if metrics.throughput >= threshold:
                return score, f"吞吐量 {metrics.throughput:.0f} QPS 达标", {"throughput": metrics.throughput}
            return score, f"吞吐量 {metrics.throughput:.0f} QPS 低于阈值 {threshold:.0f} QPS", {"throughput": metrics.throughput}
        
        def validate_memory_usage(metrics: ModelMetrics, threshold: float) -> Tuple[float, str, Dict]:
            score = 1.0 - metrics.memory_usage
            if metrics.memory_usage <= threshold:
                return score, f"内存使用 {metrics.memory_usage:.2%} 达标", {"memory_usage": metrics.memory_usage}
            return score, f"内存使用 {metrics.memory_usage:.2%} 超过阈值 {threshold:.2%}", {"memory_usage": metrics.memory_usage}
        
        self.add_rule(ValidationRule(
            "accuracy_check",
            validate_accuracy,
            self.config.get("accuracy_threshold", 0.90),
            ValidationSeverity.CRITICAL,
            "验证模型准确率是否达标"
        ))
        
        self.add_rule(ValidationRule(
            "f1_score_check",
            validate_f1_score,
            self.config.get("f1_threshold", 0.85),
            ValidationSeverity.HIGH,
            "验证F1分数是否达标"
        ))
        
        self.add_rule(ValidationRule(
            "latency_p95_check",
            validate_latency_p95,
            self.config.get("latency_p95_threshold", 100.0),
            ValidationSeverity.HIGH,
            "验证P95延迟是否达标"
        ))
        
        self.add_rule(ValidationRule(
            "error_rate_check",
            validate_error_rate,
            self.config.get("error_rate_threshold", 0.01),
            ValidationSeverity.CRITICAL,
            "验证错误率是否达标"
        ))
        
        self.add_rule(ValidationRule(
            "throughput_check",
            validate_throughput,
            self.config.get("throughput_threshold", 100.0),
            ValidationSeverity.MEDIUM,
            "验证吞吐量是否达标"
        ))
        
        self.add_rule(ValidationRule(
            "memory_usage_check",
            validate_memory_usage,
            self.config.get("memory_threshold", 0.80),
            ValidationSeverity.MEDIUM,
            "验证内存使用是否达标"
        ))
    
    def add_rule(self, rule: ValidationRule):
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def validate(
        self,
        metrics: ModelMetrics,
        rules: Optional[List[str]] = None,
        stop_on_failure: bool = False
    ) -> Dict[str, Any]:
        """
        执行验证
        
        Args:
            metrics: 模型指标
            rules: 指定要执行的规则名称列表，None表示执行所有规则
            stop_on_failure: 是否在第一个失败时停止
        
        Returns:
            验证结果字典
        """
        start_time = time.time()
        results: List[ValidationResult] = []
        
        rules_to_run = self.rules
        if rules:
            rules_to_run = [r for r in self.rules if r.name in rules]
        
        critical_failures = 0
        high_failures = 0
        
        for rule in rules_to_run:
            result = rule.validate(metrics)
            results.append(result)
            
            if result.status == ValidationStatus.FAILED:
                if rule.severity == ValidationSeverity.CRITICAL:
                    critical_failures += 1
                elif rule.severity == ValidationSeverity.HIGH:
                    high_failures += 1
                
                if stop_on_failure and rule.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                    break
        
        passed = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        
        overall_status = ValidationStatus.PASSED
        if critical_failures > 0:
            overall_status = ValidationStatus.FAILED
        elif high_failures > 0:
            overall_status = ValidationStatus.FAILED
        elif failed > 0:
            overall_status = ValidationStatus.FAILED
        
        validation_result = {
            "overall_status": overall_status.value,
            "passed_count": passed,
            "failed_count": failed,
            "total_count": len(results),
            "critical_failures": critical_failures,
            "high_failures": high_failures,
            "duration": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "score": r.score,
                    "threshold": r.threshold,
                    "message": r.message,
                    "severity": r.severity.value,
                    "duration": r.duration,
                }
                for r in results
            ],
            "metrics": {
                "accuracy": metrics.accuracy,
                "f1_score": metrics.f1_score,
                "latency_p95": metrics.latency_p95,
                "error_rate": metrics.error_rate,
                "throughput": metrics.throughput,
                "memory_usage": metrics.memory_usage,
            }
        }
        
        self.validation_history.append(validation_result)
        
        logger.info(f"Validation completed: {overall_status.value}, passed={passed}, failed={failed}")
        return validation_result
    
    def validate_with_baseline(
        self,
        metrics: ModelMetrics,
        baseline_metrics: ModelMetrics,
        min_improvement: float = 0.0
    ) -> Dict[str, Any]:
        """
        与基线对比验证
        
        Args:
            metrics: 当前模型指标
            baseline_metrics: 基线模型指标
            min_improvement: 最小改进要求
        """
        base_result = self.validate(metrics)
        
        improvements = {
            "accuracy": metrics.accuracy - baseline_metrics.accuracy,
            "f1_score": metrics.f1_score - baseline_metrics.f1_score,
            "latency_p95": baseline_metrics.latency_p95 - metrics.latency_p95,
            "error_rate": baseline_metrics.error_rate - metrics.error_rate,
            "throughput": metrics.throughput - baseline_metrics.throughput,
        }
        
        improvement_score = (
            improvements["accuracy"] * 0.3 +
            improvements["f1_score"] * 0.2 +
            (improvements["latency_p95"] / 100) * 0.2 +
            (improvements["error_rate"]) * 0.2 +
            (improvements["throughput"] / 100) * 0.1
        )
        
        regression_detected = any(
            v < -0.05 for k, v in improvements.items()
            if k not in ["latency_p95", "error_rate"]
        ) or improvements["latency_p95"] < -50 or improvements["error_rate"] < -0.01
        
        base_result["baseline_comparison"] = {
            "improvements": improvements,
            "improvement_score": improvement_score,
            "regression_detected": regression_detected,
            "meets_min_improvement": improvement_score >= min_improvement,
        }
        
        if regression_detected:
            base_result["overall_status"] = ValidationStatus.FAILED.value
            base_result["regression_detected"] = True
        
        return base_result
    
    def get_validation_summary(self) -> Dict:
        """获取验证历史摘要"""
        if not self.validation_history:
            return {"message": "No validation history"}
        
        total = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v["overall_status"] == "passed")
        
        return {
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "last_validation": self.validation_history[-1] if self.validation_history else None,
        }
    
    def export_results(self, filepath: str):
        """导出验证结果"""
        data = {
            "validation_history": self.validation_history,
            "rules": [
                {
                    "name": r.name,
                    "threshold": r.threshold,
                    "severity": r.severity.value,
                    "description": r.description,
                }
                for r in self.rules
            ],
            "summary": self.get_validation_summary(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Exported validation results to {filepath}")


class ModelVersion:
    """模型版本"""
    
    def __init__(
        self,
        version_id: str,
        model_path: str,
        metrics: ModelMetrics,
        metadata: Optional[Dict] = None
    ):
        self.version_id = version_id
        self.model_path = model_path
        self.metrics = metrics
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.validation_result: Optional[Dict] = None
        self.checksum: Optional[str] = None
        
        if os.path.exists(model_path):
            self.checksum = self._calculate_checksum(model_path)
    
    def _calculate_checksum(self, filepath: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "model_path": self.model_path,
            "metrics": {
                "accuracy": self.metrics.accuracy,
                "f1_score": self.metrics.f1_score,
                "latency_p95": self.metrics.latency_p95,
                "error_rate": self.metrics.error_rate,
                "throughput": self.metrics.throughput,
            },
            "metadata": self.metadata,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "checksum": self.checksum,
            "validation_result": self.validation_result,
        }


_global_validator: Optional[ModelValidator] = None


def get_validator() -> ModelValidator:
    """获取全局验证器实例"""
    global _global_validator
    if _global_validator is None:
        _global_validator = ModelValidator()
    return _global_validator
