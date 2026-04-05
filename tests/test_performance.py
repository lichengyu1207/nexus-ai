"""
性能测试套件
包含响应时间测试、并发测试、负载测试
"""
import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor

from chat_stream.services import (
    EmotionAnalyzer,
    SessionManager,
    PersonaManager,
    StreamOrchestrator,
)
from chat_stream.models import PersonaRole, MessageRole
from task_output.services import TaskStatusManager, ProgressUpdater
from task_output.models import TaskType, TaskStatus


class TestResponseTime:
    """响应时间测试"""

    def test_emotion_analyzer_response_time(self):
        """测试情绪分析响应时间 < 100ms"""
        analyzer = EmotionAnalyzer()
        
        start = time.perf_counter()
        for _ in range(100):
            analyzer.analyze("我很开心，非常满意这次服务")
        end = time.perf_counter()
        
        avg_time = (end - start) / 100 * 1000
        assert avg_time < 100, f"情绪分析平均响应时间 {avg_time:.2f}ms 超过100ms阈值"

    def test_session_manager_response_time(self):
        """测试会话管理响应时间 < 50ms"""
        manager = SessionManager()
        
        start = time.perf_counter()
        for i in range(100):
            manager.create_session(f"user_{i}")
        end = time.perf_counter()
        
        avg_time = (end - start) / 100 * 1000
        assert avg_time < 50, f"创建会话平均响应时间 {avg_time:.2f}ms 超过50ms阈值"

    def test_task_status_manager_response_time(self):
        """测试任务状态管理响应时间 < 50ms"""
        manager = TaskStatusManager()
        
        start = time.perf_counter()
        for i in range(100):
            manager.create_task(f"任务_{i}", TaskType.PROPERTY_ANALYSIS, {})
        end = time.perf_counter()
        
        avg_time = (end - start) / 100 * 1000
        assert avg_time < 50, f"创建任务平均响应时间 {avg_time:.2f}ms 超过50ms阈值"

    def test_persona_manager_response_time(self):
        """测试人格管理响应时间 < 10ms"""
        manager = PersonaManager()
        
        start = time.perf_counter()
        for _ in range(100):
            manager.get_persona_info(PersonaRole.ZHOU_YU)
        end = time.perf_counter()
        
        avg_time = (end - start) / 100 * 1000
        assert avg_time < 10, f"获取角色信息平均响应时间 {avg_time:.2f}ms 超过10ms阈值"


class TestConcurrency:
    """并发测试"""

    def test_concurrent_session_creation(self):
        """测试并发创建会话"""
        manager = SessionManager()
        
        def create_session(user_id):
            return manager.create_session(user_id)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_session, f"user_{i}") for i in range(50)]
            results = [f.result() for f in futures]
        
        assert len(results) == 50
        sessions = manager.get_user_sessions("user_0")
        assert len(sessions) >= 1

    def test_concurrent_task_operations(self):
        """测试并发任务操作"""
        manager = TaskStatusManager()
        
        task_ids = []
        for i in range(20):
            task_id = manager.create_task(f"任务_{i}", TaskType.PROPERTY_ANALYSIS, {})
            task_ids.append(task_id)
        
        def update_progress(task_id):
            for progress in range(0, 101, 10):
                manager.update_progress(task_id, progress)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_progress, tid) for tid in task_ids[:10]]
            for f in futures:
                f.result()
        
        for task_id in task_ids[:10]:
            task = manager.get_task(task_id)
            assert task.progress == 100

    def test_concurrent_emotion_analysis(self):
        """测试并发情绪分析"""
        analyzer = EmotionAnalyzer()
        
        texts = [
            "我很开心",
            "我很伤心",
            "我很焦虑",
            "服务很好",
            "太糟糕了",
        ] * 10
        
        def analyze(text):
            return analyzer.analyze(text)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze, text) for text in texts]
            results = [f.result() for f in futures]
        
        assert len(results) == 50


class TestLoad:
    """负载测试"""

    def test_large_session_messages(self):
        """测试大量消息的会话"""
        manager = SessionManager()
        session = manager.create_session("load_test_user")
        
        start = time.perf_counter()
        for i in range(1000):
            manager.add_message(
                session.session_id,
                MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                f"消息_{i}"
            )
        end = time.perf_counter()
        
        total_time = (end - start) * 1000
        avg_time = total_time / 1000
        
        assert avg_time < 5, f"添加消息平均时间 {avg_time:.2f}ms 超过5ms阈值"
        
        updated_session = manager.get_session(session.session_id)
        assert len(updated_session.messages) == 1000

    def test_large_task_steps(self):
        """测试大量步骤的任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("负载测试任务", TaskType.PROPERTY_ANALYSIS, {})
        
        start = time.perf_counter()
        for i in range(100):
            manager.add_execution_step(task_id, f"智能体_{i % 5}", f"步骤_{i}")
        end = time.perf_counter()
        
        total_time = (end - start) * 1000
        avg_time = total_time / 100
        
        assert avg_time < 2, f"添加步骤平均时间 {avg_time:.2f}ms 超过2ms阈值"
        
        task = manager.get_task(task_id)
        assert len(task.execution_steps) == 100

    def test_large_context_data(self):
        """测试大量上下文数据"""
        manager = SessionManager()
        session = manager.create_session("context_test_user")
        
        start = time.perf_counter()
        for i in range(100):
            manager.set_context(session.session_id, f"key_{i}", f"value_{i}" * 10)
        end = time.perf_counter()
        
        total_time = (end - start) * 1000
        avg_time = total_time / 100
        
        assert avg_time < 2, f"设置上下文平均时间 {avg_time:.2f}ms 超过2ms阈值"
        
        for i in range(100):
            value = manager.get_context(session.session_id, f"key_{i}")
            assert value is not None


class TestMemoryUsage:
    """内存使用测试"""

    def test_session_memory_cleanup(self):
        """测试会话内存清理"""
        manager = SessionManager()
        
        initial_count = len(manager._sessions)
        
        for i in range(100):
            manager.create_session(f"temp_user_{i}")
        
        assert len(manager._sessions) == initial_count + 100
        
        for session in list(manager._sessions.values()):
            manager.close_session(session.session_id)
        
        for session in list(manager._sessions.values()):
            assert not session.is_active

    def test_task_memory_management(self):
        """测试任务内存管理"""
        manager = TaskStatusManager()
        
        for i in range(100):
            manager.create_task(f"任务_{i}", TaskType.PROPERTY_ANALYSIS, {})
        
        assert len(manager._tasks) == 100
        
        for task_id in list(manager._tasks.keys()):
            task = manager.get_task(task_id)
            assert task is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
