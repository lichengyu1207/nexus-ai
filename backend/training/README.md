# 房都督平台业务层智能体训练系统

## 一、系统概述

本训练系统基于《业务层智能体训练方案》实现，旨在全面提升房都督平台"三省六部"业务层智能体的专业能力、决策准确率、协同效率和用户满意度。

## 二、系统架构

```
backend/training/
├── __init__.py              # 模块入口
├── data_collector.py        # 数据收集和处理
├── reward_functions.py      # 奖励函数系统
├── zhongshu_trainer.py      # 中书省（决策）训练器
├── gongbu_trainer.py        # 工部（估值）训练器
├── libu_trainer.py          # 礼部（咨询）训练器
├── multi_agent_trainer.py   # 多智能体联合训练
└── evaluation.py            # 评估和监控系统
```

## 三、核心模块

### 3.1 数据收集系统 (data_collector.py)

**功能**：
- 收集对话记录
- 收集任务执行记录
- 收集估值对比数据
- 收集合规检查数据
- 支持专家示范数据

**使用示例**：
```python
from backend.training import TrainingDataCollector

collector = TrainingDataCollector()

# 记录对话
collector.record_dialogue(
    session_id="session_001",
    user_input="帮我分析深圳南山区学区房",
    agent_reply="关于您的问题...",
    agent_type="li_bu_consult",
    response_time=1.5
)

# 添加用户反馈
collector.add_user_feedback(
    session_id="session_001",
    rating=5,
    comment="非常有帮助"
)

# 获取训练数据集
dataset = collector.get_training_dataset(data_type="dialogue")
```

### 3.2 奖励函数系统 (reward_functions.py)

**功能**：
- 为各智能体定义奖励信号
- 支持自定义奖励配置
- 计算协同奖励

**奖励设计**：

| 智能体 | 正向奖励 | 负向惩罚 |
|--------|----------|----------|
| 中书省 | 任务拆解正确 +1.0 | 不必要子任务 -0.5 |
| 门下省 | 正确拦截违规 +1.0 | 漏过违规 -2.0 |
| 工部 | 误差<3% +1.0 | 误差>5% -1.0 |
| 礼部 | 用户评分≥4.5 +1.0 | 评分<3 -2.0 |

**使用示例**：
```python
from backend.training import RewardCalculator

calculator = RewardCalculator()

# 计算单个智能体奖励
reward = calculator.calculate_reward(
    agent_type="zhongshu",
    execution_result={
        "decomposition_correct": True,
        "response_time": 1.5,
        "unnecessary_subtasks": 0
    }
)

# 计算协同奖励
collab_reward = calculator.calculate_collaborative_reward(
    agent_results={"zhongshu": {...}, "gong_bu": {...}},
    task_completion_time=8.5,
    communication_delay=0.02,
    api_cost=0.5,
    cost_budget=1.0
)
```

### 3.3 中书省训练器 (zhongshu_trainer.py)

**训练目标**：
- 任务拆解准确率：92% → 96%
- 响应时间：<2秒

**核心功能**：
- 任务模式识别
- 智能体能力匹配
- 任务拆解优化

**使用示例**：
```python
from backend.training import ZhongshuTrainer

trainer = ZhongshuTrainer()

# 加载训练数据
trainer.load_training_data(task_records)

# 训练模型
result = trainer.train()

# 预测任务拆解
prediction = trainer.predict("帮我分析深圳南山区学区房，预算1000万")
# 输出: {"subtasks": [...], "task_type": "valuation_analysis", ...}
```

### 3.4 工部训练器 (gongbu_trainer.py)

**训练目标**：
- 估价误差：<5% → <3%
- 增强特征工程

**核心功能**：
- 特征提取（位置、面积、楼层、朝向等）
- 估值模型训练
- 增量学习支持

**使用示例**：
```python
from backend.training import GongbuTrainer

trainer = GongbuTrainer()

# 加载训练数据
trainer.load_training_data(valuation_records)

# 训练模型
result = trainer.train()

# 预测估值
prediction = trainer.predict({
    "location": "深圳南山",
    "area": 100,
    "floor": 15,
    "orientation": "南",
    "age": 5
})
# 输出: {"estimated_price": 850.0, "confidence": 0.92, ...}
```

### 3.5 礼部训练器 (libu_trainer.py)

**训练目标**：
- 用户满意度：4.5 → 4.7
- 优化回复质量

**核心功能**：
- 查询分类
- 个性化回复生成
- RLHF支持

**使用示例**：
```python
from backend.training import LibuTrainer

trainer = LibuTrainer()

# 加载训练数据
trainer.load_training_data(dialogue_records)

# 训练模型
result = trainer.train()

# 生成回复
response = trainer.generate_response(
    user_query="深圳学区房政策如何？",
    context={"location": "深圳"},
    user_preferences={"style": "formal"}
)
# 输出: {"response": "...", "query_type": "policy", ...}
```

### 3.6 多智能体联合训练 (multi_agent_trainer.py)

**训练目标**：
- 协同延迟：<50ms → <30ms
- API成本降低15%

**核心功能**：
- 协同模式定义
- 任务分配优化
- 联合奖励计算

**使用示例**：
```python
from backend.training import MultiAgentTrainer

trainer = MultiAgentTrainer()

# 加载训练数据
trainer.load_training_data(collaborative_tasks)

# 训练模型
result = trainer.train()

# 分配任务
allocation = trainer.allocate_task(
    task_description="分析深圳南山区学区房投资价值",
    task_type="investment_consultation"
)
# 输出: {"agents": ["zhongshu", "gong_bu", "li_bu_consult"], ...}

# 执行协同任务
result = await trainer.execute_collaborative_task(
    task_description="...",
    task_type="valuation_analysis"
)
```

### 3.7 评估和监控系统 (evaluation.py)

**核心功能**：
- 离线评估
- 在线评估
- 性能监控
- 告警系统

**使用示例**：
```python
from backend.training import TrainingEvaluator

evaluator = TrainingEvaluator()

# 评估智能体
metrics = evaluator.evaluate_agent(
    agent_type="zhongshu",
    predictions=predictions,
    ground_truth=ground_truth
)

# 监控性能
monitoring = evaluator.monitor_performance(
    agent_type="zhongshu",
    metrics={"latency": 1.5, "accuracy": 0.95}
)

# 与基线对比
comparison = evaluator.compare_with_baseline(
    agent_type="zhongshu",
    current_metrics={"accuracy": 0.94}
)

# 生成报告
report = evaluator.generate_report(period="daily")
```

## 四、训练流程

### 4.1 数据准备阶段（第1-2周）

```python
# 1. 初始化数据收集器
from backend.training import TrainingDataCollector
collector = TrainingDataCollector()

# 2. 收集历史数据
# - 从数据库导出对话记录
# - 从日志提取任务执行记录
# - 收集估值对比数据

# 3. 添加专家示范
collector.add_expert_demonstration(
    scenario="学区房分析",
    user_input="帮我分析深圳南山区学区房，预算1000万",
    ideal_task_decomposition=[
        "调用兵部采集南山区学区数据",
        "调用工部估算房价趋势",
        "调用礼部生成分析报告"
    ],
    ideal_reply="根据您的要求，我们首先分析了...",
    expected_valuation=950,
    confidence=0.95
)

# 4. 数据划分
dataset = collector.get_training_dataset(data_type="all")
```

### 4.2 单智能体训练阶段（第4-6周）

```python
# 1. 中书省训练
from backend.training import ZhongshuTrainer
zhongshu_trainer = ZhongshuTrainer()
zhongshu_trainer.load_training_data(dataset["train"]["tasks"])
zhongshu_result = zhongshu_trainer.train()

# 2. 工部训练
from backend.training import GongbuTrainer
gongbu_trainer = GongbuTrainer()
gongbu_trainer.load_training_data(dataset["train"]["valuations"])
gongbu_result = gongbu_trainer.train()

# 3. 礼部训练
from backend.training import LibuTrainer
libu_trainer = LibuTrainer()
libu_trainer.load_training_data(dataset["train"]["dialogues"])
libu_result = libu_trainer.train()
```

### 4.3 联合训练阶段（第7-8周）

```python
# 多智能体联合训练
from backend.training import MultiAgentTrainer
multi_trainer = MultiAgentTrainer()
multi_trainer.load_training_data(collaborative_tasks)
multi_result = multi_trainer.train()
```

### 4.4 评估阶段（第9周）

```python
# 离线评估
from backend.training import TrainingEvaluator
evaluator = TrainingEvaluator()

# 评估各智能体
zhongshu_metrics = evaluator.evaluate_agent(
    "zhongshu", predictions, ground_truth
)

# 评估协同效果
collab_result = evaluator.evaluate_collaboration(
    task_results, execution_times, communication_delays
)

# 生成报告
report = evaluator.generate_report(period="weekly")
```

## 五、目标指标

| 智能体 | 关键指标 | 当前值 | 目标值 |
|--------|----------|--------|--------|
| 中书省 | 任务拆解准确率 | 92% | ≥96% |
| 门下省 | 合规检查准确率 | 95% | ≥98% |
| 礼部 | 用户情感评分 | 4.5/5 | ≥4.7/5 |
| 工部 | 估价误差 | <5% | <3% |
| 兵部 | 数据采集覆盖率 | 70% | ≥85% |
| 整体 | 智能体协同延迟 | <50ms | <30ms |
| 整体 | API调用成本 | 基准 | 降低15% |

## 六、持续迭代

### 6.1 在线学习

```python
# 收集用户反馈
collector.add_user_feedback(
    session_id="session_xxx",
    rating=4,
    comment="回复很专业"
)

# 增量更新
gongbu_trainer.incremental_update(new_valuation_data)
```

### 6.2 A/B测试

```python
# 部署新模型
# 通过配置控制流量分配
# 对比新旧模型指标
```

### 6.3 定期评估

```python
# 每日报告
daily_report = evaluator.generate_report("daily")

# 每周报告
weekly_report = evaluator.generate_report("weekly")
```

## 七、文件结构

```
backend/
├── training/
│   ├── __init__.py
│   ├── data_collector.py
│   ├── reward_functions.py
│   ├── zhongshu_trainer.py
│   ├── gongbu_trainer.py
│   ├── libu_trainer.py
│   ├── multi_agent_trainer.py
│   └── evaluation.py
├── training_data/
│   ├── dialogues.json
│   ├── tasks.json
│   ├── valuations.json
│   └── expert_demonstrations.json
├── models/
│   ├── zhongshu/
│   ├── gongbu/
│   ├── libu/
│   └── multi_agent/
└── logs/
    └── training/
```

## 八、总结

本训练系统提供了从数据收集到模型部署的全流程支持，包括：

1. **数据层**：完整的数据收集、处理和存储系统
2. **训练层**：针对各智能体的专用训练器
3. **协同层**：多智能体联合训练和优化
4. **评估层**：全面的评估、监控和告警系统

通过系统化的训练方法，平台将逐步实现智能体集群的自进化，持续提升业务能力和用户体验。
