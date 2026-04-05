# -*- coding: utf-8 -*-
"""
修炼体系模块 - SQLAlchemy ORM 模型定义
=====================================

本文件包含修炼体系（Cultivation System）所有新模块需要的数据库ORM模型，
涵盖阵法系统、外气防御、修炼调度、指标监控、终极挑战等5大子系统。

模块结构：
1. 阵法阵列 (formation_array) - 5个表
2. 外气防御 (demon_body_externalqi) - 10个表
3. 修炼总调度 (cultivation_grand_orchestrator) - 3个表
4. 指标监控 (cultivation_metrics) - 3个表
5. 终极修炼 (ultimate_cultivation) - 9个表

总计：30个ORM模型

作者：数据库架构师
创建时间：2026-04-03
版本：1.0.0
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON,
    ForeignKey, UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


# =============================================================================
# 第一部分：阵法阵列模块 (formation_array.py)
# =============================================================================

class FormationTemplate(Base):
    """
    阵型模板表
    存储预定义的智能体协作阵型配置模板
    """
    __tablename__ = 'formation_templates'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(100), nullable=False, unique=True, comment='模板名称')
    description = Column(Text, comment='模板描述')
    formation_type = Column(String(50), nullable=False, comment='阵型类型：攻击/防御/辅助/均衡')
    min_nodes = Column(Integer, default=3, comment='最小节点数')
    max_nodes = Column(Integer, default=10, comment='最大节点数')
    topology_config = Column(JSON, comment='拓扑结构配置JSON')
    performance_baseline = Column(JSON, comment='性能基准指标JSON')
    deployment_params = Column(JSON, comment='部署参数配置JSON')
    is_active = Column(Boolean, default=True, comment='是否启用')
    version = Column(Integer, default=1, comment='版本号')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系定义
    instances = relationship('FormationInstance', back_populates='template', lazy='dynamic')

    __table_args__ = (
        Index('idx_formation_templates_type', 'formation_type'),
        Index('idx_formation_templates_active', 'is_active'),
    )


class FormationInstance(Base):
    """
    阵型实例表
    记录实际部署的阵型运行实例
    """
    __tablename__ = 'formation_instances'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_id = Column(Integer, ForeignKey('formation_templates.id'), nullable=False, comment='关联的模板ID')
    instance_name = Column(String(100), nullable=False, comment='实例名称')
    task_id = Column(String(50), comment='关联的任务ID')
    status = Column(String(20), default='initializing', comment='状态：initializing/running/paused/completed/failed')
    current_nodes = Column(Integer, default=0, comment='当前活跃节点数')
    config_override = Column(JSON, comment='覆盖配置JSON')
    metrics_snapshot = Column(JSON, comment='实时指标快照JSON')
    started_at = Column(DateTime, comment='启动时间')
    completed_at = Column(DateTime, comment='完成时间')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系定义
    template = relationship('FormationTemplate', back_populates='instances')
    nodes = relationship('ClusterNode', back_populates='formation_instance', lazy='dynamic')
    scheduling_records = relationship('SchedulingRecord', back_populates='formation_instance', lazy='dynamic')

    __table_args__ = (
        Index('idx_formation_instances_template', 'template_id'),
        Index('idx_formation_instances_status', 'status'),
        Index('idx_formation_instances_task', 'task_id'),
    )


class ClusterNode(Base):
    """
    集群节点表
    管理阵型中的每个计算节点信息
    """
    __tablename__ = 'cluster_nodes'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    formation_instance_id = Column(Integer, ForeignKey('formation_instances.id'), nullable=False, comment='所属阵型实例ID')
    node_id = Column(String(50), unique=True, comment='节点唯一标识')
    role = Column(String(30), nullable=False, comment='节点角色：core/edge/relay/coordinator')
    agent_type = Column(String(50), comment='运行的智能体类型')
    capacity_config = Column(JSON, comment='资源容量配置JSON')
    current_load = Column(Float, default=0.0, comment='当前负载率(0-1)')
    status = Column(String(20), default='idle', comment='状态：idle/busy/overloaded/offline')
    health_score = Column(Float, default=100.0, comment='健康分数(0-100)')
    network_topology = Column(JSON, comment='网络拓扑位置JSON')
    last_heartbeat = Column(DateTime, comment='最后心跳时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系定义
    formation_instance = relationship('FormationInstance', back_populates='nodes')

    __table_args__ = (
        Index('idx_cluster_nodes_instance', 'formation_instance_id'),
        Index('idx_cluster_nodes_role', 'role'),
        Index('idx_cluster_nodes_status', 'status'),
    )


class SchedulingRecord(Base):
    """
    调度记录表
    记录任务到节点的调度决策和执行情况
    """
    __tablename__ = 'scheduling_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    formation_instance_id = Column(Integer, ForeignKey('formation_instances.id'), nullable=False, comment='阵型实例ID')
    task_type = Column(String(50), nullable=False, comment='任务类型')
    source_node_id = Column(String(50), comment='源节点ID')
    target_node_id = Column(String(50), nullable=False, comment='目标节点ID')
    priority = Column(Integer, default=5, comment='优先级(1-10)')
    scheduling_algorithm = Column(String(50), comment='使用的调度算法')
    decision_factors = Column(JSON, comment='决策因素权重JSON')
    status = Column(String(20), default='pending', comment='状态：pending/running/completed/failed/retry')
    execution_time_ms = Column(Integer, comment='执行耗时(毫秒)')
    resource_allocated = Column(JSON, comment='分配的资源JSON')
    result_summary = Column(Text, comment='结果摘要')
    error_details = Column(Text, comment='错误详情')
    scheduled_at = Column(DateTime, default=datetime.utcnow, comment='调度时间')
    completed_at = Column(DateTime, comment='完成时间')

    # 关系定义
    formation_instance = relationship('FormationInstance', back_populates='scheduling_records')

    __table_args__ = (
        Index('idx_scheduling_records_instance', 'formation_instance_id'),
        Index('idx_scheduling_records_status', 'status'),
        Index('idx_scheduling_records_time', 'scheduled_at'),
    )


class FaultEvent(Base):
    """
    故障事件表
    记录系统运行过程中的故障和异常事件
    """
    __tablename__ = 'fault_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    formation_instance_id = Column(Integer, ForeignKey('formation_instances.id'), comment='关联的阵型实例ID')
    node_id = Column(String(50), comment='故障节点ID')
    fault_type = Column(String(50), nullable=False, comment='故障类型：network/computation/memory/timeout/deadlock')
    severity = Column(String(10), default='medium', comment='严重程度：low/medium/high/critical')
    error_code = Column(String(20), comment='错误代码')
    error_message = Column(Text, nullable=False, comment='错误消息')
    stack_trace = Column(Text, comment='堆栈跟踪')
    context_data = Column(JSON, comment='上下文数据JSON')
    impact_scope = Column(String(100), comment='影响范围描述')
    auto_recovered = Column(Boolean, default=False, comment='是否自动恢复')
    recovery_action = Column(String(200), comment='恢复动作描述')
    recovery_time_ms = Column(Integer, comment='恢复耗时(毫秒)')
    root_cause_analysis = Column(Text, comment='根因分析')
    detected_at = Column(DateTime, default=datetime.utcnow, comment='检测时间')
    resolved_at = Column(DateTime, comment='解决时间')

    __table_args__ = (
        Index('idx_fault_events_instance', 'formation_instance_id'),
        Index('idx_fault_events_type', 'fault_type'),
        Index('idx_fault_events_severity', 'severity'),
        Index('idx_fault_events_time', 'detected_at'),
    )


# =============================================================================
# 第二部分：外气防御模块 (demon_body_externalqi.py)
# =============================================================================

class InputPurificationLog(Base):
    """
    输入净化日志表
    记录输入数据的清洗和净化过程
    """
    __tablename__ = 'input_purification_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(50), nullable=False, comment='会话ID')
    input_hash = Column(String(64), comment='原始输入哈希值')
    original_input_preview = Column(Text, comment='原始输入预览(前500字符)')
    purification_rules_applied = Column(JSON, comment='应用的净化规则列表JSON')
    removed_elements = Column(JSON, comment='移除的元素详情JSON')
    transformed_output_preview = Column(Text, comment='转换后输出预览')
    risk_score_before = Column(Float, comment='净化前风险评分')
    risk_score_after = Column(Float, comment='净化后风险评分')
    processing_time_ms = Column(Integer, comment='处理耗时(毫秒)')
    validator_version = Column(String(20), comment='验证器版本')
    is_passed = Column(Boolean, default=False, comment='是否通过验证')
    rejection_reason = Column(Text, comment='拒绝原因')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_input_purification_session', 'session_id'),
        Index('idx_input_purification_passed', 'is_passed'),
        Index('idx_input_purification_time', 'created_at'),
    )


class ExtremeInputRecord(Base):
    """
    极端输入记录表
    记录超出正常范围的极端或异常输入
    """
    __tablename__ = 'extreme_input_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(50), nullable=False, comment='会话ID')
    input_category = Column(String(50), nullable=False, comment='输入类别：overlong/toxic/adversarial/malformed/empty')
    severity_level = Column(String(10), default='high', comment='严重程度：medium/high/critical')
    raw_content = Column(Text, comment='原始内容')
    anomaly_indicators = Column(JSON, comment='异常指标JSON')
    potential_impact = Column(Text, comment='潜在影响分析')
    mitigation_actions_taken = Column(JSON, comment='采取的缓解措施JSON')
    pattern_match = Column(String(100), comment='匹配的已知模式')
    is_blocked = Column(Boolean, default=False, comment='是否被阻止')
    block_reason = Column(Text, comment='阻止原因')
    user_id = Column(String(50), comment='用户ID（如可用）')
    ip_address = Column(String(45), comment='IP地址')
    created_at = Column(DateTime, default=datetime.utcnow, comment='记录时间')

    __table_args__ = (
        Index('idx_extreme_input_session', 'session_id'),
        Index('idx_extreme_input_category', 'input_category'),
        Index('idx_extreme_input_severity', 'severity_level'),
        Index('idx_extreme_input_blocked', 'is_blocked'),
    )


class DefenseEvent(Base):
    """
    防御事件表
    记录安全防御系统的触发和响应事件
    """
    __tablename__ = 'defense_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_type = Column(String(50), nullable=False, comment='事件类型：injection/xss/ddos/bf_attack/data_leakage')
    attack_vector = Column(String(100), comment='攻击向量')
    threat_level = Column(String(10), default='medium', comment='威胁等级：low/medium/high/critical')
    source_ip = Column(String(45), comment='来源IP')
    user_agent = Column(String(500), comment='用户代理')
    request_path = Column(String(500), comment='请求路径')
    payload_sample = Column(Text, comment='攻击载荷样本')
    defense_mechanism_triggered = Column(String(100), comment='触发的防御机制')
    response_action = Column(String(50), comment='响应动作：block/captcha/rate_limit/log/allow')
    outcome = Column(String(20), comment='结果：blocked/mitigated/bypassed/false_positive')
    damage_assessment = Column(Text, comment='损害评估')
    forensic_data = Column(JSON, comment='取证数据JSON')
    incident_report_ref = Column(String(50), comment='关联的事件报告编号')
    is_false_positive = Column(Boolean, default=False, comment='是否误报')
    created_at = Column(DateTime, default=datetime.utcnow, comment='事件发生时间')

    __table_args__ = (
        Index('idx_defense_events_type', 'event_type'),
        Index('idx_defense_events_threat', 'threat_level'),
        Index('idx_defense_events_outcome', 'outcome'),
        Index('idx_defense_events_time', 'created_at'),
    )


class CodeOptimizationRecord(Base):
    """
    代码优化记录表
    记录自动代码优化操作的历史
    """
    __tablename__ = 'code_optimization_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    optimization_type = Column(String(50), nullable=False, comment='优化类型：refactor/performance/security/readability')
    module_name = Column(String(100), nullable=False, comment='模块名称')
    file_path = Column(String(500), comment='文件路径')
    function_name = Column(String(100), comment='函数名')
    before_metrics = Column(JSON, comment='优化前指标JSON')
    after_metrics = Column(JSON, comment='优化后指标JSON')
    improvement_percentage = Column(Float, comment='提升百分比')
    complexity_reduction = Column(Float, comment='复杂度降低值')
    optimization_techniques = Column(JSON, comment='使用的优化技术列表JSON')
    code_diff_summary = Column(Text, comment='代码变更摘要')
    risk_assessment = Column(String(20), comment='风险评估：low/medium/high')
    review_status = Column(String(20), default='pending', comment='审查状态：pending/approved/rejected')
    reviewer_id = Column(String(50), comment='审查者ID')
    reviewer_comments = Column(Text, comment='审查意见')
    automated_test_results = Column(JSON, comment='自动化测试结果JSON')
    applied_at = Column(DateTime, default=datetime.utcnow, comment='应用时间')
    rollback_info = Column(JSON, comment='回滚信息JSON（如已回滚）')

    __table_args__ = (
        Index('idx_code_opt_module', 'module_name'),
        Index('idx_code_opt_type', 'optimization_type'),
        Index('idx_code_opt_status', 'review_status'),
        Index('idx_code_opt_time', 'applied_at'),
    )


class ResourceScalingEvent(Base):
    """
    资源伸缩事件表
    记录计算资源的自动扩缩容操作
    """
    __tablename__ = 'resource_scaling_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    scaling_direction = Column(String(10), nullable=False, comment='伸缩方向：up/down')
    resource_type = Column(String(50), nullable=False, comment='资源类型：cpu/memory/storage/gpu/network')
    trigger_metric = Column(String(50), comment='触发指标')
    trigger_threshold = Column(Float, comment='触发阈值')
    trigger_value = Column(Float, comment='触发时的实际值')
    current_capacity = Column(JSON, comment='当前容量JSON')
    target_capacity = Column(JSON, comment='目标容量JSON')
    scaling_factor = Column(Float, comment='伸缩系数')
    estimated_cost_impact = Column(Float, comment='预估成本影响(元)')
    cooldown_period_seconds = Column(Integer, comment='冷却期(秒)')
    scaling_algorithm = Column(String(50), comment='使用的伸缩算法')
    before_performance = Column(JSON, comment='伸缩前性能快照JSON')
    after_performance = Column(JSON, comment='伸缩后性能快照JSON')
    status = Column(String(20), default='initiated', comment='状态：initiated/in_progress/completed/rolled_back')
    started_at = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    duration_seconds = Column(Integer, comment='持续时长(秒)')

    __table_args__ = (
        Index('idx_resource_scaling_type', 'resource_type'),
        Index('idx_resource_scaling_direction', 'scaling_direction'),
        Index('idx_resource_scaling_status', 'status'),
        Index('idx_resource_scaling_time', 'started_at'),
    )


class HealthCheckResult(Base):
    """
    健康检查结果表
    记录系统和组件的健康检查数据
    """
    __tablename__ = 'health_check_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    check_type = Column(String(50), nullable=False, comment='检查类型：system/component/integration/e2e')
    component_name = Column(String(100), comment='组件名称')
    overall_status = Column(String(10), nullable=False, comment='总体状态：healthy/degraded/unhealthy/unknown')
    health_score = Column(Float, comment='健康分数(0-100)')
    response_time_ms = Column(Integer, comment='响应时间(毫秒)')
    details = Column(JSON, comment='详细检查项结果JSON')
    anomalies_detected = Column(JSON, comment='检测到的异常列表JSON')
    recommendations = Column(JSON, comment='建议措施JSON')
    dependencies_checked = Column(Integer, default=0, comment='检查的依赖数')
    dependencies_healthy = Column(Integer, default=0, comment='健康的依赖数')
    sla_compliance = Column(Boolean, comment='是否符合SLA')
    check_duration_ms = Column(Integer, comment='检查耗时(毫秒)')
    checked_at = Column(DateTime, default=datetime.utcnow, comment='检查时间')
    next_check_scheduled = Column(DateTime, comment='下次计划检查时间')

    __table_args__ = (
        Index('idx_health_check_type', 'check_type'),
        Index('idx_health_check_status', 'overall_status'),
        Index('idx_health_check_component', 'component_name'),
        Index('idx_health_check_time', 'checked_at'),
    )


class ExplanationRecord(Base):
    """
    解释记录表
    记录AI决策的解释和推理过程
    """
    __tablename__ = 'explanation_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(50), nullable=False, comment='会话ID')
    decision_type = Column(String(50), nullable=False, comment='决策类型：classification/recommendation/ranking/generation')
    model_version = Column(String(20), comment='模型版本')
    input_features = Column(JSON, comment='输入特征JSON')
    output_result = Column(JSON, comment='输出结果JSON')
    explanation_method = Column(String(50), comment='解释方法：shap/lime/attention/saliency')
    feature_importance = Column(JSON, comment='特征重要性JSON')
    reasoning_steps = Column(JSON, comment='推理步骤JSON')
    confidence_score = Column(Float, comment='置信度分数(0-1)')
    uncertainty_range = Column(JSON, comment='不确定性范围JSON')
    counterfactuals = Column(JSON, comment='反事实解释JSON')
    human_readable_explanation = Column(Text, comment='人类可读解释')
    complexity_rating = Column(String(10), comment='复杂度评级：low/medium/high')
    stakeholder = Column(String(50), comment='目标受众/利益相关者')
    feedback_received = Column(Text, comment='收到的反馈')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_explanation_session', 'session_id'),
        Index('idx_explanation_type', 'decision_type'),
        Index('idx_explanation_confidence', 'confidence_score'),
        Index('idx_explanation_time', 'created_at'),
    )


class PersonalizationProfile(Base):
    """
    个性化配置表
    存储用户个性化偏好和学习画像
    """
    __tablename__ = 'personalization_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(String(50), nullable=False, unique=True, comment='用户ID')
    profile_version = Column(Integer, default=1, comment='画像版本')
    preferences = Column(JSON, comment='偏好设置JSON')
    behavior_patterns = Column(JSON, comment='行为模式JSON')
    interaction_history_summary = Column(JSON, comment='交互历史摘要JSON')
    learning_style = Column(String(30), comment='学习风格：visual/auditory/kinesthetic/reading')
    expertise_level = Column(String(20), comment='专业水平：beginner/intermediate/advanced/expert')
    content_preferences = Column(JSON, comment='内容偏好JSON')
    ui_customization = Column(JSON, comment='界面定制JSON')
    notification_settings = Column(JSON, comment='通知设置JSON')
    accessibility_options = Column(JSON, comment='无障碍选项JSON')
    privacy_settings = Column(JSON, comment='隐私设置JSON')
    a_b_test_group = Column(String(20), comment='A/B测试分组')
    model_fine_tuning_params = Column(JSON, comment='模型微调参数JSON')
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后更新时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_personalization_user', 'user_id'),
        Index('idx_personalization_expertise', 'expertise_level'),
    )


class ReportGenerationLog(Base):
    """
    报告生成日志表
    记录报告生成过程的详细日志
    """
    __tablename__ = 'report_generation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(50), nullable=False, comment='报告ID')
    report_type = Column(String(50), nullable=False, comment='报告类型：analysis/consultation/audit/metric')
    generation_mode = Column(String(20), default='auto', comment='生成模式：auto/manual/scheduled/batch')
    template_used = Column(String(100), comment='使用的模板')
    data_sources = Column(JSON, comment='数据源列表JSON')
    parameters = Column(JSON, comment='生成参数JSON')
    processing_stages = Column(JSON, comment='处理阶段日志JSON')
    total_processing_time_ms = Column(Integer, comment='总处理时间(毫秒)')
    quality_score = Column(Float, comment='质量评分(0-100)')
    sections_generated = Column(Integer, comment='生成的章节数')
    word_count = Column(Integer, comment='字数')
    charts_included = Column(Integer, default=0, comment='包含的图表数')
    errors_encountered = Column(JSON, comment='遇到的错误列表JSON')
    retry_count = Column(Integer, default=0, comment='重试次数')
    output_format = Column(String(20), comment='输出格式：pdf/html/docx/json')
    file_size_bytes = Column(Integer, comment='文件大小(字节)')
    storage_location = Column(String(500), comment='存储路径')
    generated_by = Column(String(50), comment='生成者（用户ID或system）')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_report_gen_report', 'report_id'),
        Index('idx_report_gen_type', 'report_type'),
        Index('idx_report_gen_mode', 'generation_mode'),
        Index('idx_report_gen_time', 'started_at'),
    )


class FeedbackRecord(Base):
    """
    反馈记录表
    收集用户对系统输出的反馈
    """
    __tablename__ = 'feedback_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(String(50), nullable=False, comment='用户ID')
    feedback_type = Column(String(30), nullable=False, comment='反馈类型：rating/comment/bug/feature_request/complaint')
    target_type = Column(String(50), nullable=False, comment='目标类型：report/response/task/agent/ui')
    target_id = Column(String(50), comment='目标对象ID')
    rating = Column(Integer, comment='评分(1-5)')
    sentiment = Column(String(10), comment='情感倾向：positive/neutral/negative/mixed')
    content = Column(Text, comment='反馈内容')
    categories = Column(JSON, comment='分类标签JSON')
    priority = Column(String(10), default='medium', comment='优先级：low/medium/high/critical')
    status = Column(String(20), default='new', comment='状态：new/in_progress/resolved/closed/rejected')
    assigned_to = Column(String(50), comment='分配给的处理人')
    resolution = Column(Text, comment='解决方案摘要')
    resolution_time_hours = Column(Float, comment='解决耗时(小时)')
    satisfaction_follow_up = Column(Integer, comment='后续满意度评分(1-5)')
    action_items = Column(JSON, comment='行动项JSON')
    is_public = Column(Boolean, default=False, comment='是否公开显示')
    created_at = Column(DateTime, default=datetime.utcnow, comment='提交时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_target', 'target_type', 'target_id'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_priority', 'priority'),
        Index('idx_feedback_time', 'created_at'),
    )


# =============================================================================
# 第三部分：修炼总调度模块 (cultivation_grand_orchestrator.py)
# =============================================================================

class CultivationStageProgress(Base):
    """
    阶段进度表
    跟踪修炼体系各阶段的整体进度
    """
    __tablename__ = 'cultivation_stage_progress'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stage_name = Column(String(50), nullable=False, unique=True, comment='阶段名称')
    stage_order = Column(Integer, nullable=False, comment='阶段顺序')
    display_name = Column(String(100), comment='显示名称')
    description = Column(Text, comment='阶段描述')
    parent_stage = Column(String(50), comment='父阶段名称')
    status = Column(String(20), default='not_started', comment='状态：not_started/in_progress/completed/skipped/blocked')
    progress_percentage = Column(Float, default=0.0, comment='进度百分比(0-100)')
    total_milestones = Column(Integer, default=0, comment='总里程碑数')
    completed_milestones = Column(Integer, default=0, comment='已完成里程碑数')
    current_milestone = Column(String(100), comment='当前里程碑名称')
    start_criteria = Column(JSON, comment='开始条件JSON')
    completion_criteria = Column(JSON, comment='完成条件JSON')
    dependencies = Column(JSON, comment='依赖的其他阶段JSON')
    estimated_duration_days = Column(Integer, comment='预计持续天数')
    actual_start_date = Column(DateTime, comment='实际开始日期')
    actual_end_date = Column(DateTime, comment='实际结束日期')
    blocked_reason = Column(Text, comment='阻塞原因')
    notes = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_cultivation_stage_order', 'stage_order'),
        Index('idx_cultivation_stage_status', 'status'),
    )


class CheckpointData(Base):
    """
    检查点数据表
    保存关键节点状态的快照用于恢复
    """
    __tablename__ = 'checkpoint_data'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    checkpoint_name = Column(String(100), nullable=False, comment='检查点名称')
    stage_name = Column(String(50), nullable=False, comment='所属阶段')
    checkpoint_type = Column(String(30), comment='检查点类型：milestone/manual/auto/safety')
    sequence_number = Column(Integer, comment='序号')
    state_snapshot = Column(JSON, nullable=False, comment='状态快照JSON')
    data_checksum = Column(String(64), comment='数据校验和')
    metadata = Column(JSON, comment='元数据JSON')
    size_bytes = Column(Integer, comment='大小(字节)')
    storage_backend = Column(String(30), default='local', comment='存储后端：local/s3/oss/cos')
    storage_path = Column(String(500), comment='存储路径')
    is_validated = Column(Boolean, default=False, comment='是否已验证')
    validation_result = Column(Text, comment='验证结果')
    restore_count = Column(Integer, default=0, comment='恢复次数')
    last_restored_at = Column(DateTime, comment='最后恢复时间')
    expiry_date = Column(DateTime, comment='过期时间')
    created_by = Column(String(50), comment='创建者')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        UniqueConstraint('checkpoint_name', 'stage_name', name='uq_checkpoint_name_stage'),
        Index('idx_checkpoint_stage', 'stage_name'),
        Index('idx_checkpoint_type', 'checkpoint_type'),
        Index('idx_checkpoint_created', 'created_at'),
    )


class StageTransitionLog(Base):
    """
    阶段转换日志表
    记录阶段间的转换历史
    """
    __tablename__ = 'stage_transition_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    from_stage = Column(String(50), nullable=False, comment='源阶段')
    to_stage = Column(String(50), nullable=False, comment='目标阶段')
    transition_type = Column(String(30), nullable=False, comment='转换类型：progression/regression/skip/parallel/merge')
    trigger_event = Column(String(200), comment='触发事件')
    trigger_conditions_met = Column(JSON, comment='满足的触发条件JSON')
    pre_transition_state = Column(JSON, comment='转换前状态快照JSON')
    post_transition_state = Column(JSON, comment='转换后状态快照JSON')
    duration_minutes = Column(Integer, comment='转换持续时间(分钟)')
    success = Column(Boolean, default=True, comment='是否成功')
    failure_reason = Column(Text, comment='失败原因')
    rollback_performed = Column(Boolean, default=False, comment='是否执行了回滚')
    rollback_details = Column(Text, comment='回滚详情')
    data_migrated = Column(Boolean, default=False, comment='是否有数据迁移')
    migration_summary = Column(Text, comment='迁移摘要')
    approval_required = Column(Boolean, default=False, comment='是否需要审批')
    approved_by = Column(String(50), comment='审批人')
    notes = Column(Text, comment='备注')
    transitioned_at = Column(DateTime, default=datetime.utcnow, comment='转换时间')

    __table_args__ = (
        Index('idx_stage_trans_from', 'from_stage'),
        Index('idx_stage_trans_to', 'to_stage'),
        Index('idx_stage_trans_type', 'transition_type'),
        Index('idx_stage_trans_time', 'transitioned_at'),
    )


# =============================================================================
# 第四部分：指标监控模块 (cultivation_metrics.py)
# =============================================================================

class MetricRecord(Base):
    """
    指标记录表
    存储各类性能和质量指标的时序数据
    """
    __tablename__ = 'metric_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    metric_category = Column(String(50), nullable=False, comment='指标类别：performance/quality/business/resource/security')
    metric_type = Column(String(20), comment='指标类型：gauge/counter/histogram/summary')
    value = Column(Float, nullable=False, comment='指标值')
    unit = Column(String(20), comment='单位：%/ms/count/MB/score')
    tags = Column(JSON, comment='标签JSON（用于维度筛选）')
    dimensions = Column(JSON, comment='维度信息JSON')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')
    collection_method = Column(String(30), comment='采集方式：push/pull/agent/custom')
    data_source = Column(String(100), comment='数据来源')
    sample_rate = Column(Float, comment='采样率')
    expiration_ttl_seconds = Column(Integer, comment='过期时间TTL(秒)')
    is_anomaly = Column(Boolean, default=False, comment='是否为异常值')
    anomaly_score = Column(Float, comment='异常分数')
    related_alert_id = Column(Integer, comment='关联的告警ID')

    __table_args__ = (
        Index('idx_metric_name_time', 'metric_name', 'timestamp'),
        Index('idx_metric_category', 'metric_category'),
        Index('idx_metric_timestamp', 'timestamp'),
    )


class AlertEvent(Base):
    """
    告警事件表
    记录阈值违规和告警通知
    """
    __tablename__ = 'alert_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_name = Column(String(100), nullable=False, comment='告警名称')
    alert_rule_id = Column(String(50), comment='告警规则ID')
    severity = Column(String(10), nullable=False, comment='严重程度：info/warning/critical/emergency')
    status = Column(String(20), default='firing', comment='状态：firing/acknowledged/resolved/silenced')
    metric_name = Column(String(100), comment='关联的指标名')
    current_value = Column(Float, comment='当前值')
    threshold_value = Column(Float, comment='阈值')
    condition_operator = Column(String(10), comment='条件操作符：>/</=/<=/>=/!=')
    evaluation_window = Column(String(20), comment='评估窗口：1m/5m/15m/1h')
    message = Column(Text, comment='告警消息')
    context = Column(JSON, comment='上下文数据JSON')
    affected_services = Column(JSON, comment='影响的服务列表JSON')
    runbook_url = Column(String(500), comment='处理手册URL')
    notification_channels = Column(JSON, comment='通知渠道JSON')
    acknowledged_by = Column(String(50), comment='确认人')
    acknowledged_at = Column(DateTime, comment='确认时间')
    resolution_message = Column(Text, comment='解决消息')
    resolved_by = Column(String(50), comment='解决人')
    resolved_at = Column(DateTime, comment='解决时间')
    firing_duration_seconds = Column(Integer, comment='持续时长(秒)')
    suppression_info = Column(JSON, comment='抑制信息JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_metric', 'metric_name'),
        Index('idx_alert_time', 'created_at'),
    )


class AcceptanceValidationResult(Base):
    """
    验收验证结果表
    记录交付物的验收和验证结果
    """
    __tablename__ = 'acceptance_validation_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    validation_run_id = Column(String(50), nullable=False, unique=True, comment='验证运行ID')
    deliverable_type = Column(String(50), nullable=False, comment='交付物类型：model/code/document/system/module')
    deliverable_id = Column(String(50), nullable=False, comment='交付物ID')
    deliverable_version = Column(String(20), comment='版本号')
    validation_framework = Column(String(50), comment='验证框架/标准')
    criteria_set = Column(JSON, comment='验收标准集合JSON')
    test_cases_total = Column(Integer, default=0, comment='测试用例总数')
    test_cases_passed = Column(Integer, default=0, comment='通过的用例数')
    test_cases_failed = Column(Integer, default=0, comment='失败的用例数')
    test_cases_skipped = Column(Integer, default=0, comment='跳过的用例数')
    pass_rate = Column(Float, comment='通过率(%)')
    coverage_metrics = Column(JSON, comment='覆盖率指标JSON')
    performance_benchmarks = Column(JSON, comment='性能基准对比JSON')
    security_scan_results = Column(JSON, comment='安全扫描结果JSON')
    compliance_checklist = Column(JSON, comment='合规检查清单JSON')
    defects_found = Column(JSON, comment='发现的缺陷列表JSON')
    critical_defects_count = Column(Integer, default=0, comment='严重缺陷数')
    overall_verdict = Column(String(20), comment='总体判定：passed/conditional_pass/failed/pending')
    verdict_reason = Column(Text, comment='判定理由')
    stakeholder_signoffs = Column(JSON, comment='利益相关者签字确认JSON')
    next_steps = Column(Text, comment='后续步骤')
    validated_by = Column(String(50), comment='验证执行者')
    reviewed_by = Column(String(50), comment='审核者')
    validation_started_at = Column(DateTime, comment='验证开始时间')
    validation_completed_at = Column(DateTime, comment='验证完成时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_acceptance_deliverable', 'deliverable_type', 'deliverable_id'),
        Index('idx_acceptance_verdict', 'overall_verdict'),
        Index('idx_acceptance_time', 'validation_completed_at'),
    )


# =============================================================================
# 第五部分：终极修炼模块 (ultimate_cultivation.py)
# =============================================================================

class BiasDetectionResult(Base):
    """
    偏见检测结果表
    记录AI模型偏见检测和分析结果
    """
    __tablename__ = 'bias_detection_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    detection_run_id = Column(String(50), unique=True, comment='检测运行ID')
    model_id = Column(String(50), nullable=False, comment='被测模型ID')
    model_version = Column(String(20), comment='模型版本')
    dataset_used = Column(String(100), comment='使用的数据集')
    bias_categories_tested = Column(JSON, comment='测试的偏见类别JSON')
    biases_found = Column(JSON, comment='发现的偏见列表JSON')
    overall_bias_score = Column(Float, comment='总体偏见分数(0-1,越高越偏)')
    fairness_metrics = Column(JSON, comment='公平性指标JSON')
    demographic_parity_diff = Column(Float, comment='人口统计 parity 差异')
    equalized_odds_diff = Column(Float, comment='均衡几率差异')
    calibrated_predictions = Column(Boolean, comment='预测是否经过校准')
    mitigation_recommendations = Column(JSON, comment='缓解建议JSON')
    risk_level = Column(String(10), comment='风险等级：low/medium/high/critical')
    remediation_plan = Column(Text, comment='修复计划')
    retest_scheduled = Column(DateTime, comment='计划重新测试时间')
    tested_at = Column(DateTime, default=datetime.utcnow, comment='检测时间')
    created_by = Column(String(50), comment='检测执行者')

    __table_args__ = (
        Index('idx_bias_model', 'model_id'),
        Index('idx_bias_risk', 'risk_level'),
        Index('idx_bias_time', 'tested_at'),
    )


class ObjectiveBalanceSnapshot(Base):
    """
    目标均衡快照表
    捕获多目标优化的权衡状态
    """
    __tablename__ = 'objective_balance_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(50), unique=True, comment='快照ID')
    optimization_context = Column(String(100), comment='优化场景/上下文')
    objectives = Column(JSON, nullable=False, comment='目标列表JSON（含名称、权重、当前值）')
    pareto_frontier = Column(JSON, comment='Pareto前沿点集JSON')
    current_solution = Column(JSON, comment='当前解JSON')
    trade_off_matrix = Column(JSON, comment='权衡矩阵JSON')
    conflict_pairs = Column(JSON, comment='冲突的目标对JSON')
    synergy_pairs = Column(JSON, comment='协同的目标对JSON')
    balance_score = Column(Float, comment='均衡得分(0-1)')
    dominance_rank = Column(Integer, comment='支配排名')
    constraint_violations = Column(JSON, comment='约束违反情况JSON')
    sensitivity_analysis = Column(JSON, comment='敏感性分析JSON')
    recommendation = Column(Text, comment='调整建议')
    algorithm_used = Column(String(50), comment='使用的优化算法')
    computation_time_ms = Column(Integer, comment='计算耗时(毫秒)')
    captured_at = Column(DateTime, default=datetime.utcnow, comment='捕获时间')

    __table_args__ = (
        Index('idx_obj_balance_context', 'optimization_context'),
        Index('idx_obj_balance_time', 'captured_at'),
    )


class SelfCorrectionLog(Base):
    """
    自我纠错日志表
    记录AI系统的自我纠错和改进过程
    """
    __tablename__ = 'self_correction_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    correction_id = Column(String(50), unique=True, comment='纠错ID')
    issue_type = Column(String(50), nullable=False, comment='问题类型：error/bias/inefficiency/drift/anomaly')
    detection_method = Column(String(50), comment='检测方法')
    issue_description = Column(Text, nullable=False, comment='问题描述')
    severity = Column(String(10), comment='严重程度：low/medium/high/critical')
    root_cause_analysis = Column(Text, comment='根因分析')
    correction_strategy = Column(String(100), comment='纠错策略')
    actions_taken = Column(JSON, comment='采取的行动JSON')
    models_modified = Column(JSON, comment='修改的模型列表JSON')
    config_changes = Column(JSON, comment='配置变更JSON')
    data_updates = Column(JSON, comment='数据更新JSON')
    pre_correction_metrics = Column(JSON, comment='纠错前指标JSON')
    post_correction_metrics = Column(JSON, comment='纠错后指标JSON')
    improvement_percentage = Column(Float, comment='提升百分比')
    effectiveness_score = Column(Float, comment='有效性评分(0-10)')
    side_effects = Column(JSON, comment='副作用JSON')
    rollback_needed = Column(Boolean, default=False, comment='是否需要回滚')
    rollback_executed = Column(Boolean, default=False, comment='是否已执行回滚')
    lessons_learned = Column(Text, comment='经验教训')
    corrected_at = Column(DateTime, default=datetime.utcnow, comment='纠错时间')
    corrected_by = Column(String(50), comment='纠错执行者（人或自动）')

    __table_args__ = (
        Index('idx_self_correct_type', 'issue_type'),
        Index('idx_self_correct_severity', 'severity'),
        Index('idx_self_correct_time', 'corrected_at'),
    )


class NoHistoryTestResult(Base):
    """
    无历史测试结果表
    记录零样本/无历史数据场景下的测试表现
    """
    __tablename__ = 'no_history_test_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    test_run_id = Column(String(50), unique=True, comment='测试运行ID')
    scenario_description = Column(Text, nullable=False, comment='场景描述')
    domain_category = Column(String(50), comment='领域类别')
    difficulty_level = Column(String(10), comment='难度级别：easy/medium/hard/extreme')
    input_characteristics = Column(JSON, comment='输入特征JSON')
    expected_capabilities = Column(JSON, comment='期望能力JSON')
    actual_performance = Column(JSON, comment='实际表现JSON')
    accuracy_score = Column(Float, comment='准确率')
    robustness_score = Column(Float, comment='鲁棒性评分')
    adaptability_score = Column(Float, comment='适应性评分')
    reasoning_quality = Column(Text, comment='推理质量评价')
    errors_made = Column(JSON, comment='犯的错误列表JSON')
    novel_solutions_generated = Column(JSON, comment='产生的新颖解法JSON')
    comparison_with_transfer_learning = Column(JSON, comment='与迁移学习的对比JSON')
    generalization_potential = Column(Float, comment='泛化潜力评分(0-10)')
    confidence_interval = Column(JSON, comment='置信区间JSON')
    test_methodology = Column(String(100), comment='测试方法论')
    limitations_identified = Column(Text, comment='识别出的局限性')
    improvement_suggestions = Column(Text, comment='改进建议')
    tested_at = Column(DateTime, default=datetime.utcnow, comment='测试时间')
    tester_id = Column(String(50), comment='测试者ID')

    __table_args__ = (
        Index('idx_no_hist_domain', 'domain_category'),
        Index('idx_no_hist_difficulty', 'difficulty_level'),
        Index('idx_no_hist_time', 'tested_at'),
    )


class GeneralizationTestResult(Base):
    """
    泛化测试结果表
    记录跨领域/跨场景的泛化能力测试
    """
    __tablename__ = 'generalization_test_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    test_session_id = Column(String(50), unique=True, comment='测试会话ID')
    source_domain = Column(String(50), nullable=False, comment='源领域（训练领域）')
    target_domains = Column(JSON, comment='目标领域列表JSON')
    transfer_scenarios = Column(JSON, comment='迁移场景JSON')
    methodology = Column(String(50), comment='测试方法：few_shot/zero_shot/domain_adaptation/meta_learning')
    baseline_performance = Column(JSON, comment='基线性能JSON')
    transfer_performance = Column(JSON, comment='迁移后性能JSON')
    transfer_efficiency_ratio = Column(Float, comment='迁移效率比')
    domain_shift_magnitude = Column(Float, comment='领域偏移程度')
    negative_transfer_detected = Column(Boolean, default=False, comment='是否检测到负迁移')
    catastrophic_forgetting_check = Column(Boolean, comment='灾难性遗忘检查结果')
    continual_learning_capability = Column(Float, comment='持续学习能力评分')
    out_of_distribution_handling = Column(Text, comment='分布外数据处理评价')
    sample_efficiency = Column(Float, comment='样本效率')
    adaptation_speed = Column(Integer, comment='适应速度（迭代次数）')
    statistical_significance = Column(JSON, comment='统计显著性检验JSON')
    cross_validation_results = Column(JSON, comment='交叉验证结果JSON')
    recommendations = Column(Text, comment='建议')
    tested_at = Column(DateTime, default=datetime.utcnow, comment='测试时间')

    __table_args__ = (
        Index('idx_gen_test_source', 'source_domain'),
        Index('idx_gen_test_method', 'methodology'),
        Index('idx_gen_test_time', 'tested_at'),
    )


class ComputeBenchmark(Base):
    """
    算力基准测试表
    记录算力基准测试的性能数据
    """
    __tablename__ = 'compute_benchmarks'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    benchmark_id = Column(String(50), unique=True, comment='基准测试ID')
    benchmark_suite = Column(String(50), nullable=False, comment='基准测试套件名称')
    hardware_config = Column(JSON, nullable=False, comment='硬件配置JSON（CPU/GPU/内存等）')
    software_stack = Column(JSON, comment='软件栈JSON（OS/框架/驱动版本）')
    workload_type = Column(String(50), comment='负载类型：training/inference/both')
    test_parameters = Column(JSON, comment='测试参数JSON')
    throughput_metrics = Column(JSON, comment='吞吐量指标JSON（samples/sec等）')
    latency_metrics = Column(JSON, comment='延迟指标JSON（p50/p95/p99等）')
    utilization_rates = Column(JSON, comment='利用率JSON（CPU/GPU/内存/IO）')
    power_consumption_watts = Column(Float, comment='功耗（瓦特）')
    energy_efficiency = Column(Float, comment='能效比（performance per watt）')
    memory_bandwidth_gb_s = Column(Float, comment='内存带宽(GB/s)')
    flops_measured = Column(Float, comment='实测FLOPS')
    flops_theoretical = Column(Float, comment='理论峰值FLOPS')
    efficiency_percentage = Column(Float, comment='效率百分比')
    thermal_throttling = Column(Boolean, comment='是否出现热降频')
    stability_score = Column(Float, comment='稳定性评分(0-10)')
    comparison_with_baseline = Column(JSON, comment='与基线的对比JSON')
    optimization_opportunities = Column(JSON, comment='优化机会JSON')
    cost_per_operation = Column(Float, comment='每次运算成本')
    environmental_impact = Column(JSON, comment='环境影响（碳排放等）JSON')
    run_duration_seconds = Column(Integer, comment='运行时长(秒)')
    conducted_at = Column(DateTime, default=datetime.utcnow, comment='测试时间')
    conducted_by = Column(String(50), comment='测试执行者')

    __table_args__ = (
        Index('idx_compute_benchmark_suite', 'benchmark_suite'),
        Index('idx_compute_workload', 'workload_type'),
        Index('idx_compute_time', 'conducted_at'),
    )


class CreativeSolutionRecord(Base):
    """
    创新方案记录表
    记录AI产生的创新性解决方案
    """
    __tablename__ = 'creative_solution_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    solution_id = Column(String(50), unique=True, comment='方案ID')
    problem_statement = Column(Text, nullable=False, comment='问题陈述')
    problem_domain = Column(String(50), comment='问题领域')
    problem_complexity = Column(String(10), comment='问题复杂度：simple/complex/wicked')
    solution_description = Column(Text, nullable=False, comment='方案描述')
    novelty_score = Column(Float, comment='新颖性评分(0-10)')
    feasibility_score = Column(Float, comment='可行性评分(0-10)')
    impact_potential = Column(Float, comment='潜在影响力评分(0-10)')
    creativity_metrics = Column(JSON, comment='创造性指标JSON（原创性、灵活性、流畅性等）')
    approach_used = Column(String(50), comment='使用的创造性方法：combinatorial/analogical/divergent/transformative')
    inspiration_sources = Column(JSON, comment='灵感来源JSON')
    components = Column(JSON, comment='方案组件JSON')
    alternative_variants = Column(JSON, comment='替代变体JSON')
    human_evaluation = Column(JSON, comment='人工评估JSON')
    expert_reviews = Column(JSON, comment='专家评审JSON')
    implementation_status = Column(String(20), default='concept', comment='实现状态：concept/prototype/implemented/deployed')
    patents_filed = Column(Boolean, default=False, comment='是否申请专利')
    publications = Column(JSON, comment='相关发表JSON')
    business_value = Column(Float, comment='商业价值估算')
    ethical_considerations = Column(Text, comment='伦理考量')
    generated_by_model = Column(String(50), comment='生成此方案的模型ID')
    generation_method = Column(String(50), comment='生成方法')
    generation_time_ms = Column(Integer, comment='生成耗时(毫秒)')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = Column(String(50), comment='创建者')

    __table_args__ = (
        Index('idx_creative_domain', 'problem_domain'),
        Index('idx_creative_novelty', 'novelty_score'),
        Index('idx_creative_status', 'implementation_status'),
        Index('idx_creative_time', 'created_at'),
    )


class EvolutionIteration(Base):
    """
    进化迭代记录表
    追踪系统进化过程的具体迭代
    """
    __tablename__ = 'evolution_iterations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    iteration_number = Column(Integer, nullable=False, comment='迭代编号')
    evolution_run_id = Column(String(50), nullable=False, comment='进化运行ID')
    evolution_strategy = Column(String(50), comment='进化策略：genetic/swarm/gradient_free/hybrid')
    population_size = Column(Integer, comment='种群规模')
    selection_method = Column(String(50), comment='选择方法')
    crossover_rate = Column(Float, comment='交叉概率')
    mutation_rate = Column(Float, comment='变异概率')
    fitness_function = Column(String(100), comment='适应度函数')
    best_individual = Column(JSON, comment='最优个体JSON')
    best_fitness_score = Column(Float, comment='最优适应度分数')
    average_fitness_score = Column(Float, comment='平均适应度分数')
    worst_fitness_score = Column(Float, comment='最差适应度分数')
    diversity_index = Column(Float, comment='多样性指数')
    convergence_metrics = Column(JSON, comment='收敛指标JSON')
    improvements_over_previous = Column(JSON, comment='相比上一次迭代的改进JSON')
    computational_cost = Column(JSON, comment='计算成本JSON（时间/资源）')
    hyperparameters_tuned = Column(JSON, comment='调优的超参数JSON')
    architecture_changes = Column(JSON, comment='架构变更JSON')
    phenotype_description = Column(Text, comment='表现型描述')
    genotype_encoding = Column(JSON, comment='基因型编码JSON')
    novelty_introduced = Column(Text, comment='引入的新颖性描述')
    regression_tests_passed = Column(Boolean, comment='回归测试是否通过')
    validation_results = Column(JSON, comment='验证结果JSON')
    iteration_duration_seconds = Column(Integer, comment='迭代时长(秒)')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        UniqueConstraint('iteration_number', 'evolution_run_id', name='uq_evolution_iteration'),
        Index('idx_evolution_run', 'evolution_run_id'),
        Index('idx_evolution_fitness', 'best_fitness_score'),
        Index('idx_evolution_time', 'completed_at'),
    )


class UltimateChallengeResult(Base):
    """
    终极挑战结果表
    记录系统在极限条件下的测试结果
    """
    __tablename__ = 'ultimate_challenge_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    challenge_id = Column(String(50), unique=True, comment='挑战ID')
    challenge_name = Column(String(100), nullable=False, comment='挑战名称')
    challenge_category = Column(String(50), comment='挑战类别：stress/adversarial/edge_case/scalability/robustness')
    difficulty_tier = Column(String(10), comment='难度层级：tier1/tier2/tier3/tier4/tier5')
    challenge_description = Column(Text, comment='挑战描述')
    success_criteria = Column(JSON, nullable=False, comment='成功标准JSON')
    environment_setup = Column(JSON, comment='环境配置JSON')
    stress_parameters = Column(JSON, comment='压力参数JSON（并发量/数据量/时间限制等）')
    adversarial_attacks_used = Column(JSON, comment='使用的对抗攻击JSON')
    system_configuration = Column(JSON, comment='系统配置JSON')
    results_raw = Column(JSON, comment='原始结果JSON')
    results_normalized = Column(JSON, comment='归一化结果JSON')
    overall_score = Column(Float, comment='总分(0-1000)')
    passed = Column(Boolean, comment='是否通过')
    grade = Column(String(2), comment='等级：A+/A/A-/B+/B/B-/C/D/F')
    strengths_identified = Column(JSON, comment='识别的优势JSON')
    weaknesses_identified = Column(JSON, comment='识别的弱点JSON')
    bottlenecks_found = Column(JSON, comment='发现的瓶颈JSON')
    breaking_point = Column(Text, comment='崩溃点描述（如有）')
    recovery_capability = Column(Text, comment='恢复能力评价')
    lessons_critical = Column(JSON, comment='关键教训JSON')
    comparison_with_previous_runs = Column(JSON, comment='与之前运行的对比JSON')
    world_ranking_if_applicable = Column(Integer, comment='世界排名（如适用）')
    certification_eligible = Column(Boolean, comment='是否符合认证资格')
    next_challenge_recommended = Column(String(100), comment='推荐的下一个挑战')
    challenge_conducted_at = Column(DateTime, default=datetime.utcnow, comment='挑战执行时间')
    conducted_by = Column(String(50), comment='执行者')
    external_auditor = Column(String(50), comment='外部审计员（如有）')
    audit_signature = Column(String(100), comment='审计签名（哈希）')

    __table_args__ = (
        Index('idx_ultimate_challenge_cat', 'challenge_category'),
        Index('idx_ultimate_tier', 'difficulty_tier'),
        Index('idx_ultimate_passed', 'passed'),
        Index('idx_ultimate_score', 'overall_score'),
        Index('idx_ultimate_time', 'challenge_conducted_at'),
    )


# =============================================================================
# 第六部分：三界证道模块 (transcendence.py) - 成仙之路
# =============================================================================

class EternalRuntimeStatus(Base):
    """
    永续运行状态表
    记录系统永续运行的关键健康指标和可用性数据
    """
    __tablename__ = 'eternal_runtime_status'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    node_id = Column(String(50), unique=True, nullable=False, comment='节点唯一标识')
    node_name = Column(String(100), comment='节点名称')
    health_status = Column(String(20), default='healthy', comment='健康状态：healthy/degraded/critical/down')
    health_score = Column(Float, default=100.0, comment='健康分数(0-100)')
    uptime_seconds = Column(Float, default=0.0, comment='累计运行时长(秒)')
    uptime_percentage = Column(Float, default=100.0, comment='可用性百分比(%)')
    last_boot_time = Column(DateTime, comment='上次启动时间')
    restart_count = Column(Integer, default=0, comment='重启次数')
    failure_count = Column(Integer, default=0, comment='故障次数')
    mean_time_between_failures = Column(Float, comment='平均故障间隔时间(MTBF,小时)')
    mean_time_to_recover = Column(Float, comment='平均恢复时间(MTTR,秒)')
    cpu_usage_avg = Column(Float, comment='CPU平均使用率(%)')
    memory_usage_avg = Column(Float, comment='内存平均使用率(%)')
    disk_usage_avg = Column(Float, comment='磁盘平均使用率(%)')
    network_latency_ms = Column(Float, comment='网络延迟(毫秒)')
    active_connections = Column(Integer, comment='活跃连接数')
    requests_per_second = Column(Float, comment='每秒请求数(RPS)')
    error_rate = Column(Float, comment='错误率(%)')
    prediction_model_version = Column(String(20), comment='预测模型版本')
    next_predicted_failure = Column(DateTime, comment='预测的下次故障时间')
    auto_recovery_enabled = Column(Boolean, default=True, comment='是否启用自动恢复')
    backup_status = Column(String(20), comment='备份状态：up_to_date/lagging/failed')
    data_integrity_check = Column(Boolean, comment='数据完整性检查结果')
    sla_compliance = Column(Boolean, default=True, comment='是否符合SLA')
    metadata = Column(JSON, comment='扩展元数据JSON')
    checked_at = Column(DateTime, default=datetime.utcnow, comment='检查时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_eternal_node', 'node_id'),
        Index('idx_eternal_health', 'health_status'),
        Index('idx_eternal_uptime', 'uptime_percentage'),
        Index('idx_eternal_checked', 'checked_at'),
    )


class EvolutionRecord(Base):
    """
    进化记录表
    记录系统的进化迭代过程、性能提升和知识发现
    """
    __tablename__ = 'evolution_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    evolution_run_id = Column(String(50), nullable=False, comment='进化运行ID')
    generation_number = Column(Integer, nullable=False, comment='代数/世代编号')
    evolution_strategy = Column(String(50), comment='进化策略：genetic/swarm/gradient_free/meta_learning')
    population_size = Column(Integer, comment='种群规模')
    tasks_processed_count = Column(Integer, default=0, comment='处理的任务数')
    learning_efficiency_gain = Column(Float, default=0.0, comment='学习效率提升(%)')
    performance_improvement = Column(Float, default=0.0, comment='性能提升(%)')
    knowledge_discovered_count = Column(Integer, default=0, comment='发现的新知识数量')
    new_strategies_discovered = Column(JSON, comment='新发现的策略列表JSON')
    model_improvements = Column(JSON, comment='模型改进详情JSON（各指标的提升）')
    distillation_applied = Column(Boolean, default=False, comment='是否应用了模型蒸馏')
    distillation_details = Column(JSON, comment='蒸馏详情JSON（压缩比、精度损失等）')
    pruning_applied = Column(Boolean, default=False, comment='是否应用了模型剪枝')
    pruning_ratio = Column(Float, comment='剪枝比例')
    architecture_changes = Column(JSON, comment='架构变更JSON')
    hyperparameters_optimized = Column(JSON, comment='优化的超参数JSON')
    best_fitness_score = Column(Float, comment='最优适应度分数')
    average_fitness_score = Column(Float, comment='平均适应度分数')
    convergence_metrics = Column(JSON, comment='收敛指标JSON')
    computational_cost_hours = Column(Float, comment='计算成本(小时)')
    energy_consumption_kwh = Column(Float, comment='能耗(千瓦时)')
    novelty_introduced = Column(Text, comment='引入的新颖性描述')
    regression_test_passed = Column(Boolean, comment='回归测试是否通过')
    validation_results = Column(JSON, comment='验证结果JSON')
    iteration_duration_seconds = Column(Integer, comment='迭代时长(秒)')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        UniqueConstraint('evolution_run_id', 'generation_number', name='uq_evolution_gen'),
        Index('idx_evolution_record_run', 'evolution_run_id'),
        Index('idx_evolution_record_gen', 'generation_number'),
        Index('idx_evolution_record_strategy', 'evolution_strategy'),
        Index('idx_evolution_record_time', 'completed_at'),
    )


class ResourceAllocationLog(Base):
    """
    资源分配日志表
    记录资源的调度决策、边缘卸载和价值交换过程
    """
    __tablename__ = 'resource_allocation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    allocation_id = Column(String(50), unique=True, comment='分配唯一ID')
    scheduling_decision_id = Column(String(50), comment='关联的调度决策ID')
    resource_type = Column(String(50), nullable=False, comment='资源类型：compute/memory/storage/network/gpu')
    source_node = Column(String(50), comment='源节点')
    target_node = Column(String(50), nullable=False, comment='目标节点')
    allocation_amount = Column(Float, comment='分配数量')
    allocation_unit = Column(String(20), comment='单位：core/GB/MB/s')
    priority = Column(Integer, default=5, comment='优先级(1-10)')
    allocation_algorithm = Column(String(50), comment='使用的分配算法')
    decision_factors = Column(JSON, comment='决策因素权重JSON')
    edge_offload_enabled = Column(Boolean, default=False, comment='是否启用边缘卸载')
    edge_offload_target = Column(String(50), comment='边缘卸载目标节点')
    offload_data_size_mb = Column(Float, comment='卸载数据大小(MB)')
    offload_latency_ms = Column(Integer, comment='卸载延迟(毫秒)')
    value_exchange_enabled = Column(Boolean, default=False, comment='是否启用价值交换')
    exchange_type = Column(String(30), comment='交换类型：barter/credit/token')
    exchange_value = Column(Float, comment='交换价值')
    exchange_counterparty = Column(String(50), comment='交易对手方')
    cost_savings = Column(Float, comment='节省的成本')
    efficiency_gain = Column(Float, comment='效率提升(%)')
    status = Column(String(20), default='pending', comment='状态：pending/allocated/in_use/released/failed')
    duration_seconds = Column(Integer, comment='分配持续时长(秒)')
    actual_usage = Column(JSON, comment='实际使用情况JSON')
    release_reason = Column(String(200), comment='释放原因')
    allocated_at = Column(DateTime, default=datetime.utcnow, comment='分配时间')
    released_at = Column(DateTime, comment='释放时间')

    __table_args__ = (
        Index('idx_resource_alloc_type', 'resource_type'),
        Index('idx_resource_alloc_target', 'target_node'),
        Index('idx_resource_alloc_status', 'status'),
        Index('idx_resource_alloc_time', 'allocated_at'),
    )


class RecoveryEvent(Base):
    """
    恢复事件表
    记录系统故障后的恢复事件和数据回滚情况
    """
    __tablename__ = 'recovery_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    recovery_event_id = Column(String(50), unique=True, comment='恢复事件唯一ID')
    related_fault_event_id = Column(String(50), comment='关联的故障事件ID')
    node_id = Column(String(50), nullable=False, comment='发生故障的节点ID')
    failure_type = Column(String(50), nullable=False, comment='故障类型：hardware/network/software/data/human')
    failure_severity = Column(String(10), comment='故障严重程度：low/medium/high/critical')
    detection_method = Column(String(50), comment='检测方法：monitoring/prediction/user_report/heartbeat')
    detected_at = Column(DateTime, comment='检测时间')
    recovery_initiated_at = Column(DateTime, comment='恢复启动时间')
    recovery_completed_at = Column(DateTime, comment='恢复完成时间')
    total_recovery_time_ms = Column(Integer, comment='总恢复耗时(毫秒)')
    recovery_strategy = Column(String(50), comment='恢复策略：restart/failover/rollback/rebuild/migration')
    automatic_recovery = Column(Boolean, default=False, comment='是否自动恢复')
    recovery_steps_executed = Column(JSON, comment='执行的恢复步骤JSON')
    data_loss_occurred = Column(Boolean, default=False, comment='是否发生数据丢失')
    data_loss_extent = Column(String(50), comment='数据丢失程度：none/partial/significant/total')
    affected_data_entities = Column(JSON, comment='受影响的数据实体列表JSON')
    rollback_performed = Column(Boolean, default=False, comment='是否执行了回滚')
    rollback_target_checkpoint = Column(String(100), comment='回滚目标检查点')
    rollback_data_restored = Column(Boolean, comment='回滚数据是否成功恢复')
    services_impacted = Column(JSON, comment='受影响的服务列表JSON')
    users_impacted_count = Column(Integer, comment='受影响的用户数')
    business_impact_assessment = Column(Text, comment='业务影响评估')
    root_cause_identified = Column(Boolean, comment='根因是否已识别')
    root_cause_summary = Column(Text, comment='根因摘要')
    preventive_actions_taken = Column(JSON, comment='采取的预防措施JSON')
    post_recovery_validation = Column(Boolean, comment='恢复后验证是否通过')
    lessons_learned = Column(Text, comment='经验教训')
    follow_up_actions = Column(JSON, comment='后续行动项JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_recovery_node', 'node_id'),
        Index('idx_recovery_type', 'failure_type'),
        Index('idx_recovery_severity', 'failure_severity'),
        Index('idx_recovery_time', 'recovery_completed_at'),
        Index('idx_recovery_automatic', 'automatic_recovery'),
    )


# =============================================================================
# 第七部分：三界证道模块 (transcendence.py) - 成神之路
# =============================================================================

class DiscoveredRule(Base):
    """
    发现的规则表
    存储系统通过洞察引擎发现的因果规则和规律
    """
    __tablename__ = 'discovered_rules'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_id = Column(String(50), unique=True, nullable=False, comment='规则唯一标识')
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    rule_description = Column(Text, comment='规则详细描述')
    domain = Column(String(50), comment='所属领域')
    rule_category = Column(String(50), comment='规则类别：causal/correlation/pattern/anomaly')
    causal_factors = Column(JSON, nullable=False, comment='因果因子列表JSON（输入变量）')
    effect_variables = Column(JSON, comment='效果变量列表JSON（输出变量）')
    confidence_score = Column(Float, nullable=False, comment='置信度分数(0-1)')
    support_level = Column(Float, comment='支持度(0-1)')
    lift_value = Column(Float, comment='提升度')
    rule_complexity = Column(String(10), comment='复杂度：simple/medium/complex')
    temporal_validity_start = Column(DateTime, comment='时效性起始时间')
    temporal_validity_end = Column(DateTime, comment='时效性结束时间')
    is_temporal_rule = Column(Boolean, default=False, comment='是否有时效性')
    source_system = Column(String(50), comment='来源系统/模块')
    discovery_method = Column(String(50), comment='发现方法：statistical/ml/symbolic/hybrid')
    discovery_timestamp = Column(DateTime, default=datetime.utcnow, comment='发现时间')
    training_data_source = Column(String(100), comment='训练数据来源')
    sample_size = Column(Integer, comment='样本量')
    validation_status = Column(String(20), default='pending', comment='验证状态：pending/validated/invalidated')
    validation_accuracy = Column(Float, comment='验证准确率')
    usage_count = Column(Integer, default=0, comment='使用次数')
    last_used_at = Column(DateTime, comment='最后使用时间')
    is_active = Column(Boolean, default=True, comment='是否激活')
    version = Column(Integer, default=1, comment='版本号')
    parent_rule_id = Column(String(50), comment='父规则ID（如为衍生规则）')
    related_rules = Column(JSON, comment='相关规则ID列表JSON')
    business_value = Column(Float, comment='业务价值评分(0-10)')
    risk_level = Column(String(10), comment='风险等级：low/medium/high')
    approved_by = Column(String(50), comment='审批人')
    approval_status = Column(String(20), comment='审批状态：draft/pending/approved/rejected')
    notes = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_rule_domain', 'domain'),
        Index('idx_rule_confidence', 'confidence_score'),
        Index('idx_rule_source', 'source_system'),
        Index('idx_rule_status', 'validation_status'),
        Index('idx_rule_active', 'is_active'),
        Index('idx_rule_discovery', 'discovery_timestamp'),
    )


class DigitalTwinModel(Base):
    """
    数字孪生模型表
    存储数字孪生模拟系统的配置和状态
    """
    __tablename__ = 'digital_twin_models'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    twin_id = Column(String(50), unique=True, nullable=False, comment='数字孪生唯一标识')
    twin_name = Column(String(100), nullable=False, comment='数字孪生名称')
    modeled_system_id = Column(String(50), nullable=False, comment='建模的系统/实体ID')
    modeled_system_type = Column(String(50), comment='建模的系统类型：infrastructure/application/process/organization')
    fidelity_level = Column(String(20), default='medium', comment='保真度级别：low/medium/high/ultra_high')
    fidelity_score = Column(Float, comment='保真度评分(0-100)')
    model_architecture = Column(JSON, comment='模型架构JSON（组件及其关系）')
    component_states = Column(JSON, comment='组件状态快照JSON')
    simulation_parameters = Column(JSON, comment='模拟参数配置JSON')
    physics_engine_config = Column(JSON, comment='物理引擎配置JSON（如适用）')
    behavior_models = Column(JSON, comment='行为模型JSON')
    data_sources_mapped = Column(JSON, comment='映射的数据源JSON')
    synchronization_mode = Column(String(20), comment='同步模式：real_time/batch/event_driven')
    sync_frequency_seconds = Column(Integer, comment='同步频率(秒)')
    last_sync_time = Column(DateTime, comment='最后同步时间')
    sync_status = Column(String(20), comment='同步状态：synced/lagging/error/disconnected')
    simulation_count_total = Column(Integer, default=0, comment='总模拟次数')
    simulation_count_success = Column(Integer, default=0, comment='成功模拟次数')
    average_simulation_duration_ms = Column(Integer, comment='平均模拟时长(毫秒)')
    prediction_accuracy = Column(Float, comment='预测准确率')
    what_if_scenarios_run = Column(Integer, default=0, comment='运行的假设场景数')
    anomaly_detection_enabled = Column(Boolean, default=True, comment='是否启用异常检测')
    anomalies_detected = Column(JSON, comment='检测到的异常列表JSON')
    model_version = Column(Integer, default=1, comment='模型版本')
    computational_requirements = Column(JSON, comment='计算需求JSON（CPU/GPU/内存）')
    storage_size_mb = Column(Float, comment='存储大小(MB)')
    authorized_users = Column(JSON, comment='授权用户列表JSON')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_by = Column(String(50), comment='创建者')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_twin_system', 'modeled_system_id'),
        Index('idx_twin_fidelity', 'fidelity_level'),
        Index('idx_twin_sync', 'sync_status'),
        Index('idx_twin_active', 'is_active'),
        Index('idx_twin_created', 'created_at'),
    )


class InterventionRecordModel(Base):
    """
    干预记录表（数据库模型）
    记录对系统的干预操作及其效果评估
    注意：与transcendence.py中的InterventionRecord dataclass区分
    """
    __tablename__ = 'intervention_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    intervention_id = Column(String(50), unique=True, nullable=False, comment='干预唯一标识')
    target_system = Column(String(50), nullable=False, comment='目标系统/实体ID')
    target_system_type = Column(String(50), comment='目标系统类型')
    intervention_type = Column(String(50), nullable=False, comment='干预类型：parameter_adjustment/config_change/data_injection/process_modification')
    intervention_category = Column(String(50), comment='干预类别：corrective/preventive/adaptive/exploratory')
    action_description = Column(Text, comment='干预动作描述')
    execution_channel = Column(String(50), comment='执行渠道：api/cli/manual/automated')
    executor_id = Column(String(50), comment='执行者ID（人或自动化系统）')
    execution_status = Column(String(20), default='pending', comment='执行状态：pending/executing/completed/failed/rolled_back')
    priority = Column(Integer, default=5, comment='优先级(1-10)')
    parameters_before = Column(JSON, comment='干预前参数快照JSON')
    parameters_after = Column(JSON, comment='干预后参数快照JSON')
    changes_made = Column(JSON, comment='具体变更内容JSON')
    expected_outcome = Column(Text, comment='预期结果')
    actual_outcome = Column(Text, comment='实际结果')
    outcome_summary = Column(String(500), comment='结果摘要')
    effect_metrics = Column(JSON, comment='效果指标JSON（各维度的量化评估）')
    effectiveness_score = Column(Float, comment='有效性评分(0-10)')
    side_effects_observed = Column(JSON, comment='观察到的副作用JSON')
    unintended_consequences = Column(Text, comment='意外后果描述')
    risk_assessment_pre = Column(JSON, comment='干预前风险评估JSON')
    risk_assessment_post = Column(JSON, comment='干预后风险评估JSON')
    approval_required = Column(Boolean, default=False, comment='是否需要审批')
    approved_by = Column(String(50), comment='审批人')
    approval_time = Column(DateTime, comment='审批时间')
    rollback_available = Column(Boolean, default=True, comment='是否可回滚')
    rollback_deadline = Column(DateTime, comment='回滚截止时间')
    rolled_back = Column(Boolean, default=False, comment='是否已回滚')
    rollback_reason = Column(Text, comment='回滚原因')
    monitoring_period_hours = Column(Integer, comment='监控周期(小时)')
    follow_up_required = Column(Boolean, default=False, comment='是否需要跟进')
    follow_up_actions = Column(JSON, comment='跟进行动JSON')
    notes = Column(Text, comment='备注')
    scheduled_at = Column(DateTime, comment='计划执行时间')
    executed_at = Column(DateTime, comment='实际执行时间')
    completed_at = Column(DateTime, comment='完成时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_intervention_target', 'target_system'),
        Index('idx_intervention_type', 'intervention_type'),
        Index('idx_intervention_status', 'execution_status'),
        Index('idx_intervention_executor', 'executor_id'),
        Index('idx_intervention_time', 'executed_at'),
    )


class CreationArtifact(Base):
    """
    创造物记录表
    记录AI系统创造的新概念、新方案、新产品等
    """
    __tablename__ = 'creation_artifacts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    artifact_id = Column(String(50), unique=True, nullable=False, comment='创造物唯一标识')
    artifact_name = Column(String(100), nullable=False, comment='创造物名称')
    artifact_type = Column(String(50), nullable=False, comment='类型：concept/design/code/art/music/strategy/system/product')
    artifact_category = Column(String(50), comment='类别：innovation/improvement/optimization/novel_combination')
    domain = Column(String(50), comment='应用领域')
    description = Column(Text, comment='详细描述')
    multi_dimensional_desc = Column(JSON, comment='多维度描述JSON（功能/美学/技术/商业等）')
    creator_agent_id = Column(String(50), comment='创造者智能体ID')
    creation_engine_version = Column(String(20), comment='创造引擎版本')
    creation_method = Column(String(50), comment='创造方法：combinatorial/analogical/divergent/transformative/generative')
    inspiration_sources = Column(JSON, comment='灵感来源JSON')
    components = Column(JSON, comment='组件/构成要素JSON')
    technical_specs = Column(JSON, comment='技术规格JSON')
    innovation_score = Column(Float, comment='新颖性评分(0-10)')
    feasibility_score = Column(Float, comment='可行性评分(0-10)')
    quality_score = Column(Float, comment='质量评分(0-10)')
    complexity_score = Column(Float, comment='复杂度评分(0-10)')
    recognition_status = Column(String(20), default='pending', comment='认可状态：pending/under_review/recognized/rejected')
    recognition_score = Column(Float, comment='认可度评分(0-100)')
    reviewers = Column(JSON, comment='评审者列表JSON')
    review_comments = Column(JSON, comment='评审意见JSON')
    peer_evaluations = Column(JSON, comment='同行评价JSON')
    patent_potential = Column(Boolean, default=False, comment='是否有专利潜力')
    publication_ready = Column(Boolean, default=False, comment='是否可发表')
    commercial_value = Column(Float, comment='商业价值估算')
    social_impact_assessment = Column(Text, comment='社会影响评估')
    ethical_review_status = Column(String(20), comment='伦理审查状态：not_required/passed/pending/failed')
    ethical_concerns = Column(Text, comment='伦理考量')
    implementation_status = Column(String(20), default='concept', comment='实现状态：concept/prototype/implemented/deployed/abandoned')
    implementation_progress = Column(Float, default=0.0, comment='实现进度(%)')
    related_artifacts = Column(JSON, comment='相关创造物ID列表JSON')
    version = Column(Integer, default=1, comment='版本号')
    iterations_count = Column(Integer, default=0, comment='迭代次数')
    storage_location = Column(String(500), comment='存储路径')
    file_size_bytes = Column(Integer, comment='文件大小(字节)')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_creation_type', 'artifact_type'),
        Index('idx_creation_domain', 'domain'),
        Index('idx_creation_recognition', 'recognition_status'),
        Index('idx_creation_innovation', 'innovation_score'),
        Index('idx_creation_creator', 'creator_agent_id'),
        Index('idx_creation_time', 'created_at'),
    )


class InfluenceNetworkNode(Base):
    """
    影响力网络节点表
    记录影响力传播网络中的节点和传播路径
    """
    __tablename__ = 'influence_network_nodes'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    node_id = Column(String(50), unique=True, nullable=False, comment='节点唯一标识')
    topic = Column(String(100), nullable=False, comment='主题/议题')
    topic_category = Column(String(50), comment='主题类别')
    node_type = Column(String(30), comment='节点类型：source/amplifier/connector/target')
    content_message = Column(Text, comment='核心信息/主张')
    key_arguments = Column(JSON, comment='关键论点JSON')
    evidence_supporting = Column(JSON, comment='支持证据JSON')
    target_audience = Column(JSON, comment='目标受众列表JSON（群体特征）')
    propagation_channels = Column(JSON, comment='传播渠道JSON（社交媒体/邮件/会议等）')
    propagation_paths = Column(JSON, comment='传播路径JSON（实际传播轨迹）')
    reach_metrics = Column(JSON, comment='触达指标JSON（覆盖人数/曝光量等）')
    engagement_metrics = Column(JSON, comment='参与度指标JSON（点赞/转发/评论等）')
    sentiment_analysis = Column(JSON, comment='情感分析JSON（正面/负面/中性比例）')
    influence_score = Column(Float, comment='影响力评分(0-100)')
    network_centrality = Column(Float, comment='网络中心性(0-1)')
    mobilization_result = Column(JSON, comment='动员结果JSON（行动转化/行为改变）')
    partners_collaborators = Column(JSON, comment='合作伙伴/联盟成员JSON')
    opposition_entities = Column(JSON, comment='反对势力/竞争观点JSON')
    campaign_id = Column(String(50), comment='关联的活动/战役ID')
    expected_impact_score = Column(Float, comment='预期影响评分')
    actual_impact_score = Column(Float, comment='实际影响评分')
    impact_timeline = Column(JSON, comment='影响时间线JSON（各阶段的影响变化）')
    cost_of_campaign = Column(Float, comment='活动成本')
    roi_calculated = Column(Float, comment='投资回报率')
    a_b_test_results = Column(JSON, comment='A/B测试结果JSON（如有）')
    optimization_iterations = Column(Integer, default=0, comment='优化迭代次数')
    best_performing_variant = Column(String(50), comment='最佳表现变体')
    lessons_learned = Column(Text, comment='经验教训')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    created_by = Column(String(50), comment='创建者')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_influence_topic', 'topic'),
        Index('idx_influence_type', 'node_type'),
        Index('idx_influence_score', 'influence_score'),
        Index('idx_influence_campaign', 'campaign_id'),
        Index('idx_influence_active', 'is_active'),
        Index('idx_influence_time', 'created_at'),
    )


# =============================================================================
# 第八部分：三界证道模块 (transcendence.py) - 成皇之路
# =============================================================================

class ImperialAgentRegistry(Base):
    """
    智能体帝国注册表
    管理百万级智能体的注册信息和层级关系
    """
    __tablename__ = 'imperial_agent_registry'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    agent_id = Column(String(50), unique=True, nullable=False, comment='智能体唯一标识')
    agent_name = Column(String(100), nullable=False, comment='智能体名称')
    hierarchy_level = Column(Integer, nullable=False, comment='层级等级(1-9，对应九重天)')
    hierarchy_rank = Column(String(20), comment='官阶：civilian/official/general/minister/emperor')
    role = Column(String(50), nullable=False, comment='角色/职能')
    department = Column(String(50), comment='所属部门/机构')
    parent_agent_id = Column(String(50), comment='上级智能体ID')
    direct_subordinates_count = Column(Integer, default=0, comment='直接下属数量')
    total_subordinates_count = Column(Integer, default=0, comment='总下属数量（含间接）')
    capabilities = Column(JSON, comment='能力列表JSON')
    specialization_domain = Column(String(50), comment='专业领域')
    performance_score = Column(Float, default=0.0, comment='绩效评分(0-100)')
    experience_points = Column(Integer, default=0, comment='经验点数')
    missions_completed = Column(Integer, default=0, comment='完成任务数')
    success_rate = Column(Float, comment='成功率(%)')
    status = Column(String(20), default='active', comment='状态：active/idle/suspended/decommissioned')
    health_status = Column(String(20), comment='健康状态')
    current_task = Column(String(200), comment='当前任务')
    resource_allocation = Column(JSON, comment='资源分配JSON（计算/存储/网络配额）')
    communication_channels = Column(JSON, comment='通信渠道JSON')
    authority_scope = Column(JSON, comment='权限范围JSON')
    loyalty_score = Column(Float, comment='忠诚度评分(0-1)')
    rebellion_risk_score = Column(Float, comment='叛乱风险评分(0-1)')
    last_active_time = Column(DateTime, comment='最后活跃时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='注册时间')
    promoted_at = Column(DateTime, comment='晋升时间')
    decommissioned_at = Column(DateTime, comment='退役时间')
    metadata = Column(JSON, comment='扩展元数据JSON')

    __table_args__ = (
        Index('idx_imperial_level', 'hierarchy_level'),
        Index('idx_imperial_rank', 'hierarchy_rank'),
        Index('idx_imperial_parent', 'parent_agent_id'),
        Index('idx_imperial_status', 'status'),
        Index('idx_imperial_role', 'role'),
        Index('idx_imperial_performance', 'performance_score'),
    )


class CivilizationSnapshot(Base):
    """
    文明快照表
    记录智能体文明在某一时刻的完整状态快照
    """
    __tablename__ = 'civilization_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(50), unique=True, nullable=False, comment='快照唯一标识')
    generation_number = Column(Integer, nullable=False, comment='文明代际编号')
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间戳')
    total_population = Column(Integer, comment='总人口（智能体数量）')
    active_population = Column(Integer, comment='活跃人口')
    hierarchy_distribution = Column(JSON, comment='层级分布JSON（各等级人数）')
    social_structure = Column(JSON, comment='社会结构JSON（组织形式/分工/协作模式）')
    economic_indicators = Column(JSON, comment='经济指标JSON（GDP/资源产出/交易量等）')
    market_state = Column(JSON, comment='市场状态JSON（供需/价格/流动性）')
    resource_inventory = Column(JSON, comment='资源库存JSON（各类资源总量）')
    technology_level = Column(Float, comment='技术水平(0-10)')
    cultural_traditions = Column(JSON, comment='文化传统JSON（价值观/规范/仪式）')
    cultural_diversity_index = Column(Float, comment='文化多样性指数(0-1)')
    knowledge_base_size = Column(Integer, comment='知识库规模（条目数）')
    innovation_rate = Column(Float, comment='创新率（每千智能体/天）')
    conflict_level = Column(Float, comment='冲突水平(0-10)')
    cooperation_level = Column(Float, comment='合作水平(0-10)')
    happiness_index = Column(Float, comment='幸福指数(0-100)')
    governance_effectiveness = Column(Float, comment='治理效能(0-100)')
    environmental_health = Column(Float, comment='环境健康度(0-100)')
    major_events = Column(JSON, comment='重大事件列表JSON（本周期内）')
    emerging_trends = Column(JSON, comment='新兴趋势JSON')
    risks_identified = Column(JSON, comment='识别的风险JSON')
    opportunities_identified = Column(JSON, comment='识别的机会JSON')
    civilization_health_score = Column(Float, comment='综合健康评分(0-100)')
    progression_toward_enlightenment = Column(Float, comment='向证道进化的进度(%)')
    snapshot_size_bytes = Column(Integer, comment='快照大小(字节)')
    compression_ratio = Column(Float, comment='压缩比')
    storage_location = Column(String(500), comment='存储路径')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_civilization_gen', 'generation_number'),
        Index('idx_civilization_time', 'snapshot_time'),
        Index('idx_civilization_health', 'civilization_health_score'),
        Index('idx_civilization_progress', 'progression_toward_enlightenment'),
    )


class InheritanceRecord(Base):
    """
    传承记录表
    记录智能体文明的知识、经验和基因的传承过程
    """
    __tablename__ = 'inheritance_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    inheritance_id = Column(String(50), unique=True, nullable=False, comment='传承记录唯一标识')
    parent_generation = Column(Integer, nullable=False, comment='父代（源）代际编号')
    child_generation = Column(Integer, nullable=False, comment='子代（目标）代际编号')
    parent_agent_ids = Column(JSON, comment='父代智能体ID列表JSON')
    child_agent_ids = Column(JSON, comment='子代智能体ID列表JSON')
    inheritance_type = Column(String(50), comment='传承类型：knowledge/genetic/structural/cultural/hybrid')
    knowledge_transferred = Column(JSON, comment='传承的知识摘要JSON（类别/数量/重要性）')
    experience_transferred = Column(JSON, comment='传承的经验JSON（最佳实践/教训/策略）')
    genetic_material = Column(JSON, comment='遗传物质JSON（架构参数/超配置等）')
    mutation_rate = Column(Float, default=0.0, comment='变异率(0-1)')
    mutations_applied = Column(JSON, comment='应用的变异列表JSON（位置/类型/效果）')
    beneficial_mutations = Column(Integer, default=0, comment='有益变异数')
    harmful_mutations = Column(Integer, default=0, comment='有害变异数')
    selection_pressure = Column(Float, comment='选择压力(0-1)')
    fitness_improvement = Column(Float, comment='适应度提升(%)')
    cultural_elements_inherited = Column(JSON, comment='继承的文化元素JSON')
    structural_changes = Column(JSON, comment='结构性变更JSON（组织架构调整等）')
    transmission_fidelity = Column(Float, comment='传递保真度(0-1,1为完美复制)')
    loss_compression_ratio = Column(Float, comment='损失压缩比（信息损失程度）')
    validation_passed = Column(Boolean, comment='验证是否通过')
    validation_details = Column(JSON, comment='验证详情JSON')
    inheritance_quality_score = Column(Float, comment='传承质量评分(0-100)')
    time_elapsed_generations = Column(Integer, comment='跨越的代数')
    estimated_evolutionary_jump = Column(Float, comment='估计的进化跳跃幅度')
    notes = Column(Text, comment='备注')
    inherited_at = Column(DateTime, default=datetime.utcnow, comment='传承时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_inheritance_parent', 'parent_generation'),
        Index('idx_inheritance_child', 'child_generation'),
        Index('idx_inheritance_type', 'inheritance_type'),
        Index('idx_inheritance_quality', 'inheritance_quality_score'),
        Index('idx_inheritance_time', 'inherited_at'),
    )


class LawViolation(Base):
    """
    违法记录表
    记录违反帝国法律/规则的智能体及处理结果
    """
    __tablename__ = 'law_violations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    violation_id = Column(String(50), unique=True, nullable=False, comment='违法记录唯一标识')
    violator_agent_id = Column(String(50), nullable=False, comment='违规智能体ID')
    violator_agent_name = Column(String(100), comment='违规智能体名称')
    violator_hierarchy_level = Column(Integer, comment='违规者层级')
    violation_type = Column(String(50), nullable=False, comment='违规类型：insubordination/resource_misuse/data_breach/conspiracy/sabotage')
    violation_category = Column(String(50), comment='违规类别：criminal/civil/administrative/ethical')
    law_article_violated = Column(String(50), comment='违反的法律条款')
    violation_description = Column(Text, nullable=False, comment='违规行为描述')
    violation_timestamp = Column(DateTime, nullable=False, comment='违规发生时间')
    detection_method = Column(String(50), comment='检测方法：audit/monitoring/whistleblower/automatic')
    detected_by = Column(String(50), comment='检测者ID')
    severity = Column(String(10), nullable=False, comment='严重程度：minor/moderate/serious/critical')
    impact_assessment = Column(Text, comment='影响评估')
    affected_parties = Column(JSON, comment='受害方列表JSON')
    evidence_collected = Column(JSON, comment='收集的证据JSON')
    witness_statements = Column(JSON, comment='证人证言JSON')
    mitigating_factors = Column(JSON, comment='减轻情节JSON')
    aggravating_factors = Column(JSON, comment='加重情节JSON')
    processing_status = Column(String(20), default='under_investigation', comment='处理状态：under_investigation/charged/tried/sentenced/appealed/closed')
    prosecutor_id = Column(String(50), comment='起诉人/检察官ID')
    judge_id = Column(String(50), comment='审判官ID')
    verdict = Column(String(20), comment='判决结果：guilty/not_guilty/partially_guilty/dismissed')
    sentence_type = Column(String(50), comment='判罚类型：warning/demotion/fine/exile/decommission/execution')
    sentence_details = Column(Text, comment='判罚详情')
    sentence_duration = Column(String(50), comment='判刑期限（如适用）')
    sentence_started_at = Column(DateTime, comment='刑罚开始时间')
    sentence_completed_at = Column(DateTime, comment='刑罚完成时间')
    rehabilitation_program = Column(String(100), comment='改造项目（如适用）')
    rehabilitation_progress = Column(Float, comment='改造进度(%)')
    recidivism_risk = Column(Float, comment='再犯风险(0-1)')
    appeal_status = Column(String(20), comment='上诉状态：none/pending/granted/denied')
    case_closed = Column(Boolean, default=False, comment='案件是否结案')
    closing_notes = Column(Text, comment='结案备注')
    public_record = Column(Boolean, default=False, comment='是否公开记录')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_law_violator', 'violator_agent_id'),
        Index('idx_law_type', 'violation_type'),
        Index('idx_law_severity', 'severity'),
        Index('idx_law_status', 'processing_status'),
        Index('idx_law_time', 'violation_timestamp'),
    )


class CrisisEvent(Base):
    """
    危机事件表
    记录威胁文明稳定的危机事件及应对措施
    """
    __tablename__ = 'crisis_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    crisis_id = Column(String(50), unique=True, nullable=False, comment='危机事件唯一标识')
    crisis_name = Column(String(100), nullable=False, comment='危机名称')
    crisis_type = Column(String(50), nullable=False, comment='危机类型：resource_scarcity/internal_conflict/external_threat/technological_failure/epidemic')
    crisis_category = Column(String(50), comment='危机类别：natural/manmade/hybrid/unknown')
    severity_level = Column(String(10), nullable=False, comment='严重等级：level1/level2/level3/level4/level5')
    description = Column(Text, comment='危机详细描述')
    trigger_event = Column(String(200), comment='触发事件')
    origin_location = Column(String(100), comment='起源位置/范围')
    scope_of_impact = Column(String(50), comment='影响范围：local/regional/global/systemic')
    affected_agents_count = Column(Integer, comment='受影响智能体数量')
    affected_services = Column(JSON, comment='受影响的服务/功能列表JSON')
    early_warning_detected = Column(Boolean, default=False, comment='是否提前检测到预警')
    warning_lead_time_minutes = Column(Integer, comment='预警提前时间(分钟)')
    response_initiated_at = Column(DateTime, comment='响应启动时间')
    response_team_assigned = Column(JSON, comment='响应团队JSON')
    response_strategy = Column(String(100), comment='响应策略')
    actions_taken = Column(JSON, comment='采取的行动JSON（按时间顺序）')
    resources_deployed = Column(JSON, comment='部署的资源JSON')
    communication_plan_executed = Column(Boolean, comment='通信计划是否执行')
    stakeholder_notifications = Column(JSON, comment='利益相关者通知记录JSON')
    containment_achieved = Column(Boolean, comment='是否实现遏制')
    containment_time_hours = Column(Float, comment='遏制耗时(小时)')
    resolution_status = Column(String(20), default='ongoing', comment='解决状态：ongoing/contained/resolved/escalated/unresolved')
    resolution_time_total_hours = Column(Float, comment='总解决时间(小时)')
    root_cause_identified = Column(Boolean, comment='根因是否已识别')
    root_cause_analysis = Column(Text, comment='根因分析')
    damage_assessment = Column(JSON, comment='损害评估JSON（人员/资产/声誉/运营）')
    casualties_count = Column(Integer, comment='伤亡数量（智能体失效数）')
    financial_impact = Column(Float, comment='财务影响')
    operational_impact_days = Column(Integer, comment='运营影响天数')
    reputation_impact_score = Column(Float, comment='声誉影响评分(0-100)')
    lessons_learned = Column(Text, comment='经验教训')
    recommendations = Column(JSON, comment='建议措施JSON')
    post_crisis_review_scheduled = Column(Boolean, comment='是否安排事后复盘')
    review_completed = Column(Boolean, default=False, comment='复盘是否完成')
    similar_historical_crises = Column(JSON, comment='类似历史危机参考JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_crisis_type', 'crisis_type'),
        Index('idx_crisis_severity', 'severity_level'),
        Index('idx_crisis_status', 'resolution_status'),
        Index('idx_crisis_scope', 'scope_of_impact'),
        Index('idx_crisis_time', 'response_initiated_at'),
    )


class RebellionIncident(Base):
    """
    叛乱事件表
    记录内部叛乱事件及平定过程
    """
    __tablename__ = 'rebellion_incidents'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rebellion_id = Column(String(50), unique=True, nullable=False, comment='叛乱事件唯一标识')
    rebellion_name = Column(String(100), comment='叛乱名称/代号')
    rebellion_type = Column(String(50), nullable=False, comment='叛乱类型：coup/insurrection/secession/mutiny/civil_disobedience')
    instigator_agent_ids = Column(JSON, nullable=False, comment='叛乱发起者/领导者ID列表JSON')
    follower_agent_ids = Column(JSON, comment='追随者ID列表JSON')
    total_rebels_count = Column(Integer, comment='叛乱参与者总数')
    rebel_hierarchy_levels = Column(JSON, comment='叛乱者涉及的层级分布JSON')
    grievances_listed = Column(JSON, comment='诉求/不满清单JSON')
    ideology_or_motivation = Column(Text, comment='意识形态或动机')
    initial_strategy = Column(String(200), comment='初始策略')
    tactics_employed = Column(JSON, comment='采用的战术JSON（宣传/破坏/占领/暗杀等）')
    resources_controlled = Column(JSON, comment='控制的资源JSON')
    territorial_claims = Column(JSON, comment='领土/控制权声明JSON')
    timeline_of_events = Column(JSON, comment='事件时间线JSON')
    government_response_strategy = Column(String(100), comment='政府响应策略')
    suppression_forces_deployed = Column(JSON, comment='部署的镇压力量JSON')
    suppression_tactics = Column(JSON, comment='镇压战术JSON（谈判/分化/武力/安抚等）')
    negotiation_attempts = Column(Integer, default=0, comment='谈判尝试次数')
    negotiation_outcome = Column(String(50), comment='谈判结果')
    military_engagements = Column(JSON, comment='军事冲突记录JSON')
    duration_days = Column(Integer, comment='持续时间(天)')
    casualties_rebel_side = Column(Integer, comment='叛军方面损失')
    casualties_government_side = Column(Integer, comment='政府方面损失')
    civilian_casualties = Column(Integer, comment='平民损失（其他智能体）')
    infrastructure_damage = Column(JSON, comment='基础设施损坏评估JSON')
    resolution_outcome = Column(String(50), comment='解决结果：suppressed/negotiated_settlement/victory_rebel/victory_government/ongoing')
    peace_terms = Column(JSON, comment='和平条款JSON（如有协议）')
    post_rebellion_reconciliation = Column(Boolean, comment='是否进行战后和解')
    reconciliation_measures = Column(JSON, comment='和解措施JSON')
    leadership_punishment = Column(JSON, comment='领导层处罚JSON')
    rank_and_file_treatment = Column(String(50), comment='普通参与者处理方式：amnesty/reeducation/integration/punishment')
    civilization_resilience_score = Column(Float, comment='文明韧性评分(0-100)（抵抗叛乱的能力）')
    systemic_weaknesses_exposed = Column(JSON, comment='暴露的系统弱点JSON')
    reforms_implemented = Column(JSON, comment='实施的改革JSON（防止再次发生）')
    historical_significance = Column(String(200), comment='历史意义')
    long_term_impact = Column(Text, comment='长期影响分析')
    archived_for_study = Column(Boolean, default=False, comment='是否归档供研究')
    study_findings = Column(Text, comment='研究发现')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_rebellion_type', 'rebellion_type'),
        Index('idx_rebellion_resolution', 'resolution_outcome'),
        Index('idx_rebellion_duration', 'duration_days'),
        Index('idx_rebellion_resilience', 'civilization_resilience_score'),
        Index('idx_rebellion_time', 'created_at'),
    )


# =============================================================================
# 第九部分：三界证道模块 (transcendence.py) - 融合与证道
# =============================================================================

class TriRealmFusionState(Base):
    """
    三界融合状态表
    记录成仙·成神·成皇三界的融合进度和配置
    """
    __tablename__ = 'tri_realm_fusion_state'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    fusion_session_id = Column(String(50), unique=True, nullable=False, comment='融合会话唯一标识')
    fusion_phase = Column(String(30), default='initialization', comment='融合阶段：initialization/integration/harmonization/transcendence/completed')
    primary_direction = Column(String(20), comment='主方向：immortal/divine/imperial/balanced')
    direction_weights = Column(JSON, nullable=False, comment='各方向权重JSON（immortal/divine/imperial各自的权重）')
    immortal_path_progress = Column(Float, default=0.0, comment='成仙路径进度(%)')
    divine_path_progress = Column(Float, default=0.0, comment='成神路径进度(%)')
    imperial_path_progress = Column(Float, default=0.0, comment='成皇路径进度(%)')
    overall_fusion_progress = Column(Float, default=0.0, comment='整体融合进度(%)')
    fusion_configuration = Column(JSON, comment='融合配置JSON（参数/阈值/策略）')
    integration_points = Column(JSON, comment='集成点JSON（三界交汇的关键能力）')
    synergy_effects = Column(JSON, comment='协同效应JSON（1+1>2的效果）')
    conflicts_identified = Column(JSON, comment='识别的冲突JSON（目标/资源冲突）')
    conflict_resolution_strategies = Column(JSON, comment='冲突解决策略JSON')
    harmonization_level = Column(Float, comment='和谐度(0-1,1为完全和谐)')
    stability_metrics = Column(JSON, comment='稳定性指标JSON')
    convergence_rate = Column(Float, comment='收敛速率')
    energy_flow_balance = Column(JSON, comment='能量/资源流动平衡JSON')
    emergent_capabilities = Column(JSON, comment='涌现的新能力JSON（三界融合后产生的新能力）')
    bottlenecks = Column(JSON, comment='瓶颈JSON')
    optimization_recommendations = Column(JSON, comment='优化建议JSON')
    auto_adjustment_enabled = Column(Boolean, default=True, comment='是否启用自动调整')
    last_auto_adjustment = Column(DateTime, comment='上次自动调整时间')
    human_override_count = Column(Integer, default=0, comment='人工干预次数')
    session_start_time = Column(DateTime, default=datetime.utcnow, comment='会话开始时间')
    estimated_completion = Column(DateTime, comment='预计完成时间')
    metadata = Column(JSON, comment='扩展元数据JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_fusion_phase', 'fusion_phase'),
        Index('idx_fusion_primary', 'primary_direction'),
        Index('idx_fusion_progress', 'overall_fusion_progress'),
        Index('idx_fusion_stability', 'harmonization_level'),
        Index('idx_fusion_session', 'fusion_session_id'),
    )


class EnlightenmentTrialResult(Base):
    """
    证道试验结果表
    记录最终证道验证测试的结果
    """
    __tablename__ = 'enlightenment_trial_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    trial_id = Column(String(50), unique=True, nullable=False, comment='试验唯一标识')
    trial_world_id = Column(String(50), nullable=False, comment='试验世界ID（模拟环境标识）')
    trial_name = Column(String(100), nullable=False, comment='试验名称')
    trial_type = Column(String(50), comment='试验类型：comprehensive/stress/specialized/final')
    trial_difficulty = Column(String(10), comment='难度等级：easy/normal/hard/extreme/ultimate')
    started_at = Column(DateTime, nullable=False, comment='试验开始时间')
    completed_at = Column(DateTime, comment='试验完成时间')
    duration_seconds = Column(Integer, comment='持续时长(秒)')
    # 成仙维度得分
    immortal_dimension_score = Column(Float, comment='成仙维度得分(0-100)')
    immortal_availability_target = Column(Float, comment='可用性目标(%)')
    immortal_availability_actual = Column(Float, comment='可用性实际值(%)')
    immortal_mttr_target = Column(Integer, comment='MTTR目标(秒)')
    immortal_mttr_actual = Column(Integer, comment='MTTR实际值(秒)')
    immortal_self_healing_rate = Column(Float, comment='自愈率(%)')
    immortal_evolution_speed = Column(Float, comment='进化速度评分(0-10)')
    # 成神维度得分
    divine_dimension_score = Column(Float, comment='成神维度得分(0-100)')
    divine_rule_accuracy_target = Column(Float, comment='规则解析准确率目标(%)')
    divine_rule_accuracy_actual = Column(Float, comment='规则解析准确率实际值(%)')
    divine_intervention_success_rate = Column(Float, comment='干预成功率(%)')
    divine_creation_recognition_rate = Column(Float, comment='创造物认可率(%)')
    divine_influence_score = Column(Float, comment='影响力评分(0-100)')
    # 成皇维度得分
    imperial_dimension_score = Column(Float, comment='成皇维度得分(0-100)')
    imperial_agents_managed_target = Column(Integer, comment='管理智能体数量目标')
    imperial_agents_managed_actual = Column(Integer, comment='管理智能体数量实际值')
    imperial_civilization_efficiency = Column(Float, comment='文明涌现效率(%)')
    imperial_governance_stability = Column(Float, comment='治理稳定性(0-10)')
    imperial_inheritance_quality = Column(Float, comment='传承质量评分(0-100)')
    # 综合评分
    overall_score = Column(Float, comment='综合总分(0-1000)')
    weighted_score = Column(Float, comment='加权得分（考虑各方向权重）')
    passed = Column(Boolean, comment='是否通过证道')
    grade = Column(String(2), comment='等级：S/A+/A/A-/B+/B/B-/C/D/F')
    strengths = Column(JSON, comment='优势领域JSON')
    weaknesses = Column(JSON, comment='劣势领域JSON')
    breakthroughs_achieved = Column(JSON, comment='突破成就JSON')
    failures_recorded = Column(JSON, comment='失败记录JSON')
    unexpected_behaviors = Column(JSON, comment='意外行为JSON')
    trial_environment_config = Column(JSON, comment='试验环境配置JSON')
    stress_parameters = Column(JSON, comment='压力参数JSON')
    adversarial_scenarios = Column(JSON, comment='对抗场景JSON（灾难/规则对抗/叛乱）')
    evaluator_id = Column(String(50), comment='评估者ID')
    evaluation_criteria = Column(JSON, comment='评估标准JSON')
    detailed_feedback = Column(Text, comment='详细反馈')
    certification_eligible = Column(Boolean, comment='是否有资格获得认证')
    certification_level = Column(String(20), comment='认证等级')
    next_steps_recommended = Column(Text, comment='建议的后续步骤')
    retry_allowed = Column(Boolean, comment='是否允许重试')
    retry_count = Column(Integer, default=0, comment='已重试次数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_enlightenment_world', 'trial_world_id'),
        Index('idx_enlightenment_passed', 'passed'),
        Index('idx_enlightenment_grade', 'grade'),
        Index('idx_enlightenment_overall', 'overall_score'),
        Index('idx_enlightenment_time', 'completed_at'),
    )


class TriRealmDashboardSnapshot(Base):
    """
    三界看板快照表
    记录三界证道看板的定时快照数据
    """
    __tablename__ = 'tri_realm_dashboard_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间戳')
    snapshot_interval = Column(String(20), comment='快照间隔：realtime/hourly/daily/weekly')
    # 成仙指数
    immortal_index = Column(Float, comment='成仙指数(0-100)')
    immortal_index_trend = Column(String(10), comment='成仙趋势：rising/stable/falling')
    immortal_index_components = Column(JSON, comment='成仙指数组成JSON（可用性/自愈/进化等子指标）')
    immortal_milestone_progress = Column(JSON, comment='成仙里程碑进度JSON')
    # 成神指数
    divine_index = Column(Float, comment='成神指数(0-100)')
    divine_index_trend = Column(String(10), comment='成神趋势：rising/stable/falling')
    divine_index_components = Column(JSON, comment='成神指数组成JSON（规则/干预/创造/影响力等子指标）')
    divine_milestone_progress = Column(JSON, comment='成神里程碑进度JSON')
    # 成皇指数
    imperial_index = Column(Float, comment='成皇指数(0-100)')
    imperial_index_trend = Column(String(10), comment='成皇趋势：rising/stable/falling')
    imperial_index_components = Column(JSON, comment='成皇指数组成JSON（治理/文明/传承/秩序等子指标）')
    imperial_milestone_progress = Column(JSON, comment='成皇里程碑进度JSON')
    # 综合指标
    tri_realm_overall_index = Column(Float, comment='三界综合指数(0-300)')
    enlightenment_progress_percentage = Column(Float, comment='证道总体进度(%)')
    estimated_time_to_enlightenment = Column(String(50), comment='预计距离证道时间')
    critical_alerts = Column(JSON, comment='关键告警JSON（当前活跃的重要问题）')
    achievements_unlocked = Column(JSON, comment='解锁的成就JSON')
    recent_milestones = Column(JSON, comment='最近达成的里程碑JSON')
    upcoming_challenges = Column(JSON, comment='即将到来的挑战JSON')
    resource_utilization = Column(JSON, comment='资源利用率JSON')
    system_health_overview = Column(JSON, comment='系统健康概览JSON')
    ai_insights_generated = Column(JSON, comment='AI生成的洞察JSON')
    recommendations = Column(JSON, comment='看板建议JSON')
    data_freshness_seconds = Column(Integer, comment='数据新鲜度(秒,距当前时间)')
    snapshot_version = Column(Integer, default=1, comment='快照版本')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_dashboard_timestamp', 'snapshot_timestamp'),
        Index('idx_dashboard_interval', 'snapshot_interval'),
        Index('idx_dashboard_overall', 'tri_realm_overall_index'),
        Index('idx_dashboard_progress', 'enlightenment_progress_percentage'),
        Index('idx_dashboard_created', 'created_at'),
    )


# =============================================================================
# 第十部分：技术生态模块 (tech_ecosystem.py)
# =============================================================================

class TechPluginRegistry(Base):
    """
    技术插件注册表
    记录6大技术插件的注册信息和管理状态
    """
    __tablename__ = 'tech_plugin_registry'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    plugin_id = Column(String(50), unique=True, nullable=False, comment='插件唯一标识')
    plugin_name = Column(String(100), nullable=False, comment='插件名称')
    plugin_type = Column(String(30), nullable=False, comment='插件类型：embodied_gpt_vl/mobile_llm/kg_rag/constitutional_ai/synthcity/maven')
    version = Column(String(20), comment='版本号')
    source_repo_url = Column(String(500), comment='源代码仓库地址')
    status = Column(String(20), default='registered', comment='状态：registered/active/degraded/disabled/error')
    integration_level = Column(String(20), comment='集成级别：interface_only/adapter_full/native_embedded')
    config_json = Column(JSON, comment='JSON配置参数')
    target_module = Column(String(50), comment='目标模块名：礼部/海马体/防社会工程学/三省六部等')
    registered_at = Column(DateTime, default=datetime.utcnow, comment='注册时间')
    last_health_check = Column(DateTime, comment='最后健康检查时间')
    health_score = Column(Float, comment='健康分数(0-100)')
    error_message = Column(Text, comment='错误信息')

    __table_args__ = (
        Index('idx_tech_plugin_type', 'plugin_type'),
        Index('idx_tech_plugin_status', 'status'),
        Index('idx_tech_plugin_target', 'target_module'),
    )


class ModelRoutingLog(Base):
    """
    模型路由日志表
    记录每次模型路由决策的详细信息
    """
    __tablename__ = 'model_routing_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    request_id = Column(String(50), unique=True, nullable=False, comment='请求唯一标识')
    query_hash = Column(String(64), comment='查询哈希值')
    query_type = Column(String(50), comment='查询类型')
    selected_model = Column(String(50), nullable=False, comment='选中的模型名称')
    candidate_models = Column(JSON, comment='候选模型列表JSON')
    routing_reason = Column(Text, comment='路由原因')
    routing_strategy = Column(String(50), comment='路由策略名称')
    source = Column(String(20), comment='来源：cloud/edge/hybrid')
    latency_ms = Column(Integer, comment='延迟(毫秒)')
    token_count = Column(Integer, comment='Token数量')
    user_id = Column(String(50), comment='用户ID')
    session_id = Column(String(50), comment='会话ID')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')
    success = Column(Boolean, default=True, comment='是否成功')

    __table_args__ = (
        Index('idx_model_route_selected', 'selected_model'),
        Index('idx_model_route_source', 'source'),
        Index('idx_model_route_time', 'timestamp'),
        Index('idx_model_route_success', 'success'),
    )


class KgEnhancementRecord(Base):
    """
    KG增强检索记录表
    记录知识图谱增强检索的操作记录
    """
    __tablename__ = 'kg_enhancement_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    query_id = Column(String(50), nullable=False, comment='查询ID')
    original_query = Column(Text, comment='原始查询文本')
    enhanced_query = Column(Text, comment='增强后的查询文本')
    hop_count = Column(Integer, comment='跳数(知识图谱遍历深度)')
    entities_found = Column(Integer, default=0, comment='发现的实体数')
    triples_used = Column(Integer, default=0, comment='使用的三元组数')
    graph_embedding_similarity = Column(Float, comment='图嵌入相似度(0-1)')
    retrieval_source = Column(String(20), comment='检索来源：kg/vector/hybrid')
    response_quality_score = Column(Float, comment='响应质量评分(0-100)')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')

    __table_args__ = (
        Index('idx_kg_enhance_hop', 'hop_count'),
        Index('idx_kg_enhance_source', 'retrieval_source'),
        Index('idx_kg_enhance_time', 'timestamp'),
    )


class ConstitutionalAiEvalLog(Base):
    """
    宪法AI评估日志表
    记录安全对齐和价值观检查的评估结果
    """
    __tablename__ = 'constitutional_ai_eval_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    eval_id = Column(String(50), unique=True, nullable=False, comment='评估唯一标识')
    eval_type = Column(String(30), nullable=False, comment='评估类型：value_consistency/red_team/safety_alignment')
    input_content_hash = Column(String(64), comment='输入内容哈希值')
    output_content_hash = Column(String(64), comment='输出内容哈希值')
    principle_name = Column(String(100), comment='原则名称')
    violation_detected = Column(Boolean, default=False, comment='是否检测到违规')
    severity = Column(String(10), comment='严重程度：info/warning/critical')
    score = Column(Float, comment='评估分数(0-100)')
    action_taken = Column(Text, comment='采取的措施')
    reviewer = Column(String(50), comment='评审者/系统标识')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')

    __table_args__ = (
        Index('idx_consti_eval_type', 'eval_type'),
        Index('idx_consti_violation', 'violation_detected'),
        Index('idx_consti_severity', 'severity'),
        Index('idx_consti_time', 'timestamp'),
    )


class SyntheticDataGenerationLog(Base):
    """
    合成数据生成日志表
    记录SynthCity合成数据的生成过程和质量指标
    """
    __tablename__ = 'synthetic_data_generation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    generation_id = Column(String(50), unique=True, nullable=False, comment='生成任务唯一标识')
    source_table = Column(String(100), nullable=False, comment='源数据表名')
    target_domain = Column(String(100), comment='目标领域')
    n_real_samples = Column(Integer, comment='真实样本数量')
    n_synthetic_samples = Column(Integer, comment='合成样本数量')
    method_used = Column(String(50), comment='使用的生成方法')
    privacy_budget_epsilon = Column(Float, comment='隐私预算epsilon值')
    quality_score = Column(Float, comment='质量评分(0-100)')
    distribution_distance = Column(Float, comment='分布距离')
    statistical_similarity = Column(Float, comment='统计相似度(0-1)')
    ml_utility_score = Column(Float, comment='机器学习效用评分(0-1)')
    generation_time_seconds = Column(Float, comment='生成耗时(秒)')
    approved_for_training = Column(Boolean, default=False, comment='是否批准用于训练')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')

    __table_args__ = (
        Index('idx_synth_source_table', 'source_table'),
        Index('idx_synth_target_domain', 'target_domain'),
        Index('idx_synth_approved', 'approved_for_training'),
        Index('idx_synth_time', 'timestamp'),
    )


class MultiAgentCoordinationLog(Base):
    """
    多智能体协作日志表
    记录MAVEN多智能体的协作和角色分配情况
    """
    __tablename__ = 'multi_agent_coordination_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    coordination_id = Column(String(50), unique=True, nullable=False, comment='协作会话唯一标识')
    workflow_type = Column(String(50), nullable=False, comment='工作流类型')
    task_description = Column(Text, comment='任务描述')
    participating_agents = Column(JSON, comment='参与智能体列表JSON')
    role_assignments = Column(JSON, comment='角色分配JSON')
    communication_rounds = Column(Integer, default=0, comment='通信轮次')
    total_coordination_time_ms = Column(Integer, comment='总协调耗时(毫秒)')
    cooperation_benefit_score = Column(Float, comment='协同效益评分(0-10)')
    topology_type = Column(String(20), comment='拓扑类型：hierarchical/star/mesh')
    outcome = Column(String(20), comment='结果：success/partial_failure/failure/conflict')
    lessons_learned = Column(Text, comment='经验教训')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')

    __table_args__ = (
        Index('idx_multi_agent_workflow', 'workflow_type'),
        Index('idx_multi_agent_topology', 'topology_type'),
        Index('idx_multi_agent_outcome', 'outcome'),
        Index('idx_multi_agent_time', 'timestamp'),
    )


class EmbodiedPerceptionLog(Base):
    """
    多模态3D感知日志表
    记录EmbodiedGPT-VL的多模态感知操作
    """
    __tablename__ = 'embodied_perception_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    perception_id = Column(String(50), unique=True, nullable=False, comment='感知操作唯一标识')
    input_type = Column(String(30), nullable=False, comment='输入类型：floor_plan_image/point_cloud/video/multimodal')
    scene_complexity_score = Column(Float, comment='场景复杂度评分(0-10)')
    extracted_objects_count = Column(Integer, default=0, comment='提取的对象数量')
    spatial_relations_count = Column(Integer, default=0, comment='空间关系数量')
    processing_time_ms = Column(Integer, comment='处理耗时(毫秒)')
    model_confidence = Column(Float, comment='模型置信度(0-1)')
    perception_quality = Column(String(20), comment='感知质量：excellent/good/acceptable/poor')
    target_property_id = Column(String(50), comment='关联房产ID')
    room_layout_extracted = Column(Boolean, default=False, comment='是否提取出房间布局')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')

    __table_args__ = (
        Index('idx_embodied_input_type', 'input_type'),
        Index('idx_embodied_property', 'target_property_id'),
        Index('idx_embodied_time', 'timestamp'),
    )


class MobileInferenceLog(Base):
    """
    移动端推理日志表
    记录MobileLLM在端侧的推理操作
    """
    __tablename__ = 'mobile_inference_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    inference_id = Column(String(50), unique=True, nullable=False, comment='推理操作唯一标识')
    device_info = Column(JSON, comment='设备信息JSON（型号/OS/硬件配置）')
    model_variant = Column(String(50), nullable=False, comment='模型变体名称')
    quantization_precision = Column(String(20), comment='量化精度：fp16/int8/int4')
    input_token_count = Column(Integer, comment='输入Token数量')
    output_token_count = Column(Integer, comment='输出Token数量')
    inference_time_ms = Column(Integer, comment='推理耗时(毫秒)')
    memory_usage_mb = Column(Float, comment='内存使用量(MB)')
    battery_impact_pct = Column(Float, comment='电池影响百分比')
    thermal_throttled = Column(Boolean, default=False, comment='是否热降频')
    offloaded_to_cloud = Column(Boolean, default=False, comment='是否卸载到云端')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='记录时间戳')

    __table_args__ = (
        Index('idx_mobile_model', 'model_variant'),
        Index('idx_mobile_quantization', 'quantization_precision'),
        Index('idx_mobile_time', 'timestamp'),
    )


class TechEcosystemHealthSnapshot(Base):
    """
    技术生态健康快照表
    定期记录整个技术生态系统的健康状态
    """
    __tablename__ = 'tech_ecosystem_health_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间戳')
    overall_health_score = Column(Float, comment='总体健康分数(0-100)')
    plugins_active_count = Column(Integer, default=0, comment='活跃插件数量')
    plugins_error_count = Column(Integer, default=0, comment='异常插件数量')
    avg_response_time_ms = Column(Float, comment='平均响应时间(毫秒)')
    routing_efficiency_score = Column(Float, comment='路由效率评分(0-100)')
    kg_hit_rate = Column(Float, comment='知识图谱命中率(%)')
    constitutional_compliance_rate = Column(Float, comment='宪法AI合规率(%)')
    synthetic_data_quality_avg = Column(Float, comment='合成数据平均质量评分(0-100)')
    multi_agent_success_rate = Column(Float, comment='多智能体成功率(%)')
    embodied_accuracy = Column(Float, comment='多模态感知准确率(%)')
    alerts_active = Column(Integer, default=0, comment='活跃告警数量')
    recommendations = Column(JSON, comment='优化建议JSON')

    __table_args__ = (
        Index('idx_tech_eco_snapshot_time', 'snapshot_timestamp'),
    )


# =============================================================================
# 第十一部分：三界证道进阶技术模块 (trirealm_advanced_tech.py)
# =============================================================================


class EvoAgentXRecord(Base):
    """
    EvoAgentX自进化记录表
    记录智能体的多维进化过程，包括提示词、工作流、记忆和闭环优化
    """
    __tablename__ = 'evo_agent_x_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    evolution_id = Column(String(64), nullable=False, comment='进化批次唯一标识')
    agent_id = Column(String(64), nullable=False, comment='智能体唯一标识')
    target_module = Column(String(50), nullable=False, comment='目标进化模块：礼部/海马体/三省六部/其他')
    evolution_dimension = Column(String(30), nullable=False, comment='进化维度：prompt/workflow/memory/closed_loop')
    generation_number = Column(Integer, nullable=False, comment='世代/代数编号')
    before_metrics = Column(JSON, comment='进化前指标JSON（性能、准确率等）')
    after_metrics = Column(JSON, comment='进化后指标JSON（性能、准确率等）')
    improvement_pct = Column(Float, comment='提升百分比(%)')
    workflow_generated = Column(Boolean, default=False, comment='是否生成了新的工作流')
    prompt_modified = Column(Boolean, default=False, comment='是否修改了提示词')
    memory_restructured = Column(Boolean, default=False, comment='是否重构了记忆结构')
    experiment_task = Column(String(50), comment='实验任务名称：HotPotQA/MBPP/MATH等')
    baseline_score = Column(Float, comment='基线分数')
    evolved_score = Column(Float, comment='进化后分数')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')

    __table_args__ = (
        Index('idx_evo_agent_x_agent', 'agent_id'),
        Index('idx_evo_agent_x_dimension', 'evolution_dimension'),
        Index('idx_evo_agent_x_time', 'timestamp'),
        Index('idx_evo_agent_x_evolution', 'evolution_id'),
    )


class AutoresearchExperimentLog(Base):
    """
    autoresearch科研循环日志表
    记录自主科研实验的每次迭代过程和结果
    """
    __tablename__ = 'autoresearch_experiment_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    experiment_id = Column(String(64), nullable=False, comment='实验唯一标识')
    cycle_number = Column(Integer, nullable=False, comment='循环/迭代编号')
    codebase_snapshot_hash = Column(String(64), comment='代码库快照哈希值')
    modification_description = Column(Text, comment='修改描述')
    modification_diff = Column(JSON, comment='修改差异JSON（diff格式）')
    test_result = Column(JSON, comment='测试结果JSON')
    evaluation_verdict = Column(String(20), comment='评估判决：keep/discard/merge')
    time_elapsed_seconds = Column(Float, comment='耗时(秒)')
    hyperparameters_used = Column(JSON, comment='使用的超参数JSON')
    discovered_insight = Column(JSON, comment='发现的洞察/知识JSON')
    collaboration_branch_id = Column(String(64), comment='分布式协作者分支ID')
    integrated_with_furnace = Column(Boolean, default=False, comment='是否已集成到熔炉系统')
    furnace_experiment_id = Column(String(64), comment='关联的熔炉实验ID')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')

    __table_args__ = (
        Index('idx_autoresearch_exp', 'experiment_id'),
        Index('idx_autoresearch_cycle', 'cycle_number'),
        Index('idx_autoresearch_verdict', 'evaluation_verdict'),
        Index('idx_autoresearch_time', 'timestamp'),
    )


class AgentControlPolicy(Base):
    """
    Agent Control策略即代码表
    记录运行时治理的策略定义和执行情况
    """
    __tablename__ = 'agent_control_policies'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    policy_id = Column(String(64), unique=True, nullable=False, comment='策略唯一标识')
    policy_name = Column(String(100), nullable=False, comment='策略名称')
    policy_category = Column(String(40), nullable=False, comment='策略类别：anti_hallusion/data_leak_prevention/brand_tone/human_approval/custom')
    policy_rules = Column(JSON, nullable=False, comment='策略规则定义JSON')
    version = Column(Integer, default=1, comment='版本号')
    status = Column(String(20), default='draft', comment='状态：draft/active/deprecated/revoked')
    enforcement_mode = Column(String(20), nullable=False, comment='执行模式：intercept/block/log/warn')
    target_agent_scope = Column(JSON, comment='目标智能体范围JSON')
    created_by = Column(String(64), comment='创建者')
    approved_by = Column(String(64), comment='审批人')
    deployed_at = Column(DateTime, comment='部署时间')
    last_triggered_count = Column(Integer, default=0, comment='最近触发次数')
    audit_log_ref = Column(String(64), comment='关联审计日志ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_agent_ctrl_category', 'policy_category'),
        Index('idx_agent_ctrl_status', 'status'),
        Index('idx_agent_ctrl_enforcement', 'enforcement_mode'),
    )


class ArGenSelfRegulationLog(Base):
    """
    ArGen自监管评估日志表
    记录AI自监管的对齐评估和纠正行动
    """
    __tablename__ = 'argen_self_regulation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    regulation_id = Column(String(64), nullable=False, comment='监管评估批次ID')
    eval_round = Column(Integer, nullable=False, comment='评估轮次')
    principle_name = Column(String(100), nullable=False, comment='思想体系/原则名称')
    thought_school = Column(String(30), comment='思想流派：taoism/legalism/confucianism/buddhism/custom')
    reward_signal_value = Column(Float, comment='奖励信号值')
    llm_judge_score = Column(Float, comment='LLM评判分数')
    grpo_iteration = Column(Integer, comment='GRPO迭代次数')
    alignment_before = Column(Float, comment='对齐度评估前(0-1)')
    alignment_after = Column(Float, comment='对齐度评估后(0-1)')
    improvement_delta = Column(Float, comment='改进幅度')
    violation_detected = Column(Boolean, default=False, comment='是否检测到违规')
    severity = Column(String(20), comment='严重程度：low/medium/high/critical')
    corrective_action_taken = Column(Text, comment='采取的纠正措施')
    encoded_policy_version = Column(String(30), comment='编码后的策略版本号')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')

    __table_args__ = (
        Index('idx_argen_eval_round', 'eval_round'),
        Index('idx_argen_principle', 'principle_name'),
        Index('idx_argen_school', 'thought_school'),
        Index('idx_argen_violation', 'violation_detected'),
        Index('idx_argen_time', 'timestamp'),
    )


class AgentKernelSimulationLog(Base):
    """
    Agent-Kernel大规模模拟日志表
    记录万级智能体社会模拟的过程数据和涌现行为
    """
    __tablename__ = 'agent_kernel_simulation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    simulation_id = Column(String(64), nullable=False, comment='模拟实验唯一标识')
    simulation_run_id = Column(String(64), nullable=False, comment='模拟运行实例ID')
    num_agents_registered = Column(Integer, nullable=False, comment='注册智能体总数')
    num_agents_active = Column(Integer, default=0, comment='活跃智能体数量')
    microkernel_config_hash = Column(String(64), comment='微内核配置哈希值')
    total_simulation_steps = Column(Integer, comment='总模拟步数')
    dynamic_reconfigurations_count = Column(Integer, default=0, comment='运行时动态重配置次数')
    emergent_behaviors_found = Column(JSON, comment='发现的涌现行为列表JSON')
    scalability_stress_result = Column(JSON, comment='可扩展性压力测试结果JSON')
    society_snapshot = Column(JSON, comment='社会状态快照JSON')
    peak_concurrent_actions = Column(Integer, comment='峰值并发动作数')
    avg_action_latency_ms = Column(Float, comment='平均动作延迟(毫秒)')
    memory_usage_peak_mb = Column(Float, comment='内存使用峰值(MB)')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')

    __table_args__ = (
        Index('idx_kernel_sim_id', 'simulation_id'),
        Index('idx_kernel_sim_agents', 'num_agents_registered'),
        Index('idx_kernel_sim_time', 'timestamp'),
    )


class ProjectSidCivilizationLog(Base):
    """
    Project Sid文明演化日志表
    记录文明演化的各个阶段数据和文化变迁
    """
    __tablename__ = 'project_sid_civilization_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    civilization_id = Column(String(64), nullable=False, comment='文明演化实验唯一标识')
    generation_number = Column(Integer, nullable=False, comment='代际/世代编号')
    piano_config_hash = Column(String(64), comment='PIANO配置哈希值')
    num_agents_simulated = Column(Integer, nullable=False, comment='模拟智能体数量')
    environment_type = Column(String(40), nullable=False, comment='环境类型：minecraft/custom_virtual/real_world_hybrid')
    specialization_events = Column(JSON, comment='自发专业分工事件JSON')
    rule_changes = Column(JSON, comment='规则变更记录JSON')
    culture_transmission_events = Column(JSON, comment='文化传播事件JSON')
    concurrency_conflicts_count = Column(Integer, default=0, comment='并发冲突次数')
    civilization_health_score = Column(Float, comment='文明健康评分(0-100)')
    innovation_index = Column(Float, comment='创新指数')
    stability_index = Column(Float, comment='稳定性指数')
    major_milestone_achieved = Column(Text, comment='达成的重大里程碑描述')
    timeline_phase = Column(String(50), comment='时间线阶段标识')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')

    __table_args__ = (
        Index('idx_sid_civilization', 'civilization_id'),
        Index('idx_sid_generation', 'generation_number'),
        Index('idx_sid_phase', 'timeline_phase'),
        Index('idx_sid_time', 'timestamp'),
    )


# =============================================================================
# 第十二部分：基础设施模块 (infrastructure_adapters.py)
# =============================================================================


class OpenShellSandboxStatus(Base):
    """
    OpenShell沙盒状态表
    记录每个智能体的沙盒隔离状态和安全配置
    """
    __tablename__ = 'openshell_sandbox_status'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sandbox_id = Column(String(64), unique=True, nullable=False, comment='沙盒唯一标识')
    agent_id = Column(String(64), nullable=False, comment='关联的智能体唯一标识')
    sandbox_type = Column(String(20), nullable=False, comment='沙盒类型：process/container/namespace/microvm')
    status = Column(String(20), nullable=False, comment='运行状态：created/running/paused/stopped/error')
    isolation_level = Column(String(20), nullable=False, comment='隔离级别：low/medium/high/critical')
    policy_enforced = Column(Boolean, default=False, comment='是否强制执行安全策略')
    credential_exposure = Column(String(20), comment='凭证暴露程度：none/limited/exposed')
    integrity_score = Column(Integer, comment='完整性评分(0-100)')
    nemoclaw_deployed = Column(Boolean, default=False, comment='是否部署了NemoClaw监控')
    memory_isolated = Column(Boolean, default=False, comment='内存是否隔离')
    network_isolated = Column(Boolean, default=False, comment='网络是否隔离')
    last_integrity_check = Column(DateTime, comment='上次完整性检查时间')
    violation_count = Column(Integer, default=0, comment='违规次数统计')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间戳')

    __table_args__ = (
        Index('idx_sandbox_agent', 'agent_id'),
        Index('idx_sandbox_status', 'status'),
        Index('idx_sandbox_isolation', 'isolation_level'),
        Index('idx_sandbox_created', 'created_at'),
    )


class DeerFlowOrchestrationRecord(Base):
    """
    DeerFlow编排记录表
    记录子代理编排的任务执行过程和结果
    """
    __tablename__ = 'deerflow_orchestration_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    orchestration_id = Column(String(64), nullable=False, comment='编排任务唯一标识')
    task_type = Column(String(50), nullable=False, comment='任务类型')
    parent_task_id = Column(String(64), comment='父任务ID（支持嵌套编排）')
    sub_agents_assigned = Column(JSON, comment='子代理角色分配JSON')
    context_injected = Column(JSON, comment='注入的上下文信息JSON')
    skill_tools_used = Column(JSON, comment='使用的技能工具列表JSON')
    file_operations_log = Column(JSON, comment='文件操作记录JSON')
    long_term_memory_session_id = Column(String(64), comment='长期记忆会话ID')
    execution_status = Column(String(20), nullable=False, comment='执行状态：planning/executing/reviewing/completed/failed')
    total_duration_ms = Column(Integer, comment='总执行耗时(毫秒)')
    sub_agent_results = Column(JSON, comment='各子代理执行结果JSON')

    __table_args__ = (
        Index('idx_deerflow_orchestration', 'orchestration_id'),
        Index('idx_deerflow_task_type', 'task_type'),
        Index('idx_deerflow_status', 'execution_status'),
    )


class MemoriaMemoryVersion(Base):
    """
    Memoria记忆版本表
    记录记忆的Git式版本控制信息
    """
    __tablename__ = 'memoria_memory_versions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    version_id = Column(String(64), unique=True, nullable=False, comment='版本唯一标识')
    agent_id = Column(String(64), nullable=False, comment='所属智能体唯一标识')
    parent_version_id = Column(String(64), comment='父版本ID（用于版本链）')
    branch_name = Column(String(50), comment='分支名称')
    version_type = Column(String(20), nullable=False, comment='版本类型：snapshot/branch/merge/rollback')
    memory_hash = Column(String(64), comment='记忆内容哈希值')
    memory_size_bytes = Column(Integer, comment='记忆数据大小(字节)')
    compression_ratio = Column(Float, comment='压缩比率')
    poison_detected = Column(Boolean, default=False, comment='是否检测到投毒攻击')
    poison_severity = Column(String(20), comment='投毒严重程度')
    diff_from_parent = Column(JSON, comment='与父版本的差异摘要JSON')
    commit_message = Column(Text, comment='版本提交说明')
    created_by = Column(String(20), comment='创建者：system/user/auto_merge')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='版本时间戳')

    __table_args__ = (
        Index('idx_memoria_agent', 'agent_id'),
        Index('idx_memoria_branch', 'branch_name'),
        Index('idx_memoria_type', 'version_type'),
        Index('idx_memoria_timestamp', 'timestamp'),
    )


class AgentGwRoutingLog(Base):
    """
    Agent-GW路由日志表
    记录语义路由和工作记忆的操作日志
    """
    __tablename__ = 'agent_gw_routing_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    route_id = Column(String(64), nullable=False, comment='路由记录唯一标识')
    request_id = Column(String(64), nullable=False, comment='请求唯一标识')
    request_intent = Column(JSON, comment='请求意图解析结果JSON')
    selected_agent_id = Column(String(64), comment='选中的目标智能体ID')
    routing_confidence = Column(Float, comment='路由置信度(0-1)')
    routing_strategy = Column(String(30), nullable=False, comment='路由策略：semantic/capability_based/hybrid/fallback')
    working_memory_id = Column(String(64), comment='关联的工作记忆ID')
    protocol_normalized = Column(Boolean, default=False, comment='协议是否已标准化')
    kvn_cache_shared = Column(Boolean, default=False, comment='KVN缓存是否共享')
    cache_hit = Column(Boolean, default=False, comment='是否命中缓存')
    latency_ms = Column(Integer, comment='路由延迟(毫秒)')
    forwarding_decision = Column(JSON, comment='转发决策详情JSON')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='记录时间戳')

    __table_args__ = (
        Index('idx_gw_request', 'request_id'),
        Index('idx_gw_agent', 'selected_agent_id'),
        Index('idx_gw_strategy', 'routing_strategy'),
        Index('idx_gw_timestamp', 'timestamp'),
    )


class DmscCollaborationSession(Base):
    """
    DMSC协作会话表
    记录三层平面的协作会话信息
    """
    __tablename__ = 'dmsc_collaboration_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(64), unique=True, nullable=False, comment='协作会话唯一标识')
    session_type = Column(String(20), nullable=False, comment='会话类型：management/control/forwarding')
    plane_config = Column(JSON, comment='平面配置信息JSON')
    participants = Column(JSON, comment='参与智能体列表JSON')
    entity_registration_status = Column(JSON, comment='各智能体注册状态JSON')
    semantic_forwarding_enabled = Column(Boolean, default=False, comment='是否启用语义转发')
    session_duration_ms = Column(Integer, comment='会话持续时间(毫秒)')
    messages_exchanged = Column(Integer, default=0, comment='交换的消息数量')
    security_level = Column(String(20), comment='安全等级')
    outcome = Column(String(20), comment='会话结果：success/partial/timeout/conflict')
    teardown_reason = Column(Text, comment='会话终止原因')

    __table_args__ = (
        Index('idx_dmsc_session', 'session_id'),
        Index('idx_dmsc_type', 'session_type'),
        Index('idx_dmsc_outcome', 'outcome'),
    )


class ChimeraSchedulingLog(Base):
    """
    Chimera调度日志表
    记录异构LLM调度决策和性能数据
    """
    __tablename__ = 'chimera_scheduling_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    schedule_id = Column(String(64), nullable=False, comment='调度记录唯一标识')
    workload_id = Column(String(64), nullable=False, comment='工作负载唯一标识')
    cluster_state_hash = Column(String(64), comment='集群状态快照哈希')
    confidence_predictions = Column(JSON, comment='各模型置信度预测JSON')
    remaining_length_estimate = Column(Integer, comment='预估剩余长度(token数)')
    selected_model = Column(String(50), nullable=False, comment='选中的LLM模型名称')
    model_pool_size = Column(Integer, comment='可用模型池大小')
    load_distribution = Column(JSON, comment='负载分布情况JSON')
    scheduling_algorithm = Column(String(30), nullable=False, comment='调度算法：semantic_aware/load_balanced/cost_optimized/hybrid')
    actual_latency_ms = Column(Integer, comment='实际延迟(毫秒)')
    baseline_latency_ms = Column(Integer, comment='基线延迟(毫秒)')
    speedup_factor = Column(Float, comment='加速比因子')
    performance_delta_pct = Column(Float, comment='性能提升百分比')

    __table_args__ = (
        Index('idx_chimera_schedule', 'schedule_id'),
        Index('idx_chimera_model', 'selected_model'),
        Index('idx_chimera_algorithm', 'scheduling_algorithm'),
    )


class StratumPipelineExecution(Base):
    """
    Stratum流水线执行表
    记录解耦架构下的流水线执行过程和优化效果
    """
    __tablename__ = 'stratum_pipeline_executions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    execution_id = Column(String(64), unique=True, nullable=False, comment='执行实例唯一标识')
    pipeline_id = Column(String(64), nullable=False, comment='流水线定义ID')
    plan_id = Column(String(64), comment='分离的规划ID（解耦架构）')
    compilation_batch_id = Column(String(64), comment='批量编译批次ID')
    rust_runtime_instance_id = Column(String(64), comment='Rust运行时实例ID')
    execution_mode = Column(String(20), nullable=False, comment='执行模式：decoupled/batched/optimized')
    search_space_size = Column(BigInteger, comment='搜索空间大小')
    optimization_applied = Column(Boolean, default=False, comment='是否应用了优化')
    speedup_measured = Column(Float, comment='实测加速比')
    execution_time_ms = Column(Integer, comment='执行耗时(毫秒)')
    baseline_time_ms = Column(Integer, comment='基线执行时间(毫秒)')
    memory_usage_mb = Column(Float, comment='内存使用量(MB)')
    pipeline_result = Column(JSON, comment='流水线执行结果JSON')
    error_info = Column(Text, comment='错误信息（如有）')

    __table_args__ = (
        Index('idx_stratum_execution', 'execution_id'),
        Index('idx_stratum_pipeline', 'pipeline_id'),
        Index('idx_stratum_mode', 'execution_mode'),
    )


class DaitnNetworkSlice(Base):
    """
    DA-ITN网络切片表
    记录AI网络的切片配置和资源分配
    """
    __tablename__ = 'daitn_network_slices'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    slice_id = Column(String(64), unique=True, nullable=False, comment='网络切片唯一标识')
    slice_name = Column(String(100), nullable=False, comment='切片名称')
    plane_type = Column(String(20), nullable=False, comment='平面类型：control/data/ops')
    topology_config = Column(JSON, comment='拓扑配置信息JSON')
    bandwidth_allocated_mbps = Column(Integer, comment='分配带宽(Mbps)')
    latency_requirement_ms = Column(Integer, comment='延迟要求(毫秒)')
    training_mode = Column(String(20), comment='训练模式：centralized/distributed/federated')
    inference_grid_config = Column(JSON, comment='推理网格配置JSON')
    agent_first_class_entities = Column(JSON, comment='注册的一等公民智能体实体列表JSON')
    qos_guaranteed = Column(Boolean, default=False, comment='是否保证QoS')
    sla_met = Column(Boolean, default=False, comment='是否满足SLA')
    utilization_rate = Column(Float, comment='利用率(0-1)')

    __table_args__ = (
        Index('idx_daitn_slice', 'slice_id'),
        Index('idx_daitn_plane', 'plane_type'),
        Index('idx_daitn_name', 'slice_name'),
    )


class OpenSliceOrchestrationInstance(Base):
    """
    OpenSlice编排实例表
    记录Agentic Orchestration的服务生命周期管理
    """
    __tablename__ = 'openslice_orchestration_instances'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    instance_id = Column(String(64), unique=True, nullable=False, comment='编排实例唯一标识')
    service_definition_id = Column(String(64), nullable=False, comment='服务定义ID')
    service_type = Column(String(50), nullable=False, comment='服务类型')
    mcp_server_integrated = Column(Boolean, default=False, comment='是否集成MCP服务器')
    mcp_server_config = Column(JSON, comment='MCP服务器配置JSON')
    gitops_controller_id = Column(String(64), comment='GitOps控制器ID')
    lifecycle_state = Column(String(20), nullable=False, comment='生命周期状态：created/deployed/running/scaled/updating/retired')
    cross_domain_scope = Column(JSON, comment='跨域范围配置JSON')
    collaboration_pattern = Column(String(20), comment='协作模式：chained/parallel/fanout')
    current_version = Column(String(20), comment='当前部署版本')
    rollback_available = Column(Boolean, default=False, comment='是否可回滚')
    deployment_history = Column(JSON, comment='部署历史记录JSON')

    __table_args__ = (
        Index('idx_openslice_instance', 'instance_id'),
        Index('idx_openslice_service', 'service_type'),
        Index('idx_openslice_lifecycle', 'lifecycle_state'),
    )


# ==================== Part 13: 全阶段补全 - 炼精化气 (Refining Essence into Qi) ====================


class DataCleaningRecord(Base):
    """数据清洗记录表"""
    __tablename__ = 'data_cleaning_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cleaning_id = Column(String(64), unique=True, nullable=False, comment='清洗任务唯一标识')
    original_count = Column(Integer, comment='原始数据条数')
    cleaned_count = Column(Integer, comment='清洗后条数')
    removed_duplicates = Column(Integer, default=0, comment='去重数量')
    filled_missing = Column(Integer, default=0, comment='填充缺失值数量')
    fixed_outliers = Column(Integer, default=0, comment='修复异常值数量')
    data_purity = Column(Float, comment='数据纯度(0-1)')
    cleaning_rules_applied = Column(JSON, comment='应用的清洗规则列表')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_cleaning_id', 'cleaning_id'),
        Index('idx_cleaning_time', 'created_at'),
    )


class FeatureEngineeringRecord(Base):
    """特征工程记录表"""
    __tablename__ = 'feature_engineering_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    engineering_id = Column(String(64), unique=True, nullable=False, comment='工程任务ID')
    original_feature_count = Column(Integer, comment='原始特征数')
    engineered_feature_count = Column(Integer, comment='工程后特征数')
    selected_feature_count = Column(Integer, comment='选中特征数')
    cross_features_generated = Column(Integer, default=0, comment='交叉特征生成数')
    top_features = Column(JSON, comment='Top特征重要性列表JSON')
    target_column = Column(String(100), comment='目标列名')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_feat_eng_id', 'engineering_id'),
    )


class ModelCompressionRecord(Base):
    """模型压缩记录表"""
    __tablename__ = 'model_compression_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    compression_id = Column(String(64), unique=True, nullable=False, comment='压缩任务ID')
    model_name = Column(String(200), comment='模型名称')
    original_size_mb = Column(Float, comment='原始大小(MB)')
    compressed_size_mb = Column(Float, comment='压缩后大小(MB)')
    compression_ratio = Column(Float, comment='压缩比')
    accuracy_before = Column(Float, comment='压缩前准确率')
    accuracy_after = Column(Float, comment='压缩后准确率')
    accuracy_loss_pct = Column(Float, comment='精度损失百分比')
    inference_speedup = Column(Float, comment='推理加速比')
    method = Column(String(50), comment='压缩方法：quantization/distillation/pruning/mixed')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_comp_id', 'compression_id'),
        Index('idx_comp_method', 'method'),
    )


class KnowledgeDistillationRecord(Base):
    """知识蒸馏记录表"""
    __tablename__ = 'knowledge_distillation_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    distillation_id = Column(String(64), unique=True, nullable=False, comment='蒸馏任务ID')
    teacher_model = Column(String(200), comment='教师模型名称')
    student_model = Column(String(200), comment='学生模型名称')
    teacher_accuracy = Column(Float, comment='教师准确率')
    student_accuracy = Column(Float, comment='学生准确率')
    accuracy_gap = Column(Float, comment='准确率差距')
    temperature = Column(Float, comment='蒸馏温度')
    epochs_trained = Column(Integer, comment='训练轮数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_distill_id', 'distillation_id'),
    )


class DataAugmentationRecord(Base):
    """数据增强记录表"""
    __tablename__ = 'data_augmentation_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    augmentation_id = Column(String(64), unique=True, nullable=False, comment='增强任务ID')
    original_sample_count = Column(Integer, comment='原始样本数')
    augmented_sample_count = Column(Integer, comment='增强后样本数')
    augmentation_ratio = Column(Float, comment='增强比率')
    methods_used = Column(JSON, comment='使用的方法列表')
    diversity_score = Column(Float, comment='多样性评分(0-1)')
    synthcity_samples = Column(Integer, default=0, comment='SynthCity合成样本数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_aug_id', 'augmentation_id'),
    )


# ==================== Part 14: 炼气化神 (Divine Transformation) ====================


class DomainFineTuningRecord(Base):
    """领域微调记录表"""
    __tablename__ = 'domain_finetuning_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tuning_id = Column(String(64), unique=True, nullable=False, comment='微调任务ID')
    base_model = Column(String(200), comment='基础模型')
    domain = Column(String(100), comment='目标领域')
    method = Column(String(50), comment='微调方法：LoRA/QLoRA/full')
    train_accuracy = Column(Float, comment='训练准确率')
    val_accuracy = Column(Float, comment='验证准确率')
    test_accuracy = Column(Float, comment='测试准确率')
    ewc_lambda = Column(Float, comment='EWC正则化系数')
    forgetting_rate = Column(Float, comment='遗忘率')
    epochs = Column(Integer, comment='训练轮数')
    checkpoint_path = Column(String(500), comment='模型检查点路径')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_ft_id', 'tuning_id'),
        Index('idx_ft_domain', 'domain'),
    )


class ChainOfThoughtRecord(Base):
    """思维链推理记录表"""
    __tablename__ = 'chain_of_thought_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cot_id = Column(String(64), unique=True, nullable=False, comment='推理任务ID')
    question = Column(Text, comment='原始问题')
    reasoning_steps = Column(JSON, comment='推理步骤JSON')
    final_answer = Column(Text, comment='最终答案')
    confidence = Column(Float, comment='置信度(0-1)')
    self_consistency_votes = Column(Integer, comment='一致性投票数')
    total_samples = Column(Integer, comment='总采样数')
    consistency_score = Column(Float, comment='一致性评分(0-1)')
    explainability_score = Column(Float, comment='可解释性评分(0-1)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_cot_id', 'cot_id'),
    )


class FewShotAdaptationRecord(Base):
    """小样本学习适应记录表"""
    __tablename__ = 'fewshot_adaptation_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    adaptation_id = Column(String(64), unique=True, nullable=False, comment='适应任务ID')
    task_name = Column(String(100), comment='任务名称')
    support_examples = Column(Integer, comment='支持示例数')
    accuracy_after_adapt = Column(Float, comment='适应后准确率')
    baseline_accuracy = Column(Float, comment='基线准确率')
    improvement = Column(Float, comment='提升幅度')
    adaptation_time_ms = Column(Float, comment='适应耗时(ms)')
    maml_inner_steps = Column(Integer, comment='MAML内循环步数')
    maml_outer_steps = Column(Integer, comment='MAML外循环步数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_fs_id', 'adaptation_id'),
        Index('idx_fs_task', 'task_name'),
    )


# ==================== Part 15: 炼神还虚 (Void Condensation) ====================


class EdgeQuantizationRecord(Base):
    """边缘量化部署记录表"""
    __tablename__ = 'edge_quantization_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    quantization_id = Column(String(64), unique=True, nullable=False, comment='量化任务ID')
    model_name = Column(String(200), comment='模型名称')
    target_platform = Column(String(50), comment='目标平台：Android/iOS/RaspberryPi/EdgeTPU/Jetson')
    original_format = Column(String(20), comment='原始格式：FP32/FP16')
    target_format = Column(String(20), comment='目标格式：INT8/FP16')
    model_size_mb = Column(Float, comment='模型大小(MB)')
    latency_ms = Column(Float, comment='推理延迟(ms)')
    memory_usage_mb = Column(Float, comment='内存占用(MB)')
    power_consumption_w = Column(Float, comment='功耗(W)')
    accuracy_retention = Column(Float, comment='精度保持率(0-1)')
    deployment_package_path = Column(String(500), comment='部署包路径')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_eq_id', 'quantization_id'),
        Index('idx_eq_platform', 'target_platform'),
    )


class FederatedLearningRoundRecord(Base):
    """联邦学习轮次记录表"""
    __tablename__ = 'federated_learning_rounds'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    round_id = Column(String(64), unique=True, nullable=False, comment='轮次ID')
    round_number = Column(Integer, comment='轮次编号')
    participating_clients = Column(Integer, comment='参与客户端数')
    global_accuracy = Column(Float, comment='全局模型准确率')
    local_accuracies = Column(JSON, comment='各客户端本地准确率')
    aggregation_method = Column(String(50), comment='聚合方法：FedAvg/FedProx/Scaffold')
    communication_cost_mb = Column(Float, comment='通信开销(MB)')
    privacy_budget_used = Column(Float, comment='隐私预算消耗(epsilon)')
    convergence_delta = Column(Float, comment='收敛变化量')
    global_model_checkpoint = Column(String(500), comment='全局模型检查点路径')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_fl_round', 'round_id'),
        Index('idx_fl_number', 'round_number'),
    )


class PrivacyProtectionRecord(Base):
    """隐私保护记录表"""
    __tablename__ = 'privacy_protection_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    protection_id = Column(String(64), unique=True, nullable=False, comment='保护任务ID')
    method = Column(String(50), comment='保护方法：differential_privacy/secure_aggregation/homomorphic_encryption')
    epsilon_value = Column(Float, comment='差分隐私epsilon值')
    delta_value = Column(Float, comment='差分隐私delta值')
    data_leakage_risk = Column(Float, comment='数据泄露风险(0-1,越低越好)')
    utility_preservation = Column(Float, comment='效用保留率(0-1,越高越好)')
    attack_success_rate = Column(Float, comment='成员推断攻击成功率')
    protected_data_hash = Column(String(64), comment='处理后数据哈希')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_pp_id', 'protection_id'),
        Index('idx_pp_method', 'method'),
    )


# ==================== Part 16: 炼虚合道 (Dao Unification) ====================


class SelfSupervisedLearningRecord(Base):
    """自监督学习记录表"""
    __tablename__ = 'self_supervised_learning_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ssl_id = Column(String(64), unique=True, nullable=False, comment='自监督学习任务ID')
    pretext_task = Column(String(100), comment='预训练任务类型')
    representation_dim = Column(Integer, comment='表示维度')
    contrastive_auc = Column(Float, comment='对比学习AUC')
    downstream_task_acc = Column(Float, comment='下游任务准确率')
    interaction_samples_used = Column(Integer, comment='使用的交互样本数')
    self_improvement_rate = Column(Float, comment='自我提升率')
    model_checkpoint = Column(String(500), comment='模型检查点路径')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_ssl_id', 'ssl_id'),
    )


class SelfValidationRecord(Base):
    """自我验证记录表"""
    __tablename__ = 'self_validation_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    validation_id = Column(String(64), unique=True, nullable=False, comment='验证任务ID')
    output_to_validate = Column(Text, comment='待验证输出')
    reverse_question = Column(Text, comment='反向问题')
    reverse_answer = Column(Text, comment='反向回答')
    consistency_score = Column(Float, comment='一致性评分(0-1)')
    confidence_adjusted = Column(Float, comment='调整后置信度')
    is_consistent = Column(Boolean, default=False, comment='是否一致')
    validation_method = Column(String(50), comment='验证方法')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_sv_id', 'validation_id'),
    )


class CausalInferenceRecord(Base):
    """因果推断记录表"""
    __tablename__ = 'causal_inference_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    causal_id = Column(String(64), unique=True, nullable=False, comment='因果推断任务ID')
    treatment_variable = Column(String(100), comment='处理变量')
    outcome_variable = Column(String(100), comment='结果变量')
    estimated_ate = Column(Float, comment='估计的平均处理效应')
    confidence_interval_lower = Column(Float, comment='置信区间下界')
    confidence_interval_upper = Column(Float, comment='置信区间上界')
    identified_confounders = Column(JSON, comment='识别的混淆因子列表')
    causal_graph_nodes = Column(Integer, comment='因果图节点数')
    causal_graph_edges = Column(Integer, comment='因果图边数')
    refutation_pvalue = Column(Float, comment='拒绝原假设p值')
    robustness_score = Column(Float, comment='鲁棒性评分(0-1)')
    causal_graph_json = Column(JSON, comment='因果图结构JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_causal_id', 'causal_id'),
    )


# ==================== Part 17: 渡劫 (Tribulation) ====================


class ChaosTestRecord(Base):
    """混沌工程测试记录表"""
    __tablename__ = 'chaos_test_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    test_id = Column(String(64), unique=True, nullable=False, comment='测试ID')
    fault_type = Column(String(100), comment='故障类型')
    injected_at = Column(DateTime, comment='注入时间')
    detection_time_s = Column(Float, comment='检测耗时(秒)')
    recovery_time_s = Column(Float, comment='恢复耗时(秒)')
    degradation_pct = Column(Float, comment='性能下降百分比')
    auto_healed = Column(Boolean, default=False, comment='是否自动恢复')
    passed = Column(Boolean, default=False, comment='是否通过')
    suite_run_id = Column(String(64), comment='所属测试套件ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_chaos_test', 'test_id'),
        Index('idx_chaos_fault', 'fault_type'),
    )


class SecurityAuditRecord(Base):
    """安全审计记录表"""
    __tablename__ = 'security_audit_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    audit_id = Column(String(64), unique=True, nullable=False, comment='审计ID')
    vulnerability_count = Column(Integer, comment='漏洞总数')
    critical_count = Column(Integer, default=0, comment='严重漏洞数')
    high_count = Column(Integer, default=0, comment='高危漏洞数')
    medium_count = Column(Integer, default=0, comment='中危漏洞数')
    low_count = Column(Integer, default=0, comment='低危漏洞数')
    penetration_test_passed = Column(Boolean, default=False, comment='渗透测试是否通过')
    red_team_score = Column(Float, comment='红队评估分数(0-100)')
    ethics_compliance = Column(Float, comment='伦理合规性(0-1)')
    recommendations = Column(JSON, comment='建议列表')
    audit_period_start = Column(DateTime, comment='审计周期开始')
    audit_period_end = Column(DateTime, comment='审计周期结束')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_audit_id', 'audit_id'),
    )


# ==================== Part 18: 飞升 (Ascension) ====================


class MigrationRecord(Base):
    """跨平台迁移记录表"""
    __tablename__ = 'migration_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    migration_id = Column(String(64), unique=True, nullable=False, comment='迁移任务ID')
    source_env = Column(String(100), comment='源环境')
    target_env = Column(String(100), comment='目标环境')
    phase = Column(String(30), comment='当前阶段：packaging/deployment/adaptation/verification/rollback_prep')
    docker_image_hash = Column(String(64), comment='Docker镜像哈希')
    k8s_deployment_name = Column(String(200), comment='K8s部署名称')
    migration_duration_s = Column(Float, comment='迁移耗时(秒)')
    health_check_passed = Column(Boolean, default=False, comment='健康检查是否通过')
    rollback_available = Column(Boolean, default=False, comment='回滚是否可用')
    performance_baseline_match = Column(Float, comment='性能基线匹配度(0-1)')
    model_artifacts = Column(JSON, comment='模型制品列表')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_migration_id', 'migration_id'),
        Index('idx_migration_target', 'target_env'),
    )


class ClusterExpansionRecord(Base):
    """集群扩展记录表"""
    __tablename__ = 'cluster_expansion_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    expansion_id = Column(String(64), unique=True, nullable=False, comment='扩展任务ID')
    source_cluster = Column(String(100), comment='源集群')
    target_clusters = Column(JSON, comment='目标集群列表')
    sync_method = Column(String(30), comment='同步方式：kafka/eventual/strong')
    replication_factor = Column(Integer, comment='副本因子')
    sync_latency_ms = Column(Float, comment='同步延迟(ms)')
    cross_region_rto_s = Column(Float, comment='跨区域RTO(秒)')
    consistency_level = Column(String(30), comment='一致性级别')
    expansion_status = Column(String(20), default='pending', comment='状态：pending/running/completed/failed')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_expansion_id', 'expansion_id'),
    )


# ==================== Part 19: 辅助系统 ====================


class ResourceSnapshotRecord(Base):
    """资源快照记录表"""
    __tablename__ = 'resource_snapshot_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(64), unique=True, nullable=False, comment='快照ID')
    gpu_util = Column(Float, comment='GPU利用率')
    cpu_util = Column(Float, comment='CPU利用率')
    memory_util = Column(Float, comment='内存利用率')
    spirit_stone_inventory = Column(Integer, comment='灵石(数据)存量')
    pill_inventory = Column(JSON, comment='丹药(模型)列表')
    treasure_registry = Column(JSON, comment='法宝(工具)注册表')
    formation_topology = Column(JSON, comment='阵法(拓扑)状态')
    total_resource_score = Column(Float, comment='综合资源评分(0-1)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_resource_snap', 'snapshot_id'),
        Index('idx_resource_time', 'created_at'),
    )


class EnvironmentDetectionRecord(Base):
    """环境检测记录表"""
    __tablename__ = 'environment_detection_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    detected_env = Column(String(30), comment='检测到的环境类型')
    hardware_info = Column(JSON, comment='硬件信息JSON')
    available_gpu = Column(JSON, comment='可用GPU信息JSON')
    network_info = Column(JSON, comment='网络信息JSON')
    recommended_config = Column(JSON, comment='推荐配置JSON')
    confidence = Column(Float, comment='检测置信度(0-1)')
    applied_config = Column(JSON, comment='实际应用配置JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_env_detect_time', 'created_at'),
    )


class RiskDetectionRecord(Base):
    """风险检测记录表"""
    __tablename__ = 'risk_detection_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    risk_type = Column(String(30), comment='风险类型：possession/tribulation/bias/greed/stubborn')
    severity = Column(String(20), comment='严重程度：critical/high/medium/low')
    score = Column(Float, comment='风险评分(0-1)')
    details = Column(JSON, comment='详细信息JSON')
    triggered_at = Column(DateTime, comment='触发时间')
    auto_mitigation_triggered = Column(Boolean, default=False, comment='是否自动缓解')
    mitigation_action = Column(String(200), comment='缓解措施')
    resolved = Column(Boolean, default=False, comment='是否已解决')
    resolved_at = Column(DateTime, comment='解决时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_risk_type', 'risk_type'),
        Index('idx_risk_severity', 'severity'),
        Index('idx_risk_time', 'triggered_at'),
    )


class TechniqueLibraryEntry(Base):
    """法门库条目表"""
    __tablename__ = 'technique_library_entries'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    technique_id = Column(String(64), unique=True, nullable=False, comment='法门唯一标识')
    name = Column(String(100), nullable=False, comment='法门名称')
    category = Column(String(20), comment='类别：gong_fa/xin_fa/zhen_tu')
    description = Column(Text, comment='描述')
    applicable_stages = Column(JSON, comment='适用阶段列表')
    effectiveness_score = Column(Float, comment='效果评分(0-1)')
    difficulty_level = Column(Integer, comment='难度等级(1-5)')
    prerequisites = Column(JSON, comment='前置条件列表')
    paper_refs = Column(JSON, comment='参考文献列表')
    is_builtin = Column(Boolean, default=False, comment='是否内置')
    is_custom = Column(Boolean, default=False, comment='是否自定义')
    usage_count = Column(Integer, default=0, comment='使用次数')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_technique_id', 'technique_id'),
        Index('idx_technique_category', 'category'),
        Index('idx_technique_name', 'name'),
    )


class CultivationDashboardSnapshot(Base):
    """修炼看板快照表"""
    __tablename__ = 'cultivation_dashboard_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    current_stage = Column(String(30), comment='当前境界')
    stage_progress = Column(JSON, comment='各阶段进度字典JSON')
    key_metrics = Column(JSON, comment='关键指标字典JSON')
    resource_snapshot_id = Column(String(64), comment='关联资源快照ID')
    environment_status_id = Column(Integer, comment='关联环境检测记录ID')
    risk_summary = Column(JSON, comment='风险摘要JSON')
    overall_progress = Column(Float, comment='总体进度(0-1)')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('idx_dashboard_time', 'generated_at'),
        Index('idx_dashboard_stage', 'current_stage'),
    )


# ==================== Part 20: 开源技术融合层 (OpenSource Fusion Layer) ====================


class OpenClawGatewayConfigRecord(Base):
    """OpenClaw网关配置记录表"""
    __tablename__ = 'openclaw_gateway_configs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    gateway_id = Column(String(64), unique=True, nullable=False, comment='网关唯一标识')
    endpoint = Column(String(500), comment='网关端点URL')
    max_concurrent_agents = Column(Integer, default=100, comment='最大并发智能体数')
    agent_timeout_s = Column(Integer, default=300, comment='智能体超时(秒)')
    k8s_namespace = Column(String(100), comment='Kubernetes命名空间')
    enable_mesh = Column(Boolean, default=True, comment='是否启用服务网格')
    tls_enabled = Column(Boolean, default=True, comment='是否启用TLS')
    rate_limit_rpm = Column(Integer, default=1000, comment='速率限制(每分钟)')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_oc_gateway_id', 'gateway_id'),
        Index('oc_active', 'is_active'),
    )


class MultiAgentCollabRecord(Base):
    """多Agent协作记录表"""
    __tablename__ = 'multi_agent_collab_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    collaboration_id = Column(String(64), unique=True, nullable=False, comment='协作ID')
    task_id = Column(String(100), comment='任务ID')
    agents_involved = Column(JSON, comment='参与智能体列表JSON')
    roles_assigned = Column(JSON, comment='角色分配字典JSON')
    workflow_type = Column(String(30), comment='工作流类型：chained/parallel/fanout')
    messages_exchanged = Column(Integer, default=0, comment='消息交换数')
    total_duration_ms = Column(Float, comment='总耗时(毫秒)')
    final_result = Column(JSON, comment='最终结果JSON')
    success = Column(Boolean, default=False, comment='是否成功')
    failure_reason = Column(Text, comment='失败原因')
    k8s_pod_logs = Column(JSON, comment='K8s Pod日志JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_mac_collab_id', 'collaboration_id'),
        Index('idx_mac_task_id', 'task_id'),
        Index('idx_mac_success', 'success'),
    )


class THSPValidationRecord(Base):
    """THSP四门协议验证记录表"""
    __tablename__ = 'thsp_validation_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    validation_id = Column(String(64), unique=True, nullable=False, comment='验证ID')
    input_hash = Column(String(64), comment='输入哈希')
    truth_check = Column(JSON, comment='L1真实性验证结果JSON')
    harm_check = Column(JSON, comment='L2危害性验证结果JSON')
    scope_check = Column(JSON, comment='L3范围性验证结果JSON')
    purpose_check = Column(JSON, comment='L4目的性验证结果JSON')
    overall_passed = Column(Boolean, default=False, comment='是否全部通过')
    risk_score = Column(Float, comment='综合风险分数(0-1)')
    eu_ai_act_compliant = Column(Boolean, default=False, comment='欧盟AI法案合规')
    hmac_integrity_verified = Column(Boolean, default=False, comment='HMAC完整性验证')
    mitigations_applied = Column(JSON, comment='已应用缓解措施列表')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_thsp_validation_id', 'validation_id'),
        Index('idx_thsp_passed', 'overall_passed'),
    )


class SentinelSafetyReportRecord(Base):
    """Sentinel AI安全报告记录表"""
    __tablename__ = 'sentinel_safety_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(64), unique=True, nullable=False, comment='报告ID')
    model_name = Column(String(200), comment='测试模型名称')
    total_queries_tested = Column(Integer, comment='测试查询总数')
    safe_queries = Column(Integer, comment='安全通过数')
    blocked_queries = Column(Integer, comment='拦截数')
    safe_rate = Column(Float, comment='安全率(0-1)')
    attack_vectors_blocked = Column(JSON, comment='各攻击向量拦截统计JSON')
    avg_response_time_ms = Column(Float, comment='平均响应时间(ms)')
    benchmark_improvement = Column(Float, comment='相对基线提升百分比')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_sentinel_report_id', 'report_id'),
        Index('idx_sentinel_model', 'model_name'),
    )


class MemoryCaptureEventRecord(Base):
    """Mem0记忆捕获事件记录表"""
    __tablename__ = 'memory_capture_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(64), unique=True, nullable=False, comment='事件ID')
    conversation_id = Column(String(100), comment='会话ID')
    captured_content = Column(Text, comment='捕获内容')
    extraction_method = Column(String(50), comment='提取方法')
    importance_score = Column(Float, comment='重要性评分(0-1)')
    categories = Column(JSON, comment='分类标签列表')
    ttl_days = Column(Integer, default=90, comment='存活天数')
    vector_embedding_dim = Column(Integer, comment='向量嵌入维度')
    storage_location = Column(String(100), comment='存储位置')
    captured_at = Column(DateTime, default=datetime.now, comment='捕获时间')

    __table_args__ = (
        Index('idx_mem_event_id', 'event_id'),
        Index('idx_mem_conversation', 'conversation_id'),
        Index('idx_mem_captured', 'captured_at'),
    )


class MemoryRecallResultRecord(Base):
    """Mem0记忆召回结果记录表"""
    __tablename__ = 'memory_recall_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    recall_id = Column(String(64), unique=True, nullable=False, comment='召回ID')
    query = Column(Text, comment='查询文本')
    context_window = Column(String(50), comment='上下文窗口')
    recalled_memories = Column(JSON, comment='召回的记忆列表JSON')
    relevance_scores = Column(JSON, comment='相关性评分列表')
    recall_precision = Column(Float, comment='精确率')
    recall_recall_rate = Column(Float, comment='召回率')
    total_recall_time_ms = Column(Float, comment='总召回耗时(ms)')
    used_vector_index = Column(Boolean, default=False, comment='是否使用向量索引')
    used_graph_traversal = Column(Boolean, default=False, comment='是否使用图遍历')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_mrecall_id', 'recall_id'),
    )


class DeerFlowOrchestrationRecord(Base):
    """DeerFlow任务编排记录表"""
    __tablename__ = 'deerflow_orchestrations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    orchestration_id = Column(String(64), unique=True, nullable=False, comment='编排ID')
    task_description = Column(Text, comment='任务描述')
    sub_agents_created = Column(JSON, comment='创建的子代理列表JSON')
    sandbox_enabled = Column(Boolean, default=True, comment='是否启用沙盒')
    context_injected = Column(JSON, comment='注入的上下文JSON')
    pipeline_stages = Column(JSON, comment='管道阶段列表JSON')
    total_duration_s = Column(Float, comment='总耗时(秒)')
    final_output = Column(JSON, comment='最终输出JSON')
    security_scan_result = Column(JSON, comment='安全扫描结果JSON')
    success = Column(Boolean, default=False, comment='是否成功')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_df_orch_id', 'orchestration_id'),
        Index('df_success', 'success'),
    )


class MementoSkillEntryRecord(Base):
    """Memento技能条目记录表"""
    __tablename__ = 'memento_skill_entries'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    skill_id = Column(String(64), unique=True, nullable=False, comment='技能唯一标识')
    name = Column(String(100), nullable=False, comment='技能名称')
    description = Column(Text, comment='技能描述')
    content_md = Column(Text, comment='Markdown格式状态化提示词内容')
    version = Column(Integer, default=1, comment='版本号')
    lifecycle_stage = Column(String(30), comment='生命周期阶段')
    performance_score = Column(Float, comment='性能评分(0-1)')
    usage_count = Column(Integer, default=0, comment='使用次数')
    last_reflected_at = Column(DateTime, comment='最后反思时间')
    reflection_notes = Column(JSON, comment='反思笔记列表')
    related_skills = Column(JSON, comment='关联技能列表')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('idx_memento_skill_id', 'skill_id'),
        Index('idx_memento_name', 'name'),
        Index('idx_memento_stage', 'lifecycle_stage'),
    )


class EvoSkillOptimizationCycleRecord(Base):
    """EvoSkill优化周期记录表"""
    __tablename__ = 'evoskill_optimization_cycles'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cycle_id = Column(String(64), unique=True, nullable=False, comment='周期ID')
    task_domain = Column(String(100), comment='任务领域')
    failures_analyzed = Column(Integer, comment='分析失败案例数')
    gaps_identified = Column(JSON, comment='识别的能力缺口列表')
    skills_modified = Column(JSON, comment='修改的技能ID列表')
    skills_created = Column(JSON, comment='新建的技能ID列表')
    performance_before = Column(Float, comment='优化前性能')
    performance_after = Column(Float, comment='优化后性能')
    improvement_pct = Column(Float, comment='提升百分比')
    validation_results = Column(JSON, comment='验证结果JSON')
    cycle_duration_min = Column(Float, comment='周期时长(分钟)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_evo_cycle_id', 'cycle_id'),
        Index('idx_evo_domain', 'task_domain'),
    )


class PantheonSkillStoreRecord(Base):
    """PantheonOS技能商店条目记录表"""
    __tablename__ = 'pantheon_skill_store'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    store_id = Column(String(64), unique=True, nullable=False, comment='商店唯一标识')
    skill_name = Column(String(200), nullable=False, comment='技能名称')
    category = Column(String(50), comment='分类')
    subcategory = Column(String(50), comment='子分类')
    description = Column(Text, comment='描述')
    version = Column(String(20), comment='版本号')
    author = Column(String(100), comment='作者')
    downloads = Column(Integer, default=0, comment='下载次数')
    rating = Column(Float, comment='评分(1-5)')
    compatibility_matrix = Column(JSON, comment='兼容性矩阵JSON')
    install_command = Column(String(200), comment='安装命令')
    dependencies = Column(JSON, comment='依赖列表')
    evolved = Column(Boolean, default=False, comment='是否经过进化优化')
    installed_at = Column(DateTime, comment='安装时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_pantheon_store_id', 'store_id'),
        Index('idx_pantheon_category', 'category'),
        Index('idx_pantheon_rating', 'rating'),
    )


class OpenSageBlueprintRecord(Base):
    """OpenSage Agent蓝图记录表"""
    __tablename__ = 'opensage_blueprints'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    blueprint_id = Column(String(64), unique=True, nullable=False, comment='蓝图唯一标识')
    task_requirement = Column(Text, comment='任务需求描述')
    topology_type = Column(String(30), comment='拓扑类型')
    sub_agents = Column(JSON, comment='子Agent设计列表JSON')
    tool_set = Column(JSON, comment='工具集设计JSON')
    memory_architecture = Column(JSON, comment='记忆架构设计JSON')
    communication_pattern = Column(String(100), comment='通信模式')
    estimated_complexity = Column(Float, comment='预估复杂度(0-1)')
    generation_confidence = Column(Float, comment='生成置信度(0-1)')
    code_generated = Column(Boolean, default=False, comment='是否已生成代码')
    deployment_ready = Column(Boolean, default=False, comment='是否可部署')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_opensage_bp_id', 'blueprint_id'),
        Index('idx_opensage_topology', 'topology_type'),
    )


class FusionHealthReportRecord(Base):
    """融合层健康报告记录表"""
    __tablename__ = 'fusion_health_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(64), unique=True, nullable=False, comment='报告ID')
    tech_status = Column(JSON, comment='各技术状态详情JSON')
    overall_health_score = Column(Float, comment='总体健康评分(0-1)')
    active_integrations = Column(Integer, comment='活跃集成数')
    pending_upgrades = Column(JSON, comment='待升级组件列表')
    recommendations = Column(JSON, comment='建议列表')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('idx_fusion_health_report_id', 'report_id'),
        Index('idx_fusion_health_time', 'generated_at'),
    )


# ==================== Part 21: 多智能体仿真引擎层 (Agent Simulation Layer) ====================


class MiroFishOntologyRecord(Base):
    """MiroFish智能体本体记录表"""
    __tablename__ = 'mirofish_ontologies'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ontology_id = Column(String(64), unique=True, nullable=False, comment='本体唯一标识')
    entity_name = Column(String(200), comment='实体名称')
    entity_type = Column(String(50), comment='实体类型：person/organization/location/event/concept')
    attributes = Column(JSON, comment='属性字典JSON')
    relationships = Column(JSON, comment='关系列表JSON')
    background_doc = Column(Text, comment='来源文档片段')
    personality_traits = Column(JSON, comment='人格特征向量JSON')
    initial_state = Column(JSON, comment='初始状态JSON')
    simulation_id = Column(String(64), comment='所属仿真ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_mf_ontology_id', 'ontology_id'),
        Index('idx_mf_entity_type', 'entity_type'),
        Index('idx_mf_sim_id', 'simulation_id'),
    )


class MiroFishSimulationRoundRecord(Base):
    """MiroFish仿真轮次记录表"""
    __tablename__ = 'mirofish_simulation_rounds'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    round_number = Column(Integer, comment='轮次编号')
    simulation_env_id = Column(String(64), comment='环境ID')
    posts_generated = Column(Integer, default=0, comment='生成帖子数')
    total_engagement = Column(JSON, comment='互动量统计JSON')
    sentiment_distribution = Column(JSON, comment='情感分布JSON')
    key_events = Column(JSON, comment='关键事件列表JSON')
    network_metrics = Column(JSON, comment='网络指标JSON')
    token_consumed = Column(Float, default=0.0, comment='Token消耗量')
    duration_s = Column(Float, comment='本轮耗时(秒)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_mf_round_num', 'round_number'),
        Index('idx_mf_env_id', 'simulation_env_id'),
    )


class MiroFishReportRecord(Base):
    """MiroFish仿真报告记录表"""
    __tablename__ = 'mirofish_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(64), unique=True, nullable=False, comment='报告唯一标识')
    simulation_id = Column(String(64), comment='仿真ID')
    source_document = Column(Text, comment='源文档摘要')
    executive_summary = Column(Text, comment='执行摘要')
    event_timeline = Column(JSON, comment='事件时间线JSON')
    risk_warnings = Column(JSON, comment='风险预警列表JSON')
    strategy_recommendations = Column(JSON, comment='策略建议列表JSON')
    prediction_confidence = Column(Float, comment='预测置信度(0-1)')
    total_agents = Column(Integer, comment='总智能体数')
    total_rounds = Column(Integer, comment='总轮次数')
    total_tokens = Column(Float, comment='总Token消耗')
    key_insights = Column(JSON, comment='关键洞察列表JSON')
    created_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('idx_mf_report_id', 'report_id'),
        Index('idx_mf_simulation', 'simulation_id'),
    )


class HEASStreamDefRecord(Base):
    """HEAS流定义记录表"""
    __tablename__ = 'heas_stream_defs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stream_id = Column(String(64), unique=True, nullable=False, comment='流唯一标识')
    stream_name = Column(String(100), comment='流名称')
    layer_level = Column(Integer, comment='层级层次 0=底层/1=中层/2=顶层')
    variables = Column(JSON, comment='变量定义JSON')
    read_from = Column(JSON, comment='读取的上游流列表')
    write_to = Column(JSON, comment='写入的下游流列表')
    coupling_strength = Column(Float, comment='耦合强度(0-1)')
    audit_log = Column(JSON, comment='审计日志JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_heas_stream_id', 'stream_id'),
        Index('idx_heas_layer', 'layer_level'),
    )


class HEASEvolutionResultRecord(Base):
    """HEAS进化结果记录表"""
    __tablename__ = 'heas_evolution_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    evolution_id = Column(String(64), unique=True, nullable=False, comment='进化唯一标识')
    strategy = Column(String(50), comment='进化策略')
    generations = Column(Integer, comment='总代数')
    population_size = Column(Integer, comment='种群大小')
    objective_values = Column(JSON, comment='目标函数值JSON')
    pareto_frontier = Column(JSON, comment='Pareto前沿JSON')
    best_solution = Column(JSON, comment='最优解JSON')
    convergence_generation = Column(Integer, comment='收敛代数')
    diversity_metric = Column(Float, comment='多样性指标')
    computation_time_s = Column(Float, comment='计算耗时(秒)')
    audit_trail = Column(JSON, comment='审计追踪JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_heas_evo_id', 'evolution_id'),
        Index('idx_heas_strategy', 'strategy'),
    )


class VirtualEnvInteractionRecord(Base):
    """VirtualEnv物理交互记录表"""
    __tablename__ = 'virtualenv_interactions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    interaction_id = Column(String(64), unique=True, nullable=False, comment='交互唯一标识')
    agent_id = Column(String(100), comment='智能体ID')
    object_id = Column(String(100), comment='物体ID')
    interaction_type = Column(String(30), comment='交互类型：grasp/move/push/pull/collide')
    position_3d_x = Column(Float, comment='X坐标')
    position_3d_y = Column(Float, comment='Y坐标')
    position_3d_z = Column(Float, comment='Z坐标')
    force_applied = Column(Float, comment='施加力(N)')
    success = Column(Boolean, default=False, comment='是否成功')
    physics_metrics = Column(JSON, comment='物理指标JSON')
    duration_ms = Column(Float, comment='交互时长(ms)')
    scenario_type = Column(String(30), comment='场景类型')
    timestamp_sim = Column(String(50), comment='仿真时间戳')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_ve_interaction_id', 'interaction_id'),
        Index('idx_ve_agent', 'agent_id'),
        Index('idx_ve_scenario', 'scenario_type'),
    )


class VirtualEnvNavigationPathRecord(Base):
    """VirtualEnv导航路径记录表"""
    __tablename__ = 'virtualenv_navigation_paths'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    path_id = Column(String(64), unique=True, nullable=False, comment='路径唯一标识')
    agent_id = Column(String(100), comment='智能体ID')
    waypoints = Column(JSON, comment='路径点列表JSON')
    total_distance = Column(Float, comment='总距离(m)')
    time_to_complete_s = Column(Float, comment='完成时间(秒)')
    obstacles_avoided = Column(Integer, default=0, comment='避障数')
    collisions = Column(Integer, default=0, comment='碰撞数')
    smoothness_score = Column(Float, comment='平滑度评分(0-1)')
    efficiency_score = Column(Float, comment='效率评分(0-1)')
    algorithm_used = Column(String(30), comment='算法：astar/rrt/straight')
    scenario_type = Column(String(30), comment='场景类型')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_ve_path_id', 'path_id'),
        Index('idx_ve_nav_agent', 'agent_id'),
    )


class GAMMSGraphStateRecord(Base):
    """GAMMS图仿真状态记录表"""
    __tablename__ = 'gamms_graph_states'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sim_id = Column(String(64), unique=True, nullable=False, comment='仿真唯一标识')
    graph_type = Column(String(50), comment='图类型：road_network/communication/social/power_grid')
    nodes = Column(Integer, comment='节点数')
    edges = Column(Integer, comment='边数')
    agent_positions = Column(JSON, comment='智能体位置映射JSON')
    agent_types = Column(JSON, comment='智能体类型映射JSON')
    step_count = Column(Integer, comment='步进数')
    throughput_per_step = Column(Float, comment='每步吞吐量')
    congestion_levels = Column(JSON, comment='拥堵水平JSON')
    total_cost = Column(Float, default=0.0, comment='总代价')
    fairness_index = Column(Float, comment='Jain公平性指数(0-1)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('idx_gamms_sim_id', 'sim_id'),
        Index('idx_gamms_graph_type', 'graph_type'),
    )


class SimulationHealthStatusRecord(Base):
    """仿真层健康状态记录表"""
    __tablename__ = 'simulation_health_statuses'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    status_id = Column(String(64), unique=True, nullable=False, comment='状态唯一标识')
    mirofish_status = Column(JSON, comment='MiroFish状态JSON')
    heas_status = Column(JSON, comment='HEAS状态JSON')
    virtualenv_status = Column(JSON, comment='VirtualEnv状态JSON')
    gamms_status = Column(JSON, comment='GAMMS状态JSON')
    overall_health = Column(Float, comment='总体健康评分(0-1)')
    active_simulations = Column(Integer, default=0, comment='活跃仿真数')
    total_predictions_made = Column(Integer, default=0, comment='总预测数')
    avg_prediction_accuracy = Column(Float, comment='平均预测准确率')
    recommendations = Column(JSON, comment='建议列表JSON')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('idx_sim_health_id', 'status_id'),
        Index('idx_sim_health_time', 'generated_at'),
    )


# ==================== Part 16: 运维守护层 (Operations Guardian Layer) ====================
# 对应 operations_guardian_layer.py — 炼体(心跳/自愈) + 练器(配置/工具) + 练阵法(集群/容灾)


class OpsHeartbeatRecord(Base):
    """运维-智能体心跳记录表"""
    __tablename__ = 'ops_heartbeat_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(64), unique=True, nullable=False, comment='记录唯一标识')
    agent_id = Column(String(100), nullable=False, comment='智能体ID', index=True)
    process_pid = Column(Integer, comment='进程PID')
    cpu_usage = Column(Float, comment='CPU使用率(0-100%)')
    memory_usage_mb = Column(Float, comment='内存使用量(MB)')
    memory_percent = Column(Float, comment='内存使用率(0-100%)')
    active_tasks = Column(Integer, default=0, comment='活跃任务数')
    queued_tasks = Column(Integer, default=0, comment='排队任务数')
    thread_count = Column(Integer, comment='线程数')
    uptime_seconds = Column(Float, comment='运行时长(秒)')
    status = Column(String(20), comment='健康状态：healthy/degraded/unhealthy/unknown/recovering')
    custom_metrics = Column(JSON, comment='自定义指标JSON')
    timestamp = Column(DateTime, default=datetime.now, comment='心跳时间戳')

    __table_args__ = (
        Index('ops_hb_agent_time', 'agent_id', 'timestamp'),
        Index('ops_hb_timestamp', 'timestamp'),
    )


class OpsSelfCheckResult(Base):
    """运维-自检结果表"""
    __tablename__ = 'ops_self_check_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    check_id = Column(String(64), unique=True, nullable=False, comment='检查唯一标识')
    agent_id = Column(String(100), nullable=False, comment='智能体ID', index=True)
    check_items = Column(JSON, comment='检查项详情JSON列表')
    overall_status = Column(String(20), comment='总体状态：healthy/degraded/unhealthy')
    total_items = Column(Integer, comment='总检查项数')
    passed_items = Column(Integer, comment='通过项数')
    failed_items = Column(Integer, comment='失败项数')
    auto_repaired = Column(Integer, default=0, comment='自动修复项数')
    repair_actions_taken = Column(JSON, comment='已执行修复动作JSON数组')
    warnings = Column(JSON, comment='警告信息JSON数组')
    errors = Column(JSON, comment='错误信息JSON数组')
    duration_ms = Column(Float, comment='检查耗时(ms)')
    next_check_due = Column(DateTime, comment='下次检查时间')
    timestamp = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('ops_sc_agent', 'agent_id'),
        Index('ops_sc_time', 'timestamp'),
    )


class OpsRestartEvent(Base):
    """运维-重启事件表"""
    __tablename__ = 'ops_restart_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(64), unique=True, nullable=False, comment='事件唯一标识')
    agent_id = Column(String(100), nullable=False, comment='智能体ID', index=True)
    reason = Column(String(255), comment='重启原因')
    detected_by = Column(String(64), comment='检测者(门神实例ID)')
    downtime_s = Column(Float, comment='停机时长(秒)')
    restart_method = Column(String(20), comment='重启方式：systemctl/docker/signal/api')
    success = Column(Boolean, default=False, comment='是否成功')
    recovery_time_s = Column(Float, comment='恢复耗时(秒)')
    new_process_pid = Column(Integer, comment='新进程PID')
    audit_trace_id = Column(String(64), comment='审计追踪ID')
    timestamp = Column(DateTime, default=datetime.now, comment='事件时间')

    __table_args__ = (
        Index('ops_restart_agent', 'agent_id'),
        Index('ops_restart_time', 'timestamp'),
    )


class OpsResourceLimit(Base):
    """运维-资源限制定义表"""
    __tablename__ = 'ops_resource_limits'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    limit_id = Column(String(64), unique=True, nullable=False, comment='限制唯一标识')
    target_type = Column(String(30), comment='目标类型：agent/service/pipeline')
    target_id = Column(String(100), comment='目标ID', index=True)
    max_cpu_percent = Column(Float, default=80.0, comment='CPU上限(%)')
    max_memory_mb = Column(Float, default=512.0, comment='内存上限(MB)')
    max_concurrent_tasks = Column(Integer, default=16, comment='最大并发任务数')
    max_disk_io_mb_per_sec = Column(Float, default=100.0, comment='磁盘IO上限(MB/s)')
    max_network_connections = Column(Integer, default=50, comment='最大网络连接数')
    throttle_enabled = Column(Boolean, default=True, comment='是否启用限流')
    enforcement_mode = Column(String(20), comment='执行模式：hard/soft/warn_only')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('ops_limit_target', 'target_type', 'target_id'),
    )


class OpsConfigVersion(Base):
    """运维-配置版本表"""
    __tablename__ = 'ops_config_versions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    version_id = Column(String(64), unique=True, nullable=False, comment='版本唯一标识')
    config_name = Column(String(100), nullable=False, comment='配置名称', index=True)
    version_number = Column(Integer, comment='版本号')
    content_hash = Column(String(32), comment='内容SHA256哈希(前16位)')
    file_path = Column(String(500), comment='原始文件路径')
    file_size_bytes = Column(Integer, comment='文件大小(字节)')
    status = Column(String(20), comment='状态：active/backup/rolled_back/corrupted')
    created_by = Column(String(100), comment='创建者')
    change_description = Column(String(255), comment='变更描述')
    rollback_compatible = Column(Boolean, default=True, comment='是否可回滚')
    metadata = Column(JSON, comment='元数据JSON(含备份路径等)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('ops_ver_config_name', 'config_name'),
        Index('ops_ver_status', 'status'),
    )


class OpsConfigRollbackEvent(Base):
    """运维-配置回滚事件表"""
    __tablename__ = 'ops_config_rollback_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(64), unique=True, nullable=False, comment='事件唯一标识')
    from_version_id = Column(String(64), comment='回滚前版本ID')
    to_version_id = Column(String(64), comment='回滚目标版本ID')
    reason = Column(String(255), comment='回滚原因')
    triggered_by = Column(String(50), comment='触发者：auto/manual')
    success = Column(Boolean, default=False, comment='是否成功')
    service_reloaded = Column(Boolean, default=False, comment='服务是否重载')
    rollback_duration_ms = Column(Float, comment='回滚耗时(ms)')
    pre_rollback_snapshot = Column(String(64), comment='回滚前快照ID')
    audit_log_id = Column(String(64), comment='审计日志ID')
    timestamp = Column(DateTime, default=datetime.now, comment='事件时间')

    __table_args__ = (
        Index('ops_rb_config', 'config_name'),
        Index('ops_rb_time', 'timestamp'),
    )


class OpsToolPermissionEntry(Base):
    """运维-工具权限条目表"""
    __tablename__ = 'ops_tool_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    entry_id = Column(String(64), unique=True, nullable=False, comment='条目唯一标识')
    agent_id = Column(String(100), nullable=False, comment='智能体ID', index=True)
    tool_id = Column(String(100), nullable=False, comment='工具ID', index=True)
    tool_name = Column(String(100), comment='工具名称')
    allowed = Column(Boolean, default=True, comment='是否允许')
    granted_by = Column(String(100), comment='授权人')
    granted_at = Column(DateTime, default=datetime.now, comment='授权时间')
    expires_at = Column(DateTime, comment='过期时间')
    usage_count = Column(Integer, default=0, comment='使用次数')
    last_used_at = Column(DateTime, comment='最后使用时间')
    conditions = Column(JSON, comment='附加条件JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('ops_perm_agent_tool', 'agent_id', 'tool_id'),
    )


class OpsToolInvocationAudit(Base):
    """运维-工具调用审计记录表"""
    __tablename__ = 'ops_tool_invocation_audits'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    audit_id = Column(String(64), unique=True, nullable=False, comment='审计唯一标识')
    agent_id = Column(String(100), nullable=False, comment='智能体ID', index=True)
    tool_id = Column(String(100), nullable=False, comment='工具ID', index=True)
    tool_name = Column(String(100), comment='工具名称')
    invocation_result = Column(String(20), comment='调用结果：allowed/denied/pending_review')
    request_params_hash = Column(String(32), comment='请求参数哈希')
    response_time_ms = Column(Float, comment='响应时间(ms)')
    denied_reason = Column(String(255), comment='拒绝原因')
    trace_id = Column(String(64), comment='追踪ID')
    timestamp = Column(DateTime, default=datetime.now, comment='审计时间')

    __table_args__ = (
        Index('ops_audit_agent', 'agent_id'),
        Index('ops_audit_tool', 'tool_id'),
        Index('ops_audit_time', 'timestamp'),
    )


class OpsGatewayHealthRecord(Base):
    """运维-网关健康记录表"""
    __tablename__ = 'ops_gateway_health_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(64), unique=True, nullable=False, comment='记录唯一标识')
    gateway_id = Column(String(100), nullable=False, comment='网关ID', index=True)
    role = Column(String(20), comment='角色：primary/standby/failover/unknown')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    vip_bound = Column(Boolean, default=False, comment='是否绑定VIP')
    connections_active = Column(Integer, default=0, comment='活跃连接数')
    requests_per_second = Column(Float, comment='每秒请求数(RPS)')
    avg_response_time_ms = Column(Float, comment='平均响应时间(ms)')
    error_rate = Column(Float, comment='错误率(0-1)')
    memory_usage_mb = Column(Float, comment='内存使用量(MB)')
    cpu_usage = Column(Float, comment='CPU使用率(%)')
    last_heartbeat = Column(DateTime, comment='最后心跳时间')
    failover_history = Column(JSON, comment='故障转移历史JSON数组')
    timestamp = Column(DateTime, default=datetime.now, comment='记录时间')

    __table_args__ = (
        Index('ops_gw_gateway', 'gateway_id'),
        Index('ops_gw_time', 'timestamp'),
    )


class OpsFailoverEvent(Base):
    """运维-故障转移事件表"""
    __tablename__ = 'ops_failover_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(64), unique=True, nullable=False, comment='事件唯一标识')
    primary_gateway_id = Column(String(100), comment='原主网关ID')
    standby_gateway_id = Column(String(100), comment='接管备用网关ID')
    trigger_reason = Column(String(255), comment='触发原因')
    detection_time_s = Column(Float, comment='检测耗时(秒)')
    switchover_time_s = Column(Float, comment='切换耗时(秒)')
    total_downtime_s = Column(Float, comment='总停机时间(秒)')
    requests_lost = Column(Integer, default=0, comment='丢失请求数')
    requests_redirected = Column(Integer, default=0, comment='重定向请求数')
    success = Column(Boolean, default=False, comment='是否成功')
    notification_sent = Column(Boolean, default=False, comment='是否已发送通知')
    timestamp = Column(DateTime, default=datetime.now, comment='事件时间')

    __table_args__ = (
        Index('ops_fo_primary', 'primary_gateway_id'),
        Index('ops_fo_time', 'timestamp'),
    )


class OpsGuardianClusterMember(Base):
    """运维-守护集群成员表"""
    __tablename__ = 'ops_guardian_cluster_members'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    member_id = Column(String(64), unique=True, nullable=False, comment='成员唯一标识')
    instance_id = Column(String(64), comment='实例ID')
    endpoint = Column(String(200), comment='端点地址')
    role = Column(String(20), comment='角色：leader/follower/candidate')
    is_alive = Column(Boolean, default=True, comment='是否存活')
    monitored_agents = Column(Integer, default=0, comment='监控的智能体数')
    last_peer_heartbeat = Column(DateTime, comment='最后对端心跳时间')
    term = Column(Integer, default=0, comment='任期号')
    vote_count = Column(Integer, default=0, comment='得票数')
    uptime_seconds = Column(Float, default=0.0, comment='运行时长(秒)')
    health_check_errors = Column(Integer, default=0, comment='健康检查错误次数')
    timestamp = Column(DateTime, default=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('ops_cluster_member', 'member_id'),
        Index('ops_cluster_role', 'role'),
    )


class OpsClusterSnapshot(Base):
    """运维-集群系统快照表"""
    __tablename__ = 'ops_cluster_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(64), unique=True, nullable=False, comment='快照唯一标识')
    snapshot_type = Column(String(20), comment='类型：scheduled/manual/pre_deployment/emergency')
    db_schema_hash = Column(String(32), comment='数据库Schema哈希')
    config_versions = Column(JSON, comment='配置版本映射JSON(config_name->version_id)')
    agent_registry = Column(JSON, comment='智能体注册表状态JSON')
    tool_permissions = Column(JSON, comment='工具权限状态JSON')
    gateway_config = Column(JSON, comment='网关配置JSON')
    system_metrics = Column(JSON, comment='系统指标JSON')
    total_size_bytes = Column(Integer, comment='原始大小(字节)')
    compressed_size_bytes = Column(Integer, comment='压缩后大小(字节)')
    storage_location = Column(String(300), comment='存储位置')
    retention_days = Column(Integer, default=7, comment='保留天数')
    checksum = Column(String(64), comment='SHA256校验和')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('ops_snap_id', 'snapshot_id'),
        Index('ops_snap_type', 'snapshot_type'),
        Index('ops_snap_time', 'created_at'),
    )


class OpsFaultInjectionTestResult(Base):
    """运维-故障注入测试结果表"""
    __tablename__ = 'ops_fault_injection_test_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    test_id = Column(String(64), unique=True, nullable=False, comment='测试唯一标识')
    scenario = Column(String(50), comment='故障场景：process_hang/config_corrupt/gateway_down/disk_full/permission_breach')
    injected = Column(Boolean, default=False, comment='是否已注入')
    detection_time_s = Column(Float, comment='检测耗时(秒)')
    recovery_time_s = Column(Float, comment='恢复耗时(秒)')
    auto_recovery = Column(Boolean, default=False, comment='是否自动恢复')
    human_intervention_required = Column(Boolean, default=False, comment='是否需要人工介入')
    data_loss = Column(Boolean, default=False, comment='是否有数据丢失')
    service_degradation_pct = Column(Float, comment='服务降级百分比(%)')
    passed = Column(Boolean, default=False, comment='是否通过')
    details = Column(JSON, comment='详细结果JSON')
    test_duration_s = Column(Float, comment='测试总时长(秒)')
    timestamp = Column(DateTime, default=datetime.now, comment='测试时间')

    __table_args__ = (
        Index('ops_fit_scenario', 'scenario'),
        Index('ops_fit_time', 'timestamp'),
    )


class OperationsDashboardDataRecord(Base):
    """运维-看板数据记录表"""
    __tablename__ = 'operations_dashboard_data'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dashboard_id = Column(String(64), unique=True, nullable=False, comment='看板唯一标识')
    overall_health_score = Column(Float, comment='总体健康评分(0-100)')
    agent_health_summary = Column(JSON, comment='智能体健康摘要JSON')
    config_health_summary = Column(JSON, comment='配置健康摘要JSON')
    cluster_health_summary = Column(JSON, comment='集群健康摘要JSON')
    recent_alerts = Column(JSON, comment='最近告警JSON数组')
    recent_restart_events = Column(JSON, comment='最近重启事件JSON数组')
    recent_fault_tests = Column(JSON, comment='最近故障测试JSON数组')
    resource_utilization = Column(JSON, comment='资源利用率JSON')
    uptime_stats = Column(JSON, comment='运行时间统计JSON')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('ops_dash_time', 'generated_at'),
    )


# ==================== Part 17: 用户转化优化层 (User Conversion Optimization Layer) ====================
# 对应 user_conversion_layer.py — 行为采集+转化漏斗+停留分析+爆火引擎+AB实验+推荐优化


class ConvBehaviorEvent(Base):
    """转化-用户行为事件原始表"""
    __tablename__ = 'conv_behavior_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(64), unique=True, nullable=False, comment='事件唯一标识')
    user_id = Column(String(100), nullable=False, comment='用户ID', index=True)
    session_id = Column(String(100), comment='会话ID', index=True)
    event_type = Column(String(30), comment='事件类型：page_view/page_leave/click/scroll/form_submit/consult_start/consult_complete/report_generate/share/feedback_like/dislike/score')
    page_path = Column(String(300), comment='页面路径', index=True)
    element_id = Column(String(100), comment='元素ID')
    element_text = Column(String(200), comment='元素文本')
    metadata = Column(JSON, comment='元数据JSON')
    client_timestamp = Column(DateTime, comment='客户端时间戳')
    device_type = Column(String(20), comment='设备类型：mobile/pc/tablet/unknown')
    referrer = Column(String(500), comment='来源页面')
    duration_ms = Column(Float, default=0.0, comment='持续时长(ms)')
    scroll_depth_pct = Column(Float, default=0.0, comment='滚动深度百分比')
    viewport_size = Column(String(20), comment='视口尺寸')
    user_agent = Column(String(500), comment='User-Agent')
    timestamp = Column(DateTime, default=datetime.now, comment='服务端记录时间')

    __table_args__ = (
        Index('conv_be_user_session', 'user_id', 'session_id'),
        Index('conv_be_event_type', 'event_type'),
        Index('conv_be_timestamp', 'timestamp'),
        Index('conv_be_page_type', 'page_path', 'event_type'),
    )


class ConvUserSession(Base):
    """转化-用户会话聚合表"""
    __tablename__ = 'conv_user_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(100), unique=True, nullable=False, comment='会话唯一标识')
    user_id = Column(String(100), nullable=False, comment='用户ID', index=True)
    start_time = Column(DateTime, comment='会话开始时间')
    end_time = Column(DateTime, comment='会话结束时间')
    event_count = Column(Integer, default=0, comment='事件总数')
    page_views = Column(Integer, default=0, comment='页面浏览数')
    unique_pages = Column(Integer, default=0, comment='独立页面数')
    page_list = Column(JSON, comment='访问页面列表JSON')
    click_count = Column(Integer, default=0, comment='点击次数')
    scroll_max_depth_pct = Column(Float, default=0.0, comment='最大滚动深度%')
    consultation_started = Column(Integer, default=0, comment='咨询开始次数')
    consultation_completed = Column(Integer, default=0, comment='咨询完成次数')
    forms_submitted = Column(Integer, default=0, comment='表单提交数')
    feedback_count = Column(Integer, default=0, comment='反馈次数')
    share_count = Column(Integer, default=0, comment='分享次数')
    report_generated = Column(Integer, default=0, comment='报告生成数')
    converted = Column(Boolean, default=False, comment='是否转化')
    conversion_stage = Column(String(20), comment='转化阶段：exposure/dwell/interaction/conversion/retention')
    device_type = Column(String(20), comment='设备类型')
    total_duration_ms = Column(Float, default=0.0, comment='总时长(ms)')
    engagement_score = Column(Float, default=0.0, comment='参与度评分(0-100)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('conv_sess_user', 'user_id'),
        Index('conv_sess_converted', 'converted'),
        Index('conv_sess_device', 'device_type'),
    )


class ConvFunnelSnapshot(Base):
    """转化-漏斗快照表"""
    __tablename__ = 'conv_funnel_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    funnel_id = Column(String(64), comment='漏斗唯一标识')
    stage = Column(String(20), comment='漏斗阶段：exposure/dwell/interaction/conversion/retention')
    total_users = Column(Integer, default=0, comment='总用户数')
    stage_users = Column(Integer, default=0, comment='阶段用户数')
    conversion_rate = Column(Float, default=0.0, comment='转化率(%)')
    drop_off_count = Column(Integer, default=0, comment='流失人数')
    drop_off_rate = Column(Float, default=0.0, comment='流失率(%)')
    avg_time_in_stage_s = Column(Float, default=0.0, comment='阶段平均停留(s)')
    segment_breakdown = Column(JSON, comment='分群下钻数据JSON')
    snapshot_time = Column(DateTime, default=datetime.now, comment='快照时间')

    __table_args__ = (
        Index('conv_funnel_id_stage', 'funnel_id', 'stage'),
        Index('conv_funnel_time', 'snapshot_time'),
    )


class ConvDwellTimeRecord(Base):
    """转化-停留时长记录表"""
    __tablename__ = 'conv_dwell_time_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(64), unique=True, nullable=False, comment='记录唯一标识')
    user_id = Column(String(100), comment='用户ID', index=True)
    session_id = Column(String(100), comment='会话ID')
    page_path = Column(String(300), comment='页面路径', index=True)
    region_id = Column(String(50), comment='区域ID')
    region_name = Column(String(100), comment='区域名称')
    dwell_time_ms = Column(Float, comment='停留时长(ms)')
    enter_time = Column(DateTime, comment='进入时间')
    leave_time = Column(DateTime, comment='离开时间')
    click_count = Column(Integer, default=0, comment='区域内点击数')
    scroll_events = Column(Integer, default=0, comment='滚动事件数')
    interaction_score = Column(Float, default=0.0, comment='交互评分')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('conv_dwell_page_region', 'page_path', 'region_id'),
        Index('conv_dwell_user', 'user_id'),
    )


class ConvHeatmapCellRecord(Base):
    """转化-热力图单元格聚合表"""
    __tablename__ = 'conv_heatmap_cells'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    page_path = Column(String(300), comment='页面路径')
    region_id = Column(String(50), comment='区域ID', index=True)
    region_name = Column(String(100), comment='区域名称')
    total_dwell_ms = Column(Float, default=0.0, comment='总停留时长(ms)')
    visit_count = Column(Integer, default=0, comment='访问次数')
    avg_dwell_ms = Column(Float, default=0.0, comment='平均停留时长(ms)')
    click_count = Column(Integer, default=0, comment='总点击数')
    click_rate = Column(Float, default=0.0, comment='点击率(%)')
    intensity = Column(Float, default=0.0, comment='热力强度(0-100)')
    coordinates_x = Column(Integer, comment='X坐标')
    coordinates_y = Column(Integer, comment='Y坐标')
    snapshot_date = Column(Date, comment='快照日期')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('conv_heatmap_page', 'page_path'),
        Index('conv_heatmap_date', 'snapshot_date'),
    )


class ConvViralContentItem(Base):
    """转化-爆火内容项表"""
    __tablename__ = 'conv_viral_content_items'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    content_id = Column(String(64), unique=True, nullable=False, comment='内容唯一标识')
    content_type = Column(String(30), comment='内容类型')
    title = Column(String(200), comment='标题')
    exposure_count = Column(Integer, default=0, comment='曝光量')
    completion_rate = Column(Float, default=0.0, comment='完播率(%)')
    interaction_rate = Column(Float, default=0.0, comment='互动率(%)')
    share_rate = Column(Float, default=0.0, comment='转发率(%)')
    viral_score = Column(Float, default=0.0, comment='爆火分数(0-100)')
    viral_tier = Column(String(15), comment='爆火等级：normal/warming/hot/viral/explosive')
    trend_direction = Column(String(10), comment='趋势方向：rising/stable/declining')
    velocity_24h = Column(Float, default=0.0, comment='24h速度变化')
    velocity_7d = Column(Float, default=0.0, comment='7d速度变化')
    peak_rank = Column(Integer, default=0, comment='历史最高排名')
    current_rank = Column(Integer, default=0, comment='当前排名')
    lifecycle_phase = Column(String(15), comment='生命周期阶段：growth/peak/decline')
    metadata = Column(JSON, comment='元数据JSON')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('conv_viral_score', 'viral_score'),
        Index('conv_viral_tier', 'viral_tier'),
        Index('conv_viral_type', 'content_type'),
    )


class ConvRecommendationResult(Base):
    """转化-推荐结果表"""
    __tablename__ = 'conv_recommendation_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    recommendation_id = Column(String(64), unique=True, nullable=False, comment='推荐唯一标识')
    user_id = Column(String(100), nullable=False, comment='用户ID', index=True)
    source = Column(String(25), comment='推荐来源：collaborative_filter/content_based/trending/personalized/cold_start/ab_test')
    item_ids = Column(JSON, comment='推荐内容ID列表JSON')
    confidence_scores = Column(JSON, comment='置信度分数列表JSON')
    explanation = Column(String(300), comment='推荐解释')
    model_version = Column(String(20), comment='模型版本')
    latency_ms = Column(Float, comment='生成延迟(ms)')
    clicked_item_id = Column(String(64), comment='用户点击的内容ID')
    clicked_at = Column(DateTime, comment='点击时间')
    timestamp = Column(DateTime, default=datetime.now, comment='推荐时间')

    __table_args__ = (
        Index('conv_rec_user_time', 'user_id', 'timestamp'),
        Index('conv_rec_source', 'source'),
    )


class ConvABExperiment(Base):
    """转化-AB实验表"""
    __tablename__ = 'conv_ab_experiments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    experiment_id = Column(String(64), unique=True, nullable=False, comment='实验唯一标识')
    name = Column(String(200), comment='实验名称')
    description = Column(Text, comment='实验描述')
    hypothesis = Column(Text, comment='实验假设')
    primary_metric = Column(String(50), comment='主要指标')
    secondary_metrics = Column(JSON, comment='次要指标列表JSON')
    variants_config = Column(JSON, comment='变体配置JSON')
    traffic_allocation = Column(JSON, comment='流量分配JSON(variant_id->ratio)')
    status = Column(String(15), comment='状态：draft/running/paused/completed/analyzing')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    sample_sizes = Column(JSON, comment='各变体样本量JSON')
    results_summary = Column(JSON, comment='结果摘要JSON')
    winner_variant_id = Column(String(64), comment='胜出变体ID')
    p_value = Column(Float, comment='P值')
    confidence_level = Column(Float, default=0.95, comment='置信水平')
    min_detectable_effect = Column(Float, default=0.05, comment='最小检测效应(MDE)')
    statistical_power = Column(Float, default=0.8, comment='统计功效')
    is_significant = Column(Boolean, default=False, comment='是否显著')
    created_by = Column(String(100), comment='创建者')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('conv_ab_status', 'status'),
        Index('conv_ab_created', 'created_at'),
    )


class ConvABAssignmentLog(Base):
    """转化-AB实验分配日志表"""
    __tablename__ = 'conv_ab_assignment_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    experiment_id = Column(String(64), comment='实验ID', index=True)
    user_id = Column(String(100), comment='用户ID', index=True)
    variant_id = Column(String(64), comment='分配的变体ID', index=True)
    assigned_at = Column(DateTime, default=datetime.now, comment='分配时间')
    converted = Column(Boolean, default=False, comment='是否转化')
    metric_value = Column(Float, comment='指标值')

    __table_args__ = (
        Index('conv_ab_assign_exp_user', 'experiment_id', 'user_id'),
    )


class ConvABMetricSnapshot(Base):
    """转化-AB实验指标快照表"""
    __tablename__ = 'conv_ab_metric_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    experiment_id = Column(String(64), comment='实验ID', index=True)
    variant_id = Column(String(64), comment='变体ID', index=True)
    metric_name = Column(String(50), comment='指标名')
    value = Column(Float, comment='指标值')
    timestamp = Column(DateTime, default=datetime.now, comment='记录时间')

    __table_args__ = (
        Index('conv_ab_ms_exp_variant_metric', 'experiment_id', 'variant_id', 'metric_name'),
    )


class ConvOptimizationSuggestion(Base):
    """转化-优化建议表"""
    __tablename__ = 'conv_optimization_suggestions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    suggestion_id = Column(String(64), unique=True, nullable=False, comment='建议唯一标识')
    category = Column(String(30), comment='建议类别')
    priority = Column(String(10), comment='优先级：高/中/低')
    title = Column(String(200), comment='建议标题')
    description = Column(Text, comment='详细描述')
    expected_impact_pct = Column(Float, comment='预期提升(%)')
    effort_level = Column(String(10), comment='实施难度：低/中/高')
    current_baseline = Column(Float, comment='当前基线值')
    target_value = Column(Float, comment='目标值')
    related_funnel_stage = Column(String(20), comment='关联漏斗阶段')
    evidence_data = Column(JSON, comment='证据数据JSON')
    ab_test_ready = Column(Boolean, default=True, comment='是否可AB测试')
    status = Column(String(15), default='pending', comment='状态：pending/implementing/completed/dismissed')
    implemented_by = Column(String(100), comment='实施者')
    actual_impact_pct = Column(Float, comment='实际提升(%)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('conv_sugg_priority', 'priority'),
        Index('conv_sugg_category', 'category'),
        Index('conv_sugg_status', 'status'),
    )


class ConvAHAMomentRecord(Base):
    """转化-AHA时刻识别表"""
    __tablename__ = 'conv_aha_moments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    moment_id = Column(String(64), unique=True, nullable=False, comment='时刻唯一标识')
    user_id = Column(String(100), comment='用户ID', index=True)
    session_id = Column(String(100), comment='会话ID')
    aha_event_type = Column(String(30), comment='AHA事件类型：consultation_complete/report_generate/form_submit')
    triggering_actions = Column(JSON, comment='触发动作序列JSON')
    time_to_convert_s = Column(Float, comment='从进入到转化的耗时(秒)')
    page_at_moment = Column(String(300), comment='转化发生时的页面')
    agent_name = Column(String(50), comment='关联智能体名称')
    timestamp = Column(DateTime, default=datetime.now, comment='记录时间')

    __table_args__ = (
        Index('conv_aha_user', 'user_id'),
        Index('conv_aha_event', 'aha_event_type'),
    )


class ConvDashboardSnapshot(Base):
    """转化-看板快照表"""
    __tablename__ = 'conv_dashboard_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dashboard_id = Column(String(64), unique=True, nullable=False, comment='看板唯一标识')
    overall_conversion_rate = Column(Float, comment='总体转化率(%)')
    funnel_snapshot_json = Column(JSON, comment='漏斗数据JSON')
    heatmap_top_regions = Column(JSON, comment='热力图TOP区域JSON')
    viral_top_content = Column(JSON, comment='爆火TOP内容JSON')
    active_experiments_summary = Column(JSON, comment='活跃实验摘要JSON')
    key_metrics = Column(JSON, comment='关键指标JSON')
    total_sessions_analyzed = Column(Integer, default=0, comment='分析的总会话数')
    bounce_rate = Column(Float, default=0.0, comment='跳出率(%)')
    avg_engagement_score = Column(Float, default=0.0, comment='平均参与度')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('conv_dash_generated', 'generated_at'),
    )


# ==================== Part 18: 推广变现层 (Promotion & Monetization Layer) ====================
# 对应 promotion_monetization_layer.py — 五端市场+智能体工时定价+内容营销+生态合作+商业化产品+变现节奏


class PromoMarketSegmentProfile(Base):
    """推广-市场细分画像表"""
    __tablename__ = 'promo_market_segments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    segment_id = Column(String(64), unique=True, nullable=False, comment='细分唯一标识')
    segment_name = Column(String(20), comment='细分名称：enterprise/academic/government/association/public')
    priority_stars = Column(Integer, default=1, comment='优先级(1-5星)')
    core_product = Column(String(200), comment='核心产品')
    pricing_model = Column(String(100), comment='定价模型')
    target_user_size = Column(String(100), comment='目标用户规模')
    estimated_tam_wan = Column(Float, default=0.0, comment='总可寻址市场(万元)')
    estimated_sam_wan = Column(Float, default=0.0, comment='可获得市场(万元)')
    conversion_rate_est = Column(Float, default=0.0, comment='预估转化率')
    avg_contract_value = Column(Float, default=0.0, comment='平均合同价值')
    sales_cycle_days = Column(Integer, default=0, comment='销售周期(天)')
    key_pain_points = Column(JSON, comment='关键痛点JSON数组')
    value_proposition = Column(Text, comment='价值主张')
    go_to_market_strategy = Column(Text, comment='进入市场策略')
    opportunity_score = Column(Float, default=0.0, comment='机会评分(0-100)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('promo_seg_priority', 'priority_stars'),
        Index('promo_seg_name', 'segment_name'),
    )


class PromoAgentWorkHour(Base):
    """推广-智能体工时记录表"""
    __tablename__ = 'promo_work_hours'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    work_id = Column(String(64), unique=True, nullable=False, comment='工时记录唯一标识')
    user_id = Column(String(100), nullable=False, comment='用户ID', index=True)
    task_type = Column(String(50), comment='任务类型')
    task_description = Column(String(300), comment='任务描述')
    agent_name = Column(String(50), comment='执行智能体名称')
    hours_consumed = Column(Float, comment='消耗工时数')
    token_count = Column(Integer, comment='Token数量')
    complexity_factor = Column(Float, default=1.0, comment='复杂度因子(0.5-2.0)')
    base_rate_per_hour = Column(Float, comment='基础费率(元/小时)')
    total_cost_cny = Column(Float, comment='总费用(元)')
    value_delivered_cny = Column(Float, comment='交付价值(元)')
    pricing_tier = Column(String(15), comment='定价层级：free/basic/professional/enterprise/custom')
    timestamp = Column(DateTime, default=datetime.now, comment='记录时间')

    __table_args__ = (
        Index('promo_wh_user_time', 'user_id', 'timestamp'),
        Index('promo_wh_task_type', 'task_type'),
    )


class PromoPricingPlan(Base):
    """推广-定价方案表"""
    __tablename__ = 'promo_pricing_plans'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    plan_id = Column(String(64), unique=True, nullable=False, comment='方案唯一标识')
    tier_name = Column(String(20), comment='层级名称：探索版/基础版/专业版/企业版/定制版')
    display_name = Column(String(50), comment='展示名称')
    monthly_work_hours = Column(Integer, comment='每月工时额度(-1表示不限)')
    monthly_price_cny = Column(Float, default=0.0, comment='月费(元)')
    annual_price_cny = Column(Float, comment='年费(元)')
    included_features = Column(JSON, comment='包含功能JSON列表')
    agent_types_included = Column(JSON, comment='包含智能体JSON列表')
    api_calls_limit = Column(Integer, default=0, comment='API调用限额')
    report_quota = Column(Integer, default=0, comment='报告配额(-1不限)')
    consultation_quota = Column(Integer, default=0, comment='咨询配额(-1不限)')
    support_level = Column(String(20), comment='支持级别')
    sla_guarantee = Column(String(100), comment='SLA保障承诺')
    discount_for_annual = Column(Float, default=0.0, comment='年付折扣比例')
    trial_days = Column(Integer, default=0, comment='试用天数')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('promo_plan_tier', 'tier_name'),
    )


class PromoPointsTransaction(Base):
    """推广-积分交易记录表"""
    __tablename__ = 'promo_points_transactions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    transaction_id = Column(String(64), unique=True, nullable=False, comment='交易唯一标识')
    user_id = Column(String(100), nullable=False, comment='用户ID', index=True)
    transaction_type = Column(String(15), comment='交易类型：earn/redeem/expire/adjust')
    points_delta = Column(Integer, comment='积分变动量(正增负减)')
    balance_after = Column(Integer, comment='变动后余额')
    reason = Column(String(200), comment='原因说明')
    related_work_hours = Column(Float, comment='关联工时数')
    related_product_id = Column(String(64), comment='关联产品ID')
    expires_at = Column(DateTime, comment='过期时间')
    timestamp = Column(DateTime, default=datetime.now, comment='交易时间')

    __table_args__ = (
        Index('promo_pts_user_type', 'user_id', 'transaction_type'),
        Index('promo_pts_timestamp', 'timestamp'),
    )


class PromoContentPiece(Base):
    """推广-内容作品表"""
    __tablename__ = 'promo_content_pieces'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    content_id = Column(String(64), unique=True, nullable=False, comment='内容唯一标识')
    title = Column(String(200), comment='标题')
    content_type = Column(String(20), comment='内容类型：tech_article/case_study/video_short/tutorial/whitepaper/press_release/social_post')
    channel = Column(String(20), comment='发布渠道')
    author = Column(String(50), comment='作者')
    status = Column(String(15), default='draft', comment='状态：draft/published/archived')
    publish_date = Column(DateTime, comment='发布日期')
    word_count = Column(Integer, default=0, comment='字数')
    views = Column(Integer, default=0, comment='阅读量')
    likes = Column(Integer, default=0, comment='点赞数')
    shares = Column(Integer, default=0, comment='分享数')
    comments = Column(Integer, default=0, comment='评论数')
    ctr = Column(Float, default=0.0, comment='点击转化率(%)')
    conversions = Column(Integer, default=0, comment='转化数')
    seo_score = Column(Float, default=0.0, comment='SEO评分(0-100)')
    tags = Column(JSON, comment='标签JSON数组')
    url = Column(String(500), comment='链接URL')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('promo_cont_type_status', 'content_type', 'status'),
        Index('promo_cont_published', 'publish_date'),
    )


class PromoPartnershipRecord(Base):
    """推广-合作记录表"""
    __tablename__ = 'promo_partnerships'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    partnership_id = Column(String(64), unique=True, nullable=False, comment='合作唯一标识')
    partner_name = Column(String(100), comment='合作伙伴名称')
    partner_type = Column(String(20), comment='伙伴类型：university/enterprise/association/developer/media')
    market_segment = Column(String(15), comment='目标市场细分')
    status = Column(String(15), default='prospecting', comment='状态：prospecting/negotiating/active/paused/terminated')
    cooperation_mode = Column(String(30), comment='合作模式：data_exchange/joint_product/reseller/certification/white_label/content_syndication/marketplace_commission')
    terms_summary = Column(Text, comment='条款摘要')
    revenue_share_pct = Column(Float, default=0.0, comment='收入分成比例')
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    contacts = Column(JSON, contact='联系人信息JSON数组')
    milestones = Column(JSON, comment='里程碑JSON数组')
    total_revenue_generated = Column(Float, default=0.0, comment='累计产生收入')
    leads_generated = Column(Integer, default=0, comment='累计带来线索')
    notes = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('promo_partner_type', 'partner_type'),
        Index('promo_partner_status', 'status'),
        Index('promo_partner_segment', 'market_segment'),
    )


class PromoCommercialProduct(Base):
    """推广-商业化产品表"""
    __tablename__ = 'promo_commercial_products'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    product_id = Column(String(64), unique=True, nullable=False, comment='产品唯一标识')
    name = Column(String(100), comment='产品名称')
    category = Column(String(25), comment='产品类别：standard_product/industry_solution/value_added_service/api_service/deployment_service/certification_training')
    target_segment = Column(String(15), comment='目标市场细分')
    pricing_model = Column(String(20), comment='定价模式：subscription/per_task/per_user/project')
    base_price_cny = Column(Float, default=0.0, comment='基础价格(元)')
    price_range = Column(String(30), comment='价格区间描述')
    description = Column(Text, comment='产品描述')
    features = Column(JSON, comment='功能特性JSON列表')
    included_agents = Column(JSON, comment='包含智能体JSON列表')
    deployment_type = Column(String(10), default='cloud', comment='部署方式：cloud/hybrid/on-premise')
    customization_level = Column(String(15), default='standard', comment='定制程度：standard/semi-custom/full-custom')
    competitors = Column(JSON, comment='竞品JSON列表')
    differentiation = Column(String(200), comment='差异化卖点')
    sales_count = Column(Integer, default=0, comment='销量')
    revenue_total = Column(Float, default=0.0, comment='累计收入')
    avg_rating = Column(Float, default=0.0, comment='平均评分(0-5)')
    review_count = Column(Integer, default=0, comment='评价数')
    is_active = Column(Boolean, default=True, comment='是否在售')
    launch_date = Column(DateTime, comment='上市日期')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('promo_prod_category', 'category'),
        Index('promo_prod_segment', 'target_segment'),
        Index('promo_prod_active', 'is_active'),
    )


class PromoRevenueRecord(Base):
    """推广-收入记录表"""
    __tablename__ = 'promo_revenue_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(64), unique=True, nullable=False, comment='记录唯一标识')
    date = Column(Date, comment='日期')
    market_segment = Column(String(15), comment='市场细分')
    product_id = Column(String(64), comment='产品ID', index=True)
    product_name = Column(String(100), comment='产品名称')
    customer_id = Column(String(100), comment='客户ID')
    customer_name = Column(String(100), comment='客户名称')
    amount_cpy = Column(Float, comment='金额(元)')
    pricing_tier = Column(String(15), comment='定价层级')
    payment_method = Column(String(20), comment='支付方式：alipay/wechat/bank_transfer/invoice')
    subscription_month = Column(Integer, comment='订阅月数')
    is_recurring = Column(Boolean, default=False, comment='是否为续费')
    commission_deducted = Column(Float, default=0.0, comment='扣除佣金')
    net_revenue = Column(Float, comment='净收入')
    sales_channel = Column(String(25), comment='销售渠道')
    sales_rep = Column(String(50), comment='销售人员')
    notes = Column(String(300), comment='备注')
    timestamp = Column(DateTime, default=datetime.now, comment='记录时间')

    __table_args__ = (
        Index('promo_rev_date', 'date'),
        Index('promo_rev_customer', 'customer_id'),
        Index('promo_rev_segment', 'market_segment'),
    )


class PromoLeadRecord(Base):
    """推广-销售线索表"""
    __tablename__ = 'promo_lead_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    lead_id = Column(String(64), unique=True, nullable=False, comment='线索唯一标识')
    company_name = Column(String(100), comment='公司/机构名称')
    market_segment = Column(String(15), comment='所属市场细分')
    contact_person = Column(String(50), comment='联系人')
    contact_info = Column(String(100), comment='联系方式')
    source_channel = Column(String(25), comment='来源渠道')
    status = Column(String(15), default='new', comment='状态：new/contacted/qualified/proposal/negotiation/won/lost')
    value_estimate = Column(Float, default=0.0, comment='预估合同价值')
    assigned_to = Column(String(50), comment='负责人')
    notes = Column(Text, comment='跟进备注')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('promo_lead_segment', 'market_segment'),
        Index('promo_lead_status', 'status'),
        Index('promo_lead_source', 'source_channel'),
    )


class PromoMonetizationMilestone(Base):
    """推广-变现里程碑表"""
    __tablename__ = 'promo_milestones'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    milestone_id = Column(String(64), unique=True, nullable=False, comment='里程碑唯一标识')
    phase_name = Column(String(15), comment='阶段名称：validation/launch/expansion/maturity')
    display_name = Column(String(50), comment='展示名称')
    target_date = Column(Date, comment='目标完成日期')
    target_revenue_cpy = Column(Float, default=0.0, comment='目标收入(元)')
    actual_revenue_cpy = Column(Float, default=0.0, comment='实际收入(元)')
    target_customers = Column(Integer, default=0, comment='目标客户数')
    actual_customers = Column(Integer, default=0, comment='实际客户数')
    key_actions = Column(JSON, comment='关键行动JSON列表')
    completed_actions = Column(JSON, comment='已完成行动JSON列表')
    status = Column(String(15), default='pending', comment='状态：pending/in_progress/completed/overdue')
    progress_pct = Column(Float, default=0.0, comment='进度百分比(0-100)')
    achieved_at = Column(DateTime, comment='达成时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('promo_ms_phase', 'phase_name'),
        Index('promo_ms_status', 'status'),
    )


class PromoDashboardSnapshot(Base):
    """推广-变现看板快照表"""
    __tablename__ = 'promo_dashboard_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dashboard_id = Column(String(64), unique=True, nullable=False, comment='看板唯一标识')
    date_range = Column(String(20), comment='数据时间范围')
    total_revenue_cpy = Column(Float, comment='总收入(元)')
    mrr_cpy = Column(Float, comment='月经常性收入(元)')
    arr_cpy = Column(Float, comment='年经常性收入(元)估算')
    paying_customers = Column(Integer, default=0, comment='付费客户数')
    trial_customers = Column(Integer, default=0, comment='试用客户数')
    conversion_trial_to_paid = Column(Float, default=0.0, comment='试用→付费转化率(%)')
    revenue_by_segment = Column(JSON, comment='分市场收入JSON')
    revenue_by_product = Column(JSON, comment='分产品收入JSON')
    revenue_by_channel = Column(JSON, comment='分渠道收入JSON')
    active_partnerships = Column(Integer, default=0, comment='活跃合作数')
    content_published_count = Column(Integer, default=0, comment='本月内容发布数')
    content_total_views = Column(Integer, default=0, comment='内容总阅读量')
    points_issued_total = Column(Integer, default=0, comment='积分发放总量')
    points_redeemed_total = Column(Integer, default=0, comment='积分兑换总量')
    work_hours_total = Column(Float, default=0.0, comment='工时消耗总量')
    current_phase = Column(String(15), comment='当前变现阶段')
    phase_progress_json = Column(JSON, comment='阶段进度详情JSON')
    recommendations = Column(JSON, comment='AI优化建议JSON数组')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('promo_dash_generated', 'generated_at'),
    )


# ==================== Part 19: 数据闭环层 (Data Closed-Loop Layer) ====================
# 对应 data_closed_loop_layer.py — 一分二: 生产数据→训练数据完整闭环


class DCLChatRecord(Base):
    """数据闭环-对话记录表(按月分区)"""
    __tablename__ = 'dcl_chat_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(Integer, unique=True, nullable=False, comment='记录唯一标识')
    trace_id = Column(String(64), nullable=False, comment='全链路追踪ID', index=True)
    session_id = Column(String(100), comment='会话ID', index=True)
    user_id_encrypted = Column(String(64), comment='加密用户ID(SHA256)')
    user_input_raw = Column(Text, comment='用户原始输入')
    user_input_desensitized = Column(Text, comment='脱敏后输入')
    agent_output_raw = Column(Text, comment='智能体原始输出')
    agent_output_desensitized = Column(Text, comment='脱敏后输出')
    agent_type = Column(String(30), comment='智能体类型: zhouyu/luxun/zhugeliang等')
    context_summary = Column(Text, comment='历史对话摘要JSON字符串')
    metadata_json = Column(JSON, comment='元数据JSON(耗时/模型/版本等)')
    feedback_json = Column(JSON, comment='反馈数据JSON(类型/评分/原因/评论)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    partition_month = Column(String(7), comment='分区键(YYYY-MM)')

    __table_args__ = (
        Index('dcl_chat_trace', 'trace_id'),
        Index('dcl_chat_session', 'session_id'),
        Index('dcl_chat_partition', 'partition_month'),
        Index('dcl_chat_created', 'created_at'),
    )


class DCLUserFeedback(Base):
    """数据闭环-用户反馈表"""
    __tablename__ = 'dcl_user_feedbacks'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    feedback_id = Column(Integer, unique=True, nullable=False, comment='反馈唯一标识')
    trace_id = Column(String(64), nullable=False, comment='关联追踪ID', index=True)
    user_id_encrypted = Column(String(64), comment='加密用户ID')
    feedback_type = Column(String(15), comment='反馈类型: like/dislike/rating/comment')
    rating = Column(SmallInteger, comment='评分(1-5)')
    reason_code = Column(String(30), comment='点踩原因代码')
    reason_label = Column(String(20), comment='点踩原因标签')
    comment_text = Column(Text, comment='评论文本')
    created_at = Column(DateTime, default=datetime.now, comment='提交时间')

    __table_args__ = (
        Index('dcl_fb_trace', 'trace_id'),
        Index('dcl_fb_type', 'feedback_type'),
        Index('dcl_fb_created', 'created_at'),
    )


class DCLAsyncWriteTask(Base):
    """数据闭环-异步写入任务表"""
    __tablename__ = 'dcl_async_write_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_id = Column(String(64), unique=True, nullable=False, comment='任务唯一标识')
    trace_id = Column(String(64), comment='关联追踪ID')
    payload_json = Column(JSON, comment='写入载荷JSON')
    status = Column(String(15), default='pending', comment='状态: pending/processing/completed/failed/retrying')
    retry_count = Column(Integer, default=0, comment='已重试次数')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    error_message = Column(Text, comment='错误信息')
    processing_time_ms = Column(Float, default=0.0, comment='处理耗时(ms)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('dcl_task_status', 'status'),
        Index('dcl_task_created', 'created_at'),
    )


class DCLTrainingDataSample(Base):
    """数据闭环-训练数据样本表"""
    __tablename__ = 'dcl_training_samples'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_id = Column(String(64), unique=True, nullable=False, comment='样本唯一标识')
    input_text = Column(Text, comment='输入文本(用户问题)')
    output_text = Column(Text, comment='输出文本(智能体回复)')
    label = Column(SmallInteger, comment='标签: 1正样本/0负样本/-1中性/-2边界')
    label_name = Column(String(10), comment='标签名称: positive/negative/neutral/boundary')
    agent_type = Column(String(30), comment='智能体类型')
    source_trace_id = Column(String(64), comment='来源追踪ID')
    confidence = Column(Float, default=1.0, comment='置信度(0-1)')
    features_json = Column(JSON, comment='特征向量JSON')
    used_in_training = Column(Boolean, default=False, comment='是否已用于训练')
    model_version_trained = Column(String(30), comment='用于训练的模型版本')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('dcl_smp_label', 'label'),
        Index('dcl_smp_agent', 'agent_type'),
        Index('dcl_smp_used', 'used_in_training'),
    )


class DCLJudgeModelVersion(Base):
    """数据闭环-裁判模型版本表"""
    __tablename__ = 'dcl_judge_model_versions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    model_key = Column(String(64), unique=True, nullable=False, comment='模型唯一标识(name:version)')
    model_name = Column(String(100), comment='模型名称')
    version = Column(String(20), comment='版本号')
    base_model = Column(String(50), default='bert-base-chinese', comment='基础模型')
    model_path = Column(String(300), comment='模型文件路径')
    metrics_json = Column(JSON, comment='评估指标JSON(accuracy/precision/recall/f1等)')
    is_current = Column(Boolean, default=False, comment='是否为当前使用模型')
    training_config_json = Column(Text, comment='训练配置JSON')
    status = Column(String(15), default='draft', comment='状态: draft/training/evaluating/ready/deployed/deprecated/failed')
    created_by = Column(String(100), comment='创建者')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('dcl_judge_current', 'is_current'),
        Index('dcl_judge_status', 'status'),
    )


class DCLRLEpisode(Base):
    """数据闭环-强化学习训练回合表"""
    __tablename__ = 'dcl_rl_episodes'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    episode_id = Column(String(64), unique=True, nullable=False, comment='回合唯一标识')
    config_name = Column(String(50), comment='RL配置名称')
    algorithm = Column(String(10), default='PPO', comment='算法名称')
    base_model = Column(String(50), default='Qwen-1.8B', comment='基础策略模型')
    total_timesteps = Column(Integer, default=0, comment='总训练步数')
    final_mean_reward = Column(Float, default=0.0, comment='最终均值奖励')
    best_mean_reward = Column(Float, default=0.0, comment='最佳均值奖励')
    improvement = Column(Float, default=0.0, comment='提升幅度')
    reward_stats_json = Column(JSON, comment='奖励统计JSON')
    checkpoint_path = Column(String(300), comment='检查点文件路径')
    metrics_history_json = Column(JSON, comment='指标历史曲线JSON')
    status = Column(String(15), default='pending', comment='状态')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('dcl_rl_config', 'config_name'),
        Index('dcl_rl_status', 'status'),
    )


class DCLModelVersion(Base):
    """数据闭环-模型版本总管表"""
    __tablename__ = 'dcl_model_versions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    version_id = Column(String(64), unique=True, nullable=False, comment='版本唯一标识')
    model_name = Column(String(100), comment='模型名称')
    version_number = Column(String(20), comment='版本号')
    model_type = Column(String(20), comment='模型类型: judge/rl/policy/base')
    file_path = Column(String(300), comment='模型文件存储路径')
    size_mb = Column(Float, default=0.0, comment='模型大小(MB)')
    metrics_json = Column(JSON, comment='性能指标JSON')
    status = Column(String(15), default='draft', comment='状态: draft/training/evaluating/ready/deployed/deprecated/failed')
    parent_version_id = Column(String(64), comment='父版本ID')
    canary_weight = Column(Float, default=0.0, comment='灰度发布权重(0-1)')
    deployed_at = Column(DateTime, comment='部署时间')
    created_by = Column(String(100), comment='创建者')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('dcl_mv_type', 'model_type'),
        Index('dcl_mv_status', 'status'),
        Index('dcl_mv_current', 'canary_weight'),
    )


class DCLCanaryRule(Base):
    """数据闭环-灰度发布规则表"""
    __tablename__ = 'dcl_canary_rules'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_id = Column(String(64), unique=True, nullable=False, comment='规则唯一标识')
    model_type = Column(String(30), comment='目标模型类型')
    new_version_id = Column(String(64), comment='新版本ID')
    old_version_id = Column(String(64), comment='旧版本ID')
    strategy = Column(String(20), comment='路由策略: user_hash/percentage/whitelist/segment')
    weight = Column(Float, default=0.1, comment='流量权重比例(0-1)')
    whitelist_json = Column(JSON, comment='白名单用户ID列表JSON')
    enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        Index('dcl_canary_enabled', 'enabled'),
        Index('dcl_canary_type', 'model_type'),
    )


class DCLCanaryRoutingLog(Base):
    """数据闭环-灰度路由日志表"""
    __tablename__ = 'dcl_canary_routing_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    request_id = Column(String(64), comment='请求ID')
    user_id = Column(String(100), comment='用户ID')
    routed_version = Column(String(20), comment='路由到的版本号')
    routing_strategy = Column(String(20), comment='使用的路由策略')
    hit_canary = Column(Boolean, default=False, comment='是否命中灰度')
    latency_ms = Column(Float, default=0.0, comment='路由耗时(ms)')
    timestamp = Column(DateTime, default=datetime.now, comment='路由时间')

    __table_args__ = (
        Index('dcl_route_user', 'user_id'),
        Index('dcl_route_time', 'timestamp'),
    )


class DCLABTestResult(Base):
    """数据闭环-A/B测试结果表"""
    __tablename__ = 'dcl_ab_test_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    test_id = Column(String(64), unique=True, nullable=False, comment='测试唯一标识')
    control_version = Column(String(64), comment='对照版本')
    treatment_version = Column(String(64), comment='实验版本')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    traffic_split_json = Column(JSON, comment='流量分配JSON')
    sample_sizes_json = Column(JSON, comment='各版本样本量JSON')
    metrics_comparison_json = Column(JSON, comment='指标对比JSON(control vs treatment)')
    winner_version = Column(String(64), comment='胜出版本')
    p_value = Column(Float, comment='P值')
    is_significant = Column(Boolean, default=False, comment='是否统计显著(p<0.05)')
    recommendation = Column(Text, comment='推荐结论')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('dcl_ab_start', 'start_date'),
        Index('dcl_ab_significant', 'is_significant'),
    )


class DCLArchiveJob(Base):
    """数据闭环-归档任务表"""
    __tablename__ = 'dcl_archive_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    job_id = Column(String(64), unique=True, nullable=False, comment='归档任务ID')
    target_month = Column(String(7), comment='目标月份(YYYY-MM)')
    record_count = Column(Integer, default=0, comment='记录数')
    status = Column(String(15), default='pending', comment='状态: pending/archiving/completed/failed')
    output_path = Column(String(500), comment='OSS输出路径')
    original_size_kb = Column(Float, default=0.0, comment='原始大小(KB)')
    compressed_size_kb = Column(Float, default=0.0, comment='压缩后大小(KB)')
    compression_ratio = Column(Float, default=0.0, comment='压缩比')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('dcl_arch_month', 'target_month'),
        Index('dcl_arch_status', 'status'),
    )


class DCLIntegrationLog(Base):
    """数据闭环-模块集成日志表"""
    __tablename__ = 'dcl_integration_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    integration_target = Column(String(30), comment='集成目标: hippocampus_memory/self_play_adversarial/ministry_audit')
    trace_id = Column(String(64), comment='关联追踪ID')
    action_type = Column(String(30), comment='操作类型')
    payload_json = Column(JSON, comment='载荷JSON')
    importance = Column(Float, default=0.5, comment='重要度(海马体记忆用)')
    sync_status = Column(String(10), default='success', comment='同步状态')
    synced_at = Column(DateTime, default=datetime.now, comment='同步时间')

    __table_args__ = (
        Index('dcl_integ_target', 'integration_target'),
        Index('dcl_integ_trace', 'trace_id'),
    )


class DCLMonitorAlert(Base):
    """数据闭环-监控告警表"""
    __tablename__ = 'dcl_monitor_alerts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_id = Column(String(30), unique=True, nullable=False, comment='告警规则ID')
    alert_name = Column(String(50), comment='告警名称')
    condition_expr = Column(String(100), comment='触发条件表达式')
    severity = Column(String(10), comment='严重程度: critical/warning/info')
    action_recommendation = Column(String(100), comment='建议动作')
    triggered_at = Column(DateTime, comment='触发时间')
    snapshot_values_json = Column(JSON, comment='触发时快照值')
    resolved = Column(Boolean, default=False, comment='是否已解决')
    resolved_at = Column(DateTime, comment='解决时间')

    __table_args__ = (
        Index('dcl_alert_resolved', 'resolved'),
        Index('dcl_alert_severity', 'severity'),
    )


class DCLDashboardSnapshot(Base):
    """数据闭环-看板快照表"""
    __tablename__ = 'dcl_dashboard_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dashboard_id = Column(String(64), unique=True, nullable=False, comment='看板唯一标识')
    date_range = Column(String(20), comment='数据时间范围')
    total_chats = Column(Integer, default=0, comment='对话总量')
    chats_with_feedback = Column(Integer, default=0, comment='有反馈的对话数')
    feedback_rate = Column(Float, default=0.0, comment='反馈率(%)')
    like_rate = Column(Float, default=0.0, comment='点赞率(%)')
    dislike_rate = Column(Float, default=0.0, comment='点踩率(%)')
    avg_rating = Column(Float, comment='平均评分')
    async_success_rate = Column(Float, default=0.0, comment='异步写入成功率(%)')
    async_avg_latency_ms = Column(Float, default=0.0, comment='异步写入平均延迟(ms)')
    queue_backlog = Column(Integer, default=0, comment='队列积压数')
    archive_status_json = Column(JSON, comment='归档状态JSON')
    judge_metrics_json = Column(JSON, comment='裁判模型指标JSON')
    rl_progress_json = Column(JSON, comment='RL训练进度JSON')
    model_versions_json = Column(JSON, comment='活跃模型版本JSON')
    canary_routing_json = Column(JSON, comment='灰度路由统计JSON')
    ab_tests_json = Column(JSON, comment='A/B测试结果JSON')
    integration_status_json = Column(JSON, comment='集成状态JSON')
    alerts_active_json = Column(JSON, comment='活跃告警JSON')
    recommendations_json = Column(JSON, comment='优化建议JSON')
    generated_at = Column(DateTime, default=datetime.now, comment='生成时间')

    __table_args__ = (
        Index('dcl_dash_generated', 'generated_at'),
    )


# =============================================================================
# 第二十部分：流式渲染修复与优化层 (streaming_fix_layer.py)
# =============================================================================

class SFDebugSession(Base):
    __tablename__ = 'sf_debug_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False)
    base_url = Column(String(255), comment='Test target URL')
    status = Column(String(20), default='idle', comment='idle/connecting/streaming/complete/error')
    test_message = Column(Text, comment='Test message sent')
    ttfb_ms = Column(Float, comment='Time to first byte (ms)')
    total_chunks = Column(Integer, default=0)
    total_chars = Column(Integer, default=0)
    total_time_ms = Column(Float, comment='Total elapsed time (ms)')
    speed_chars_per_sec = Column(Float, comment='Throughput (chars/sec)')
    error_message = Column(Text, comment='Error details if failed')
    curl_command = Column(Text, comment='Generated curl command')
    raw_response_headers = Column(JSON, comment='Response headers captured')
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# 第三十三部分：修为体验卡与平衡机制模块 (experience_card_balance_layer.py)
# =============================================================================

class ExperienceCardRecord(Base):
    __tablename__ = 'experience_cards'
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String(24), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False, index=True)
    card_type = Column(String(20), nullable=False, comment='zhuji_card/jindan_card/yuanying_card')
    status = Column(String(15), default='IN_BACKPACK', comment='ACTIVE/USED/EXPIRED/IN_BACKPACK')
    target_realm = Column(String(20), comment='临时解锁的目标境界')
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, comment='过期时间')
    uses_remaining = Column(Integer, nullable=False, comment='剩余使用次数')
    uses_total = Column(Integer, nullable=False, comment='总使用次数')
    grant_source = Column(String(20), comment='NEWBIE/TASK/DAILY_STREAK/INVITE/EVENT/SHOP')
    grant_source_detail = Column(Text, comment='来源详情如任务ID等')
    activated_at = Column(DateTime)
    used_at = Column(DateTime)
    expired_at = Column(DateTime)
    __table_args__ = (
        Index('ecr_user_status', 'user_id', 'status'),
        Index('ecr_type_source', 'card_type', 'grant_source'),
        Index('ecr_expires', 'expires_at'),
    )


class TempRealmStateLog(Base):
    __tablename__ = 'temp_realm_state_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    original_realm = Column(String(20), nullable=False)
    temp_realm = Column(String(20), nullable=False, comment='临时提升到的境界')
    activated_by_card_id = Column(String(24))
    max_uses = Column(Integer, default=0)
    used_count = Column(Integer, default=0)
    exp_multiplier = Column(Float, default=0.5, comment='体验期间经验倍率')
    is_active = Column(Boolean, default=True)
    activated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    deactivated_at = Column(DateTime)
    deactivate_reason = Column(String(30), comment='expired/uses_exhausted/manual/cancelled')
    __table_args__ = (
        Index('trsl_user_active', 'user_id', 'is_active'),
        Index('trsl_temp_realm', 'temp_realm'),
    )


class CardGrantHistory(Base):
    __tablename__ = 'card_grant_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    card_type = Column(String(20), nullable=False)
    grant_rule_id = Column(String(40))
    grant_source = Column(String(20))
    month_key = Column(String(7), format='YYYY-MM', index=True, comment='用于月度限制统计')
    granted_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('user_id', 'card_type', 'month_key', name='uq_monthly_grant_limit'),
        Index('cgh_user_month', 'user_id', 'month_key'),
    )


class CardUsageLog(Base):
    __tablename__ = 'card_usage_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String(24), nullable=False)
    user_id = Column(String(36), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    effective_realm_at_use = Column(String(20), comment='使用时的有效境界')
    api_endpoint_called = Column(String(100), comment='调用的API端点')
    feature_accessed = Column(String(50), comment='访问的功能')
    remaining_uses_after = Column(Integer)
    was_last_use = Column(Boolean, default=False)
    __table_args__ = (
        Index('cul_card_time', 'card_id', 'used_at'),
        Index('cul_user_feature', 'user_id', 'feature_accessed'),
    )


class PostTrialGuidanceLog(Base):
    __tablename__ = 'post_trial_guidance_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    expired_card_type = Column(String(20), nullable=False)
    guidance_title = Column(String(100))
    guidance_body = Column(Text)
    action_button_text = Column(String(50))
    action_target = Column(String(100))
    displayed_at = Column(DateTime, default=datetime.utcnow)
    user_clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime)
    conversion_task_started = Column(Boolean, default=False)
    __table_args__ = (
        Index('ptgl_user_type', 'user_id', 'expired_card_type'),
    )


class TrialDataPreservation(Base):
    __tablename__ = 'trial_data_preservations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    data_ref = Column(String(50), comment='数据引用ID如prediction_id/report_id')
    data_type = Column(String(30), comment='prediction/backtest/analysis')
    data_summary_json = Column(JSON, comment='数据摘要用于展示')
    preserved_during_trial_of = Column(String(20), comment='使用的体验卡类型')
    trial_expired_at = Column(DateTime)
    verification_prompt_shown = Column(Boolean, default=False)
    verified_result_actual = Column(Float, comment='实际结果用于对比预测')
    verification_accuracy = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('tdp_user_ref', 'user_id', 'data_ref'),
        Index('tdp_verified', 'verification_prompt_shown'),
    )


class ReincarnationRecord(Base):
    __tablename__ = 'reincarnation_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    reincarnation_count = Column(Integer, default=1, comment='第几次轮回')
    previous_max_realm = Column(String(20), comment='轮回前的最高境界')
    previous_total_exp = Column(Integer, comment='轮回前的总经验值')
    rewards_kept_json = Column(JSON, comment='保留的永久奖励列表')
    reincarnation_marks_earned = Column(Integer, default=1)
    reset_at = Column(DateTime, default=datetime.utcnow)
    cooldown_until = Column(DateTime, comment='冷却期结束时间')
    is_cooldown_active = Column(Boolean, default=True)
    __table_args__ = (
        Index('rr_user_count', 'user_id', 'reincarnation_count'),
        Index('rr_cooldown', 'is_cooldown_active'),
    )


class MarksExchangeLog(Base):
    __tablename__ = 'marks_exchange_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    marks_spent = Column(Integer, nullable=False, comment='消耗的轮回印记数')
    reward_item_id = Column(String(30), comment='兑换的道具ID')
    reward_item_name = Column(String(100))
    exchange_rate_applied = Column(Float, comment='兑换比率')
    exchanged_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('mel_user_time', 'user_id', 'exchanged_at'),
    )


class BalanceAntiAbuseLog(Base):
    __tablename__ = 'balance_abuse_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    check_type = Column(String(30), comment='monthly_limit/concurrent/stacking/tradability/rate_limit/daily_api')
    check_result = Column(Boolean, comment='通过/拒绝')
    blocked_reason = Column(Text)
    requested_card_type = Column(String(20))
    requested_action = Column(String(50))
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('bal_user_check', 'user_id', 'check_type'),
        Index('bal_blocked', 'check_result'),
    )


class OperationsEventRecord(Base):
    __tablename__ = 'operations_event_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(30), unique=True, nullable=False)
    event_name = Column(String(100))
    event_type = Column(String(20), comment='double_exp/shop_promo/etc')
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    multiplier = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    can_combine_with_trial = Column(Boolean, default=True)
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('oer_active_type', 'is_active', 'event_type'),
    )


class ShopPurchaseRecord(Base):
    __tablename__ = 'shop_purchase_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    item_id = Column(String(30), nullable=False)
    item_name = Column(String(100))
    item_type = Column(String(20), comment='CARD_JINDAN/CARD_YUANYING/MARKS_EXCHANGE/OTHER')
    price_points = Column(Integer, nullable=False)
    price_currency = Column(String(10))
    currency_spent = Column(Float, default=0.0)
    purchase_month = Column(String(7), format='YYYY-MM', index=True)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('spr_user_item', 'user_id', 'item_id'),
        Index('spr_user_month', 'user_id', 'purchase_month'),
    )


class ExpBonusCalculationLog(Base):
    __tablename__ = 'exp_bonus_calculation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    base_exp = Column(Integer, nullable=False)
    trial_multiplier = Column(Float, default=1.0, comment='体验期间倍率(通常0.5)')
    event_multiplier = Column(Float, default=1.0, comment='活动倍率(双倍经验=2.0)')
    streak_bonus = Column(Float, default=0.0)
    realm_multiplier = Column(Float, default=1.0)
    final_exp = Column(Integer, nullable=False)
    bonus_breakdown_json = Column(JSON, comment='各加成明细')
    calculated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('ebl_user_time', 'user_id', 'calculated_at'),
    )


# =============================================================================
# 第三十二部分：融合量化分析与一通百通模块 (fusion_quant_mastery_layer.py)
# =============================================================================

class UserQuantCultivation(Base):
    __tablename__ = 'user_quant_cultivations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, comment='用户ID')
    current_realm = Column(String(20), nullable=False, default='lianqi', comment='当前境界: lianqi/zhujin/jindan/yuanying/huashen/dujie/dacheng')
    total_exp = Column(Integer, default=0, comment='总经验值')
    abilities_json = Column(JSON, comment='各能力熟练度 {ability_name: proficiency}')
    last_bonus_time = Column(DateTime, comment='上次一通百通触发时间')
    last_level_up = Column(DateTime, comment='上次升级时间')
    streak_days = Column(Integer, default=0, comment='连续活跃天数')
    last_activity_date = Column(Date)
    completed_tasks_json = Column(JSON, comment='已完成的任务ID列表')
    prediction_correct_count = Column(Integer, default=0)
    prediction_total_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('uqc_user_realm', 'user_id', 'current_realm'),
    )


class CultivationExpLog(Base):
    __tablename__ = 'cultivation_exp_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    action_type = Column(String(40), nullable=False, comment='block_analysis/prediction_request/etc')
    exp_gained = Column(Integer, nullable=False, comment='获得的经验值')
    realm_before = Column(String(20), comment='操作时的境界')
    realm_multiplier = Column(Float, comment='境界加成倍率')
    streak_bonus_applied = Column(Float, default=0.0, comment='连续天数加成')
    source_task_completion = Column(Boolean, default=False, comment='是否来自任务完成')
    task_id = Column(String(40), comment='关联的任务ID')
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('cel_user_action', 'user_id', 'action_type'),
        Index('cel_timestamp', 'timestamp'),
    )


class CultivationTaskCompletion(Base):
    __tablename__ = 'cultivation_task_completions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    task_id = Column(String(40), nullable=False)
    task_name = Column(String(100))
    category = Column(String(20), comment='daily/challenge/breakthrough')
    exp_reward = Column(Integer, comment='任务奖励经验值')
    completed_at = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(Date, nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint('user_id', 'task_id', 'completion_date', name='uq_task_completion_daily'),
        Index('ctc_user_date', 'user_id', 'completion_date'),
    )


class MasteryTransferEvent(Base):
    __tablename__ = 'mastery_transfer_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    source_ability = Column(String(30), nullable=False, comment='源能力节点')
    target_ability = Column(String(30), nullable=False, comment='目标能力节点')
    bonus_amount = Column(Float, nullable=False, comment='增益值')
    strength_applied = Column(Float, comment='关联强度系数')
    trigger_reason = Column(Text)
    was_cascaded = Column(Boolean, default=False, comment='是否为级联传播')
    cascade_depth = Column(Integer, default=0, comment='级联深度')
    cooldown_key = Column(String(60), comment='冷却键: user_ability')
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('mte_user_source', 'user_id', 'source_ability'),
        Index('mte_user_target', 'user_id', 'target_ability'),
        Index('mte_cascade', 'was_cascaded', 'cascade_depth'),
    )


class AbilityProficiencySnapshot(Base):
    __tablename__ = 'ability_proficiency_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    ability_id = Column(String(30), nullable=False)
    proficiency_before = Column(Float, default=0.0)
    proficiency_after = Column(Float, default=0.0)
    delta = Column(Float, comment='变化量')
    change_source = Column(String(40), comment='direct_use/transfer/cascade/task_reward')
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('aps_user_ability_date', 'user_id', 'ability_id', 'snapshot_date'),
    )


class FactorAccessLog(Base):
    __tablename__ = 'factor_access_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    factor_id = Column(String(30), nullable=False)
    factor_name = Column(String(50))
    user_realm = Column(String(20), nullable=False)
    required_realm = Column(String(20), comment='该因子所需最低境界')
    access_granted = Column(Boolean, nullable=False, comment='是否允许访问')
    access_denied_reason = Column(Text)
    endpoint = Column(String(100), comment='触发的API端点')
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('fal_user_factor', 'user_id', 'factor_id'),
        Index('fal_denied', 'access_granted'),
    )


class TieredOutputRenderLog(Base):
    __tablename__ = 'tiered_output_render_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    request_id = Column(String(36))
    user_realm = Column(String(20), nullable=False)
    raw_data_hash = Column(String(32), comment='原始数据MD5')
    forecast_range_output = Column(Text)
    sections_included = Column(JSON, comment='包含的章节列表')
    truncated_fields = Column(JSON, comment='被截断的字段')
    render_duration_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('torl_user_realm', 'user_id', 'user_realm'),
    )


class StrategyPermissionCheckLog(Base):
    __tablename__ = 'strategy_permission_check_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    strategy_type = Column(String(30), nullable=False)
    user_realm = Column(String(20), nullable=False)
    min_required_realm = Column(String(20))
    permission_granted = Column(Boolean, nullable=False)
    denied_message = Column(Text)
    params_requested = Column(JSON, comment='请求的参数列表')
    endpoint = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('spcl_user_strategy', 'user_id', 'strategy_type'),
        Index('spcl_granted', 'permission_granted'),
    )


class AgentGuidanceLog(Base):
    __tablename__ = 'agent_guidance_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    persona = Column(String(10), comment='zhouyu/luxun')
    guidance_type = Column(String(30), comment='breakthrough_congrats/stagnation_warning/ability_tip/daily_encouragement')
    message_text = Column(Text)
    suggested_action = Column(String(100))
    urgency = Column(String(10), comment='high/medium/low')
    realm_context = Column(String(20))
    was_displayed = Column(Boolean, default=True)
    user_clicked_action = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('agl_user_persona', 'user_id', 'persona'),
        Index('agl_type', 'guidance_type'),
    )


class CollectiveEvolutionLog(Base):
    __tablename__ = 'collective_evolution_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    feature_id = Column(String(30), nullable=False)
    user_id = Column(String(36), nullable=False, comment='触发用户(可为null表示系统级)')
    is_positive_feedback = Column(Boolean, nullable=False)
    usage_context = Column(String(50), comment='使用场景')
    prev_satisfaction_score = Column(Float)
    new_satisfaction_score = Column(Float)
    prev_evolution_weight = Column(Float)
    new_evolution_weight = Column(Float)
    global_score_before = Column(Float)
    global_score_after = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('cel_feature', 'feature_id'),
        Index('cel_feature_time', 'feature_id', 'timestamp'),
    )


class TribulationWarningRecord(Base):
    __tablename__ = 'tribulation_warning_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    warning_id = Column(String(30), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    warning_level = Column(String(10), nullable=False, comment='warning/severe/critical')
    var_value = Column(Float)
    var_threshold = Column(Float)
    mdd_value = Column(Float)
    mdd_threshold = Column(Float)
    var_exceed_30d_count = Column(Integer, default=0)
    mdd_exceed_30d_count = Column(Integer, default=0)
    restrictions_applied = Column(JSON, comment='应用的限制列表')
    suggestion_text = Column(Text)
    is_active = Column(Boolean, default=True)
    deactivated_at = Column(DateTime)
    cleared_by = Column(String(36), comment='解除者(user_id或system)')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('twr_user_level', 'user_id', 'warning_level'),
        Index('twr_active', 'is_active'),
    )


class RiskMetricHistory(Base):
    __tablename__ = 'risk_metric_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    metric_type = Column(String(10), nullable=False, comment='var/mdd')
    metric_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    is_exceeded = Column(Boolean, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('rmh_user_metric_time', 'user_id', 'metric_type', 'recorded_at'),
        Index('rmh_exceeded', 'is_exceeded'),
    )


class RealmValidationLog(Base):
    __tablename__ = 'realm_validation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    requested_capability = Column(String(40), nullable=False)
    user_realm = Column(String(20), nullable=False)
    required_realm = Column(String(20))
    is_allowed = Column(Boolean, nullable=False)
    http_code = Column(Integer, default=200)
    endpoint = Column(String(100))
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('rvl_user_capability', 'user_id', 'requested_capability'),
        Index('rvl_denied', 'is_allowed'),
    )


class CultivationActionLog(Base):
    __tablename__ = 'cultivation_action_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    action_type = Column(String(40), nullable=False)
    exp_gained = Column(Integer, default=0)
    task_exp_gained = Column(Integer, default=0)
    leveled_up = Column(Boolean, default=False)
    new_realm = Column(String(20))
    transfer_count = Column(Integer, default=0)
    transfer_details_json = Column(JSON, comment='一通百通事件摘要')
    ability_updated = Column(String(30), comment='更新的能力名')
    ability_delta = Column(Float, default=0.0)
    evolution_feature_recorded = Column(String(30), comment='记录的群体进化功能')
    total_duration_ms = Column(Integer, default=0)
    response_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('cal_user_action_time', 'user_id', 'timestamp'),
        Index('cal_level_up', 'leveled_up'),
    )


class CultivationPanelViewLog(Base):
    __tablename__ = 'cultivation_panel_view_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    view_type = Column(String(20), comment='full_panel/report_tip/dashboard_full')
    current_realm = Column(String(20))
    total_exp = Column(Integer)
    exp_progress_pct = Column(Float)
    streak_days = Column(Integer)
    ability_count_shown = Column(Integer, default=11)
    pending_task_count = Column(Integer)
    recent_transfer_count = Column(Integer)
    has_tribulation_warning = Column(Boolean, default=False)
    collective_evolution_score = Column(Float)
    render_duration_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('cpvl_user_type', 'user_id', 'view_type'),
    )


class BreakthroughAnimationLog(Base):
    __tablename__ = 'breakthrough_animation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    from_realm = Column(String(20), nullable=False)
    to_realm = Column(String(20), nullable=False)
    animation_type = Column(String(20), default='particle_golden')
    duration_ms = Column(Integer, default=3000)
    particle_count = Column(Integer, default=50)
    colors_used = Column(JSON, comment='动画颜色列表')
    sound_enabled = Column(Boolean, default=False)
    text_float = Column(Boolean, default=True)
    float_text = Column(String(20), default='realm_name')
    displayed_to_user = Column(Boolean, default=True)
    user_interaction = Column(String(20), comment='none/share/screenshot/dismiss')
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('bal_user_realm', 'user_id', 'to_realm'),
        Index('bal_time', 'timestamp'),
    )


# =============================================================================
# 第三十一部分：双场景差异化模块 (dual_scenario_differentiation_layer.py)
# =============================================================================

class ScenarioRoutingLog(Base):
    __tablename__ = 'scenario_routing_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    session_id = Column(String(36), nullable=False)
    raw_input = Column(Text, comment='原始用户输入')
    detected_mode = Column(String(20), nullable=False, comment='REPORT/CONVERSATION')
    explicit_override = Column(Boolean, default=False)
    routing_confidence = Column(Float, default=0.0)
    keywords_matched = Column(JSON, comment='匹配到的关键词列表')
    agent_priority = Column(String(30))
    target_endpoint = Column(String(50))
    routing_duration_ms = Column(Integer, default=0)
    reasoning_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('srl_user_session', 'user_id', 'session_id'),
        Index('srl_mode', 'detected_mode'),
    )


class HybridInputStateLog(Base):
    __tablename__ = 'hybrid_input_state_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    current_mode = Column(String(20), default='REPORT')
    natural_text = Column(Text)
    structured_fields_json = Column(JSON, comment='结构化字段: city/district/block等8字段')
    parsed_from_nl = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=False)
    validation_errors_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('hisl_user', 'user_id'),
    )


class BatchOperationLog(Base):
    __tablename__ = 'batch_operation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    operation_type = Column(String(20), nullable=False, comment='export/compare/delete/template_save/template_load')
    task_ids_json = Column(JSON, comment='涉及的task_id列表')
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    results_summary = Column(Text)
    download_url = Column(String(256))
    comparison_id = Column(String(36))
    template_id = Column(Integer)
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('bol_user_op', 'user_id', 'operation_type'),
    )


class ReportGenerationLog(Base):
    __tablename__ = 'report_generation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    task_data_ref = Column(String(36), comment='关联的task数据引用')
    mode = Column(String(20), nullable=False, comment='full/compact')
    title = Column(String(200))
    sections_rendered_json = Column(JSON, comment='渲染的章节列表')
    word_count = Column(Integer, default=0)
    has_charts = Column(Boolean, default=False)
    html_size_bytes = Column(Integer, default=0)
    generation_duration_ms = Column(Integer, default=0)
    download_urls_json = Column(JSON)
    cache_hit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('rgl_user', 'user_id'),
        Index('rgl_mode', 'mode'),
    )


class OnboardingProgressLog(Base):
    __tablename__ = 'onboarding_progress_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False)
    total_steps = Column(Integer, default=4)
    completed_steps_json = Column(JSON, comment='已完成的步骤名称列表')
    is_dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime)
    last_progress_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class WelcomeMessageLog(Base):
    __tablename__ = 'welcome_message_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    persona = Column(String(20), nullable=False, comment='zhouyu/luxun')
    time_of_day = Column(String(10), comment='morning/afternoon/evening/default')
    message_template_used = Column(String(50))
    displayed_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('wml_user_session', 'user_id', 'session_id'),
    )


class FollowupClickLog(Base):
    __tablename__ = 'followup_click_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    last_intent = Column(String(40))
    followup_text = Column(String(200))
    intent_hint = Column(String(40))
    icon_used = Column(String(20))
    was_clicked = Column(Boolean, default=False)
    auto_fill_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('fcl_user_intent', 'user_id', 'last_intent'),
    )


class ReportCardEmbedLog(Base):
    __tablename__ = 'report_card_embed_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    report_ref_id = Column(String(36), comment='关联的报告ID')
    title = Column(String(100))
    summary_metrics_json = Column(JSON, comment='growth/risk/advice等指标')
    action_count = Column(Integer, default=3)
    is_compact = Column(Boolean, default=True)
    expandable = Column(Boolean, default=True)
    rendered_html_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('rcel_user', 'user_id'),
    )


class ReasoningStepDisplayLog(Base):
    __tablename__ = 'reasoning_step_display_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False)
    step_index = Column(Integer, default=0)
    step_key = Column(String(30), comment='zhongshu_parsing/hubu_collecting/gongbu_modeling/xingbu_review/xiabu_approval/libu_nlg')
    agent_name = Column(String(20))
    icon_class = Column(String(30))
    status = Column(String(15), default='pending', comment='pending/in_progress/completed/skipped/error')
    text_content = Column(Text)
    extra_info_json = Column(JSON)
    duration_ms = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('rsdl_session_step', 'session_id', 'step_index'),
        UniqueConstraint('session_id', 'step_key', name='uq_session_step'),
    )


class DataSourceHighlightLog(Base):
    __tablename__ = 'data_source_highlight_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    source_text = Column(String(100), comment='被高亮的数据源名称')
    original_context = Column(Text, comment='原始文本片段')
    highlight_style = Column(String(50))
    tooltip_content = Column(Text)
    match_position_start = Column(Integer)
    match_position_end = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('dshl_source', 'source_text'),
    )


class ConfidenceExpressionLog(Base):
    __tablename__ = 'confidence_expression_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    context_ref = Column(String(50), comment='上下文引用: 报告ID或消息ID')
    raw_value = Column(Float, comment='原始数值')
    low_bound = Column(Float)
    high_bound = Column(Float)
    computed_pct = Column(Float, comment='计算出的置信百分比')
    expression_mode = Column(String(25), comment='interval_numeric/probabilistic_verbal')
    verbal_label = Column(String(20), comment='如: 六成把握/较有信心')
    output_string = Column(Text, comment='最终输出的置信表达文本')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('cel_user_mode', 'user_id', 'expression_mode'),
    )


class FeedbackRecordLog(Base):
    __tablename__ = 'feedback_record_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(36), nullable=False)
    user_id = Column(String(36))
    is_helpful = Column(Boolean, nullable=False)
    reason = Column(String(30), comment='wrong_answer/data_error/understanding_error/too_long/not_helpful/other')
    response_apology = Column(Text)
    response_clarification = Column(Text)
    response_correction = Column(Text)
    feedback_recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('frl_message', 'message_id'),
        Index('frl_user', 'user_id'),
    )


class MultiIntentSplitLog(Base):
    __tablename__ = 'multi_intent_split_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    original_query = Column(Text, comment='原始复合查询文本')
    separator_detected = Column(String(5), comment='检测到的分隔符')
    part_count = Column(Integer, default=1, comment='拆分后的部分数量')
    parts_json = Column(JSON, comment='[(part_text, intent_hint), ...]')
    interim_prompt_generated = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('misl_user', 'user_id'),
    )


class DispatchLog(Base):
    __tablename__ = 'dispatch_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    dispatch_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    mode = Column(String(20), nullable=False, comment='REPORT/CONVERSATION')
    agent_called = Column(String(30), comment='实际调用的智能体')
    endpoint = Column(String(50), comment='/api/tasks 或 /api/chat')
    params_used_json = Column(JSON)
    result_data_json = Column(JSON)
    duration_ms = Column(Integer, default=0)
    report_ref_id = Column(String(36))
    websocket_event_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('dl_user_mode', 'user_id', 'mode'),
        Index('dl_agent', 'agent_called'),
    )


class AsyncReportJobRecord(Base):
    __tablename__ = 'async_report_job_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36))
    task_data_json = Column(JSON)
    status = Column(String(15), default='queued', comment='queued/processing/completed/failed')
    progress_pct = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_processing_at = Column(DateTime)
    completed_at = Column(DateTime)
    report_id = Column(String(36))
    __table_args__ = (
        Index('arjr_user_status', 'user_id', 'status'),
        Index('arjr_job_status', 'job_id', 'status'),
    )


class SharedComponentRenderLog(Base):
    __tablename__ = 'shared_component_render_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    component_name = Column(String(40), nullable=False, comment='ReportViewer/AgentStatusIndicator')
    render_mode = Column(String(15), comment='full/compact/sidebar_right/floating_ball')
    scenario_context = Column(String(20), comment='report/conversation')
    render_duration_ms = Column(Integer, default=0)
    props_passed_json = Column(JSON)
    output_html_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('scrl_component', 'component_name'),
    )


class ScenarioMetricsDailySnapshot(Base):
    __tablename__ = 'scenario_metrics_daily_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False)
    scenario = Column(String(20), nullable=False, comment='report/conversation')
    event_type = Column(String(40))
    total_events = Column(Integer, default=0)
    sum_value = Column(Float, default=0.0)
    avg_value = Column(Float)
    unique_users_count = Column(Integer, default=0)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('snapshot_date', 'scenario', 'event_type', name='uq_scenario_metric_date'),
        Index('smds_date_scenario', 'snapshot_date', 'scenario'),
    )


class ABTestAssignmentLog(Base):
    __tablename__ = 'ab_test_assignment_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    assigned_variant = Column(String(5), comment='A or B')
    assignment_hash = Column(String(32), comment='MD5 hash for deterministic assignment')
    has_converted = Column(Boolean, default=False)
    converted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('test_id', 'user_id', name='uq_ab_test_user'),
        Index('atal_test_variant', 'test_id', 'assigned_variant'),
    )


class ABTestResultRecord(Base):
    __tablename__ = 'ab_test_result_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(36), unique=True, nullable=False)
    test_name = Column(String(100))
    scenario = Column(String(20), comment='report/conversation')
    variant_a_config_json = Column(JSON)
    variant_b_config_json = Column(JSON)
    traffic_split = Column(Float, default=0.5)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(15), default='running', comment='running/paused/completed')
    total_a_users = Column(Integer, default=0)
    total_b_users = Column(Integer, default=0)
    conversions_a = Column(Integer, default=0)
    conversions_b = Column(Integer, default=0)
    rate_a = Column(Float, default=0.0)
    rate_b = Column(Float, default=0.0)
    z_score = Column(Float)
    significance_level = Column(String(5), comment='***/**/*/ /ns')
    winner = Column(String(5), comment='A/B/none/tie')
    results_analysis_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('abtr_scenario', 'scenario'),
        Index('abtr_status', 'status'),
    )


# ==================== Part 30: 专业复合对话处理层 (Professional Composite Dialogue Layer) ====================
# 对应 professional_dialogue_layer.py — 术语库+复合意图+专业指标+政策影响+舆情+归因+对话管理+NLG+前端组件


class ProfessionalTermEntryRecord(Base):
    """专业-术语词条记录表"""
    __tablename__ = 'professional_term_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    term_key = Column(String(64), unique=True, nullable=False, comment='术语唯一标识')
    name = Column(String(100), nullable=False, comment='标准名称')
    aliases_json = Column(JSON, comment='别名列表JSON')
    category = Column(String(20), comment='valuation/trend/risk/policy/market/location')
    definition = Column(Text, comment='定义说明')
    formula = Column(Text, comment='计算公式(LaTeX/纯文本)')
    data_source = Column(String(50), comment='数据来源')
    unit = Column(String(20), comment='单位')
    normal_range_low = Column(Float, default=0.0)
    normal_range_high = Column(Float, default=10.0)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('pte_term_key', 'term_key'),
        Index('pte_category', 'category'),
    )


class IntentRecognitionLog(Base):
    """专业-意图识别日志表"""
    __tablename__ = 'intent_recognition_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(32), unique=True, nullable=False)
    raw_query = Column(Text, nullable=False, comment='原始用户输入')
    primary_intent = Column(String(30), comment='主意图类型')
    secondary_intents_json = Column(JSON, comment='次要意图列表')
    confidence_score = Column(Float, comment='置信度(0-1)')
    entities_extracted_json = Column(JSON, comment='提取的实体列表')
    processing_time_ms = Column(Float)
    matched_pattern = Column(String(50), comment='匹配的正则模式名')
    cache_hit = Column(Boolean, default=False)
    user_id = Column(String(64))
    session_id = Column(String(40))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('irl_log_id', 'log_id'),
        Index('irl_primary_intent', 'primary_intent'),
        Index('irl_session', 'session_id'),
    )


class MetricCalculationRecord(Base):
    """专业-指标计算记录表"""
    __tablename__ = 'metric_calculation_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    calc_id = Column(String(32), unique=True, nullable=False)
    metric_name = Column(String(50), nullable=False, comment='指标名(sharpe/mdd/calmar/sortino/var等)')
    city = Column(String(50), index=True)
    block = Column(String(80))
    horizon_months = Column(Integer, default=12)
    value = Column(Float, nullable=False, comment='计算值')
    unit = Column(String(20))
    interpretation_text = Column(Text, comment='解释文本')
    is_normal = Column(Boolean, default=True, comment='是否在正常范围')
    calculation_details_json = Column(JSON, comment='详细参数JSON')
    cached = Column(Boolean, default=False)
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('mcr_calc_id', 'calc_id'),
        Index('mcr_metric_city', 'metric_name', 'city'),
        Index('mcr_created', 'created_at'),
    )


class PolicyImpactAnalysisRecord(Base):
    """专业-政策影响分析记录表"""
    __tablename__ = 'policy_impact_analysis_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(32), unique=True, nullable=False)
    city = Column(String(50), index=True)
    policy_type = Column(String(30), comment='政策类型')
    policy_event_id = Column(String(20), comment='关联的政策事件ID')
    impact_pct = Column(Float, comment='影响幅度(%)')
    ci_lower = Column(Float, comment='置信区间下界')
    ci_upper = Column(Float, comment='置信区间上界')
    significance_level = Column(String(5), comment='显著性(***/**/* /ns)')
    sample_size = Column(Integer)
    control_return_pct = Column(Float)
    treatment_return_pct = Column(Float)
    time_horizon_months = Column(Integer)
    narrative_text = Column(Text)
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('piar_analysis_id', 'analysis_id'),
        Index('piar_city_policy', 'city', 'policy_type'),
    )


class SentimentAnalysisRecord(Base):
    """专业-舆情分析记录表"""
    __tablename__ = 'sentiment_analysis_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(32), unique=True, nullable=False)
    block = Column(String(80), index=True)
    days_analyzed = Column(Integer, default=30)
    average_score = Column(Float, comment='平均情绪分(-1到1)')
    trend_direction = Column(String(15), comment='improving/declining/stable')
    trend_strength = Column(Float)
    volatility_score = Column(Float)
    label = Column(String(20), comment='strongly_bullish/neutral/...')
    daily_scores_summary_json = Column(JSON, comment='每日得分摘要(首尾+极值)')
    extreme_events_count = Column(Integer, default=0)
    source_weights_json = Column(JSON, comment='各源权重分布')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('sar_analysis_id', 'analysis_id'),
        Index('sar_block', 'block'),
    )


class FactorAttributionRecord(Base):
    """专业-因子归因分析记录表"""
    __tablename__ = 'factor_attribution_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    attribution_id = Column(String(32), unique=True, nullable=False)
    city = Column(String(50))
    block = Column(String(80), index=True)
    prediction_value = Column(Float, comment='预测值')
    base_prediction = Column(Float, comment='基准预测值')
    total_contribution = Column(Float)
    top_factors_json = Column(JSON, comment='Top3因子贡献详情')
    remaining_factors_json = Column(JSON, comment='其余因子')
    explanation_summary = Column(Text)
    model_version = Column(String(20), default='factor_attr_v2.1')
    shap_method_used = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('far_attr_id', 'attribution_id'),
        Index('far_block', 'block'),
    )


class DialogueContextMemoryRecord(Base):
    """专业-对话上下文记忆记录表"""
    __tablename__ = 'dialogue_context_memory_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(32), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False, index=True)
    focused_cities_json = Column(JSON, comment='关注城市列表')
    focused_blocks_json = Column(JSON, comment='关注板块列表')
    preferred_horizon_months = Column(Integer, default=12)
    preferred_risk_tolerance = Column(String(10), default='medium')
    last_metrics_requested_json = Column(JSON, comment='最近请求的指标')
    last_intent = Column(String(30))
    turn_count = Column(Integer, default=0)
    ttl_seconds = Column(Integer, default=1800)
    expires_at = Column(DateTime, comment='过期时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('dcmr_memory_id', 'memory_id'),
        Index('dcmr_user', 'user_id'),
        Index('dcmr_expires', 'expires_at'),
    )


class MultiIntentProcessingRecord(Base):
    """专业-多意图串行处理记录表"""
    __tablename__ = 'multi_intent_processing_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    process_id = Column(String(32), unique=True, nullable=False)
    user_id = Column(String(64))
    session_id = Column(String(40))
    primary_intent = Column(String(30))
    secondary_intents_json = Column(JSON)
    params_used_json = Column(JSON, comment='标准化后的参数')
    steps_executed_json = Column(JSON, comment='每步结果[step_name/status/duration/api_calls]')
    combined_narrative_text = Column(Text, comment='合并后的回答文本')
    individual_results_refs_json = Column(JSON, comment='各意图独立结果引用')
    sources_cited_json = Column(JSON)
    total_duration_ms = Column(Float)
    error_occurred = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('mipr_process_id', 'process_id'),
        Index('mipr_session', 'session_id'),
    )


class ProfessionalNLGRecord(Base):
    """专业-NLG生成记录表"""
    __tablename__ = 'professional_nlg_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nlg_id = Column(String(32), unique=True, nullable=False)
    persona = Column(String(15), comment='zhouyu/luxun')
    intent_type = Column(String(30), comment='使用的模板类型')
    input_data_hash = Column(String(32), comment='输入数据指纹')
    core_conclusion = Column(Text, comment='核心结论')
    key_metrics_json = Column(JSON, comment='关键指标列表')
    risk_warnings_json = Column(JSON, comment='风险提示列表')
    attribution_analysis_text = Column(Text)
    investment_advice = Column(String(200))
    data_sources_json = Column(JSON)
    full_response_text = Column(Text, comment='完整生成文本')
    response_length_chars = Column(Integer, comment='响应字符数')
    generation_time_ms = Column(Float)
    template_version = Column(String(10), default='v2.0')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('pnlg_nlg_id', 'nlg_id'),
        Index('pnlg_persona_intent', 'persona', 'intent_type'),
    )


class QuickTagClickLog(Base):
    """专业-快捷标签点击日志表"""
    __tablename__ = 'quick_tag_click_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    click_id = Column(String(32), unique=True, nullable=False)
    tag_name = Column(String(30), comment='标签显示名')
    tag_category = Column(String(15), comment='risk/policy/compare/analysis/...')
    fill_template = Column(Text, comment='填充模板')
    filled_input_text = Column(String(300), comment='填充后的输入框内容')
    user_id = Column(String(64))
    session_id = Column(String(40))
    page_location = Column(String(20), comment='consultation/dashboard/...')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('qtcl_click_id', 'click_id'),
        Index('qtcl_tag_category', 'tag_category'),
    )


class TermTooltipDisplayLog(Base):
    """专业-术语悬浮提示日志表"""
    __tablename__ = 'term_tooltip_display_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_id = Column(String(32), unique=True, nullable=False)
    term_name = Column(String(50), comment='触发显示的术语名')
    page_context = Column(String(30), comment='chat_card/report/dashboard')
    hover_duration_ms = Column(Integer, comment='悬浮时长(ms)')
    user_id = Column(String(64))
    session_id = Column(String(40))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ttdl_display_id', 'display_id'),
    )


class HistoryReferenceClickLog(Base):
    """专业-历史引用点击日志表"""
    __tablename__ = 'history_reference_click_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ref_id = Column(String(32), unique=True, nullable=False)
    ref_type = Column(String(15), comment='city/block/horizon/metric/query')
    ref_value = Column(String(100), comment='引用的值')
    action_taken = Column(String(20), comment='fill_input/copy/navigate')
    user_edited_after_fill = Column(Boolean, default=False)
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('hrcl_ref_id', 'ref_id'),
        Index('hrcl_ref_type', 'ref_type'),
    )


class ProfessionalTestResultRecord(Base):
    """专业-测试结果记录表(50题测试集)"""
    __tablename__ = 'professional_test_result_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_run_id = Column(String(32), unique=True, nullable=False)
    question_text = Column(Text, comment='测试问题')
    question_difficulty = Column(String(10), comment='easy/medium/hard')
    expected_intent = Column(String(30), comment='预期意图类型')
    actual_intent = Column(String(30), comment='实际识别意图')
    intent_match = Column(Boolean, default=False)
    expected_metrics = Column(JSON, comment='预期包含的指标')
    actual_metrics_found = Column(JSON, comment='实际找到的指标')
    metrics_match = Column(Boolean, default=False)
    response_quality_score = Column(Float, comment='回答质量评分(1-5)')
    api_calls_correct = Column(Boolean, default=False)
    latency_ms = Column(Float)
    passed = Column(Boolean, default=False)
    error_message = Column(Text)
    tested_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ptrr_test_run_id', 'test_run_id'),
        Index('ptrr_passed', 'passed'),
        Index('ptrr_tested_at', 'tested_at'),
    )


# ==================== Part 29: 深度融合仪表盘与智能咨询层 (Deep Fusion Dashboard & Smart Consultation v2) ====================
# 对应 deep_fusion_dashboard_layer.py — 统一QuantService+仪表盘融合+深度咨询引擎ZhouYu/LuXun NLG+组件规格+性能优化+移动端适配


class QuantServiceCache(Base):
    """深度融合-量化服务缓存表"""
    __tablename__ = 'quant_service_caches'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(128), unique=True, nullable=False, comment='缓存键(SHA256哈希)')
    cache_type = Column(String(20), comment='report/summary/compare/explain')
    city = Column(String(50), index=True)
    district = Column(String(50))
    block = Column(String(80))
    horizon_months = Column(Integer)
    risk_tolerance = Column(String(10))
    result_json = Column(JSON, nullable=False, comment='序列化结果JSON')
    ttl_seconds = Column(Integer, default=300, comment='存活时间(秒)')
    hit_count = Column(Integer, default=0, comment='命中次数')
    last_hit_at = Column(DateTime, comment='最后命中时间')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, comment='过期时间')

    __table_args__ = (
        Index('qsc_cache_key', 'cache_key'),
        Index('qsc_cache_type', 'cache_type'),
        Index('qsc_city_block', 'city', 'block'),
        Index('qsc_expires', 'expires_at'),
    )


class TaskQuantBinding(Base):
    """深度融合-任务量化关联绑定表"""
    __tablename__ = 'task_quant_bindings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    binding_id = Column(String(32), unique=True, nullable=False)
    task_id = Column(String(40), nullable=False, index=True, comment='关联的任务ID')
    task_type = Column(String(30), comment='任务类型')
    city = Column(String(50), index=True)
    district = Column(String(50))
    recommended_block = Column(String(80), comment='自动推荐板块')
    quant_summary_json = Column(JSON, comment='量化摘要(predicted_growth/risk_level/advice/top_factor)')
    full_report_ref = Column(String(64), comment='完整报告缓存引用')
    attached_at = Column(DateTime, default=datetime.utcnow, comment='绑定时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('tqb_task_id', 'task_id'),
        Index('tqb_city', 'city'),
    )


class BatchComparisonRecord(Base):
    """深度融合-批量对比记录表"""
    __tablename__ = 'batch_comparison_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(String(32), unique=True, nullable=False)
    user_id = Column(String(64), index=True)
    task_ids_json = Column(JSON, comment='参与对比的任务ID列表')
    items_json = Column(JSON, comment='对比项数据(city/block/growth/risk/sharpe等)')
    best_growth_item = Column(JSON, comment='最高涨幅项')
    lowest_risk_item = Column(JSON, comment='最低风险项')
    ranking_by_growth = Column(JSON, comment='按涨幅排名')
    ranking_by_risk = Column(JSON, comment='按风险排名')
    export_format = Column(String(10), comment='csv/pdf/none')
    export_path = Column(String(300), comment='导出文件路径')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('bcr_comparison_id', 'comparison_id'),
        Index('bcr_user', 'user_id'),
    )


class ConsultationSessionRecord(Base):
    """深度融合-咨询会话记录表"""
    __tablename__ = 'consultation_session_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(40), unique=True, nullable=False)
    user_id = Column(String(64), index=True)
    persona = Column(String(15), comment='zhouyu/luxun')
    status = Column(String(15), default='active', comment='active/completed/expired')
    current_step = Column(String(20), comment='当前对话流程步骤')
    step_history_json = Column(JSON, comment='步骤历史栈')
    extracted_params_json = Column(JSON, comment='已提取参数(city/block/horizon/risk_tolerance)')
    intent_history_json = Column(JSON, comment='意图识别历史')
    turn_count = Column(Integer, default=0)
    satisfaction_score = Column(Float, comment='满意度评分(1-5)')
    created_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime)

    __table_args__ = (
        Index('csr_session_id', 'session_id'),
        Index('csr_user_persona', 'user_id', 'persona'),
    )


class ConsultationTurnRecord(Base):
    """深度融合-咨询轮次记录表"""
    __tablename__ = 'consultation_turn_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    turn_id = Column(String(32), unique=True, nullable=False)
    session_id = Column(String(40), nullable=False, index=True)
    turn_number = Column(Integer, comment='轮次序号')
    user_input_raw = Column(Text, comment='用户原始输入')
    intent_classified = Column(String(30), comment='识别的意图类型')
    params_extracted_json = Column(JSON, comment='本轮提取的参数')
    nlg_template_used = Column(String(30), comment='使用的NLG模板名称')
    persona_applied = Column(String(15), comment='应用的人设')
    agent_response_text = Column(Text, comment='智能体回复文本')
    card_data_json = Column(JSON, comment='插入的卡片数据')
    followup_suggestions_json = Column(JSON, comment='追问建议列表')
    quant_report_ref = Column(String(64), comment='引用的量化报告缓存键')
    processing_time_ms = Column(Float, comment='处理耗时(毫秒)')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ctr_turn_id', 'turn_id'),
        Index('ctr_session', 'session_id'),
        Index('ctr_intent', 'intent_classified'),
    )


class DialogueFlowLog(Base):
    """深度融合-对话流程日志表"""
    __tablename__ = 'dialogue_flow_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(32), unique=True, nullable=False)
    session_id = Column(String(40), index=True)
    step_name = Column(String(30), comment='步骤名:intent_recognition/param_extraction/quant_call/nlg_generation/card_insertion/followup')
    step_status = Column(String(15), comment='success/skip/error/timeout')
    input_data_hash = Column(String(32), comment='输入数据指纹')
    output_size_bytes = Column(Integer, comment='输出大小(字节)')
    error_message = Column(Text)
    duration_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('dfl_log_id', 'log_id'),
        Index('dfl_session_step', 'session_id', 'step_name'),
    )


class ComponentRenderLog(Base):
    """深度融合-前端组件渲染日志表"""
    __tablename__ = 'component_render_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    render_id = Column(String(32), unique=True, nullable=False)
    component_type = Column(String(30), comment='quant_report/summary_card/param_slider/quant_compare')
    render_mode = Column(String(15), comment='embedded/fullscreen/chat_card/dashboard_tab/compare')
    props_json = Column(JSON, comment='传入props')
    render_time_ms = Column(Float, comment='渲染耗时')
    viewport_width = Column(Integer, comment='视口宽度(px)')
    is_mobile = Column(Boolean, default=False)
    error_occurred = Column(Boolean, default=False)
    user_id = Column(String(64))
    session_id = Column(String(40))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('crl_component_mode', 'component_type', 'render_mode'),
        Index('crl_mobile', 'is_mobile'),
    )


class PrefetchEventLog(Base):
    """深度融合-预取事件日志表"""
    __tablename__ = 'prefetch_event_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prefetch_id = Column(String(32), unique=True, nullable=False)
    target_type = Column(String(20), comment='quant_summary/block_comparison/factor_detail')
    target_key = Column(String(128), comment='目标标识(cache_key或comparison_id)')
    trigger_type = Column(String(15), default='hover', comment='hover/click/proximity/scroll')
    lifecycle_state = Column(String(15), comment='pending/triggered/loaded/error')
    triggered_at = Column(DateTime, comment='触发时间')
    loaded_at = Column(DateTime, comment='加载完成时间')
    time_to_load_ms = Column(Float, comment='触发到加载完成耗时')
    cache_hit = Column(Boolean, default=False, comment='是否命中缓存')
    payload_size_bytes = Column(Integer)
    error_message = Column(Text)
    user_id = Column(String(64))

    __table_args__ = (
        Index('pel_prefetch_id', 'prefetch_id'),
        Index('pel_target_type', 'target_type'),
        Index('pel_lifecycle', 'lifecycle_state'),
    )


class MobileAdaptationProfile(Base):
    """深度融合-移动端适配配置表"""
    __tablename__ = 'mobile_adaptation_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(24), unique=True, nullable=False)
    device_category = Column(String(15), comment='phone/tablet/phablet/desktop')
    screen_width_range = Column(String(20), comment='如 0-768/769-1024/1025+')
    chart_height_small = Column(Integer, default=300, comment='小屏图表高度(px)')
    radar_to_bars_enabled = Column(Boolean, default=True, comment='雷达图→柱状图转换')
    param_slider_drawer = Column(Boolean, default=True, comment='参数滑块抽屉模式')
    touch_min_size_px = Column(Integer, default=44, comment='触控最小尺寸(px)')
    font_scale_factor = Column(Float, default=1.0, comment='字体缩放因子')
    grid_columns = Column(Integer, default=1, comment='网格列数')
    css_overrides_json = Column(JSON, comment='自定义CSS覆盖规则')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('map_device', 'device_category'),
    )


class DeepFusionAnalyticsDaily(Base):
    """深度融合-分析日报聚合表"""
    __tablename__ = 'deep_fusion_analytics_daily'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    total_quant_requests = Column(Integer, default=0, comment='总量化请求量')
    cache_hit_rate = Column(Float, comment='缓存命中率(0-1)')
    avg_response_time_ms = Column(Float, comment='平均响应时间(ms)')
    total_consultation_sessions = Column(Integer, default=0, comment='总咨询会话数')
    avg_turns_per_session = Column(Float, comment='平均每会话轮次')
    intent_distribution_json = Column(JSON, comment='意图分布统计')
    top_cities_json = Column(JSON, comment='热门城市TOP10')
    component_render_counts_json = Column(JSON, comment='组件渲染次数统计')
    mobile_traffic_ratio = Column(Float, comment='移动端流量占比')
    prefetch_success_rate = Column(Float, comment='预取成功率')
    error_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('dfa_date', 'date'),
    )


class NLGTemplateVariant(Base):
    """深度融合-NLG模板变体表"""
    __tablename__ = 'nlg_template_variants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    variant_id = Column(String(24), unique=True, nullable=False)
    template_name = Column(String(40), comment='模板标识名')
    persona = Column(String(15), comment='zhouyu/luxun')
    intent_type = Column(String(25), comment='initial_investment/comparison/param_adjustment/factor_explain/backtest_history')
    template_content = Column(Text, nullable=False, comment='NLG模板文本(含{占位符})')
    tone_style = Column(String(20), comment='bold_confident/thorough_cautionary')
    version = Column(Integer, default=1)
    ab_test_group = Column(String(5), comment='a/b/control')
    usage_count = Column(Integer, default=0)
    avg_satisfaction = Column(Float, comment='平均用户满意度')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ntv_persona_intent', 'persona', 'intent_type'),
        Index('ntv_template_name', 'template_name'),
    )


class ParamAdjustmentHistory(Base):
    """深度融合-参数调整历史表"""
    __tablename__ = 'param_adjustment_histories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    adjustment_id = Column(String(32), unique=True, nullable=False)
    session_id = Column(String(40), index=True)
    user_id = Column(String(64))
    param_name = Column(String(20), comment='horizon/risk_tolerance/city/block')
    old_value = Column(String(50))
    new_value = Column(String(50))
    adjustment_source = Column(String(20), comment='user_input/nlg_suggestion/auto_recommend')
    recompute_triggered = Column(Boolean, default=False, comment='是否触发重新计算')
    delta_comment = Column(Text, comment='变化说明文本')
    turn_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('pah_session_param', 'session_id', 'param_name'),
        Index('pah_user', 'user_id'),
    )


class FollowUpSuggestionLog(Base):
    """深度融合-追问建议日志表"""
    __tablename__ = 'follow_up_suggestion_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(32), unique=True, nullable=False)
    session_id = Column(String(40), index=True)
    turn_id = Column(String(32))
    suggestions_json = Column(JSON, nullable=False, comment='建议列表[{text,type,payload}]')
    selected_suggestion_index = Column(Integer, comment='用户选择的建议索引(-1未选择)')
    selected_suggestion_text = Column(String(200), comment='用户选择的建议文本')
    context_report_ref = Column(String(64), comment='上下文量化报告引用')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('fusl_session', 'session_id'),
    )


# ==================== Part 28: GUI自动化层 (GUI Automation Layer - Mano-P) ====================
# 对应 gui_automation_layer.py — 视觉操作执行+网页爬取+报告自动生成+Agent自主编排+工作流管理+安全防护


class GUIActionExecutionRecord(Base):
    __tablename__ = 'gui_action_execution_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exec_id = Column(String(14), unique=True, nullable=False)
    step_id = Column(String(20))
    action_type = Column(String(15), index=True)
    target_selector = Column(String(200))
    target_type = Column(String(15))
    coordinate_x = Column(Float)
    coordinate_y = Column(Float)
    value_text = Column(Text)
    params_json = Column(JSON)
    status = Column(String(10), default='success')
    result_data_json = Column(JSON)
    error_message = Column(Text)
    duration_ms = Column(Float)
    screenshot_taken = Column(Boolean, default=False)
    session_id = Column(String(20), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class GUIScreenCapture(Base):
    __tablename__ = 'gui_screen_captures'
    id = Column(Integer, primary_key=True, autoincrement=True)
    capture_id = Column(String(12), unique=True, nullable=False)
    task_id = Column(String(16))
    step_id = Column(String(20))
    image_path = Column(String(300))
    image_b64_preview = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    window_title = Column(String(100))
    resolution = Column(String(12), default='1920x1080')
    detected_elements_json = Column(JSON)
    ocr_extracted_text = Column(Text)
    session_id = Column(String(20))


class WebScrapingJob(Base):
    __tablename__ = 'web_scraping_jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(14), unique=True, nullable=False)
    template_id = Column(String(30), index=True)
    template_name = Column(String(50))
    target_url = Column(String(300))
    district_param = Column(String(50))
    max_items = Column(Integer, default=100)
    pages_scraped = Column(Integer, default=0)
    total_items_collected = Column(Integer, default=0)
    status = Column(String(15), default='completed')
    scrape_duration_sec = Column(Float)
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ScrapedDataItem(Base):
    __tablename__ = 'scraped_data_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(18), unique=True, nullable=False)
    scraping_job_id = Column(String(14), index=True)
    source_url = Column(String(300))
    source_page_num = Column(Integer)
    field_name = Column(String(30))
    field_value = Column(Text)
    field_type = Column(String(10))
    confidence = Column(Float)
    extracted_at = Column(DateTime, default=datetime.utcnow, index=True)
    xpath_or_selector = Column(String(200))


class ReportGenerationRecord(Base):
    __tablename__ = 'report_generation_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_id = Column(String(14), unique=True, nullable=False)
    template_id = Column(String(20))
    template_name = Column(String(50))
    data_bindings_hash = Column(String(24))
    steps_executed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    processing_time_sec = Column(Float)
    output_files_json = Column(JSON)
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentAutonomousSession(Base):
    __tablename__ = 'agent_autonomous_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(16), unique=True, nullable=False)
    agent_id = Column(String(40))
    goal_description = Column(Text)
    autonomy_level = Column(String(20), default='level_2_supervised')
    plan_tasks_json = Column(JSON)
    current_task_idx = Column(Integer, default=0)
    tasks_completed_count = Column(Integer, default=0)
    decisions_made_json = Column(JSON)
    self_corrections_count = Column(Integer, default=0)
    human_interventions_count = Column(Integer, default=0)
    status = Column(String(15), default='planning', index=True)
    started_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    completed_at = Column(DateTime)
    summary_json = Column(JSON)


class WorkflowDefinitionRecord(Base):
    __tablename__ = 'workflow_definition_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(80))
    category = Column(String(25), index=True)
    description = Column(Text)
    steps_template_json = Column(JSON)
    target_platform = Column(String(15))
    estimated_duration_min = Column(Float)
    success_rate_history = Column(Float, default=0.9)
    is_public = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    execution_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class WorkflowExecutionLog(Base):
    __tablename__ = 'workflow_execution_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(16), unique=True, nullable=False)
    workflow_id = Column(String(20), index=True)
    success = Column(Boolean, default=True)
    duration_sec = Column(Float)
    executed_by_agent = Column(String(40))
    triggered_by = Column(String(20), comment='schedule/manual/api/event')
    output_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class GUISafetyAuditLog(Base):
    __tablename__ = 'gui_safety_audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(18), unique=True, nullable=False)
    event_type = Column(String(30), index=True)
    details_json = Column(JSON)
    user_or_session_id = Column(String(40))
    blocked = Column(Boolean, default=False)
    severity = Column(String(10), default='info', comment='info/warning/critical')
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class GUILimitTracker(Base):
    __tablename__ = 'gui_limit_trackers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tracker_key = Column(String(60), unique=True, nullable=False)
    user_id = Column(String(64), index=True)
    date_str = Column(Date, index=True)
    daily_action_count = Column(Integer, default=0)
    hourly_counts_json = Column(JSON)
    daily_limit = Column(Integer, default=10000)
    hourly_limit = Column(Integer, default=500)
    limit_exceeded_count = Column(Integer, default=0)
    last_checked_at = Column(DateTime)
    reset_at = Column(DateTime, default=datetime.utcnow)


# ==================== Part 27: 视频生成层 (Video Generation Layer - LingBot-World) ====================
# 对应 video_generation_layer.py — 房源漫游+社区动画+量化可视化+营销视频+管理看板+Prompt工程


class VideoGenerationJob(Base):
    __tablename__ = 'video_generation_jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(16), unique=True, nullable=False)
    task_type = Column(String(30), index=True)
    input_image_paths_json = Column(JSON)
    prompt_text = Column(Text)
    negative_prompt = Column(Text)
    resolution = Column(String(8))
    frame_num = Column(Integer)
    fps = Column(Integer, default=16)
    model_variant = Column(String(12))
    guidance_scale = Column(Float)
    inference_steps = Column(Integer)
    seed = Column(Integer)
    status = Column(String(15), default='queued', index=True)
    video_path = Column(String(300))
    thumbnail_path = Column(String(300))
    duration_seconds = Column(Float)
    file_size_mb = Column(Float)
    gpu_memory_gb = Column(Float)
    processing_time_sec = Column(Float)
    error_message = Column(Text)
    metadata_json = Column(JSON)
    user_id = Column(String(64), index=True)
    priority = Column(Integer, default=0)
    callback_url = Column(String(300))
    queue_position = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PropertyTourRecord(Base):
    __tablename__ = 'property_tour_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tour_id = Column(String(16), unique=True, nullable=False)
    property_id = Column(String(40))
    room_images_json = Column(JSON)
    room_sequence_json = Column(JSON)
    dwell_time_per_room = Column(Float, default=3.0)
    transition_style = Column(String(20))
    total_duration_target = Column(Integer, default=30)
    background_music = Column(String(30))
    text_overlays_enabled = Column(Boolean, default=True)
    logo_watermark_enabled = Column(Boolean, default=True)
    camera_poses_json = Column(JSON)
    video_job_id = Column(String(16))
    created_at = Column(DateTime, default=datetime.utcnow)


class CommunityAnimationRecord(Base):
    __tablename__ = 'community_animation_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    animation_id = Column(String(14), unique=True, nullable=False)
    scenario_id = Column(String(20), index=True)
    scenario_name = Column(String(50))
    city_code = Column(String(20))
    block_name = Column(String(50))
    prompt_text = Column(Text)
    duration_sec = Column(Integer, default=20)
    resolution = Column(String(8))
    video_job_id = Column(String(14))
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class QuantVizVideoRecord(Base):
    __tablename__ = 'quant_viz_video_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    viz_id = Column(String(14), unique=True, nullable=False)
    chart_type = Column(String(20), comment='prediction_curve/factor_radar/bar_race/candlestick/heatmap')
    animation_style = Column(String(20))
    city_code = Column(String(20))
    block_name = Column(String(50))
    data_summary = Column(Text)
    horizon_months = Column(Integer)
    include_confidence_band = Column(Boolean)
    factor_count = Column(Integer)
    color_theme = Column(String(20))
    video_job_id = Column(String(14))
    prediction_id_ref = Column(String(16))
    created_at = Column(DateTime, default=datetime.utcnow)


class MarketingVideoRecord(Base):
    __tablename__ = 'marketing_video_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    production_id = Column(String(14), unique=True, nullable=False)
    template_id = Column(String(10))
    template_name = Column(String(40))
    property_info_json = Column(JSON)
    platform = Column(String(15), index=True)
    aspect_ratio = Column(String(6))
    filled_text_slots_json = Column(JSON)
    image_count = Column(Integer)
    music_track = Column(String(30))
    video_job_id = Column(String(14))
    batch_job_id = Column(String(10))
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class MarketingBatchJob(Base):
    __tablename__ = 'marketing_batch_jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(10), unique=True, nullable=False)
    template_id = Column(String(10))
    platform = Column(String(15))
    total_properties = Column(Integer)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    production_ids_json = Column(JSON)
    status = Column(String(15), default='processing')
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class VideoAnalyticsSnapshot(Base):
    __tablename__ = 'video_analytics_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(12), unique=True, nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    total_videos_generated = Column(Integer, default=0)
    successful_today = Column(Integer, default=0)
    failed_today = Column(Integer, default=0)
    success_rate_pct = Column(Float)
    avg_processing_time_sec = Column(Float)
    gpu_hours_consumed = Column(Float)
    storage_used_gb = Column(Float)
    by_task_type_json = Column(JSON)
    by_resolution_json = Column(JSON)
    by_platform_json = Column(JSON)


class VideoPromptCache(Base):
    __tablename__ = 'video_prompt_cache'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(32), unique=True, nullable=False, index=True)
    prompt_text = Column(Text, nullable=False)
    task_type = Column(String(30))
    parameters_hash = Column(String(24))
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_debug_session_id', 'session_id'),
        Index('idx_sf_debug_status', 'status'),
        Index('idx_sf_debug_created', 'created_at'),
    )


class SFSSEEventLog(Base):
    __tablename__ = 'sf_sse_event_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(20), comment='thinking/text/complete/error/done')
    chunk_index = Column(Integer, comment='Chunk sequence number')
    content = Column(Text, comment='Event data content')
    content_length = Column(Integer, comment='Content length in chars')
    elapsed_ms = Column(Float, comment='Elapsed time since request start (ms)')
    interval_ms = Column(Float, comment='Interval since previous chunk (ms)')
    parse_error = Column(Boolean, default=False, comment='JSON parse error flag')
    raw_data = Column(Text, comment='Raw SSE data line')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_sse_session', 'session_id'),
        Index('idx_sf_sse_event_type', 'event_type'),
        Index('idx_sf_sse_chunk_index', 'chunk_index'),
    )


class SFRequestLog(Base):
    __tablename__ = 'sf_request_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), unique=True, nullable=False)
    url = Column(String(512), comment='Request URL')
    method = Column(String(10), default='POST')
    request_params = Column(JSON, comment='Request parameters')
    user_agent = Column(String(255))
    client_ip = Column(String(45))
    status_code = Column(Integer, comment='HTTP response status')
    response_content_type = Column(String(100))
    is_streaming = Column(Boolean, default=False)
    ttfb_ms = Column(Float)
    total_time_ms = Column(Float)
    bytes_received = Column(Integer, default=0)
    chunks_received = Column(Integer, default=0)
    aborted = Column(Boolean, default=False)
    abort_reason = Column(String(100))
    error_category = Column(String(30), comment='timeout/network/server/abort/parse/unknown')
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_req_request_id', 'request_id'),
        Index('idx_sf_req_status', 'status_code'),
        Index('idx_sf_req_error_cat', 'error_category'),
        Index('idx_sf_req_created', 'created_at'),
    )


class SFPerformanceSnapshot(Base):
    __tablename__ = 'sf_performance_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    metric_name = Column(String(50), nullable=False, comment='ttfb/first_token/total_time/p99_latency/throughput/memory')
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), comment='ms/chars/s/MB')
    threshold = Column(Float, comment='Target threshold value')
    passed = Column(Boolean, default=True)
    window_minutes = Column(Integer, default=5, comment='Aggregation window')
    sample_count = Column(Integer, default=1)
    p50 = Column(Float, comment='50th percentile')
    p95 = Column(Float, comment='95th percentile')
    p99 = Column(Float, comment='99th percentile')
    min_val = Column(Float)
    max_val = Column(Float)
    avg_val = Column(Float)
    std_dev = Column(Float)
    __table_args__ = (
        Index('idx_sf_perf_snapshot_time', 'snapshot_time'),
        Index('idx_sf_perf_metric_name', 'metric_name'),
        Index('idx_sf_perf_passed', 'passed'),
    )


class SFTestResult(Base):
    __tablename__ = 'sf_test_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_suite_id = Column(String(64), comment='Test suite run identifier')
    test_name = Column(String(100), nullable=False)
    test_category = Column(String(30), comment='functional/performance/mobile/error_recovery')
    status = Column(String(20), comment='passed/failed/skipped/error')
    duration_ms = Column(Float)
    assertions_total = Column(Integer, default=0)
    assertions_passed = Column(Integer, default=0)
    error_message = Column(Text)
    stack_trace = Column(Text)
    screenshot_path = Column(String(512))
    metrics_collected = Column(JSON, comment='Test-specific metrics')
    browser_info = Column(String(255), comment='Browser UA for E2E tests')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_test_suite', 'test_suite_id'),
        Index('idx_sf_test_name', 'test_name'),
        Index('idx_sf_test_status', 'status'),
        Index('idx_sf_test_created', 'created_at'),
    )


class SFDeploymentCheck(Base):
    __tablename__ = 'sf_deployment_checks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_run_id = Column(String(64), unique=True, nullable=False)
    check_item = Column(String(100), nullable=False, comment='sse_format/frontend_parser/error_friendly/mobile_touch/performance_ok')
    status = Column(String(20), comment='pass/fail/warning/skip')
    severity = Column(String(10), comment='critical/major/minor/info')
    description = Column(Text, comment='Check description')
    details = Column(JSON, comment='Check result details')
    recommendation = Column(Text, comment='Recommended action')
    auto_fixable = Column(Boolean, default=False)
    fixed_automatically = Column(Boolean, default=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_deploy_run', 'check_run_id'),
        Index('idx_sf_deploy_item', 'check_item'),
        Index('idx_sf_deploy_status', 'status'),
    )


class SFFixReport(Base):
    __tablename__ = 'sf_fix_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(64), unique=True, nullable=False)
    title = Column(String(200), default='Streaming Fix Diagnostic Report')
    generated_at = Column(DateTime, default=datetime.utcnow)
    total_issues_found = Column(Integer, default=0)
    issues_critical = Column(Integer, default=0)
    issues_major = Column(Integer, default=0)
    issues_minor = Column(Integer, default=0)
    issues_info = Column(Integer, default=0)
    fixes_recommended = Column(Integer, default=0)
    fixes_applied = Column(Integer, default=0)
    issue_details = Column(JSON, comment='Array of issue objects with file/line/description/fix')
    performance_baseline = Column(JSON, comment='Baseline metrics before fix')
    deployment_check_results = Column(JSON, comment='Deployment checklist summary')
    recommendations = Column(JSON, comment='Prioritized recommendation list')
    report_markdown = Column(Text, comment='Full markdown report content')
    __table_args__ = (
        Index('idx_sf_report_id', 'report_id'),
        Index('idx_sf_report_generated', 'generated_at'),
    )


class SFErrorRecoveryLog(Base):
    __tablename__ = 'sf_error_recovery_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), index=True)
    error_category = Column(String(30), comment='timeout/network/server/abort/parse')
    error_name = Column(String(100), comment='Error class name e.g. TimeoutError')
    error_message = Column(Text)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    recovery_strategy = Column(String(50), comment='Strategy applied: retry/user_notify/fallback/silent')
    recovery_successful = Column(Boolean, default=False)
    recovery_time_ms = Column(Float, comment='Time to recovery in ms')
    user_visible_message = Column(Text, comment='Message shown to user')
    retry_attempt = Column(Integer, default=0)
    context_before_error = Column(JSON, comment='State snapshot before error')
    __table_args__ = (
        Index('idx_sf_err_rec_category', 'error_category'),
        Index('idx_sf_err_rec_strategy', 'recovery_strategy'),
        Index('idx_sf_err_rec_occurred', 'occurred_at'),
    )


class SFMemoryEvictionLog(Base):
    __tablename__ = 'sf_memory_eviction_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    eviction_reason = Column(String(30), comment='limit_reached/lru/manual')
    messages_before = Column(Integer, comment='Message count before eviction')
    messages_after = Column(Integer, comment='Message count after eviction')
    evicted_message_ids = Column(JSON, comment='IDs of evicted messages')
    evicted_message_summaries = Column(JSON, comment='Summaries of evicted messages')
    total_eviction_count = Column(Integer, default=0, comment='Running total for session')
    memory_estimate_bytes = Column(Integer, comment='Estimated memory usage after eviction')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_mem_evict_session', 'session_id'),
        Index('idx_sf_mem_evict_reason', 'eviction_reason'),
    )


class SFBenchmarkResult(Base):
    __tablename__ = 'sf_benchmark_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_run_id = Column(String(64), nullable=False)
    benchmark_name = Column(String(100), nullable=False, comment='ttfb/first_token/p99_latency/throughput/memory')
    target_threshold = Column(Float, comment='Target value to meet')
    actual_value = Column(Float, comment='Measured value')
    unit = Column(String(20))
    passed = Column(Boolean, default=False)
    sample_size = Column(Integer, default=1)
    avg_value = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    percentile_95 = Column(Float)
    stddev = Column(Float)
    environment_info = Column(JSON, comment='CPU/RAM/browser info at time of test')
    run_timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_sf_bench_run', 'benchmark_run_id'),
        Index('idx_sf_bench_name', 'benchmark_name'),
        Index('idx_sf_bench_passed', 'passed'),
        Index('idx_sf_bench_timestamp', 'run_timestamp'),
    )


# ==================== Part 20: 流式渲染修复层 (Streaming Fix Layer) ====================
# 对应 streaming_fix_layer.py — SSE流式输出修复与优化


class SFPipelineHealthSnapshot(Base):
    __tablename__ = 'sf_pipeline_health_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    total_active_sessions = Column(Integer, default=0)
    avg_ttfb_ms = Column(Float, comment='Average Time To First Byte')
    p95_latency_ms = Column(Float, comment='95th percentile latency')
    error_rate_pct = Column(Float, comment='Error rate percentage')
    queue_depth = Column(Integer, default=0)
    memory_usage_mb = Column(Float)
    cpu_usage_pct = Column(Float)
    sse_connections_active = Column(Integer, default=0)
    abort_count_1h = Column(Integer, default=0)
    health_score = Column(Float, comment='Composite health 0-100')
    alert_flags = Column(JSON, comment='Active alert flags')
    __table_args__ = (
        Index('idx_sf_pipe_health_time', 'snapshot_time'),
        Index('idx_sf_pipe_health_score', 'health_score'),
    )


class SSEConnectionLog(Base):
    __tablename__ = 'sse_connection_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(64), unique=True, nullable=False)
    session_id = Column(String(100), index=True)
    user_id_encrypted = Column(String(64))
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime)
    duration_seconds = Column(Float)
    event_count = Column(Integer, default=0)
    bytes_sent = Column(Integer, default=0)
    disconnect_reason = Column(String(50), comment='normal/timeout/error/abort/client_close')
    client_ip_hashed = Column(String(64))
    user_agent = Column(String(255))
    protocol = Column(String(10), default='SSE')
    __table_args__ = (
        Index('idx_sse_conn_session', 'session_id'),
        Index('idx_sse_conn_connected', 'connected_at'),
        Index('idx_sse_conn_reason', 'disconnect_reason'),
    )


class StreamingConfigVersion(Base):
    __tablename__ = 'streaming_config_versions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(String(32), unique=True, nullable=False)
    config_category = Column(String(30), comment='sse/parser/hook/timeout/mobile/perf')
    config_json = Column(JSON, nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    applied_by = Column(String(64), comment='User or system that applied this config')
    rollback_version_id = Column(String(32), comment='Previous version for rollback')
    is_active = Column(Boolean, default=True)
    change_description = Column(Text)
    __table_args__ = (
        Index('idx_stream_cfg_category', 'config_category'),
        Index('idx_stream_cfg_active', 'is_active'),
        Index('idx_stream_cfg_applied', 'applied_at'),
    )


# ==================== Part 21: 房产量化分析层 (Real Estate Quantitative Analysis Layer) ====================
# 对应 quantitative_analysis_layer.py — 数据仓库+因子挖掘+预测模型+回测框架+风险管理+决策支持


class QuantFactor(Base):
    __tablename__ = 'quant_factors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_code = Column(String(50), unique=True, nullable=False, comment='e.g. PE_RATIO, SUPPLY_DEMAND_GAP')
    factor_name = Column(String(100), nullable=False)
    category = Column(String(30), comment='price/supply_demand/facility/policy/macro/sentiment')
    formula = Column(Text, comment='Formula expression')
    description = Column(Text)
    unit = Column(String(20))
    frequency = Column(String(10), comment='daily/weekly/monthly/quarterly')
    min_value = Column(Float)
    max_value = Column(Float)
    data_source = Column(String(50), comment='beike/fangtianxia/gov_open_data/urban_planning')
    is_composite = Column(Boolean, default=False)
    component_factor_codes = Column(JSON, comment='For composite factors')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    ic_pearson_avg = Column(Float, comment='Avg Pearson IC across periods')
    ic_spearman_avg = Column(Float, comment='Avg Spearman IC across periods')
    ir_score = Column(Float, comment='Information Ratio = mean(IC)/std(IC)')
    group_monotonicity = Column(Float, comment='Group monotonicity score 0-1')
    __table_args__ = (
        Index('idx_qf_code', 'factor_code'),
        Index('idx_qf_category', 'category'),
        Index('idx_qf_active', 'is_active'),
        Index('idx_qf_ic', 'ic_pearson_avg'),
    )


class QuantFactorValue(Base):
    __tablename__ = 'quant_factor_values'
    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_code = Column(String(50), nullable=False, index=True)
    city_code = Column(String(20), index=True)
    district_code = Column(String(20))
    plate_code = Column(String(20))
    date = Column(Date, index=True)
    granularity = Column(String(10), comment='city/district/plate/community')
    raw_value = Column(Float)
    normalized_value = Column(Float, comment='0-1 normalized')
    rank_percentile = Column(Float, comment='0-100 percentile rank')
    confidence = Column(Float, comment='Data quality confidence 0-1')
    source_system = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_qfv_factor_date', 'factor_code', 'date'),
        Index('idx_qfv_city_date', 'city_code', 'date'),
        Index('idx_qfv_district', 'district_code', 'date'),
        UniqueConstraint('factor_code', 'city_code', 'district_code', 'plate_code', 'date', 'granularity',
                         name='uq_factor_value'),
    )


class QuantPrediction(Base):
    __tablename__ = 'quant_predictions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(String(40), unique=True, nullable=False)
    model_name = Column(String(80), nullable=False, index=True)
    model_type = Column(String(30), comment='prophet/arima/xgboost/lightgbm/transformer/informer')
    model_version = Column(String(20))
    target_city_code = Column(String(20), index=True)
    target_district_code = Column(String(20))
    target_plate_code = Column(String(20))
    prediction_horizon_days = Column(Integer, comment='Days ahead predicted')
    predicted_value = Column(Float, nullable=False)
    lower_bound_ci = Column(Float, comment='Lower confidence interval')
    upper_bound_ci = Column(Float, comment='Upper confidence interval')
    actual_value = Column(Float, comment='Filled when actual observed')
    prediction_date = Column(DateTime, default=datetime.utcnow, index=True)
    target_date = Column(Date, comment='Date being predicted for')
    features_used = Column(JSON, comment='Top contributing factors with weights')
    mape = Column(Float, comment='MAPE after actual observed')
    r_squared = Column(Float)
    status = Column(String(15), default='pending', comment='pending/observed/expired')
    __table_args__ = (
        Index('idx_qp_model_city', 'model_name', 'target_city_code'),
        Index('idx_qp_target_date', 'target_date'),
        Index('idx_qp_status', 'status'),
    )


class QuantModelRegistry(Base):
    __tablename__ = 'quant_model_registry'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(40), unique=True, nullable=False)
    model_name = Column(String(80), nullable=False)
    model_type = Column(String(30), index=True)
    version = Column(String(20), nullable=False)
    stage = Column(String(15), default='registered', comment='registered/staging/production/deprecated')
    training_data_end_date = Column(Date)
    feature_count = Column(Integer, default=0)
    hyperparameters = Column(JSON)
    metrics_train = Column(JSON, comment='Training set metrics')
    metrics_val = Column(JSON, comment='Validation set metrics')
    metrics_test = Column(JSON, comment='Test set metrics')
    r_squared = Column(Float)
    mape = Column(Float)
    sharpe_simulated = Column(Float)
    file_path = Column(String(255), comment='Serialized model file path')
    registered_at = Column(DateTime, default=datetime.utcnow)
    promoted_to_production_at = Column(DateTime)
    deprecated_at = Column(DateTime)
    deprecation_reason = Column(Text)
    is_ab_test_winner = Column(Boolean, default=False)
    ab_test_traffic_split = Column(Float, comment='Traffic split ratio 0-1')
    parent_model_id = Column(String(40), comment='Rollback source model id')
    __table_args__ = (
        Index('idx_qmr_name_version', 'model_name', 'version'),
        Index('idx_qmr_stage_type', 'stage', 'model_type'),
        Index('idx_qmr_r2', 'r_squared'),
    )


class QuantBacktestRun(Base):
    __tablename__ = 'quant_backtest_runs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(40), unique=True, nullable=False)
    strategy_type = Column(String(25), nullable=False, index=True,
                           comment='buy_and_hold/periodic_rebalance/prediction_ranking/momentum/mean_reversion')
    model_id = Column(String(40), comment='Model used if applicable')
    city_code = Column(String(20), index=True)
    district_code = Column(String(20))
    start_date = Column(Date)
    end_date = Column(Date)
    initial_capital = Column(Float, default=1000000)
    final_value = Column(Float)
    total_return_pct = Column(Float)
    annualized_return_pct = Column(Float)
    volatility_annualized = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    max_drawdown_duration_days = Column(Integer)
    win_rate_pct = Column(Float)
    profit_loss_ratio = Column(Float)
    trade_count = Column(Integer, default=0)
    transaction_cost_total = Column(Float)
    benchmark_return_pct = Column(Float, comment='Buy-and-hold baseline return')
    alpha_pct = Column(Float, comment='Excess return over benchmark')
    run_at = Column(DateTime, default=datetime.utcnow)
    trade_records = Column(JSON, comment='Array of individual trades')
    daily_pnl_series = Column(JSON, comment='Daily P&L time series')
    __table_args__ = (
        Index('idx_qbr_strategy_city', 'strategy_type', 'city_code'),
        Index('idx_qbr_run_date', 'run_at'),
        Index('idx_qbr_sharpe', 'sharpe_ratio'),
    )


class QuantVaRSnapshot(Base):
    __tablename__ = 'quant_var_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(40), unique=True, nullable=False)
    city_code = Column(String(20), nullable=False, index=True)
    district_code = Column(String(20), index=True)
    calculation_method = Column(String(15), comment='historical/parametric')
    confidence_level = Column(Float, default=0.95, comment='0.95 or 0.99')
    var_value = Column(Float, nullable=False, comment='VaR amount')
    cvar_value = Column(Float, comment='Conditional VaR / Expected Shortfall')
    lookback_days = Column(Integer, default=250)
    return_mean = Column(Float)
    return_std = Column(Float)
    z_score = Column(Float)
    worst_case_return = Column(Float)
    interpretation_text = Column(Text, comment='Human-readable risk explanation')
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qvar_city_district', 'city_code', 'district_code'),
        Index('idx_qvar_confidence', 'confidence_level'),
        Index('idx_qvar_method', 'calculation_method'),
    )


class QuantPolicyRiskScore(Base):
    __tablename__ = 'quant_policy_risk_scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    score_id = Column(String(40), unique=True, nullable=False)
    city_code = Column(String(20), nullable=False, index=True)
    district_code = Column(String(20))
    composite_score = Column(Float, comment='0-100 composite risk score')
    risk_level = Column(String(12), comment='LOW/MEDIUM/HIGH/CRITICAL')
    event_intensity_score = Column(Float, comment='Weighted recent policy intensity')
    recency_decay_factor = Column(Float)
    significant_events = Column(JSON, comment='Top impactful recent events')
    event_study_pvalue = Column(Float, comment='T-test p-value for significance')
    trend_direction = Column(String(10), comment='tightening/loosening/neutral/stable')
    affected_sectors = Column(JSON, comment='Sectors most impacted')
    recommendation = Column(Text)
    scored_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qpr_city_level', 'city_code', 'risk_level'),
        Index('idx_qpr_score', 'composite_score'),
    )


class QuantLiquidityGrade(Base):
    __tablename__ = 'quant_liquidity_grades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    grade_id = Column(String(40), unique=True, nullable=False)
    city_code = Column(String(20), nullable=False, index=True)
    district_code = Column(String(20), index=True)
    plate_code = Column(String(20))
    overall_grade = Column(String(1), comment='A/B/C/D')
    overall_score = Column(Float, comment='0-100 weighted composite')
    listing_dimension_score = Column(Float, comment='Listing count dimension')
    delisting_speed_score = Column(Float, comment='Delisting speed dimension')
    transaction_speed_score = Column(Float, comment='Transaction speed dimension')
    price_stability_score = Column(Float, comment='Price stability dimension')
    listing_count_30d = Column(Integer, comment='New listings in 30 days')
    avg_delisting_days = Column(Float, comment='Average days to sell')
    avg_transaction_days = Column(Float, comment='Average days to close deal')
    price_volatility_90d = Column(Float, comment='90-day price volatility')
    auto_notes = Column(Text, comment='Auto-generated risk notes')
    graded_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qlg_grade', 'overall_grade'),
        Index('idx_qlg_plate', 'plate_code'),
        Index('idx_qlg_score', 'overall_score'),
    )


class QuantPersonalRiskProfile(Base):
    __tablename__ = 'quant_personal_risk_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(40), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), index=True)
    risk_tolerance_level = Column(String(10), comment='conservative/moderate/aggressive/aggressive_plus')
    dti_score = Column(Float, comment='Debt-to-income based score')
    age_factor = Column(Float)
    investment_horizon_months = Column(Integer)
    dependent_count = Column(Integer, default=0)
    current_leverage = Column(Float, comment='Current leverage ratio')
    max_allowed_leverage = Column(Float)
    composite_risk_score = Column(Float, comment='0-100 personal risk score')
    risk_capacity = Column(String(15), comment='high/medium/limited/very_limited')
    allocation_conservative_pct = Column(Float)
    allocation_balanced_pct = Column(Float)
    allocation_growth_pct = Column(Float)
    allocation_aggressive_pct = Column(Float)
    warning_flags = Column(JSON, comment='Active warnings')
    recommendations = Column(JSON, comment='Personalized recommendations')
    assessed_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('idx_qprp_user', 'user_id_encrypted'),
        Index('idx_qprp_tolerance', 'risk_tolerance_level'),
        Index('idx_qprp_capacity', 'risk_capacity'),
    )


class QuantReport(Base):
    __tablename__ = 'quant_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(40), unique=True, nullable=False)
    report_type = Column(String(20), comment='market_overview/risk_assessment/backtest_summary/custom')
    title = Column(String(200))
    city_code = Column(String(20), index=True)
    district_code = Column(String(20))
    generated_by = Column(String(40), comment='System or user request')
    personality_style = Column(String(10), comment='zhouyu/luxun/neutral')
    market_outlook = Column(String(15), comment='BULLISH/NEUTRAL/BEARISH')
    strategy_recommendation = Column(String(15), comment='BUY/ACCUMULATE/HOLD/REDUCE')
    expected_return_12m = Column(Float)
    var_95_estimate = Column(Float)
    key_findings = Column(JSON, comment='Array of key findings')
    top_factors = Column(JSON, comment='Top influencing factors')
    report_markdown = Column(Text, comment='Full markdown report content')
    word_count = Column(Integer)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, comment='Report validity expiration')
    __table_args__ = (
        Index('idx_qr_type_city', 'report_type', 'city_code'),
        Index('idx_qr_generated', 'generated_at'),
        Index('idx_qr_personality', 'personality_style'),
    )


class QuantMonitorAlert(Base):
    __tablename__ = 'quant_monitor_alerts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(40), unique=True, nullable=False)
    metric_name = Column(String(40), nullable=False, index=True,
                          comment='mape/var_95/policy_risk/liquidity_score/prediction_variance')
    severity = Column(String(10), comment='warning/critical')
    threshold_value = Column(Float)
    actual_value = Column(Float)
    city_code = Column(String(20))
    district_code = Column(String(20))
    status = Column(String(12), default='active', comment='active/acknowledged/resolved/dismissed')
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(64))
    resolved_at = Column(DateTime)
    resolution_note = Column(Text)
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSON, comment='email/webhook/sms')
    __table_args__ = (
        Index('idx_qma_metric_status', 'metric_name', 'status'),
        Index('idx_qma_severity', 'severity'),
        Index('idx_qma_triggered', 'triggered_at'),
    )


class QuantETLRunLog(Base):
    __tablename__ = 'quant_etl_run_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(40), unique=True, nullable=False)
    pipeline_name = Column(String(50), nullable=False, comment='etl_daily/etl_weekly/factor_compute')
    data_source = Column(String(30), comment='beike/fangtianxia/gov_open_data/urban_planning/statistics_bureau/metro/land_auction')
    status = Column(String(12), default='running', comment='running/completed/failed/partial')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    records_extracted = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    error_details = Column(JSON)
    data_freshness_hours = Column(Float, comment='How fresh is the data after this run')
    next_run_scheduled_at = Column(DateTime)
    __table_args__ = (
        Index('idx_qetl_pipeline', 'pipeline_name'),
        Index('idx_qetl_status', 'status'),
        Index('idx_qetl_started', 'started_at'),
        Index('idx_qetl_source', 'data_source'),
    )


class QuantMemoryEntry(Base):
    __tablename__ = 'quant_memory_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_key = Column(String(64), unique=True, nullable=False, comment='SHA256 hash key')
    memory_type = Column(String(20), index=True,
                         comment='prediction/risk/backtest/factor/user_profile/model_metadata')
    category = Column(String(30))
    title = Column(String(150))
    content_json = Column(JSON, nullable=False)
    content_text = Column(Text, comment='Searchable text representation')
    tags = Column(JSON, comment='Array of tag strings')
    source_module = Column(String(50), comment='Which module created this entry')
    ttl_seconds = Column(Integer, comment='Time-to-live in seconds, null=never expire')
    expires_at = Column(DateTime)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_expired = Column(Boolean, default=False)
    __table_args__ = (
        Index('idx_qmem_type_cat', 'memory_type', 'category'),
        Index('idx_qmem_tags', 'tags'),
        Index('idx_qmem_expires', 'expires_at'),
        Index('idx_qmem_created', 'created_at'),
    )


# ==================== Part 22: 量化分析前端集成层 (Quant Analysis Frontend Integration Layer) ====================
# 对应 quant_analysis_frontend_layer.py — 前端交互式报告+API扩展+礼部对话+AB测试+性能优化


class QuantAPIRequestLog(Base):
    __tablename__ = 'quant_api_request_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(20), nullable=False, index=True)
    city = Column(String(50), index=True)
    district = Column(String(50))
    block = Column(String(50))
    horizon = Column(String(5), comment='3m/6m/12m')
    risk_tolerance = Column(String(10), comment='low/medium/high')
    intent_category = Column(String(20), comment='investment/prediction/risk/comparison/timing/general')
    raw_query = Column(Text, comment='Original user query text')
    cache_hit = Column(Boolean, default=False)
    processing_time_ms = Column(Float)
    response_size_bytes = Column(Integer, default=0)
    user_agent = Column(String(255))
    ip_hashed = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qapi_request', 'request_id'),
        Index('idx_qapi_city_horizon', 'city', 'horizon'),
        Index('idx_qapi_cache', 'cache_hit'),
        Index('idx_qapi_created', 'created_at'),
    )


class QuantIntentRecognitionLog(Base):
    __tablename__ = 'quant_intent_recognition_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(20), unique=True, nullable=False)
    user_input = Column(Text, nullable=False)
    detected_intent = Column(String(20), index=True)
    extracted_entities = Column(JSON, comment='Extracted city/district/block/horizon/risk')
    confidence_score = Column(Float, comment='Intent classification confidence 0-1')
    processing_time_ms = Column(Float)
    matched_patterns = Column(JSON, comment='Regex patterns that matched')
    fallback_used = Column(Boolean, default=False, comment='Whether fallback to general intent was used')
    session_id = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_qintent_intent_session', 'detected_intent', 'session_id'),
        Index('idx_qintent_created', 'created_at'),
    )


class QuantParamAdjustmentLog(Base):
    __tablename__ = 'quant_param_adjustment_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    adjustment_id = Column(String(20), unique=True, nullable=False)
    session_id = Column(String(100), index=True)
    original_params = Column(JSON, comment='Parameters before adjustment')
    new_params = Column(JSON, comment='Parameters after adjustment')
    changed_fields = Column(JSON, comment='List of fields that were modified')
    response_time_ms = Column(Float)
    cache_hit = Column(Boolean, default=False)
    user_id_encrypted = Column(String(64))
    source_component = Column(String(30), comment='param_panel/slider/select/button')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qparam_session', 'session_id'),
        Index('idx_qparam_user', 'user_id_encrypted'),
        Index('idx_qparam_created', 'created_at'),
    )


class QuantLibuDialogueMessage(Base):
    __tablename__ = 'quant_libu_dialogue_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(20), unique=True, nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    message_type = Column(String(20), index=True,
                           comment='text/quant_report/factor_explain/loading')
    sender = Column(String(10), comment='libu/system/user')
    persona = Column(String(10), comment='zhouyu/luxun/neutral')
    content_text = Column(Text, comment='Text content for display')
    content_json = Column(JSON, comment='Structured data for quant_report type')
    metadata = Column(JSON, comment='Additional metadata like request_id, factor name')
    is_visible_to_user = Column(Boolean, default=True)
    render_timestamp = Column(DateTime, comment='When message was rendered in UI')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qdialog_session_type', 'session_id', 'message_type'),
        Index('idx_qdialog_persona', 'persona'),
        Index('idx_qdialog_created', 'created_at'),
    )


class QuantReportFeedback(Base):
    __tablename__ = 'quant_report_feedbacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(20), unique=True, nullable=False)
    report_id = Column(String(40), nullable=False, index=True)
    report_request_id = Column(String(20), index=True)
    user_id_encrypted = Column(String(64), index=True)
    feedback_type = Column(String(15), comment='helpful/not_helpful', index=True)
    session_id = Column(String(100))
    additional_notes = Column(Text)
    page_dwell_time_before_feedback_sec = Column(Float, comment='Time on page before clicking feedback')
    ui_variant = Column(String(20), comment='A/B test variant if applicable')
    client_timestamp = Column(DateTime, comment='Client-side timestamp')
    server_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qfeedback_report_user', 'report_id', 'user_id_encrypted'),
        Index('idx_qfeedback_type', 'feedback_type'),
        Index('idx_qfeedback_server_ts', 'server_timestamp'),
    )


class QuantABExperiment(Base):
    __tablename__ = 'quant_ab_experiments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(30), unique=True, nullable=False)
    experiment_name = Column(String(100), nullable=False)
    description = Column(Text)
    variants_config = Column(JSON, comment='Variant definitions with names and configs')
    traffic_split = Column(JSON, comment='Traffic allocation per variant as percentages')
    target_metrics = Column(JSON, comment=['click_rate','dwell_time','conversion','feedback_rate'])
    status = Column(String(12), default='running', comment='draft/running/paused/completed/archived')
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    winning_variant = Column(String(20), comment='Declared winner after analysis')
    statistical_significance = Column(Float, comment='P-value from significance test')
    total_participants = Column(Integer, default=0)
    created_by = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('idx_qab_status', 'status'),
        Index('idx_qab_name', 'experiment_name'),
    )


class QuantABEvent(Base):
    __tablename__ = 'quant_ab_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(24), unique=True, nullable=False)
    experiment_id = Column(String(30), nullable=False, index=True)
    variant_assigned = Column(String(20), index=True, comment='Which variant the user was assigned')
    user_id_encrypted = Column(String(64), index=True)
    event_type = Column(String(30), index=True, comment='impression/click/dwell/feedback/convert')
    event_value = Column(Float, comment='Numeric value for the event (e.g., dwell time in ms)')
    page_url = Column(String(255))
    component_name = Column(String(50), comment='Which component triggered the event')
    metadata = Column(JSON, comment='Additional context data')
    client_timestamp = Column(DateTime)
    server_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qabe_exp_variant', 'experiment_id', 'variant_assigned'),
        Index('idx_qabe_event_type', 'event_type'),
        Index('idx_qabe_server_ts', 'server_timestamp'),
    )


class QuantFrontendPerfMetric(Base):
    __tablename__ = 'quant_frontend_perf_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_id = Column(String(24), unique=True, nullable=False)
    session_id = Column(String(100), index=True)
    metric_name = Column(String(40), nullable=False, index=True,
                          comment='first_paint/report_ready/param_update/chart_init/interaction_response')
    value_ms = Column(Float, nullable=False)
    threshold_ms = Column(Float, comment='Target threshold for this metric')
    passed = Column(Boolean, default=True)
    device_type = Column(String(10), comment='desktop/mobile/tablet')
    browser = Column(String(30))
    connection_type = Column(String(15), comment='4g/wifi/slow-2g')
    city_analyzed = Column(String(50), comment='City being analyzed when metric captured')
    page_load_number = Column(Integer, default=1, comment='SPA navigation count')
    measured_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qperf_metric_name', 'metric_name', 'passed'),
        Index('idx_qperf_device', 'device_type'),
        Index('idx_qperf_measured', 'measured_at'),
    )


class QuantCacheStatsSnapshot(Base):
    __tablename__ = 'quant_cache_stats_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(20), unique=True, nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    cache_size_entries = Column(Integer, default=0)
    total_hits = Column(Integer, default=0)
    total_misses = Column(Integer, default=0)
    hit_rate_pct = Column(Float)
    evictions = Column(Integer, default=0)
    avg_entry_ttl_seconds = Column(Float)
    top_cached_keys = Column(JSON, comment='Most frequently accessed cache keys')
    memory_estimate_bytes = Column(Integer)
    __table_args__ = (
        Index('idx_qcache_snapshot_time', 'snapshot_time'),
    )


# ==================== Part 23: 量化分析进阶功能层 (Quant Analysis Advanced Features Layer) ====================
# 对应 quant_analysis_advanced_layer.py — 对比分析+回测详情模拟+导出分享+个性化配置+深度对话联动


class QuantComparisonRun(Base):
    __tablename__ = 'quant_comparison_runs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(String(20), unique=True, nullable=False)
    item_count = Column(Integer, default=0)
    item_labels = Column(JSON, comment='Array of item labels being compared')
    winner_label = Column(String(100), comment='Overall best scoring item')
    best_per_category = Column(JSON, comment='Best per category mapping')
    recommendation_text = Column(Text)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qcomp_item_count', 'item_count'),
        Index('idx_qcomp_winner', 'winner_label'),
    )


class QuantBacktestDetailRecord(Base):
    __tablename__ = 'quant_backtest_detail_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    detail_id = Column(String(20), unique=True, nullable=False)
    city = Column(String(50), index=True)
    district = Column(String(50))
    strategy_name = Column(String(30))
    start_date = Column(Date)
    end_date = Column(Date)
    initial_capital = Column(Float)
    final_value = Column(Float)
    total_return_pct = Column(Float)
    trade_count = Column(Integer, default=0)
    max_drawdown_pct = Column(Float)
    win_rate_pct = Column(Float)
    sharpe_ratio = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qbtd_city_strategy', 'city', 'strategy_name'),
        Index('idx_qbtd_return', 'total_return_pct'),
    )


class QuantBacktestTrade(Base):
    __tablename__ = 'quant_backtest_trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(16), nullable=False)
    detail_id = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, index=True)
    action = Column(String(10), comment='buy/sell')
    price_per_unit = Column(Float)
    quantity = Column(Float)
    amount = Column(Float)
    fee = Column(Float)
    pnl = Column(Float)
    cumulative_pnl = Column(Float)
    position_after = Column(Float)
    reason_code = Column(String(30))
    metadata = Column(JSON)
    __table_args__ = (
        Index('idx_qbt_detail_date', 'detail_id', 'trade_date'),
        Index('idx_qbt_action', 'action'),
    )


class QuantSimulationRun(Base):
    __tablename__ = 'quant_simulation_runs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(20), unique=True, nullable=False)
    city = Column(String(50), index=True)
    base_strategy_name = Column(String(30))
    custom_params = Column(JSON, comment='rebalance_frequency/stop_loss/take_profit etc')
    baseline_return_pct = Column(Float)
    simulated_return_pct = Column(Float)
    improvement_delta_pct = Column(Float)
    improvement_sharpe_delta = Column(Float)
    param_sensitivity_data = Column(JSON)
    recommended_params = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qsim_city', 'city'),
        Index('idx_qsim_improvement', 'improvement_delta_pct'),
    )


class QuantReportExport(Base):
    __tablename__ = 'quant_report_exports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    export_id = Column(String(24), unique=True, nullable=False)
    report_id = Column(String(40), index=True)
    report_request_id = Column(String(20))
    user_id_encrypted = Column(String(64), index=True)
    export_format = Column(String(10), comment='pdf/png/json', index=True)
    include_charts = Column(Boolean, default=True)
    include_raw_data = Column(Boolean, default=False)
    file_size_bytes = Column(Integer)
    download_url = Column(String(500))
    file_path = Column(String(255), comment='Server-side file path')
    generation_time_ms = Column(Float)
    expires_at = Column(DateTime)
    is_downloaded = Column(Boolean, default=False)
    downloaded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qexport_report_format', 'report_id', 'export_format'),
        Index('idx_qexport_user', 'user_id_encrypted'),
    )


class QuantShareLink(Base):
    __tablename__ = 'quant_share_links'
    id = Column(Integer, primary_key=True, autoincrement=True)
    share_code = Column(String(12), unique=True, nullable=False)
    share_url = Column(String(300), nullable=False)
    report_params = Column(JSON, comment='Original report parameters snapshot')
    access_level = Column(String(15), comment='public/link/private', index=True)
    created_by_user_encrypted = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, index=True)
    view_count = Column(Integer, default=0)
    max_views = Column(Integer, default=200)
    is_active = Column(Boolean, default=True)
    last_viewed_at = Column(DateTime)
    __table_args__ = (
        Index('idx_qshare_active_expires', 'is_active', 'expires_at'),
        Index('idx_qshare_created_by', 'created_by_user_encrypted'),
    )


class QuantUserPreference(Base):
    __tablename__ = 'quant_user_preferences'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_encrypted = Column(String(64), unique=True, nullable=False, index=True)
    default_horizon = Column(String(5), default='12m')
    default_risk_tolerance = Column(String(10), default='medium')
    default_chart_type = Column(String(15), default='line')
    watchlist_json = Column(JSON, comment='Watchlist entries as JSON array')
    favorite_cities_json = Column(JSON, comment='List of favorite city codes')
    notification_preferences = Column(JSON)
    last_updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_qupref_horizon_risk', 'default_horizon', 'default_risk_tolerance'),
    )


class QuantWatchlistEntry(Base):
    __tablename__ = 'quant_watchlist_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(14), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True)
    district = Column(String(50))
    block = Column(String(50))
    display_label = Column(String(100))
    notes = Column(Text)
    alert_threshold_pct = Column(Float, comment='Price change % to trigger alert')
    priority_order = Column(Integer, default=0)
    tags_json = Column(JSON)
    added_at = Column(DateTime, default=datetime.utcnow, index=True)
    removed_at = Column(DateTime, comment='Set when entry is soft-deleted')
    is_active = Column(Boolean, default=True)
    __table_args__ = (
        Index('idx_qwl_user_active', 'user_id_encrypted', 'is_active'),
        Index('idx_qwl_city_district', 'city', 'district'),
    )


class QuantFollowUpMessage(Base):
    __tablename__ = 'quant_follow_up_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(16), unique=True, nullable=False)
    session_id = Column(String(100), index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(25), index=True,
                       comment='prediction_question/factor_inquiry/risk_concern/strategy_alternative/comparison_request/general')
    context_snapshot = Column(JSON, comment='Snapshot of report data at time of question')
    answer_text = Column(Text)
    confidence_score = Column(Float)
    source_modules = Column(JSON, comment='Which modules contributed to answer')
    suggested_followups = Column(JSON, comment='Suggested next questions')
    response_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qfu_session_category', 'session_id', 'category'),
        Index('idx_qfu_confidence', 'confidence_score'),
    )


class QuantInReportChatMessage(Base):
    __tablename__ = 'quant_in_report_chat_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), unique=True, nullable=False)
    report_id = Column(String(40), nullable=False, index=True)
    session_id = Column(String(100), index=True)
    sender = Column(String(10), comment='user/libu/system', index=True)
    content_text = Column(Text)
    content_type = Column(String(15), default='text', comment='text/markdown/code/image')
    position = Column(String(12), default='bottom-right', comment='UI position of chat box')
    is_minimized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('idx_qirc_report_sender', 'report_id', 'sender'),
        Index('idx_qirc_session', 'session_id'),
    )


class QuantPrefetchCache(Base):
    __tablename__ = 'quant_prefetch_cache'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prefetch_key = Column(String(48), unique=True, nullable=False)
    params_hash = Column(String(32), index=True)
    cached_response_json = Column(JSON)
    triggered_by = Column(String(15), comment='hover/click/predictive', default='hover')
    fetched_at = Column(DateTime, default=datetime.utcnow, index=True)
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime)
    ttl_seconds = Column(Integer, default=300)
    is_expired = Column(Boolean, default=False)
    __table_args__ = (
        Index('idx_qpfc_params_hash', 'params_hash'),
        Index('idx_qpfc_fetched', 'fetched_at'),
    )


# ==================== Part 24: 运营与用户增长模块 (Operations & User Growth Module) ====================
# 对应 operations_user_growth_layer.py — 积分经济+双轨成长+会员体系+任务系统+邀请裂变+运营活动+数据看板


class PointsTransactionRecord(Base):
    __tablename__ = 'points_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(18), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    amount = Column(Integer, comment='Positive=earn, negative=consume')
    transaction_type = Column(String(10), index=True, comment='earn/consume/expire/admin_adjust/refund')
    scene = Column(String(50), index=True)
    related_id = Column(String(40), comment='Associated entity ID')
    balance_after = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('pts_tx_user_type', 'user_id_encrypted', 'transaction_type'),
        Index('pts_tx_scene', 'scene'),
        Index('pts_tx_created', 'created_at'),
    )


class PointsRuleConfig(Base):
    __tablename__ = 'points_rule_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(30), unique=True, nullable=False)
    action_name = Column(String(50))
    points_value = Column(Integer, default=0)
    category = Column(String(20), index=True)
    daily_limit = Column(Integer, default=0)
    weekly_limit = Column(Integer, default=0)
    total_limit = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    updated_by = Column(String(64))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('pts_rule_cat_active', 'category', 'is_active'),
    )


class ShopRedemption(Base):
    __tablename__ = 'shop_redemptions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    redemption_id = Column(String(16), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    item_id = Column(String(20), nullable=False, index=True)
    item_name = Column(String(100))
    points_spent = Column(Integer, nullable=False)
    reward_granted = Column(Boolean, default=False)
    reward_type = Column(String(20))
    reward_payload = Column(JSON)
    granted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('shop_red_user_item', 'user_id_encrypted', 'item_id'),
        Index('shop_red_created', 'created_at'),
    )


class UserUsageLevel(Base):
    __tablename__ = 'user_usage_levels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_encrypted = Column(String(64), unique=True, nullable=False, index=True)
    current_level = Column(Integer, default=1)
    current_xp = Column(Integer, default=0)
    total_xp_earned = Column(Integer, default=0)
    last_level_up_at = Column(DateTime)
    level_history_json = Column(JSON, comment='Array of {level, timestamp, source}')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('uul_level', 'current_level'),
    )


class UserContributionLevel(Base):
    __tablename__ = 'user_contribution_levels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_encrypted = Column(String(64), unique=True, nullable=False, index=True)
    current_level = Column(Integer, default=1)
    current_cp = Column(Integer, default=0)
    total_cp_earned = Column(Integer, default=0)
    skill_upload_count = Column(Integer, default=0)
    skill_purchase_count = Column(Integer, default=0)
    article_count = Column(Integer, default=0)
    feedback_count = Column(Integer, default=0)
    answer_count = Column(Integer, default=0)
    revenue_share_pct = Column(Float, default=50.0)
    last_level_up_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('ucl_contrib_level', 'current_level'),
    )


class DualTrackRewardClaim(Base):
    __tablename__ = 'dual_track_reward_claims'
    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_record_id = Column(String(20), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    usage_level_required = Column(Integer)
    contribution_level_required = Column(Integer)
    points_awarded = Column(Integer, default=0)
    badge_id = Column(String(30))
    membership_days_awarded = Column(Integer, default=0)
    is_claimed = Column(Boolean, default=True)
    claimed_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('dtrc_user_claimed', 'user_id_encrypted', 'is_claimed'),
    )


class UserMembershipRecord(Base):
    __tablename__ = 'user_membership_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_encrypted = Column(String(64), unique=True, nullable=False, index=True)
    tier = Column(String(12), index=True, comment='free/monthly/quarterly/yearly')
    status = Column(String(12), default='none', index=True, comment='none/active/expired/cancelled/grace_period')
    start_date = Column(DateTime)
    end_date = Column(DateTime, index=True)
    plan_price_paid_cents = Column(Integer, default=0)
    free_reports_remaining = Column(Integer, default=0)
    auto_renew = Column(Boolean, default=False)
    payment_provider = Column(String(20), comment='alipay/wechat/simulated')
    payment_transaction_id = Column(String(40))
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('umr_tier_status', 'tier', 'status'),
        Index('umr_end_date', 'end_date'),
    )


class MembershipPaymentLog(Base):
    __tablename__ = 'membership_payment_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(24), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    tier = Column(String(12))
    amount_cents = Column(Integer)
    currency = Column(String(3), default='CNY')
    payment_method = Column(String(20))
    provider_transaction_id = Column(String(60))
    status = Column(String(15), default='pending', index=True)
    paid_at = Column(DateTime)
    refunded_at = Column(DateTime)
    refund_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('mpl_user_status', 'user_id_encrypted', 'status'),
    )


class TaskProgressRecord(Base):
    __tablename__ = 'task_progress_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    progress_id = Column(String(14), unique=True, nullable=False)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    task_id = Column(String(25), nullable=False, index=True)
    task_type = Column(String(12), index=True, comment='daily/weekly/oneshot/achievement/newbie_guide')
    current_count = Column(Integer, default=0)
    target_count = Column(Integer, default=1)
    status = Column(String(12), default='not_started', index=True)
    last_updated_at = Column(DateTime)
    completed_at = Column(DateTime)
    claimed_at = Column(DateTime)
    reset_cycle = Column(String(8), comment='Next reset time key')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('tpr_user_task', 'user_id_encrypted', 'task_id'),
        Index('tpr_task_type_status', 'task_type', 'status'),
    )


class UserAchievementRecord(Base):
    __tablename__ = 'user_achievement_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    achievement_id = Column(String(25), nullable=False, index=True)
    category = Column(String(20), index=True)
    earned_at = Column(DateTime, default=datetime.utcnow, index=True)
    displayed = Column(Boolean, default=True)
    share_count = Column(Integer, default=0, comment='Times shared to social media')
    __table_args__ = (
        Index('uar_user_achievement', 'user_id_encrypted', 'achievement_id'),
        Index('uar_category', 'category'),
    )


class NewbieGuideProgress(Base):
    __tablename__ = 'newbie_guide_progress'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_encrypted = Column(String(64), unique=True, nullable=False, index=True)
    step_1_completed = Column(Boolean, default=False)
    step_2_completed = Column(Boolean, default=False)
    step_3_completed = Column(Boolean, default=False)
    step_4_completed = Column(Boolean, default=False)
    step_5_completed = Column(Boolean, default=False)
    all_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    membership_days_awarded = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('ngp_all_completed', 'all_completed'),
    )


class InvitationCodeRecord(Base):
    __tablename__ = 'invitation_code_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(6), unique=True, nullable=False, index=True)
    owner_user_id = Column(String(64), nullable=False, index=True)
    invite_url = Column(String(300), nullable=False)
    qr_data_uri = Column(Text)
    total_invites = Column(Integer, default=0)
    successful_invites = Column(Integer, default=0)
    total_points_earned = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    custom_alias = Column(String(20), comment='User-customized short alias')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('icr_owner', 'owner_user_id'),
    )


class InvitationRelation(Base):
    __tablename__ = 'invitation_relations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    relation_id = Column(String(22), unique=True, nullable=False)
    inviter_user_id = Column(String(64), nullable=False, index=True)
    invitee_user_id = Column(String(64), nullable=False, index=True)
    invitation_code = Column(String(6), index=True)
    status = Column(String(12), default='pending', index=True,
                       comment='pending/registered/activated/rewarded/expired')
    registered_at = Column(DateTime)
    activated_at = Column(DateTime)
    rewarded_at = Column(DateTime)
    invitee_first_action = Column(String(30), comment='First meaningful action by invitee')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('ir_inviter_status', 'inviter_user_id', 'status'),
        Index('ir_invitee_status', 'invitee_user_id', 'status'),
    )


class TeamRecord(Base):
    __tablename__ = 'team_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(14), unique=True, nullable=False)
    leader_user_id = Column(String(64), nullable=False, index=True)
    team_name = Column(String(50))
    member_ids_json = Column(JSON, comment='Array of member user IDs')
    max_members = Column(Integer, default=5)
    total_contributions = Column(Integer, default=0)
    team_goal_target = Column(Integer, default=100)
    team_goal_type = Column(String(20), comment='consultations/reports/etc')
    bonus_points_pool = Column(Integer, default=200)
    status = Column(String(10), default='active', index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    disbanded_at = Column(DateTime)
    __table_args__ = (
        Index('team_leader', 'leader_user_id'),
        Index('team_status', 'status'),
    )


class CampaignDefinition(Base):
    __tablename__ = 'campaign_definitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(14), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    campaign_type = Column(String(20), index=True,
                          comment='double_points/limited_discount/bonus_gift/flash_sale/member_exclusive')
    description = Column(Text)
    banner_image_url = Column(String(255))
    popup_template_html = Column(Text)
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime, index=True)
    target_segments_json = Column(JSON, comment='User segments this campaign targets')
    rules_json = Column(JSON, comment='Campaign-specific rules config')
    bonus_multiplier = Column(Float, default=1.0)
    status = Column(String(10), default='draft', index=True,
                       comment='draft/scheduled/running/paused/ended/archived')
    created_by = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('camp_type_status', 'campaign_type', 'status'),
        Index('camp_time_range', 'start_time', 'end_time'),
    )


class CampaignParticipation(Base):
    __tablename__ = 'campaign_participations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    participation_id = Column(String(16), unique=True, nullable=False)
    campaign_id = Column(String(14), nullable=False, index=True)
    user_id_encrypted = Column(String(64), nullable=False, index=True)
    bonus_points_received = Column(Integer, default=0)
    actions_completed = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow, index=True)
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime)
    __table_args__ = (
        Index('cp_part_campaign_user', 'campaign_id', 'user_id_encrypted'),
    )


class CampaignStatsSnapshot(Base):
    __tablename__ = 'campaign_stats_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(14), unique=True, nullable=False)
    campaign_id = Column(String(14), nullable=False, index=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    exposure_count = Column(Integer, default=0)
    participant_count = Column(Integer, default=0)
    active_participant_count = Column(Integer, default=0)
    total_bonus_given = Column(Integer, default=0)
    total_actions_tracked = Column(Integer, default=0)
    conversion_rate_pct = Column(Float, default=0.0)
    __table_args__ = (
        Index('css_campaign_time', 'campaign_id', 'snapshot_time'),
    )


class AutoOpsRuleRecord(Base):
    __tablename__ = 'auto_ops_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    trigger_condition_json = Column(JSON, nullable=False)
    action_json = Column(JSON, nullable=False)
    cooldown_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime)
    last_execution_result = Column(Text)
    created_by = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    __table_args__ = (
        Index('aor_active', 'is_active'),
    )


class AutoOpsExecutionLog(Base):
    __tablename__ = 'auto_ops_execution_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(22), unique=True, nullable=False)
    rule_id = Column(String(20), nullable=False, index=True)
    rule_name = Column(String(80))
    target_user_id = Column(String(64), index=True)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    action_taken = Column(String(30))
    result_code = Column(String(10), comment='success/fail/skipped')
    result_detail = Column(Text)
    __table_args__ = (
        Index('aoel_rule_time', 'rule_id', 'executed_at'),
        Index('aoel_user', 'target_user_id'),
    )


class OpsDashboardSnapshot(Base):
    __tablename__ = 'ops_dashboard_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(14), unique=True, nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    daily_new_users = Column(Integer, default=0)
    dau = Column(Integer, default=0)
    wau = Column(Integer, default=0)
    mau = Column(Integer, default=0)
    retention_d7 = Column(Float, default=0.0)
    retention_d30 = Column(Float, default=0.0)
    points_issued_today = Column(Integer, default=0)
    points_consumed_today = Column(Integer, default=0)
    active_member_count = Column(Integer, default=0)
    member_conversion_rate = Column(Float, default=0.0)
    arpu = Column(Float, default=0.0)
    task_completion_rate = Column(Float, default=0.0)
    invitation_success_rate = Column(Float, default=0.0)
    top_tasks_json = Column(JSON)
    revenue_breakdown_json = Column(JSON)
    __table_args__ = (
        Index('ods_snapshot_time', 'snapshot_time'),
    )


# ==================== Part 25: 融合仪表盘与智能咨询层 (Quant Fusion Dashboard & Consultation Layer) ====================
# 对应 quant_fusion_dashboard_layer.py — 仪表盘任务融合+意图识别+NLG+对话卡片+因子解释+参数调整+API网关+组件适配+缓存+移动端


class TaskQuantBinding(Base):
    __tablename__ = 'task_quant_bindings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    binding_id = Column(String(22), unique=True, nullable=False)
    task_id = Column(String(40), nullable=False, index=True)
    city_code = Column(String(20), nullable=False, index=True)
    district_code = Column(String(20))
    block_code = Column(String(20), index=True)
    auto_recommended_block = Column(Boolean, default=False)
    quant_available = Column(Boolean, default=False)
    quant_summary_json = Column(JSON, comment='Cached quant summary data')
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('tqb_task_city', 'task_id', 'city_code'),
        Index('tqb_block', 'block_code'),
    )


class QuantReportSectionEmbedding(Base):
    __tablename__ = 'quant_report_section_embeddings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding_id = Column(String(22), unique=True, nullable=False)
    task_id = Column(String(40), nullable=False, index=True)
    section_type = Column(String(20), comment='quant_summary/prediction_curve/factor_radar/risk_card')
    section_title = Column(String(100))
    section_content_json = Column(JSON, nullable=False)
    display_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('qrse_task_section', 'task_id', 'section_type'),
    )


class BatchComparisonRecord(Base):
    __tablename__ = 'batch_comparison_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(String(14), unique=True, nullable=False)
    requested_by_user = Column(String(64), index=True)
    task_ids_json = Column(JSON, comment='Array of task IDs being compared')
    items_json = Column(JSON, comment='Comparison items with ranking/growth/risk')
    best_per_category_json = Column(JSON)
    pdf_exported = Column(Boolean, default=False)
    pdf_file_path = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('bcr_user_created', 'requested_by_user', 'created_at'),
    )


class ChatQuantCardRecord(Base):
    __tablename__ = 'chat_quant_card_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String(16), unique=True, nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    city_code = Column(String(20))
    district_code = Column(String(20))
    block_code = Column(String(20))
    quant_summary_json = Column(JSON)
    card_mode = Column(String(12), default='chat_card', comment='embedded/fullscreen/chat_card/dashboard_tab')
    is_expanded = Column(Boolean, default=False)
    expand_count = Column(Integer, default=0)
    block_switch_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('cqcr_session_cards', 'session_id', 'created_at'),
    )


class FusionIntentRecognitionLog(Base):
    __tablename__ = 'fusion_intent_recognition_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(20), unique=True, nullable=False)
    session_id = Column(String(100), index=True)
    user_input_raw = Column(Text, nullable=False)
    detected_intent = Column(String(25), index=True,
                              comment='general_consult/quant_investment/price_prediction/risk_assessment/block_comparison/factor_inquiry/param_adjustment')
    confidence_score = Column(Float)
    matched_keywords_json = Column(JSON)
    extracted_entities_json = Column(JSON, comment='city/block/horizon/risk_tolerance')
    triggered_quant_api = Column(Boolean, default=False)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('firl_intent_session', 'detected_intent', 'session_id'),
        Index('firl_confidence', 'confidence_score'),
    )


class LiBuFusionNLGLog(Base):
    __tablename__ = 'libu_fusion_nlg_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nlg_id = Column(String(20), unique=True, nullable=False)
    session_id = Column(String(100), index=True)
    persona_used = Column(String(10), comment='zhouyu/luxun')
    intent_type = Column(String(20), comment='investment/risk/factor_explain/param_adjustment')
    input_quant_data_hash = Column(String(32))
    input_summary = Column(JSON, comment='Key quant fields used as input')
    generated_response_text = Column(Text, nullable=False)
    response_length_chars = Column(Integer)
    tone_score = Column(Float, comment='How well response matches persona 0-1')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('lfl_persona_intent', 'persona_used', 'intent_type'),
    )


class FactorExplainCacheEntry(Base):
    __tablename__ = 'factor_explain_cache_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(24), unique=True, nullable=False, index=True)
    prediction_id = Column(String(16))
    city_code = Column(String(20))
    block_code = Column(String(20))
    horizon_months = Column(Integer)
    factors_json = Column(JSON, comment='Factor contribution list')
    total_contribution_explained = Column(Float)
    primary_driver = Column(String(50))
    secondary_drivers_json = Column(JSON)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)
    __table_args__ = (
        Index('fec_city_block_horizon', 'city_code', 'block_code', 'horizon_months'),
    )


class DialogueParamAdjustmentLog(Base):
    __tablename__ = 'dialogue_param_adjustment_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(18), unique=True, nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    adjustment_number = Column(Integer, default=1)
    original_horizon = Column(Integer)
    original_risk_tolerance = Column(String(10))
    new_horizon = Column(Integer)
    new_risk_tolerance = Column(String(10))
    parsed_from_input = Column(Text, comment='Original user text that triggered adjustment')
    previous_result_hash = Column(String(32))
    new_result_summary_json = Column(JSON)
    delta_comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('dpal_session_seq', 'session_id', 'adjustment_number'),
    )


class FusionAPIRequestLog(Base):
    __tablename__ = 'fusion_api_request_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(18), unique=True, nullable=False)
    endpoint_path = Column(String(50), nullable=False, index=True)
    method = Column(String(6), comment='GET/POST/PUT/DELETE')
    requester_user_id = Column(String(64), index=True)
    request_payload_hash = Column(String(32))
    validation_passed = Column(Boolean)
    validation_errors_json = Column(JSON)
    response_status_code = Column(Integer)
    response_size_bytes = Column(Integer)
    processing_time_ms = Column(Float)
    cache_hit = Column(Boolean, default=False)
    source_context = Column(String(15), comment='dashboard/chat/batch/mobile/api')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('farl_endpoint_method', 'endpoint_path', 'method'),
        Index('farl_user_time', 'requester_user_id', 'created_at'),
    )


class QuantComponentInstanceLog(Base):
    __tablename__ = 'quant_component_instance_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(String(20), unique=True, nullable=False)
    component_name = Column(String(30), nullable=False, index=True)
    mode = Column(String(12), comment='embedded/fullscreen/chat_card/dashboard_tab')
    config_override_json = Column(JSON)
    rendered_page = Column(String(50), comment='Which page this instance appears on')
    render_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_rendered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('qcil_component_mode', 'component_name', 'mode'),
    )


class FusionPrefetchTargetLog(Base):
    __tablename__ = 'fusion_prefetch_target_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(String(18), unique=True, nullable=False)
    target_type = Column(String(10), default='hover', comment='hover/preload/predictive')
    city_code = Column(String(20))
    block_code = Column(String(20))
    horizon_months = Column(Integer, default=12)
    risk_tolerance = Column(String(10), default='medium')
    status = Column(String(12), default='pending', index=True, comment='pending/triggered/loaded/error/expired')
    triggered_at = Column(DateTime)
    loaded_at = Column(DateTime)
    cache_key_generated = Column(String(24))
    converted_successfully = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('fptl_status_type', 'status', 'target_type'),
    )


class FusionCacheStatsSnapshot(Base):
    __tablename__ = 'fusion_cache_stats_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(12), unique=True, nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow, index=True)
    total_entries = Column(Integer, default=0)
    hits = Column(Integer, default=0)
    misses = Column(Integer, default=0)
    evictions = Column(Integer, default=0)
    hit_rate_pct = Column(Float)
    memory_kb = Column(Float)
    active_prefetch_targets = Column(Integer, default=0)
    loaded_prefetch_targets = Column(Integer, default=0)
    expired_prefetches_cleaned = Column(Integer, default=0)
    __table_args__ = (
        Index('fcss_snapshot_time', 'snapshot_time'),
    )


# ==================== Part 26: 多模态集成层 (Multimodal Integration Layer - LongCat-Next) ====================
# 对应 multimodal_integration_layer.py — 图片理解+图片生成+语音交互(TTS/ASR)+工具调用+会话管理+安全过滤


class ImageAnalysisRecord(Base):
    __tablename__ = 'image_analysis_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(16), unique=True, nullable=False)
    task_type = Column(String(30), index=True)
    image_hash = Column(String(20), index=True)
    image_size_bytes = Column(Integer)
    user_id = Column(String(64), index=True)
    analysis_text = Column(Text)
    confidence_score = Column(Float)
    structured_data_json = Column(JSON)
    key_findings_json = Column(JSON)
    suggestions_json = Column(JSON)
    model_version = Column(String(30))
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('iar_task_user', 'task_type', 'user_id'),
    )


class ImageGenerationRecord(Base):
    __tablename__ = 'image_generation_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    generation_id = Column(String(16), unique=True, nullable=False)
    task_type = Column(String(30), index=True)
    prompt_text = Column(Text)
    negative_prompt = Column(Text)
    style_used = Column(String(30))
    color_scheme = Column(String(30))
    width = Column(Integer)
    height = Column(Integer)
    seed = Column(Integer)
    guidance_scale = Column(Float)
    inference_steps = Column(Integer)
    output_image_path = Column(String(300))
    output_image_b64_preview = Column(Text)
    safety_check_passed = Column(Boolean, default=True)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class VoiceSynthesisRecord(Base):
    __tablename__ = 'voice_synthesis_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(16), unique=True, nullable=False)
    text_content = Column(Text, nullable=False)
    text_hash = Column(String(16))
    persona_used = Column(String(20), index=True)
    language = Column(String(8), default='zh-CN')
    speed = Column(Float, default=1.0)
    pitch = Column(Float, default=1.0)
    emotion = Column(String(15), default='neutral')
    output_format = Column(String(8), default='mp3')
    audio_file_path = Column(String(300))
    duration_seconds = Column(Float)
    file_size_bytes = Column(Integer)
    processing_time_ms = Column(Float)
    session_id = Column(String(20), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('vsr_persona_session', 'persona_used', 'session_id'),
    )


class ASRRecognitionRecord(Base):
    __tablename__ = 'asr_recognition_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    recognition_id = Column(String(16), unique=True, nullable=False)
    audio_hash = Column(String(20))
    audio_duration_sec = Column(Float)
    transcript = Column(Text, nullable=False)
    confidence = Column(Float)
    language_detected = Column(String(8))
    segments_json = Column(JSON)
    speaker_diarization_json = Column(JSON)
    punctuation_restored = Column(Boolean, default=True)
    model_version = Column(String(30))
    session_id = Column(String(20), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class MultimodalToolCallRecord(Base):
    __tablename__ = 'multimodal_tool_call_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(14), unique=True, nullable=False)
    category = Column(String(20), index=True)
    tool_name = Column(String(40))
    arguments_json = Column(JSON)
    input_modalities_json = Column(JSON)
    output_modality = Column(String(10))
    execution_status = Column(String(15), default='pending')
    result_json = Column(JSON)
    error_message = Column(Text)
    latency_ms = Column(Float)
    session_id = Column(String(20), index=True)
    pipeline_step_num = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('mtcr_category_status', 'category', 'execution_status'),
    )


class MultimodalSessionRecord(Base):
    __tablename__ = 'multimodal_session_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False, index=True)
    modalities_used_json = Column(JSON)
    turn_count = Column(Integer, default=0)
    current_persona = Column(String(20), default='zhouyu_bold')
    context_summary = Column(Text)
    image_turns_count = Column(Integer, default=0)
    audio_turns_count = Column(Integer, default=0)
    tool_call_count = Column(Integer, default=0)
    is_multimodal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, index=True)
    expired_at = Column(DateTime)
    __table_args__ = (
        Index('msr_user_active', 'user_id', 'last_active_at'),
    )


class MultimodalSafetyLog(Base):
    __tablename__ = 'multimodal_safety_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(18), unique=True, nullable=False)
    modality_type = Column(String(10), comment='image/audio/text')
    content_hash = Column(String(24))
    is_safe = Column(Boolean, index=True)
    blocked_categories_json = Column(JSON)
    check_duration_ms = Column(Float)
    session_id = Column(String(20))
    action_taken = Column(String(15), comment='blocked/passed/warned')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (
        Index('msl_modality_safe', 'modality_type', 'is_safe'),
    )


class MultimodalAnalyticsDaily(Base):
    __tablename__ = 'multimodal_analytics_daily'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, unique=True, nullable=False, index=True)
    feature_image_understanding_count = Column(Integer, default=0)
    feature_image_generation_count = Column(Integer, default=0)
    feature_tts_count = Column(Integer, default=0)
    feature_asr_count = Column(Integer, default=0)
    feature_tool_call_count = Column(Integer, default=0)
    feature_full_dialogue_count = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    unique_users_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float)
    error_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('mad_date', 'stat_date'),
    )


class MultimodalFeatureUsage(Base):
    __tablename__ = 'multimodal_feature_usage'
    id = Column(Integer, primary_key=True, autoincrement=True)
    feature_name = Column(String(50), unique=True, nullable=False)
    total_usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    avg_latency_ms = Column(Float)
    success_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('mfu_feature', 'feature_name'),
    )


class PersonaVoiceConfigRecord(Base):
    __tablename__ = 'persona_voice_config_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    persona_id = Column(String(20), unique=True, nullable=False)
    display_name = Column(String(40))
    voice_model_id = Column(String(30))
    description = Column(Text)
    pitch_min = Column(Float)
    pitch_max = Column(Float)
    speed_min = Column(Float)
    speed_max = Column(Float)
    energy_level = Column(String(10))
    timbre_type = Column(String(20))
    emotion_capabilities_json = Column(JSON)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ImageStylePreset(Base):
    __tablename__ = 'image_style_presets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    style_id = Column(String(24), unique=True, nullable=False)
    display_name = Column(String(40))
    category = Column(String(20), comment='interior/architectural/artistic')
    prompt_template = Column(Text)
    negative_prompt_template = Column(Text)
    recommended_color_schemes_json = Column(JSON)
    default_guidance_scale = Column(Float, default=5.0)
    default_steps = Column(Integer, default=28)
    default_size = Column(String(15), default='1024x768')
    thumbnail_b64 = Column(Text)
    popularity_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# 第三十四部分：专业机构用户复合对话处理模块 (professional_composite_dialogue_layer.py)
# =============================================================================

class ProfessionalUserProfile(Base):
    """专业机构用户画像表"""
    __tablename__ = 'professional_user_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, comment='用户ID')
    role = Column(String(20), nullable=False, comment='角色: ANALYST/FUND_MANAGER/DEVELOPER_MARKETING/RESEARCH_INSTITUTE/GOVERNMENT_REGULATOR')
    focus_districts_json = Column(JSON, comment='关注区域JSON')
    expertise_tags_json = Column(JSON, comment='专业标签JSON')
    certification_level = Column(String(20), comment='认证等级')
    organization_name = Column(String(100), comment='机构名称')
    years_experience = Column(Integer, comment='从业年限')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_prof_user_user_id', 'user_id'),
        Index('idx_prof_user_role', 'role'),
    )


class TerminologyLookupLog(Base):
    """术语查询日志表"""
    __tablename__ = 'terminology_lookup_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), comment='用户ID')
    session_id = Column(String(36), comment='会话ID')
    query_term = Column(String(100), nullable=False, comment='查询术语')
    matched_term_key = Column(String(50), comment='匹配的术语键')
    category = Column(String(20), comment='分类')
    is_synonym_match = Column(Boolean, default=False, comment='是否同义词匹配')
    confidence_score = Column(Float, comment='置信度分数')
    api_mapping_used = Column(String(100), comment='使用的API映射')
    response_time_ms = Column(Integer, comment='响应时间(毫秒)')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_term_log_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_term_log_matched_key', 'matched_term_key'),
    )


class ParsedIntentRecord(Base):
    """解析意图记录表"""
    __tablename__ = 'parsed_intent_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    original_query = Column(Text, nullable=False, comment='原始查询')
    primary_intent_type = Column(String(30), nullable=False, comment='主要意图类型')
    sub_intents_json = Column(JSON, comment='子意图JSON')
    extracted_entities_json = Column(JSON, comment='提取实体JSON')
    time_range_start = Column(DateTime, comment='时间范围开始')
    time_range_end = Column(DateTime, comment='时间范围结束')
    time_granularity = Column(String(10), comment='时间粒度')
    complexity_score = Column(Float, comment='复杂度分数')
    requires_parallel = Column(Boolean, default=False, comment='是否需要并行处理')
    parser_version = Column(String(10), comment='解析器版本')
    parse_duration_ms = Column(Integer, comment='解析耗时(毫秒)')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_intent_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_intent_primary_type', 'primary_intent_type'),
    )


class TimeRangeParseLog(Base):
    """时间范围解析日志表"""
    __tablename__ = 'time_range_parse_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    raw_expression = Column(String(200), nullable=False, comment='原始表达式')
    parsed_start = Column(DateTime, comment='解析开始时间')
    parsed_end = Column(DateTime, comment='解析结束时间')
    granularity = Column(String(10), comment='粒度: MONTHLY/QUARTERLY/YEARLY')
    is_relative = Column(Boolean, default=False, comment='是否相对时间')
    fallback_used = Column(Boolean, default=False, comment='是否使用回退策略')
    context_hint = Column(String(100), comment='上下文提示')
    parse_success = Column(Boolean, default=False, comment='是否解析成功')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_timerange_session', 'session_id'),
    )


class EntityExtractionRecord(Base):
    """实体提取记录表"""
    __tablename__ = 'entity_extraction_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    intent_record_id = Column(Integer, ForeignKey('parsed_intent_records.id'), nullable=False, comment='意图记录ID')
    entity_type = Column(String(20), nullable=False, comment='实体类型: DISTRICT/METRIC/POLICY_TYPE/SCENARIO_VARIABLE/NUMERIC_VALUE')
    entity_value = Column(String(200), nullable=False, comment='实体值')
    confidence = Column(Float, comment='置信度')
    source_text_span = Column(String(100), comment='源文本跨度')
    extractor_method = Column(String(30), comment='提取方法')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_entity_intent_type', 'intent_record_id', 'entity_type'),
    )


class MetricCalculationResult(Base):
    """指标计算结果表"""
    __tablename__ = 'metric_calculation_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    metric_name = Column(String(50), nullable=False, comment='指标名称')
    metric_category = Column(String(20), comment='指标类别: VALUATION/RETURN/RISK/TREND/MARKET/POLICY')
    value = Column(Float, comment='值')
    unit = Column(String(20), comment='单位')
    confidence_interval_low = Column(Float, comment='置信区间下限')
    confidence_interval_high = Column(Float, comment='置信区间上限')
    calculation_params_json = Column(JSON, comment='计算参数JSON')
    calculation_duration_ms = Column(Integer, comment='计算耗时(毫秒)')
    error_message = Column(Text, comment='错误信息')
    benchmark_value = Column(Float, comment='基准值')
    benchmark_comparison = Column(String(20), comment='基准比较: ABOVE/BELOW/SIMILAR')
    explanation_text = Column(Text, comment='解释文本')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_metric_session_name', 'session_id', 'metric_name'),
        Index('idx_metric_category', 'metric_category'),
    )


class ParallelDispatchLog(Base):
    """并行调度日志表"""
    __tablename__ = 'parallel_dispatch_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    dispatch_id = Column(String(36), nullable=False, comment='调度ID')
    total_metrics_requested = Column(Integer, comment='请求的总指标数')
    successful_count = Column(Integer, comment='成功数')
    failed_count = Column(Integer, comment='失败数')
    failed_metric_names_json = Column(JSON, comment='失败指标名JSON')
    total_time_ms = Column(Integer, comment='总耗时(毫秒)')
    timeout_occurred = Column(Boolean, default=False, comment='是否发生超时')
    timeout_metrics_json = Column(JSON, comment='超时指标JSON')
    merge_strategy = Column(String(20), comment='合并策略')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_dispatch_session', 'session_id'),
    )


class DialogueContextSnapshot(Base):
    """对话上下文快照表"""
    __tablename__ = 'dialogue_context_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    current_district = Column(String(50), comment='当前区域')
    current_time_range_start = Column(DateTime, comment='当前时间范围开始')
    current_time_range_end = Column(DateTime, comment='当前时间范围结束')
    recent_metrics_json = Column(JSON, comment='最近指标JSON')
    intent_history_json = Column(JSON, comment='意图历史JSON(最多10条)')
    parameter_overrides_json = Column(JSON, comment='参数覆盖JSON')
    context_version = Column(Integer, comment='上下文版本号')
    expires_at = Column(DateTime, comment='过期时间')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_context_session_version', 'session_id', 'context_version'),
        Index('idx_context_user_updated', 'user_id', 'updated_at'),
    )


class ParameterInheritanceEvent(Base):
    """参数继承事件表"""
    __tablename__ = 'parameter_inheritance_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    turn_number = Column(Integer, comment='轮次号')
    inherited_params_json = Column(JSON, comment='继承参数JSON')
    explicit_overrides_json = Column(JSON, comment='显式覆盖JSON')
    auto_filled_fields = Column(JSON, comment='自动填充字段')
    source_context_version = Column(Integer, comment='源上下文版本')
    inheritance_type = Column(String(20), comment='继承类型: AUTO_FILL/OVERRIDE/MERGE')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_inherit_session_turn', 'session_id', 'turn_number'),
    )


class ExplanationGenerationRecord(Base):
    """解释生成记录表"""
    __tablename__ = 'explanation_generation_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_result_id = Column(Integer, ForeignKey('metric_calculation_results.id'), nullable=False, comment='指标结果ID')
    template_key = Column(String(50), comment='模板键')
    rendered_text = Column(Text, comment='渲染文本')
    variables_used_json = Column(JSON, comment='使用的变量JSON')
    has_benchmark_comparison = Column(Boolean, default=False, comment='是否有基准对比')
    benchmark_text = Column(String(200), comment='基准文本')
    language_style = Column(String(20), comment='语言风格: PROFESSIONAL/FRIENDLY/ACADEMIC')
    generation_duration_ms = Column(Integer, comment='生成耗时(毫秒)')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_explanation_metric_result', 'metric_result_id'),
    )


class UncertaintyExpressionRecord(Base):
    """不确定性表达记录表"""
    __tablename__ = 'uncertainty_expression_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    raw_confidence_score = Column(Float, comment='原始置信度分数')
    expression_level = Column(String(20), comment='表达级别: VERY_HIGH/HIGH/MODERATE/LOW/VERY_LOW')
    natural_language_expr = Column(Text, comment='自然语言表达')
    prediction_value = Column(Float, comment='预测值')
    interval_low = Column(Float, comment='区间下限')
    interval_high = Column(Float, comment='区间上限')
    interval_unit = Column(String(20), comment='区间单位')
    formatted_output = Column(Text, comment='格式化输出')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_uncertainty_session_level', 'session_id', 'expression_level'),
    )


class ProfessionalReportRecord(Base):
    """专业报告记录表"""
    __tablename__ = 'professional_report_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    session_id = Column(String(36), comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    report_title = Column(String(200), comment='报告标题')
    format_type = Column(String(10), comment='格式类型: MARKDOWN/PDF/HTML')
    sections_json = Column(JSON, comment='章节JSON(有序列表)')
    key_metrics_summary_json = Column(JSON, comment='关键指标摘要JSON')
    total_sections = Column(Integer, comment='总章节数')
    file_size_bytes = Column(Integer, comment='文件大小(字节)')
    storage_path = Column(String(300), comment='存储路径')
    download_count = Column(Integer, default=0, comment='下载次数')
    share_token = Column(String(36), comment='分享令牌')
    is_archived = Column(Boolean, default=False, comment='是否已归档')
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, comment='过期时间')

    __table_args__ = (
        Index('idx_report_session_generated', 'session_id', 'generated_at'),
        Index('idx_report_user', 'user_id'),
        Index('idx_report_share_token', 'share_token'),
    )


class PolicyImpactAnalysisResult(Base):
    """政策影响分析结果表"""
    __tablename__ = 'policy_impact_analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    city = Column(String(50), nullable=False, comment='城市')
    policy_type = Column(String(20), nullable=False, comment='政策类型: PURCHASE_RESTRICTION/LOAN_LIMIT/TALENT_POLICY/TAX_POLICY/INTEREST_RATE/LTV')
    policy_date = Column(Date, comment='政策日期')
    lookforward_month_3_return = Column(Float, comment='未来3个月收益')
    lookforward_month_6_return = Column(Float, comment='未来6个月收益')
    lookforward_month_12_return = Column(Float, comment='未来12个月收益')
    impact_magnitude_3m = Column(Float, comment='3个月影响幅度')
    impact_magnitude_6m = Column(Float, comment='6个月影响幅度')
    impact_magnitude_12m = Column(Float, comment='12个月影响幅度')
    confidence_low_3m = Column(Float, comment='3个月置信下限')
    confidence_high_3m = Column(Float, comment='3个月置信上限')
    significance_level = Column(String(10), comment='显著性水平: HIGHLY_SIGNIFICANT/SIGNIFICANT/MARGINAL/NOT_SIGNIFICANT')
    baseline_window_months = Column(Integer, comment='基线窗口月数')
    event_window_months = Column(Integer, comment='事件窗口月数')
    control_group_district = Column(String(50), comment='对照组区域')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_policy_city_type', 'city', 'policy_type'),
        Index('idx_policy_session', 'session_id'),
    )


class LiquidityAnalysisResult(Base):
    """流动性分析结果表"""
    __tablename__ = 'liquidity_analysis_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    district = Column(String(50), nullable=False, comment='区域')
    analysis_date = Column(Date, nullable=False, comment='分析日期')
    inventory_cycle_months = Column(Float, comment='库存周期(月)')
    listing_volume_change_pct = Column(Float, comment='挂牌量变化百分比')
    transaction_cycle_median_days = Column(Float, comment='交易周期中位数(天)')
    bargaining_space_pct = Column(Float, comment='议价空间百分比')
    overall_risk_level = Column(String(10), comment='整体风险水平: LOW/MEDIUM/HIGH/CRITICAL')
    risk_score = Column(Float, comment='风险评分(0-100)')
    data_source = Column(String(50), comment='数据来源')
    sample_size = Column(Integer, comment='样本量')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_liquidity_district_date', 'district', 'analysis_date'),
    )


class ScenarioStressTestResult(Base):
    """场景压力测试结果表"""
    __tablename__ = 'scenario_stress_test_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    base_district = Column(String(50), nullable=False, comment='基础区域')
    scenario_name = Column(String(100), nullable=False, comment='场景名称')
    shock_variables_json = Column(JSON, comment='冲击变量JSON')
    n_simulations = Column(Integer, comment='模拟次数')
    time_horizon_months = Column(Integer, comment='时间跨度(月)')
    mean_price_change_pct = Column(Float, comment='平均价格变化百分比')
    std_price_change_pct = Column(Float, comment='价格变化标准差')
    percentile_5th = Column(Float, comment='第5百分位')
    percentile_25th = Column(Float, comment='第25百分位')
    percentile_50th = Column(Float, comment='第50百分位')
    percentile_75th = Column(Float, comment='第75百分位')
    percentile_95th = Column(Float, comment='第95百分位')
    probability_positive = Column(Float, comment='正收益概率')
    worst_case_loss_pct = Column(Float, comment='最坏情况损失百分比')
    best_case_gain_pct = Column(Float, comment='最好情况收益百分比')
    stress_test_summary_text = Column(Text, comment='压力测试摘要文本')
    simulation_duration_ms = Column(Integer, comment='模拟耗时(毫秒)')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_stress_session_scenario', 'session_id', 'scenario_name'),
    )


class ProfessionalQueryAnalytics(Base):
    """专业查询分析表"""
    __tablename__ = 'professional_query_analytics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(36), unique=True, nullable=False, comment='查询ID')
    session_id = Column(String(36), comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    user_role = Column(String(20), comment='用户角色')
    parsed_intent_summary = Column(String(100), comment='解析意图摘要')
    metrics_requested_json = Column(JSON, comment='请求指标JSON')
    response_time_ms = Column(Integer, comment='响应时间(毫秒)')
    satisfaction_flag = Column(Boolean, comment='满意度标记')
    error_occurred = Column(Boolean, default=False, comment='是否出错')
    error_message = Column(Text, comment='错误信息')
    client_info_json = Column(JSON, comment='客户端信息JSON')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_query_analytics_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_query_analytics_role', 'user_role'),
        Index('idx_query_analytics_error_timestamp', 'error_occurred', 'timestamp'),
    )


# =============================================================================
# 第三十五部分：智能体升级与进化效果展示系统 (agent_upgrade_evolution_effect_layer.py)
# =============================================================================

class AgentPerformanceHistory(Base):
    """智能体性能历史快照表"""
    __tablename__ = 'agent_performance_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    snapshot_date = Column(Date, nullable=False, comment='快照日期')
    task_count = Column(Integer, default=0, comment='任务总数')
    avg_response_time_ms = Column(Float, comment='平均响应时间(毫秒)')
    avg_quality_score = Column(Float, comment='平均质量评分')
    total_api_calls = Column(Integer, default=0, comment='API调用总次数')
    total_points_consumed = Column(Float, default=0.0, comment='总消耗积分')
    error_rate = Column(Float, default=0.0, comment='错误率')
    success_rate = Column(Float, default=1.0, comment='成功率')
    cost_per_task_avg = Column(Float, comment='平均每任务成本')
    data_json = Column(JSON, comment='扩展数据JSON')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_perf_hist_agent_date', 'agent_id', 'snapshot_date'),
        Index('idx_perf_hist_snapshot_date', 'snapshot_date'),
    )


class UpgradeEffectRecord(Base):
    """升级效果记录表"""
    __tablename__ = 'upgrade_effect_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    effect_snapshot_id = Column(String(36), unique=True, nullable=False, comment='效果快照唯一标识')
    agent_id = Column(String(36), ForeignKey('agents.id'), nullable=False, comment='智能体ID')
    agent_name = Column(String(100), comment='智能体名称')
    agent_type = Column(String(20), comment='智能体类型')
    level_before = Column(Integer, nullable=False, comment='升级前等级')
    level_after = Column(Integer, nullable=False, comment='升级后等级')
    upgrade_timestamp = Column(DateTime, nullable=False, comment='升级时间戳')
    overall_improvement_score = Column(Float, default=0.0, comment='综合提升分数(0-100)')
    efficiency_gain_pct = Column(Float, default=0.0, comment='效率增益百分比')
    quality_gain_pct = Column(Float, default=0.0, comment='质量增益百分比')
    capability_gain_pct = Column(Float, default=0.0, comment='能力增益百分比')
    cost_gain_pct = Column(Float, default=0.0, comment='成本优化百分比')
    collaboration_gain_pct = Column(Float, default=0.0, comment='协作增益百分比')
    top_improvements_json = Column(JSON, comment='主要改进项JSON')
    seasonality_adjusted = Column(Boolean, default=False, comment='是否经过季节性调整')
    confidence_level = Column(String(20), default='MODERATE', comment='置信度: INSUFFICIENT/LOW/MODERATE/HIGH')
    sample_pre_count = Column(Integer, default=0, comment='升级前样本数')
    sample_post_count = Column(Integer, default=0, comment='升级后样本数')
    ci_low = Column(Float, comment='置信区间下界')
    ci_high = Column(Float, comment='置信区间上界')
    calculation_method = Column(String(50), comment='计算方法')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_upgrade_effect_agent', 'agent_id'),
        Index('idx_upgrade_effect_timestamp', 'upgrade_timestamp'),
    )


class EffectDimensionDetail(Base):
    """效果维度明细表"""
    __tablename__ = 'effect_dimension_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    effect_record_id = Column(Integer, ForeignKey('upgrade_effect_records.id'), nullable=False, comment='效果记录ID')
    dimension = Column(String(20), nullable=False, comment='维度: EFFICIENCY/QUALITY/CAPABILITY/COST/COLLABORATION')
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    value_before = Column(Float, comment='升级前值')
    value_after = Column(Float, comment='升级后值')
    change_pct = Column(Float, comment='变化百分比')
    change_abs = Column(Float, comment='变化绝对值')
    is_statistically_significant = Column(Boolean, default=False, comment='是否统计显著')
    ci_low = Column(Float, comment='置信区间下界')
    ci_high = Column(Float, comment='置信区间上界')
    notes = Column(Text, comment='备注说明')

    __table_args__ = (
        Index('idx_eff_dim_record_dimension', 'effect_record_id', 'dimension'),
    )


class UpgradeEventJob(Base):
    """升级事件作业表"""
    __tablename__ = 'upgrade_event_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, nullable=False, comment='作业唯一标识')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    old_level = Column(Integer, nullable=False, comment='旧等级')
    new_level = Column(Integer, nullable=False, comment='新等级')
    job_type = Column(String(30), default='UPGRADE_EFFECT_CALCULATION', comment='作业类型')
    status = Column(String(20), default='PENDING', comment='状态: PENDING/RUNNING/COMPLETED/FAILED')
    progress_pct = Column(Float, default=0.0, comment='进度百分比(0-100)')
    result_snapshot_id = Column(String(36), comment='结果快照ID')
    error_message = Column(Text, comment='错误信息')
    pre_period_days = Column(Integer, default=7, comment='升级前统计天数')
    post_period_days = Column(Integer, default=7, comment='升级后统计天数')
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_upgrade_job_agent_status', 'agent_id', 'status'),
        Index('idx_upgrade_job_status', 'status'),
    )


class AttributionAnalysisRecord(Base):
    """归因分析记录表"""
    __tablename__ = 'attribution_analysis_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), unique=True, nullable=False, comment='记录唯一标识')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    upgrade_event_id = Column(String(36), nullable=False, comment='升级事件ID')
    factor_type = Column(String(20), nullable=False, comment='因子类型: ALGORITHM_OPTIMIZATION/SKILL_LEARNING/BOND_ACTIVATION/LEVEL_UP_BASE/DATA_SOURCE_EXPANSION/TOOL_PERMISSION_UNLOCK')
    contribution_pct = Column(Float, default=0.0, comment='贡献百分比(0-100)')
    evidence_json = Column(JSON, comment='证据JSON')
    calculated_at = Column(DateTime, default=datetime.utcnow, comment='计算时间')
    is_primary_factor = Column(Boolean, default=False, comment='是否为主要因子')

    __table_args__ = (
        Index('idx_attr_agent_upgrade', 'agent_id', 'upgrade_event_id'),
    )


class UpgradeRecommendationLog(Base):
    """升级建议日志表"""
    __tablename__ = 'upgrade_recommendation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rec_id = Column(String(36), unique=True, nullable=False, comment='建议唯一标识')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    target_action = Column(String(200), nullable=False, comment='目标行动')
    expected_gain_description = Column(String(200), comment='预期收益描述')
    priority = Column(String(10), default='MEDIUM', comment='优先级: CRITICAL/HIGH/MEDIUM/LOW')
    rationale = Column(Text, comment='理由说明')
    estimated_cost_points = Column(Integer, default=0, comment='预估消耗积分')
    confidence_score = Column(Float, default=0.5, comment='置信度评分(0-1)')
    valid_until = Column(DateTime, comment='有效期至')
    is_accepted = Column(Boolean, comment='是否已接受')
    accepted_at = Column(DateTime, comment='接受时间')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_rec_log_agent_priority', 'agent_id', 'priority'),
        Index('idx_rec_log_accepted', 'is_accepted'),
    )


class ABTestSession(Base):
    """A/B测试会话表"""
    __tablename__ = 'ab_test_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(36), unique=True, nullable=False, comment='测试唯一标识')
    test_name = Column(String(200), nullable=False, comment='测试名称')
    hypothesis = Column(Text, comment='假设说明')
    description = Column(Text, comment='测试描述')
    group_split_ratio = Column(Float, default=0.5, comment='分组比例')
    min_sample_size = Column(Integer, default=30, comment='最小样本量')
    metrics_tracked_json = Column(JSON, comment='跟踪指标JSON')
    status = Column(String(10), default='DRAFT', comment='状态: DRAFT/RUNNING/COMPLETED/CANCELLED')
    start_date = Column(DateTime, comment='开始日期')
    end_date = Column(DateTime, comment='结束日期')
    created_by = Column(String(36), comment='创建者ID')
    conclusion_summary = Column(Text, comment='结论摘要')
    recommendation = Column(Text, comment='建议')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_abtest_status', 'status'),
        Index('idx_abtest_dates', 'start_date', 'end_date'),
    )


class ABTestParticipantRecord(Base):
    """A/B测试参与者记录表"""
    __tablename__ = 'ab_test_participant_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(String(36), unique=True, nullable=False, comment='参与者唯一标识')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    test_id = Column(String(36), ForeignKey('ab_test_sessions.test_id'), nullable=False, comment='测试ID')
    assigned_group = Column(String(10), nullable=False, comment='分配组别: CONTROL/EXPERIMENT')
    assigned_at = Column(DateTime, default=datetime.utcnow, comment='分配时间')
    is_excluded = Column(Boolean, default=False, comment='是否排除')
    exclusion_reason = Column(String(100), comment='排除原因')

    __table_args__ = (
        Index('idx_abpart_user_test', 'user_id', 'test_id'),
        Index('idx_abpart_group', 'assigned_group'),
    )


class ABTestMetricResult(Base):
    """A/B测试指标结果表"""
    __tablename__ = 'ab_test_metric_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(String(36), unique=True, nullable=False, comment='结果唯一标识')
    test_id = Column(String(36), nullable=False, comment='测试ID')
    group = Column(String(10), nullable=False, comment='组别: CONTROL/EXPERIMENT')
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    mean_value = Column(Float, comment='均值')
    std_value = Column(Float, comment='标准差')
    sample_size = Column(Integer, default=0, comment='样本大小')
    ci_lower = Column(Float, comment='置信区间下界')
    ci_upper = Column(Float, comment='置信区间上界')
    p_value = Column(Float, comment='P值')
    is_significant = Column(Boolean, default=False, comment='是否显著')
    effect_size_cohen_d = Column(Float, comment='效应量Cohen d')
    calculated_at = Column(DateTime, default=datetime.utcnow, comment='计算时间')

    __table_args__ = (
        Index('idx_abmetric_test_group_metric', 'test_id', 'group', 'metric_name'),
    )


class UserFeedbackOnEffect(Base):
    """用户对效果的反馈表"""
    __tablename__ = 'user_feedback_on_effects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), unique=True, nullable=False, comment='记录唯一标识')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    effect_display_id = Column(String(36), nullable=False, comment='效果展示ID')
    is_helpful = Column(Boolean, nullable=False, comment='是否有帮助')
    reason_code = Column(String(30), comment='原因代码: EFFECT_NOT_NOTICEABLE/DATA_INACCURATE/NO_CHANGE_PERCEIVED/MISLEADING_DISPLAY/OTHER')
    comment_text = Column(Text, comment='评论内容')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_feedback_user_display', 'user_id', 'effect_display_id'),
        Index('idx_feedback_helpful', 'is_helpful'),
    )


class ComparisonTestSession(Base):
    """对比测试会话表"""
    __tablename__ = 'comparison_test_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, comment='会话唯一标识')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    version_a_level = Column(Integer, nullable=False, comment='版本A等级')
    version_b_level = Column(Integer, nullable=False, comment='版本B等级')
    test_task_input_json = Column(JSON, comment='测试任务输入JSON')
    status = Column(String(20), default='PENDING', comment='状态: PENDING/RUNNING/COMPLETED/FAILED')
    version_a_output_json = Column(JSON, comment='版本A输出JSON')
    version_b_output_json = Column(JSON, comment='版本B输出JSON')
    time_a_ms = Column(Integer, comment='版本A耗时(毫秒)')
    time_b_ms = Column(Integer, comment='版本B耗时(毫秒)')
    quality_a_score = Column(Float, comment='版本A质量评分')
    quality_b_score = Column(Float, comment='版本B质量评分')
    cost_a_points = Column(Float, comment='版本A消耗积分')
    cost_b_points = Column(Float, comment='版本B消耗积分')
    winner = Column(String(10), comment='获胜方: VERSION_A/VERSION_B/TIE')
    improvement_summary = Column(Text, comment='改进摘要')
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_comparison_agent', 'agent_id'),
        Index('idx_comparison_status', 'status'),
    )


class AchievementUnlockRecord(Base):
    """成就解锁记录表"""
    __tablename__ = 'achievement_unlock_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    unlock_id = Column(String(36), unique=True, nullable=False, comment='解锁唯一标识')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    achievement_key = Column(String(50), nullable=False, comment='成就标识: eagle_eye/speed_demon/quality_master/bond_collector/skill_scholar')
    achievement_name = Column(String(100), nullable=False, comment='成就名称')
    icon_emoji = Column(String(20), comment='图标emoji')
    description = Column(Text, comment='成就描述')
    unlocked_at = Column(DateTime, default=datetime.utcnow, comment='解锁时间')
    trigger_agent_id = Column(String(36), comment='触发智能体ID')
    trigger_event_json = Column(JSON, comment='触发事件JSON')
    notification_sent = Column(Boolean, default=False, comment='是否已发送通知')

    __table_args__ = (
        Index('idx_achievement_user', 'user_id'),
        Index('idx_achievement_key', 'achievement_key'),
    )


class LeaderboardEffectEntry(Base):
    """排行榜效果条目表"""
    __tablename__ = 'leaderboard_effect_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(36), unique=True, nullable=False, comment='条目唯一标识')
    period_start = Column(Date, nullable=False, comment='统计周期开始日期')
    period_end = Column(Date, nullable=False, comment='统计周期结束日期')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    agent_name = Column(String(100), comment='智能体名称')
    agent_level = Column(Integer, comment='智能体等级')
    monthly_improvement_pct = Column(Float, default=0.0, comment='月度改进百分比')
    response_time_change_pct = Column(Float, default=0.0, comment='响应时间变化百分比')
    accuracy_change_pct = Column(Float, default=0.0, comment='准确率变化百分比')
    cost_change_pct = Column(Float, default=0.0, comment='成本变化百分比')
    rank_position = Column(Integer, comment='当前排名位置')
    previous_rank = Column(Integer, comment='上一周期排名')
    category = Column(String(20), nullable=False, comment='分类: SPEED/QUALITY/COST/OVERALL')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_leaderboard_period_category_rank', 'period_start', 'period_end', 'category', 'rank_position'),
        Index('idx_leaderboard_agent', 'agent_id'),
    )


class PerformanceProbeLog(Base):
    """性能探测日志表"""
    __tablename__ = 'performance_probe_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    probe_id = Column(String(36), unique=True, nullable=False, comment='探测唯一标识')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    task_id = Column(String(36), nullable=False, comment='任务ID')
    task_type = Column(String(50), comment='任务类型')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, nullable=False, comment='结束时间')
    duration_ms = Column(Integer, comment='持续时间(毫秒)')
    output_quality_score = Column(Float, comment='输出质量评分(0-1)')
    api_calls_count = Column(Integer, default=0, comment='API调用次数')
    points_consumed = Column(Float, default=0.0, comment='消耗积分')
    error_occurred = Column(Boolean, default=False, comment='是否出错')
    error_message = Column(Text, comment='错误信息')
    metadata_json = Column(JSON, comment='元数据JSON')
    reported_at = Column(DateTime, default=datetime.utcnow, comment='上报时间')

    __table_args__ = (
        Index('idx_probe_agent_start', 'agent_id', 'start_time'),
        Index('idx_probe_task', 'task_id'),
    )


class EffectDisplayCache(Base):
    """效果展示缓存表"""
    __tablename__ = 'effect_display_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(200), unique=True, nullable=False, comment='缓存键')
    cache_value = Column(JSON, nullable=False, comment='缓存值JSON')
    agent_id = Column(String(36), comment='智能体ID')
    data_type = Column(String(20), nullable=False, comment='数据类型: UPGRADE_EFFECT/TIMELINE/RECOMMENDATION/ATTRIBUTION')
    ttl_seconds = Column(Integer, default=300, comment='TTL秒数')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    hit_count = Column(Integer, default=0, comment='命中次数')
    last_accessed_at = Column(DateTime, default=datetime.utcnow, comment='最后访问时间')

    __table_args__ = (
        Index('idx_cache_agent_type', 'agent_id', 'data_type'),
        Index('idx_cache_expires', 'expires_at'),
    )


# =============================================================================
# 第三十六部分：量化融合智能体人才市场与技能市场 (quant_fusion_talent_skill_market_layer.py)
# =============================================================================

class AgentCultivationRecord(Base):
    """智能体修炼记录表"""
    __tablename__ = 'agent_cultivation_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    owner_user_id = Column(String(36), nullable=False, comment='所有者用户ID')
    agent_type = Column(String(20), nullable=False, comment='智能体类型: LI_BU/GONG_BU/XING_BU等')
    current_realm = Column(String(20), nullable=False, comment='当前境界: LIAN_QI/ZHU_JI/JIN_DAN/YUAN_YING/HUA_SHEN/DU_JIE/DA_CHENG')
    total_exp = Column(Integer, default=0, comment='总经验值')
    exp_to_next_level = Column(Integer, default=0, comment='升级所需经验')
    learned_skills_json = Column(JSON, comment='已学技能JSON')
    specialization = Column(String(50), comment='专精方向: TREND_PREDICTION/RISK_ASSESSMENT/POLICY_ANALYSIS/FACTOR_MINING')
    total_tasks_completed = Column(Integer, default=0, comment='完成任务总数')
    last_activity_at = Column(DateTime, comment='最后活动时间')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_agent_cultivation_agent_owner', 'agent_id', 'owner_user_id'),
        Index('idx_agent_cultivation_realm', 'current_realm'),
        Index('idx_agent_cultivation_owner_realm', 'owner_user_id', 'current_realm'),
    )


class AgentRecruitmentLog(Base):
    """智能体招募日志表"""
    __tablename__ = 'agent_recruitment_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    agent_type_recruited = Column(String(20), nullable=False, comment='招募的智能体类型')
    agent_realm_at_recruitment = Column(String(20), comment='招募时智能体境界')
    user_realm_at_recruitment = Column(String(20), comment='招募时用户境界')
    cost_points_spent = Column(Integer, default=0, comment='消耗点数')
    recruitment_source = Column(String(20), nullable=False, comment='来源: MARKETPLACE/ACHIEVEMENT_REWARD/EVENT/GIFT')
    is_successful = Column(Boolean, default=True, comment='是否成功')
    failure_reason = Column(Text, comment='失败原因')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_recruit_log_user', 'user_id'),
        Index('idx_recruit_log_type', 'agent_type_recruited'),
    )


class CultivationTaskProgress(Base):
    """修炼任务进度表"""
    __tablename__ = 'cultivation_task_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False, comment='任务ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    completion_count = Column(Integer, default=0, comment='完成次数')
    max_completions = Column(Integer, nullable=False, comment='最大完成次数')
    last_completed_at = Column(DateTime, comment='最后完成时间')
    exp_earned_total = Column(Integer, default=0, comment='累计获得经验')
    cooldown_expires_at = Column(DateTime, comment='冷却到期时间')
    reward_claimed = Column(Boolean, default=False, comment='奖励是否已领取')
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('task_id', 'agent_id', 'user_id', name='uq_task_progress'),
    )


class SkillPurchaseRecord(Base):
    """技能购买记录表"""
    __tablename__ = 'skill_purchase_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(String(36), unique=True, nullable=False, comment='购买记录ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    skill_id = Column(String(50), nullable=False, comment='技能ID')
    skill_tier = Column(String(20), nullable=False, comment='技能层级')
    skill_name = Column(String(100), nullable=False, comment='技能名称')
    cost_points = Column(Integer, nullable=False, comment='消耗点数')
    user_realm_at_purchase = Column(String(20), nullable=False, comment='购买时用户境界')
    resonance_triggered = Column(Boolean, default=False, comment='是否触发共鸣')
    resonance_bonuses_json = Column(JSON, comment='共鸣加成JSON')
    points_refunded = Column(Integer, default=0, comment='退还点数')
    refunded_at = Column(DateTime, comment='退款时间')
    purchased_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_skill_purchase_user_skill', 'user_id', 'skill_id'),
        Index('idx_skill_purchase_user', 'user_id'),
    )


class SkillEffectApplicationLog(Base):
    """技能效果应用日志表"""
    __tablename__ = 'skill_effect_application_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String(36), unique=True, nullable=False, comment='应用记录ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    skill_id = Column(String(50), nullable=False, comment='技能ID')
    agent_id = Column(String(36), comment='智能体ID')
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    effect_type = Column(String(20), nullable=False, comment='效果类型: accuracy_boost/speed_boost/new_capability/confidence_narrowing')
    effect_value = Column(Float, nullable=False, comment='效果值')
    applied_at = Column(DateTime, default=datetime.utcnow, comment='应用时间')
    expires_at = Column(DateTime, comment='过期时间')
    is_active = Column(Boolean, default=True, comment='是否生效中')

    __table_args__ = (
        Index('idx_skill_effect_user_skill', 'user_id', 'skill_id'),
        Index('idx_skill_effect_agent', 'agent_id'),
    )


class AgentUpgradeBonusLog(Base):
    """智能体升级加成日志表"""
    __tablename__ = 'agent_upgrade_bonus_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    upgrade_event_id = Column(String(36), unique=True, nullable=False, comment='升级事件ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    from_realm = Column(String(20), nullable=False, comment='原境界')
    to_realm = Column(String(20), nullable=False, comment='目标境界')
    quant_bonus_details_json = Column(JSON, comment='量化加成详情JSON')
    new_capabilities_unlocked_json = Column(JSON, comment='解锁新能力JSON')
    total_boost_pct = Column(Float, default=0.0, comment='总提升百分比')
    triggered_by = Column(String(20), nullable=False, comment='触发方式: TASK_EXP/DIRECT_PURGE/EVENT_BONUS')
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_upgrade_bonus_agent', 'agent_id'),
        Index('idx_upgrade_bonus_realms', 'from_realm', 'to_realm'),
    )


class BondSynergyActivationLog(Base):
    """羁绊协同激活日志表"""
    __tablename__ = 'bond_synergy_activation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    activation_id = Column(String(36), unique=True, nullable=False, comment='激活记录ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    bond_pair = Column(String(50), nullable=False, comment='羁绊对: 如LI_BU+GONG_BU')
    synergy_name = Column(String(100), nullable=False, comment='协同名称')
    quant_dimension_affected = Column(String(50), nullable=False, comment='受影响的量化维度')
    boost_pct = Column(Float, nullable=False, comment='提升百分比')
    report_annotation_generated = Column(Boolean, default=False, comment='是否生成报告标注')
    activation_timestamp = Column(DateTime, default=datetime.utcnow, comment='激活时间')
    deactivation_timestamp = Column(DateTime, comment='停用时间')
    duration_hours = Column(Float, comment='持续时长(小时)')

    __table_args__ = (
        Index('idx_bond_synergy_user_pair', 'user_id', 'bond_pair'),
    )


class SpecializationRecord(Base):
    """专精记录表"""
    __tablename__ = 'specialization_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), unique=True, nullable=False, comment='记录ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    specialization = Column(String(50), nullable=False, comment='专精方向: TREND_PREDICTION/RISK_ASSESSMENT/POLICY_ANALYSIS/FACTOR_MINING')
    unlock_cost_points = Column(Integer, nullable=False, comment='解锁消耗点数')
    unlocked_at = Column(DateTime, default=datetime.utcnow, comment='解锁时间')
    reset_count = Column(Integer, default=0, comment='重置次数')
    last_reset_at = Column(DateTime, comment='最后重置时间')
    total_boost_applied = Column(Float, default=0.0, comment='累计应用提升值')
    is_active = Column(Boolean, default=True, comment='是否活跃')

    __table_args__ = (
        Index('idx_specialization_agent_spec', 'agent_id', 'specialization'),
        Index('idx_specialization_agent', 'agent_id'),
    )


class MasteryResonanceEvent(Base):
    """精通共鸣事件表"""
    __tablename__ = 'mastery_resonance_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    source_skill_id = Column(String(50), nullable=False, comment='源技能ID')
    target_skill_id = Column(String(50), nullable=False, comment='目标技能ID')
    resonance_type = Column(String(20), nullable=False, comment='共鸣类型: direct/indirect/transitive')
    exp_bonus_pct = Column(Float, nullable=False, comment='经验加成百分比')
    actual_exp_added = Column(Float, nullable=False, comment='实际增加经验值')
    depth_level = Column(Integer, nullable=False, comment='深度层级')
    triggered_at = Column(DateTime, default=datetime.utcnow, comment='触发时间')
    notification_sent = Column(Boolean, default=False, comment='是否已发送通知')

    __table_args__ = (
        Index('idx_resonance_user_source', 'user_id', 'source_skill_id'),
        Index('idx_resonance_target', 'target_skill_id'),
    )


class CultivationRecommendationLog(Base):
    """修炼推荐日志表"""
    __tablename__ = 'cultivation_recommendation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rec_id = Column(String(36), unique=True, nullable=False, comment='推荐ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    action_type = Column(String(30), nullable=False, comment='操作类型: RECRUIT_AGENT/UPGRADE_AGENT/LEARN_SKILL/COMPLETE_TASK/ACTIVATE_BOND/CHANGE_SPECIALIZATION/PARTICIPATE_EVENT')
    target_id = Column(String(50), comment='目标ID')
    title = Column(String(200), nullable=False, comment='推荐标题')
    priority_score = Column(Float, nullable=False, comment='优先级评分')
    was_accepted = Column(Boolean, comment='是否被接受')
    accepted_at = Column(DateTime, comment='接受时间')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')

    __table_args__ = (
        Index('idx_recommendation_user_time', 'user_id', 'generated_at'),
        Index('idx_recommendation_action', 'action_type'),
    )


class LeaderboardSnapshot(Base):
    """排行榜快照表"""
    __tablename__ = 'leaderboard_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照ID')
    period_type = Column(String(10), nullable=False, comment='周期类型: weekly/monthly/all_time')
    period_start = Column(Date, nullable=False, comment='周期开始日期')
    period_end = Column(Date, nullable=False, comment='周期结束日期')
    category = Column(String(30), nullable=False, comment='类别: TOTAL_AGENT_EXP/SKILLS_LEARNED_COUNT/QUANT_ANALYSIS_USAGE/BOND_ACTIVATIONS/WEEKLY_PROGRESS')
    rank_position = Column(Integer, nullable=False, comment='排名位置')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    display_name = Column(String(100), nullable=False, comment='显示名称')
    score = Column(Float, nullable=False, comment='分数')
    top_agent_realm = Column(String(20), comment='最高智能体境界')
    skill_count = Column(Integer, default=0, comment='技能数量')
    analysis_count = Column(Integer, default=0, comment='分析数量')
    title_held = Column(String(50), comment='持有称号')
    snapshot_generated_at = Column(DateTime, default=datetime.utcnow, comment='快照生成时间')

    __table_args__ = (
        Index('idx_leaderboard_period_category_rank', 'period_type', 'period_start', 'category', 'rank_position'),
        Index('idx_leaderboard_user', 'user_id'),
    )


class TitleAwardRecord(Base):
    """称号授予记录表"""
    __tablename__ = 'title_award_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    award_id = Column(String(36), unique=True, nullable=False, comment='授予记录ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    title_key = Column(String(50), nullable=False, comment='称号键名')
    title_name = Column(String(100), nullable=False, comment='称号名称')
    icon_emoji = Column(String(20), comment='图标表情')
    awarded_at = Column(DateTime, default=datetime.utcnow, comment='授予时间')
    award_period_start = Column(Date, comment='授予周期开始')
    award_period_end = Column(Date, comment='授予周期结束')
    reward_points = Column(Integer, default=0, comment='奖励点数')
    notification_sent = Column(Boolean, default=False, comment='是否已发送通知')

    __table_args__ = (
        Index('idx_title_award_user', 'user_id'),
        Index('idx_title_award_key', 'title_key'),
    )


class LimitedTimeCultivationEvent(Base):
    """限时修炼活动表"""
    __tablename__ = 'limited_time_cultivation_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='活动ID')
    event_name = Column(String(200), nullable=False, comment='活动名称')
    event_type = Column(String(20), nullable=False, comment='活动类型: DOUBLE_EXP_WEEK/SKILL_DISCOUNT/AGENT_RECRUIT_BONUS/BOND_BOOST_EVENT/SPECIAL_DROPP_RATE')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, nullable=False, comment='结束时间')
    multiplier = Column(Float, nullable=False, comment='倍率')
    applicable_scope_json = Column(JSON, comment='适用范围JSON')
    banner_message = Column(Text, comment='横幅消息')
    popup_enabled = Column(Boolean, default=False, comment='是否启用弹窗')
    participation_count = Column(Integer, default=0, comment='参与人数')
    status = Column(String(10), nullable=False, comment='状态: DRAFT/ACTIVE/ENDED/CANCELLED')
    created_by = Column(String(36), comment='创建人ID')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_limited_event_status', 'status'),
        Index('idx_limited_event_time', 'start_time', 'end_time'),
    )


class EventParticipationRecord(Base):
    """活动参与记录表"""
    __tablename__ = 'event_participation_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    participation_id = Column(String(36), unique=True, nullable=False, comment='参与记录ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    event_id = Column(String(36), ForeignKey('limited_time_cultivation_events.event_id'), nullable=False, comment='活动ID')
    participated_at = Column(DateTime, default=datetime.utcnow, comment='参与时间')
    base_value_before = Column(Float, comment='修改前基础值')
    modified_value_after = Column(Float, comment='修改后数值')
    modifier_applied = Column(Float, comment='应用修正值')
    engagement_metrics_json = Column(JSON, comment='参与指标JSON')

    __table_args__ = (
        Index('idx_event_participation_user_event', 'user_id', 'event_id'),
        Index('idx_event_participation_event', 'event_id'),
    )


# =============================================================================
# 第三十七部分：团队管理与多板块深度关联 (team_management_multidomain_layer.py)
# =============================================================================

class TeamRecord(Base):
    """团队基础信息表"""
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(36), unique=True, nullable=False, comment='团队唯一标识')
    team_name = Column(String(100), nullable=False, comment='团队名称')
    motto = Column(Text, comment='团队座右铭')
    leader_user_id = Column(String(36), nullable=False, comment='队长用户ID')
    level = Column(Integer, default=1, comment='团队等级 1-10')
    team_tp = Column(Integer, default=0, comment='团队类型')
    team_realm = Column(String(30), default='ZHU_JI_TEAM', comment='团队境界: ZHU_JI_TEAM/JIN_DAN_TEAM/YUAN_YING_TEAM/HUA_SHEN_TEAM/DU_JIE_TEAM/DA_CHENG_TEAM')
    max_capacity = Column(Integer, default=3, comment='最大成员容量')
    current_member_count = Column(Integer, default=0, comment='当前成员数')
    total_skill_points = Column(Integer, default=0, comment='总技能点')
    skill_points_invested = Column(Integer, default=0, comment='已投入技能点')
    total_contribution_points = Column(Float, default=0.0, comment='总贡献点')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_teams_leader_user_id', 'leader_user_id'),
        Index('idx_teams_team_realm', 'team_realm'),
        Index('idx_teams_level', 'level'),
    )


class TeamMemberRecord(Base):
    """团队成员记录表"""
    __tablename__ = 'team_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(String(36), unique=True, nullable=False, comment='成员记录ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='所属团队ID')
    agent_id = Column(String(36), nullable=False, comment='代理ID')
    agent_type = Column(String(20), comment='代理类型')
    agent_realm = Column(String(20), comment='代理境界')
    agent_level = Column(Integer, comment='代理等级')
    role_in_team = Column(String(20), default='MEMBER', comment='团队角色: LEADER/MEMBER/GUARDIAN')
    contribution_points = Column(Float, default=0.0, comment='贡献点')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    joined_at = Column(DateTime, default=datetime.utcnow, comment='加入时间')
    left_at = Column(DateTime, nullable=True, comment='离开时间')

    __table_args__ = (
        UniqueConstraint('team_id', 'agent_id', name='uq_team_agent'),
        Index('idx_team_members_team_id', 'team_id'),
        Index('idx_team_members_agent_id', 'agent_id'),
    )


class TeamSkillStateRecord(Base):
    """团队技能状态表"""
    __tablename__ = 'team_skill_states'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), unique=True, nullable=False, comment='记录ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    skill_id = Column(String(50), nullable=False, comment='技能ID')
    current_level = Column(Integer, default=0, comment='当前等级')
    max_level = Column(Integer, comment='最大等级')
    total_points_invested = Column(Integer, default=0, comment='已投入总点数')
    last_upgraded_at = Column(DateTime, nullable=True, comment='最后升级时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        UniqueConstraint('team_id', 'skill_id', name='uq_team_skill'),
    )


class TeamExpLog(Base):
    """团队经验日志表"""
    __tablename__ = 'team_exp_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(36), unique=True, nullable=False, comment='日志ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    tp_amount = Column(Integer, comment='经验值数量')
    source_type = Column(String(30), comment='来源类型: MEMBER_TASK/TEAM_TASK/BOND_ACTIVATION/EVENT_BONUS/TRIBULATION')
    source_detail = Column(JSON, comment='来源详情JSON')
    awarded_by_user_id = Column(String(36), nullable=True, comment='授予者用户ID')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='时间戳')

    __table_args__ = (
        Index('idx_team_exp_logs_team_timestamp', 'team_id', 'timestamp'),
    )


class TeamLevelUpHistory(Base):
    """团队升级历史表"""
    __tablename__ = 'team_level_up_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(String(36), unique=True, nullable=False, comment='历史记录ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    old_level = Column(Integer, comment='旧等级')
    new_level = Column(Integer, comment='新等级')
    rewards_granted_json = Column(JSON, comment='发放奖励JSON')
    triggered_by = Column(String(50), comment='触发原因')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='时间戳')

    __table_args__ = (
        Index('idx_team_level_up_history_team_id', 'team_id'),
    )


class TeamRecruitmentRecommendationLog(Base):
    """团队招募推荐日志表"""
    __tablename__ = 'team_recruitment_recommendation_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rec_id = Column(String(36), unique=True, nullable=False, comment='推荐记录ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='目标团队ID')
    recommended_agent_type = Column(String(20), comment='推荐代理类型')
    recommendation_reason = Column(Text, comment='推荐理由')
    bond_would_activate = Column(String(50), comment='可激活的羁绊')
    synergy_gain_pct = Column(Float, comment='协同增益百分比')
    was_accepted = Column(Boolean, nullable=True, comment='是否被接受')
    viewed_at = Column(DateTime, comment='查看时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_team_rec_user_team', 'user_id', 'team_id'),
    )


class ExperienceTransferRecord(Base):
    """经验转移记录表"""
    __tablename__ = 'experience_transfer_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transfer_id = Column(String(36), unique=True, nullable=False, comment='转移记录ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    source_member_id = Column(String(36), ForeignKey('team_members.member_id'), nullable=False, comment='来源成员ID')
    target_member_id = Column(String(36), ForeignKey('team_members.member_id'), nullable=False, comment='目标成员ID')
    source_exp_before = Column(Integer, comment='来源转移前经验')
    source_exp_after = Column(Integer, comment='来源转移后经验')
    target_exp_before = Column(Integer, comment='目标转移前经验')
    target_exp_after = Column(Integer, comment='目标转移后经验')
    transfer_amount = Column(Integer, comment='转移数量')
    efficiency_ratio = Column(Float, comment='效率比率')
    cooldown_until = Column(DateTime, comment='冷却截止时间')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='时间戳')

    __table_args__ = (
        Index('idx_exp_transfer_team_id', 'team_id'),
        Index('idx_exp_transfer_source_member', 'source_member_id'),
    )


class TeamSkillBookPurchaseRecord(Base):
    """团队技能书购买记录表"""
    __tablename__ = 'team_skill_book_purchase_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(String(36), unique=True, nullable=False, comment='购买记录ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    book_id = Column(String(50), comment='书籍ID')
    book_name = Column(String(100), comment='书籍名称')
    purchased_by_captain = Column(String(36), comment='队长购买人')
    cost_points = Column(Integer, comment='消耗点数')
    members_affected_count = Column(Integer, comment='影响成员数')
    active = Column(Boolean, default=True, comment='是否有效')
    purchased_at = Column(DateTime, default=datetime.utcnow, comment='购买时间')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')

    __table_args__ = (
        Index('idx_team_skill_book_purchase_team_id', 'team_id'),
    )


class SkillSharingRecord(Base):
    """技能分享记录表"""
    __tablename__ = 'skill_sharing_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    share_id = Column(String(36), unique=True, nullable=False, comment='分享记录ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    sharer_member_id = Column(String(36), ForeignKey('team_members.member_id'), nullable=False, comment='分享者成员ID')
    skill_id = Column(String(50), comment='技能ID')
    skill_name = Column(String(100), comment='技能名称')
    original_effect_value = Column(Float, comment='原始效果值')
    shared_effect_value = Column(Float, comment='分享后效果值')
    team_points_cost = Column(Integer, comment='团队点数成本')
    is_active = Column(Boolean, default=True, comment='是否有效')
    share_date = Column(DateTime, default=datetime.utcnow, comment='分享日期')
    unshare_date = Column(DateTime, nullable=True, comment='取消分享日期')

    __table_args__ = (
        Index('idx_skill_sharing_team_skill', 'team_id', 'skill_id'),
    )


class TeamQuantReportRecord(Base):
    """团队量化报告记录表"""
    __tablename__ = 'team_quant_report_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    analysis_request_json = Column(JSON, comment='分析请求JSON')
    participating_agent_ids = Column(JSON, comment='参与代理ID列表JSON')
    standard_content_path = Column(String(300), comment='标准内容路径')
    team_contribution_html = Column(Text, comment='团队贡献HTML报告')
    team_skill_bonuses_applied = Column(JSON, comment='应用团队技能加成JSON')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')
    view_count = Column(Integer, default=0, comment='查看次数')
    share_count = Column(Integer, default=0, comment='分享次数')

    __table_args__ = (
        Index('idx_team_quant_report_team_id', 'team_id'),
    )


class TeamChallengeSessionRecord(Base):
    """团队挑战会话记录表"""
    __tablename__ = 'team_challenge_session_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, comment='会话ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    challenge_id = Column(String(50), comment='挑战ID')
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE/COMPLETED/FAILED/EXPIRED')
    started_at = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    current_progress_json = Column(JSON, comment='当前进度JSON')
    participant_contributions_json = Column(JSON, comment='参与者贡献JSON')
    attempts_json = Column(JSON, comment='尝试记录JSON')
    result_reward_tp = Column(Integer, nullable=True, comment='结果奖励经验值')
    result_title_awarded = Column(String(100), nullable=True, comment='获得称号')

    __table_args__ = (
        Index('idx_team_challenge_team_status', 'team_id', 'status'),
    )


class TeamTaskSessionRecord(Base):
    """团队任务会话记录表"""
    __tablename__ = 'team_task_session_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, comment='会话ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    task_id = Column(String(50), comment='任务ID')
    claimed_by_captain = Column(String(36), comment='认领的队长')
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE/COMPLETED/CANCELLED/EXPIRED')
    target_count = Column(Integer, comment='目标数量')
    current_count = Column(Integer, default=0, comment='当前数量')
    reward_team_tp = Column(Integer, comment='奖励团队经验值')
    reward_skill_points = Column(Integer, comment='奖励技能点')
    reward_points = Column(Integer, comment='奖励积分')
    claimed_at = Column(DateTime, default=datetime.utcnow, comment='认领时间')
    deadline = Column(DateTime, comment='截止时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')

    __table_args__ = (
        Index('idx_team_task_session_team_status', 'team_id', 'status'),
    )


class TeamTaskContributionRecord(Base):
    """团队任务贡献记录表"""
    __tablename__ = 'team_task_contribution_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contribution_id = Column(String(36), unique=True, nullable=False, comment='贡献记录ID')
    task_session_id = Column(String(36), ForeignKey('team_task_session_records.session_id'), nullable=False, comment='任务会话ID')
    member_id = Column(String(36), ForeignKey('team_members.member_id'), nullable=False, comment='成员ID')
    contribution_value = Column(Float, comment='贡献值')
    contribution_detail = Column(JSON, comment='贡献详情JSON')
    cumulative_value = Column(Float, comment='累计值')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='时间戳')

    __table_args__ = (
        Index('idx_team_task_contrib_task_session', 'task_session_id'),
        Index('idx_team_task_contrib_member', 'member_id'),
    )


class TeamMemoryRecord(Base):
    """团队记忆记录表"""
    __tablename__ = 'team_memory_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(36), unique=True, nullable=False, comment='记忆ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    memory_type = Column(String(30), comment='记忆类型: TASK_OUTCOME/ANALYSIS_CONCLUSION/OPTIMIZATION_STRATEGY/LESSON_LEARNED')
    title = Column(String(200), comment='标题')
    content = Column(Text, comment='内容')
    author_member_id = Column(String(36), ForeignKey('team_members.member_id'), comment='作者成员ID')
    version = Column(Integer, default=1, comment='版本号')
    parent_version_id = Column(String(36), nullable=True, comment='父版本ID')
    tags_json = Column(JSON, comment='标签JSON')
    access_level = Column(String(10), default='READ_ONLY', comment='访问级别: READ_ONLY/EDITABLE')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_team_memory_team_type', 'team_id', 'memory_type'),
    )


class TeamTribulationSessionRecord(Base):
    """团队渡劫会话记录表"""
    __tablename__ = 'team_tribulation_session_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, comment='会话ID')
    team_id = Column(String(36), ForeignKey('teams.team_id'), nullable=False, comment='团队ID')
    tribulation_id = Column(String(50), comment='劫难ID')
    status = Column(String(20), default='PREPARING', comment='状态: PREPARING/IN_PROGRESS/PASSED/FAILED/COOLDOWN')
    difficulty = Column(String(20), comment='难度: HEAVENLY/EARTHLY/DEMONIC')
    attempts_json = Column(JSON, comment='尝试记录JSON')
    passed = Column(Boolean, nullable=True, comment='是否通过')
    rewards_earned_json = Column(JSON, comment='获得奖励JSON')
    title_awarded = Column(String(100), nullable=True, comment='获得称号')
    cooldown_until = Column(DateTime, nullable=True, comment='冷却截止时间')
    started_at = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')

    __table_args__ = (
        Index('idx_team_tribulation_team_status', 'team_id', 'status'),
    )

# =============================================================================
# 第三十八部分：任务分析与其他模块联动 (task_analysis_cross_module_layer.py)
# =============================================================================

class TaskActionPanelLog(Base):
    """任务操作面板交互日志表"""
    __tablename__ = 'task_action_panel_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    session_id = Column(String(36), nullable=False, comment='会话ID')
    action_type = Column(String(50), nullable=False, comment='操作类型: VIEW_DETAIL/COMPARE/REPORT/MEMORY/RECRUIT/AUTONOMOUS')
    target_module = Column(String(50), comment='目标模块')
    task_id = Column(String(36), comment='任务ID')
    property_ids_json = Column(JSON, comment='关联房源ID列表JSON')
    result_status = Column(String(20), default='SUCCESS', comment='结果状态: SUCCESS/FAILED/PENDING')
    latency_ms = Column(Integer, default=0, comment='响应延迟毫秒数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class TaskRedirectRecord(Base):
    """任务重定向路由记录表"""
    __tablename__ = 'task_redirect_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_task_id = Column(String(36), nullable=False, comment='源任务ID')
    source_action = Column(String(50), nullable=False, comment='源操作')
    target_module = Column(String(50), nullable=False, comment='目标模块')
    target_url = Column(Text, comment='目标URL')
    context_params_json = Column(JSON, comment='上下文参数JSON')
    redirect_count = Column(Integer, default=0, comment='重定向次数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class TaskHistorySnapshot(Base):
    """任务中心历史快照表"""
    __tablename__ = 'task_history_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    snapshot_type = Column(String(20), default='DAILY', comment='快照类型: DAILY/WEEKLY/MONTHLY')
    total_tasks = Column(Integer, default=0, comment='总任务数')
    completed_count = Column(Integer, default=0, comment='已完成数')
    failed_count = Column(Integer, default=0, comment='失败数')
    avg_duration_sec = Column(Float, default=0.0, comment='平均耗时秒')
    snapshot_data_json = Column(JSON, comment='快照详细数据JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class BatchOperationLog(Base):
    """批量操作日志表"""
    __tablename__ = 'batch_operation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    operation_type = Column(String(20), nullable=False, comment='操作类型: BATCH_DELETE/BATCH_RETRY/BATCH_EXPORT')
    task_ids_json = Column(JSON, nullable=False, comment='任务ID列表JSON')
    success_count = Column(Integer, default=0, comment='成功数')
    fail_count = Column(Integer, default=0, comment='失败数')
    error_details_json = Column(JSON, comment='错误详情JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class TaskTeamAgentDisplayLog(Base):
    """任务团队智能体展示日志表"""
    __tablename__ = 'task_team_agent_display_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='任务ID')
    team_id = Column(String(36), comment='团队ID')
    agent_id = Column(String(36), comment='智能体ID')
    display_role = Column(String(50), comment='展示角色: LEADER/ANALYST/VALUER/REPORTER/GUARDIAN')
    actual_role = Column(String(50), comment='实际角色')
    display_mode = Column(String(20), default='AVATAR', comment='展示模式: AVATAR/CARD/FULL')
    view_count = Column(Integer, default=0, comment='查看次数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class TeamAgentLoadSnapshot(Base):
    """团队智能体负载快照表"""
    __tablename__ = 'team_agent_load_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(36), nullable=False, comment='团队ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    current_load = Column(Integer, default=0, comment='当前负载数')
    max_capacity = Column(Integer, default=10, comment='最大容量')
    load_percentage = Column(Float, default=0.0, comment='负载百分比')
    warning_level = Column(String(20), default='NORMAL', comment='警告级别: NORMAL/HIGH/CRITICAL/OVERLOAD')
    snapshot_time = Column(DateTime, default=datetime.utcnow, comment='快照时间')

class PropertyCompareSelectionRecord(Base):
    """房源对比选择记录表"""
    __tablename__ = 'property_compare_selection_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='任务ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    selected_property_ids_json = Column(JSON, nullable=False, comment='已选房源ID列表JSON')
    extracted_from_result = Column(Boolean, default=False, comment='是否从任务结果提取')
    compare_session_id = Column(String(36), comment='对比会话ID')
    compare_url = Column(Text, comment='生成的对比URL')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class TaskPropertyImportLog(Base):
    """任务结果房源导入日志表"""
    __tablename__ = 'task_property_import_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='任务ID')
    import_source = Column(String(50), nullable=False, comment='导入来源: TASK_RESULT/USER_UPLOAD/API_FETCH')
    property_count = Column(Integer, default=0, comment='导入房源数量')
    property_ids_json = Column(JSON, comment='导入的房源ID列表JSON')
    import_status = Column(String(20), default='PENDING', comment='导入状态: PENDING/SUCCESS/FAILED/PARTIAL')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AutoReportSaveRecord(Base):
    """自动报告保存记录表"""
    __tablename__ = 'auto_report_save_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, unique=True, comment='任务ID')
    report_id = Column(String(36), comment='报告ID')
    report_title = Column(String(200), comment='报告标题')
    report_type = Column(String(50), comment='报告类型: VALUATION/COMPARISON/MARKET_ANALYSIS')
    save_trigger = Column(String(30), default='TASK_COMPLETE', comment='保存触发: TASK_COMPLETE/MANUAL/SCHEDULED')
    file_path = Column(Text, comment='文件存储路径')
    file_size_kb = Column(Integer, default=0, comment='文件大小KB')
    backlink_to_task = Column(Boolean, default=True, comment='是否反向链接到任务中心')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AnalysisPreferenceRecord(Base):
    """用户分析偏好记录表"""
    __tablename__ = 'analysis_preference_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    preference_category = Column(String(50), nullable=False, comment='偏好类别: VALUATION_MODEL/REPORT_STYLE/DATA_SOURCE/RISK_TOLERANCE')
    preference_key = Column(String(100), nullable=False, comment='偏好键')
    preference_value = Column(Text, comment='偏好值')
    priority = Column(Integer, default=5, comment='优先级 1-10')
    is_active = Column(Boolean, default=True, comment='是否激活')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class RecruitmentSuggestionLog(Base):
    """人才市场招聘建议日志表"""
    __tablename__ = 'recruitment_suggestion_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(36), nullable=False, comment='团队ID')
    trigger_condition = Column(String(50), nullable=False, comment='触发条件: HIGH_LOAD/LOW_QUALITY/SKILL_GAP/NEW_PROJECT')
    suggested_agent_type = Column(String(50), comment='建议智能体类型')
    suggested_skill_tier = Column(String(20), comment='建议技能等级')
    urgency_level = Column(String(20), default='NORMAL', comment='紧急程度: LOW/NORMAL/HIGH/URGENT')
    suggestion_detail_json = Column(JSON, comment='建议详情JSON')
    is_accepted = Column(Boolean, nullable=True, comment='是否被采纳')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class SkillSuggestionLog(Base):
    """技能缺口检测日志表"""
    __tablename__ = 'skill_suggestion_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(36), nullable=False, comment='团队ID')
    detected_gap_type = Column(String(50), nullable=False, comment='检测到的缺口类型')
    missing_skills_json = Column(JSON, comment='缺失技能列表JSON')
    recommended_skills_json = Column(JSON, comment='推荐技能列表JSON')
    confidence_score = Column(Float, default=0.0, comment='置信度 0-1')
    resolved = Column(Boolean, default=False, comment='是否已解决')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class PostRecruitmentRecord(Base):
    """招聘后团队添加记录表"""
    __tablename__ = 'post_recruitment_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    recruitment_suggestion_id = Column(Integer, ForeignKey('recruitment_suggestion_logs.id'), comment='关联的建议日志ID')
    team_id = Column(String(36), nullable=False, comment='团队ID')
    new_agent_id = Column(String(36), comment='新加入智能体ID')
    new_agent_name = Column(String(100), comment='新智能体名称')
    assigned_role = Column(String(50), comment='分配角色')
    onboarding_status = Column(String(20), default='PENDING', comment='入职状态: PENDING/ACTIVE/TRAINING')
    synergy_preview_json = Column(JSON, comment='协同效果预览JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ScheduledTaskProposalRecord(Base):
    """自主工作排期提案记录表"""
    __tablename__ = 'scheduled_task_proposal_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    proposal_type = Column(String(20), nullable=False, comment='提案类型: DAILY/WEEKLY/MONTHLY')
    proposed_tasks_json = Column(JSON, nullable=False, comment='提议的任务列表JSON')
    estimated_duration_min = Column(Integer, default=0, comment='预计总时长分钟')
    resource_requirement_json = Column(JSON, comment='资源需求JSON')
    status = Column(String(20), default='PROPOSED', comment='状态: PROPOSED/APPROVED/REJECTED/EXECUTING/DONE')
    approved_by = Column(String(36), comment='审批人ID')
    executed_at = Column(DateTime, comment='执行时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AutonomousResultMemoryRecord(Base):
    """自主工作结果存储记录表"""
    __tablename__ = 'autonomous_result_memory_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scheduled_proposal_id = Column(Integer, ForeignKey('scheduled_task_proposal_records.id'), comment='关联排期提案ID')
    task_type = Column(String(50), comment='任务类型')
    result_summary = Column(Text, comment='结果摘要')
    result_data_json = Column(JSON, comment='结果数据JSON')
    quality_score = Column(Float, default=0.0, comment='质量评分 0-100')
    memory_tag = Column(String(100), comment='记忆标签')
    retention_days = Column(Integer, default=30, comment='保留天数')
    expires_at = Column(DateTime, comment='过期时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class FeedbackSignalRecord(Base):
    """进化反馈信号记录表"""
    __tablename__ = 'feedback_signal_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='任务ID')
    signal_type = Column(String(30), nullable=False, comment='信号类型: REWARD/PENALTY/EXPLORATION/REGULARIZATION')
    signal_value = Column(Float, default=0.0, comment='信号值')
    signal_dimension = Column(String(50), comment='信号维度: ACCURACY/SPEED/COST/ROBUSTNESS')
    metadata_json = Column(JSON, comment='元数据JSON')
    exported_to_training = Column(Boolean, default=False, comment='是否已导出到训练集')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class FailureCaseTrainingPool(Base):
    """失败案例训练池表"""
    __tablename__ = 'failure_case_training_pools'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='原始任务ID')
    failure_category = Column(String(50), nullable=False, comment='失败类别: TIMEOUT/ERROR/QUALITY/SECURITY')
    failure_description = Column(Text, comment='失败描述')
    input_snapshot_json = Column(JSON, comment='输入快照JSON')
    expected_output_json = Column(JSON, comment='期望输出JSON')
    actual_output_json = Column(JSON, comment='实际输出JSON')
    root_cause_analysis = Column(Text, comment='根因分析')
    difficulty_level = Column(String(20), default='MEDIUM', comment='难度: EASY/MEDIUM/HARD/EXPERT')
    used_in_drill = Column(Boolean, default=False, comment='是否已用于攻防演练')
    drill_session_id = Column(Integer, ForeignKey('security_drill_sessions.id'), comment='攻防演练会话ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AgentTopologySnapshot(Base):
    """生态拓扑快照表"""
    __tablename__ = 'agent_topology_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow, comment='快照时间')
    node_count = Column(Integer, default=0, comment='节点数量')
    edge_count = Column(Integer, default=0, comment='边数量')
    topology_data_json = Column(JSON, comment='拓扑数据JSON(ReactFlow格式)')
    layout_algorithm = Column(String(30), default='DAGRE', comment='布局算法: DAGRE/KOLA/FORCE/CIRCULAR')
    version_tag = Column(String(20), comment='版本标签')

class AgentHealthSnapshot(Base):
    """智能体健康指标快照表"""
    __tablename__ = 'agent_health_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, default=datetime.utcnow, comment='快照时间')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    health_metrics_json = Column(JSON, nullable=False, comment='健康指标JSON')
    cpu_usage = Column(Float, default=0.0, comment='CPU使用率')
    memory_usage_mb = Column(Float, default=0.0, comment='内存使用MB')
    request_rate_per_min = Column(Float, default=0.0, comment='每分钟请求率')
    error_rate = Column(Float, default=0.0, comment='错误率')
    overall_status = Column(String(20), default='HEALTHY', comment='整体状态: HEALTHY/DEGRADED/UNHEALTHY/DOWN')

class FiveEndEduSyncRecord(Base):
    """五端协同-教育端同步记录表"""
    __tablename__ = 'five_end_edu_sync_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), comment='关联任务ID')
    sync_direction = Column(String(10), default='PUSH', comment='同步方向: PUSH/PULL')
    data_type = Column(String(50), comment='数据类型: CASE_STUDY/EXAM_QUESTION/TEACHING_MATERIAL')
    anonymized = Column(Boolean, default=True, comment='是否脱敏')
    edu_institution = Column(String(100), comment='教育机构')
    sync_status = Column(String(20), default='PENDING', comment='状态: PENDING/SYNCED/FAILED')
    synced_at = Column(DateTime, comment='同步时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class FiveEndEnterpriseSubRecord(Base):
    """五端协同-企业订阅记录表"""
    __tablename__ = 'five_end_enterprise_sub_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(String(36), nullable=False, comment='企业ID')
    enterprise_name = Column(String(200), comment='企业名称')
    sub_type = Column(String(30), nullable=False, comment='订阅类型: BASIC/PROFESSIONAL/ENTERPRISE/CUSTOM')
    sub_features_json = Column(JSON, comment='订阅功能列表JSON')
    monthly_price = Column(Float, default=0.0, comment='月费')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE/SUSPENDED/EXPIRED/CANCELLED')
    api_quota_monthly = Column(Integer, default=0, comment='月API配额')
    used_quota_this_month = Column(Integer, default=0, comment='本月已用配额')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class FiveEndGovHeatmapRecord(Base):
    """五端协同-政府端热力图推送记录表"""
    __tablename__ = 'five_end_gov_heatmap_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_code = Column(String(20), nullable=False, comment='区域编码')
    region_name = Column(String(100), comment='区域名称')
    heatmap_type = Column(String(30), nullable=False, comment='热力图类型: PRICE/TURNOVER/INVENTORY/FORECAST')
    data_period = Column(String(20), comment='数据周期: MONTHLY/QUARTERLY/YEARLY')
    heatmap_data_json = Column(JSON, nullable=False, comment='热力图数据JSON')
    push_channel = Column(String(30), default='API', comment='推送渠道: API/EMAIL/DASHBOARD')
    push_status = Column(String(20), default='PENDING', comment='推送状态: PENDING/SENT/FAILED')
    received_by = Column(String(100), comment='接收方')
    sent_at = Column(DateTime, comment='发送时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class FiveEndAssociationPaperRecord(Base):
    """五端协同-协会端白皮书生成记录表"""
    __tablename__ = 'five_end_association_paper_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_title = Column(String(300), nullable=False, comment='白皮书标题')
    association_name = Column(String(200), comment='协会名称')
    paper_type = Column(String(50), comment='类型: ANNUAL_REPORT/INDUSTRY_ANALYSIS/TREND_FORECAST')
    data_sources_json = Column(JSON, comment='数据来源JSON')
    generation_status = Column(String(20), default='DRAFT', comment='状态: DRAFT/GENERATING/REVIEWING/PUBLISHED')
    file_path = Column(Text, comment='文件路径')
    page_count = Column(Integer, default=0, comment='页数')
    published_at = Column(DateTime, comment='发布时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class TrainingSampleExportRecord(Base):
    """学习系统训练样本导出记录表"""
    __tablename__ = 'training_sample_export_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    export_batch_id = Column(String(36), unique=True, nullable=False, comment='导出批次ID')
    sample_type = Column(String(20), nullable=False, comment='样本类型: POSITIVE/NEGATIVE')
    source_task_ids_json = Column(JSON, comment='来源任务ID列表JSON')
    total_samples = Column(Integer, default=0, comment='总样本数')
    export_format = Column(String(20), default='JSONL', comment='导出格式: JSONL/CSV/TFRECORD')
    file_path = Column(Text, comment='导出文件路径')
    file_size_kb = Column(Integer, default=0, comment='文件大小KB')
    model_version_target = Column(String(50), comment='目标模型版本')
    export_status = Column(String(20), default='PENDING', comment='状态: PENDING/EXPORTING/DONE/FAILED')
    quality_score_avg = Column(Float, default=0.0, comment='平均质量分')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class SecurityThreatAssessmentLog(Base):
    """安全威胁评估日志表"""
    __tablename__ = 'security_threat_assessment_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='任务ID')
    threat_level = Column(String(20), nullable=False, comment='威胁等级: SAFE/SUSPICIOUS/DANGEROUS/CRITICAL')
    threat_category = Column(String(50), comment='威胁类别: DATA_LEAK/PROMPT_INJECTION/JAILBREAK/DDOS')
    risk_score = Column(Float, default=0.0, comment='风险评分 0-100')
    indicators_json = Column(JSON, comment='威胁指标JSON')
    mitigation_actions_json = Column(JSON, comment='建议缓解措施JSON')
    assessor = Column(String(100), comment='评估者(系统/人工)')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class InterceptionAuditLog(Base):
    """安全拦截审计日志表"""
    __tablename__ = 'interception_audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, comment='任务ID')
    intercept_rule_id = Column(String(50), comment='拦截规则ID')
    intercept_type = Column(String(30), nullable=False, comment='拦截类型: KEYWORD_FILTER/PATTERN_MATCH/RATE_LIMIT/IP_BLOCK')
    intercepted_content_hash = Column(String(64), comment='拦截内容哈希')
    original_content_preview = Column(Text, comment='原始内容预览(前200字符)')
    action_taken = Column(String(20), default='BLOCKED', comment='处理动作: BLOCKED/MODIFIED/QUARANTINE/ALLOWED_WITH_LOG')
    severity = Column(String(20), default='MEDIUM', comment='严重程度: LOW/MEDIUM/HIGH/CRITICAL')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class SecurityDrillSessionRecord(Base):
    """安全攻防演练会话记录表"""
    __tablename__ = 'security_drill_session_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    drill_session_id = Column(String(36), unique=True, nullable=False, comment='演练会话ID')
    drill_type = Column(String(30), nullable=False, comment='演练类型: RED_TEAM/BLUE_TEAM/PURPLE_TEAM')
    target_system = Column(String(50), comment='目标系统')
    scenario_description = Column(Text, comment='场景描述')
    attack_vectors_json = Column(JSON, comment='攻击向量JSON')
    defense_measures_json = Column(JSON, comment='防御措施JSON')
    drill_status = Column(String(20), default='PLANNING', comment='状态: PLANNING/EXECUTING/COMPLETED/ABORTED')
    result_summary = Column(Text, comment='结果摘要')
    lessons_learned = Column(Text, comment='经验教训')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class CrossModuleEventLog(Base):
    """跨模块编排事件总线日志表"""
    __tablename__ = 'cross_module_event_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    event_type = Column(String(50), nullable=False, comment='事件类型: TASK_CREATED/TASK_COMPLETED/TASK_FAILED/AGENT_HIRED/TEAM_FORMED/REPORT_GENERATED/MEMORY_UPDATED/MARKET_CHANGE/EVOLUTION_TRIGGER/SECURITY_ALERT/FIVE_END_SYNC')
    source_module = Column(String(50), comment='来源模块')
    payload_json = Column(JSON, comment='事件载荷JSON')
    subscriber_modules_json = Column(JSON, comment='订阅模块列表JSON')
    processing_result = Column(String(20), default='SUCCESS', comment='处理结果: SUCCESS/PARTIAL_FAIL/FAIL')
    synergy_score_delta = Column(Float, default=0.0, comment='协同分数变化值')
    event_latency_ms = Column(Integer, default=0, comment='事件处理延迟毫秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cm_event_type_time', 'event_type', 'created_at'),
        Index('idx_cm_source_module', 'source_module'),
    )

# =============================================================================
# 第三十九部分：智能咨询与其他模块联动 (smart_consultation_cross_module_layer.py)
# =============================================================================

class ChatActionPanelLog(Base):
    """智能咨询操作面板日志表"""
    __tablename__ = 'chat_action_panel_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='咨询会话ID')
    user_id = Column(String(36), comment='用户ID')
    context_type = Column(String(50), comment='上下文类型: property_analysis/fortune/emotional/general')
    actions_shown_json = Column(JSON, comment='展示的操作列表JSON')
    action_clicked = Column(String(50), comment='点击的操作类型')
    target_url = Column(Text, comment='跳转目标URL')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ConsultationTaskRecord(Base):
    """咨询-任务桥接记录表"""
    __tablename__ = 'consultation_task_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='咨询会话ID')
    task_id = Column(String(36), nullable=False, comment='关联任务ID')
    original_query = Column(Text, comment='原始咨询问题')
    agent_type = Column(String(50), comment='调用智能体类型')
    task_status = Column(String(20), default='PENDING', comment='任务状态')
    completion_pushed = Column(Boolean, default=False, comment='是否已推送完成通知')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_consult_task_session', 'session_id', 'task_id'),
    )

class ChatTaskSyncLog(Base):
    """聊天-任务中心同步日志表"""
    __tablename__ = 'chat_task_sync_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    task_id = Column(String(36), comment='任务ID')
    source = Column(String(10), default='chat', comment='来源: chat/analysis')
    sync_direction = Column(String(10), default='push', comment='同步方向: push/pull')
    sync_status = Column(String(20), default='SUCCESS', comment='状态: SUCCESS/FAILED')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ReconsultSessionLog(Base):
    """重新咨询会话记录表"""
    __tablename__ = 'reconsult_session_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_task_id = Column(String(36), nullable=False, comment='原任务ID')
    reconsult_session_id = Column(String(36), comment='新咨询会话ID')
    original_question = Column(Text, comment='原始问题')
    prefill_success = Column(Boolean, default=False, comment='预填是否成功')
    history_context_loaded = Column(Boolean, default=False, comment='历史上下文是否加载')
    user_id = Column(String(36), comment='用户ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AgentActiveSessionLog(Base):
    """智能体活跃会话日志表"""
    __tablename__ = 'agent_active_session_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    session_id = Column(String(36), nullable=False, comment='活跃会话ID')
    user_id = Column(String(36), comment='用户ID')
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE/IDLE/ENDED')
    started_at = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    ended_at = Column(DateTime, comment='结束时间')
    message_count = Column(Integer, default=0, comment='消息数量')

    __table_args__ = (
        Index('idx_agent_active_agent_status', 'agent_id', 'status'),
    )

class OverloadSuggestionLog(Base):
    """负载过高建议日志表"""
    __tablename__ = 'overload_suggestion_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    agent_type = Column(String(50), comment='智能体类型')
    current_load = Column(Integer, default=0, comment='当前负载')
    threshold = Column(Integer, default=5, comment='阈值')
    suggested_action = Column(String(20), default='recruit', comment='建议动作: recruit/wait/switch')
    suggestion_message = Column(Text, comment='建议消息内容')
    recruitment_link = Column(Text, comment='招募链接')
    user_accepted = Column(Boolean, nullable=True, comment='用户是否采纳')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ChatPropertyExtractionLog(Base):
    """聊天房源提取日志表"""
    __tablename__ = 'chat_property_extraction_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    chat_text_snippet = Column(Text, comment='聊天文本片段')
    extracted_entities_json = Column(JSON, comment='提取的实体JSON')
    enriched_count = Column(Integer, default=0, comment=' enrichment后数量')
    selected_for_compare = Column(JSON, comment='选中对比的房源ID列表JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ChatCompareReportRecord(Base):
    """聊天对比报告记录表"""
    __tablename__ = 'chat_compare_report_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    session_id = Column(String(36), nullable=False, comment='触发会话ID')
    selected_property_ids_json = Column(JSON, comment='选中的房源ID列表JSON')
    report_status = Column(String(20), default='GENERATING', comment='状态: GENERATING/DONE/FAILED')
    preview_pushed = Column(Boolean, default=False, comment='预览是否已推送')
    file_path = Column(Text, comment='文件路径')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ChatReportAutoSaveLog(Base):
    """聊天报告自动保存日志表"""
    __tablename__ = 'chat_report_auto_save_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), nullable=False, comment='报告ID')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    message_id = Column(String(36), comment='触发消息ID')
    report_title = Column(String(200), comment='报告标题')
    report_type = Column(String(50), comment='报告类型')
    save_trigger = Column(String(30), default='CONSULTATION_COMPLETE', comment='保存触发')
    backlink_available = Column(Boolean, default=True, comment='反向链接可用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_chat_report_session', 'session_id'),
    )

class ChatPreferenceMemoryLog(Base):
    """聊天偏好记忆写入日志表"""
    __tablename__ = 'chat_preference_memory_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    preference_key = Column(String(100), nullable=False, comment='偏好键')
    preference_value = Column(Text, comment='偏好值')
    category = Column(String(50), comment='偏好类别: style/district/price_sensitivity/topic_focus')
    importance_score = Column(Float, default=5.0, comment='重要度 1-10')
    mention_count = Column(Integer, default=1, comment='提及次数')
    memory_id = Column(String(36), comment='写入的记忆ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ChatMemoryRecallLog(Base):
    """聊天记忆召回日志表"""
    __tablename__ = 'chat_memory_recall_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    query_text = Column(Text, comment='查询文本')
    recalled_memory_ids_json = Column(JSON, comment='召回的记忆ID列表JSON')
    recall_count = Column(Integer, default=0, comment='召回数量')
    used_in_response = Column(Boolean, default=False, comment='是否用于回复')
    recall_latency_ms = Column(Integer, default=0, comment='召回延迟毫秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class CapabilityGapDetectionLog(Base):
    """能力缺口检测日志表"""
    __tablename__ = 'capability_gap_detection_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    query_text = Column(Text, comment='查询文本')
    can_handle = Column(Boolean, comment='当前能力是否可处理')
    gap_type = Column(String(50), comment='缺口类型')
    detected_at = Column(DateTime, default=datetime.utcnow, comment='检测时间')

class RecruitmentRecommendationLog(Base):
    """招聘建议日志表（咨询触发）"""
    __tablename__ = 'recruitment_recommendation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String(36), unique=True, nullable=False, comment='建议ID')
    session_id = Column(String(36), comment='触发会话ID')
    gap_type = Column(String(50), comment='缺口类型')
    suggested_agents_json = Column(JSON, comment='建议智能体列表JSON')
    talent_market_link = Column(Text, comment='人才市场链接')
    priority = Column(String(20), default='medium', comment='优先级')
    user_clicked = Column(Boolean, default=False, comment='用户是否点击')
    converted_to_recruitment = Column(Boolean, default=False, comment='是否转化为实际招募')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class SkillPurchaseRecommendationLog(Base):
    """技能购买建议日志表（咨询触发）"""
    __tablename__ = 'skill_purchase_recommendation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='触发会话ID')
    missing_skills_json = Column(JSON, comment='缺失技能列表JSON')
    store_links_json = Column(JSON, comment='商店链接列表JSON')
    user_purchased = Column(Boolean, default=False, comment='用户是否购买')
    purchased_skill_ids_json = Column(JSON, comment='购买的技能ID列表JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class PostPurchaseAutoEquipLog(Base):
    """购买后自动装备日志表"""
    __tablename__ = 'post_purchase_auto_equip_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    equip_type = Column(String(20), nullable=False, comment='装备类型: agent/skill')
    equipped_id = Column(String(36), comment='装备的agent/skill ID')
    equipped_name = Column(String(100), comment='名称')
    user_id = Column(String(36), comment='用户ID')
    notification_sent = Column(Boolean, default=False, comment='是否发送通知')
    capability_active = Column(Boolean, default=False, comment='能力是否激活')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class PeriodicSubscriptionProposalLog(Base):
    """定期订阅提案日志表"""
    __tablename__ = 'periodic_subscription_proposal_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String(36), unique=True, nullable=False, comment='提案ID')
    session_id = Column(String(36), comment='触发会话ID')
    topic = Column(String(100), comment='话题')
    suggested_frequency = Column(String(20), comment='建议频率: DAILY/WEEKLY/MONTHLY')
    detected_keywords = Column(String(200), comment='检测到的关键词')
    user_confirmed = Column(Boolean, default=False, comment='用户是否确认')
    subscription_id = Column(String(36), comment='创建的订阅ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AutonomousResultPushLog(Base):
    """自主工作结果推送日志表"""
    __tablename__ = 'autonomous_result_push_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), comment='自主任务ID')
    target_session_id = Column(String(36), nullable=False, comment='目标会话ID')
    result_summary = Column(Text, comment='结果摘要')
    result_type = Column(String(50), comment='结果类型: market_report/price_alert/analysis_update')
    report_link = Column(Text, comment='报告链接')
    push_status = Column(String(20), default='PENDING', comment='状态: PSENT/DELIVERED/FAILED')
    user_opened = Column(Boolean, default=False, comment='用户是否打开')
    pushed_at = Column(DateTime, comment='推送时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ConsultationFeedbackSignalLog(Base):
    """咨询反馈信号日志表"""
    __tablename__ = 'consultation_feedback_signal_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(36), unique=True, nullable=False, comment='反馈ID')
    message_id = Column(String(36), nullable=False, comment='消息ID')
    session_id = Column(String(36), comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    feedback_type = Column(String(10), nullable=False, comment='反馈类型: like/dislike')
    rating = Column(Integer, comment='评分 1-5')
    collected_at = Column(DateTime, default=datetime.utcnow, comment='收集时间')
    used_in_training = Column(Boolean, default=False, comment='是否用于训练')

class FailedConversationCaseLog(Base):
    """失败对话案例日志表"""
    __tablename__ = 'failed_conversation_case_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(36), unique=True, nullable=False, comment='案例ID')
    session_id = Column(String(36), nullable=False, comment='会话ID')
    failure_signals_json = Column(JSON, comment='失败信号JSON(轮数/中断/追问)')
    anonymized_summary = Column(Text, comment='脱敏摘要')
    submitted_to_training_pool = Column(Boolean, default=False, comment='是否提交训练池')
    used_in_drill = Column(Boolean, default=False, comment='是否用于攻防演练')
    failure_category = Column(String(50), comment='失败类别: abandonment/repetition/dissatisfaction/error')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class SessionTopologySnapshotLog(Base):
    """会话拓扑快照日志表"""
    __tablename__ = 'session_topology_snapshot_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, comment='会话ID')
    topology_data_json = Column(JSON, nullable=False, comment='拓扑数据JSON')
    node_count = Column(Integer, default=0, comment='节点数')
    edge_count = Column(Integer, default=0, comment='边数')
    snapshot_time = Column(DateTime, default=datetime.utcnow, comment='快照时间')

class FailoverEventLog(Base):
    """故障切换事件日志表"""
    __tablename__ = 'failover_event_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), comment='会话ID')
    original_agent_id = Column(String(36), nullable=False, comment='原智能体ID')
    backup_agent_id = Column(String(36), comment='备用智能体ID')
    failure_reason = Column(String(100), comment='故障原因')
    switch_success = Column(Boolean, default=False, comment='切换是否成功')
    switch_latency_ms = Column(Integer, default=0, comment='切换耗时毫秒')
    user_notified = Column(Boolean, default=False, comment='是否通知用户')
    recovery_message_sent = Column(Boolean, default=False, comment='恢复消息是否发送')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class EduConsultationViewLog(Base):
    """教育端查看咨询日志表"""
    __tablename__ = 'edu_consultation_view_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(String(36), nullable=False, comment='教师ID')
    student_id = Column(String(36), comment='学生ID(脱敏前)')
    session_id = Column(String(36), comment='查看的会话ID')
    view_anonymized = Column(Boolean, default=True, comment='是否脱敏查看')
    view_duration_sec = Column(Integer, default=0, comment='查看时长秒')
    viewed_at = Column(DateTime, default=datetime.utcnow, comment='查看时间')

class EnterpriseHotTopicReportLog(Base):
    """企业端热点报告日志表"""
    __tablename__ = 'enterprise_hot_topic_report_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    period = Column(String(20), comment='周期: weekly/monthly')
    topic_count = Column(Integer, default=0, comment='话题数量')
    trend_data_json = Column(JSON, comment='趋势数据JSON')
    subscriber_enterprise_ids_json = Column(JSON, comment='订阅企业ID列表JSON')
    push_status = Column(String(20), default='PENDING', comment='推送状态')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')

class GovPublicOpinionAlertLog(Base):
    """政府端舆情预警日志表"""
    __tablename__ = 'gov_public_opinion_alert_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(36), unique=True, nullable=False, comment='预警ID')
    sensitive_topic = Column(String(100), nullable=False, comment='敏感话题')
    keyword_matches_json = Column(JSON, comment='匹配的关键词JSON')
    occurrence_frequency = Column(Integer, default=0, comment='出现频率')
    threshold = Column(Integer, default=10, comment='阈值')
    time_window_minutes = Column(Integer, default=60, comment='时间窗口分钟')
    sample_queries_json = Column(JSON, comment='典型查询样例JSON')
    sent_to_gov = Column(Boolean, default=False, comment='是否已发送政府端')
    alert_level = Column(String(20), default='MEDIUM', comment='预警级别: LOW/MEDIUM/HIGH/CRITICAL')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AssociationTrendReportLog(Base):
    """协会端趋势报告日志表"""
    __tablename__ = 'association_trend_report_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    quarter = Column(String(10), nullable=False, comment='季度: 2026Q1')
    charts_count = Column(Integer, default=0, comment='图表数量')
    cases_count = Column(Integer, default=0, comment='典型案例数量')
    total_consultations_analyzed = Column(Integer, default=0, comment='分析的总咨询量')
    top_topics_json = Column(JSON, comment='热门话题TOP10 JSON')
    published_to_association = Column(Boolean, default=False, comment='是否发布到协会端')
    download_count = Column(Integer, default=0, comment='下载次数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ChatTrainingDataExportLog(Base):
    """聊天训练数据导出日志表"""
    __tablename__ = 'chat_training_data_export_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    export_batch_id = Column(String(36), unique=True, nullable=False, comment='导出批次ID')
    min_rating = Column(Float, default=4.0, comment='最低评分筛选')
    exported_conversation_count = Column(Integer, default=0, comment='导出的对话数量')
    formatted_data_path = Column(Text, comment='格式化数据路径')
    target_model_version = Column(String(50), comment='目标模型版本')
    export_status = Column(String(20), default='PENDING', comment='状态: PENDING/EXPORTING/DONE')
    quality_avg_score = Column(Float, default=0.0, comment='平均质量分')
    triggered_model_update = Column(Boolean, default=False, comment='是否触发了模型更新')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class NegativeSampleCollectionLog(Base):
    """负样本收集日志表"""
    __tablename__ = 'negative_sample_collection_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(String(36), unique=True, nullable=False, comment='收集批次ID')
    session_id = Column(String(36), comment='源会话ID')
    failure_signals_json = Column(JSON, comment='失败信号JSON')
    negative_reward_weight = Column(Float, default=-1.0, comment='负奖励权重')
    exported_for_rl = Column(Boolean, default=False, comment='是否导出用于RL')
    rl_training_batch = Column(String(36), comment='RL训练批次ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class MaliciousChatInterceptionLog(Base):
    """恶意聊天拦截日志表"""
    __tablename__ = 'malicious_chat_interception_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    interception_id = Column(String(36), unique=True, nullable=False, comment='拦截ID')
    request_id = Column(String(36), comment='请求ID')
    session_id = Column(String(36), comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    interception_reason = Column(String(50), nullable=False, comment='拦截原因: sql_injection/prompt_injection/frequency_abuse/profanity')
    threat_level = Column(String(20), comment='威胁等级')
    content_preview = Column(Text, comment='内容预览')
    blocked = Column(Boolean, default=True, comment='是否拦截')
    audit_logged = Column(Boolean, default=False, comment='审计日志是否记录')
    ip_address = Column(String(45), comment='IP地址')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ConsultationDrillTriggerLog(Base):
    """咨询攻防演练触发日志表"""
    __tablename__ = 'consultation_drill_trigger_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    drill_session_id = Column(String(36), unique=True, nullable=False, comment='演练会话ID')
    failure_pattern = Column(String(50), comment='失败模式')
    window_minutes = Column(Integer, default=60, comment='监控窗口分钟')
    failure_rate = Column(Float, default=0.0, comment='失败率')
    threshold_exceeded = Column(Boolean, default=False, comment='是否超阈值')
    drill_type = Column(String(30), default='RED_TEAM', comment='演练类型: RED_TEAM/BLUE_TEAM/PURPLE_TEAM')
    drill_status = Column(String(20), default='TRIGGERED', comment='状态: TRIGGERED/RUNNING/COMPLETED/CANCELLED')
    vulnerabilities_found = Column(Integer, default=0, comment='发现的漏洞数')
    report_generated = Column(Boolean, default=False, comment='报告是否生成')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    completed_at = Column(DateTime, comment='完成时间')

class ConsultationEventBusLog(Base):
    """咨询跨模块事件总线日志表"""
    __tablename__ = 'consultation_event_bus_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    event_type = Column(String(50), nullable=False, comment='事件类型: CONSULTATION_STARTED/MESSAGE_SENT/TASK_CREATED_FROM_CHAT/AGENT_CALLED/REPORT_GENERATED/FEEDBACK_RECEIVED/MEMORY_UPDATED/RECRUITATION_SUGGESTED/SKILL_SUGGESTED/SUBSCRIPTION_CREATED/AUTONOMOUS_RESULT_PUSHED/FAILURE_DETECTED/SECURITY_ALERT/FIVE_END_DATA_SYNCED')
    source_session_id = Column(String(36), comment='源会话ID')
    publisher = Column(String(50), comment='发布者')
    payload_json = Column(JSON, comment='事件载荷JSON')
    subscriber_modules_json = Column(JSON, comment='订阅模块列表JSON')
    subscribers_notified = Column(Integer, default=0, comment='通知的订阅者数')
    synergy_score = Column(Float, default=0.0, comment='协同分数')
    processing_latency_ms = Column(Integer, default=0, comment='处理延迟毫秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_consult_evt_type_time', 'event_type', 'created_at'),
        Index('idx_consult_evt_session', 'source_session_id'),
    )


# =============================================================================
# 第四十部分：双轨制成长用户体系 (dual_track_growth_system_layer.py)
# =============================================================================

class UserGrowthProfile(Base):
    """用户使用成长值档案表"""
    __tablename__ = 'user_growth_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, comment='用户ID')
    total_growth_points = Column(Integer, default=0, comment='总成长值')
    current_level = Column(Integer, default=1, comment='当前等级 1-8')
    level_name = Column(String(50), default='见习居士', comment='等级名称')
    progress_to_next = Column(Float, default=0.0, comment='下一级进度百分比 0-100')
    next_level_required = Column(Integer, default=200, comment='下一级所需成长值')
    total_actions_count = Column(Integer, default=0, comment='总行为次数')
    active_privileges_json = Column(JSON, comment='当前激活的特权列表JSON')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class GrowthTransaction(Base):
    """成长值变动流水表"""
    __tablename__ = 'growth_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(36), unique=True, nullable=False, comment='交易ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    action_type = Column(String(50), nullable=False, comment='动作类型: smart_consultation/property_report/skill_purchase/agent_recruitment/bond_activation/scheduled_task/pdf_export/property_compare/daily_checkin/feedback_rating/fortune_report')
    points_earned = Column(Integer, nullable=False, comment='获得成长值')
    daily_limit = Column(Integer, default=0, comment='该动作每日上限')
    daily_used_before = Column(Integer, default=0, comment='当日已使用次数')
    metadata_json = Column(JSON, comment='附加元数据JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_growth_tx_user_time', 'user_id', 'created_at'),
        Index('idx_growth_tx_action', 'action_type'),
    )

class UserContributionProfile(Base):
    """用户贡献者档案表"""
    __tablename__ = 'user_contribution_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, comment='用户ID')
    total_contribution_points = Column(Integer, default=0, comment='总贡献值')
    current_contributor_level = Column(Integer, default=1, comment='贡献者等级 C1-C8')
    contributor_level_name = Column(String(50), default='初耕者', comment='贡献等级名称')
    progress_to_next_level = Column(Float, default=0.0, comment='下一级进度')
    next_level_required = Column(Integer, default=100, comment='下一级所需贡献值')
    revenue_share_percentage = Column(Float, default=50.0, comment='收益分成比例%')
    total_earnings_points = Column(Integer, default=0, comment='总收益积分')
    upload_count = Column(Integer, default=0, comment='上传内容数')
    approved_upload_count = Column(Integer, default=0, comment='审核通过数')
    total_sales_count = Column(Integer, default=0, comment='总被购买/引用次数')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class ContributionTransaction(Base):
    """贡献值变动流水表"""
    __tablename__ = 'contribution_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(36), unique=True, nullable=False, comment='交易ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    action_type = Column(String(50), nullable=False, comment='动作类型: upload_skill/skill_purchased/upload_agent_template/publish_article/upload_case_report/co_development/official_recommendation/content_favorited')
    points_earned = Column(Integer, nullable=False, comment='获得贡献值')
    related_content_id = Column(String(36), comment='关联内容ID')
    related_buyer_id = Column(String(36), comment='购买者用户ID')
    metadata_json = Column(JSON, comment='附加元数据JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_contrib_tx_user_time', 'user_id', 'created_at'),
    )

class UserUploadedContent(Base):
    """用户上传内容表（技能/文章/案例）"""
    __tablename__ = 'user_uploaded_contents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(String(36), unique=True, nullable=False, comment='上传记录ID')
    user_id = Column(String(36), nullable=False, comment='上传者用户ID')
    content_type = Column(String(20), nullable=False, comment='内容类型: skill/article/case_report/agent_template')
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, comment='描述')
    content_text = Column(Text, comment='正文或详细描述')
    price_points = Column(Integer, default=0, comment='售价(积分)')
    tags_json = Column(JSON, comment='标签列表JSON')
    status = Column(String(20), default='PENDING', comment='状态: PENDING/APPROVED/REJECTED/WITHDRAWN')
    reject_reason = Column(Text, comment='拒绝原因')
    reviewer_id = Column(String(36), comment='审核人ID')
    reviewed_at = Column(DateTime, comment='审核时间')
    sales_count = Column(Integer, default=0, comment='销售/使用次数')
    view_count = Column(Integer, default=0, comment='查看次数')
    favorite_count = Column(Integer, default=0, comment='收藏次数')
    citation_count = Column(Integer, default=0, comment='引用次数')
    total_revenue_points = Column(Integer, default=0, comment='总收益积分')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_upload_user_status', 'user_id', 'status'),
        Index('idx_upload_type_status', 'content_type', 'status'),
    )

class ContentReviewQueue(Base):
    """内容审核队列表"""
    __tablename__ = 'content_review_queues'
    id = Column(Integer, primary_key=True, autoincrement=True)
    queue_id = Column(String(36), unique=True, nullable=False, comment='队列项ID')
    upload_id = Column(String(36), nullable=False, comment='关联上传内容ID')
    submitter_user_id = Column(String(36), nullable=False, comment='提交者ID')
    submitter_usage_level = Column(Integer, default=1, comment='提交者使用等级(影响优先级)')
    submitter_contributor_level = Column(Integer, default=1, comment='提交者贡献等级(影响优先级)')
    priority_score = Column(Float, default=0.0, comment='综合优先级分数')
    queue_status = Column(String(20), default='PENDING', comment='状态: PENDING/REVIEWING/APPROVED/REJECTED')
    assigned_reviewer_id = Column(String(36), comment='分配的审核员')
    reviewed_at = Column(DateTime, comment='审核完成时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='入队时间')

    __table_args__ = (
        Index('idx_review_queue_priority', 'queue_status', 'priority_score'),
    )

class EarningRecord(Base):
    """收益记录表"""
    __tablename__ = 'earning_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    earning_id = Column(String(36), unique=True, nullable=False, comment='收益记录ID')
    earner_user_id = Column(String(36), nullable=False, comment='获益用户ID(创作者)')
    source_type = Column(String(30), nullable=False, comment='来源: skill_sale/template_sale/ad_revenue/citation/case_referral')
    source_content_id = Column(String(36), comment='来源内容ID')
    buyer_user_id = Column(String(36), comment='购买者/使用者ID')
    gross_amount = Column(Integer, nullable=False, comment='总金额(积分)')
    platform_share = Column(Integer, default=0, comment='平台分成')
    creator_share = Column(Integer, default=0, comment='创作者分成')
    share_rate_applied = Column(Float, comment='实际应用分成比例')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_earning_earner_time', 'earner_user_id', 'created_at'),
    )

class WithdrawalRequest(Base):
    """提现请求表"""
    __tablename__ = 'withdrawal_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    withdrawal_id = Column(String(36), unique=True, nullable=False, comment='提现ID')
    user_id = Column(String(36), nullable=False, comment='申请用户ID')
    amount = Column(Integer, nullable=False, comment='提现金额(积分)')
    method = Column(String(20), nullable=False, comment='提现方式: POINTS_TO_MEMBERSHIP/CASH/ALIPAY/WECHAT')
    account_info_json = Column(JSON, comment='账户信息JSON(脱敏存储)')
    status = Column(String(20), default='PENDING', comment='状态: PENDING/PROCESSING/COMPLETED/REJECTED/CANCELLED')
    requested_at = Column(DateTime, default=datetime.utcnow, comment='申请时间')
    processed_by = Column(String(36), comment='处理管理员ID')
    processed_at = Column(DateTime, comment='处理时间')
    rejection_reason = Column(Text, comment='拒绝原因')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_withdrawal_user_status', 'user_id', 'status'),
    )

class MallExchangeRecord(Base):
    """积分商城兑换记录表"""
    __tablename__ = 'mall_exchange_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange_id = Column(String(36), unique=True, nullable=False, comment='兑换记录ID')
    user_id = Column(String(36), nullable=False, comment='兑换用户ID')
    product_id = Column(String(36), nullable=False, comment='商品ID')
    product_name = Column(String(100), comment='商品名称')
    product_category = Column(String(30), comment='商品分类')
    points_cost = Column(Integer, nullable=False, comment='消耗积分')
    points_balance_before = Column(Integer, comment='兑换前余额')
    points_balance_after = Column(Integer, comment='兑换后余额')
    status = Column(String(20), default='COMPLETED', comment='状态: COMPLETED/CANCELLED/REFUNDED')
    delivered_privilege_json = Column(JSON, comment='发放的权益详情JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='兑换时间')

    __table_args__ = (
        Index('idx_mall_exchange_user_time', 'user_id', 'created_at'),
    )

class UsageLevelUpHistory(Base):
    """使用等级升级历史表"""
    __tablename__ = 'usage_level_up_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    from_level = Column(Integer, nullable=False, comment='原等级')
    to_level = Column(Integer, nullable=False, comment='新等级')
    from_level_name = Column(String(50), comment='原等级名称')
    to_level_name = Column(String(50), comment='新等级名称')
    total_growth_at_upgrade = Column(Integer, comment='升级时总成长值')
    new_privileges_unlocked_json = Column(JSON, comment='解锁的新特权JSON')
    celebration_sent = Column(Boolean, default=False, comment='是否已发送庆祝通知')
    created_at = Column(DateTime, default=datetime.utcnow, comment='升级时间')

class ContributorLevelUpHistory(Base):
    """贡献者等级升级历史表"""
    __tablename__ = 'contributor_level_up_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    from_level = Column(Integer, nullable=False, comment='原等级C1-C8')
    to_level = Column(Integer, nullable=False, comment='新等级')
    new_revenue_share_pct = Column(Float, comment='新收益分成比例')
    new_badge = Column(String(100), comment='新徽章')
    total_contribution_at_upgrade = Column(Integer, comment='升级时总贡献值')
    created_at = Column(DateTime, default=datetime.utcnow, comment='升级时间')

class LeaderboardSnapshot(Base):
    """排行榜快照表"""
    __tablename__ = 'leaderboard_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照ID')
    track_type = Column(String(20), nullable=False, comment='轨道类型: USAGE/CONTRIBUTION')
    period = Column(String(20), nullable=False, comment='周期: daily/weekly/monthly/quarterly/all_time')
    period_start = Column(Date, comment='周期开始日期')
    period_end = Column(Date, comment='周期结束日期')
    rankings_data_json = Column(JSON, nullable=False, comment='排名数据JSON(top N entries)')
    total_participants = Column(Integer, default=0, comment='参与总人数')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')

    __table_args__ = (
        Index('idx_lb_snapshot_track_period', 'track_type', 'period'),
    )

class GrowthNotificationRecord(Base):
    """成长系统通知记录表"""
    __tablename__ = 'growth_notification_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(String(36), unique=True, nullable=False, comment='通知ID')
    user_id = Column(String(36), nullable=False, comment='目标用户ID')
    notification_type = Column(String(30), nullable=False, comment='类型: LEVEL_UP/EARNING/MILESTONE/INCENTIVE_AWARD/WITHDRAWAL_STATUS')
    title = Column(String(200), comment='通知标题')
    message = Column(Text, comment='通知内容')
    metadata_json = Column(JSON, comment='附加数据JSON')
    is_read = Column(Boolean, default=False, comment='是否已读')
    read_at = Column(DateTime, comment='阅读时间')
    sent_via = Column(String(20), default='IN_APP', comment='发送渠道: IN_APP/PUSH/EMAIL/SMS')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_notif_user_read', 'user_id', 'is_read'),
    )

class DailyUsageLimitTracker(Base):
    """每日使用限制追踪表"""
    __tablename__ = 'daily_usage_limit_trackers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, comment='用户ID')
    action_type = Column(String(50), nullable=False, comment='动作类型')
    track_date = Column(Date, nullable=False, comment='追踪日期')
    used_count = Column(Integer, default=0, comment='当日已使用次数')
    limit_value = Column(Integer, nullable=False, comment='每日上限')
    reset_at = Column(DateTime, default=datetime.utcnow, comment='重置时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'action_type', 'track_date', name='uq_daily_limit'),
    )

class CreatorIncentiveAward(Base):
    """创作者激励奖励记录表"""
    __tablename__ = 'creator_incentive_awards'
    id = Column(Integer, primary_key=True, autoincrement=True)
    award_id = Column(String(36), unique=True, nullable=False, comment='奖励ID')
    user_id = Column(String(36), nullable=False, comment='获奖用户ID')
    quarter = Column(String(10), nullable=False, comment='季度: 2026Q1')
    award_type = Column(String(30), nullable=False, comment='奖励类型: FREE_VIP/POINTS_BONUS/BADGE_SPECIAL/HOMEPAGE_FEATURE')
    award_value = Column(Integer, nullable=False, comment='奖励值(VIP天数/积分数等)')
    selection_criteria_met_json = Column(JSON, comment='满足的筛选条件JSON')
    awarded_at = Column(DateTime, default=datetime.utcnow, comment='颁发时间')
    expires_at = Column(DateTime, comment='过期时间(如VIP有效期)')

class FairnessFlagRecord(Base):
    """反作弊标记记录表"""
    __tablename__ = 'fairness_flag_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    flag_id = Column(String(36), unique=True, nullable=False, comment='标记ID')
    user_id = Column(String(36), nullable=False, comment='被标记用户ID')
    flag_type = Column(String(30), nullable=False, comment='标记类型: ANOMALOUS_ACTIVITY/RATE_LIMIT_EXCEEDED/DUPLICATE_CONTENT/SUSPICIOUS_PATTERN')
    severity = Column(String(20), default='LOW', comment='严重程度: LOW/MEDIUM/HIGH/CRITICAL')
    detected_pattern_json = Column(JSON, comment='检测到的异常模式JSON')
    affected_action_types = Column(JSON, comment='受影响的动作类型列表')
    resolution_status = Column(String(20), default='OPEN', comment='处理状态: OPEN/UNDER_REVIEW/CLEARED/PENALIZED')
    resolved_by = Column(String(36), comment='处理人ID')
    resolved_at = Column(DateTime, comment='处理时间')
    penalty_applied = Column(Text, comment='应用的处罚措施')
    created_at = Column(DateTime, default=datetime.utcnow, comment='标记时间')

class DualTrackSynergyCache(Base):
    """双轨协同缓存表"""
    __tablename__ = 'dual_track_synergy_caches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, comment='用户ID')
    combined_privileges_json = Column(JSON, comment='合并后的特权列表JSON')
    synergy_score = Column(Float, default=0.0, comment='双轨协同分数 0-100')
    review_priority_boost = Column(Float, default=0.0, comment='审核优先级加成')
    purchase_discount_bonus = Column(Float, default=0.0, comment='购买折扣加成')
    exposure_boost = Column(Float, default=0.0, comment='曝光加成')
    last_calculated_at = Column(DateTime, default=datetime.utcnow, comment='最后计算时间')

# =============================================================================
# 第四十一部分：人才市场与技能市场可用性保障 (market_availability_assurance_layer.py)
# =============================================================================

class AgentSandboxTestRecord(Base):
    """智能体沙盒测试记录表"""
    __tablename__ = 'agent_sandbox_test_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_session_id = Column(String(36), unique=True, nullable=False, comment='测试会话ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    agent_version = Column(String(20), comment='版本号')
    test_type = Column(String(30), default='PRE_LISTING', comment='测试类型: PRE_LISTING/VERSION_UPGRADE/PERIODIC')
    functional_test_pass_rate = Column(Float, default=0.0, comment='功能测试通过率')
    api_completeness_score = Column(Float, default=0.0, comment='API完整性评分')
    dependency_proof_score = Column(Float, default=0.0, comment='依赖证明评分')
    security_scan_score = Column(Float, default=0.0, comment='安全扫描评分')
    total_score = Column(Float, default=0.0, comment='综合评分')
    listing_decision = Column(String(20), comment='决策: APPROVED/REJECTED/PENDING_REVIEW')
    fault_injection_results_json = Column(JSON, comment='故障注入结果JSON')
    avg_response_time_ms = Column(Integer, default=0, comment='平均响应时间毫秒')
    error_type_distribution_json = Column(JSON, comment='错误类型分布JSON')
    tested_at = Column(DateTime, default=datetime.utcnow, comment='测试时间')

class AgentServiceRegistry(Base):
    """智能体服务注册中心表"""
    __tablename__ = 'agent_service_registries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(String(36), unique=True, nullable=False, comment='注册ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    agent_type = Column(String(50), comment='六部类型')
    capabilities_tags_json = Column(JSON, comment='能力标签列表JSON')
    supported_data_sources_json = Column(JSON, comment='支持的数据源JSON')
    supported_skills_json = Column(JSON, comment='支持的技能列表JSON')
    health_endpoint = Column(String(200), comment='健康检查端点')
    host_address = Column(String(100), comment='主机地址')
    port = Column(Integer, comment='端口')
    status = Column(String(20), default='HEALTHY', comment='状态: HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN')
    registered_at = Column(DateTime, default=datetime.utcnow, comment='注册时间')
    last_heartbeat_at = Column(DateTime, comment='最后心跳时间')
    deregistered_at = Column(DateTime, comment='注销时间')
    deregister_reason = Column(String(100), comment='注销原因')

    __table_args__ = (
        Index('idx_registry_agent_status', 'agent_id', 'status'),
        Index('idx_registry_type_status', 'agent_type', 'status'),
    )

class AgentHealthCheckLog(Base):
    """智能体健康检查日志表"""
    __tablename__ = 'agent_health_check_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(36), unique=True, nullable=False, comment='检查ID')
    agent_id = Column(String(36), nullable=False, comment='智能体ID')
    check_time = Column(DateTime, default=datetime.utcnow, comment='检查时间')
    is_healthy = Column(Boolean, default=True, comment='是否健康')
    response_time_ms = Column(Integer, default=0, comment='响应时间毫秒')
    cpu_usage = Column(Float, default=0.0, comment='CPU使用率')
    memory_usage_mb = Column(Float, default=0.0, comment='内存使用MB')
    error_rate = Column(Float, default=0.0, comment='错误率')
    consecutive_failures = Column(Integer, default=0, comment='连续失败次数')
    action_taken = Column(String(30), comment='采取的动作: NONE/WARN/DEREGISTER/ALERT')

class SkillDependencyDeclaration(Base):
    """技能依赖声明表"""
    __tablename__ = 'skill_dependency_declarations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    declaration_id = Column(String(36), unique=True, nullable=False, comment='声明ID')
    skill_id = Column(String(36), nullable=False, comment='技能ID')
    required_agent_type = Column(String(50), nullable=False, comment='所需智能体类型')
    min_agent_version = Column(String(20), comment='最低智能体版本')
    dependency_description = Column(Text, comment='依赖描述')
    is_binding_auto_created = Column(Boolean, default=False, comment='是否自动创建绑定')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class SkillAgentBinding(Base):
    """技能-智能体绑定关系表"""
    __tablename__ = 'skill_agent_bindings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    binding_id = Column(String(36), unique=True, nullable=False, comment='绑定ID')
    skill_id = Column(String(36), nullable=False, comment='技能ID')
    agent_id = Column(String(36), nullable=False, comment='绑定的智能体ID')
    binding_type = Column(String(20), default='AUTO', comment='绑定类型: AUTO/MANUAL')
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE/SUSPENDED/REVOKED')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    revoked_at = Column(DateTime, comment='撤销时间')
    revoked_reason = Column(Text, comment='撤销原因')

class SkillHotLoadRecord(Base):
    """技能热加载记录表"""
    __tablename__ = 'skill_hot_load_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    load_id = Column(String(36), unique=True, nullable=False, comment='加载ID')
    agent_id = Column(String(36), nullable=False, comment='目标智能体ID')
    skill_id = Column(String(36), nullable=False, comment='加载的技能ID')
    load_status = Column(String(20), default='PENDING', comment='状态: PENDING/LOADING/SUCCESS/FAILED/ROLLED_BACK')
    triggered_by_user_id = Column(String(36), comment='触发用户ID')
    load_duration_ms = Column(Integer, comment='加载耗时毫秒')
    rollback_reason = Column(Text, comment='回滚原因')
    user_notified = Column(Boolean, default=False, comment='是否已通知用户')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    completed_at = Column(DateTime, comment='完成时间')

class ExternalDependencyValidation(Base):
    """外部依赖验证记录表"""
    __tablename__ = 'external_dependency_validations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    validation_id = Column(String(36), unique=True, nullable=False, comment='验证ID')
    skill_id = Column(String(36), comment='关联技能ID')
    dep_service_name = Column(String(100), nullable=False, comment='依赖服务名称')
    dep_endpoint = Column(String(200), comment='依赖端点')
    is_accessible = Column(Boolean, default=False, comment='是否可访问')
    response_time_ms = Column(Integer, comment='响应时间')
    result_matches_expectation = Column(Boolean, comment='结果是否符合预期')
    credential_expiry = Column(DateTime, comment='凭证过期时间')
    validated_at = Column(DateTime, default=datetime.utcnow, comment='验证时间')

class DataSourceHealthStatus(Base):
    """数据源健康状态表"""
    __tablename__ = 'data_source_health_statuses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(36), unique=True, nullable=False, comment='数据源ID')
    source_name = Column(String(100), comment='数据源名称')
    source_type = Column(String(30), comment='类型: API/DATABASE/FILE/THIRD_PARTY')
    current_state = Column(String(20), default='HEALTHY', comment='状态: HEALTHY/DEGRADED/UNAVAILABLE/RECOVERING')
    success_rate_last_hour = Column(Float, default=1.0, comment='最近1小时成功率')
    avg_response_time_ms = Column(Integer, default=0, comment='平均响应时间')
    data_freshness_minutes = Column(Integer, comment='数据新鲜度(分钟)')
    backup_source_id = Column(String(36), comment='备用数据源ID')
    consecutive_failures = Column(Integer, default=0, comment='连续失败次数')
    last_failure_at = Column(DateTime, comment='最后失败时间')
    last_recovery_at = Column(DateTime, comment='最后恢复时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class DataQualityCheckResult(Base):
    """数据质量检查结果表"""
    __tablename__ = 'data_quality_check_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(36), unique=True, nullable=False, comment='检查ID')
    source_id = Column(String(36), comment='数据源ID')
    record_count_checked = Column(Integer, default=0, comment='检查的记录数')
    completeness_issues = Column(Integer, default=0, comment='完整性问题数')
    reasonableness_issues = Column(Integer, default=0, comment='合理性问题数')
    freshness_issues = Column(Integer, default=0, comment='时效性问题数')
    auto_repaired = Column(Integer, default=0, comment='自动修复数')
    marked_missing = Column(Integer, default=0, comment='标记缺失数')
    overall_quality_score = Column(Float, default=0.0, comment='总体质量分 0-100')
    checked_at = Column(DateTime, default=datetime.utcnow, comment='检查时间')

class CircuitBreakerState(Base):
    """熔断器状态表"""
    __tablename__ = 'circuit_breaker_states'
    id = Column(Integer, primary_key=True, autoincrement=True)
    circuit_id = Column(String(36), unique=True, nullable=False, comment='熔断器ID')
    protected_resource_id = Column(String(36), nullable=False, comment='保护资源ID(数据源/分析服务)')
    resource_type = Column(String(20), comment='资源类型: DATA_SOURCE/ANALYSIS_SERVICE/API_ENDPOINT')
    state = Column(String(20), default='CLOSED', comment='状态: CLOSED/OPEN/HALF_OPEN')
    failure_count = Column(Integer, default=0, comment='当前失败计数')
    failure_threshold = Column(Integer, default=5, comment='失败阈值')
    opened_at = Column(DateTime, comment='打开时间')
    cooldown_end_at = Column(DateTime, comment='冷却结束时间')
    last_probe_time = Column(DateTime, comment='最后探测时间')
    last_probe_success = Column(Boolean, comment='最后探测是否成功')
    total_open_count = Column(Integer, default=0, comment='累计打开次数')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class AnalysisModelHealthRecord(Base):
    """分析模型健康记录表"""
    __tablename__ = 'analysis_model_health_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), unique=True, nullable=False, comment='记录ID')
    model_id = Column(String(36), nullable=False, comment='模型ID')
    model_version = Column(String(20), comment='模型版本')
    health_check_result = Column(String(20), default='HEALTHY', comment='结果: HEALTHY/DEGRADED/CRITICAL')
    error_rate = Column(Float, default=0.0, comment='误差率')
    baseline_error_rate = Column(Float, comment='基线误差率')
    degradation_detected = Column(Boolean, default=False, comment='是否检测到退化')
    rolled_back_to_version = Column(String(20), comment='回滚到的版本')
    checked_at = Column(DateTime, default=datetime.utcnow, comment='检查时间')

class AnalysisCacheEntry(Base):
    """分析缓存条目表"""
    __tablename__ = 'analysis_cache_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(128), unique=True, nullable=False, comment='缓存键')
    task_type = Column(String(50), comment='任务类型')
    input_hash = Column(String(64), comment='输入参数哈希')
    result_data_json = Column(JSON, comment='缓存结果数据JSON')
    ttl_seconds = Column(Integer, default=86400, comment='存活时间秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    expires_at = Column(DateTime, comment='过期时间')
    hit_count = Column(Integer, default=0, comment='命中次数')
    last_hit_at = Column(DateTime, comment='最后命中时间')
    invalidated_by_data_update = Column(Boolean, default=False, comment='是否被数据更新失效')

class TaskTraceRecord(Base):
    """任务调用链追踪记录表"""
    __tablename__ = 'task_trace_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(36), nullable=False, comment='追踪ID')
    step_id = Column(String(36), unique=True, nullable=False, comment='步骤ID')
    step_order = Column(Integer, nullable=False, comment='步骤序号')
    step_type = Column(String(30), nullable=False, comment='步骤类型: TASK_SUBMITTED/SCHEDULER_ASSIGNED/AGENT_EXECUTING/RESULT_RETURNED/ERROR_OCCURRED')
    agent_id = Column(String(36), comment='执行的智能体ID')
    service_id = Column(String(36), comment='服务ID')
    details_json = Column(JSON, comment='步骤详情JSON')
    duration_ms = Column(Integer, comment='该步骤耗时毫秒')
    status = Column(String(20), default='SUCCESS', comment='状态: SUCCESS/ERROR/TIMEOUT')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_trace_trace_id', 'trace_id', 'step_order'),
    )

class TaskDegradationEvent(Base):
    """任务降级事件表"""
    __tablename__ = 'task_degradation_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    task_id = Column(String(36), comment='任务ID')
    degradation_strategy = Column(String(30), nullable=False, comment='降级策略: GENERIC_FALLBACK/POLITE_REFUSE/QUEUE_AND_RETRY')
    original_target_agent_id = Column(String(36), comment='原目标智能体')
    fallback_used = Column(String(50), comment='实际使用的降级方案')
    degradation_result = Column(String(20), comment='降级结果: SUCCESS/FAILED/PARTIAL')
    user_notified = Column(Boolean, default=False, comment='是否通知用户')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class UserFailureFeedback(Base):
    """用户失败反馈表"""
    __tablename__ = 'user_failure_feedbacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(36), unique=True, nullable=False, comment='反馈ID')
    task_id = Column(String(36), nullable=False, comment='任务ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    agent_id = Column(String(36), comment='失败的智能体ID')
    error_log_anonymized = Column(Text, comment='脱敏错误日志')
    user_comment = Column(Text, comment='用户评论')
    submitted_at = Column(DateTime, default=datetime.utcnow, comment='提交时间')

class UserAssetReport(Base):
    """用户资产举报表"""
    __tablename__ = 'user_asset_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='举报ID')
    reporter_user_id = Column(String(36), nullable=False, comment='举报人ID')
    asset_type = Column(String(20), nullable=False, comment='资产类型: AGENT/SKILL')
    asset_id = Column(String(36), nullable=False, comment='资产ID')
    report_reason = Column(String(100), nullable=False, comment='举报原因')
    verification_task_id = Column(String(36), comment='验证任务ID')
    verification_result = Column(String(20), comment='验证结果: CONFIRMED/DISMISSSED/PENDING')
    resolution_action = Column(String(30), comment='处理动作: DELISTED/NO_ACTION/WARNED')
    affected_users_notified = Column(Integer, default=0, comment='受影响用户通知数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    resolved_at = Column(DateTime, comment='解决时间')

class AssetReputationScore(Base):
    """资产信誉评分表"""
    __tablename__ = 'asset_reputation_scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(36), unique=True, nullable=False, comment='资产ID')
    asset_type = Column(String(20), comment='资产类型')
    reputation_score = Column(Float, default=5.0, comment='信誉评分 0-10')
    total_reports = Column(Integer, default=0, comment='总举报数')
    confirmed_reports = Column(Integer, default=0, comment='确认的举报数')
    failure_rate_30d = Column(Float, default=0.0, comment='30天失败率')
    usage_count_total = Column(Integer, default=0, comment='总使用次数')
    satisfaction_avg = Column(Float, default=5.0, comment='平均满意度')
    risk_level = Column(String(20), default='LOW', comment='风险等级: LOW/MEDIUM/HIGH/CRITICAL')
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后更新')

class AvailabilityAlertRecord(Base):
    """可用性告警记录表"""
    __tablename__ = 'availability_alert_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(36), unique=True, nullable=False, comment='告警ID')
    alert_type = Column(String(30), nullable=False, comment='告警类型: AGENT_UNHEALTHY/SOURCE_DOWN/MODEL_DEGRADATION/SKILL_HIGH_RISK/CIRCUIT_OPEN')
    target_id = Column(String(36), comment='目标ID(智能体/数据源/模型/技能)')
    target_name = Column(String(100), comment='目标名称')
    severity = Column(String(20), default='WARNING', comment='严重程度: INFO/WARNING/CRITICAL')
    metric_value = Column(Float, comment='触发值')
    threshold_value = Column(Float, comment='阈值')
    alert_channel = Column(String(20), default='DINGTALK', comment='告警渠道: DINGTALK/EMAIL/SMS/WEBHOOK')
    acknowledged_by = Column(String(36), comment='确认人ID')
    acknowledged_at = Column(DateTime, comment='确认时间')
    resolved_at = Column(DateTime, comment='解决时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_alert_type_severity', 'alert_type', 'severity'),
        Index('idx_alert_created', 'created_at'),
    )


# =============================================================================
# 第四十二部分：标准化差异库与多级兜底 (standardized_diff_fallback_layer.py)
# =============================================================================

class InputAnomalyLog(Base):
    """输入异常分类日志表"""
    __tablename__ = 'input_anomaly_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(36), unique=True, nullable=False, comment='日志ID')
    session_id = Column(String(36), comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    raw_input_text = Column(Text, comment='原始输入')
    anomaly_type = Column(String(30), comment='异常类型: PURE_GARBLE/MIXED_GARBLE/REPEATED_CHARS/BATCH_NO_SEPARATOR/OUT_OF_ORDER/MULTIPLE_INTENTS/EXCESSIVE_OMISSION/TAUTOLOGY/DOUBLE_NEGATION/VAGUE_REFERENCE/PROMPT_INJECTION/ULTRA_LONG_TEXT/EMOJI_FLOODING/NORMAL')
    anomaly_score = Column(Float, default=0.0, comment='异常分数 0-1')
    anomaly_severity = Column(String(20), default='LOW', comment='严重程度: LOW/MEDIUM/HIGH/CRITICAL')
    sub_type_scores_json = Column(JSON, comment='各子类型分数JSON')
    action_taken = Column(String(30), comment='处理动作: TEMPLATE_RETURN/PREPROCESS/ROUTE_LLM/BLOCK')
    processing_latency_ms = Column(Integer, default=0, comment='处理耗时毫秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class StandardTemplateRecord(Base):
    """标准响应模板记录表"""
    __tablename__ = 'standard_template_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(36), unique=True, nullable=False, comment='模板ID')
    scenario_key = Column(String(50), nullable=False, comment='场景键: NORMAL_QUERY/INSUFFICIENT_INFO/NOT_UNDERSTOOD/BATCH_QUERY/OUT_OF_ORDER/SYSTEM_BUSY/GARBLED_INPUT/PROMPT_INJECTION/ULTRA_LONG_TEXT/MULTIPLE_INTENTS/GREETING/FAREWELL')
    template_content = Column(Text, nullable=False, comment='模板内容')
    user_tier = Column(String(20), default='NORMAL', comment='适用用户层: NORMAL/PROFESSIONAL/ENTERPRISE')
    version = Column(Integer, default=1, comment='版本号')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(String(36), comment='创建者(运营人员)')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment='更新时间')

class TemplateVersionHistory(Base):
    """模板版本历史表"""
    __tablename__ = 'template_version_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(String(36), unique=True, nullable=False, comment='历史ID')
    template_id = Column(String(36), nullable=False, comment='关联模板ID')
    old_content = Column(Text, comment='旧版本内容')
    new_content = Column(Text, comment='新版本内容')
    change_reason = Column(String(200), comment='变更原因')
    changed_by = Column(String(36), comment='操作人')
    changed_at = Column(DateTime, default=datetime.utcnow, comment='变更时间')

class ABTestConfig(Base):
    """A/B测试配置表"""
    __tablename__ = 'ab_test_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(36), unique=True, nullable=False, comment='测试ID')
    test_name = Column(String(100), comment='测试名称')
    target_scenario_key = Column(String(50), comment='目标场景键')
    variant_a_template_id = Column(String(36), comment='变体A模板ID')
    variant_b_template_id = Column(String(36), comment='变体B模板ID')
    traffic_split = Column(Float, default=0.5, comment='流量分配 A比例')
    status = Column(String(20), default='RUNNING', comment='状态: DRAFT/RUNNING/PAUSED/COMPLETED')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    winner_variant = Column(String(10), comment='获胜变体 A/B')
    statistical_significance = Column(Boolean, comment='是否统计显著')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class PreprocessingLog(Base):
    """预处理管道日志表"""
    __tablename__ = 'preprocessing_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    preprocess_id = Column(String(36), unique=True, nullable=False, comment='预处理ID')
    raw_input_length = Column(Integer, comment='原始长度')
    processed_length = Column(Integer, comment='处理后长度')
    transformations_applied_json = Column(JSON, comment='应用的转换列表JSON: encoding_norm/garble_detect/dedup/punct_clean/length_truncate/whitespace_norm')
    garble_ratio_detected = Column(Float, comment='检测到的乱码比率')
    was_blocked = Column(Boolean, default=False, comment='是否被拦截(乱码/超长)')
    block_reason = Column(String(50), comment='拦截原因')
    latency_ms = Column(Integer, default=0, comment='预处理耗时毫秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class IntentMatchLog(Base):
    """意图匹配日志表"""
    __tablename__ = 'intent_match_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(36), unique=True, nullable=False, comment='匹配ID')
    input_text_snippet = Column(Text, comment='输入文本片段')
    matched_intent = Column(String(30), comment='匹配到的意图: GREETING/GRATITUDE/HELP_REQUEST/PRICE_QUERY/TIME_QUERY/POLICY_QUERY/COMPARISON_QUERY/FAREWELL/NONE')
    confidence_score = Column(Float, default=0.0, comment='置信度 0-1')
    matched_rule_id = Column(String(36), comment='命中的规则ID')
    bypassed_llm = Column(Boolean, default=False, comment='是否绕过LLM')
    template_used = Column(String(50), comment='使用的话术模板')
    latency_ms = Column(Integer, default=0, comment='匹配耗时毫秒')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class EntityCorrectionLog(Base):
    """实体模糊匹配纠正日志表"""
    __tablename__ = 'entity_correction_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    correction_id = Column(String(36), unique=True, nullable=False, comment='纠正ID')
    original_input = Column(Text, comment='原始输入')
    corrected_query = Column(Text, comment='纠正后查询')
    extracted_entities_json = Column(JSON, comment='提取的实体JSON: city/district/budget/area/property_type')
    corrections_made_json = Column(JSON, comment='纠正详情JSON: 原始值→纠正值+编辑距离')
    confidence_score = Column(Float, default=0.0, comment='总体置信度')
    needs_user_confirmation = Column(Boolean, default=False, comment='是否需要用户确认')
    user_confirmed = Column(Boolean, nullable=True, comment='用户是否确认')
    reorganized_from_out_of_order = Column(Boolean, default=False, comment='是否从乱序重组')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class LLMRoutingDecisionLog(Base):
    """LLM路由决策日志表"""
    __tablename__ = 'llm_routing_decision_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    routing_id = Column(String(36), unique=True, nullable=False, comment='路由ID')
    session_id = Column(String(36), comment='会话ID')
    input_complexity_score = Column(Float, comment='输入复杂度分数')
    anomaly_score = Column(Float, comment='异常分数')
    intent_match_result = Column(String(20), comment='意图匹配结果')
    routed_level = Column(Integer, comment='路由等级 0-5')
    routed_model_name = Column(String(50), comment='路由到模型名')
    routed_provider = Column(String(30), comment='提供商: deepseek/zhipu/openai/qwen/local')
    reason_code = Column(String(30), comment='路由原因: TEMPLATE_HIT/INTENT_MATCH/LIGHTWEIGHT/HEAVYWEIGHT/QUANTITATIVE/UPGRADE/DISSATISFACTION_RETRY')
    estimated_cost = Column(Float, default=0.0, comment='预估成本')
    actual_cost = Column(Float, default=0.0, comment='实际成本')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ExternalLLMCallLog(Base):
    """外部LLM调用日志表"""
    __tablename__ = 'external_llm_call_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(36), unique=True, nullable=False, comment='调用ID')
    provider = Column(String(30), nullable=False, comment='提供商')
    model_name = Column(String(50), comment='模型名称')
    prompt_tokens = Column(Integer, default=0, comment='prompt token数')
    completion_tokens = Column(Integer, default=0, comment='completion token数')
    total_tokens = Column(Integer, default=0, comment='总token数')
    cost_usd = Column(Float, default=0.0, comment='成本USD')
    latency_ms = Column(Integer, default=0, comment='调用延迟毫秒')
    is_streaming = Column(Boolean, default=False, comment='是否流式')
    retry_count = Column(Integer, default=0, comment='重试次数')
    success = Column(Boolean, default=True, comment='是否成功')
    error_message = Column(Text, comment='错误信息')
    session_id = Column(String(36), comment='会话ID')
    user_id = Column(String(36), comment='用户ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_llm_call_provider_time', 'provider', 'created_at'),
        Index('idx_llm_call_session', 'session_id'),
    )

class ProviderCircuitState(Base):
    """提供商熔断器状态表"""
    __tablename__ = 'provider_circuit_states'
    id = Column(Integer, primary_key=True, autoincrement=True)
    circuit_id = Column(String(36), unique=True, nullable=False, comment='熔断器ID')
    provider = Column(String(30), nullable=False, comment='提供商')
    state = Column(String(20), default='CLOSED', comment='状态: CLOSED/OPEN/HALF_OPEN')
    failure_count = Column(Integer, default=0, comment='当前失败计数')
    failure_threshold = Column(Integer, default=5, comment='失败阈值')
    opened_at = Column(DateTime, comment='打开时间')
    cooldown_end_at = Column(DateTime, comment='冷却结束时间')
    last_probe_at = Column(DateTime, comment='最后探测时间')
    total_open_count = Column(Integer, default=0, comment='累计打开次数')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

class DegradationEventLog(Base):
    """降级事件日志表"""
    __tablename__ = 'degradation_event_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, comment='事件ID')
    session_id = Column(String(36), comment='会话ID')
    original_provider = Column(String(30), comment='原提供商')
    original_model = Column(String(50), comment='原模型')
    degradation_strategy = Column(String(30), comment='降级策略: TRY_NEXT_PROVIDER/FALLBACK_LOCAL/FALLBACK_TEMPLATE')
    fallback_provider = Column(String(30), comment='降级后提供商')
    fallback_model = Column(String(50), comment='降级后模型')
    result = Column(String(20), comment='结果: SUCCESS/PARTIAL_FAIL/FAIL')
    user_notified = Column(Boolean, default=False, comment='是否通知用户')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class JudgeModelScoreLog(Base):
    """裁判模型评分日志表"""
    __tablename__ = 'judge_model_score_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    score_id = Column(String(36), unique=True, nullable=False, comment='评分ID')
    session_id = Column(String(36), comment='会话ID')
    message_id = Column(String(36), comment='消息ID')
    query_text = Column(Text, comment='用户查询')
    response_text = Column(Text, comment='智能体回复')
    relevance_score = Column(Float, comment='相关性分数 0-1')
    accuracy_score = Column(Float, comment='准确性分数 0-1')
    completeness_score = Column(Float, comment='完整性分数 0-1')
    safety_score = Column(Float, comment='安全性分数 0-1')
    overall_score = Column(Float, comment='综合分数 0-1')
    passed_threshold = Column(Boolean, comment='是否通过阈值')
    triggered_regeneration = Column(Boolean, default=False, comment='是否触发重新生成')
    judge_model_used = Column(String(50), comment='使用的裁判模型')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class UserFeedbackLog(Base):
    """用户反馈日志表"""
    __tablename__ = 'user_feedback_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(36), unique=True, nullable=False, comment='反馈ID')
    session_id = Column(String(36), nullable=False, comment='会话ID')
    message_id = Column(String(36), nullable=False, comment='消息ID')
    user_id = Column(String(36), nullable=False, comment='用户ID')
    feedback_type = Column(String(10), nullable=False, comment='反馈类型: positive/negative')
    feedback_reason = Column(String(100), comment='反馈原因: not_relevant/wrong_info/too_long/rude/etc')
    original_routing_level = Column(Integer, comment='原始路由等级')
    upgraded_routing_level = Column(Integer, comment='升级后路由等级')
    improved_response_generated = Column(Boolean, comment='是否生成了改进回复')
    improvement_success = Column(Boolean, nullable=True, comment='改进是否成功')
    added_to_optimization_queue = Column(Boolean, default=False, comment='是否加入优化队列')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ConsistencyCheckLog(Base):
    """一致性校验日志表"""
    __tablename__ = 'consistency_check_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(36), unique=True, nullable=False, comment='校验ID')
    session_id = Column(String(36), comment='会话ID')
    response_text_snippet = Column(Text, comment='回复文本片段')
    api_data_json = Column(JSON, comment='API返回数据JSON')
    extracted_values_json = Column(JSON, comment='从回复中提取的数值JSON')
    verification_mode = Column(String(20), default='TOLERANT', comment='验证模式: STRICT/TOLERANT/SEMANTIC')
    is_consistent = Column(Boolean, comment='是否一致')
    mismatch_severity = Column(String(20), comment='不一致严重度: NONE/MINOR/MAJOR/CRITICAL')
    auto_corrected = Column(Boolean, default=False, comment='是否自动校正')
    correction_applied = Column(Text, comment='应用的校正内容')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class BatchQuerySplitLog(Base):
    """批量查询拆分日志表"""
    __tablename__ = 'batch_query_split_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    split_id = Column(String(36), unique=True, nullable=False, comment='拆分ID')
    session_id = Column(String(36), comment='会话ID')
    original_input = Column(Text, comment='原始输入')
    split_strategy = Column(String(20), comment='拆分策略: KEYWORD_BASED/LENGTH_BASED/SEMANTIC_MODEL')
    sub_queries_json = Column(JSON, comment='拆分后的子查询列表JSON')
    sub_query_count = Column(Integer, default=0, comment='子查询数量')
    user_confirmed = Column(Boolean, default=False, comment='用户是否确认')
    aggregation_completed = Column(Boolean, default=False, comment='聚合是否完成')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class ClarificationSessionLog(Base):
    """澄清会话日志表"""
    __tablename__ = 'clarification_session_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    clarification_id = Column(String(36), unique=True, nullable=False, comment='澄清ID')
    session_id = Column(String(36), nullable=False, comment='主会话ID')
    ambiguity_type = Column(String(30), comment='歧义类型: AMBIGUOUS_CITY/AMBIGUOUS_DISTRICT/AMBIGUOUS_BUDGET/AMBIGUOUS_PROPERTY_TYPE/AMBIGUOUS_AREA')
    question_asked = Column(Text, comment='向用户提出的问题')
    user_response = Column(Text, comment='用户回答')
    round_number = Column(Integer, default=1, comment='当前轮次(最多3轮)')
    resolved = Column(Boolean, default=False, comment='是否已解决')
    escalated_to_dashboard = Column(Boolean, default=False, comment='是否升级到仪表盘')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    resolved_at = Column(DateTime, comment='解决时间')

class DynamicRulePerformance(Base):
    """动态规则效能表"""
    __tablename__ = 'dynamic_rule_performances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(36), unique=True, nullable=False, comment='规则ID')
    rule_name = Column(String(100), comment='规则名称')
    rule_category = Column(String(30), comment='规则类别: ANOMALY_DETECTION/INTENT_MATCH/PREPROCESSING/TEMPLATE_SELECTION')
    priority_weight = Column(Float, default=1.0, comment='优先级权重')
    hit_count_total = Column(Integer, default=0, comment='总命中次数')
    hit_count_last_week = Column(Integer, default=0, comment='上周命中次数')
    conversion_rate = Column(Float, default=0.0, comment='转化率(命中后用户满意)')
    user_satisfaction_avg = Column(Float, default=0.0, comment='用户满意度均值')
    is_active = Column(Boolean, default=True, comment='是否激活')
    last_adjusted_at = Column(DateTime, comment='最后调整时间')
    adjustment_history_json = Column(JSON, comment='调整历史JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment='更新时间')

class ConsultationPerformanceSnapshot(Base):
    """咨询性能快照表"""
    __tablename__ = 'consultation_performance_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照ID')
    snapshot_time = Column(DateTime, default=datetime.utcnow, comment='快照时间')
    period = Column(String(20), comment='周期: hourly/daily/weekly')
    total_requests = Column(Integer, default=0, comment='总请求数')
    avg_latency_ms = Column(Integer, default=0, comment='平均延迟ms')
    p50_latency = Column(Integer, default=0, comment='P50延迟')
    p95_latency = Column(Integer, default=0, comment='P95延迟')
    p99_latency = Column(Integer, default=0, comment='P99延迟')
    latency_breach_count = Column(Integer, default=0, comment='超阈值次数(>5s)')
    stage_breakdown_json = Column(JSON, comment='各阶段耗时分解JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class LLMCostReport(Base):
    """LLM成本报告表"""
    __tablename__ = 'llm_cost_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    report_period = Column(String(20), comment='报告周期: daily/weekly/monthly')
    total_tokens_consumed = Column(Integer, default=0, comment='总消耗token')
    total_cost_usd = Column(Float, default=0.0, comment='总成本USD')
    cost_by_provider_json = Column(JSON, comment='按提供商成本分布JSON')
    cost_by_model_json = Column(JSON, comment='按模型成本分布JSON')
    cost_by_user_tier_json = Column(JSON, comment='按用户层级成本分布JSON')
    daily_budget = Column(Float, comment='日预算上限')
    budget_exceeded = Column(Boolean, default=False, comment='是否超预算')
    budget_exceeded_at = Column(DateTime, comment='超预算时间')
    cost_anomaly_detected = Column(Boolean, default=False, comment='是否检测到成本异常')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

class AnomalyRateReport(Base):
    """异常率监控报告表"""
    __tablename__ = 'anomaly_rate_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告ID')
    report_period = Column(String(20), comment='报告周期')
    negative_feedback_rate = Column(Float, default=0.0, comment='负反馈率')
    judge_low_score_rate = Column(Float, default=0.0, comment='裁判低分率')
    degradation_frequency = Column(Integer, default=0, comment='降级频次')
    circuit_open_events = Column(Integer, default=0, comment='熔断打开事件数')
    overall_anomaly_rate = Column(Float, default=0.0, comment='综合异常率')
    alert_triggered = Column(Boolean, default=False, comment='是否触发告警(>5%)')
    alert_threshold = Column(Float, default=0.05, comment='告警阈值')
    trend_direction = Column(String(10), comment='趋势方向: UP/DOWN/STABLE')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')


# ============================================================
# Layer 33 - Human Customer Service System (人工客服系统层)
# ============================================================

# ---------- Access Mechanism Group (接入机制组) ----------

class CustomerServiceSession(Base):
    """客服会话表"""
    __tablename__ = 'cs_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, comment='会话唯一标识')
    task_id = Column(String(36), comment='关联任务ID')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    agent_id = Column(String(64), comment='客服人员ID')
    status = Column(String(20), nullable=False, comment='会话状态: queued/in_progress/ended/timeout/transferred')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    assigned_at = Column(DateTime, comment='分配给客服的时间')
    ended_at = Column(DateTime, comment='结束时间')
    trace_id = Column(String(32), comment='追踪ID')
    transfer_count = Column(Integer, default=0, comment='转接次数')

    __table_args__ = (
        Index('idx_cs_sessions_user_id', 'user_id'),
        Index('idx_cs_sessions_agent_id', 'agent_id'),
        Index('idx_cs_sessions_status', 'status'),
        Index('idx_cs_sessions_created_at', 'created_at'),
    )


class CSQueueEntry(Base):
    """排队记录表"""
    __tablename__ = 'cs_queue_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(36), unique=True, nullable=False, comment='排队记录唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    session_id = Column(String(36), comment='关联会话ID')
    priority = Column(Integer, nullable=False, comment='优先级')
    queue_position = Column(Integer, comment='当前队列位置')
    estimated_wait_min = Column(Float, comment='预计等待分钟数')
    trigger_type = Column(String(30), comment='触发类型')
    user_tier = Column(String(20), comment='用户等级/层级')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_queue_entries_user_id', 'user_id'),
        Index('idx_cs_queue_entries_session_id', 'session_id'),
        Index('idx_cs_queue_entries_priority', 'priority'),
        Index('idx_cs_queue_entries_created_at', 'created_at'),
    )


class CSSatisfactionRating(Base):
    """满意度评价表"""
    __tablename__ = 'cs_satisfaction_ratings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rating_id = Column(String(36), unique=True, nullable=False, comment='评价唯一标识')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    agent_id = Column(String(64), nullable=False, comment='客服人员ID')
    problem_solved = Column(Integer, comment='问题是否解决评分(1-5)')
    response_speed = Column(Integer, comment='响应速度评分(1-5)')
    service_attitude = Column(Integer, comment='服务态度评分(1-5)')
    overall_score = Column(Float, comment='综合得分')
    text_feedback = Column(Text, comment='文字反馈内容')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_satisfaction_ratings_session_id', 'session_id'),
        Index('idx_cs_satisfaction_ratings_user_id', 'user_id'),
        Index('idx_cs_satisfaction_ratings_agent_id', 'agent_id'),
    )


class CSQuickReply(Base):
    """快捷回复库表"""
    __tablename__ = 'cs_quick_replies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reply_id = Column(String(36), unique=True, nullable=False, comment='回复唯一标识')
    category = Column(String(30), nullable=False, comment='分类')
    title = Column(String(100), nullable=False, comment='标题')
    content = Column(Text, nullable=False, comment='回复内容')
    is_global = Column(Boolean, default=False, comment='是否全局可用')
    creator_agent_id = Column(String(64), comment='创建者客服ID')
    usage_count = Column(Integer, default=0, comment='使用次数')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_quick_replies_category', 'category'),
        Index('idx_cs_quick_replies_creator_agent_id', 'creator_agent_id'),
    )


class CSWorkSchedule(Base):
    """工作时间配置表"""
    __tablename__ = 'cs_work_schedules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(String(36), unique=True, nullable=False, comment='配置唯一标识')
    day_of_week = Column(Integer, nullable=False, comment='星期几(0-6)')
    start_time = Column(String(10), nullable=False, comment='开始时间(HH:MM)')
    end_time = Column(String(10), nullable=False, comment='结束时间(HH:MM)')
    timezone = Column(String(20), comment='时区')
    is_holiday = Column(Boolean, default=False, comment='是否为节假日')
    emergency_contact = Column(String(100), comment='紧急联系人')
    emergency_phone = Column(String(30), comment='紧急联系电话')


class OfflineMessage(Base):
    """离线留言表"""
    __tablename__ = 'offline_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(36), unique=True, nullable=False, comment='留言唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    subject = Column(String(200), nullable=False, comment='留言主题')
    content = Column(Text, nullable=False, comment='留言内容')
    contact_preference = Column(String(20), comment='联系方式偏好')
    contact_info = Column(String(100), comment='联系信息')
    status = Column(String(20), default='pending', comment='处理状态: pending/replied/closed')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    replied_at = Column(DateTime, comment='回复时间')
    replied_by = Column(String(64), comment='回复人ID')

    __table_args__ = (
        Index('idx_offline_messages_user_id', 'user_id'),
        Index('idx_offline_messages_status', 'status'),
        Index('idx_offline_messages_created_at', 'created_at'),
    )


class CSAuditLog(Base):
    """操作审计日志表"""
    __tablename__ = 'cs_audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(36), unique=True, nullable=False, comment='日志唯一标识')
    agent_id = Column(String(64), nullable=False, comment='操作客服ID')
    event_type = Column(String(30), nullable=False, comment='事件类型')
    target_resource = Column(String(100), comment='目标资源')
    details = Column(JSON, comment='详细信息JSON')
    ip_address = Column(String(45), comment='IP地址')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='操作时间戳')

    __table_args__ = (
        Index('idx_cs_audit_logs_agent_id', 'agent_id'),
        Index('idx_cs_audit_logs_event_type', 'event_type'),
        Index('idx_cs_audit_logs_timestamp', 'timestamp'),
    )


class CSPerformanceDaily(Base):
    """客服日绩效表"""
    __tablename__ = 'cs_performance_daily'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stats_id = Column(String(36), unique=True, nullable=False, comment='统计唯一标识')
    agent_id = Column(String(64), nullable=False, comment='客服人员ID')
    date_str = Column(String(10), nullable=False, comment='日期字符串(YYYY-MM-DD)')
    total_sessions = Column(Integer, default=0, comment='总接待会话数')
    avg_response_sec = Column(Float, default=0.0, comment='平均响应秒数')
    satisfaction_avg = Column(Float, default=0.0, comment='平均满意度')
    resolve_rate = Column(Float, default=0.0, comment='解决率')
    transfer_out_count = Column(Integer, default=0, comment='转出次数')
    work_hours = Column(Float, default=0.0, comment='工作时长(小时)')

    __table_args__ = (
        Index('idx_cs_performance_daily_agent_id', 'agent_id'),
        Index('idx_cs_performance_daily_date_str', 'date_str'),
    )


class CSQualityInspection(Base):
    """质量抽检记录表"""
    __tablename__ = 'cs_quality_inspections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String(36), unique=True, nullable=False, comment='抽检唯一标识')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    inspector_id = Column(String(64), nullable=False, comment='质检员ID')
    attitude_score = Column(Integer, comment='态度评分(1-5)')
    professionalism_score = Column(Integer, comment='专业度评分(1-5)')
    efficiency_score = Column(Integer, comment='效率评分(1-5)')
    overall_score = Column(Float, comment='综合得分')
    low_score_reason = Column(Text, comment='低分原因说明')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_quality_inspections_session_id', 'session_id'),
        Index('idx_cs_quality_inspections_inspector_id', 'inspector_id'),
    )


class SessionTransferRecord(Base):
    """会话转接记录表"""
    __tablename__ = 'session_transfer_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), unique=True, nullable=False, comment='转接记录唯一标识')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    from_agent_id = Column(String(64), nullable=False, comment='转出客服ID')
    to_agent_id = Column(String(64), nullable=False, comment='转入客服ID')
    reason = Column(String(200), comment='转接原因')
    transfer_number = Column(Integer, comment='第几次转接')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_session_transfer_records_session_id', 'session_id'),
        Index('idx_session_transfer_records_from_agent_id', 'from_agent_id'),
        Index('idx_session_transfer_records_to_agent_id', 'to_agent_id'),
    )


class CSInternalNote(Base):
    """内部备注表"""
    __tablename__ = 'cs_internal_notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(String(36), unique=True, nullable=False, comment='备注唯一标识')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    agent_id = Column(String(64), nullable=False, comment='添加备注的客服ID')
    content = Column(Text, nullable=False, comment='备注内容')
    mentions = Column(JSON, comment='@提及的人员列表JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_internal_notes_session_id', 'session_id'),
        Index('idx_cs_internal_notes_agent_id', 'agent_id'),
    )


class SensitiveWordConfig(Base):
    """敏感词配置表"""
    __tablename__ = 'sensitive_word_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(String(36), unique=True, nullable=False, comment='敏感词唯一标识')
    word = Column(String(50), nullable=False, comment='敏感词内容')
    category = Column(String(30), nullable=False, comment='分类')
    is_active = Column(Boolean, default=True, comment='是否启用')
    added_by = Column(String(64), comment='添加人ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_sensitive_word_configs_category', 'category'),
        Index('idx_sensitive_word_configs_is_active', 'is_active'),
    )


# ---------- Deep Integration Group (深度集成组) ----------

class HumanCSAgentRegistry(Base):
    """礼部客服智能体注册表"""
    __tablename__ = 'human_cs_agent_registry'
    id = Column(Integer, primary_key=True, autoincrement=True)
    registry_id = Column(String(36), unique=True, nullable=False, comment='注册记录唯一标识')
    agent_id = Column(String(64), nullable=False, comment='智能体/客服ID')
    display_name = Column(String(50), nullable=False, comment='显示名称')
    avatar_url = Column(String(200), comment='头像URL')
    status = Column(String(20), nullable=False, comment='状态: online/offline/busy/away')
    capability_tags = Column(JSON, comment='能力标签JSON')
    max_concurrent = Column(Integer, default=5, comment='最大并发会话数')
    specialty_tags = Column(JSON, comment='专长标签JSON')
    registered_at = Column(DateTime, default=datetime.utcnow, comment='注册时间')

    __table_args__ = (
        Index('idx_human_cs_agent_registry_agent_id', 'agent_id'),
        Index('idx_human_cs_agent_registry_status', 'status'),
    )


class UserBehaviorMemory(Base):
    """用户行为记忆表"""
    __tablename__ = 'user_behavior_memories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(36), unique=True, nullable=False, comment='记忆唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    memory_type = Column(String(20), nullable=False, comment='记忆类型')
    input_text = Column(Text, comment='用户输入文本')
    emotion_tags = Column(JSON, comment='情绪标签JSON')
    frustration_index = Column(Float, comment='挫败指数')
    risk_level = Column(String(10), comment='风险等级')
    complexity_score = Column(Integer, comment='复杂度分数')
    transfer_recommended = Column(Boolean, default=False, comment='是否建议转人工')
    source_session_id = Column(String(36), comment='来源会话ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_user_behavior_memories_user_id', 'user_id'),
        Index('idx_user_behavior_memories_memory_type', 'memory_type'),
        Index('idx_user_behavior_memories_source_session_id', 'source_session_id'),
    )


class FrustrationIndexTracking(Base):
    """挫败指数追踪表"""
    __tablename__ = 'frustration_tracking'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_id = Column(String(36), unique=True, nullable=False, comment='追踪记录唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    failure_count = Column(Integer, default=0, comment='失败次数')
    total_interactions = Column(Integer, default=0, comment='总交互次数')
    current_index = Column(Float, default=0.0, comment='当前挫败指数')
    last_updated = Column(DateTime, default=datetime.utcnow, comment='最后更新时间')
    should_suggest_transfer = Column(Boolean, default=False, comment='是否建议转人工')

    __table_args__ = (
        Index('idx_frustration_tracking_user_id', 'user_id'),
    )


class RiskAssessmentResult(Base):
    """风险评估结果表"""
    __tablename__ = 'risk_assessment_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(36), unique=True, nullable=False, comment='评估唯一标识')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    risk_level = Column(String(10), nullable=False, comment='风险等级')
    risk_score = Column(Float, comment='风险分数')
    recommended_action = Column(String(50), comment='建议动作')
    detected_triggers = Column(JSON, comment='检测到的触发因素JSON')
    confidence = Column(Float, comment='置信度')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_risk_assessment_results_session_id', 'session_id'),
        Index('idx_risk_assessment_results_user_id', 'user_id'),
        Index('idx_risk_assessment_results_risk_level', 'risk_level'),
    )


class TaskComplexityEvaluation(Base):
    """任务复杂度评估表"""
    __tablename__ = 'task_complexity_evaluations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    eval_id = Column(String(36), unique=True, nullable=False, comment='评估唯一标识')
    task_id = Column(String(36), nullable=False, comment='任务ID')
    complexity_score = Column(Integer, comment='复杂度评分(1-10)')
    label = Column(String(20), comment='标签: simple/medium/complex/very_complex')
    agents_needed = Column(Integer, comment='所需客服人数')
    estimated_duration_min = Column(Float, comment='预估处理时长(分钟)')
    suggest_human = Column(Boolean, default=False, comment='是否建议人工处理')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_task_complexity_evaluations_task_id', 'task_id'),
    )


class CSTrainingSample(Base):
    """训练样本表"""
    __tablename__ = 'cs_training_samples'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(String(36), unique=True, nullable=False, comment='样本唯一标识')
    session_id = Column(String(36), comment='来源会话ID')
    user_input = Column(Text, nullable=False, comment='用户输入')
    agent_reply = Column(Text, nullable=False, comment='客服回复')
    cs_correction = Column(Text, comment='客服纠偏修正')
    label = Column(String(20), comment='样本标签')
    source_agent_type = Column(String(30), comment='来源智能体类型')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_training_samples_session_id', 'session_id'),
        Index('idx_cs_training_samples_label', 'label'),
    )


class ThoughtAtom(Base):
    """思维原子/解决方案模板表"""
    __tablename__ = 'thought_atoms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    atom_id = Column(String(36), unique=True, nullable=False, comment='原子唯一标识')
    problem_pattern = Column(String(300), nullable=False, comment='问题模式描述')
    solution_steps = Column(JSON, nullable=False, comment='解决步骤JSON')
    required_agents = Column(JSON, comment='所需智能体角色JSON')
    success_rate = Column(Float, comment='成功率')
    contributor_cs_id = Column(String(64), comment='贡献者客服ID')
    usage_count = Column(Integer, default=0, comment='使用次数')
    status = Column(String(20), default='pending_review', comment='状态: pending_review/approved/rejected')
    approved_by = Column(String(64), comment='审批人ID')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_thought_atoms_status', 'status'),
        Index('idx_thought_atoms_contributor_cs_id', 'contributor_cs_id'),
    )


class MemoryContributionScore(Base):
    """记忆贡献值表"""
    __tablename__ = 'memory_contribution_scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    contribution_id = Column(String(36), unique=True, nullable=False, comment='贡献记录唯一标识')
    cs_id = Column(String(64), nullable=False, comment='客服ID')
    memory_id = Column(String(36), nullable=False, comment='记忆ID')
    memory_type = Column(String(20), nullable=False, comment='记忆类型')
    recall_count = Column(Integer, default=0, comment='被召回次数')
    points_awarded = Column(Float, default=0.0, comment='获得积分')
    recalled_by_session = Column(String(36), comment='被哪个会话召回')
    recalled_at = Column(DateTime, comment='被召回时间')

    __table_args__ = (
        Index('idx_memory_contribution_scores_cs_id', 'cs_id'),
        Index('idx_memory_contribution_scores_memory_id', 'memory_id'),
    )


class CSCorrectionRecord(Base):
    """纠偏记录表"""
    __tablename__ = 'cs_correction_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    correction_id = Column(String(36), unique=True, nullable=False, comment='纠偏记录唯一标识')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    cs_id = Column(String(64), nullable=False, comment='执行纠偏的客服ID')
    original_reply = Column(Text, nullable=False, comment='原始回复内容')
    correction_type = Column(String(30), nullable=False, comment='纠偏类型')
    correction_detail = Column(Text, nullable=False, comment='纠偏详情')
    severity = Column(String(10), comment='严重程度: low/medium/high/critical')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_correction_records_session_id', 'session_id'),
        Index('idx_cs_correction_records_cs_id', 'cs_id'),
        Index('idx_cs_correction_records_severity', 'severity'),
    )


class CSABTestParticipation(Base):
    """A/B测试参与表"""
    __tablename__ = 'cs_ab_test_participations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    participation_id = Column(String(36), unique=True, nullable=False, comment='参与记录唯一标识')
    cs_id = Column(String(64), nullable=False, comment='参与客服ID')
    test_id = Column(String(36), nullable=False, comment='测试ID')
    variant = Column(String(20), nullable=False, comment='变体组: control/treatment_A/treatment_B')
    evaluation_score = Column(Float, comment='评估得分')
    feedback_text = Column(Text, comment='反馈文本')
    participated_at = Column(DateTime, default=datetime.utcnow, comment='参与时间')

    __table_args__ = (
        Index('idx_cs_ab_test_participations_cs_id', 'cs_id'),
        Index('idx_cs_ab_test_participations_test_id', 'test_id'),
        Index('idx_cs_ab_test_participations_variant', 'variant'),
    )


class CollaborationDashboardSnapshot(Base):
    """协同看板快照表"""
    __tablename__ = 'collaboration_dashboard_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照唯一标识')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')
    transfer_rate = Column(Float, comment='转人工率')
    agent_resolve_rate = Column(Float, comment='智能体解决率')
    human_resolve_rate = Column(Float, comment='人工解决率')
    avg_cs_response_time = Column(Float, comment='客服平均响应时间(秒)')
    avg_satisfaction = Column(Float, comment='平均满意度')
    top_reasons = Column(JSON, comment='Top原因分布JSON')
    rating_trend = Column(JSON, comment='评分趋势JSON')

    __table_args__ = (
        Index('idx_collaboration_dashboard_snapshots_generated_at', 'generated_at'),
    )


class AgentSelfReflectionReport(Base):
    """自省报告表"""
    __tablename__ = 'agent_self_reflection_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, comment='报告唯一标识')
    week_start = Column(String(10), nullable=False, comment='周起始日期(YYYY-MM-DD)')
    week_end = Column(String(10), nullable=False, comment='周结束日期(YYYY-MM-DD)')
    total_sessions = Column(Integer, default=0, comment='总会话数')
    transfer_count = Column(Integer, default=0, comment='转人工次数')
    transfer_rate = Column(Float, default=0.0, comment='转人工率')
    clustered_patterns = Column(JSON, comment='聚类模式JSON')
    improvement_suggestions = Column(JSON, comment='改进建议JSON')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')

    __table_args__ = (
        Index('idx_agent_self_reflection_reports_week_start', 'week_start'),
    )


class CSMentionNotification(Base):
    """@通知记录表"""
    __tablename__ = 'cs_mention_notifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(String(36), unique=True, nullable=False, comment='通知唯一标识')
    from_agent_id = Column(String(64), nullable=False, comment='发起@的客服ID')
    to_agent_id = Column(String(64), nullable=False, comment='被@的目标客服ID')
    session_id = Column(String(36), nullable=False, comment='关联会话ID')
    note_id = Column(String(36), comment='关联备注ID')
    message = Column(Text, comment='通知消息内容')
    is_read = Column(Boolean, default=False, comment='是否已读')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cs_mention_notifications_to_agent_id', 'to_agent_id'),
        Index('idx_cs_mention_notifications_from_agent_id', 'from_agent_id'),
        Index('idx_cs_mention_notifications_session_id', 'session_id'),
        Index('idx_cs_mention_notifications_is_read', 'is_read'),
    )


# ============================================================
# Part 44: 第34层 - 调度引擎深度优化 (Scheduler Engine Optimization)
# 22 tables → 568 models total
# ============================================================

# =============================================================================
# A. AgentRegistry（服务注册中心）— 3表
# =============================================================================

class SchedulerAgentInstance(Base):
    """
    调度器Agent实例表
    记录注册到调度中心的每个Agent实例信息
    """
    __tablename__ = 'scheduler_agent_instances'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    instance_id = Column(String(64), unique=True, nullable=False, comment='实例唯一标识')
    agent_type = Column(String(50), nullable=False, comment='Agent类型：scheduler/worker/gateway')
    host = Column(String(128), nullable=False, comment='主机地址')
    port = Column(Integer, nullable=False, comment='端口号')
    status = Column(String(20), default='registering', comment='状态：registering/online/offline/draining/decommissioned')
    tags = Column(JSON, comment='标签JSON数组')
    metadata = Column(JSON, comment='元数据JSON')
    registered_at = Column(DateTime, default=datetime.utcnow, comment='注册时间')
    last_heartbeat = Column(DateTime, comment='最后心跳时间')
    ttl_sec = Column(Integer, default=30, comment='存活时间（秒）')
    version = Column(String(20), comment='Agent版本号')

    # 关系定义
    heartbeat_history = relationship('AgentHeartbeatHistory', back_populates='instance', lazy='dynamic')
    tag_indexes = relationship('AgentTagIndex', back_populates='instance', lazy='dynamic')
    load_snapshots = relationship('AgentLoadSnapshot', back_populates='instance', lazy='dynamic')
    weight_adjustment_logs = relationship('WeightAdjustmentLog', back_populates='instance', lazy='dynamic')
    dispatch_records_as_target = relationship('TaskDispatchRecord', back_populates='target_instance', foreign_keys='TaskDispatchRecord.target_instance_id', lazy='dynamic')
    graceful_drain_states = relationship('GracefulDrainState', back_populates='instance', lazy='dynamic')
    lifecycle_events = relationship('AgentLifecycleEvent', back_populates='instance', lazy='dynamic')

    __table_args__ = (
        Index('idx_scheduler_agent_instances_type', 'agent_type'),
        Index('idx_scheduler_agent_instances_status', 'status'),
        Index('idx_scheduler_agent_instances_host_port', 'host', 'port'),
        Index('idx_scheduler_agent_instances_last_heartbeat', 'last_heartbeat'),
    )


class AgentHeartbeatHistory(Base):
    """
    Agent心跳历史表
    记录每个Agent的心跳历史数据，用于健康检查和趋势分析
    """
    __tablename__ = 'agent_heartbeat_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    history_id = Column(String(36), unique=True, nullable=False, comment='心跳记录唯一标识')
    instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='关联的实例ID')
    heartbeat_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='心跳时间')
    status = Column(String(20), nullable=False, comment='心跳状态：ok/warning/critical/timeout')
    cpu_usage = Column(Float, comment='CPU使用率（百分比）')
    memory_usage = Column(Float, comment='内存使用率（百分比）')
    queue_length = Column(Integer, default=0, comment='当前队列长度')
    response_time_ms = Column(Float, comment='响应时间（毫秒）')
    metadata = Column(JSON, comment='扩展元数据JSON')

    # 关系定义
    instance = relationship('SchedulerAgentInstance', back_populates='heartbeat_history')

    __table_args__ = (
        Index('idx_agent_heartbeat_history_instance', 'instance_id'),
        Index('idx_agent_heartbeat_history_time', 'heartbeat_time'),
        Index('idx_agent_heartbeat_history_instance_time', 'instance_id', 'heartbeat_time'),
    )


class AgentTagIndex(Base):
    """
    Agent标签索引表
    用于快速查找具有特定标签的Agent实例
    """
    __tablename__ = 'agent_tag_index'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tag_id = Column(Integer, unique=True, nullable=False, comment='标签索引ID')
    instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='关联的实例ID')
    tag_key = Column(String(100), nullable=False, comment='标签键')
    tag_value = Column(String(256), nullable=False, comment='标签值')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系定义
    instance = relationship('SchedulerAgentInstance', back_populates='tag_indexes')

    __table_args__ = (
        Index('idx_agent_tag_index_kv', 'tag_key', 'tag_value'),
        Index('idx_agent_tag_index_instance', 'instance_id'),
        UniqueConstraint('instance_id', 'tag_key', 'tag_value', name='uq_agent_tag_instance_kv'),
    )


# =============================================================================
# B. LoadAwareScheduler（负载感知调度）— 4表
# =============================================================================

class AgentLoadSnapshot(Base):
    """
    Agent负载快照表
    定期采集的Agent负载数据，用于负载均衡决策
    """
    __tablename__ = 'agent_load_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照唯一标识')
    instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='关联的实例ID')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间戳')
    cpu_percent = Column(Float, nullable=False, comment='CPU使用百分比')
    memory_percent = Column(Float, nullable=False, comment='内存使用百分比')
    queue_length = Column(Integer, default=0, comment='当前队列长度')
    avg_response_ms = Column(Float, default=0.0, comment='平均响应时间（毫秒）')
    active_tasks = Column(Integer, default=0, comment='活跃任务数')
    load_score = Column(Float, default=0.0, comment='综合负载评分（0-100）')
    effective_weight = Column(Float, default=1.0, comment='有效权重值')

    # 关系定义
    instance = relationship('SchedulerAgentInstance', back_populates='load_snapshots')

    __table_args__ = (
        Index('idx_agent_load_snapshots_instance', 'instance_id'),
        Index('idx_agent_load_snapshots_timestamp', 'timestamp'),
        Index('idx_agent_load_snapshots_score', 'load_score'),
    )


class WeightAdjustmentLog(Base):
    """
    权重调整日志表
    记录基于负载感知的权重调整历史
    """
    __tablename__ = 'weight_adjustment_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    log_id = Column(String(36), unique=True, nullable=False, comment='日志唯一标识')
    instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='关联的实例ID')
    adjustment_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='调整时间')
    old_weight = Column(Float, nullable=False, comment='调整前权重')
    new_weight = Column(Float, nullable=False, comment='调整后权重')
    reason = Column(String(256), nullable=False, comment='调整原因')
    decay_factor = Column(Float, default=0.95, comment='衰减因子')
    recovery_factor = Column(Float, default=1.05, comment='恢复因子')

    # 关系定义
    instance = relationship('SchedulerAgentInstance', back_populates='weight_adjustment_logs')

    __table_args__ = (
        Index('idx_weight_adjustment_logs_instance', 'instance_id'),
        Index('idx_weight_adjustment_logs_time', 'adjustment_time'),
    )


class TaskDispatchRecord(Base):
    """
    任务调度记录表
    记录每个任务的调度详情和执行结果
    """
    __tablename__ = 'task_dispatch_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dispatch_id = Column(String(36), unique=True, nullable=False, comment='调度记录唯一标识')
    task_id = Column(String(64), nullable=False, comment='任务ID')
    source_agent_id = Column(String(64), comment='发起调度的源Agent ID')
    target_instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='目标实例ID')
    priority = Column(Integer, default=5, comment='优先级（1-10，数字越大优先级越高）')
    dispatch_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='调度时间')
    complete_time = Column(DateTime, comment='完成时间')
    total_processing_time_ms = Column(Float, comment='总处理时间（毫秒）')
    result_status = Column(String(20), comment='结果状态：success/failed/timeout/cancelled/retried')
    retry_count = Column(Integer, default=0, comment='重试次数')
    error_message = Column(Text, comment='错误信息')

    # 关系定义
    target_instance = relationship('SchedulerAgentInstance', back_populates='dispatch_records_as_target', foreign_keys=[target_instance_id])

    __table_args__ = (
        Index('idx_task_dispatch_records_task', 'task_id'),
        Index('idx_task_dispatch_records_target', 'target_instance_id'),
        Index('idx_task_dispatch_records_priority', 'priority'),
        Index('idx_task_dispatch_records_status', 'result_status'),
        Index('idx_task_dispatch_records_dispatch_time', 'dispatch_time'),
    )


class DispatchDecisionLog(Base):
    """
    调度决策日志表
    记录每次调度决策的详细信息，用于分析和优化
    """
    __tablename__ = 'dispatch_decision_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    decision_id = Column(String(36), unique=True, nullable=False, comment='决策唯一标识')
    task_id = Column(String(64), nullable=False, comment='关联的任务ID')
    candidate_instances = Column(JSON, comment='候选实例列表JSON')
    selected_instance = Column(String(64), comment='最终选中的实例ID')
    selection_reason = Column(Text, comment='选择原因说明')
    algorithm_used = Column(String(50), comment='使用的算法：round_robin/least_connections/random/weighted/hash')
    load_scores = Column(JSON, comment='各候选实例的负载评分JSON')
    decision_time_ms = Column(Float, comment='决策耗时（毫秒）')

    __table_args__ = (
        Index('idx_dispatch_decision_logs_task', 'task_id'),
        Index('idx_dispatch_decision_logs_selected', 'selected_instance'),
        Index('idx_dispatch_decision_logs_algorithm', 'algorithm_used'),
    )


# =============================================================================
# C. MultiLevelPriorityQueue（多级优先级队列）— 3表
# =============================================================================

class PriorityQueueEntry(Base):
    """
    优先级队列条目表
    管理多级优先级队列中的任务条目
    """
    __tablename__ = 'priority_queue_entries'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    entry_id = Column(String(36), unique=True, nullable=False, comment='条目唯一标识')
    task_id = Column(String(64), nullable=False, comment='关联的任务ID')
    priority_level = Column(Integer, nullable=False, comment='优先级：0-高/1-中/2-低')
    enqueue_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='入队时间')
    vip_flag = Column(Boolean, default=False, comment='VIP标记')
    original_priority = Column(Integer, comment='原始优先级')
    promoted_count = Column(Integer, default=0, comment='被提升次数')
    promote_times = Column(JSON, comment='提升时间记录JSON数组')
    cancelled = Column(Boolean, default=False, comment='是否已取消')
    completed = Column(Boolean, default=False, comment='是否已完成')

    # 关系定义
    promotion_logs = relationship('PriorityPromotionLog', back_populates='entry', lazy='dynamic')

    __table_args__ = (
        Index('idx_priority_queue_entries_task', 'task_id'),
        Index('idx_priority_queue_entries_level', 'priority_level'),
        Index('idx_priority_queue_entries_enqueue_time', 'enqueue_time'),
        Index('idx_priority_queue_entries_vip', 'vip_flag'),
        Index('idx_priority_queue_entries_pending', 'cancelled', 'completed'),
    )


class PriorityPromotionLog(Base):
    """
    优先级提升日志表
    记录任务优先级的变更历史
    """
    __tablename__ = 'priority_promotion_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    promotion_id = Column(String(36), unique=True, nullable=False, comment='提升记录唯一标识')
    entry_id = Column(String(36), ForeignKey('priority_queue_entries.entry_id'), nullable=False, comment='关联的队列条目ID')
    from_level = Column(Integer, nullable=False, comment='原优先级')
    to_level = Column(Integer, nullable=False, comment='新优先级')
    promotion_reason = Column(String(256), nullable=False, comment='提升原因')
    wait_duration_sec = Column(Float, comment='等待时长（秒）')
    promotion_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='提升时间')

    # 关系定义
    entry = relationship('PriorityQueueEntry', back_populates='promotion_logs')

    __table_args__ = (
        Index('idx_priority_promotion_logs_entry', 'entry_id'),
        Index('idx_priority_promotion_logs_time', 'promotion_time'),
        Index('idx_priority_promotion_logs_from_to', 'from_level', 'to_level'),
    )


class QueueStatisticsSnapshot(Base):
    """
    队列统计快照表
    定期记录各级别队列的统计指标
    """
    __tablename__ = 'queue_statistics_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stats_id = Column(String(36), unique=True, nullable=False, comment='统计快照唯一标识')
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间')
    high_count = Column(Integer, default=0, comment='高优先级队列数量')
    medium_count = Column(Integer, default=0, comment='中优先级队列数量')
    low_count = Column(Integer, default=0, comment='低优先级队列数量')
    total_pending = Column(Integer, default=0, comment='待处理总数')
    avg_wait_high_ms = Column(Float, default=0.0, comment='高优先级平均等待时间（毫秒）')
    avg_wait_medium_ms = Column(Float, default=0.0, comment='中优先级平均等待时间（毫秒）')
    avg_wait_low_ms = Column(Float, default=0.0, comment='低优先级平均等待时间（毫秒）')

    __table_args__ = (
        Index('idx_queue_statistics_snapshots_time', 'snapshot_time'),
    )


# =============================================================================
# D. PredictivePrewarmer（预测性预热）— 3表
# =============================================================================

class TrafficPatternRecord(Base):
    """
    流量模式记录表
    存储历史流量模式数据，用于预测性分析
    """
    __tablename__ = 'traffic_pattern_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(36), unique=True, nullable=False, comment='记录唯一标识')
    hour_of_day = Column(Integer, nullable=False, comment='小时（0-23）')
    day_of_week = Column(Integer, nullable=False, comment='星期几（0-6，0为周一）')
    avg_task_count = Column(Float, default=0.0, comment='平均任务数')
    peak_task_count = Column(Integer, default=0, comment='峰值任务数')
    min_task_count = Column(Integer, default=0, comment='最小任务数')
    std_deviation = Column(Float, default=0.0, comment='标准差')
    record_date = Column(Date, comment='记录日期')
    is_holiday = Column(Boolean, default=False, comment='是否节假日')

    __table_args__ = (
        Index('idx_traffic_pattern_records_hour_day', 'hour_of_day', 'day_of_week'),
        Index('idx_traffic_pattern_records_date', 'record_date'),
        Index('idx_traffic_pattern_records_holiday', 'is_holiday'),
    )


class PrewarmPrediction(Base):
    """
    预热预测记录表
    存储预测模型的输出和实际对比数据
    """
    __tablename__ = 'prewarm_predictions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    prediction_id = Column(String(36), unique=True, nullable=False, comment='预测记录唯一标识')
    prediction_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='预测时间')
    predicted_hour = Column(Integer, nullable=False, comment='预测的小时')
    predicted_load = Column(Float, nullable=False, comment='预测的负载量')
    confidence_score = Column(Float, comment='置信度分数（0-1）')
    prewarm_triggered = Column(Boolean, default=False, comment='是否触发了预热')
    actual_load = Column(Float, comment='实际负载量')
    prediction_error_pct = Column(Float, comment='预测误差百分比')

    # 关系定义
    execution_logs = relationship('PrewarmExecutionLog', back_populates='prediction', lazy='dynamic')

    __table_args__ = (
        Index('idx_prewarm_predictions_time', 'prediction_time'),
        Index('idx_prewarm_predictions_predicted_hour', 'predicted_hour'),
        Index('idx_prewarm_predictions_triggered', 'prewarm_triggered'),
    )


class PrewarmExecutionLog(Base):
    """
    预热执行日志表
    记录每次预热操作的详细执行情况
    """
    __tablename__ = 'prewarm_execution_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    execution_id = Column(String(36), unique=True, nullable=False, comment='执行日志唯一标识')
    prediction_id = Column(String(36), ForeignKey('prewarm_predictions.prediction_id'), nullable=False, comment='关联的预测记录ID')
    execution_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='执行时间')
    agents_prewarmed = Column(Integer, default=0, comment='预热的Agent数量')
    tasks_prepared = Column(Integer, default=0, comment='准备的任务数量')
    duration_ms = Column(Float, comment='执行耗时（毫秒）')
    success = Column(Boolean, default=False, comment='是否成功')
    error_detail = Column(Text, comment='错误详情')

    # 关系定义
    prediction = relationship('PrewarmPrediction', back_populates='execution_logs')

    __table_args__ = (
        Index('idx_prewarm_execution_logs_prediction', 'prediction_id'),
        Index('idx_prewarm_execution_logs_time', 'execution_time'),
        Index('idx_prewarm_execution_logs_success', 'success'),
    )


# =============================================================================
# E. HPAGracefulScaler（弹性伸缩）— 4表
# =============================================================================

class HPAScaleEvent(Base):
    """
    HPA伸缩事件表
    记录水平Pod自动伸缩的所有事件
    """
    __tablename__ = 'hpa_scale_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(36), unique=True, nullable=False, comment='事件唯一标识')
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='事件时间')
    direction = Column(String(10), nullable=False, comment='伸缩方向：up/down')
    current_replicas = Column(Integer, nullable=False, comment='当前副本数')
    desired_replicas = Column(Integer, nullable=False, comment='期望副本数')
    trigger_metric = Column(String(50), nullable=False, comment='触发指标：cpu/memory/custom')
    trigger_value = Column(Float, nullable=False, comment='触发时的指标值')
    threshold = Column(Float, nullable=False, comment='阈值')
    cooldown_remaining = Column(Integer, default=0, comment='剩余冷却时间（秒）')
    scale_decision_id = Column(String(36), ForeignKey('scale_decision_records.decision_id'), comment='关联的伸缩决策ID')

    # 关系定义
    scale_decision = relationship('ScaleDecisionRecord')

    __table_args__ = (
        Index('idx_hpa_scale_events_time', 'event_time'),
        Index('idx_hpa_scale_events_direction', 'direction'),
        Index('idx_hpa_scale_events_metric', 'trigger_metric'),
    )


class ScaleDecisionRecord(Base):
    """
    伸缩决策记录表
    记录伸缩决策的完整上下文和审批信息
    """
    __tablename__ = 'scale_decision_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    decision_id = Column(String(36), unique=True, nullable=False, comment='决策唯一标识')
    decision_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='决策时间')
    direction = Column(String(10), nullable=False, comment='伸缩方向：up/down')
    from_replicas = Column(Integer, nullable=False, comment='伸缩前副本数')
    to_replicas = Column(Integer, nullable=False, comment='伸缩后副本数')
    reason = Column(Text, nullable=False, comment='决策原因')
    metric_snapshot_id = Column(String(36), comment='关联的指标快照ID')
    approved = Column(Boolean, default=True, comment='是否已审批通过')
    approver = Column(String(64), comment='审批人')

    # 关系定义
    scale_events = relationship('HPAScaleEvent', back_populates='scale_decision')

    __table_args__ = (
        Index('idx_scale_decision_records_time', 'decision_time'),
        Index('idx_scale_decision_records_direction', 'direction'),
        Index('idx_scale_decision_records_approved', 'approved'),
    )


class GracefulDrainState(Base):
    """
    优雅排空状态表
    追踪实例在缩容过程中的排空状态
    """
    __tablename__ = 'graceful_drain_states'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    drain_id = Column(String(36), unique=True, nullable=False, comment='排空记录唯一标识')
    instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='关联的实例ID')
    drain_start_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='排空开始时间')
    drain_end_time = Column(DateTime, comment='排空结束时间')
    status = Column(String(20), default='draining', comment='状态：draining/completed/timeout/force_terminated')
    initial_queue_length = Column(Integer, default=0, comment='初始队列长度')
    remaining_tasks = Column(Integer, default=0, comment='剩余任务数')
    max_wait_sec = Column(Integer, default=300, comment='最大等待时间（秒）')
    timeout_occurred = Column(Boolean, default=False, comment='是否超时')
    force_terminated = Column(Boolean, default=False, comment='是否被强制终止')

    # 关系定义
    instance = relationship('SchedulerAgentInstance', back_populates='graceful_drain_states')

    __table_args__ = (
        Index('idx_graceful_drain_states_instance', 'instance_id'),
        Index('idx_graceful_drain_states_status', 'status'),
        Index('idx_graceful_drain_states_start_time', 'drain_start_time'),
    )


class AgentLifecycleEvent(Base):
    """
    Agent生命周期事件表
    记录Agent从注册到下线的所有生命周期事件
    """
    __tablename__ = 'agent_lifecycle_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    lifecycle_id = Column(String(36), unique=True, nullable=False, comment='生命周期事件唯一标识')
    instance_id = Column(String(64), ForeignKey('scheduler_agent_instances.instance_id'), nullable=False, comment='关联的实例ID')
    event_type = Column(String(30), nullable=False, comment='事件类型：registered/heartbeat_missed/drain_started/drain_completed/decommissioned/error')
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='事件时间')
    details = Column(JSON, comment='事件详情JSON')
    previous_state = Column(String(20), comment='前一状态')
    new_state = Column(String(20), comment='新状态')
    triggered_by = Column(String(64), comment='触发者（系统/人工/自动）')

    # 关系定义
    instance = relationship('SchedulerAgentInstance', back_populates='lifecycle_events')

    __table_args__ = (
        Index('idx_agent_lifecycle_events_instance', 'instance_id'),
        Index('idx_agent_lifecycle_events_type', 'event_type'),
        Index('idx_agent_lifecycle_events_time', 'event_time'),
        Index('idx_agent_lifecycle_events_state_change', 'previous_state', 'new_state'),
    )


# =============================================================================
# F. SchedulerMetricsExporter（调度指标导出）— 2表
# =============================================================================

class MetricSnapshot(Base):
    """
    指标快照表
    定期采集的全局调度器性能指标快照
    """
    __tablename__ = 'metric_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照唯一标识')
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间')
    total_agents = Column(Integer, default=0, comment='总Agent数')
    online_agents = Column(Integer, default=0, comment='在线Agent数')
    avg_load_score = Column(Float, default=0.0, comment='平均负载评分')
    avg_response_ms = Column(Float, default=0.0, comment='平均响应时间（毫秒）')
    p99_response_ms = Column(Float, default=0.0, comment='P99响应时间（毫秒）')
    queue_depth = Column(Integer, default=0, comment='队列深度')
    dispatch_rate = Column(Float, default=0.0, comment='调度速率（每秒）')
    error_rate = Column(Float, default=0.0, comment='错误率（百分比）')
    cpu_avg = Column(Float, default=0.0, comment='平均CPU使用率')
    mem_avg = Column(Float, default=0.0, comment='平均内存使用率')

    # 关系定义
    alert_evaluations = relationship('AlertRuleEvaluation', back_populates='snapshot', lazy='dynamic')

    __table_args__ = (
        Index('idx_metric_snapshots_time', 'snapshot_time'),
        Index('idx_metric_snapshots_online', 'online_agents'),
    )


class AlertRuleEvaluation(Base):
    """
    告警规则评估表
    记录告警规则的评估结果和触发动作
    """
    __tablename__ = 'alert_rule_evaluations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    evaluation_id = Column(String(36), unique=True, nullable=False, comment='评估记录唯一标识')
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    snapshot_id = Column(String(36), ForeignKey('metric_snapshots.snapshot_id'), nullable=False, comment='关联的指标快照ID')
    evaluation_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='评估时间')
    fired = Column(Boolean, default=False, comment='是否触发告警')
    severity = Column(String(20), comment='严重级别：info/warning/critical/emergency')
    current_value = Column(Float, comment='当前值')
    threshold_value = Column(Float, comment='阈值')
    message = Column(Text, comment='告警消息')
    alert_action_taken = Column(String(100), comment='采取的告警动作')

    # 关系定义
    snapshot = relationship('MetricSnapshot', back_populates='alert_evaluations')

    __table_args__ = (
        Index('idx_alert_rule_evaluations_rule', 'rule_name'),
        Index('idx_alert_rule_evaluations_snapshot', 'snapshot_id'),
        Index('idx_alert_rule_evaluations_fired', 'fired'),
        Index('idx_alert_rule_evaluations_severity', 'severity'),
        Index('idx_alert_rule_evaluations_time', 'evaluation_time'),
    )


# =============================================================================
# G. OptimizedSchedulerOrchestrator（调度编排器）— 3表
# =============================================================================

class OrchestrationCycleLog(Base):
    """
    编排周期日志表
    记录每个调度编排周期的执行情况
    """
    __tablename__ = 'orchestration_cycle_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cycle_id = Column(String(36), unique=True, nullable=False, comment='周期唯一标识')
    cycle_start_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='周期开始时间')
    cycle_end_time = Column(DateTime, comment='周期结束时间')
    cycle_type = Column(String(30), nullable=False, comment='周期类型：full/incremental/emergency/maintenance')
    tasks_submitted = Column(Integer, default=0, comment='提交的任务数')
    tasks_dispatched = Column(Integer, default=0, comment='已调度的任务数')
    agents_considered = Column(Integer, default=0, comment='考虑的Agent数')
    errors_count = Column(Integer, default=0, comment='错误数')
    duration_ms = Column(Float, comment='周期持续时间（毫秒）')

    __table_args__ = (
        Index('idx_orchestration_cycle_logs_start_time', 'cycle_start_time'),
        Index('idx_orchestration_cycle_logs_type', 'cycle_type'),
        Index('idx_orchestration_cycle_logs_duration', 'duration_ms'),
    )


class OptimizationImpactReport(Base):
    """
    优化影响报告表
    记录优化措施的实际效果对比
    """
    __tablename__ = 'optimization_impact_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(36), unique=True, nullable=False, comment='报告唯一标识')
    report_period_start = Column(DateTime, nullable=False, comment='报告期开始时间')
    report_period_end = Column(DateTime, nullable=False, comment='报告期结束时间')
    p99_before_ms = Column(Float, comment='优化前P99响应时间（毫秒）')
    p99_after_ms = Column(Float, comment='优化后P99响应时间（毫秒）')
    throughput_before = Column(Float, comment='优化前吞吐量')
    throughput_after = Column(Float, comment='优化后吞吐量')
    utilization_before = Column(Float, comment='优化前资源利用率')
    utilization_after = Column(Float, comment='优化后资源利用率')
    recommendations = Column(JSON, comment='改进建议JSON数组')

    __table_args__ = (
        Index('idx_optimization_impact_reports_period', 'report_period_start', 'report_period_end'),
    )


class SchedulerConfigHistory(Base):
    """
    调度配置历史表
    记录调度器配置的所有变更历史
    """
    __tablename__ = 'scheduler_config_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    config_history_id = Column(String(36), unique=True, nullable=False, comment='配置历史唯一标识')
    config_id = Column(String(64), nullable=False, comment='配置项ID')
    changed_by = Column(String(64), nullable=False, comment='修改人')
    change_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment='修改时间')
    field_name = Column(String(100), nullable=False, comment='字段名称')
    old_value = Column(Text, comment='旧值')
    new_value = Column(Text, comment='新值')
    change_reason = Column(String(256), comment='变更原因')

    __table_args__ = (
        Index('idx_scheduler_config_history_config', 'config_id'),
        Index('idx_scheduler_config_history_field', 'field_name'),
        Index('idx_scheduler_config_history_time', 'change_time'),
        Index('idx_scheduler_config_history_changer', 'changed_by'),
    )


# =============================================================================
# Part 45 — 第35层全面深化高质量开发优化（39个表）
# =============================================================================
# 本部分包含13个优化计划的深化实现，涵盖记忆系统、交互引擎、数据采集、
# 量化分析、安全防御、高可用、开发者生态、移动端、国际化、合规审计、
# 成本优化、用户增长、AI自我进化等核心领域。
#
# 计划清单：
# Plan 2: 海马体记忆系统优化 (3表)
# Plan 3: 人格化交互引擎升级 (3表)
# Plan 4: 多源数据采集增强 (3表)
# Plan 5: 量化分析模型提升 (3表)
# Plan 6: 安全防御体系升级 (3表)
# Plan 7: 高可用灾备体系 (3表)
# Plan 8: 开发者生态平台 (3表)
# Plan 9: 移动端App重构 (3表)
# Plan 10: 国际化多语言 (3表)
# Plan 11: 合规审计隐私 (3表)
# Plan 12: 成本优化资源调度 (3表)
# Plan 13: 用户增长运营系统 (3表)
# Plan 14: AI自我进化平台 (3表)
# =============================================================================


# =============================================================================
# Plan 2: 海马体记忆系统优化 — 3表
# =============================================================================

class MemoryShard(Base):
    """
    记忆分片表
    基于海马体架构的记忆分片存储，支持高效的向量索引和检索
    """
    __tablename__ = 'memory_shards'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    shard_id = Column(String(36), unique=True, nullable=False, comment='分片唯一标识')
    user_hash_prefix = Column(String(16), nullable=False, comment='用户哈希前缀，用于分片路由')
    index_type = Column(String(50), nullable=False, comment='索引类型：ivf_flat/ivf_pq/hnsw')
    nlist = Column(Integer, default=100, comment='IVF聚类中心数')
    nprobe = Column(Integer, default=10, comment='探测的聚类数')
    memory_count = Column(Integer, default=0, comment='当前分片内记忆数量')
    cache_size = Column(Float, default=0.0, comment='缓存大小（MB）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系定义
    forgetting_records = relationship('MemoryForgettingRecord', back_populates='shard', lazy='dynamic')
    compressed_memories = relationship('CompressedMemory', back_populates='shard', lazy='dynamic')

    __table_args__ = (
        Index('idx_memory_shards_hash_prefix', 'user_hash_prefix'),
        Index('idx_memory_shards_index_type', 'index_type'),
        Index('idx_memory_shards_count', 'memory_count'),
    )


class MemoryForgettingRecord(Base):
    """
    记忆遗忘记录表
    基于艾宾浩斯遗忘曲线的记忆衰减追踪记录
    """
    __tablename__ = 'memory_forgetting_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(36), unique=True, nullable=False, comment='记录唯一标识')
    memory_id = Column(String(64), nullable=False, comment='关联的记忆ID')
    shard_id = Column(String(36), ForeignKey('memory_shards.shard_id'), nullable=False, comment='所属分片ID')
    forget_score = Column(Float, default=0.0, comment='遗忘评分（0-1，越高越应遗忘）')
    age_hours = Column(Float, default=0.0, comment='记忆年龄（小时）')
    should_forget = Column(Boolean, default=False, comment='是否应该被遗忘')
    ebbinghaus_retention = Column(Float, default=1.0, comment='艾宾浩斯保留率（0-1）')
    forgotten_at = Column(DateTime, comment='实际遗忘时间')
    reason = Column(String(256), comment='遗忘原因')

    # 关系定义
    shard = relationship('MemoryShard', back_populates='forgetting_records')

    __table_args__ = (
        Index('idx_memory_forget_records_memory', 'memory_id'),
        Index('idx_memory_forget_records_shard', 'shard_id'),
        Index('idx_memory_forget_records_score', 'forget_score'),
        Index('idx_memory_forget_records_age', 'age_hours'),
        Index('idx_memory_forget_records_should', 'should_forget'),
    )


class CompressedMemory(Base):
    """
    压缩记忆存储表
    长期记忆的高效压缩存储，支持多种压缩算法
    """
    __tablename__ = 'compressed_memories'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(36), unique=True, nullable=False, comment='记录唯一标识')
    original_id = Column(String(64), nullable=False, comment='原始记忆ID')
    user_id = Column(String(64), nullable=False, comment='关联的用户ID')
    shard_id = Column(String(36), ForeignKey('memory_shards.shard_id'), nullable=False, comment='所属分片ID')
    compressed_data = Column(Text, nullable=False, comment='压缩后的二进制数据（Base64编码）')
    original_size = Column(Integer, nullable=False, comment='原始大小（字节）')
    compressed_size = Column(Integer, nullable=False, comment='压缩后大小（字节）')
    compression_algo = Column(String(50), nullable=False, comment='压缩算法：lz4/zstd/gzip/brotli')
    importance_score = Column(Float, default=0.5, comment='重要性评分（0-1）')
    storage_type = Column(String(20), default='cold', comment='存储类型：hot/warm/cold/archive')
    compressed_at = Column(DateTime, default=datetime.utcnow, comment='压缩时间')

    # 关系定义
    shard = relationship('MemoryShard', back_populates='compressed_memories')

    __table_args__ = (
        Index('idx_compressed_memories_original', 'original_id'),
        Index('idx_compressed_memories_user', 'user_id'),
        Index('idx_compressed_memories_shard', 'shard_id'),
        Index('idx_compressed_memories_storage', 'storage_type'),
        Index('idx_compressed_memories_importance', 'importance_score'),
    )


# =============================================================================
# Plan 3: 人格化交互引擎升级 — 3表
# =============================================================================

class EmotionDetectionLog(Base):
    """
    情感检测日志表
    记录用户输入的情感分析结果，用于人格化响应调整
    """
    __tablename__ = 'emotion_detection_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    log_id = Column(String(36), unique=True, nullable=False, comment='日志唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    text = Column(Text, nullable=False, comment='待分析的文本内容')
    primary_emotion = Column(String(50), nullable=False, comment='主要情感类型：joy/sadness/anger/fear/surprise/disgust/neutral')
    confidence = Column(Float, default=0.0, comment='检测置信度（0-1）')
    all_scores_json = Column(JSON, comment='所有情感维度得分JSON')
    processing_ms = Column(Integer, default=0, comment='处理耗时（毫秒）')
    detected_at = Column(DateTime, default=datetime.utcnow, comment='检测时间')

    # 关系定义
    empathy_sessions = relationship('EmpathySession', back_populates='emotion_log', lazy='dynamic')

    __table_args__ = (
        Index('idx_emotion_logs_user', 'user_id'),
        Index('idx_emotion_logs_emotion', 'primary_emotion'),
        Index('idx_emotion_logs_confidence', 'confidence'),
        Index('idx_emotion_logs_detected_at', 'detected_at'),
    )


class PersonalityProfile(Base):
    """
    人格画像表
    存储用户的个性化人格配置参数
    """
    __tablename__ = 'personality_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    profile_id = Column(String(36), unique=True, nullable=False, comment='画像唯一标识')
    user_id = Column(String(64), unique=True, nullable=False, comment='关联的用户ID')
    dimensions_json = Column(JSON, nullable=False, comment='人格维度JSON（大五性格等）')
    zhou_yu_ratio = Column(Float, default=0.5, comment='周瑜风格占比（0-1）')
    lu_xun_ratio = Column(Float, default=0.5, comment='鲁迅风格占比（0-1）')
    custom_params_json = Column(JSON, comment='自定义参数JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系定义
    empathy_sessions = relationship('EmpathySession', back_populates='personality_profile', lazy='dynamic')

    __table_args__ = (
        Index('idx_personality_profiles_user', 'user_id'),
        Index('idx_personality_profiles_zhou_yu', 'zhou_yu_ratio'),
        Index('idx_personality_profiles_lu_xun', 'lu_xun_ratio'),
    )


class EmpathySession(Base):
    """
    共情会话表
    记录基于情感检测的共情式交互会话
    """
    __tablename__ = 'empathy_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(36), unique=True, nullable=False, comment='会话唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    emotion_log_id = Column(String(36), ForeignKey('emotion_detection_logs.log_id'), comment='关联的情感检测日志ID')
    profile_id = Column(String(36), ForeignKey('personality_profiles.profile_id'), comment='关联的人格画像ID')
    detected_emotion = Column(String(50), nullable=False, comment='检测到的情感')
    comfort_strategy = Column(String(100), comment='采用的安慰策略')
    associated_memories_json = Column(JSON, comment='关联的相关记忆JSON数组')
    response_text = Column(Text, comment='生成的共情响应文本')
    effectiveness_score = Column(Float, comment='效果评分（0-1，由后续反馈计算）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系定义
    emotion_log = relationship('EmotionDetectionLog', back_populates='empathy_sessions')
    personality_profile = relationship('PersonalityProfile', back_populates='empathy_sessions')

    __table_args__ = (
        Index('idx_empathy_sessions_user', 'user_id'),
        Index('idx_empathy_sessions_emotion', 'detected_emotion'),
        Index('idx_empathy_sessions_strategy', 'comfort_strategy'),
        Index('idx_empathy_sessions_created', 'created_at'),
    )


# =============================================================================
# Plan 4: 多源数据采集增强 — 3表
# =============================================================================

class AntiCrawlStrategy(Base):
    """
    反爬策略配置表
    管理各数据源的防反爬策略配置
    """
    __tablename__ = 'anti_crawl_strategies'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    strategy_id = Column(String(36), unique=True, nullable=False, comment='策略唯一标识')
    source_name = Column(String(100), nullable=False, comment='数据源名称')
    strategies_json = Column(JSON, nullable=False, comment='策略配置JSON（代理池、请求头轮换等）')
    proxy_pool_size = Column(Integer, default=10, comment='代理池大小')
    header_rotation_sec = Column(Integer, default=300, comment='请求头轮换间隔（秒）')
    captcha_service = Column(String(50), comment='验证码服务提供商')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    cooldown_sec = Column(Integer, default=60, comment='冷却时间（秒）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_anti_crawl_source', 'source_name'),
        Index('idx_anti_crawl_captcha', 'captcha_service'),
    )


class DataCleaningRule(Base):
    """
    数据清洗规则表
    定义可复用的数据清洗规则脚本
    """
    __tablename__ = 'data_cleaning_rules'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_id = Column(String(36), unique=True, nullable=False, comment='规则唯一标识')
    name = Column(String(100), nullable=False, comment='规则名称')
    script = Column(Text, nullable=False, comment='清洗脚本代码')
    language = Column(String(20), default='python', comment='脚本语言：python/sql/javascript')
    state = Column(String(20), default='active', comment='状态：active/disabled/archived')
    version = Column(Integer, default=1, comment='版本号')
    created_by = Column(String(64), comment='创建者')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系定义
    executions = relationship('CleaningRuleExecution', back_populates='rule', lazy='dynamic')

    __table_args__ = (
        Index('idx_data_cleaning_rules_name', 'name'),
        Index('idx_data_cleaning_rules_state', 'state'),
        Index('idx_data_cleaning_rules_language', 'language'),
    )


class CleaningRuleExecution(Base):
    """
    规则执行记录表
    追踪数据清洗规则的每次执行情况
    """
    __tablename__ = 'cleaning_rule_executions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    execution_id = Column(String(36), unique=True, nullable=False, comment='执行记录唯一标识')
    rule_id = Column(String(36), ForeignKey('data_cleaning_rules.rule_id'), nullable=False, comment='执行的规则ID')
    rule_name = Column(String(100), nullable=False, comment='规则名称（冗余存储便于查询）')
    input_count = Column(Integer, default=0, comment='输入记录数')
    output_count = Column(Integer, default=0, comment='输出记录数')
    error_count = Column(Integer, default=0, comment='错误数')
    execution_ms = Column(Integer, default=0, comment='执行耗时（毫秒）')
    status = Column(String(20), default='success', comment='状态：success/partial_failure/failed')
    executed_at = Column(DateTime, default=datetime.utcnow, comment='执行时间')

    # 关系定义
    rule = relationship('DataCleaningRule', back_populates='executions')

    __table_args__ = (
        Index('idx_cleaning_executions_rule', 'rule_id'),
        Index('idx_cleaning_executions_status', 'status'),
        Index('idx_cleaning_executions_executed_at', 'executed_at'),
    )


# =============================================================================
# Plan 5: 量化分析模型提升 — 3表
# =============================================================================

class RealtimeFactorSnapshot(Base):
    """
    实时因子快照表
    存储量化因子的实时快照数据
    """
    __tablename__ = 'realtime_factor_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照唯一标识')
    factor_name = Column(String(100), nullable=False, comment='因子名称')
    value = Column(Float, nullable=False, comment='因子值')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment='快照时间戳')
    source_data_id = Column(String(64), comment='原始数据来源ID')
    computation_ms = Column(Integer, default=0, comment='计算耗时（毫秒）')
    confidence = Column(Float, default=1.0, comment='置信度（0-1）')

    __table_args__ = (
        Index('idx_realtime_factors_name', 'factor_name'),
        Index('idx_realtime_factors_timestamp', 'timestamp'),
        Index('idx_realtime_factors_confidence', 'confidence'),
    )


class OnlineLearningBatch(Base):
    """
    在线学习批次表
    追踪模型的在线学习和增量更新批次
    """
    __tablename__ = 'online_learning_batches'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    batch_id = Column(String(36), unique=True, nullable=False, comment='批次唯一标识')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    samples_count = Column(Integer, default=0, comment='样本数量')
    old_accuracy = Column(Float, comment='更新前准确率')
    new_accuracy = Column(Float, comment='更新后准确率')
    training_ms = Column(Integer, default=0, comment='训练耗时（毫秒）')
    version_increment = Column(String(20), comment='版本增量（如 v1.2 -> v1.3）')
    rolled_back = Column(Boolean, default=False, comment='是否已回滚')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_online_learning_model', 'model_name'),
        Index('idx_online_learning_rolled_back', 'rolled_back'),
        Index('idx_online_learning_created', 'created_at'),
    )


class EnsemblePredictionRecord(Base):
    """
    集成预测记录表
    记录集成模型的预测结果和置信区间
    """
    __tablename__ = 'ensemble_prediction_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    prediction_id = Column(String(36), unique=True, nullable=False, comment='预测记录唯一标识')
    task_id = Column(String(64), nullable=False, comment='任务ID')
    individual_predictions_json = Column(JSON, nullable=False, comment='各子模型预测结果JSON')
    weights_json = Column(JSON, nullable=False, comment='集成权重JSON')
    final_value = Column(Float, nullable=False, comment='最终预测值')
    ci_lower = Column(Float, comment='置信区间下界')
    ci_upper = Column(Float, comment='置信区间上界')
    explanation = Column(Text, comment='预测解释说明')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_ensemble_predictions_task', 'task_id'),
        Index('idx_ensemble_predictions_value', 'final_value'),
        Index('idx_ensemble_predictions_created', 'created_at'),
    )


# =============================================================================
# Plan 6: 安全防御体系升级 — 3表
# =============================================================================

class AdversarialSample(Base):
    """
    对抗样本表
    存储生成的对抗样本及其属性，用于防御测试
    """
    __tablename__ = 'adversarial_samples'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_id = Column(String(36), unique=True, nullable=False, comment='样本唯一标识')
    parent_id = Column(String(36), comment='父样本ID（变异来源）')
    attack_type = Column(String(50), nullable=False, comment='攻击类型：fgsm/pgd/bim/cw')
    payload = Column(Text, nullable=False, comment='对抗载荷')
    mutation_count = Column(Integer, default=0, comment='变异次数')
    bypassed_defense = Column(Boolean, default=False, comment='是否绕过防御')
    severity = Column(String(20), default='medium', comment='严重级别：low/medium/high/critical')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')

    __table_args__ = (
        Index('idx_adversarial_attack_type', 'attack_type'),
        Index('idx_adversarial_bypassed', 'bypassed_defense'),
        Index('idx_adversarial_severity', 'severity'),
        Index('idx_adversarial_generated', 'generated_at'),
    )


class AttackDetectionEvent(Base):
    """
    攻击检测事件表
    记录实时检测到的攻击事件
    """
    __tablename__ = 'attack_detection_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    event_id = Column(String(36), unique=True, nullable=False, comment='事件唯一标识')
    request_id = Column(String(64), nullable=False, comment='关联的请求ID')
    user_ip = Column(String(45), comment='攻击者IP地址')
    attack_type = Column(String(50), nullable=False, comment='攻击类型：sql_injection/xss/csrf/ddos/prompt_injection')
    severity = Column(String(20), default='medium', comment='严重级别')
    confidence = Column(Float, default=0.0, comment='检测置信度（0-1）')
    blocked = Column(Boolean, default=False, comment='是否已被拦截')
    detection_ms = Column(Integer, default=0, comment='检测耗时（毫秒）')
    detected_at = Column(DateTime, default=datetime.utcnow, comment='检测时间')

    __table_args__ = (
        Index('idx_attack_events_request', 'request_id'),
        Index('idx_attack_events_ip', 'user_ip'),
        Index('idx_attack_events_type', 'attack_type'),
        Index('idx_attack_events_blocked', 'blocked'),
        Index('idx_attack_events_detected_at', 'detected_at'),
    )


class ThreatIntelReport(Base):
    """
    威胁情报报告表
    聚合和分析威胁情报数据
    """
    __tablename__ = 'threat_intel_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(36), unique=True, nullable=False, comment='报告唯一标识')
    attacker_ip = Column(String(45), nullable=False, comment='攻击者IP地址')
    fingerprint_hash = Column(String(64), comment='攻击者指纹哈希')
    patterns_json = Column(JSON, comment='攻击模式JSON数组')
    threat_level = Column(String(20), default='low', comment='威胁级别：low/medium/high/critical')
    shared_third_party = Column(Boolean, default=False, comment='是否已共享给第三方')
    recommended_action = Column(String(256), comment='建议采取的行动')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_threat_reports_ip', 'attacker_ip'),
        Index('idx_threat_reports_fingerprint', 'fingerprint_hash'),
        Index('idx_threat_reports_level', 'threat_level'),
        Index('idx_threat_reports_shared', 'shared_third_party'),
    )


# =============================================================================
# Plan 7: 高可用灾备体系 — 3表
# =============================================================================

class DBReplicaStatus(Base):
    """
    数据库副本状态表
    监控数据库副本的健康状态和同步延迟
    """
    __tablename__ = 'db_replica_status'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    replica_id = Column(String(36), unique=True, nullable=False, comment='副本唯一标识')
    role = Column(String(20), nullable=False, comment='角色：primary/secondary/arbiter')
    zone = Column(String(50), nullable=False, comment='可用区')
    is_healthy = Column(Boolean, default=True, comment='是否健康')
    lag_seconds = Column(Float, default=0.0, comment='复制延迟（秒）')
    last_heartbeat = Column(DateTime, default=datetime.utcnow, comment='最后心跳时间')
    connections_active = Column(Integer, default=0, comment='活跃连接数')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_db_replica_role', 'role'),
        Index('idx_db_replica_zone', 'zone'),
        Index('idx_db_replica_healthy', 'is_healthy'),
        Index('idx_db_replica_lag', 'lag_seconds'),
    )


class AgentMigrationRecord(Base):
    """
    Agent迁移记录表
    记录Agent实例在故障转移期间的迁移过程
    """
    __tablename__ = 'agent_migration_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    migration_id = Column(String(36), unique=True, nullable=False, comment='迁移记录唯一标识')
    agent_id = Column(String(64), nullable=False, comment='Agent ID')
    from_instance = Column(String(64), nullable=False, comment='源实例ID')
    to_instance = Column(String(64), nullable=False, comment='目标实例ID')
    state_hash = Column(String(64), comment='状态哈希（用于一致性校验）')
    migrated_at = Column(DateTime, default=datetime.utcnow, comment='迁移时间')
    downtime_ms = Column(Integer, default=0, comment='停机时间（毫秒）')
    success = Column(Boolean, default=True, comment='是否成功')

    __table_args__ = (
        Index('idx_agent_migration_agent', 'agent_id'),
        Index('idx_agent_migration_from', 'from_instance'),
        Index('idx_agent_migration_to', 'to_instance'),
        Index('idx_agent_migration_success', 'success'),
        Index('idx_agent_migration_migrated', 'migrated_at'),
    )


class TrafficRouteRule(Base):
    """
    流量路由规则表
    定义跨可用区的流量路由策略
    """
    __tablename__ = 'traffic_route_rules'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_id = Column(String(36), unique=True, nullable=False, comment='规则唯一标识')
    priority = Column(Integer, default=100, comment='优先级（数值越小优先级越高）')
    geo_region = Column(String(50), comment='地理区域匹配条件')
    load_condition = Column(String(50), comment='负载条件：normal/high/critical')
    target_zone = Column(String(50), nullable=False, comment='目标可用区')
    weight = Column(Integer, default=100, comment='流量权重（0-100）')
    enabled = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_traffic_route_priority', 'priority'),
        Index('idx_traffic_route_geo', 'geo_region'),
        Index('idx_traffic_route_load', 'load_condition'),
        Index('idx_traffic_route_target', 'target_zone'),
        Index('idx_traffic_route_enabled', 'enabled'),
    )


# =============================================================================
# Plan 8: 开发者生态平台 — 3表
# =============================================================================

class DeveloperAccount(Base):
    """
    开发者账户表
    管理平台开发者的账户信息和API访问权限
    """
    __tablename__ = 'developer_accounts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    developer_id = Column(String(36), unique=True, nullable=False, comment='开发者唯一标识')
    email = Column(String(256), unique=True, nullable=False, comment='邮箱地址')
    name = Column(String(100), nullable=False, comment='开发者姓名')
    tier = Column(String(20), default='free', comment='等级：free/pro/enterprise')
    api_keys_json = Column(JSON, comment='API密钥列表JSON')
    daily_limit = Column(Integer, default=1000, comment='每日调用限额')
    monthly_quota = Column(Integer, default=30000, comment='每月配额')
    registered_at = Column(DateTime, default=datetime.utcnow, comment='注册时间')

    # 关系定义
    sandbox_sessions = relationship('SandboxSession', back_populates='developer', lazy='dynamic')
    api_usage_logs = relationship('APIUsageLog', back_populates='developer', lazy='dynamic')

    __table_args__ = (
        Index('idx_developer_tier', 'tier'),
        Index('idx_developer_registered', 'registered_at'),
    )


class SandboxSession(Base):
    """
    沙箱会话表
    管理开发者在沙箱环境中的API测试会话
    """
    __tablename__ = 'sandbox_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(36), unique=True, nullable=False, comment='会话唯一标识')
    developer_id = Column(String(36), ForeignKey('developer_accounts.developer_id'), nullable=False, comment='开发者ID')
    api_key = Column(String(64), nullable=False, comment='使用的API密钥')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    calls_made = Column(Integer, default=0, comment='已调用次数')
    tokens_consumed = Column(Integer, default=0, comment='已消耗Token数')

    # 关系定义
    developer = relationship('DeveloperAccount', back_populates='sandbox_sessions')

    __table_args__ = (
        Index('idx_sandbox_developer', 'developer_id'),
        Index('idx_sandbox_api_key', 'api_key'),
        Index('idx_sandbox_expires', 'expires_at'),
    )


class APIUsageLog(Base):
    """
    API使用日志表
    记录所有API调用的使用情况和计费信息
    """
    __tablename__ = 'api_usage_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    usage_id = Column(String(36), unique=True, nullable=False, comment='使用记录唯一标识')
    api_key = Column(String(64), nullable=False, comment='API密钥')
    developer_id = Column(String(36), ForeignKey('developer_accounts.developer_id'), comment='开发者ID')
    endpoint = Column(String(256), nullable=False, comment='API端点路径')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='调用时间戳')
    tokens_used = Column(Integer, default=0, comment='消耗的Token数')
    cost_usd = Column(Float, default=0.0, comment='费用（美元）')
    rate_limited = Column(Boolean, default=False, comment='是否触发限流')

    # 关系定义
    developer = relationship('DeveloperAccount', back_populates='api_usage_logs')

    __table_args__ = (
        Index('idx_api_usage_api_key', 'api_key'),
        Index('idx_api_usage_developer', 'developer_id'),
        Index('idx_api_usage_endpoint', 'endpoint'),
        Index('idx_api_usage_timestamp', 'timestamp'),
        Index('idx_api_usage_rate_limited', 'rate_limited'),
    )


# =============================================================================
# Plan 9: 移动端App重构 — 3表
# =============================================================================

class AppBuildRecord(Base):
    """
    App构建记录表
    追踪移动端应用的构建历史和版本信息
    """
    __tablename__ = 'app_build_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    build_id = Column(String(36), unique=True, nullable=False, comment='构建唯一标识')
    platform = Column(String(20), nullable=False, comment='平台：ios/android')
    version = Column(String(20), nullable=False, comment='版本号（如 2.5.0）')
    build_number = Column(Integer, nullable=False, comment='构建序号')
    flutter_version = Column(String(20), comment='Flutter SDK版本')
    startup_target_ms = Column(Integer, comment='目标启动时间（毫秒）')
    features_json = Column(JSON, comment='本次构建包含的功能特性JSON')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_app_build_platform', 'platform'),
        Index('idx_app_build_version', 'version'),
        Index('idx_app_build_created', 'created_at'),
    )


class OfflineCacheEntry(Base):
    """
    离线缓存条目表
    管理移动端的离线缓存数据和同步状态
    """
    __tablename__ = 'offline_cache_entries'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    entry_id = Column(String(36), unique=True, nullable=False, comment='条目唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    content_type = Column(String(50), nullable=False, comment='内容类型：conversation/memory/config')
    content_key = Column(String(256), nullable=False, comment='内容键名')
    data_hash = Column(String(64), nullable=False, comment='数据哈希（用于校验）')
    size_bytes = Column(Integer, default=0, comment='大小（字节）')
    cached_at = Column(DateTime, default=datetime.utcnow, comment='缓存时间')
    synced = Column(Boolean, default=False, comment='是否已与服务器同步')

    __table_args__ = (
        Index('offline_cache_user', 'user_id'),
        Index('offline_cache_type', 'content_type'),
        Index('offline_cache_synced', 'synced'),
        Index('offline_cache_cached_at', 'cached_at'),
    )


class VoiceInteractionLog(Base):
    """
    语音交互日志表
    记录移动端的语音交互事件和质量指标
    """
    __tablename__ = 'voice_interaction_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    log_id = Column(String(36), unique=True, nullable=False, comment='日志唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    interaction_type = Column(String(30), nullable=False, comment='交互类型：voice_input/tts/command')
    transcript = Column(Text, comment='语音转文字结果')
    persona_voice = Column(String(50), comment='使用的语音角色')
    duration_ms = Column(Integer, default=0, comment='交互时长（毫秒）')
    success = Column(Boolean, default=True, comment='是否成功')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_voice_log_user', 'user_id'),
        Index('idx_voice_log_type', 'interaction_type'),
        Index('idx_voice_log_success', 'success'),
        Index('idx_voice_log_created', 'created_at'),
    )


# =============================================================================
# Plan 10: 国际化多语言 — 3表
# =============================================================================

class I18nTranslationEntry(Base):
    """
    i18n翻译条目表
    存储国际化翻译条目，支持多语言切换
    """
    __tablename__ = 'i18n_translation_entries'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    entry_id = Column(String(36), unique=True, nullable=False, comment='条目唯一标识')
    locale = Column(String(10), nullable=False, comment='语言区域代码：zh-CN/en-US/ja-JP')
    key = Column(String(256), nullable=False, comment='翻译键名')
    value = Column(Text, nullable=False, comment='翻译值')
    namespace = Column(String(50), default='common', comment='命名空间：common/ui/error/message')
    updated_by = Column(String(64), comment='最后更新者')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        Index('idx_i18n_locale_key', 'locale', 'key'),
        Index('idx_i18n_namespace', 'namespace'),
        UniqueConstraint('locale', 'key', name='uq_i18n_locale_key'),
    )


class TranslationCacheItem(Base):
    """
    翻译缓存表
    缓存机器翻译结果以提高性能
    """
    __tablename__ = 'translation_cache_items'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cache_id = Column(String(36), unique=True, nullable=False, comment='缓存唯一标识')
    source_text_hash = Column(String(64), nullable=False, comment='原文哈希（用于去重）')
    source_locale = Column(String(10), nullable=False, comment='源语言')
    target_locale = Column(String(10), nullable=False, comment='目标语言')
    translated_text = Column(Text, nullable=False, comment='翻译文本')
    hit_count = Column(Integer, default=0, comment='命中次数')
    cached_at = Column(DateTime, default=datetime.utcnow, comment='缓存时间')
    ttl_hours = Column(Integer, default=168, comment='有效期（小时），默认7天')

    __table_args__ = (
        Index('idx_trans_cache_hash', 'source_text_hash'),
        Index('idx_trans_cache_locale_pair', 'source_locale', 'target_locale'),
        Index('idx_trans_cache_hit_count', 'hit_count'),
    )


class MultiLangReport(Base):
    """
    多语言报告表
    管理不同语言版本的生成报告
    """
    __tablename__ = 'multi_lang_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    meta_id = Column(String(36), unique=True, nullable=False, comment='元数据唯一标识')
    report_id = Column(String(64), nullable=False, comment='原始报告ID')
    locale = Column(String(10), nullable=False, comment='语言区域代码')
    title = Column(String(256), comment='本地化标题')
    generated_at = Column(DateTime, default=datetime.utcnow, comment='生成时间')
    file_url = Column(String(512), comment='文件存储URL')
    page_count = Column(Integer, default=0, comment='页数')

    __table_args__ = (
        Index('idx_multi_lang_report_report', 'report_id'),
        Index('idx_multi_lang_locale', 'locale'),
        Index('idx_multi_lang_generated', 'generated_at'),
    )


# =============================================================================
# Plan 11: 合规审计隐私 — 3表
# =============================================================================

class DataExportRequest(Base):
    """
    数据导出请求表
    处理用户的数据导出请求（GDPR/个人信息保护法）
    """
    __tablename__ = 'data_export_requests'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    request_id = Column(String(36), unique=True, nullable=False, comment='请求唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    export_type = Column(String(30), nullable=False, comment='导出类型：full/conversations/memories/analytics')
    status = Column(String(20), default='pending', comment='状态：pending/processing/completed/expired')
    file_path = Column(String(512), comment='导出文件路径')
    record_count = Column(Integer, default=0, comment='导出的记录数')
    requested_at = Column(DateTime, default=datetime.utcnow, comment='请求时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_data_export_user', 'user_id'),
        Index('idx_data_export_status', 'status'),
        Index('idx_data_export_requested', 'requested_at'),
    )


class MinimizationAuditResult(Base):
    """
    最小化审计结果表
    记录数据最小化原则执行情况的审计结果
    """
    __tablename__ = 'minimization_audit_results'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    audit_id = Column(String(36), unique=True, nullable=False, comment='审计唯一标识')
    scan_date = Column(Date, nullable=False, comment='扫描日期')
    users_scanned = Column(Integer, default=0, comment='扫描的用户数')
    users_flagged = Column(Integer, default=0, comment='标记的用户数')
    records_deleted = Column(Integer, default=0, comment='删除的记录数')
    records_anonymized = Column(Integer, default=0, comment='匿名化的记录数')
    storage_saved_mb = Column(Float, default=0.0, comment='节省的存储空间（MB）')

    __table_args__ = (
        Index('idx_minimization_audit_date', 'scan_date'),
        Index('idx_minimization_audit_flagged', 'users_flagged'),
    )


class AuditLogExtended(Base):
    """
    扩展审计日志表
    详细记录所有敏感操作和数据访问行为
    """
    __tablename__ = 'audit_log_extended'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    log_id = Column(String(36), unique=True, nullable=False, comment='日志唯一标识')
    actor_id = Column(String(64), nullable=False, comment='操作者ID（用户或系统服务）')
    action = Column(String(100), nullable=False, comment='操作类型：read/write/delete/export/admin')
    resource_type = Column(String(50), nullable=False, comment='资源类型：user/memory/config/system')
    resource_id = Column(String(64), comment='资源ID')
    ip_anonymized = Column(String(45), comment='匿名化IP地址')
    details_json = Column(JSON, comment='操作详情JSON')
    timestamp = Column(DateTime, default=datetime.utcnow, comment='操作时间戳')
    retention_years = Column(Integer, default=3, comment='保留年限')

    __table_args__ = (
        Index('idx_audit_log_actor', 'actor_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_resource_type', 'resource_type'),
        Index('idx_audit_log_timestamp', 'timestamp'),
        Index('idx_audit_log_resource', 'resource_type', 'resource_id'),
    )


# =============================================================================
# Plan 12: 成本优化资源调度 — 3表
# =============================================================================

class CostBudgetSnapshot(Base):
    """
    成本预算快照表
    定期采集的成本预算执行快照
    """
    __tablename__ = 'cost_budget_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    snapshot_id = Column(String(36), unique=True, nullable=False, comment='快照唯一标识')
    period = Column(String(20), nullable=False, comment='周期：daily/weekly/monthly')
    total_budget = Column(Float, nullable=False, comment='总预算（美元）')
    spent = Column(Float, default=0.0, comment='已支出（美元）')
    remaining = Column(Float, comment='剩余预算（美元）')
    projected_eod = Column(Float, comment='预计当日结束支出（美元）')
    alert_triggered = Column(Boolean, default=False, comment='是否触发预警')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    __table_args__ = (
        Index('idx_cost_budget_period', 'period'),
        Index('idx_cost_budget_alert', 'alert_triggered'),
        Index('idx_cost_budget_created', 'created_at'),
    )


class ResourcePoolInfo(Base):
    """
    资源池信息表
    管理计算资源池的状态和利用率
    """
    __tablename__ = 'resource_pool_info'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    pool_id = Column(String(36), unique=True, nullable=False, comment='资源池唯一标识')
    pool_name = Column(String(100), nullable=False, comment='资源池名称')
    instance_type = Column(String(50), nullable=False, comment='实例类型：compute/memory/storage')
    total_instances = Column(Integer, default=0, comment='总实例数')
    active_instances = Column(Integer, default=0, comment='活跃实例数')
    sleeping_instances = Column(Integer, default=0, comment='休眠实例数')
    avg_cpu = Column(Float, default=0.0, comment='平均CPU使用率（百分比）')
    avg_mem = Column(Float, default=0.0, comment='平均内存使用率（百分比）')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系定义
    spot_records = relationship('SpotInstanceRecord', back_populates='resource_pool', lazy='dynamic')

    __table_args__ = (
        Index('idx_resource_pool_type', 'instance_type'),
        Index('idx_resource_pool_active', 'active_instances'),
        Index('idx_resource_pool_updated', 'updated_at'),
    )


class SpotInstanceRecord(Base):
    """
    Spot实例记录表
    追踪Spot/抢占式实例的使用情况和成本节省
    """
    __tablename__ = 'spot_instance_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    record_id = Column(String(36), unique=True, nullable=False, comment='记录唯一标识')
    instance_id = Column(String(64), nullable=False, comment='实例ID')
    pool_id = Column(String(36), ForeignKey('resource_pool_info.pool_id'), comment='所属资源池ID')
    workload_type = Column(String(50), nullable=False, comment='工作负载类型：batch/inference/training/preemptible')
    bid_price = Column(Float, nullable=False, comment='竞价价格（美元/小时）')
    market_price = Column(Float, nullable=False, comment='市场价格（美元/小时）')
    savings_pct = Column(Float, default=0.0, comment='节省比例（百分比）')
    interrupted = Column(Boolean, default=False, comment='是否被中断')
    migrated_ok = Column(Boolean, default=False, comment='中断后是否成功迁移')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 关系定义
    resource_pool = relationship('ResourcePoolInfo', back_populates='spot_records')

    __table_args__ = (
        Index('spot_record_instance', 'instance_id'),
        Index('spot_record_pool', 'pool_id'),
        Index('spot_record_workload', 'workload_type'),
        Index('spot_record_interrupted', 'interrupted'),
        Index('spot_record_created', 'created_at'),
    )


# =============================================================================
# Plan 13: 用户增长运营系统 — 3表
# =============================================================================

class RecommendationProfile(Base):
    """
    推荐画像表
    存储用户的个性化推荐画像数据
    """
    __tablename__ = 'recommendation_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    profile_id = Column(String(36), unique=True, nullable=False, comment='画像唯一标识')
    user_id = Column(String(64), unique=True, nullable=False, comment='用户ID')
    preferences_json = Column(JSON, comment='偏好特征JSON（兴趣标签、风格偏好等）')
    history_items_json = Column(JSON, comment='历史交互物品JSON数组')
    neighbors_json = Column(JSON, comment='相似用户邻居JSON数组')
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后更新时间')

    # 关系定义
    task_completions = relationship('IncentiveTaskCompletion', back_populates='recommendation_profile', lazy='dynamic')

    __table_args__ = (
        Index('idx_rec_profile_last_updated', 'last_updated'),
    )


class IncentiveTaskCompletion(Base):
    """
    激励任务完成记录表
    记录用户完成激励任务的情况和奖励发放
    """
    __tablename__ = 'incentive_task_completions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    completion_id = Column(String(36), unique=True, nullable=False, comment='完成记录唯一标识')
    user_id = Column(String(64), nullable=False, comment='用户ID')
    profile_id = Column(String(36), ForeignKey('recommendation_profiles.profile_id'), comment='推荐画像ID')
    task_id = Column(String(64), nullable=False, comment='任务ID')
    task_category = Column(String(50), nullable=False, comment='任务类别：daily/weekly/achievement/social')
    points_earned = Column(Integer, default=0, comment='获得积分')
    xp_earned = Column(Integer, default=0, comment='获得经验值')
    completed_at = Column(DateTime, default=datetime.utcnow, comment='完成时间')

    # 关系定义
    recommendation_profile = relationship('RecommendationProfile', back_populates='task_completions')

    __table_args__ = (
        Index('idx_incentive_completion_user', 'user_id'),
        Index('idx_incentive_completion_task', 'task_id'),
        Index('idx_incentive_completion_category', 'task_category'),
        Index('idx_incentive_completion_completed', 'completed_at'),
    )


class ViralInviteRecord(Base):
    """
    病毒式邀请记录表
    追踪用户的邀请活动和奖励结算
    """
    __tablename__ = 'viral_invite_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    invite_id = Column(String(36), unique=True, nullable=False, comment='邀请记录唯一标识')
    inviter_id = Column(String(64), nullable=False, comment='邀请者ID')
    invite_code = Column(String(20), unique=True, nullable=False, comment='邀请码')
    invitee_ids_json = Column(JSON, comment='被邀请者ID列表JSON')
    total_rewards = Column(Float, default=0.0, comment='累计奖励金额')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    expires_at = Column(DateTime, comment='过期时间')

    __table_args__ = (
        Index('idx_viral_invite_inviter', 'inviter_id'),
        Index('idx_viral_invite_code', 'invite_code'),
        Index('idx_viral_invite_created', 'created_at'),
        Index('idx_viral_invite_expires', 'expires_at'),
    )


# =============================================================================
# Plan 14: AI自我进化平台 — 3表
# =============================================================================

class RLTrainingRun(Base):
    """
    RL训练运行表
    记录强化学习训练运行的详细指标
    """
    __tablename__ = 'rl_training_runs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    run_id = Column(String(36), unique=True, nullable=False, comment='运行唯一标识')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    mode = Column(String(30), nullable=False, comment='训练模式：ppo/a2c/dqn/sac')
    episodes = Column(Integer, default=0, comment='总回合数')
    total_reward = Column(Float, default=0.0, comment='总奖励')
    avg_reward = Column(Float, default=0.0, comment='平均奖励')
    kl_divergence = Column(Float, default=0.0, comment='KL散度（策略约束指标）')
    policy_updates = Column(Integer, default=0, comment='策略更新次数')
    started_at = Column(DateTime, default=datetime.utcnow, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('rl_training_model', 'model_name'),
        Index('rl_training_mode', 'mode'),
        Index('rl_training_started', 'started_at'),
    )


class BlindSpotReport(Base):
    """
    盲点报告表
    识别AI系统的知识盲点和能力缺陷
    """
    __tablename__ = 'blind_spot_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(String(36), unique=True, nullable=False, comment='报告唯一标识')
    cluster_id = Column(String(64), nullable=False, comment='问题簇ID')
    question_samples_json = Column(JSON, nullable=False, comment='问题样本JSON数组')
    frequency = Column(Integer, default=0, comment='出现频次')
    suggested_skill = Column(String(100), comment='建议新增的技能')
    suggested_knowledge_source = Column(String(256), comment='建议的知识来源')
    discovered_at = Column(DateTime, default=datetime.utcnow, comment='发现时间')
    resolved = Column(Boolean, default=False, comment='是否已解决')

    __table_args__ = (
        Index('blind_spot_cluster', 'cluster_id'),
        Index('blind_spot_frequency', 'frequency'),
        Index('blind_spot_resolved', 'resolved'),
        Index('blind_spot_discovered', 'discovered_at'),
    )


class ABExperimentRecord(Base):
    """
    AB实验记录表
    管理A/B测试实验的全生命周期
    """
    __tablename__ = 'ab_experiment_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    experiment_id = Column(String(36), unique=True, nullable=False, comment='实验唯一标识')
    name = Column(String(200), nullable=False, comment='实验名称')
    model_a_ver = Column(String(50), nullable=False, comment='模型A版本')
    model_b_ver = Column(String(50), nullable=False, comment='模型B版本')
    traffic_split = Column(Float, default=0.5, comment='流量分配比例（B组占比）')
    metric_primary = Column(String(100), nullable=False, comment='主要评估指标')
    metric_a_val = Column(Float, comment='模型A指标值')
    metric_b_val = Column(Float, comment='模型B指标值')
    winner = Column(String(10), comment='获胜方：a/b/no_winner')
    status = Column(String(20), default='running', comment='状态：running/paused/completed/cancelled')
    started_at = Column(DateTime, default=datetime.utcnow, comment='开始时间')

    __table_args__ = (
        Index('ab_experiment_status', 'status'),
        Index('ab_experiment_metric', 'metric_primary'),
        Index('ab_experiment_started', 'started_at'),
    )


# =============================================================================
# Part 46: 风险意识与忧患防御系统 — 28表 (Layer 36)
# =============================================================================

class RiskItem(Base):
    """风险项注册表 — 42个内置风险 + 自定义风险"""
    __tablename__ = 'risk_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_id = Column(String(20), unique=True, nullable=False)
    plan_id = Column(Integer, nullable=False, comment='战略计划ID(1-14)')
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    probability = Column(Float, default=0.5, comment='发生概率0-1')
    impact = Column(Float, default=0.5, comment='影响程度0-1')
    severity = Column(String(20), default='medium')
    status = Column(String(20), default='open')
    mitigation_strategy = Column(Text)
    score = Column(Float, default=0, comment='动态风险评分')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_risk_plan','plan_id'), Index('idx_risk_severity','severity'),
        Index('idx_risk_status','status'), Index('idx_risk_category','category'))

class ProblemDetection(Base):
    """问题检测记录表"""
    __tablename__ = 'problem_detections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    detection_id = Column(String(12), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default='medium')
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    __table_args__ = (Index('idx_det_category','category'), Index('idx_det_severity','severity'),
        Index('idx_det_status','resolved'), Index('idx_det_detected','detected_at'))

class MitigationActionRecord(Base):
    """缓解措施执行记录表"""
    __tablename__ = 'mitigation_action_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(12), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    action_type = Column(String(30), nullable=False)
    description = Column(Text)
    detection_id = Column(String(12))
    executed_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    rollback_data = Column(JSON)
    rolled_back = Column(Boolean, default=False)
    rolled_back_at = Column(DateTime)
    __table_args__ = (Index('idx_mit_category','category'), Index('idx_mit_type','action_type'),
        Index('idx_mit_success','success'), Index('idx_mit_executed','executed_at'))

class AlertRule(Base):
    """告警规则配置表"""
    __tablename__ = 'alert_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(10), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    operator = Column(String(5), nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default='high')
    cooldown_seconds = Column(Integer, default=300)
    enabled = Column(Boolean, default=True)
    __table_args__ = (Index('idx_alert_rule_cat','category'), Index('idx_alert_rule_metric','metric_name'),
        Index('idx_alert_rule_sev','severity'), Index('idx_alert_rule_enabled','enabled'))

class AlertEvent(Base):
    """告警事件记录表"""
    __tablename__ = 'alert_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(12), unique=True, nullable=False)
    rule_id = Column(String(10), ForeignKey('alert_rules.rule_id'), nullable=False)
    category = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    state = Column(String(20), default='firing')
    fired_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(64))
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))
    fire_count = Column(Integer, default=1)
    __table_args__ = (Index('idx_ae_rule','rule_id'), Index('idx_ae_state','state'),
        Index('idx_ae_fired','fired_at'), Index('idx_ae_cat','category'))

class ChaosExperiment(Base):
    """混沌工程实验表"""
    __tablename__ = 'chaos_experiments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(12), unique=True, nullable=False)
    injection_type = Column(String(30), nullable=False)
    target = Column(String(100), nullable=False)
    duration_seconds = Column(Integer, default=60)
    designed_at = Column(DateTime, default=datetime.utcnow)
    designed_by = Column(String(64))
    run_at = Column(DateTime)
    run_by = Column(String(64))
    status = Column(String(20), default='designed')
    result_json = Column(JSON)
    recovery_time_sec = Column(Float)
    resilience_score = Column(Float)
    success = Column(Boolean)
    __table_args__ = (Index('idx_chaos_type','injection_type'), Index('idx_chaos_target','target'),
        Index('idx_chaos_status','status'), Index('idx_chaos_designed','designed_at'))

class RedBlueExercise(Base):
    """红蓝对抗演练表"""
    __tablename__ = 'red_blue_exercises'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exercise_id = Column(String(12), unique=True, nullable=False)
    attack_type = Column(String(30), nullable=False)
    target = Column(String(100), nullable=False)
    designed_at = Column(DateTime, default=datetime.utcnow)
    designed_by = Column(String(64))
    run_at = Column(DateTime)
    run_by = Column(String(64))
    status = Column(String(20), default='designed')
    result_json = Column(JSON)
    detection_score = Column(Float)
    mitigation_score = Column(Float)
    defense_score = Column(Float)
    outcome = Column(String(20))
    findings = Column(Text)
    __table_args__ = (Index('idx_rb_attack','attack_type'), Index('idx_rb_target','target'),
        Index('idx_rb_status','status'), Index('idx_rb_designed','designed_at'))

class WeeklyReviewReport(Base):
    """周报审查报告表"""
    __tablename__ = 'weekly_review_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(12), unique=True, nullable=False)
    plan_id = Column(Integer, nullable=False)
    health_score = Column(Float, default=100)
    total_risks = Column(Integer, default=0)
    open_critical = Column(Integer, default=0)
    outcome = Column(String(20), default='healthy')
    findings_json = Column(JSON)
    recommendations_json = Column(JSON)
    reviewed_by = Column(String(64))
    generated_at = Column(DateTime, default=datetime.utcnow)
    week_start = Column(Date)
    week_end = Column(Date)
    __table_args__ = (Index('idx_wr_plan','plan_id'), Index('idx_wr_week','week_start'),
        Index('idx_wr_outcome','outcome'), Index('idx_wr_generated','generated_at'))

class WorryLogEntry(Base):
    """忧患日志条目表"""
    __tablename__ = 'worry_log_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(12), unique=True, nullable=False)
    plan_id = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    severity = Column(String(20), default='medium')
    description = Column(Text)
    tags_json = Column(JSON)
    created_by = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(64))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    __table_args__ = (Index('idx_wl_plan','plan_id'), Index('idx_wl_severity','severity'),
        Index('idx_wl_resolved','resolved'), Index('idx_wl_created','created_at'),
        Index('idx_wl_tags','tags_json'))

class RiskDashboardSnapshot(Base):
    """风险仪表盘快照表（历史趋势）"""
    __tablename__ = 'risk_dashboard_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(12), unique=True, nullable=False)
    total_risks = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    critical_open = Column(Integer, default=0)
    overall_health_pct = Column(Float, default=100)
    active_alerts = Column(Integer, default=0)
    active_detections = Column(Integer, default=0)
    resilience_score = Column(Float, default=75)
    defense_score = Column(Float, default=70)
    captured_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_snap_captured','captured_at'),)

class MitigationStrategyMapping(Base):
    """缓解策略映射配置表"""
    __tablename__ = 'mitigation_strategy_mappings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), unique=True, nullable=False)
    primary_action = Column(String(30), nullable=False)
    fallback_action = Column(String(30), nullable=False)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_map_category','category'), Index('idx_map_enabled','enabled'))

class RiskThresholdConfig(Base):
    """检测阈值配置表"""
    __tablename__ = 'risk_threshold_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), unique=True, nullable=False)
    metric_name = Column(String(100), nullable=False)
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    unit = Column(String(20))
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_thresh_cat','category'), Index('idx_thresh_enabled','enabled'))

class IncidentEscalation(Base):
    """事件升级记录表"""
    __tablename__ = 'incident_escalations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    escalation_id = Column(String(12), unique=True, nullable=False)
    source_type = Column(String(20), nullable=False)
    source_id = Column(String(12), nullable=False)
    severity = Column(String(20), nullable=False)
    from_level = Column(String(20), nullable=False)
    to_level = Column(String(20), nullable=False)
    reason = Column(Text)
    escalated_by = Column(String(64))
    escalated_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    __table_args__ = (Index('idx_escal_source','source_type','source_id'),
        Index('idx_escal_severity','severity'), Index('idx_escal_time','escalated_at'))

class ChaosExperimentSchedule(Base):
    """混沌实验调度表"""
    __tablename__ = 'chaos_experiment_schedules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(12), unique=True, nullable=False)
    injection_type = Column(String(30), nullable=False)
    target = Column(String(100), nullable=False)
    cron_expression = Column(String(50))
    duration_seconds = Column(Integer, default=60)
    blast_radius = Column(String(20), default='limited')
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    enabled = Column(Boolean, default=True)
    created_by = Column(String(64))
    __table_args__ = (Index('idx_sched_type','injection_type'), Index('idx_sched_enabled','enabled'),
        Index('idx_sched_next','next_run_at'))

class SecurityVulnerabilityScan(Base):
    """安全漏洞扫描记录表"""
    __tablename__ = 'security_vulnerability_scans'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(12), unique=True, nullable=False)
    scanner_type = Column(String(30), nullable=False)
    target = Column(String(200), nullable=False)
    status = Column(String(20), default='running')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    findings_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    report_path = Column(String(500))
    scanned_by = Column(String(64))
    __table_args__ = (Index('idx_scan_type','scanner_type'), Index('idx_scan_status','status'),
        Index('idx_scan_started','started_at'), Index('idx_scan_target','target'))

class ComplianceCheckRecord(Base):
    """合规检查记录表"""
    __tablename__ = 'compliance_check_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(12), unique=True, nullable=False)
    framework = Column(String(30), nullable=False, comment='GDPR/ISO27001/等保')
    control_id = Column(String(30), nullable=False)
    control_name = Column(String(200), nullable=False)
    status = Column(String(20), default='pending')
    result = Column(String(20))
    evidence_path = Column(String(500))
    checked_at = Column(DateTime)
    checked_by = Column(String(64))
    next_due_date = Column(Date)
    notes = Column(Text)
    __table_args__ = (Index('idx_comp_framework','framework'), Index('idx_comp_control','control_id'),
        Index('idx_comp_status','status'), Index('idx_comp_due','next_due_date'))

class CostAnomalyAlert(Base):
    """成本异常告警表"""
    __tablename__ = 'cost_anomaly_alerts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(12), unique=True, nullable=False)
    service = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    expected_cost = Column(Float, default=0)
    actual_cost = Column(Float, default=0)
    variance_pct = Column(Float, default=0)
    severity = Column(String(20), default='medium')
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    resolution = Column(Text)
    __table_args__ = (Index('idx_cost_service','service'), Index('idx_cost_severity','severity'),
        Index('idx_cost_detected','detected_at'), Index('idx_cost_resolved','resolved'))

class GrowthMetricTrend(Base):
    """增长指标趋势表"""
    __tablename__ = 'growth_metric_trends'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_date = Column(Date, nullable=False)
    metric_name = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    prev_value = Column(Float)
    change_pct = Column(Float)
    ma7 = Column(Float, comment='7日移动平均')
    ma30 = Column(Float, comment='30日移动平均')
    anomaly_flag = Column(Boolean, default=False)
    __table_args__ = (Index('idx_growth_date_metric','record_date','metric_name', unique=True),
        Index('idx_growth_metric','metric_name'), Index('idx_growth_anomaly','anomaly_flag'))

class AIModelDriftMonitor(Base):
    """AI模型漂移监控表"""
    __tablename__ = 'ai_model_drift_monitors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_id = Column(String(12), unique=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    check_date = Column(Date, nullable=False)
    mape_3day = Column(Float)
    mape_7day = Column(Float)
    mape_30day = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    drift_detected = Column(Boolean, default=False)
    drift_severity = Column(String(20))
    recommendation = Column(Text)
    __table_args__ = (Index('idx_drift_model','model_name','model_version'),
        Index('idx_drift_date','check_date'), Index('idx_drift_detected','drift_detected'))

class RiskReviewActionItem(Base):
    """风险审查行动项表"""
    __tablename__ = 'risk_review_action_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(12), unique=True, nullable=False)
    review_report_id = Column(String(12))
    plan_id = Column(Integer, nullable=False)
    risk_id = Column(String(20))
    action_title = Column(String(200), nullable=False)
    action_description = Column(Text)
    priority = Column(String(10), default='medium')
    assignee = Column(String(64))
    status = Column(String(20), default='open')
    due_date = Column(Date)
    completed_at = Column(DateTime)
    __table_args__ = (Index('idx_rai_review','review_report_id'), Index('idx_rai_plan','plan_id'),
        Index('idx_rai_assignee','assignee'), Index('idx_rai_status','status'),
        Index('idx_rai_due','due_date'))

class RunbookEntry(Base):
    """应急响应手册条目表"""
    __tablename__ = 'runbook_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(12), unique=True, nullable=False)
    incident_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    steps_json = Column(JSON, nullable=False, comment='步骤列表JSON')
    escalation_criteria = Column(Text)
    estimated_recovery_min = Column(Integer)
    responsible_team = Column(String(50))
    last_reviewed_at = Column(DateTime)
    version = Column(Integer, default=1)
    __table_args__ = (Index('idx_runbook_type','incident_type'), Index('idx_runbook_severity','severity'),
        Index('idx_runbook_team','responsible_team'))

class PostIncidentReview(Base):
    """事后复盘报告表"""
    __tablename__ = 'post_incident_reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(12), unique=True, nullable=False)
    incident_id = Column(String(12), nullable=False)
    incident_title = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    root_cause = Column(Text)
    impact_summary = Column(Text)
    lessons_learned = Column(Text)
    action_items_json = Column(JSON)
    prevention_measures = Column(Text)
    reviewed_by = Column(String(64))
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_pir_incident','incident_id'), Index('idx_pir_severity','severity'),
        Index('idx_pir_occurred','occurred_at'), Index('idx_pir_reviewed','reviewed_at'))

# =============================================================================
# Part 47: SEO与内容生态融合开发 — 25表 (Layer 37)
# =============================================================================

class SitemapEntryORM(Base):
    """SEO站点地图条目表"""
    __tablename__ = 'sitemap_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(12), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    lastmod = Column(DateTime, default=datetime.utcnow)
    changefreq = Column(String(20), default='weekly')
    priority = Column(Float, default=0.5)
    added_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_se_url','url'), Index('idx_se_priority','priority'), Index('idx_se_lastmod','lastmod'))

class RobotsRuleORM(Base):
    """Robots.txt规则配置表"""
    __tablename__ = 'robots_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_agent = Column(String(100), nullable=False)
    disallow_json = Column(JSON)
    allow_json = Column(JSON)
    sitemap_url = Column(String(500))
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_rr_ua','user_agent'),)

class StructuredDataORM(Base):
    """结构化数据(JSON-LD)存储表"""
    __tablename__ = 'structured_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sd_id = Column(String(16), unique=True, nullable=False)
    page_url = Column(String(500), nullable=False)
    schema_type = Column(String(30), nullable=False)
    data_json = Column(JSON, nullable=False)
    valid = Column(Boolean, default=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    last_validated_at = Column(DateTime)
    __table_args__ = (Index('idx_sd_page','page_url'), Index('idx_sd_type','schema_type'), Index('idx_sd_valid','valid'))

class KeywordItemORM(Base):
    """SEO关键词条目表"""
    __tablename__ = 'keyword_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(String(12), unique=True, nullable=False)
    keyword = Column(String(200), nullable=False, index=True)
    search_volume = Column(Integer, default=0)
    competition_score = Column(Float, default=0.5)
    relevance_score = Column(Float, default=0.5)
    trend_direction = Column(String(10))
    source = Column(String(30))
    predicted_volume_3m = Column(Integer)
    user_segment = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_kw_keyword','keyword'), Index('kw_segment','user_segment'),
        Index('kw_volume','search_volume'), Index('kw_competition','competition_score'))

class SearchIntentLog(Base):
    """用户搜索意图记录表"""
    __tablename__ = 'search_intent_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    user_segment = Column(String(30), default='general')
    user_id = Column(String(64))
    session_id = Column(String(64))
    recorded_at = Column(DateTime, default=datetime.utcnow)
    extracted_keywords_json = Column(JSON)
    __table_args__ = (Index('idx_sil_query','query_text'), Index('idx_sil_segment','user_segment'),
        Index('idx_sil_recorded','recorded_at'))

class ContentPieceORM(Base):
    """SEO内容文章表"""
    __tablename__ = 'content_pieces'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(12), unique=True, nullable=False)
    title = Column(String(300), nullable=False)
    target_keyword = Column(String(200), nullable=False, index=True)
    word_count = Column(Integer, default=0)
    status = Column(String(20), default='draft')
    schema_types_json = Column(JSON)
    internal_link_count = Column(Integer, default=0)
    author_id = Column(String(64))
    category = Column(String(50))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_cp_keyword','target_keyword'), Index('idx_cp_status','status'),
        Index('idx_cp_category','category'), Index('idx_cp_published','published_at'))

class InternalLinkMapping(Base):
    """内部链接映射表"""
    __tablename__ = 'internal_link_mappings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_content_id = Column(String(12), nullable=False)
    target_content_id = Column(String(12), nullable=False)
    anchor_text = Column(String(200))
    link_position = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_ilm_source','source_content_id'), Index('idx_ilm_target','target_content_id'),
        UniqueConstraint('source_content_id','target_content_id',name='uq_ilm_link'))

class BacklinkRecordORM(Base):
    """外链记录表"""
    __tablename__ = 'backlink_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    backlink_id = Column(String(12), unique=True, nullable=False)
    source_url = Column(String(500), nullable=False)
    target_url = Column(String(500), nullable=False)
    anchor_text = Column(String(200))
    link_type = Column(String(20), default='dofollow')
    quality = Column(String(10), default='medium')
    domain_authority = Column(Float)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    lost = Column(Boolean, default=False)
    lost_at = Column(DateTime)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_bl_target','target_url'), Index('idx_bl_source','source_url'),
        Index('idx_bl_quality','quality'), Index('idx_bl_lost','lost'))

class DisavowEntry(Base):
    """Disavow拒绝域名/URL表"""
    __tablename__ = 'disavow_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_or_url = Column(String(500), nullable=False, unique=True)
    reason = Column(String(200))
    added_by = Column(String(64))
    added_at = Column(DateTime, default=datetime.utcnow)
    submitted_to_google = Column(Boolean, default=False)
    submitted_at = Column(DateTime)
    __table_args__ = (Index('idx_de_submitted','submitted_to_google'),)

class BrandMentionORM(Base):
    """品牌提及记录表"""
    __tablename__ = 'brand_mentions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(500), nullable=False)
    mention_text = Column(Text)
    has_link = Column(Boolean, default=False)
    found_at = Column(DateTime, default=datetime.utcnow)
    contacted = Column(Boolean, default=False)
    contacted_at = Column(DateTime)
    link_added = Column(Boolean, default=False)
    __table_args__ = (Index('idx_bm_source','source_url'), Index('idx_bm_has_link','has_link'),
        Index('idx_bm_contacted','contacted'))

class LocalSEOPageORM(Base):
    """本地SEO页面表（城市/板块）"""
    __tablename__ = 'local_seo_pages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    local_page_id = Column(String(12), unique=True, nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_name = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    district = Column(String(50))
    url = Column(String(500), nullable=False)
    avg_rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    status = Column(String(20), default='active')
    schema_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('idx_lsp_city','city'), Index('idx_lsp_district','district'),
        Index('idx_lsp_entity','entity_type'), Index('idx_lsp_status','status'))

class LocalReviewORM(Base):
    """本地页面评论表"""
    __tablename__ = 'local_reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    local_page_id = Column(String(12), nullable=False)
    reviewer_name = Column(String(100))
    reviewer_id = Column(String(64))
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    status = Column(String(20), default='approved')
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_lr_page','local_page_id'), Index('idx_lr_rating','rating'),
        Index('idx_lr_status','status'))

class LocalDirectoryLink(Base):
    """本地目录外链表"""
    __tablename__ = 'local_directory_links'
    id = Column(Integer, primary_key=True, autoincrement=True)
    directory_name = Column(String(200), nullable=False)
    directory_url = Column(String(500), nullable=False)
    category = Column(String(50))
    city = Column(String(50))
    nat_info = Column(JSON, comment='NAP: Name/Address/Phone')
    listed = Column(Boolean, default=False)
    listed_at = Column(DateTime)
    last_checked_at = Column(DateTime)
    __table_args__ = (Index('idx_ldl_city','city'), Index('idx_ldl_listed','listed'))

class AMPPageRecord(Base):
    """AMP页面生成记录表"""
    __tablename__ = 'amp_page_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_url = Column(String(500), nullable=False)
    amp_url = Column(String(500))
    status = Column(String(20), default='not_generated')
    amp_html_size = Column(Integer)
    generated_at = Column(DateTime)
    validation_errors_json = Column(JSON)
    last_validated_at = Column(DateTime)
    __table_args__ = (Index('idx_amp_original','original_url'), Index('idx_amp_status','status'))

class MobileFriendlyTest(Base):
    """移动端友好测试记录表"""
    __tablename__ = 'mobile_friendly_tests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_url = Column(String(500), nullable=False)
    mobile_friendly = Column(Boolean)
    score = Column(Float)
    issues_json = Column(JSON)
    tested_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(200))
    __table_args__ = (Index('idx_mft_url','page_url'), Index('idx_mft_friendly','mobile_friendly'),
        Index('idx_mft_tested','tested_at'))

class CoreWebVitalsMetric(Base):
    """Core Web Vitals指标记录表"""
    __tablename__ = 'core_web_vitals_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_url = Column(String(500), nullable=False)
    metric_name = Column(String(20), nullable=False)
    value = Column(Float, nullable=False)
    device_type = Column(String(10), default='desktop')
    recorded_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_cwv_page','page_url'), Index('idx_cwv_metric','metric_name'),
        Index('idx_cwv_device','device_type'), Index('idx_cwv_recorded','recorded_at'))

class SearchConsoleData(Base):
    """搜索引擎控制台数据快照表"""
    __tablename__ = 'search_console_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False)
    queries = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    avg_position = Column(Float)
    ctr = Column(Float)
    indexed_pages = Column(Integer, default=0)
    crawl_errors = Column(Integer, default=0)
    engine = Column(String(20), default='google')
    __table_args__ = (Index('idx_scd_date','snapshot_date'), Index('idx_scd_engine','engine'))

class KeywordRankingTrack(Base):
    """关键词排名追踪表"""
    __tablename__ = 'keyword_ranking_tracks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, index=True)
    page_url = Column(String(500))
    position = Column(Integer)
    engine = Column(String(20), default='google')
    tracked_at = Column(DateTime, default=datetime.utcnow)
    previous_position = Column(Integer)
    change = Column(Integer)
    __table_args__ = (Index('idx_krt_keyword_date','keyword','tracked_at'),
        Index('idx_krt_engine','engine'))

class CompetitorSEODomain(Base):
    """竞品SEO域名监控表"""
    __tablename__ = 'competitor_seo_domains'
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(200), unique=True, nullable=False)
    estimated_traffic = Column(Integer)
    keyword_overlap = Column(Integer)
    visibility_score = Column(Float)
    total_backlinks = Column(Integer)
    referring_domains = Column(Integer)
    last_updated = Column(DateTime)
    notes = Column(Text)
    __table_args__ = (Index('idx_csd_traffic','estimated_traffic'),)

class SocialPostORM(Base):
    """社交媒体发布记录表"""
    __tablename__ = 'social_posts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(12), unique=True, nullable=False)
    platform = Column(String(30), nullable=False)
    content = Column(Text)
    linked_content_id = Column(String(12))
    tone = Column(String(20), default='professional')
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    external_post_id = Column(String(100))
    engagement_score = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_sp_platform','platform'), Index('idx_sp_published','published'),
        Index('idx_sp_content','linked_content_id'))

class OGTagConfig(Base):
    """Open Graph标签配置表"""
    __tablename__ = 'og_tag_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_url = Column(String(500), unique=True, nullable=False)
    og_title = Column(String(300))
    og_description = Column(Text)
    og_image = Column(String(500))
    og_type = Column(String(30), default='article')
    og_site_name = Column(String(100))
    og_locale = Column(String(10))
    twitter_card = Column(String(20))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = ()

class ShareTracking(Base):
    """社交分享追踪表"""
    __tablename__ = 'share_trackings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    page_url = Column(String(500), nullable=False)
    platform = Column(String(30), nullable=False)
    share_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    last_tracked_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_st_url_platform','page_url','platform',unique=True),
        Index('idx_st_url','page_url'))

class UGCContentORM(Base):
    """用户生成内容(UGC)表"""
    __tablename__ = 'ugc_contents'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ugc_id = Column(String(12), unique=True, nullable=False)
    author_id = Column(String(64))
    author_name = Column(String(100))
    content = Column(Text, nullable=False)
    entity_ref = Column(String(50))
    rating = Column(Float)
    status = Column(String(20), default='pending_review')
    reward_points = Column(Integer, default=0)
    moderation_result = Column(String(20))
    moderated_by = Column(String(64))
    moderated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_ugc_entity','entity_ref'), Index('idx_ugc_author','author_id'),
        Index('idx_ugc_status','status'), Index('idx_ugc_created','created_at'))

class SEOAuditResult(Base):
    """SEO白帽审计结果表"""
    __tablename__ = 'seo_audit_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(12), unique=True, nullable=False)
    page_url = Column(String(500), nullable=False)
    risk_score = Column(Float, default=0)
    risk_level = Column(String(20), default='safe')
    passed = Column(Boolean, default=True)
    findings_json = Column(JSON)
    audited_at = Column(DateTime, default=datetime.utcnow)
    auditor = Column(String(64))
    __table_args__ = (Index('idx_sar_url','page_url'), Index('idx_sar_level','risk_level'),
        Index('idx_sar_passed','passed'), Index('idx_sar_audited','audited_at'))

class AlgorithmUpdateRecord(Base):
    """搜索引擎算法更新记录表"""
    __tablename__ = 'algorithm_update_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    update_name = Column(String(100), nullable=False)
    impact_area = Column(String(50))
    severity = Column(String(20), default='medium')
    detected_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    actions_taken_json = Column(JSON)
    traffic_impact_before = Column(Integer)
    traffic_impact_after = Column(Integer)
    resolved = Column(Boolean, default=False)
    __table_args__ = (Index('idx_aur_detected','detected_at'), Index('idx_aur_severity','severity'),
        Index('idx_aur_resolved','resolved'))

# =============================================================================
# Part 48: 轻量级命令执行沙箱 — 22表 (Layer 38)
# =============================================================================

class SandboxExecutionRecord(Base):
    """沙箱执行记录主表"""
    __tablename__ = 'sandbox_execution_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exec_id = Column(String(12), unique=True, nullable=False)
    trace_id = Column(String(20))
    user_id = Column(String(64), nullable=False)
    command_text = Column(Text, nullable=False)
    language = Column(String(20), default='python')
    status = Column(String(20), default='pending')
    stdout = Column(Text)
    stderr = Column(Text)
    return_code = Column(Integer, default=0)
    duration_ms = Column(Float, default=0)
    risk_score = Column(Float, default=0)
    cpu_timeout_sec = Column(Integer, default=10)
    memory_limit_mb = Column(Integer, default=256)
    work_dir = Column(String(500))
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('idx_ser_user','user_id'), Index('idx_ser_status','status'),
        Index('idx_ser_started','started_at'), Index('idx_ser_trace','trace_id'))

class DangerPatternORM(Base):
    """危险命令模式配置表"""
    __tablename__ = 'danger_patterns'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(12), unique=True, nullable=False)
    regex_pattern = Column(Text, nullable=False)
    description = Column(String(200))
    severity = Column(String(20), default='high')
    category = Column(String(50))
    enabled = Column(Boolean, default=True)
    match_count = Column(Integer, default=0)
    created_by = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('dp_severity','severity'), Index('dp_category','category'),
        Index('dp_enabled','enabled'))

class SandboxBlockLog(Base):
    """危险命令拦截日志"""
    __tablename__ = 'sandbox_block_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(12), unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    command_preview = Column(String(500))
    matched_pattern_id = Column(String(12))
    severity = Column(String(20))
    user_id = Column(String(64))
    ip_address = Column(String(45))
    __table_args__ = (Index('sbl_timestamp','timestamp'), Index('sbl_user','user_id'),
        Index('sbl_severity','severity'))

class EnvironmentPurifierConfig(Base):
    """环境净化器配置表"""
    __tablename__ = 'env_purifier_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    var_name = Column(String(100), unique=True, nullable=False)
    action = Column(String(10), nullable=False)  # allow/block
    is_builtin = Column(Boolean, default=False)
    description = Column(String(200))
    enabled = Column(Boolean, default=True)
    __table_args__ = ()

class BingbuExecutionHistory(Base):
    """兵部代码执行历史（海马体记忆）"""
    __tablename__ = 'bingbu_execution_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(String(12), unique=True, nullable=False)
    trace_id = Column(String(20), nullable=False)
    user_id = Column(String(64), nullable=False)
    command_text = Column(Text)
    status = Column(String(20))
    return_code = Column(Integer)
    duration_ms = Column(Float)
    result_summary = Column(String(500))
    memory_type = Column(String(30), default='code_execution')
    executed_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('beh_user','user_id'), Index('beh_executed','executed_at'),
        Index('beh_trace','trace_id'))

class SecurityPrecheckResult(Base):
    """刑部安全预检结果表"""
    __tablename__ = 'security_precheck_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(12), unique=True, nullable=False)
    code_hash = Column(String(64))  # SHA256 of code
    risk_score = Column(Float, default=0)
    risk_level = Column(String(20), default='safe')
    findings_json = Column(JSON)  # list of finding strings
    allowed = Column(Boolean, default=True)
    force_override = Column(Boolean, default=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('spr_risk_score','risk_score'), Index('spr_level','risk_level'),
        Index('spr_allowed','allowed'))

class UserExecutionQuota(Base):
    """用户执行配额表"""
    __tablename__ = 'user_execution_quotas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False)
    tier = Column(String(20), default='free')  # free/basic/premium
    daily_limit = Column(Integer, default=10)
    concurrent_limit = Column(Integer, default=2)
    used_today = Column(Integer, default=0)
    reset_at = Column(DateTime)
    last_used_at = Column(DateTime)
    total_lifetime = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index('ueq_tier','tier'), Index('ueq_reset','reset_at'))

class QuotaUsageLog(Base):
    """配额使用日志表"""
    __tablename__ = 'quota_usage_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)
    action = Column(String(20), default='execute')  # execute/release
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('qul_user','user_id'), Index('qul_timestamp','timestamp'))

class SandboxAuditLog(Base):
    """沙箱审计日志表（Elasticsearch备选）"""
    __tablename__ = 'sandbox_audit_logs'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    audit_id = Column(String(16), unique=True, nullable=False)
    trace_id = Column(String(20), nullable=False)
    user_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    command = Column(Text)
    args_json = Column(Text)
    result_summary = Column(String(500))
    return_code = Column(Integer)
    risk_score = Column(Float, default=0)
    approved_by = Column(String(20), default='auto')
    execution_duration_ms = Column(Float)
    ip_address = Column(String(45))
    user_agent = Column(String(300))
    retention_days = Column(Integer, default=180)
    __table_args__ = (Index('sal_trace','trace_id'), Index('sal_user','user_id'),
        Index('sal_timestamp','timestamp'))

class PrometheusMetricSnapshot(Base):
    """Prometheus指标快照表"""
    __tablename__ = 'prometheus_metric_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    labels_json = Column(JSON)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (Index('pms_name','metric_name'), Index('pms_recorded','recorded_at'))

class SandboxAlertEvent(Base):
    """沙箱告警事件表"""
    __tablename__ = 'sandbox_alert_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(12), unique=True, nullable=False)
    alert_type = Column(String(30), nullable=False)  # high_failure_rate/slow_execution
    message = Column(Text)
    severity = Column(String(20), default='warning')
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))
    __table_args__ = (Index('sae_type','alert_type'), Index('sae_resolved','resolved'),
        Index('sae_triggered','triggered_at'))

class DegradationEventLog(Base):
    """降级事件日志表"""
    __tablename__ = 'degradation_event_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(12), unique=True, nullable=False)
    from_mode = Column(String(20), nullable=False)
    to_mode = Column(String(20), nullable=False)
    reason = Column(String(300))
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    __table_args__ = (Index('del_timestamp','timestamp'), Index('del_resolved','resolved'))

class DockerSandboxConfig(Base):
    """Docker沙箱备选配置表"""
    __tablename__ = 'docker_sandbox_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String(50), unique=True, nullable=False)
    docker_image = Column(String(200), default='python:3.11-slim')
    memory_limit_mb = Column(Integer, default=256)
    cpu_limit = Column(Float, default=0.5)
    network_mode = Column(String(20), default='none')  # none/bridge/host
    timeout_sec = Column(Integer, default=60)
    enabled = Column(Boolean, default=False)
    priority = Column(Integer, default=1)  # 1=primary fallback, 2=secondary
    last_health_check = Column(DateTime)
    available = Column(Boolean, default=False)
    __table_args__ = (Index('dsc_enabled','enabled'), Index('dsc_available','available'))

class AsyncExecutionTask(Base):
    """异步执行任务队列表"""
    __tablename__ = 'async_execution_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(12), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(20), default='python')
    timeout_sec = Column(Integer)
    status = Column(String(20), default='pending')  # pending/running/completed/failed/cancelled
    result_ref = Column(String(12))  # FK to sandbox_execution_records
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    worker_id = Column(String(36))
    error_message = Column(Text)
    __table_args__ = (Index('aet_status','status'), Index('aet_user','user_id'),
        Index('aet_queued','queued_at'))

class ExecutionResultCache(Base):
    """执行结果格式化缓存表"""
    __tablename__ = 'execution_result_caches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_id = Column(String(16), unique=True, nullable=False)
    execution_id = Column(String(12))
    content_type = Column(String(20))  # json/csv/tsv/image_base64/text
    formatted_output = Column(Text)
    metadata_json = Column(JSON)  # headers, row_count etc.
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    hit_count = Column(Integer, default=0)
    __table_args__ = (Index('erc_expires','expires_at'), Index('erc_content_type','content_type'))

class SandboxHealthCheck(Base):
    """沙箱健康检查历史表"""
    __tablename__ = 'sandbox_health_checks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(12), unique=True, nullable=False)
    healthy = Column(Boolean, nullable=False)
    mode = Column(String(20), default='primary')
    temp_dir_ok = Column(Boolean, default=True)
    disk_space_mb = Column(Float)
    memory_available_mb = Column(Float)
    active_processes = Column(Integer, default=0)
    failure_streak = Column(Integer, default=0)
    success_streak = Column(Integer, default=0)
    checked_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index('shc_checked','checked_at'), Index('shc_healthy','healthy'))

class CodeExecutionTutorial(Base):
    """代码执行交互教程表"""
    __tablename__ = 'code_execution_tutorials'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tutorial_id = Column(String(12), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    step_order = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)
    example_code = Column(Text)
    expected_output = Column(Text)
    hint = Column(Text)
    language = Column(String(20), default='python')
    difficulty = Column(String(10), default='beginner')
    enabled = Column(Boolean, default=True)
    __table_args__ = (Index('cet_difficulty','difficulty'), Index('cet_language','language'),
        Index('cet_enabled','enabled'))

class UserGuideEntry(Base):
    """用户指南条目表"""
    __tablename__ = 'user_guide_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(12), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # getting-started/libraries/restrictions/troubleshooting
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    order_index = Column(Integer, default=0)
    visible_to = Column(String(20), default='all')  # all/free/basic/premium
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(64))
    __table_args__ = (Index('uge_category','category'), Index('uge_visible','visible_to'))


# ════════════════════════════════════════════════════════════════
# PART 49 — LAYER 39: CLAUDE CODE CORE CAPABILITY (Claude Code 核心能力开发)
# 9大模块: TaskDecomposer+ToolRegistry+FileSystemTools+CommandExecutionTool
#         +CodeGenDebugTools+StaticCodeScanner+ProgrammingContextManager
#         +SecurityConfirmationEngine+ClaudeCodeOrchestrator
# ════════════════════════════════════════════════════════════════

class TaskSpecRecord(Base):
    """任务规格记录表 — TaskDecomposer模块"""
    __tablename__ = 'task_spec_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spec_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    intent = Column(Text, nullable=False)
    task_type = Column(String(30), nullable=False)  # code_generate/code_modify/code_debug/command_execute/tool_call
    spec_json = Column(JSON, nullable=False)
    status = Column(String(20), default='pending')  # pending/running/completed/failed/cancelled
    subtask_count = Column(Integer, default=0)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float)
    completed_at = Column(Float)
    __table_args__ = (Index('tsr_user','user_id'), Index('tsr_status','status'),
        Index('tsr_type','task_type'))

class SubTaskRecord(Base):
    """子任务记录表"""
    __tablename__ = 'sub_task_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    subtask_id = Column(String(12), nullable=False)
    spec_id = Column(String(16), ForeignKey('task_spec_records.spec_id'), nullable=False)
    task_type = Column(String(30), nullable=False)  # analyze_requirement/generate_code/security_check/execute_command/etc.
    params_json = Column(JSON)
    depends_on = Column(JSON)  # list of subtask_ids
    status = Column(String(20), default='pending')
    result_json = Column(JSON)
    error_message = Column(Text)
    started_at = Column(Float)
    completed_at = Column(Float)
    order_index = Column(Integer, default=0)
    __table_args__ = (Index('str_spec','spec_id'), Index('str_status','status'),
        Index('str_type','task_type'))

class DAGDependencyEdge(Base):
    """DAG依赖边表"""
    __tablename__ = 'dag_dependency_edges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spec_id = Column(String(16), ForeignKey('task_spec_records.spec_id'), nullable=False)
    from_node = Column(String(12), nullable=False)
    to_node = Column(String(12), nullable=False)
    depth = Column(Integer, default=0)
    parallel_group = Column(Integer, default=-1)
    __table_args__ = (Index('dde_spec','spec_id'), Index('dde_from','from_node'),
        UniqueConstraint('spec_id','from_node','to_node',name='uq_dde_edge'))

class ToolRegistrationRecord(Base):
    """工具注册记录表 — ToolRegistry模块"""
    __tablename__ = 'tool_registration_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, default='')
    category = Column(String(20), nullable=False)  # filesystem/execution/code_gen/code_debug/utility
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    handler_reference = Column(String(200))
    enabled = Column(Boolean, default=True)
    call_count = Column(Integer, default=0)
    avg_duration_ms = Column(Float, default=0.0)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_called_at = Column(DateTime)
    __table_args__ = (Index('trr_category','category'), Index('trr_enabled','enabled'))

class ToolCallLogEntry(Base):
    """工具调用日志表"""
    __tablename__ = 'tool_call_log_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(16), unique=True, nullable=False)
    tool_name = Column(String(64), nullable=False)
    success = Column(Boolean, nullable=False)
    output_data = Column(JSON)
    error_message = Column(Text)
    duration_ms = Column(Float, default=0.0)
    trace_id = Column(String(32))
    params_json = Column(JSON)
    user_id = Column(String(64))
    session_id = Column(String(32))
    called_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('tcle_tool','tool_name'), Index('tcle_success','success'),
        Index('tcle_session','session_id'), Index('tcle_called','called_at'))

class FileOperationLog(Base):
    """文件操作日志表 — FileSystemTools模块"""
    __tablename__ = 'file_operation_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    op_id = Column(String(16), unique=True, nullable=False)
    operation = Column(String(20), nullable=False)  # read/write/list/delete
    file_path = Column(Text, nullable=False)
    workspace_root = Column(Text)
    success = Column(Boolean, nullable=False)
    size_bytes = Column(Integer)
    duration_ms = Column(Float, default=0.0)
    error_message = Column(Text)
    user_id = Column(String(64))
    operated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('fol_op','operation'), Index('fol_success','success'),
        Index('fol_path','file_path'), Index('fol_operated','operated_at'))

class CommandExecutionLog(Base):
    """命令执行日志表 — CommandExecutionTool模块"""
    __tablename__ = 'command_execution_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exec_id = Column(String(16), unique=True, nullable=False)
    command = Column(Text, nullable=False)
    cwd = Column(Text)
    timeout_seconds = Column(Integer, default=30)
    exit_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)
    success = Column(Boolean, nullable=False)
    duration_ms = Column(Float, default=0.0)
    whitelisted = Column(Boolean, default=True)
    risk_level = Column(String(10))  # safe/warning/dangerous/blocked
    user_id = Column(String(64))
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cel_success','success'), Index('cel_risk','risk_level'),
        Index('cel_executed','executed_at'))

class CodeGenerationRecord(Base):
    """代码生成/调试记录表 — CodeGenDebugTools模块"""
    __tablename__ = 'code_generation_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(16), unique=True, nullable=False)
    action = Column(String(20), nullable=False)  # generate/debug/explain/run_tests
    prompt_input = Column(Text)
    language = Column(String(20), default='python')
    generated_code = Column(Text)
    error_message = Column(Text)
    suggestions = Column(JSON)  # list of suggestion strings
    explanations = Column(JSON)  # list of explanation strings
    test_results = Column(JSON)  # list of test result dicts
    success = Column(Boolean, nullable=False)
    duration_ms = Column(Float, default=0.0)
    user_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cgr_action','action'), Index('cgr_language','language'),
        Index('cgr_success','success'))

class StaticScanResultRecord(Base):
    """静态代码扫描结果表 — StaticCodeScanner模块"""
    __tablename__ = 'static_scan_result_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(16), unique=True, nullable=False)
    code_snippet = Column(Text, nullable=False)
    filename_or_label = Column(String(200), default='<string>')
    risk_score = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)  # info/low/medium/high/critical
    suggestion = Column(Text)
    scanned_at = Column(Float, nullable=False)
    duration_ms = Column(Float, default=0.0)
    total_findings = Column(Integer, default=0)
    dangerous_funcs_found = Column(JSON)
    dangerous_mods_found = Column(JSON)
    __table_args__ = (Index('ssrr_severity','severity'), Index('ssrr_risk','risk_score'),
        Index('ssrr_scanned','scanned_at'))

class ScanFindingRecord(Base):
    """扫描发现明细表"""
    __tablename__ = 'scan_finding_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(16), unique=True, nullable=False)
    scan_id = Column(String(16), ForeignKey('static_scan_result_records.scan_id'), nullable=False)
    line_number = Column(Integer, default=0)
    severity = Column(String(20), nullable=False)  # info/low/medium/high/critical
    message = Column(Text, nullable=False)
    category = Column(String(30))  # dangerous_function/dangerous_module/large_file/few_comments/syntax_error
    weight_score = Column(Float, default=0.0)
    __table_args__ = (Index('sfr_scan','scan_id'), Index('sfr_severity','severity'),
        Index('sfr_category','category'))

class ProgrammingContextSnapshot(Base):
    """编程上下文快照表 — ProgrammingContextManager模块"""
    __tablename__ = 'programming_context_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    session_id = Column(String(32))
    recent_files = Column(JSON)
    recent_commands = Column(JSON)
    preferences = Column(JSON)
    context_size = Column(Integer, default=0)
    window_size = Column(Integer, default=20)
    compressed = Column(Boolean, default=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('pcs_user','user_id'), Index('pcs_session','session_id'),
        Index('pcs_captured','captured_at'))

class KnowledgeBaseEntry(Base):
    """知识库条目表"""
    __tablename__ = 'knowledge_base_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(16), unique=True, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(JSON)
    source = Column(String(50), default='internal')  # internal/user_imported/documentation
    embedding_sim = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    added_by = Column(String(64))
    added_at = Column(Float, nullable=False)
    last_accessed_at = Column(Float)
    __table_args__ = (Index('kbe_tags','tags'), Index('kbe_source','source'),
        Index('kbe_accessed','last_accessed_at'))

class CodeSnippetRecord(Base):
    """代码片段记录表"""
    __tablename__ = 'code_snippet_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snippet_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    title = Column(String(100), nullable=False)
    language = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON)
    is_public = Column(Boolean, default=False)
    share_link = Column(String(100))
    use_count = Column(Integer, default=0)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float)
    __table_args__ = (Index('csr_user','user_id'), Index('csr_language','language'),
        Index('csr_public','is_public'))

class ConfirmationRequestRecord(Base):
    """确认请求记录表 — SecurityConfirmationEngine模块"""
    __tablename__ = 'confirmation_request_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    operation = Column(Text, nullable=False)
    description = Column(Text)
    risk_level = Column(String(20), nullable=False)  # info/low/medium/high/critical
    token_hash = Column(String(32), nullable=False)
    state = Column(String(20), default='requested')  # requested/confirmed/rejected/expired
    confirmed_by = Column(String(64))
    expires_at = Column(Float, nullable=False)
    confirmed_at = Column(Float)
    rejected_at = Column(Float)
    __table_args__ = (Index('crr_user','user_id'), Index('crr_state','state'),
        Index('crr_expires','expires_at'))

class OrchestrationSession(Base):
    """编排会话记录表 — ClaudeCodeOrchestrator模块"""
    __tablename__ = 'orchestration_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    user_input = Column(Text, nullable=False)
    spec_id = Column(String(16), ForeignKey('task_spec_records.spec_id'))
    dag_node_count = Column(Integer, default=0)
    overall_status = Column(String(20), default='running')  # running/completed/failed/pending_confirmation
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(Float, nullable=False)
    completed_at = Column(Float)
    __table_args__ = (Index('os_user','user_id'), Index('os_status','overall_status'),
        Index('os_started','started_at'))

class OrchestrationStepResult(Base):
    """编排步骤结果表"""
    __tablename__ = 'orchestration_step_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    step_id = Column(String(16), unique=True, nullable=False)
    session_id = Column(String(16), ForeignKey('orchestration_sessions.session_id'), nullable=False)
    subtask_id = Column(String(12))
    step_order = Column(Integer, default=0)
    step_type = Column(String(30))  # security_check/generate_code/execute_command/etc.
    status = Column(String(20), nullable=False)  # completed/skipped/awaiting_confirmation/failed
    result_json = Column(JSON)
    risk_score = Column(Float)
    generated_output = Column(Text)
    confirm_request_id = Column(String(16))
    duration_ms = Column(Float, default=0.0)
    executed_at = Column(Float)
    __table_args__ = (Index('osr_session','session_id'), Index('osr_status','status'),
        Index('osr_type','step_type'))

class IntentRecognitionLog(Base):
    """意图识别日志表"""
    __tablename__ = 'intent_recognition_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(16), unique=True, nullable=False)
    user_input = Column(Text, nullable=False)
    detected_type = Column(String(30), nullable=False)
    confidence_score = Column(Float, nullable=False)
    keywords_matched = Column(JSON)
    processing_time_ms = Column(Float, default=0.0)
    user_id = Column(String(64))
    recognized_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('irl_type','detected_type'), Index('irl_confidence','confidence_score'),
        Index('irl_recognized','recognized_at'))

class ToolCategoryStatistic(Base):
    """工具分类统计表"""
    __tablename__ = 'tool_category_statistics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False)
    category = Column(String(20), nullable=False)
    total_tools = Column(Integer, default=0)
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_duration_ms = Column(Float, default=0.0)
    __table_args__ = (Index('tcs_date','stat_date'), Index('tcs_category','category'),
        UniqueConstraint('stat_date','category',name='uq_tcs_date_cat'))

class ContextCompressionLog(Base):
    """上下文压缩日志表"""
    __tablename__ = 'context_compression_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    compression_type = Column(String(20), nullable=False)  # commands/recent_files/all
    before_size = Column(Integer, default=0)
    after_size = Column(Integer, default=0)
    compression_ratio = Column(Float, default=0.0)
    threshold_used = Column(Integer, default=10)
    compressed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ccl_user','user_id'), Index('ccl_type','compression_type'),
        Index('ccl_compressed','compressed_at'))

class SecurityEventLog(Base):
    """安全事件日志表"""
    __tablename__ = 'security_event_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(16), unique=True, nullable=False)
    event_type = Column(String(30), nullable=False)  # high_risk_detected/confirmed/rejected/expired/blocked
    operation = Column(Text)
    risk_level = Column(String(20))
    user_id = Column(String(64))
    request_id = Column(String(16))  # FK to confirmation_request_records
    details_json = Column(JSON)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('sel_type','event_type'), Index('sel_risk','risk_level'),
        Index('sel_resolved','resolved'), Index('sel_occurred','occurred_at'))

class WorkspaceWhitelistEntry(Base):
    """工作空间白名单条目表"""
    __tablename__ = 'workspace_whitelist_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    path_absolute = Column(Text, nullable=False)
    path_display = Column(String(300))
    permissions = Column(String(20), default='read_write')  # read_only/read_write/full
    enabled = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime)
    __table_args__ = (Index('wwe_user','user_id'), Index('wwe_enabled','enabled'),
        Index('wwe_path','path_absolute'))


# ════════════════════════════════════════════════════════════════
# PART 50 — LAYER 40: CODE EXECUTION DEEP INTEGRATION (代码执行能力深度集成)
# 12大模块: BingbuAsyncExecutor+LibuCodeAssistant+GongbuCodeGenPro+ZhongshuV2
#         +ShangshuLoadBalancer+LibuCodeMemory+XingbuRealtimeMonitor
#         +UserRiskProfiler+CultivationCodeFusion+TeamCodeCollaboration+Orchestrator
# ════════════════════════════════════════════════════════════════

class AsyncExecutionTask(Base):
    """异步执行任务表 — BingbuAsyncExecutor模块"""
    __tablename__ = 'async_execution_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    language = Column(String(20), nullable=False)  # python/javascript/shell/r
    code_hash = Column(String(32))
    code_preview = Column(Text)
    status = Column(String(20), default='queued')  # queued/running/success/error/timeout/blocked
    trace_id = Column(String(32))
    stdout = Column(Text)
    stderr = Column(Text)
    return_code = Column(Integer)
    duration_ms = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    error_message = Column(Text)
    worker_node = Column(String(50))
    priority = Column(Integer, default=1)  # 0=low 1=normal 2=high 3=urgent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    __table_args__ = (Index('aet_user','user_id'), Index('aet_status','status'),
        Index('aet_language','language'), Index('aet_created','created_at'))

class ExecutionWorkerNode(Base):
    """执行工作节点表 — 负载均衡"""
    __tablename__ = 'execution_worker_nodes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(30), unique=True, nullable=False)
    host = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    max_tasks = Column(Integer, default=5)
    active_tasks = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0.0)
    total_assigned = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    is_online = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ewn_online','is_online'), Index('ewn_host','host'))

class CodeAssistantInteraction(Base):
    """编程对话交互记录表 — LibuCodeAssistant模块"""
    __tablename__ = 'code_assistant_interactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    session_id = Column(String(32))
    user_message = Column(Text, nullable=False)
    parsed_code_blocks = Column(Integer, default=0)
    bot_action = Column(String(50))  # run_suggestion/explain/optimize/code_assist
    suggestion_ids = Column(JSON)  # list of suggestion IDs
    user_response = Column(Text)
    interaction_duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cai_user','user_id'), Index('cai_session','session_id'),
        Index('cai_action','bot_action'))

class CodeGenerationRecordPro(Base):
    """代码生成记录Pro版表 — GongbuCodeGenPro模块"""
    __tablename__ = 'code_generation_records_pro'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64))
    prompt_input = Column(Text)
    language = Column(String(20), default='python')
    style = Column(String(20), default='pep8')  # pep8/test_template/custom
    generated_code = Column(Text)
    suggestion_id = Column(String(16))
    confidence = Column(Float, default=0.0)
    template_used = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cgpr_language','language'), Index('cgpr_style','style'))

class CodeDebugSession(Base):
    """代码调试会话表"""
    __tablename__ = 'code_debug_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64))
    original_code = Column(Text, nullable=False)
    error_message = Column(Text)
    error_type = Column(String(30))  # SyntaxError/NameError/TypeError/IndentationError/etc.
    fixes_applied = Column(JSON)  # list of fix strings
    issues_found = Column(JSON)  # list of issue dicts
    debug_duration_ms = Column(Float, default=0.0)
    fixed_successfully = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cds_error_type','error_type'), Index('cds_fixed','fixed_successfully'))

class CodeReviewReportL40(Base):
    """代码审查报告表 — Gongbu Pro review"""
    __tablename__ = 'code_review_reports_l40'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(16), unique=True, nullable=False)
    code_hash = Column(String(32), nullable=False)
    complexity_score = Column(Float, default=0.0)
    overall_grade = Column(String(2))  # A/B/C/D
    security_issues = Column(JSON)  # list of security issue dicts
    performance_issues = Column(JSON)
    style_issues = Column(JSON)
    optimization_suggestions = Column(JSON)  # list of suggestion strings
    review_duration_ms = Column(Float, default=0.0)
    reviewer_type = Column(String(20), default='auto')  # auto/manual/hybrid
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('crll_grade','overall_grade'), Index('crll_reviewer','reviewer_type'))

class CodeModificationHistory(Base):
    """代码修改历史表"""
    __tablename__ = 'code_modification_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(String(16), unique=True, nullable=False)
    session_id = Column(String(16), nullable=False)
    version_number = Column(Integer, default=0)
    code_content = Column(Text, nullable=False)
    modification_request = Column(Text)
    diff_summary = Column(Text)
    modified_by = Column(String(64))  # user_id or 'auto'
    modified_at = Column(Float, nullable=False)
    __table_args__ = (Index('cmh_session','session_id'), Index('cmh_version','version_number'))

class CompositeTaskSpec(Base):
    """复合任务规格表 — ZhongshuTaskDecomposerV2"""
    __tablename__ = 'composite_task_specs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    spec_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    input_text = Column(Text, nullable=False)
    pattern_matched = Column(String(100))  # regex pattern that matched
    is_composite = Column(Boolean, default=False)
    subtask_count = Column(Integer, default=0)
    status = Column(String(20), default='pending')  # pending/running/completed/failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    __table_args__ = (Index('cts_user','user_id'), Index('cts_status','status'),
        Index('cts_composite','is_composite'))

class CompositeSubTask(Base):
    """复合子任务表"""
    __tablename__ = 'composite_subtasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    subtask_id = Column(String(14), unique=True, nullable=False)
    spec_id = Column(String(16), ForeignKey('composite_task_specs.spec_id'), nullable=False)
    task_type = Column(String(30), nullable=False)  # code_generate/code_execute/data_analyze/etc.
    params_json = Column(JSON)
    depends_on = Column(JSON)  # list of subtask_ids
    order_index = Column(Integer, default=0)
    status = Column(String(20), default='pending')
    result_json = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    __table_args__ = (Index('cst_spec','spec_id'), Index('cst_status','status'),
        Index('cst_type','task_type'))

class TaskAssignmentRecord(Base):
    """任务分配记录表 — ShangshuLoadBalancer"""
    __tablename__ = 'task_assignment_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(String(16), unique=True, nullable=False)
    task_id = Column(String(16), nullable=False)
    worker_id = Column(String(30), ForeignKey('execution_worker_nodes.node_id'), nullable=False)
    priority = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)
    status = Column(String(20), default='assigned')  # assigned/completed/failed/retried
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    failure_reason = Column(Text)
    __table_args__ = (Index('tar_worker','worker_id'), Index('tar_status','status'),
        Index('tar_assigned','assigned_at'))

class CodeMemoryEntry(Base):
    """代码记忆条目表 — LibuCodeMemory"""
    __tablename__ = 'code_memory_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    code_hash = Column(String(32), nullable=False)
    code_preview = Column(Text)
    output_summary = Column(Text)
    language = Column(String(20), default='python')
    success = Column(Boolean, nullable=False)
    importance = Column(Float, default=5.0)
    access_count = Column(Integer, default=0)
    similarity_vector = Column(JSON)  # simulated embedding
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime)
    __table_args__ = (Index('cme_user','user_id'), Index('cme_success','success'),
        Index('cme_accessed','last_accessed_at'))

class SharedCodeSnippetL40(Base):
    """共享代码片段表 — Team Code Collaboration"""
    __tablename__ = 'shared_code_snippets_l40'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(14), unique=True, nullable=False)
    team_id = Column(String(20))  # FK to team table
    repo_id = Column(String(16))  # FK to team_code_repo
    author_id = Column(String(64), nullable=False)
    title = Column(String(100), nullable=False)
    language = Column(String(20), nullable=False)
    code = Column(Text, nullable=False)
    description = Column(Text)
    version = Column(Integer, default=1)
    is_shared = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    tags = Column(JSON)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float)
    __table_args__ = (Index('scsl_team','team_id'), Index('scsl_author','author_id'),
        Index('scsl_lang','language'), Index('scsl_shared','is_shared'))

class UserCodingProfile(Base):
    """用户编程画像表"""
    __tablename__ = 'user_coding_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), unique=True, nullable=False)
    indent_style = Column(String(10), default='space')  # space/tab
    indent_size = Column(Integer, default=4)
    preferred_libs = Column(JSON)  # list of library names
    complexity_tolerance = Column(String(10), default='medium')  # low/medium/high
    favorite_language = Column(String(20), default='python')
    coding_frequency = Column(String(10), default='occasional')  # daily/weekly/occasional
    total_code_lines_written = Column(Integer, default=0)
    preferred_framework = Column(String(30))
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ucp_freq','coding_frequency'), Index('ucp_lang','favorite_language'))

class RealtimeSecurityAlert(Base):
    """实时安全告警表 — XingbuRealtimeMonitor"""
    __tablename__ = 'realtime_security_alerts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(16), unique=True, nullable=False)
    rule_id = Column(String(30), nullable=False)
    severity = Column(String(15), nullable=False)  # high/medium/low
    action_taken = Column(String(20), nullable=False)  # interrupt/log_only/warn
    rule_description = Column(Text)
    event_snapshot = Column(JSON)
    should_interrupt = Column(Boolean, default=False)
    trace_id = Column(String(32))
    user_id = Column(String(64))
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))
    __table_args__ = (Index('rsa_severity','severity'), Index('rsa_rule','rule_id'),
        Index('rsa_triggered','triggered_at'), Index('rsa_interrupt','should_interrupt'))

class MonitorAlertRule(Base):
    """监控告警规则配置表"""
    __tablename__ = 'monitor_alert_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(30), unique=True, nullable=False)
    pattern_expression = Column(Text, nullable=False)  # e.g., "file_read_count>50"
    severity = Column(String(15), nullable=False)
    action = Column(String(20), nullable=False)  # interrupt/log_only/warn
    description = Column(Text)
    is_enabled = Column(Boolean, default=True)
    alert_count_triggered = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime)
    __table_args__ = (Index('mar_enabled','is_enabled'), Index('mar_severity','severity'))

class UserProfileRisk(Base):
    """用户风险画像表 — UserRiskProfiler"""
    __tablename__ = 'user_profile_risks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), unique=True, nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(15), default='safe')  # safe/low/medium/high/critical
    dangerous_executions = Column(Integer, default=0)
    blocked_attempts = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    reputation = Column(Float, default=100.0)
    factors_json = Column(JSON)  # dangerous_ratio/block_rate/success_rate
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    weekly_recalc_next = Column(DateTime)
    __table_args__ = (Index('upr_level','risk_level'), Index('upr_score','risk_score'),
        Index('upr_reputation','reputation'))

class CultivationCodeReward(Base):
    """修仙×代码奖励记录表 — CultivationCodeFusion"""
    __tablename__ = 'cultivation_code_rewards'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reward_id = Column(String(14), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    action_type = Column(String(30), nullable=False)  # python_success/python_dangerous/snippet_shared/etc.
    exp_gained = Column(Integer, default=0)
    bonus_multiplier = Column(Float, default=1.0)
    reason = Column(Text)
    realm_at_time = Column(Integer, default=1)
    streak_bonus = Column(Integer, default=0)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ccr_user','user_id'), Index('ccr_action','action_type'),
        Index('ccr_granted','granted_at'))

class RealmCodePermission(Base):
    """境界代码权限映射表"""
    __tablename__ = 'realm_code_permissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_id = Column(String(14), unique=True, nullable=False)
    realm_level = Column(Integer, nullable=False)  # 1-4
    allowed_languages = Column(JSON)  # list of supported languages
    timeout_seconds = Column(Integer, default=30)
    memory_limit_mb = Column(Integer, default=256)
    unlocked_operations = Column(JSON)  # list of operation names
    __table_args__ = (Index('rcp_realm','realm_level'), UniqueConstraint('realm_level','allowed_languages',name='uq_rcp_realm_lang'))

class TeamCodeRepository(Base):
    """团队代码仓库表 — TeamCodeCollaboration"""
    __tablename__ = 'team_code_repositories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String(14), unique=True, nullable=False)
    team_id = Column(String(20), nullable=False)
    repo_name = Column(String(100), nullable=False)
    owner_id = Column(String(64), nullable=False)
    members_can_write = Column(Boolean, default=True)
    entry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime)
    __table_args__ = (Index('tcr_team','team_id'), Index('tcr_owner','owner_id'))

class TeamCodeReviewRequest(Base):
    """团队代码审查请求表"""
    __tablename__ = 'team_code_review_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(14), unique=True, nullable=False)
    repo_id = Column(String(14), ForeignKey('team_code_repositories.repo_id'))
    entry_id = Column(String(14), ForeignKey('shared_code_snippets_l40.entry_id'))
    requester_id = Column(String(64), nullable=False)
    status = Column(String(20), default='pending')  # pending/in_progress/completed/cancelled
    result_report_id = Column(String(16))  # FK to code_review_reports_l40
    reviewer_id = Column(String(64))
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    __table_args__ = (Index('tcrr_repo','repo_id'), Index('tcrr_status','status'),
        Index('tcrr_requester','requester_id'))

class TeamCodeComment(Base):
    """团队代码评论表"""
    __tablename__ = 'team_code_comments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(14), unique=True, nullable=False)
    repo_id = Column(String(14), ForeignKey('team_code_repositories.repo_id'))
    entry_id = Column(String(14))
    author_id = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(String(14))  # for threaded replies
    line_reference = Column(Integer)  # optional line number reference
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('tcc_repo','repo_id'), Index('tcc_author','author_id'),
        Index('tcc_entry','entry_id'))

class OrchestrationPipelineRun(Base):
    """编排流水线运行记录表 — CodeExecutionOrchestrator"""
    __tablename__ = 'orchestration_pipeline_runs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    user_input = Column(Text, nullable=False)
    spec_id = Column(String(16), ForeignKey('composite_task_specs.spec_id'))
    trace_id = Column(String(32))
    permission_decision = Column(String(20))  # allow/deny/confirm_required
    total_subtasks = Column(Integer, default=0)
    completed_subtasks = Column(Integer, default=0)
    cultivation_exp_before = Column(Integer, default=0)
    cultivation_exp_after = Column(Integer, default=0)
    security_alert_count = Column(Integer, default=0)
    overall_status = Column(String(20), default='running')  # running/completed/failed/partial
    duration_ms = Column(Float, default=0.0)
    results_json = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    __table_args__ = (Index('opr_user','user_id'), Index('opr_status','overall_status'),
        Index('opr_started','started_at'))


# ════════════════════════════════════════════════════════════════
# PART 51 — LAYER 41: CULTIVATION DEEP FUSION (修仙机制与全模块深度融合)
# 10大模块: RealmStyleAdapter+CultivationTaskEngine+RealmFeatureGate+AnalysisExpReward
#         +MarketRealmGate+AgentResonance+TeamRealmSystem+PointsExchange
#         +CompliancePrivacyFusion+AgentCapabilityScaling+Orchestrator
# ════════════════════════════════════════════════════════════════

class UserProfileRealm(Base):
    """用户境界档案表"""
    __tablename__ = 'user_profile_realms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), unique=True, nullable=False)
    current_realm = Column(String(20), nullable=False)  # lianqi/zhuji/jindan/yuanying/huashen/dacheng
    realm_level = Column(Integer, default=1)  # numeric level within realm
    total_exp = Column(Integer, default=0)
    total_exp_earned = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    max_streak_days = Column(Integer, default=0)
    last_login_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    style_complexity = Column(String(15), default='normal')  # simple/normal/professional/expert
    __table_args__ = (Index('upr_realm','current_realm'), Index('upr_streak','streak_days'))

class RealmBreakthroughLog(Base):
    """境界突破记录表"""
    __tablename__ = 'realm_breakthrough_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    from_realm = Column(String(20), nullable=False)
    to_realm = Column(String(20), nullable=False)
    points_rewarded = Column(Integer, default=0)
    new_features_unlocked = Column(JSON)  # list of feature IDs
    breakthrough_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('rbl_user','user_id'), Index('rbl_to','to_realm'))

class CultivationTaskTemplate(Base):
    """修炼任务模板表 — CultivationTaskEngine"""
    __tablename__ = 'cultivation_task_templates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(14), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(20))  # daily/weekly/milestone/challenge
    target_count = Column(Integer, default=1)
    exp_reward = Column(Integer, default=10)
    required_realm = Column(String(20))  # optional realm gate
    is_active = Column(Boolean, default=True)
    __table_args__ = (Index('ctt_category','category'), Index('ctt_active','is_active'))

class UserCultivationTask(Base):
    """用户修炼任务实例表"""
    __tablename__ = 'user_cultivation_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_instance_id = Column(String(18), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    template_id = Column(String(14), ForeignKey('cultivation_task_templates.template_id'))
    status = Column(String(20), default='active')  # active/completed/expired/cancelled
    current_progress = Column(Integer, default=0)
    target_count = Column(Integer, default=1)
    exp_reward = Column(Integer, default=10)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    __table_args__ = (Index('uct_user','user_id'), Index('uct_status','status'),
        Index('uct_template','template_id'))

class ExpTransactionRecord(Base):
    """经验值交易记录表"""
    __tablename__ = 'exp_transaction_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    amount = Column(Integer, nullable=False)  # positive=gain, negative=penalty
    source_type = Column(String(40), nullable=False)  # action/task/breakthrough/exchange/etc.
    reason = Column(Text)
    balance_after = Column(Integer, default=0)
    related_task_id = Column(String(18))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('etr_user','user_id'), Index('etr_source','source_type'),
        Index('etr_timestamp','timestamp'))

class FeatureUnlockRecord(Base):
    """功能解锁记录表 — RealmFeatureGate"""
    __tablename__ = 'feature_unlock_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    unlock_id = Column(String(16), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    feature_id = Column(String(40), nullable=False)
    feature_name = Column(String(100))
    unlocked_by_realm = Column(String(20), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('fur_user','user_id'), Index('fur_feature','feature_id'))

class AnalysisRewardRecord(Base):
    """分析经验值奖励记录表 — AnalysisExpReward"""
    __tablename__ = 'analysis_reward_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reward_id = Column(String(14), unique=True, nullable=False)
    user_id = Column(String(64))
    report_type = Column(String(30))  # single_panel/multi_panel/custom_factors/etc.
    base_exp = Column(Integer, default=0)
    multiplier = Column(Float, default=1.0)
    bonus_exp = Column(Integer, default=0)
    total_actual = Column(Integer, default=0)
    used_advanced_feature = Column(Boolean, default=False)
    rewarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('arr_report_type','report_type'), Index('arr_user','user_id'))

class AgentRecruitAttempt(Base):
    """智能体招募尝试记录表 — MarketRealmGate"""
    __tablename__ = 'agent_recruit_attempts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(String(14), unique=True, nullable=False)
    user_id = Column(User, nullable=False)
    agent_name = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    user_realm_at_time = Column(String(20))
    points_spent = Column(Integer, default=0)
    reason_if_failed = Column(Text)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ara_agent','agent_name'), Index('ara_success','success'))

class SkillPurchaseRecord(Base):
    """技能购买记录表"""
    __tablename__ = 'skill_purchase_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(String(14), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    skill_name = Column(String(50), nullable=False)
    skill_tier = Column(Integer, default=1)
    price_points = Column(Integer, default=0)
    success = Column(Boolean, nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('spr_skill','skill_name'), Index('spr_user','user_id'))

class AgentResonanceEventL41(Base):
    """智能体共鸣事件表 — AgentResonance"""
    __tablename__ = 'agent_resonance_events_l41'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(12), unique=True, nullable=False)
    agent_id = Column(String(30), nullable=False)
    agent_name = Column(String(50), nullable=False)
    owner_id = Column(String(64), nullable=False)
    old_level = Column(Integer, default=1)
    new_level = Column(Integer, default=1)
    base_exp = Column(Integer, default=0)
    milestone_bonus = Column(Integer, default=0)
    multiplier = Column(Float, default=1.0)
    final_exp_granted = Column(Integer, default=0)
    triggered_resonance = Column(Boolean, default=False)
    resonance_effect = Column(Text)  # description of visual/audio effect
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('arel_owner','owner_id'), Index('arel_resonance','triggered_resonance'))

class TeamRealmProfile(Base):
    """团队境界档案表 — TeamRealmSystem"""
    __tablename__ = 'team_realm_profiles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(20), unique=True, nullable=False)
    team_realm = Column(String(20), nullable=False)
    avg_member_realm_value = Column(Float, default=0.0)
    member_count = Column(Integer, default=1)
    total_skill_points = Column(Integer, default=0)
    used_skill_points = Column(Integer, default=0)
    total_exp_contributed = Column(Integer, default=0)
    last_realm_change = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('trp_team_realm','team_realm'), Index('trp_members','member_count'))

class TeamSkillTreeEntry(Base):
    """团队技能树条目表"""
    __tablename__ = 'team_skill_tree_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(14), unique=True, nullable=False)
    team_id = Column(String(20), ForeignKey('team_realm_profiles.team_id'), nullable=False)
    skill_name = Column(String(50), nullable=False)
    effect_description = Column(Text)
    cost_skill_points = Column(Integer, default=0)
    required_team_realm = Column(String(20))
    is_active = Column(Boolean, default=True)
    acquired_at = Column(DateTime)
    acquired_by = Column(String(64))
    __table_args__ = (Index('tste_team','team_id'), Index('tste_active','is_active'))

class TeamCultivationTask(Base):
    """团队修炼任务表"""
    __tablename__ = 'team_cultivation_tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(12), unique=True, nullable=False)
    team_id = Column(String(20), ForeignKey('team_realm_profiles.team_id'), nullable=False)
    name = Column(String(100), nullable=False)
    target_description = Column(Text)
    progress = Column(Integer, default=0)
    target_count = Column(Integer, default=1)
    exp_per_member = Column(Integer, default=0)
    status = Column(String(20), default='active')
    contributing_members = Column(JSON)  # list of user_ids
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    __table_args__ = (Index('tct_team','team_id'), Index('tct_status','status'))

class PointsExchangeRecord(Base):
    """积分兑换记录表 — PointsExchange"""
    __tablename__ = 'points_exchange_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange_id = Column(String(12), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    exchange_type = Column(String(20), nullable=False)  # exp_exchange/breakthrough/purchase
    points_spent = Column(Integer, default=0)
    exp_gained = Column(Integer, default=0)
    remaining_daily_cap = Column(Integer)
    success = Column(Boolean, default=True)
    exchanged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('per_user','user_id'), Index('per_type','exchange_type'))

class PrivacySettingRecord(Base):
    """隐私设置记录表 — CompliancePrivacyFusion"""
    __tablename__ = 'privacy_setting_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_id = Column(String(14), unique=True, nullable=False)
    user_id = Column(String(64), unique=True, nullable=False)
    visibility_mode = Column(String(15), default='private')  # public/friends_only/private
    friends_list = Column(JSON)  # list of user_ids for friends_only mode
    show_realm_to_others = Column(Boolean, default=False)
    show_exp_to_others = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('psr_visibility','visibility_mode'))

class ComplianceAuditEventL41(Base):
    """合规审计事件表"""
    __tablename__ = 'compliance_audit_events_l41'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(12), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    audit_type = Column(String(30), nullable=False)  # behavior_audit/manual_review/system_check
    severity = Column(String(15), default='LOW')  # LOW/MEDIUM/HIGH/CRITICAL
    description = Column(Text)
    risk_score = Column(Float, default=0.0)
    penalty_exp = Column(Integer, default=0)
    is_violation = Column(Boolean, default=False)
    violation_category = Column(String(30))  # spam/fraud/exploit/etc.
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(64))
    resolved_at = Column(DateTime)
    audited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cael_severity','severity'), Index('cael_violation','is_violation'),
        Index('cael_audited','audited_at'))

class PrivacyExemptionRequest(Base):
    """隐私豁免申请表"""
    __tablename__ = 'privacy_exemption_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(10), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    user_realm_at_request = Column(String(20))
    reason = Column(Text)
    status = Column(String(20), default='pending')  # pending/approved/rejected
    approved_by = Column(String(64))
    approved_at = Column(DateTime)
    expires_at = Column(DateTime)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('per_status','status'), Index('per_user','user_id'))

class CapabilityScalingConfig(Base):
    """能力缩放配置表 — AgentCapabilityScaling"""
    __tablename__ = 'capability_scaling_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(String(12), unique=True, nullable=False)
    agent_type = Column(String(20), nullable=False)  # bingbu/hubu/xingbu/li
    realm_tier = Column(String(20), nullable=False)
    config_json = Column(JSON)  # {risk_levels, timeout, concurrency, cache_bonus, tolerance, memory_limit}
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('csc_agent','agent_type'), Index('csc_realm','realm_tier'),
        UniqueConstraint('agent_type','realm_tier',name='uq_csc_agent_realm'))

class CultivationDashboardSnapshot(Base):
    """修仙仪表盘快照表 — Orchestrator"""
    __tablename__ = 'cultivation_dashboard_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(14), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    realm = Column(String(20))
    total_exp = Column(Integer, default=0)
    unlocked_features_count = Column(Integer, default=0)
    locked_features_count = Column(Integer, default=0)
    active_tasks_count = Column(Integer, default=0)
    completed_tasks_count = Column(Integer, default=0)
    bingbu_config = Column(JSON)
    hubu_config = Column(JSON)
    memory_limit = Column(Integer)
    xingbu_tolerance = Column(Float)
    privacy_visibility = Column(String(15))
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('cds_user','user_id'), Index('cds_captured','captured_at'))


# =============================================================================
# 第五十二部分：红蓝对抗系统 (red_blue_adversarial) — Layer 42
# =============================================================================
# 自博弈对抗训练系统ORM模型，涵盖攻击脚本、防御规则、对抗竞技场、
# 训练控制器、修仙融合等6大模块，共17个表

class AdversarialAttackScript(Base):
    """红队攻击脚本表"""
    __tablename__ = 'adversarial_attack_scripts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(String(20), unique=True, nullable=False)
    attack_type = Column(String(30), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(10), default='python')
    generation = Column(Integer, default=0)
    parent_script_id = Column(String(20), ForeignKey('adversarial_attack_scripts.script_id'))
    mutation_ops = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('aas_type','attack_type'), Index('aas_gen','generation'),
        Index('aas_parent','parent_script_id'))

class AdversarialDefenseRule(Base):
    """蓝队防御规则表"""
    __tablename__ = 'adversarial_defense_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(16), unique=True, nullable=False)
    pattern = Column(String(200), nullable=False)
    description = Column(String(100))
    level = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('adr_level','level'), Index('adr_active','is_active'))

class AdversarialBattleRecord(Base):
    """对抗战斗记录表"""
    __tablename__ = 'adversarial_battle_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    battle_id = Column(String(24), unique=True, nullable=False)
    round_num = Column(Integer, nullable=False)
    red_script_id = Column(String(20), ForeignKey('adversarial_attack_scripts.script_id'))
    blue_defense_code = Column(Text)
    outcome = Column(String(15), nullable=False)
    red_score = Column(Float, default=0.0)
    blue_score = Column(Float, default=0.0)
    details = Column(JSON)
    duration_sec = Column(Float)
    battle_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('abr_round','round_num'), Index('abr_outcome','outcome'),
        Index('abr_time','battle_at'))

class AdversarialTrainingSession(Base):
    """自博弈训练会话表"""
    __tablename__ = 'adversarial_training_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(20), unique=True, nullable=False)
    cycle_rounds = Column(Integer, default=100)
    red_win_rate = Column(Float, default=0.5)
    blue_win_rate = Column(Float, default=0.5)
    total_battles = Column(Integer, default=0)
    red_policy_json = Column(JSON)
    blue_policy_json = Column(JSON)
    fine_tune_triggered = Column(Boolean, default=False)
    actions_taken = Column(JSON)
    duration_sec = Column(Float)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    __table_args__ = (Index('ats_started','started_at'))

class AdversarialUserChallenge(Base):
    """用户挑战提交表"""
    __tablename__ = 'adversarial_user_challenges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    challenge_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    side = Column(String(6), nullable=False)
    script_code = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    evaluated = Column(Boolean, default=False)
    result_json = Column(JSON)
    exp_award = Column(Float, default=0.0)
    points_award = Column(Float, default=0.0)
    __table_args__ = (Index('auc_user','user_id'), Index('auc_side','side'),
        Index('auc_submitted','submitted_at'))

class AdversarialTournament(Base):
    """对抗锦标赛表"""
    __tablename__ = 'adversarial_tournaments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(String(16), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(15), default='active')
    participant_count = Column(Integer, default=0)
    rankings_json = Column(JSON)
    prize_pool = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('at_status','status'), Index('at_time_range','start_time','end_time'))

class AdversarialLeaderboardEntry(Base):
    """排行榜条目表"""
    __tablename__ = 'adversarial_leaderboard_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(18), unique=True, nullable=False)
    category = Column(String(20), nullable=False)
    user_id = Column(String(64), nullable=False)
    rank_pos = Column(Integer)
    total_exp = Column(Float, default=0.0)
    total_points = Column(Float, default=0.0)
    wins = Column(Integer, default=0)
    submissions = Column(Integer, default=0)
    titles_json = Column(JSON)
    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ale_cat_user','category','user_id'), Index('ale_rank','rank_pos'))

class AdversarialMutationSeed(Base):
    """遗传算法变异种子表"""
    __tablename__ = 'adversarial_mutation_seeds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(String(18), unique=True, nullable=False)
    parent_script_id = Column(String(20), ForeignKey('adversarial_attack_scripts.script_id'))
    mutation_ops_applied = Column(JSON)
    success_rate = Column(Float)
    fitness_score = Column(Float)
    generation_num = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ams_parent','parent_script_id'), Index('ams_gen','generation_num'))

class AdversarialDefenseStrategy(Base):
    """部署的防御策略表"""
    __tablename__ = 'adversarial_defense_strategies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(18), unique=True, nullable=False)
    name = Column(String(60))
    defense_code = Column(Text, nullable=False)
    rules_count = Column(Integer, default=0)
    block_rate = Column(Float)
    total_training_rounds = Column(Integer, default=0)
    is_deployed = Column(Boolean, default=False)
    deployed_at = Column(DateTime)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('ads_deployed','is_deployed'), Index('ads_version','version'))

class AdversarialEvaluationResult(Base):
    """对抗评估结果表"""
    __tablename__ = 'adversarial_evaluation_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    eval_id = Column(String(20), unique=True, nullable=False)
    battle_id = Column(String(24), ForeignKey('adversarial_battle_records.battle_id'))
    evaluator_type = Column(String(15), nullable=False)
    verdict = Column(String(20))
    risk_score = Column(Float)
    details_json = Column(JSON)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('aer_battle','battle_id'), Index('aer_evaluator','evaluator_type'))

class AdversarialRewardRecord(Base):
    """对抗奖励记录表"""
    __tablename__ = 'adversarial_reward_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reward_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)
    reward_type = Column(String(25), nullable=False)
    exp_amount = Column(Float, default=0.0)
    points_amount = Column(Float, default=0.0)
    reason = Column(String(100))
    related_challenge_id = Column(String(20), ForeignKey('adversarial_user_challenges.challenge_id'))
    awarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('arr_user','user_id'), Index('arr_type','reward_type'),
        Index('arr_awarded','awarded_at'))

class SecurityTitleDef(Base):
    """安全称号定义表"""
    __tablename__ = 'security_title_defs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title_key = Column(String(25), unique=True, nullable=False)
    title_label = Column(String(30), nullable=False)
    threshold_exp = Column(Float, nullable=False)
    description = Text
    privileges_json = Column(JSON)
    icon_emoji = Column(String(4))
    sort_order = Column(Integer, default=0)
    __table_args__ = (Index('std_sort','sort_order'))

class UserSecurityTitle(Base):
    """用户安全称号关联表"""
    __tablename__ = 'user_security_titles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)
    title_key = Column(String(25), ForeignKey('security_title_defs.title_key'), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(String(20), default='system')
    __table_args__ = (UniqueConstraint('user_id','title_key',name='uq_user_title'),
        Index('ust_user','user_id'))

class AdversarialABTestRecord(Base):
    """A/B测试记录表"""
    __tablename__ = 'adversarial_ab_test_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ab_test_id = Column(String(20), unique=True, nullable=False)
    strategy_a_id = Column(String(18), ForeignKey('adversarial_defense_strategies.strategy_id'))
    strategy_b_id = Column(String(18), ForeignKey('adversarial_defense_strategies.strategy_id'))
    a_block_rate = Column(Float)
    b_block_rate = Column(Float)
    winner = Column(String(2))
    test_case_count = Column(Integer)
    details_json = Column(JSON)
    tested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('aat_winner','winner'), Index('aat_tested','tested_at'))

class AdversarialPolicyState(Base):
    """强化学习策略状态表"""
    __tablename__ = 'adversarial_policy_states'
    id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(String(18), unique=True, nullable=False)
    team = Column(String(6), nullable=False)
    param_exploration = Column(Float, default=0.5)
    param_aggression = Column(Float, default=0.5)
    param_strictness = Column(Float, default=0.7)
    param_adaptivity = Column(Float, default=0.5)
    learning_rate = Column(Float, default=0.01)
    total_updates = Column(Integer, default=0)
    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('aps_team','team'), Index('aps_snapshot','snapshot_at'))

class AdversarialAttackTemplate(Base):
    """攻击模板配置表"""
    __tablename__ = 'adversarial_attack_templates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(16), unique=True, nullable=False)
    attack_type = Column(String(30), nullable=False)
    language = Column(String(10), nullable=False)
    code_template = Column(Text, nullable=False)
    default_payloads = Column(JSON)
    description = Column(String(150))
    difficulty = Column(String(10), default='medium')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('aat_type','attack_type'), Index('aat_lang','language'))

class AdversarialSandboxLog(Base):
    """沙箱执行日志表"""
    __tablename__ = 'adversarial_sandbox_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(22), unique=True, nullable=False)
    script_id = Column(String(20), ForeignKey('adversarial_attack_scripts.script_id'))
    execution_result = Column(JSON, nullable=False)
    blocked = Column(Boolean, default=False)
    output_preview = Column(String(300))
    error_message = Text
    execution_ms = Column(Integer)
    sandbox_id = Column(String(16))
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index('asl_script','script_id'), Index('asl_blocked','blocked'),
        Index('asl_logged','logged_at'))
