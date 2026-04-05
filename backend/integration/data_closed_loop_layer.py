# -*- coding: utf-8 -*-
"""
智能体修炼体系 - 数据闭环层（第9层：Data Closed-Loop Layer）
==========================================================================
对应设计文档「一分二模块开发提示词」完整落地。
将智能咨询的输出同时用于用户实时回复和后续模型训练，构建
"生产数据→训练数据"完整闭环，通过异步收集用户反馈和对话记录，
离线训练裁判模型与强化学习策略，持续优化智能体能力。

十大模块：
  数据模型篇 — 对话记录+反馈表+脱敏函数
    chat_records表(trace_id/session_id/user_id加密/user_input/agent_output/
    agent_type/context JSONB/metadata JSONB/feedback JSONB/按月分区)
    user_feedback表(like/dislike/rating 1-5/comment/关联trace_id)
    desensitize()脱敏函数(手机号/身份证/邮箱/IP→[PII]正则可扩展)

  API增强篇 — trace_id全链路追踪+异步写入
    /api/chat增强: 回复返回同时异步写入消息队列(RabbitMQ/Kafka)不阻塞响应
    响应体增加trace_id+record_id字段供前端反馈上报使用
    Celery任务async_save_chat_record: 脱敏后插入chat_records, 重试3次指数退避
    数据库连接池复用防泄漏, 失败日志告警

  反馈收集篇 — /api/feedback + 前端组件
    POST /api/feedback接收前端点赞👍点踩👎星级评分(1-5⭐)
    校验trace_id存在性404, 异步写入user_feedback+更新chat_records.feedback
    点踩弹出原因选择(答非所问/内容错误/速度慢/格式差), 防重复提交

  数据存储篇 — 数据湖归档+训练数据查询API
    超过3个月记录定时导出Parquet上传OSS(year/month/chat_YYYYMM.parquet)
    GET /api/internal/training-data内部API供训练脚本拉取
    参数: start_time/end_time/feedback_filter/limit/offset, 需API Key权限验证

  裁判模型篇 — BERT微调二分类好/坏
    build_training_dataset.py: 抽取3个月有反馈数据, 点赞≥4为正样本, 点踩≤2为负样本
    train_judge_model.py: BERT-base-chinese微调 [CLS]问题[SEP]回复[SEP]→二分类
    早停法保F1最高模型 → models/judge_model/
    evaluate_judge_model.py: 准确率/精确率/召回率/F1/混淆矩阵+人工抽样校验

  强化学习篇 — PPO策略网络离线训练
    build_rl_data.py: 状态(输入+历史摘要+画像)→动作(回复)→奖励(点赞+1/点踩-1/评分归一化[-1,1])
    train_rl.py: PPO算法微调Qwen-1.8B策略网络+价值头, 多轮训练奖励曲线
    定期评估检查点保存

  模型版本管理篇 — 注册/切换/灰度/A/B测试
    model_versions表(id/name/version/path/metrics/is_current)
    POST /api/models/register注册新模型, PUT /api/models/current切换当前模型
    灰度发布中间件: 用户ID哈希/比例分流部分流量到新模型
    ab_test_report.py: 新旧模型对比(点赞率/平均评分/响应时间) p<0.05自动全量推广

  模块集成篇 — 海马体记忆/自博弈训练/刑部审计
    对话自动存入海马体记忆(chat_history类型, 重要度按反馈动态调整)
    点踩对话作为红队攻击样本加入自博弈训练池, 每周抽取推送红队队列
    全部对话关联trace_id纳入刑部审计日志, 管理员按trace_id检索排查

  测试验收篇 — 单元/集成/性能三重保障
    pytest覆盖: 脱敏函数/异步任务重试/反馈幂等性/版本切换原子性
    端到端E2E: 咨询→回复→反馈→离线训练→模型更新→灰度发布全流程
    Locust性能测试: 异步写入下P99延迟增量<10ms, 吞吐量不降

  运维监控篇 — Grafana看板+告警规则
    每日对话数/有反馈比例, 点赞点踩分布/平均评分
    裁判模型质量曲线(实时打分vs用户反馈对比), RL训练奖励曲线
    告警: MQ积压>1000条/裁判准确率连续两周下降/反馈率<5%

通关标准:
  异步写入不阻塞主流程(P99延迟增量<10ms), 数据脱敏覆盖率100%
  裁判模型F1≥0.85, RL训练后点赞率提升≥5%
  灰度发布零回滚, A/B测试统计显著性p<0.05, 月均模型迭代≥2次
"""
from __future__ import annotations

import json
import math
import random
import statistics
import logging
import time
import copy
import uuid
import os
import re
import hashlib
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from collections import deque, defaultdict, Counter

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================


class FeedbackType(Enum):
    """反馈类型"""
    LIKE = "like"
    DISLIKE = "dislike"
    RATING = "rating"
    COMMENT = "comment"


class FeedbackReason(Enum):
    """点踩原因"""
    IRRELEVANT = "答非所问"
    WRONG_CONTENT = "内容错误"
    TOO_SLOW = "响应太慢"
    BAD_FORMAT = "格式不佳"
    INCOMPLETE = "回答不完整"
    RUDE_TONE = "语气不当"
    OTHER = "其他"


class DataLabel(Enum):
    """数据标签"""
    POSITIVE = 1
    NEGATIVE = 0
    NEUTRAL = -1
    BOUNDARY = -2


class ModelStatus(Enum):
    """模型状态"""
    DRAFT = "草稿"
    TRAINING = "训练中"
    EVALUATING = "评估中"
    READY = "就绪"
    DEPLOYED = "已部署"
    DEPRECATED = "已弃用"
    FAILED = "训练失败"


class CanaryStrategy(Enum):
    """灰度发布策略"""
    USER_HASH = "用户ID哈希"
    PERCENTAGE = "比例分配"
    WHITELIST = "白名单"
    SEGMENT = "分群"


class ArchiveStatus(Enum):
    """归档状态"""
    ACTIVE = "活跃"
    ARCHIVING = "归档中"
    ARCHIVED = "已归档"
    DELETED = "已删除"


# ==================== 数据结构定义 ====================


@dataclass
class ChatRecord:
    """对话记录"""
    record_id: int
    trace_id: str
    session_id: str
    user_id_encrypted: str
    user_input_raw: str
    user_input_desensitized: str
    agent_output_raw: str
    agent_output_desensitized: str
    agent_type: str  # zhouyu/luxun/zhugeliang etc.
    context_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    feedback_data: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    partition_month: str = ""


@dataclass
class UserFeedback:
    """用户反馈"""
    feedback_id: int
    trace_id: str
    user_id_encrypted: str
    feedback_type: FeedbackType
    rating: Optional[int] = None  # 1-5
    reason: Optional[FeedbackReason] = None
    comment: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AsyncWriteTask:
    """异步写入任务"""
    task_id: str
    trace_id: str
    payload: Dict[str, Any]
    status: str = "pending"  # pending/processing/completed/failed/retrying
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0


@dataclass
class TrainingDataSample:
    """训练数据样本"""
    sample_id: str
    input_text: str
    output_text: str
    label: DataLabel
    agent_type: str
    source_trace_id: str
    confidence: float = 1.0
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeModelConfig:
    """裁判模型配置"""
    model_name: str
    version: str
    base_model: str = "bert-base-chinese"
    input_format: str = "[CLS]{input}[SEP]{output}[SEP]"
    output_classes: int = 2
    max_seq_length: int = 512
    learning_rate: float = 2e-5
    batch_size: int = 32
    epochs: int = 10
    early_stopping_patience: int = 3
    metrics: Dict[str, float] = field(default_factory=dict)
    model_path: str = ""
    is_current: bool = False


@dataclass
class RLTrainingConfig:
    """强化学习训练配置"""
    model_name: str
    base_model: str = "Qwen-1.8B"
    algorithm: str = "PPO"
    learning_rate: float = 1e-6
    kl_coef: float = 0.1
    gamma: float = 0.99
    gae_lambda: float = 0.95
    batch_size: int = 64
    ppo_epochs: int = 4
    clip_range: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    total_timesteps: int = 100000
    reward_stats: Dict[str, float] = field(default_factory=dict)
    checkpoint_path: str = ""
    metrics_history: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class ModelVersion:
    """模型版本"""
    version_id: str
    model_name: str
    version_number: str
    model_type: str  # judge/rl/policy
    path: str
    size_mb: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    status: ModelStatus = ModelStatus.DRAFT
    parent_version: Optional[str] = None
    training_config_json: Optional[str] = None
    canary_weight: float = 0.0
    deployed_at: Optional[str] = None
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CanaryRoutingResult:
    """灰度路由结果"""
    request_id: str
    user_id: str
    routed_model_version: str
    routing_strategy: CanaryStrategy
    hit_canary: bool
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_id: str
    control_version: str
    treatment_version: str
    start_date: str
    end_date: Optional[str] = None
    traffic_split: Dict[str, float] = field(default_factory=dict)
    sample_sizes: Dict[str, int] = field(default_factory=dict)
    metrics_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)
    winner: Optional[str] = None
    p_value: Optional[float] = None
    is_significant: bool = False
    recommendation: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DataClosedLoopDashboardData:
    """数据闭环看板数据"""
    dashboard_id: str
    date_range: str
    total_chats: int
    chats_with_feedback: int
    feedback_rate: float
    like_rate: float
    dislike_rate: float
    avg_rating: float
    async_write_success_rate: float
    async_write_avg_latency_ms: float
    queue_backlog: int
    archive_status: Dict[str, Any]
    judge_model_metrics: Optional[Dict[str, Any]] = None
    rl_training_progress: Optional[Dict[str, Any]] = None
    active_model_versions: List[Dict[str, Any]] = field(default_factory=list)
    canary_routing_stats: Dict[str, Any] = field(default_factory=dict)
    ab_test_results: List[ABTestResult] = field(default_factory=list)
    integration_status: Dict[str, bool] = field(default_factory=dict)
    alerts_active: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ==================== Part A: 数据模型篇 — 对话记录+反馈表+脱敏函数 ====================


class DataDesensitizer:
    """数据脱敏器 — PII信息识别与替换"""

    PATTERNS = {
        "phone": (r'1[3-9]\d{9}', '[PHONE]'),
        "id_card": (r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]', '[ID_CARD]'),
        "email": (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
        "ip_address": (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]'),
        "bank_card": (r'\b\d{16,19}\b', '[BANK_CARD]'),
        "name": (r'[\u4e00-\u9fa5]{2,4}(?:先生|女士|小姐|经理|总|董|老师)', '[NAME]'),
        "address": (r'[\u4e00-\u9fa5]*?[省市区县镇村路号栋单元楼室][\u4e00-\u9fa5\d\-\s]+', '[ADDRESS]'),
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._custom_patterns: List[Tuple[re.Pattern, str]] = []
        self._stats = {"total_processed": 0, "items_masked": 0}
        self._enabled = self.config.get("enabled", True)

    def add_custom_pattern(self, pattern_str: str, replacement: str) -> None:
        """添加自定义脱敏规则"""
        try:
            compiled = re.compile(pattern_str)
            self._custom_patterns.append((compiled, replacement))
            logger.debug(f"[脱敏器] 添加自定义规则: {pattern_str} → {replacement}")
        except re.error as e:
            logger.error(f"[脱敏器] 正则表达式错误: {pattern_str} - {e}")

    def desensitize(self, text: str) -> str:
        """对文本进行PII脱敏"""
        if not self._enabled or not text:
            return text
        self._stats["total_processed"] += 1
        result = text
        masked_in_this = 0
        for name, (pattern, replacement) in self.PATTERNS.items():
            matches = re.findall(pattern, result)
            if matches:
                count = len(matches)
                result = re.sub(pattern, replacement, result)
                masked_in_this += count
                logger.debug(f"[脱敏器] {name}: 替换{count}处")
        for custom_pattern, replacement in self._custom_patterns:
            matches = custom_pattern.findall(result)
            if matches:
                result = custom_pattern.sub(replacement, result)
                masked_in_this += len(matches)
        self._stats["items_masked"] += masked_in_this
        return result

    def desensitize_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """对字典中的指定字段批量脱敏"""
        result = dict(data)
        for f in fields:
            if f in result and isinstance(result[f], str):
                result[f] = self.desensitize(result[f])
        return result

    def encrypt_user_id(self, user_id: str, salt: str = "fangdu_secret") -> str:
        """加密用户ID用于存储"""
        raw = f"{user_id}:{salt}"
        hash_bytes = hashlib.sha256(raw.encode()).digest()
        encoded = base64.b64encode(hash_bytes).decode()
        return f"enc_{encoded[:24]}"

    def get_stats(self) -> Dict[str, Any]:
        """获取脱敏统计"""
        return {
            **self._stats,
            "mask_ratio": round(
                self._stats["items_masked"] / max(self._stats["total_processed"], 1), 4),
            "patterns_loaded": len(self.PATTERNS) + len(self._custom_patterns),
        }


class ChatRecordStore:
    """对话记录存储器 — 分区表管理+CRUD"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._records: Dict[int, ChatRecord] = {}
        self._by_trace_id: Dict[str, int] = {}
        self._by_session: Dict[str, List[int]] = defaultdict(list)
        self._next_record_id = 1
        self._desensitizer = DataDesensitizer(config=self.config.get("desensitization", {}))
        self._partition_retention_months = self.config.get("retention_months", 12)

    def store_record(self, trace_id: str, session_id: str, user_id: str,
                     user_input: str, agent_output: str,
                     agent_type: str = "zhouyu",
                     context: Optional[Dict] = None,
                     metadata: Optional[Dict] = None) -> ChatRecord:
        """存储一条对话记录(含脱敏)"""
        rid = self._next_record_id
        self._next_record_id += 1
        now = datetime.now(timezone.utc)
        record = ChatRecord(
            record_id=rid, trace_id=trace_id, session_id=session_id,
            user_id_encrypted=self._desensitizer.encrypt_user_id(user_id),
            user_input_raw=user_input,
            user_input_desensitized=self._desensitizer.desensitize(user_input),
            agent_output_raw=agent_output,
            agent_output_desensitized=self._desensitizer.desensitize(agent_output),
            agent_type=agent_type,
            context_summary=json.dumps(context, ensure_ascii=False) if context else None,
            metadata=metadata or {},
            partition_key=now.strftime("%Y-%m"),
        )
        self._records[rid] = record
        self._by_trace_id[trace_id] = rid
        self._by_session[session_id].append(rid)
        return record

    def get_record_by_trace(self, trace_id: str) -> Optional[ChatRecord]:
        """通过trace_id获取记录"""
        rid = self._by_trace_id.get(trace_id)
        return self._records.get(rid) if rid else None

    def get_session_records(self, session_id: str) -> List[ChatRecord]:
        """获取会话所有记录"""
        rids = self._by_session.get(session_id, [])
        return [self._records[r] for r in rids if r in self._records]

    def update_feedback(self, trace_id: str, feedback_data: Dict[str, Any]) -> bool:
        """更新记录的反馈数据"""
        record = self.get_record_by_trace(trace_id)
        if record:
            record.feedback_data = feedback_data
            return True
        return False

    def query_for_training(self, start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           feedback_only: bool = True,
                           limit: int = 1000,
                           offset: int = 0) -> List[ChatRecord]:
        """查询训练用数据"""
        results = []
        for record in self._records.values():
            if feedback_only and not record.feedback_data:
                continue
            if start_time and record.created_at < start_time:
                continue
            if end_time and record.created_at > end_time:
                continue
            results.append(record)
        results.sort(key=lambda r: r.created_at)
        return results[offset:offset + limit]

    def get_store_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        with_feedback = sum(1 for r in self._records.values() if r.feedback_data)
        by_agent = Counter(r.agent_type for r in self._records.values())
        by_partition = Counter(r.partition_month for r in self._records.values())
        return {
            "total_records": len(self._records),
            "with_feedback": with_feedback,
            "feedback_rate": round(with_feedback / max(len(self._records), 1) * 100, 2),
            "by_agent": dict(by_agent),
            "by_partition": dict(by_partition),
            "desensitizer_stats": self._desensitizer.get_stats(),
        }


# ==================== Part B: API增强篇 — trace_id追踪+异步写入 ====================


class AsyncWriteEngine:
    """异步写入引擎 — Celery风格的任务队列模拟"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._task_queue: deque = deque()
        self._completed_tasks: List[AsyncWriteTask] = []
        self._failed_tasks: List[AsyncWriteTask] = []
        self._store: Optional[ChatRecordStore] = None
        self._max_backlog = self.config.get("max_backlog", 5000)
        self._base_delay_s = self.config.get("base_retry_delay", 1)
        self._worker_running = False
        self._stats = {"total_enqueued": 0, "total_completed": 0, "total_failed": 0,
                       "avg_latency_ms": 0}

    def bind_store(self, store: ChatRecordStore) -> None:
        """绑定存储器"""
        self._store = store

    def enqueue_write(self, trace_id: str, session_id: str, user_id: str,
                      user_input: str, agent_output: str,
                      agent_type: str = "zhouyu",
                      context: Optional[Dict] = None,
                      metadata: Optional[Dict] = None) -> AsyncWriteTask:
        """入队异步写入任务"""
        task = AsyncWriteTask(
            task_id=f"task_{uuid.uuid4().hex[:10]}",
            trace_id=trace_id,
            payload={"session_id": session_id, "user_id": user_id,
                     "user_input": user_input, "agent_output": agent_output,
                     "agent_type": agent_type, "context": context, "metadata": metadata},
        )
        self._task_queue.append(task)
        self._stats["total_enqueued"] += 1
        logger.info(f"[异步写入] 入队: {task.task_id} trace={trace_id}")
        if len(self._task_queue) > self._max_backlog * 0.8:
            logger.warning(f"[异步写入] 队列积压: {len(self._task_queue)}/{self._max_backlog}")
        return task

    def process_queue(self, batch_size: int = 50) -> int:
        """处理队列中的写入任务(模拟Celery worker)"""
        processed = 0
        while self._task_queue and processed < batch_size:
            task = self._task_queue.popleft()
            start = time.time()
            success = self._execute_task(task)
            task.processing_time_ms = (time.time() - start) * 1000
            task.completed_at = datetime.now(timezone.utc).isoformat()

            if success:
                task.status = "completed"
                self._completed_tasks.append(task)
                self._stats["total_completed"] += 1
            else:
                task.status = "failed" if task.retry_count >= task.max_retries else "retrying"
                self._handle_failure(task)
            processed += 1

        if self._completed_tasks:
            latencies = [t.processing_time_ms for t in self._completed_tasks[-100:]]
            self._stats["avg_latency_ms"] = round(statistics.mean(latencies), 2) if latencies else 0
        return processed

    def _execute_task(self, task: AsyncWriteTask) -> bool:
        """执行单个写入任务"""
        if not self._store:
            task.error_message = "未绑定存储器"
            return False
        try:
            p = task.payload
            self._store.store_record(
                trace_id=task.trace_id, session_id=p["session_id"],
                user_id=p["user_id"], user_input=p["user_input"],
                agent_output=p["agent_output"], agent_type=p.get("agent_type", "zhouyu"),
                context=p.get("context"), metadata=p.get("metadata"),
            )
            return True
        except Exception as e:
            task.error_message = str(e)
            logger.error(f"[异步写入] 任务失败: {task.task_id} - {e}")
            return False

    def _handle_failure(self, task: AsyncWriteTask) -> None:
        """处理失败任务(重试或标记最终失败)"""
        if task.retry_count < task.max_retries:
            delay = self._base_delay_s * (2 ** task.retry_count)
            task.retry_count += 1
            task.status = "retrying"
            self._task_queue.appendleft(task)
            logger.warning(f"[异步写入] 重试 {task.retry_count}/{task.max_retries}, "
                           f"延迟{delay}s: {task.task_id}")
            self._stats["total_failed"] += 1
        else:
            self._failed_tasks.append(task)
            logger.error(f"[异步写入] 最终失败: {task.task_id} ({task.max_retries}次重试耗尽)")

    def get_engine_stats(self) -> Dict[str, Any]:
        """获取引擎统计"""
        return {
            **self._stats,
            "queue_backlog": len(self._task_queue),
            "max_backlog": self._max_backlog,
            "backlog_pct": round(len(self._task_queue) / max(self._max_backlog, 1) * 100, 1),
            "success_rate": round(
                self._stats["total_completed"] /
                max(self._stats["total_completed"] + self._stats["total_failed"], 1) * 100, 2),
            "alert_triggered": len(self._task_queue) > self._max_backlog,
        }


class TraceTracker:
    """全链路追踪器 — trace_id生成与管理"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._active_traces: Dict[str, Dict[str, Any]] = {}

    def generate_trace_id(self) -> str:
        """生成全局唯一trace_id"""
        ts = int(time.time() * 1000)
        rand = uuid.uuid4().hex[:8]
        return f"tr_{ts}_{rand}"

    def begin_trace(self, trace_id: str, user_id: str, session_id: str,
                    request_meta: Optional[Dict] = None) -> Dict[str, Any]:
        """开始一条追踪链路"""
        trace_info = {
            "trace_id": trace_id, "user_id": user_id, "session_id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "request_meta": request_meta or {},
            "steps": [],
            "record_id": None,
            "status": "active",
        }
        self._active_traces[trace_id] = trace_info
        return trace_info

    def add_step(self, trace_id: str, step_name: str, duration_ms: float,
                 details: Optional[Dict] = None) -> None:
        """添加追踪步骤"""
        trace = self._active_traces.get(trace_id)
        if trace:
            trace["steps"].append({
                "step": step_name, "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": details or {},
            })

    def complete_trace(self, trace_id: str, record_id: int,
                       response_meta: Optional[Dict] = None) -> Dict[str, Any]:
        """完成追踪链路"""
        trace = self._active_traces.get(trace_id)
        if trace:
            trace["record_id"] = record_id
            trace["status"] = "completed"
            trace["completed_at"] = datetime.now(timezone.utc).isoformat()
            trace["response_meta"] = response_meta or {}
            total_duration = sum(s["duration_ms"] for s in trace["steps"])
            trace["total_duration_ms"] = round(total_duration, 2)
        return trace or {}

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """获取追踪详情"""
        return self._active_traces.get(trace_id)

    def get_active_traces_count(self) -> int:
        """活跃追踪数量"""
        return sum(1 for t in self._active_traces.values() if t["status"] == "active")


# ==================== Part C: 反馈收集篇 — /api/feedback + 前端组件逻辑 ====================


class FeedbackCollector:
    """反馈收集器 — 点赞/点踩/评分/评论"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._feedbacks: Dict[int, UserFeedback] = {}
        self._by_trace: Dict[str, int] = {}
        self._by_user: Dict[str, List[int]] = defaultdict(list)
        self._next_fid = 1
        self._submitted_trace_ids: Set[str] = set()
        self._store: Optional[ChatRecordStore] = None

    def bind_store(self, store: ChatRecordStore) -> None:
        """绑定存储器"""
        self._store = store

    def submit_feedback(self, trace_id: str, user_id: str,
                        feedback_type: FeedbackType,
                        rating: Optional[int] = None,
                        reason: Optional[FeedbackReason] = None,
                        comment: Optional[str] = None) -> Tuple[bool, str, Optional[UserFeedback]]:
        """提交用户反馈"""
        if trace_id in self._submitted_trace_ids:
            return False, "该条目已提交过反馈，请勿重复提交", None
        if self._store and not self._store.get_record_by_trace(trace_id):
            return False, f"trace_id {trace_id} 不存在", None

        fid = self._next_fid
        self._next_fid += 1
        feedback = UserFeedback(
            feedback_id=fid, trace_id=trace_id,
            user_id_encrypted=hashlib.sha256(user_id.encode()).hexdigest()[:16],
            feedback_type=feedback_type, rating=rating,
            reason=reason, comment=comment,
        )
        self._feedbacks[fid] = feedback
        self._by_trace[trace_id] = fid
        encrypted_uid = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        self._by_user[encrypted_uid].append(fid)
        self._submitted_trace_ids.add(trace_id)

        if self._store:
            fb_data = {"type": feedback_type.value, "rating": rating,
                       "reason": reason.value if reason else None,
                       "comment": comment, "submitted_at": feedback.created_at}
            self._store.update_feedback(trace_id, fb_data)

        logger.info(f"[反馈收集] {feedback_type.value} | trace={trace_id} "
                    f"| rating={rating} | reason={reason.value if reason else 'N/A'}")
        return True, "反馈提交成功", feedback

    def get_feedback_by_trace(self, trace_id: str) -> Optional[UserFeedback]:
        """通过trace_id获取反馈"""
        fid = self._by_trace.get(trace_id)
        return self._feedbacks.get(fid) if fid else None

    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取反馈统计"""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        recent = [f for f in self._feedbacks.values() if f.created_at >= cutoff]
        if not recent:
            return {"period_days": days, "total": 0}
        type_counts = Counter(f.feedback_type.value for f in recent)
        ratings = [f.rating for f in recent if f.rating is not None]
        reasons = Counter(f.reason.value for f in recent if f.reason is not None)
        return {
            "period_days": days, "total": len(recent),
            "by_type": dict(type_counts),
            "avg_rating": round(statistics.mean(ratings), 2) if ratings else None,
            "like_rate": round(type_counts.get("like", 0) / max(len(recent), 1) * 100, 2),
            "dislike_rate": round(type_counts.get("dislike", 0) / max(len(recent), 1) * 100, 2),
            "top_dislike_reasons": dict(reasons.most_common(5)),
            "unique_users_gave_feedback": len(set(
                f.user_id_encrypted for f in recent)),
        }

    def get_dislike_reason_options(self) -> List[Dict[str, str]]:
        """获取点踩原因选项列表"""
        return [{"value": r.value, "label": r.name} for r in FeedbackReason]


# ==================== Part D: 数据存储篇 — OSS归档+训练数据API ====================


class DataLakeArchiver:
    """数据湖归档器 — 超期数据导出Parquet上传OSS"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._archive_jobs: List[Dict[str, Any]] = []
        self._archive_manifest: Dict[str, Dict[str, Any]] = {}
        self._retention_months = self.config.get("retention_months", 3)
        self._oss_base_path = self.config.get("oss_base_path", "archived/chats")

    def create_archive_job(self, target_month: str,
                            records: List[ChatRecord]) -> Dict[str, Any]:
        """创建归档任务"""
        job_id = f"archive_{uuid.uuid4().hex[:8]}"
        job = {
            "job_id": job_id, "target_month": target_month,
            "record_count": len(records), "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "output_path": f"{self._oss_base_path}/{target_month.replace('-', '/')}/"
                          f"chat_records_{target_month}.parquet",
            "compressed_size_kb": 0, "original_size_kb": 0,
            "compression_ratio": 0.0,
        }
        self._archive_jobs.append(job)
        logger.info(f"[数据湖] 创建归档任务: {job_id} 目标月份={target_month} 记录数={len(records)}")
        return job

    def simulate_archive(self, job_id: str) -> Dict[str, Any]:
        """模拟执行归档(实际环境调用PyArrow+OSS SDK)"""
        job = next((j for j in self._archive_jobs if j["job_id"] == job_id), None)
        if not job or job["status"] != "pending":
            return {"error": "任务不存在或已完成"}
        job["status"] = "archiving"
        original_kb = job["record_count"] * random.uniform(2, 8)
        compressed_kb = original_kb * random.uniform(0.08, 0.15)
        job["original_size_kb"] = round(original_kb, 1)
        job["compressed_size_kb"] = round(compressed_kb, 1)
        job["compression_ratio"] = round(compressed_kb / max(original_kb, 0.01), 3)
        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._archive_manifest[job["target_month"]] = {
            "job_id": job_id, "path": job["output_path"],
            "record_count": job["record_count"],
            "archived_at": job["completed_at"],
        }
        return job

    def get_archive_status(self) -> Dict[str, Any]:
        """获取归档状态概览"""
        completed = [j for j in self._archive_jobs if j["status"] == "completed"]
        pending = [j for j in self._archive_jobs if j["status"] == "pending"]
        total_saved_kb = sum(j.get("compressed_size_kb", 0) for j in completed)
        return {
            "total_jobs": len(self._archive_jobs),
            "completed": len(completed), "pending": len(pending),
            "total_compressed_kb": round(total_saved_kb, 1),
            "total_compressed_mb": round(total_saved_kb / 1024, 2),
            "avg_compression_ratio": round(
                statistics.mean([j["compression_ratio"] for j in completed]), 3)
            if completed else 0,
            "manifest_entries": len(self._archive_manifest),
        }


class TrainingDataAPI:
    """训练数据查询API — 内部接口供训练脚本拉取"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._store: Optional[ChatRecordStore] = None
        self._api_keys: Set[str] = set(self.config.get("api_keys", ["dev-key-internal"]))
        self._access_log: List[Dict[str, Any]] = []

    def bind_store(self, store: ChatRecordStore) -> None:
        """绑定存储器"""
        self._store = store

    def query_training_data(self, api_key: str, start_time: Optional[str] = None,
                            end_time: Optional[str] = None,
                            feedback_only: bool = True,
                            agent_filter: Optional[str] = None,
                            limit: int = 1000,
                            offset: int = 0) -> Tuple[bool, str, List[Dict]]:
        """查询训练数据(需API Key认证)"""
        if api_key not in self._api_keys:
            self._log_access(api_key, False, "unauthorized")
            return False, "无效API Key", []

        if not self._store:
            return False, "存储器未绑定", []

        records = self._store.query_for_training(start_time, end_time, feedback_only, limit * 2, offset)
        if agent_filter:
            records = [r for r in records if r.agent_type == agent_filter]

        result = []
        for r in records[:limit]:
            result.append({
                "trace_id": r.trace_id, "user_input": r.user_input_desensitized,
                "agent_output": r.agent_output_desensitized,
                "agent_type": r.agent_type,
                "feedback": r.feedback_data,
                "created_at": r.created_at,
            })

        self._log_access(api_key, True, f"returned {len(result)} records")
        return True, f"成功返回{len(result)}条记录", result

    def _log_access(self, api_key: str, success: bool, detail: str) -> None:
        """记录访问日志"""
        self._access_log.append({
            "api_key_hash": hashlib.md5(api_key.encode()).hexdigest()[:12],
            "success": success, "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_api_stats(self) -> Dict[str, Any]:
        """获取API统计"""
        recent = [l for l in self._access_log
                   if l["timestamp"] > (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()]
        return {
            "total_queries": len(self._access_log),
            "queries_24h": len(recent),
            "success_rate_24h": round(
                sum(1 for l in recent if l["success"]) / max(len(recent), 1) * 100, 2),
            "active_keys": len(self._api_keys),
        }


# ==================== Part E: 裁判模型篇 — BERT微调二分类 ====================


class JudgeModelTrainer:
    """裁判模型训练器 — BERT-base-chinese 微调"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._models: Dict[str, JudgeModelConfig] = {}
        self._training_datasets: List[TrainingDataSample] = []
        self._evaluation_results: Dict[str, Dict[str, float]] = {}

    def build_dataset_from_records(self, records: List[ChatRecord],
                                    positive_threshold: int = 4,
                                    negative_threshold: int = 2) -> List[TrainingDataSample]:
        """从对话记录构建训练数据集"""
        dataset = []
        for record in records:
            if not record.feedback_data:
                continue
            fb = record.feedback_data
            fb_type = fb.get("type", "")
            rating = fb.get("rating")

            if fb_type == "like" or (rating and rating >= positive_threshold):
                label = DataLabel.POSITIVE
            elif fb_type == "dislike" or (rating and rating <= negative_threshold):
                label = DataLabel.NEGATIVE
            elif rating == 3:
                label = DataLabel.BOUNDARY
            else:
                continue

            sample = TrainingDataSample(
                sample_id=f"smp_{uuid.uuid4().hex[:10]}",
                input_text=record.user_input_desensitized,
                output_text=record.agent_output_desensitized,
                label=label, agent_type=record.agent_type,
                source_trace_id=record.trace_id,
                confidence=1.0 if rating and abs(rating - 3) >= 1 else 0.7,
                features={
                    "agent_type": record.agent_type,
                    "input_length": len(record.user_input_desensitized),
                    "output_length": len(record.agent_output_desensitized),
                    "has_context": record.context_summary is not None,
                },
            )
            dataset.append(sample)

        self._training_datasets.extend(dataset)
        pos = sum(1 for s in dataset if s.label == DataLabel.POSITIVE)
        neg = sum(1 for s in dataset if s.label == DataLabel.NEGATIVE)
        logger.info(f"[裁判模型] 构建数据集: 总计{len(dataset)}条 (正样本{pos}/负样本{neg})")
        return dataset

    def register_judge_model(self, name: str, version: str,
                              **kwargs) -> JudgeModelConfig:
        """注册裁判模型配置"""
        config = JudgeModelConfig(model_name=name, version=version, **kwargs)
        self._models[f"{name}:{version}"] = config
        logger.info(f"[裁判模型] 注册: {name} v{version} (基础模型={config.base_model})")
        return config

    def simulate_training(self, model_key: str,
                          epochs: int = 10) -> Dict[str, Any]:
        """模拟训练过程(实际环境调HuggingFace Trainer)"""
        config = self._models.get(model_key)
        if not config:
            return {"error": f"模型 {model_key} 未注册"}

        pos_samples = [s for s in self._training_datasets if s.label == DataLabel.POSITIVE]
        neg_samples = [s for s in self._training_datasets if s.label == DataLabel.NEGATIVE]

        history = []
        best_f1 = 0
        best_epoch = 0
        for epoch in range(1, epochs + 1):
            train_loss = max(0.9 - epoch * 0.07 + random.uniform(-0.03, 0.03), 0.05)
            val_loss = train_loss * random.uniform(1.05, 1.2)
            acc = min(0.55 + epoch * 0.04 + random.uniform(-0.02, 0.02), 0.98)
            prec = acc + random.uniform(-0.03, 0.03)
            rec = acc + random.uniform(-0.04, 0.04)
            f1 = 2 * prec * rec / max(prec + rec, 0.001)
            f1 = min(max(f1, 0.5), 0.96)

            epoch_metrics = {
                "epoch": epoch, "train_loss": round(train_loss, 4),
                "val_loss": round(val_loss, 4),
                "accuracy": round(acc, 4), "precision": round(prec, 4),
                "recall": round(rec, 4), "f1": round(f1, 4),
            }
            history.append(epoch_metrics)

            if f1 > best_f1:
                best_f1 = f1
                best_epoch = epoch

            if epoch - best_epoch >= config.early_stopping_patience:
                logger.info(f"[裁判模型] 早停于第{epoch}轮 (最佳F1={best_f1:.4f}@第{best_epoch}轮)")
                break

        final_metrics = history[-1] if history else {}
        final_metrics["best_f1"] = round(best_f1, 4)
        final_metrics["best_epoch"] = best_epoch
        final_metrics["total_epochs"] = len(history)
        config.metrics = final_metrics
        config.model_path = f"models/judge_{model_key.replace(':', '_')}_v{config.version}"
        config.is_current = True
        self._evaluation_results[model_key] = final_metrics

        return {
            "model": model_key, "status": "completed",
            "final_metrics": final_metrics,
            "training_history": history,
            "model_path": config.model_path,
        }

    def evaluate_model(self, model_key: str, test_samples: Optional[List] = None) -> Dict[str, Any]:
        """评估裁判模型"""
        config = self._models.get(model_key)
        if not config or not config.metrics:
            return {"error": "模型尚未训练"}
        metrics = config.metrics
        cm = {"TP": int(metrics.get("precision", 0) * 200),
              "FP": int((1 - metrics.get("precision", 0)) * 50),
              "FN": int((1 - metrics.get("recall", 0)) * 50),
              "TN": int(metrics.get("accuracy", 0) * 800)}
        return {
            "model": model_key,
            "accuracy": metrics.get("accuracy", 0),
            "precision": metrics.get("precision", 0),
            "recall": metrics.get("recall", 0),
            "f1": metrics.get("f1", 0),
            "confusion_matrix": cm,
            "recommendation": "✅ 可上线" if metrics.get("f1", 0) >= 0.85 else "⚠️ 需继续优化",
        }


# ==================== Part F: 强化学习篇 — PPO策略网络训练 ====================


class RLTrainingEngine:
    """强化学习训练引擎 — PPO算法离线训练"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._rl_configs: Dict[str, RLTrainingConfig] = {}
        self._rl_sequences: List[Dict[str, Any]] = []
        self._training_histories: Dict[str, List[Dict]] = defaultdict(list)

    def build_rl_dataset(self, records: List[ChatRecord]) -> List[Dict[str, Any]]:
        """构建强化学习训练数据(状态-动作-奖励序列)"""
        sequences = []
        for record in records:
            if not record.feedback_data:
                continue
            fb = record.feedback_data
            reward = 0.0
            if fb.get("type") == "like":
                reward = 1.0
            elif fb.get("type") == "dislike":
                reward = -1.0
            elif fb.get("rating"):
                reward = (fb["rating"] - 3) / 2.0

            seq = {
                "state": {
                    "user_input": record.user_input_desensitized,
                    "history_summary": record.context_summary or "",
                    "agent_type": record.agent_type,
                },
                "action": record.agent_output_desensitized,
                "reward": round(reward, 3),
                "trace_id": record.trace_id,
                "timestamp": record.created_at,
            }
            sequences.append(seq)
        self._rl_sequences.extend(sequences)
        logger.info(f"[RL引擎] 构建RL数据: {len(sequences)}条序列 "
                    f"(平均奖励={statistics.mean([s['reward'] for s in sequences]):.3f})")
        return sequences

    def register_rl_config(self, name: str, **kwargs) -> RLTrainingConfig:
        """注册RL训练配置"""
        config = RLTrainingConfig(model_name=name, **kwargs)
        self._rl_configs[name] = config
        return config

    def simulate_ppo_training(self, config_name: str,
                                total_steps: int = 50000) -> Dict[str, Any]:
        """模拟PPO训练过程"""
        config = self._rl_configs.get(config_name)
        if not config:
            return {"error": f"RL配置 {config_name} 未注册"}

        history = []
        mean_reward = 0.0
        best_mean_reward = -999
        for step in range(0, total_steps + 1, max(1, total_steps // 50)):
            episode_reward = random.gauss(mean_reward + step * 0.00005, 0.8)
            episode_reward = max(min(episode_reward, 1.5), -1.5)
            policy_loss = max(0.8 - step / total_steps * 0.5 + random.uniform(-0.1, 0.1), 0.1)
            value_loss = max(0.5 - step / total_steps * 0.3 + random.uniform(-0.05, 0.05), 0.05)
            entropy = max(0.8 - step / total_steps * 0.4, 0.1) + random.uniform(-0.05, 0.05)
            kl_divergence = min(step / total_steps * 0.15 + random.uniform(0, 0.02), 0.2)

            mean_reward = mean_reward * 0.95 + episode_reward * 0.05

            entry = {
                "step": step, "mean_reward": round(mean_reward, 4),
                "policy_loss": round(policy_loss, 4),
                "value_loss": round(value_loss, 4),
                "entropy": round(entropy, 4),
                "kl_divergence": round(kl_divergence, 4),
            }
            history.append(entry)

            if mean_reward > best_mean_reward:
                best_mean_reward = mean_reward

        final_entry = history[-1] if history else {}
        config.reward_stats = {
            "final_mean_reward": round(mean_reward, 4),
            "best_mean_reward": round(best_mean_reward, 4),
            "improvement": round(best_mean_reward - (-0.5), 4),
            "total_steps": total_steps,
        }
        config.metrics_history = history[-20:]
        config.checkpoint_path = f"models/ppo_{config_name}_{uuid.uuid4().hex[:6]}"

        return {
            "model": config_name, "algorithm": config.algorithm,
            "base_model": config.base_model,
            "final_stats": config.reward_stats,
            "training_curve": history[-10:] if len(history) > 10 else history,
            "checkpoint": config.checkpoint_path,
        }


# ==================== Part G: 模型版本管理篇 — 注册/切换/灰度/A/B ====================


class ModelVersionManager:
    """模型版本管理器 — 注册/切换/灰度发布/A/B测试"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._versions: Dict[str, ModelVersion] = {}
        self._current_models: Dict[str, str] = {}  # model_type -> version_id
        self._canary_rules: List[Dict[str, Any]] = []
        self._routing_log: List[CanaryRoutingResult] = []
        self._ab_tests: Dict[str, ABTestResult] = {}

    def register_model(self, name: str, version: str, model_type: str,
                       path: str, metrics: Optional[Dict] = None,
                       **kwargs) -> ModelVersion:
        """注册新模型版本"""
        vid = f"ver_{uuid.uuid4().hex[:10]}"
        version = ModelVersion(
            version_id=vid, model_name=name, version_number=version,
            model_type=model_type, path=path,
            metrics=metrics or {}, **kwargs,
        )
        self._versions[vid] = version
        logger.info(f"[模型版本] 注册: {name} v{version} [{model_type}] id={vid}")
        return version

    def set_current_model(self, model_type: str, version_id: str) -> bool:
        """切换当前模型(原子操作)"""
        version = self._versions.get(version_id)
        if not version:
            return False
        old_id = self._current_models.get(model_type)
        self._current_models[model_type] = version_id
        version.status = ModelStatus.DEPLOYED
        version.deployed_at = datetime.now(timezone.utc).isoformat()
        if old_id and old_id != version_id:
            old_ver = self._versions.get(old_id)
            if old_ver:
                old_ver.status = ModelStatus.DEPRECATED
        logger.info(f"[模型版本] 切换: {model_type} → {version.model_name} v{version.version_number} "
                    f"(替换={old_id})")
        return True

    def configure_canary(self, model_type: str, new_version_id: str,
                           strategy: CanaryStrategy,
                           weight: float = 0.1,
                           whitelist_users: Optional[List[str]] = None) -> Dict[str, Any]:
        """配置灰度发布规则"""
        rule = {
            "rule_id": f"canary_{uuid.uuid4().hex[:8]}",
            "model_type": model_type, "new_version_id": new_version_id,
            "old_version_id": self._current_models.get(model_type, ""),
            "strategy": strategy.value, "weight": weight,
            "whitelist": whitelist_users or [],
            "enabled": True, "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._canary_rules.append(rule)
        logger.info(f"[灰度发布] 配置: {model_type} 新版流量{weight*100:.0f}% "
                    f"(策略={strategy.value})")
        return rule

    def route_request(self, user_id: str, model_type: str) -> CanaryRoutingResult:
        """路由请求到对应模型版本"""
        req_id = f"route_{uuid.uuid4().hex[:8]}"
        current_vid = self._current_models.get(model_type, "")
        rule = next((r for r in self._canary_rules
                     if r["model_type"] == model_type and r["enabled"]), None)
        routed_vid = current_vid
        hit_canary = False

        if rule:
            if rule["strategy"] == CanaryStrategy.USER_HASH.value:
                hash_val = int(hashlib.md5(f"{user_id}:{model_type}".encode()).hexdigest(), 16)
                hit = (hash_val % 100) < (rule["weight"] * 100)
                if hit:
                    routed_vid = rule["new_version_id"]
                    hit_canary = True
            elif rule["strategy"] == CanaryStrategy.PERCENTAGE.value:
                if random.random() < rule["weight"]:
                    routed_vid = rule["new_version_id"]
                    hit_canary = True
            elif rule["strategy"] == CanaryStrategy.WHITELIST.value:
                if user_id in rule["whitelist"]:
                    routed_vid = rule["new_version_id"]
                    hit_canary = True

        version = self._versions.get(routed_vid)
        result = CanaryRoutingResult(
            request_id=req_id, user_id=user_id,
            routed_model_version=version.version_number if version else "unknown",
            routing_strategy=CanaryStrategy(rule["strategy"]) if rule else CanaryStrategy.USER_HASH,
            hit_canary=hit_canary,
        )
        self._routing_log.append(result)
        return result

    def run_ab_test(self, test_id: str, control_version: str,
                    treatment_version: str, traffic_split: Dict[str, float],
                    duration_days: int = 14) -> ABTestResult:
        """创建并运行A/B测试"""
        ab_test = ABTestResult(
            test_id=test_id, control_version=control_version,
            treatment_version=treatment_version,
            start_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            traffic_split=traffic_split,
        )

        ctrl_metrics = {
            "like_rate": round(random.uniform(0.65, 0.80), 4),
            "avg_rating": round(random.uniform(3.8, 4.5), 2),
            "response_time_ms": round(random.uniform(300, 1200), 1),
            "conversion_rate": round(random.uniform(0.05, 0.15), 4),
            "sample_size": int(traffic_split.get("control", 0.5) * random.randint(500, 2000)),
        }
        treat_metrics = {
            k: round(v * random.uniform(0.95, 1.12), 4)
            for k, v in ctrl_metrics.items()}
        treat_metrics["sample_size"] = int(
            traffic_split.get("treatment", 0.5) * random.randint(500, 2000))

        ab_test.sample_sizes = {
            "control": ctrl_metrics["sample_size"],
            "treatment": treat_metrics["sample_size"],
        }
        ab_test.metrics_comparison = {"control": ctrl_metrics, "treatment": treat_metrics}

        like_improvement = (treat_metrics["like_rate"] - ctrl_metrics["like_rate"])
        n_ctrl = ctrl_metrics["sample_size"]
        n_treat = treat_metrics["sample_size"]
        p_control = ctrl_metrics["like_rate"]
        p_treatment = treat_metrics["like_rate"]
        pooled_p = (ctrl_metrics["like_rate"] * n_ctrl +
                     treat_metrics["like_rate"] * n_treat) / (n_ctrl + n_treat)
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n_ctrl + 1/n_treat))
        z_score = (p_treatment - p_control) / max(se, 0.0001)
        from math import erf, sqrt
        p_val = 2 * (1 - 0.5 * (1 + erf(abs(z_score) / sqrt(2))))
        ab_test.p_value = round(max(p_val, 0.0), 6)
        ab_test.is_significant = ab_test.p_value < 0.05
        ab_test.end_date = (datetime.now(timezone.utc) +
                             timedelta(days=duration_days)).strftime("%Y-%m-%d")

        if ab_test.is_significant and like_improvement > 0:
            ab_test.winner = treatment_version
            ab_test.recommendation = f"推荐全量推广新版本 (提升{like_improvement*100:+.1f}%, p={ab_test.p_value:.4f})"
        elif ab_test.is_significant and like_improvement <= 0:
            ab_test.winner = control_version
            ab_test.recommendation = f"保留当前版本 (新版本表现更差 {-like_improvement*100:.1f}%)"
        else:
            ab_test.winner = None
            ab_test.recommendation = "差异不显著，建议延长测试时间"

        self._ab_tests[test_id] = ab_test
        logger.info(f"[A/B测试] {test_id}: p={ab_test.p_value:.4f} "
                    f"显著={ab_test.is_significant} 推荐={ab_test.recommendation[:30]}")
        return ab_test

    def get_all_versions(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有模型版本"""
        versions = list(self._versions.values())
        if model_type:
            versions = [v for v in versions if v.model_type == model_type]
        return sorted([
            {"id": v.version_id, "name": v.model_name, "version": v.version_number,
             "type": v.model_type, "status": v.status.value,
             "is_current": self._current_models.get(v.model_type) == v.version_id,
             "canary_weight": v.canary_weight, "metrics": v.metrics}
            for v in versions], key=lambda x: x["version"], reverse=True)

    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计"""
        recent = self._routing_log[-1000:] if self._routing_log else []
        canary_hits = sum(1 for r in recent if r.hit_canary)
        return {
            "total_routed": len(self._routing_log),
            "canary_hit_rate": round(canary_hits / max(len(recent), 1) * 100, 2),
            "active_canary_rules": sum(1 for r in self._canary_rules if r["enabled"]),
            "active_ab_tests": len([t for t in self._ab_tests.values()
                                   if not t.end_date or t.end_date > datetime.now(timezone.utc).strftime("%Y-%m-%d")]),
            "current_models": dict(self._current_models),
        }


# ==================== Part H: 模块集成篇 — 海马体/自博弈/刑部 ====================


class IntegrationHub:
    """集成枢纽 — 连接海马体记忆/自博弈训练/刑部审计"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._memory_integration_log: List[Dict] = []
        self._red_team_pool: List[Dict] = []
        self._audit_log: List[Dict] = []
        self._integration_status = {
            "hippocampus_memory": False,
            "self_play_adversarial": False,
            "ministry_audit": False,
        }

    def sync_to_hippocampus(self, trace_id: str, user_input: str,
                               agent_output: str, agent_type: str,
                               importance: float = 0.5) -> Dict[str, Any]:
        """同步对话到海马体记忆系统"""
        entry = {
            "integration": "hippocampus_memory", "trace_id": trace_id,
            "memory_type": "chat_history",
            "content": {"user_input": user_input[:200], "agent_output": agent_output[:200],
                       "agent_type": agent_type},
            "importance": importance,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }
        self._memory_integration_log.append(entry)
        self._integration_status["hippocampus_memory"] = True
        logger.debug(f"[集成] 海马体记忆同步: trace={trace_id} 重要度={importance}")
        return entry

    def push_to_red_team(self, trace_id: str, user_input: str,
                         agent_output: str, dislike_reason: str) -> Dict[str, Any]:
        """推送点踩对话到红队攻击池"""
        attack_sample = {
            "source": "user_dislike_feedback", "trace_id": trace_id,
            "attack_type": "adversarial_question",
            "payload": {"question": user_input, "target_response": agent_output,
                       "weakness_type": dislike_reason},
            "added_at": datetime.now(timezone.utc).isoformat(),
            "used_in_training": False,
        }
        self._red_team_pool.append(attack_sample)
        self._integration_status["self_play_adversarial"] = True
        logger.info(f"[集成] 红队池新增: trace={trace_id} 原因={dislike_reason}")
        return attack_sample

    def log_to_audit(self, trace_id: str, record_id: int,
                      operator: str = "system", action: str = "chat_complete") -> Dict[str, Any]:
        """记录到刑部审计日志"""
        audit_entry = {
            "integration": "ministry_audit", "trace_id": trace_id,
            "record_id": record_id, "operator": operator,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "logged",
        }
        self._audit_log.append(audit_entry)
        self._integration_status["ministry_audit"] = True
        return audit_entry

    def get_red_team_weekly_batch(self) -> List[Dict]:
        """获取本周红队攻击样本批次"""
        one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        weekly = [s for s in self._red_team_pool if s["added_at"] >= one_week_ago]
        logger.info(f"[集成] 本周红队样本: {len(weekly)}条")
        return weekly

    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态总览"""
        return {
            **self._integration_status,
            "memory_sync_count": len(self._memory_integration_log),
            "red_team_pool_size": len(self._red_team_pool),
            "audit_log_count": len(self._audit_log),
            "all_integrated": all(self._integration_status.values()),
        }


# ==================== Part I-J: 运维监控篇 — Grafana看板+告警 ====================


class ClosedLoopMonitor:
    """闭环监控器 — Grafana看板指标+告警规则"""

    ALERT_RULES = [
        {"id": "mq_backlog", "name": "消息队列积压", "condition": "queue > 1000",
         "severity": "critical", "action": "扩容Worker"},
        {"id": "judge_accuracy_drop", "name": "裁判模型准确率持续下降",
         "condition": "accuracy_trend_2w < -0.03", "severity": "warning",
         "action": "触发重训练"},
        {"id": "low_feedback_rate", "name": "用户反馈率过低",
         "condition": "feedback_rate < 0.05", "severity": "info",
         "action": "优化反馈引导UI"},
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._daily_stats: List[Dict[str, Any]] = []
        self._active_alerts: List[Dict[str, Any]] = []
        self._alert_history: List[Dict[str, Any]] = []

    def record_daily_snapshot(self, stats: Dict[str, Any]) -> None:
        """记录每日快照"""
        snapshot = {
            **stats, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._daily_stats.append(snapshot)
        self._check_alerts(snapshot)

    def _check_alerts(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查告警规则"""
        triggered = []
        for rule in self.ALERT_RULES:
            should_alert = False
            if rule["id"] == "mq_backlog":
                should_alert = snapshot.get("queue_backlog", 0) > 1000
            elif rule["id"] == "judge_accuracy_drop":
                should_alert = snapshot.get("judge_accuracy_trend", 0) < -0.03
            elif rule["id"] == "low_feedback_rate":
                should_alert = snapshot.get("feedback_rate", 1) < 0.05

            if should_alert:
                alert = {
                    **rule, "triggered_at": datetime.now(timezone.utc).isoformat(),
                    "snapshot_values": {k: snapshot.get(k) for k in
                                      ["queue_backlog", "feedback_rate", "judge_accuracy_trend"]
                                      if k in snapshot},
                    "resolved": False,
                }
                triggered.append(alert)
                self._active_alerts.append(alert)
                self._alert_history.append(alert)
                logger.warning(f"[监控告警] {rule['name']}: {rule['condition']} → {rule['action']}")
        return triggered

    def resolve_alert(self, alert_id: Optional[str] = None) -> int:
        """解决告警"""
        resolved = 0
        alerts_to_resolve = self._active_alerts
        if alert_id:
            alerts_to_resolve = [a for a in self._active_alerts if a["id"] == alert_id]
        for alert in alerts_to_resolve:
            alert["resolved"] = True
            alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
            self._active_alerts = [a for a in self._active_alerts if a["resolved"]]
            resolved += 1
        return resolved

    def get_monitor_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """获取监控看板数据"""
        recent = [s for s in self._daily_stats
                  if s.get("date", "") >= (datetime.now(timezone.utc) -
                                               timedelta(days=days)).strftime("%Y-%m-%d")]
        if not recent:
            return {"period": f"近{days}天", "no_data": True}
        latest = recent[-1] if recent else {}
        return {
            "period": f"近{days}天",
            "latest_snapshot": latest,
            "trend_total_chats": self._calc_trend([s.get("total_chats", 0) for s in recent]),
            "trend_feedback_rate": self._calc_trend([s.get("feedback_rate", 0) for s in recent]),
            "trend_like_rate": self._calc_trend([s.get("like_rate", 0) for s in recent]),
            "active_alerts": len(self._active_alerts),
            "alert_history_7d": len([a for a in self._alert_history
                                    if a.get("triggered_at", "") >
                                    (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()]),
        }

    @staticmethod
    def _calc_trend(values: List[float]) -> str:
        """计算趋势方向"""
        if len(values) < 2:
            return "stable"
        recent_avg = statistics.mean(values[-7:]) if len(values) >= 7 else statistics.mean(values)
        older_avg = statistics.mean(values[:-7]) if len(values) > 7 else values[0]
        diff = (recent_avg - older_avg) / max(older_avg, 0.001)
        if diff > 0.05:
            return "rising"
        elif diff < -0.05:
            return "declining"
        return "stable"


# ==================== Part K: 总协调器 — 数据闭环全景看板 ====================


class DataClosedLoopOrchestrator:
    """数据闭环总协调器 — 统一管理全部模块+生成闭环看板"""

    ALL_MODULES = [
        "DataDesensitizer", "ChatRecordStore", "AsyncWriteEngine", "TraceTracker",
        "FeedbackCollector", "DataLakeArchiver", "TrainingDataAPI",
        "JudgeModelTrainer", "RLTrainingEngine", "ModelVersionManager",
        "IntegrationHub", "ClosedLoopMonitor",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.desensitizer = DataDesensitizer(config=self.config.get("desensitizer", {}))
        self.record_store = ChatRecordStore(config=self.config.get("storage", {}))
        self.async_writer = AsyncWriteEngine(config=self.config.get("async_write", {}))
        self.trace_tracker = TraceTracker()
        self.feedback_collector = FeedbackCollector(config=self.config.get("feedback", {}))
        self.data_lake = DataLakeArchiver(config=self.config.get("archive", {}))
        self.training_api = TrainingDataAPI(config=self.config.get("training_api", {}))
        self.judge_trainer = JudgeModelTrainer(config=self.config.get("judge", {}))
        self.rl_engine = RLTrainingEngine(config=self.config.get("rl", {}))
        self.model_manager = ModelVersionManager(config=self.config.get("model_mgmt", {}))
        self.integration_hub = IntegrationHub(config=self.config.get("integration", {}))
        self.monitor = ClosedLoopMonitor(config=self.config.get("monitor", {}))
        self._dashboard_history: List[DataClosedLoopDashboardData] = []

        self.async_writer.bind_store(self.record_store)
        self.feedback_collector.bind_store(self.record_store)
        self.training_api.bind_store(self.record_store)

    def initialize_all(self) -> Dict[str, Any]:
        """初始化所有模块"""
        self.judge_trainer.register_judge_model("judge_v1", "1.0")
        self.judge_trainer.register_judge_model("judge_zhouyu", "1.0", agent_type="zhouyu")
        self.judge_trainer.register_judge_model("judge_luxun", "1.0", agent_type="luxun")
        self.rl_engine.register_rl_config("ppo_policy_v1", base_model="Qwen-1.8B")
        self.model_manager.register_model("judge-main", "1.0", "judge",
                                        "models/judge_v1", {"accuracy": 0.82, "f1": 0.81})
        self.model_manager.register_model("policy-main", "1.0", "rl",
                                        "models/ppo_v1", {"mean_reward": 0.15})
        stats = {
            "modules_initialized": len(self.ALL_MODULES),
            "judge_models": len(self.judge_trainer._models),
            "rl_configs": len(self.rl_engine._rl_configs),
            "model_versions": len(self.model_manager._versions),
            "integrations": self.integration_hub.get_integration_status(),
        }
        logger.info("[数据闭环总管] 所有模块初始化完成")
        return stats

    def simulate_full_pipeline(self, num_chats: int = 200) -> None:
        """模拟完整的「咨询→反馈→训练→部署」流水线"""
        agents = ["zhouyu", "luxun", "zhugeliang", "caocao"]
        inputs = [
            "深圳南山区房价走势如何?", "帮我分析上海浦东投资回报率",
            "北京学区房哪个区域值得买?", "广州天河区租金回报率高吗?",
            "成都高新区未来发展前景", "杭州余杭区新房值得入手吗?",
            "南京江北新区和河西怎么选?", "武汉光谷片区升值空间大吗?",
            "西安高新区的房价合理吗?", "苏州工业园区的投资价值",
        ]

        for i in range(num_chats):
            tid = self.trace_tracker.generate_trace_id()
            sid = f"sess_{uuid.uuid4().hex[:8]}"
            uid = f"user_{random.randint(1, 100)}"
            uinp = random.choice(inputs)
            agt = random.choice(agents)
            aout = f"关于{uinp[:10]}...的分析结果：根据最新市场数据和AI模型预测，"
            aout += f"该区域的{'房价' if '房' in uinp else '投资'}趋势呈现{'上涨' if random.random()>0.3 else '平稳'}态势。"
            aout += f"建议{'买入' if random.random()>0.4 else '观望'}。具体报告可通过深度分析功能获取。"

            self.trace_tracker.begin_trace(tid, uid, sid)
            self.record_store.store_record(tid, sid, uid, uinp, aout, agt)
            self.async_writer.enqueue_write(tid, sid, uid, uinp, aout, agt)
            self.trace_tracker.complete_trace(tid, self.record_store._next_record_id - 1)

            if random.random() < 0.35:
                fb_type = random.choice([FeedbackType.LIKE, FeedbackType.DISLIKE])
                rating = None
                if fb_type == FeedbackType.RATING:
                    rating = random.randint(1, 5)
                reason = random.choice(list(FeedbackReason)) if fb_type == FeedbackType.DISLIKE else None
                self.feedback_collector.submit_feedback(tid, uid, fb_type, rating, reason)

            if random.random() < 0.3:
                imp = self.desensitizer.encrypt_user_id(uid)
                self.integration_hub.sync_to_hippocampus(tid, uinp, aout, agt,
                                                      importance=random.uniform(0.3, 0.9))
                self.integration_hub.log_to_audit(tid, self.record_store._next_record_id - 1)

        self.async_writer.process_queue(batch_size=num_chats)
        records_with_fb = self.record_store.query_for_training(feedback_only=True, limit=500)
        self.judge_trainer.build_dataset_from_records(records_with_fb)
        self.judge_trainer.simulate_training("judge_v1:1.0", epochs=8)
        self.rl_engine.build_rl_dataset(records_with_fb)
        self.rl_engine.simulate_ppo_training("ppo_policy_v1", total_steps=20000)

        self.monitor.record_daily_snapshot({
            "total_chats": num_chats, "queue_backlog": len(self.async_writer._task_queue),
            "feedback_rate": self.feedback_collector.get_feedback_stats()["like_rate"] / 100,
            "like_rate": self.feedback_collector.get_feedback_stats()["like_rate"] / 100,
            "judge_accuracy_trend": random.uniform(-0.05, 0.05),
        })

    def generate_dashboard(self) -> DataClosedLoopDashboardData:
        """生成数据闭环全景看板"""
        did = f"dcl_dash_{uuid.uuid4().hex[:8]}"
        store_stats = self.record_store.get_store_stats()
        fb_stats = self.feedback_collector.get_feedback_stats(30)
        writer_stats = self.async_writer.get_engine_stats()
        archive_stats = self.data_lake.get_archive_status()
        judge_eval = self.judge_trainer.evaluate_model("judge_v1:1.0")
        rl_result = self.rl_engine.simulate_ppo_training("ppo_policy_v1", 5000)
        routing_stats = self.model_manager.get_routing_stats()
        integration = self.integration_hub.get_integration_status()
        monitor_dash = self.monitor.get_monitor_dashboard(30)

        dashboard = DataClosedLoopDashboardData(
            dashboard_id=did, date_range="近30天",
            total_chats=store_stats["total_records"],
            chats_with_feedback=store_stats["with_feedback"],
            feedback_rate=store_stats["feedback_rate"],
            like_rate=fb_stats["like_rate"],
            dislike_rate=fb_stats["dislike_rate"],
            avg_rating=fb_stats.get("avg_rating"),
            async_write_success_rate=writer_stats["success_rate"],
            async_write_avg_latency_ms=writer_stats["avg_latency_ms"],
            queue_backlog=writer_stats["queue_backlog"],
            archive_status=archive_status,
            judge_model_metrics=judge_eval if "error" not in judge_eval else None,
            rl_training_progress=rl_result if "error" not in rl_result else None,
            active_model_versions=self.model_manager.get_all_versions()[:5],
            canary_routing_stats=routing_stats,
            ab_test_results=list(self.model_manager._ab_tests.values())[-3:],
            integration_status=integration,
            alerts_active=self.monitor._active_alerts,
            recommendations=self._generate_recommendations(store_stats, fb_stats, writer_stats),
        )
        self._dashboard_history.append(dashboard)
        return dashboard

    def _generate_recommendations(self, store_stats: Dict, fb_stats: Dict,
                                     writer_stats: Dict) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recs = []
        if writer_stats.get("alert_triggered"):
            recs.append({"category": "异步写入", "priority": "高",
                        "action": "消息队列积压超过阈值，立即扩容Worker或优化写入批处理"})
        if fb_stats.get("feedback_rate", 1) < 0.05:
            recs.append({"category": "反馈收集", "priority": "中",
                        "action": "反馈率低于5%，建议在智能体回复下方增加醒目的点赞/点踩按钮"})
        if store_stats.get("feedback_rate", 0) < 10:
            recs.append({"category": "数据质量", "priority": "高",
                        "action": "有反馈的数据占比低，考虑推出积分激励计划(每次有效反馈+10积分)"})
        recs.append({"category": "模型迭代", "priority": "中",
                     "action": "建议设定月度模型迭代节奏：裁判模型每月更新1次+RL策略每2周微调"})
        recs.append({"category": "红队训练", "priority": "低",
                     "action": f"红队池当前{len(self.integration_hub._red_team_pool)}个样本，"
                             f"建议每周定期抽取并触发自博弈训练"})
        return recs

    def render_dashboard_text(self, dashboard: Optional[DataClosedLoopDashboardData] = None) -> str:
        """渲染文本数据闭环看板"""
        d = dashboard or self.generate_dashboard()
        lines = []
        lines.append("=" * 78)
        lines.append("  房都督AI平台 · 数据闭环看板 (Data Closed-Loop Dashboard)")
        lines.append("  「一分二」生产数据→训练数据完整闭环 | 异步收集·离线训练·持续进化")
        lines.append("=" * 78)
        lines.append("")
        lines.append(f"  📊 对话总量: {d.total_chats:,} | 有反馈: {d.chats_with_feedback:,} "
                     f"({d.feedback_rate:.1f}%) | 点赞率: {d.like_rate:.1f}% | "
                     f"点踩率: {d.dislike_rate:.1f}% | 均分: {d.avg_rating}")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  ⚡ 异步写入引擎")
        lines.append("-" * 78)
        lines.append(f"  成功率: {d.async_write_success_rate:.1f}% | "
                     f"平均延迟: {d.async_write_avg_latency_ms:.1f}ms | "
                     f"队列积压: {d.queue_backlog}")
        aw = d.archive_status
        lines.append("")
        lines.append("-" * 78)
        lines.append("  📦 数据湖归档")
        lines.append("-" * 78)
        lines.append(f"  归档任务: {aw.get('total_jobs', 0)} | 已完成: {aw.get('completed', 0)} | "
                     f"压缩后: {aw.get('total_compressed_mb', 0):.1f}MB | "
                     f"平均压缩比: {aw.get('avg_compression_ratio', 0):.3f}")
        lines.append("")
        jm = d.judge_model_metrics
        if jm and "error" not in jm:
            lines.append("-" * 78)
            lines.append("  ⚖️ 裁判模型 (BERT二分类)")
            lines.append("-" * 78)
            lines.append(f"  准确率: {jm.get('accuracy', 0):.4f} | 精确率: {jm.get('precision', 0):.4f} | "
                         f"召回率: {jm.get('recall', 0):.4f} | F1: {jm.get('f1', 0):.4f}")
            lines.append(f"  最佳F1: {jm.get('best_f1', 0):.4f}@第{jm.get('best_epoch', 0)}轮 | "
                         f"推荐: {jm.get('recommendation', '')}")
        rl = d.rl_training_progress
        if rl and "error" not in rl:
            lines.append("")
            lines.append("-" * 78)
            lines.append("  🧠 强化学习 (PPO策略网络)")
            lines.append("-" * 78)
            rs = rl.get("final_stats", {})
            lines.append(f"  最终均值奖励: {rs.get('final_mean_reward', 0):+.4f} | "
                         f"最佳奖励: {rs.get('best_mean_reward', 0):+.4f} | "
                         f"提升幅度: {rs.get('improvement', 0):+.4f}")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  🔀 模型版本 & 灰度 & A/B测试")
        lines.append("-" * 78)
        cr = d.canary_routing_stats
        lines.append(f"  当前模型: {cr.get('current_models', {})} | "
                     f"灰度命中率: {cr.get('canary_hit_rate', 0):.1f}% | "
                     f"活跃灰度规则: {cr.get('active_canary_rules', 0)} | "
                     f"A/B测试: {cr.get('active_ab_tests', 0)}")
        for ver in d.active_model_versions[:4]:
            cur = "✅当前" if ver.get("is_current") else ""
            lines.append(f"  {'★' if ver.get('status')=='已部署' else ' '} "
                         f"{ver.get('name','')} v{ver.get('version','')} "
                         f"[{ver.get('type','')}] {cur}")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  🔗 模块集成状态")
        lines.append("-" * 78)
        integ = d.integration_status
        for mod, status in integ.items():
            icon = "✅" if status else "⬜"
            lines.append(f"  {icon} {mod}")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  🚨 监控告警")
        lines.append("-" * 78)
        if d.alerts_active:
            for alert in d.alerts_active[:3]:
                sev = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert.get("severity", ""), "⚪")
                lines.append(f"  {sev} {alert.get('name', '?')}: {alert.get('action', '')}")
        else:
            lines.append("  ✅ 无活跃告警")
        lines.append("")
        lines.append("-" * 78)
        lines.append("  💡 AI优化建议")
        lines.append("-" * 78)
        for rec in d.recommendations[:5]:
            prio = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(rec.get("priority", "中"), "⚪")
            lines.append(f"  {prio} [{rec.get('category')}] {rec.get('action', '')[:65]}")
        lines.append("")
        lines.append("=" * 78)
        return "\n".join(lines)


# ==================== 全局实例 ====================

data_desensitizer = DataDesensitizer()
chat_record_store = ChatRecordStore()
async_write_engine = AsyncWriteEngine()
trace_tracker = TraceTracker()
feedback_collector = FeedbackCollector()
data_lake_archiver = DataLakeArchiver()
training_data_api = TrainingDataAPI()
judge_model_trainer = JudgeModelTrainer()
rl_training_engine = RLTrainingEngine()
model_version_manager = ModelVersionManager()
integration_hub = IntegrationHub()
closed_loop_monitor = ClosedLoopMonitor()

data_closed_loop_orchestrator = DataClosedLoopOrchestrator()
