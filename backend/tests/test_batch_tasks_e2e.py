"""
批量任务端到端测试
测试完整的批量任务创建、执行、监控流程
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.task_dag import (
    build_task_dag,
    infer_dependencies,
    TaskDAG,
    TaskNode,
    TaskPriority,
    BatchTaskScheduler,
)
from backend.services.intent_parser import parse_intent, TaskType
from backend.services.param_extractor import extract_params, generate_questions


class TestTaskDAG:
    """任务DAG测试"""

    def test_build_simple_dag(self):
        """测试构建简单DAG"""
        tasks = [
            {"id": "task1", "type": "property_analysis", "params": {"city": "深圳"}},
            {"id": "task2", "type": "report_generation", "params": {}, "dependencies": ["task1"]},
        ]
        
        dag = build_task_dag(tasks)
        
        assert len(dag.nodes) == 2
        assert "task1" in dag.nodes
        assert "task2" in dag.nodes
        assert "task1" in dag.nodes["task2"].dependencies

    def test_detect_cycle(self):
        """测试循环依赖检测"""
        tasks = [
            {"id": "task1", "type": "a", "dependencies": ["task3"]},
            {"id": "task2", "type": "b", "dependencies": ["task1"]},
            {"id": "task3", "type": "c", "dependencies": ["task2"]},
        ]
        
        dag = build_task_dag(tasks)
        has_cycle, cycle_nodes = dag.detect_cycle()
        
        assert has_cycle is True
        assert len(cycle_nodes) > 0

    def test_topological_sort(self):
        """测试拓扑排序"""
        tasks = [
            {"id": "task1", "type": "a"},
            {"id": "task2", "type": "b", "dependencies": ["task1"]},
            {"id": "task3", "type": "c", "dependencies": ["task1"]},
            {"id": "task4", "type": "d", "dependencies": ["task2", "task3"]},
        ]
        
        dag = build_task_dag(tasks)
        order = dag.topological_sort()
        
        assert order.index("task1") < order.index("task2")
        assert order.index("task1") < order.index("task3")
        assert order.index("task2") < order.index("task4")
        assert order.index("task3") < order.index("task4")

    def test_get_execution_levels(self):
        """测试获取执行层级"""
        tasks = [
            {"id": "task1", "type": "a"},
            {"id": "task2", "type": "b"},
            {"id": "task3", "type": "c", "dependencies": ["task1", "task2"]},
        ]
        
        dag = build_task_dag(tasks)
        levels = dag.get_execution_levels()
        
        assert len(levels) == 2
        assert len(levels[0]) == 2
        assert "task1" in levels[0]
        assert "task2" in levels[0]
        assert levels[1] == ["task3"]

    def test_infer_dependencies(self):
        """测试自动推断依赖"""
        tasks = [
            {"id": "data1", "type": "data_collection", "params": {}},
            {"id": "analysis1", "type": "property_analysis", "params": {}},
            {"id": "report1", "type": "report_generation", "params": {}},
        ]
        
        enhanced = infer_dependencies(tasks)
        
        analysis_task = next(t for t in enhanced if t["id"] == "analysis1")
        report_task = next(t for t in enhanced if t["id"] == "report1")
        
        assert "data1" in analysis_task["dependencies"]
        assert "analysis1" in report_task["dependencies"]


class TestBatchTaskScheduler:
    """批量任务调度器测试"""

    @pytest.mark.asyncio
    async def test_schedule_simple_tasks(self):
        """测试调度简单任务"""
        scheduler = BatchTaskScheduler(max_concurrent=3)
        
        tasks = [
            {"id": "task1", "type": "property_analysis", "params": {"city": "深圳"}},
            {"id": "task2", "type": "property_analysis", "params": {"city": "北京"}},
        ]
        
        async def mock_executor(task_node):
            await asyncio.sleep(0.1)
            return {"status": "success", "task_id": task_node.id}
        
        result = await scheduler.schedule(tasks, mock_executor)
        
        assert result["status"] == "completed"
        assert "task1" in result["task_status"]
        assert "task2" in result["task_status"]

    @pytest.mark.asyncio
    async def test_schedule_with_dependencies(self):
        """测试调度有依赖的任务"""
        scheduler = BatchTaskScheduler(max_concurrent=2)
        
        tasks = [
            {"id": "task1", "type": "data_collection", "params": {}},
            {"id": "task2", "type": "property_analysis", "params": {}, "dependencies": ["task1"]},
        ]
        
        execution_order = []
        
        async def mock_executor(task_node):
            execution_order.append(task_node.id)
            await asyncio.sleep(0.1)
            return {"status": "success"}
        
        result = await scheduler.schedule(tasks, mock_executor)
        
        assert execution_order.index("task1") < execution_order.index("task2")

    def test_get_progress(self):
        """测试获取进度"""
        scheduler = BatchTaskScheduler()
        scheduler.task_status = {
            "task1": "completed",
            "task2": "completed",
            "task3": "running",
            "task4": "pending",
        }
        
        progress = scheduler.get_progress()
        
        assert progress["total"] == 4
        assert progress["completed"] == 2
        assert progress["running"] == 1
        assert progress["pending"] == 1
        assert progress["percent"] == 50.0


class TestIntentParser:
    """意图解析测试"""

    def test_parse_single_task(self):
        """测试解析单个任务"""
        result = parse_intent("分析深圳南山区的房价")
        
        assert len(result.tasks) >= 1
        assert result.tasks[0].type == TaskType.PROPERTY_ANALYSIS

    def test_parse_multiple_tasks(self):
        """测试解析多个任务"""
        result = parse_intent("分析深圳房价，查一下杭州政策")
        
        assert len(result.tasks) >= 2
        task_types = [t.type for t in result.tasks]
        assert TaskType.PROPERTY_ANALYSIS in task_types
        assert TaskType.POLICY_QUERY in task_types

    def test_parse_with_confidence(self):
        """测试解析置信度"""
        result = parse_intent("帮我算一下命盘")
        
        assert len(result.tasks) >= 1
        assert result.tasks[0].confidence > 0


class TestParamExtractor:
    """参数提取测试"""

    def test_extract_city(self):
        """测试提取城市"""
        result = extract_params(TaskType.PROPERTY_ANALYSIS, "深圳南山区的房价")
        
        assert "city" in result

    def test_extract_missing_params(self):
        """测试提取缺失参数"""
        result = extract_params(TaskType.PROPERTY_ANALYSIS, "分析房价")
        
        missing = [k for k, v in result.items() if hasattr(v, 'status') and v.status.value == 'missing']
        assert len(missing) > 0

    def test_generate_questions(self):
        """测试生成追问"""
        question = generate_questions(["city", "price_range"], TaskType.PROPERTY_ANALYSIS)
        
        assert isinstance(question, str)
        assert len(question) > 0


class TestIntegration:
    """集成测试"""

    def test_full_parsing_flow(self):
        """测试完整解析流程"""
        text = "分析深圳南山区的房价，顺便查一下杭州的政策"
        
        parse_result = parse_intent(text)
        assert len(parse_result.tasks) >= 2
        
        tasks = []
        for parsed_task in parse_result.tasks:
            params = extract_params(parsed_task.type, text)
            
            task = {
                "id": f"task_{len(tasks)}",
                "type": parsed_task.type.value,
                "params": {k: v for k, v in params.items()},
            }
            tasks.append(task)
        
        enhanced_tasks = infer_dependencies(tasks)
        dag = build_task_dag(enhanced_tasks)
        
        assert len(dag.nodes) >= 2
        assert not dag.detect_cycle()[0]

    @pytest.mark.asyncio
    async def test_batch_workflow(self):
        """测试批量任务工作流"""
        tasks = [
            {"id": "t1", "type": "property_analysis", "params": {"city": "深圳"}},
            {"id": "t2", "type": "property_analysis", "params": {"city": "北京"}},
            {"id": "t3", "type": "report_generation", "params": {}},
        ]
        
        enhanced = infer_dependencies(tasks)
        dag = build_task_dag(enhanced)
        
        assert not dag.detect_cycle()[0]
        
        scheduler = BatchTaskScheduler(max_concurrent=2)
        
        async def mock_executor(task):
            await asyncio.sleep(0.05)
            return {"success": True}
        
        result = await scheduler.schedule(enhanced, mock_executor)
        
        assert result["status"] == "completed"
        assert all(s == "completed" for s in result["task_status"].values())


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_tasks(self):
        """测试空任务列表"""
        dag = build_task_dag([])
        assert len(dag.nodes) == 0

    def test_single_task(self):
        """测试单个任务"""
        dag = build_task_dag([{"id": "only", "type": "test"}])
        levels = dag.get_execution_levels()
        
        assert len(levels) == 1
        assert levels[0] == ["only"]

    def test_all_parallel_tasks(self):
        """测试全部并行任务"""
        tasks = [
            {"id": f"task{i}", "type": "test"} for i in range(5)
        ]
        
        dag = build_task_dag(tasks)
        levels = dag.get_execution_levels()
        
        assert len(levels) == 1
        assert len(levels[0]) == 5

    def test_linear_chain(self):
        """测试线性链"""
        tasks = [
            {"id": "t1", "type": "a"},
            {"id": "t2", "type": "b", "dependencies": ["t1"]},
            {"id": "t3", "type": "c", "dependencies": ["t2"]},
            {"id": "t4", "type": "d", "dependencies": ["t3"]},
        ]
        
        dag = build_task_dag(tasks)
        levels = dag.get_execution_levels()
        
        assert len(levels) == 4
        for level in levels:
            assert len(level) == 1

    @pytest.mark.asyncio
    async def test_task_failure_handling(self):
        """测试任务失败处理"""
        scheduler = BatchTaskScheduler()
        
        tasks = [
            {"id": "fail", "type": "test"},
            {"id": "success", "type": "test"},
        ]
        
        async def failing_executor(task):
            if task.id == "fail":
                raise Exception("Task failed")
            return {"success": True}
        
        try:
            await scheduler.schedule(tasks, failing_executor)
        except Exception:
            pass
        
        assert scheduler.task_status.get("fail") == "failed"
