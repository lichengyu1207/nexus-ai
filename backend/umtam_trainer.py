"""
UMTAM动量感知训练与模型合并模块（Unified Momentum-Aware Training & Merging）
基于论文核心思想：保留曲率信息用于更优的训练动态和模型合并

核心能力：
1. 动量感知优化器：在训练中保留曲率信息，30%内存开销 vs AdamW
2. 自适应学习率调整：基于动量和曲率的联合信号
3. 模型合并策略：利用动量历史指导模型融合权重分配
4. 训练收敛监控：多维度收敛检测与早停机制
"""
import json
import logging
import time
import math
import copy
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class ConvergenceStatus(str, Enum):
    """收敛状态"""
    CONVERGED = "converged"
    CONVERGING = "converging"
    STAGNANT = "stagnant"
    DIVERGING = "diverging"
    EARLY_STOPPED = "early_stopped"


@dataclass
class MomentumState:
    """UMTAM动量状态"""
    param_name: str
    first_moment: float = 0.0
    second_moment: float = 0.0
    curvature_estimate: float = 0.0
    momentum_history: deque = field(default_factory=lambda: deque(maxlen=50))
    gradient_history: deque = field(default_factory=lambda: deque(maxlen=20))
    update_count: int = 0
    effective_lr: float = 0.001
    variance_ratio: float = 1.0


@dataclass
class TrainingCheckpoint:
    """训练检查点"""
    checkpoint_id: str
    epoch: int
    global_step: int
    loss: float
    metrics: Dict[str, float]
    momentum_snapshots: Dict[str, Dict[str, float]]
    timestamp: float = field(default_factory=time.time)
    model_hash: str = ""


@dataclass
class MergeCandidate:
    """模型合并候选"""
    model_id: str
    checkpoint: TrainingCheckpoint
    merge_weight: float = 0.0
    momentum_similarity: float = 0.0
    performance_score: float = 0.0
    specialization_score: Dict[str, float] = field(default_factory=dict)


class UMTAMOptimizer:
    """
    UMTAM动量感知优化器
    核心创新：在AdamW基础上增加曲率感知能力，内存开销仅比标准优化器高30%

    相比AdamW的改进：
    - 保留梯度曲率信息（对角Hessian近似）
    - 基于曲率的自适应学习率缩放
    - 动量-曲率联合信号检测收敛/发散
    - 支持周期性动量重置避免局部最优
    """

    def __init__(
        self,
        lr: float = 0.001,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
        weight_decay: float = 0.01,
        curvature_beta: float = 0.99,
        max_grad_norm: float = 10.0,
    ):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        self.curvature_beta = curvature_beta
        self.max_grad_norm = max_grad_norm

        self.momentum_states: Dict[str, MomentumState] = {}
        self.global_step = 0
        self.training_stats = {
            "total_updates": 0,
            "total_gradients_clipped": 0,
            "avg_gradient_norm": 0.0,
            "avg_effective_lr": 0.0,
            "curvature_adjustments": 0,
            "momentum_resets": 0,
        }

    def register_parameters(self, param_names: List[str]):
        """注册参数名（模拟PyTorch参数）"""
        for name in param_names:
            if name not in self.momentum_states:
                self.momentum_states[name] = MomentumState(param_name=name)

    def step(self, gradients: Dict[str, float], current_values: Dict[str, float]) -> Dict[str, float]:
        """
        执行一步UMTAM更新

        Args:
            gradients: 参数名 -> 梯度值
            current_values: 参数名 -> 当前参数值

        Returns:
            更新后的参数值
        """
        self.global_step += 1
        updated_params = {}

        grad_norm_sq = sum(g**2 for g in gradients.values())
        grad_norm = math.sqrt(grad_norm_sq) if grad_norm_sq > 0 else 0.0

        if grad_norm > self.max_grad_norm:
            scale = self.max_grad_norm / max(grad_norm, 1e-6)
            gradients = {k: v * scale for k, v in gradients.items()}
            self.training_stats["total_gradients_clipped"] += 1

        n = len(gradients)
        self.training_stats["avg_gradient_norm"] = (
            (self.training_stats["avg_gradient_norm"] * (n - 1) + grad_norm) / n
        )

        for param_name, grad in gradients.items():
            if param_name not in self.momentum_states:
                self.momentum_states[param_name] = MomentumState(param_name=param_name)

            state = self.momentum_states[param_name]

            state.first_moment = self.beta1 * state.first_moment + (1 - self.beta1) * grad
            state.second_moment = self.beta2 * state.second_moment + (1 - self.beta2) * (grad ** 2)

            grad_change = abs(grad - (state.gradient_history[-1] if state.gradient_history else 0))
            state.curvature_estimate = (
                self.curvature_beta * state.curvature_estimate +
                (1 - self.curvature_beta) * grad_change
            )
            state.gradient_history.append(grad)

            bias_correction1 = 1 - self.beta1 ** self.global_step
            bias_correction2 = 1 - self.beta2 ** self.global_step

            m_hat = state.first_moment / max(bias_correction1, self.eps)
            v_hat = state.second_moment / max(bias_correction2, self.eps)

            curvature_factor = 1.0 / (1.0 + state.curvature_estimate * 10)
            adaptive_lr = self.lr * curvature_factor

            if state.curvature_estimate > 2.0 and state.update_count > 100:
                adaptive_lr *= 0.5
                self.training_stats["curvature_adjustments"] += 1

            update = adaptive_lr * m_hat / (math.sqrt(v_hat) + self.eps)
            update -= self.weight_decay * self.lr * current_values.get(param_name, 0.0)

            new_value = current_values.get(param_name, 0.0) - update
            updated_params[param_name] = new_value

            state.effective_lr = adaptive_lr
            state.momentum_history.append(state.first_moment)
            state.update_count += 1

            variance_ratio = max(v_hat, self.eps) / max(abs(m_hat), self.eps)
            state.variance_ratio = min(10.0, variance_ratio)

        self.training_stats["total_updates"] += 1
        avg_eff = sum(s.effective_lr for s in self.momentum_states.values()) / max(len(self.momentum_states), 1)
        n_updates = self.training_stats["total_updates"]
        self.training_stats["avg_effective_lr"] = (
            (self.training_stats["avg_effective_lr"] * (n_updates - 1) + avg_eff) / n_updates
        )

        return updated_params

    def reset_momentum(self, param_patterns: List[str] = None):
        """
        选择性重置动量（用于跳出局部最优）

        Args:
            param_patterns: 要重置的参数模式列表，None表示全部重置
        """
        count = 0
        targets = param_patterns or list(self.momentum_states.keys())

        for name in targets:
            if name in self.momentum_states:
                state = self.momentum_states[name]
                state.first_moment *= 0.5
                state.second_moment = max(state.second_moment, 0.5)
                state.momentum_history.clear()
                count += 1

        self.training_stats["momentum_resets"] += count
        logger.info(f"UMTAM动量重置: {count}个参数")

    def get_state_summary(self) -> Dict[str, Any]:
        """获取优化器状态摘要"""
        states = list(self.momentum_states.values())
        if not states:
            return {"param_count": 0, **self.training_stats}

        high_curvature = [s.param_name for s in states if s.curvature_estimate > 1.5]
        high_variance = [s.param_name for s in states if s.variance_ratio > 3.0]

        return {
            "param_count": len(states),
            "global_step": self.global_step,
            "high_curvature_params": high_curvature[:10],
            "high_variance_params": high_variance[:10],
            "high_curvature_count": len(high_curvature),
            **self.training_stats,
        }


class ConvergenceMonitor:
    """
    UMTAM收敛监控器
    多维度检测训练收敛状态
    """

    def __init__(self, window_size: int = 20, patience: int = 15, min_delta: float = 1e-6):
        self.window_size = window_size
        self.patience = patience
        self.min_delta = min_delta

        self.loss_history: deque = deque(maxlen=window_size * 3)
        self.metric_history: Dict[str, deque] = {}
        self._no_improve_count = 0
        self._best_loss = float('inf')
        self._status = ConvergenceStatus.CONVERGING
        self._status_history: List[Tuple[float, ConvergenceStatus]] = []

    def record(self, loss: float, metrics: Dict[str, float] = None, step: int = 0):
        """记录一个训练步骤的数据"""
        self.loss_history.append(loss)

        for key, value in (metrics or {}).items():
            if key not in self.metric_history:
                self.metric_history[key] = deque(maxlen=self.window_size * 3)
            self.metric_history[key].append(value)

        if loss < self._best_loss - self.min_delta:
            self._best_loss = loss
            self._no_improve_count = 0
        else:
            self._no_improve_count += 1

        self._status = self._assess_status()

        self._status_history.append((time.time(), self._status))

    def _assess_status(self) -> ConvergenceStatus:
        """评估当前收敛状态"""
        if len(self.loss_history) < 5:
            return ConvergenceStatus.CONVERGING

        recent_losses = list(self.loss_history)[-self.window_size:]
        if len(recent_losses) < self.window_size:
            return ConvergenceStatus.CONVERGING

        loss_std = math.sqrt(sum((l - sum(recent_losses)/len(recent_losses))**2 for l in recent_losses) / len(recent_losses))
        loss_trend = recent_losses[-1] - recent_losses[0] if len(recent_losses) > 1 else 0

        if self._no_improve_count >= self.patience:
            return ConvergenceStatus.EARLY_STOPPED

        if loss_trend > abs(recent_losses[0]) * 0.1 and loss_std > abs(recent_losses[0]) * 0.05:
            return ConvergenceStatus.DIVERGING

        if loss_std < self.min_delta * 10 and abs(loss_trend) < self.min_delta * self.window_size:
            return ConvergenceStatus.CONVERGED

        if self._no_improve_count > self.patience * 0.5:
            return ConvergenceStatus.STAGNANT

        return ConvergenceStatus.CONVERGING

    @property
    def status(self) -> ConvergenceStatus:
        return self._status

    @property
    def should_stop(self) -> bool:
        return self._status in [ConvergenceStatus.CONVERGED, ConvergenceStatus.EARLY_STOPPED, ConvergenceStatus.DIVERGING]

    def get_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        recent = list(self.loss_history)[-self.window_size:] if self.loss_history else []
        return {
            "current_status": self._status.value,
            "should_stop": self.should_stop,
            "current_loss": recent[-1] if recent else None,
            "best_loss": self._best_loss,
            "no_improve_steps": self._no_improve_count,
            "patience_limit": self.patience,
            "loss_window_size": len(recent),
            "avg_recent_loss": sum(recent)/len(recent) if recent else None,
        }


class ModelMerger:
    """
    UMTAM模型合并器
    利用动量历史指导模型融合决策

    核心思想：
    - 动量相似度反映两个模型在优化空间中的接近程度
    - 曲率信息指示各参数的敏感度，影响合并权重
    - 性能指标加权确保合并后模型质量
    """

    def __init__(self):
        self.candidates: List[MergeCandidate] = []
        self.merge_history: List[Dict[str, Any]] = []

    def add_candidate(
        self,
        model_id: str,
        checkpoint: TrainingCheckpoint,
        performance_metrics: Dict[str, float],
        specialization_tags: List[str] = None,
    ):
        """添加模型合并候选"""
        candidate = MergeCandidate(
            model_id=model_id,
            checkpoint=checkpoint,
            performance_score=self._compute_performance_score(performance_metrics),
            specialization_score={tag: 1.0 for tag in (specialization_tags or [])},
        )
        self.candidates.append(candidate)
        logger.info(f"UMTAM添加合并候选: {model_id}, 性能分={candidate.performance_score:.3f}")

    def _compute_performance_score(self, metrics: Dict[str, float]) -> float:
        """计算综合性能分数"""
        if not metrics:
            return 0.5

        weights = {
            "accuracy": 0.3,
            "loss": -0.25,
            "f1": 0.2,
            "precision": 0.1,
            "recall": 0.1,
            "speed": 0.05,
        }

        score = 0.0
        total_weight = 0.0
        for metric, value in metrics.items():
            w = weights.get(metric, 0.05)
            normalized = max(0.0, min(1.0, value)) if metric != "loss" else max(0.0, min(1.0, 1.0 / (1.0 + value)))
            score += w * normalized
            total_weight += abs(w)

        return score / max(total_weight, 0.01)

    def compute_merge_weights(self, target_task: str = "general") -> Dict[str, float]:
        """
        计算模型合并权重

        Args:
            target_task: 目标任务类型

        Returns:
            模型ID -> 合并权重的字典
        """
        if len(self.candidates) < 2:
            return {c.model_id: 1.0 for c in self.candidates}

        n = len(self.candidates)
        raw_weights = {}

        for i, candidate in enumerate(self.candidates):
            base_weight = candidate.performance_score

            momentum_sim_sum = 0.0
            for j, other in enumerate(self.candidates):
                if i != j:
                    sim = self._compute_momentum_similarity(candidate, other)
                    momentum_sim_sum += sim

            avg_momentum_sim = momentum_sim_sum / max(n - 1, 1)
            diversity_bonus = 1.0 - avg_momentum_sim

            final_weight = base_weight * 0.6 + diversity_bonus * 0.4
            raw_weights[candidate.model_id] = max(0.05, final_weight)

        total = sum(raw_weights.values())
        normalized = {k: v / total for k, v in raw_weights.items()}

        self.merge_history.append({
            "timestamp": time.time(),
            "target_task": target_task,
            "candidate_count": n,
            "weights": {k: round(v, 4) for k, v in sorted(normalized.items(), key=lambda x: x[1], reverse=True)},
        })

        logger.info(f"UMTAM合并权重计算完成: {dict(list(normalized.items())[:3])}")
        return normalized

    def _compute_momentum_similarity(self, c1: MergeCandidate, c2: MergeCandidate) -> float:
        """计算两个候选模型的动量相似度"""
        snap1 = c1.checkpoint.momentum_snapshots
        snap2 = c2.checkpoint.momentum_snapshots

        common_keys = set(snap1.keys()) & set(snap2.keys())
        if not common_keys:
            return 0.5

        similarities = []
        for key in common_keys:
            v1 = snap1[key].get("first_moment", 0)
            v2 = snap2[key].get("first_moment", 0)
            norm = math.sqrt(v1**2 + v2**2)
            if norm > 1e-8:
                cos_sim = (v1 * v2) / norm
                similarities.append((cos_sim + 1) / 2)
            else:
                similarities.append(1.0)

        return sum(similarities) / max(len(similarities), 1)


class UMTAMTrainingManager:
    """
    UMTAM训练管理器
    统一管理优化器、收敛监控和模型合并
    """

    def __init__(self, lr: float = 0.001):
        self.optimizer = UMTAMOptimizer(lr=lr)
        self.convergence_monitor = ConvergenceMonitor()
        self.model_merger = ModelMerger()
        self.checkpoints: List[TrainingCheckpoint] = []

    def training_step(
        self,
        gradients: Dict[str, float],
        params: Dict[str, float],
        loss: float,
        metrics: Dict[str, float] = None,
        step: int = 0,
    ) -> Dict[str, Any]:
        """
        执行完整的训练步骤

        Returns:
            包含新参数、状态等信息的字典
        """
        new_params = self.optimizer.step(gradients, params)
        self.convergence_monitor.record(loss, metrics, step)

        should_checkpoint = (step > 0 and step % 100 == 0) or self.convergence_monitor.should_stop

        result = {
            "new_params": new_params,
            "step": step,
            "loss": loss,
            "convergence_status": self.convergence_monitor.status.value,
            "should_stop": self.convergence_monitor.should_stop,
            "optimizer_state": self.optimizer.get_state_summary(),
        }

        if should_checkpoint:
            checkpoint = self._create_checkpoint(step, loss, metrics or {})
            self.checkpoints.append(checkpoint)
            self.model_merger.add_candidate(f"model_step_{step}", checkpoint, metrics or {})
            result["checkpoint_created"] = True
            result["checkpoint_id"] = checkpoint.checkpoint_id

        return result

    def _create_checkpoint(self, step: int, loss: float, metrics: Dict[str, float]) -> TrainingCheckpoint:
        """创建训练检查点"""
        snapshots = {}
        for name, state in self.optimizer.momentum_states.items():
            snapshots[name] = {
                "first_moment": round(state.first_moment, 6),
                "second_moment": round(state.second_moment, 6),
                "curvature": round(state.curvature_estimate, 6),
                "variance_ratio": round(state.variance_ratio, 4),
            }
        return TrainingCheckpoint(
            checkpoint_id=f"ckpt_{int(time.time()*1000)}",
            epoch=step // 100,
            global_step=step,
            loss=loss,
            metrics={k: round(v, 6) for k, v in metrics.items()},
            momentum_snapshots=snapshots,
        )

    def get_training_report(self) -> Dict[str, Any]:
        """获取完整训练报告"""
        convergence_report = self.convergence_monitor.get_report()

        best_ckpt = min(self.checkpoints, key=lambda c: c.loss, default=None)

        return {
            "optimizer": self.optimizer.get_state_summary(),
            "convergence": convergence_report,
            "checkpoints_count": len(self.checkpoints),
            "best_checkpoint": {
                "id": best_ckpt.checkpoint_id,
                "epoch": best_ckpt.epoch,
                "loss": best_ckpt.loss,
            } if best_ckpt else None,
            "merge_candidates": len(self.model_merger.candidates),
            "latest_merge_weights": (
                self.model_merger.compute_merge_weights() if self.model_merger.candidates else {}
            ),
        }


umtam_manager = UMTAMTrainingManager()
