"""
集成测试套件
包含API端点测试、边界条件测试、异常处理测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chat_stream.models import (
    EmotionType,
    PersonaRole,
    MessageRole,
    AgentState,
)
from chat_stream.services import (
    EmotionAnalyzer,
    SessionManager,
    PersonaManager,
)
from task_output.services import (
    TaskStatusManager,
    ProgressUpdater,
)
from task_output.models import TaskStatus, TaskType, StepStatus


class TestEmotionAnalyzerEdge:
    """情绪分析器边界测试"""

    def test_empty_string(self):
        """测试空字符串"""
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze("")
        assert result.emotion == EmotionType.NEUTRAL

    def test_very_long_string(self):
        """测试超长字符串"""
        analyzer = EmotionAnalyzer()
        long_text = "开心" * 1000
        result = analyzer.analyze(long_text)
        assert result.emotion == EmotionType.POSITIVE

    def test_special_characters(self):
        """测试特殊字符"""
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze("!@#$%^&*()")
        assert result.emotion == EmotionType.NEUTRAL

    def test_mixed_emotions(self):
        """测试混合情绪"""
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze("我很开心，但是也有点焦虑")
        assert result.emotion in [EmotionType.POSITIVE, EmotionType.ANXIOUS]

    def test_numbers_only(self):
        """测试纯数字"""
        analyzer = EmotionAnalyzer()
        result = analyzer.analyze("123456789")
        assert result.emotion == EmotionType.NEUTRAL


class TestSessionManagerEdge:
    """会话管理器边界测试"""

    def test_empty_user_id(self):
        """测试空用户ID"""
        manager = SessionManager()
        session = manager.create_session("")
        assert session.user_id == ""

    def test_very_long_user_id(self):
        """测试超长用户ID"""
        manager = SessionManager()
        long_id = "user_" * 100
        session = manager.create_session(long_id)
        assert session.user_id == long_id

    def test_multiple_sessions_same_user(self):
        """测试同一用户多个会话"""
        manager = SessionManager()
        session1 = manager.create_session("user001")
        session2 = manager.create_session("user001")
        sessions = manager.get_user_sessions("user001")
        assert len(sessions) == 2

    def test_add_message_to_nonexistent_session(self):
        """测试向不存在的会话添加消息"""
        manager = SessionManager()
        with pytest.raises(ValueError):
            manager.add_message("nonexistent", MessageRole.USER, "test")

    def test_update_nonexistent_message(self):
        """测试更新不存在的消息"""
        manager = SessionManager()
        session = manager.create_session("user001")
        result = manager.update_message(session.session_id, "nonexistent", content="test")
        assert result is None

    def test_context_with_none_value(self):
        """测试上下文None值"""
        manager = SessionManager()
        session = manager.create_session("user001")
        manager.set_context(session.session_id, "key", None)
        value = manager.get_context(session.session_id, "key")
        assert value is None


class TestPersonaManagerEdge:
    """人格化角色管理器边界测试"""

    def test_get_info_all_personas(self):
        """测试获取所有角色信息"""
        manager = PersonaManager()
        for role in PersonaRole:
            info = manager.get_persona_info(role)
            assert "name" in info
            assert "style" in info

    def test_user_preference_persistence(self):
        """测试用户偏好持久化"""
        manager = PersonaManager()
        manager.set_user_preference("user001", PersonaRole.LU_XUN)
        assert manager.get_user_preference("user001") == PersonaRole.LU_XUN

    def test_format_response_all_emotions(self):
        """测试所有情绪的响应格式化"""
        manager = PersonaManager()
        for emotion in EmotionType:
            result = manager.format_response(PersonaRole.ZHOU_YU, "测试内容", emotion)
            assert isinstance(result, str)


class TestTaskStatusManagerEdge:
    """任务状态管理器边界测试"""

    def test_create_task_empty_title(self):
        """测试创建空标题任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("", TaskType.PROPERTY_ANALYSIS, {})
        task = manager.get_task(task_id)
        assert task.title == ""

    def test_create_task_with_empty_parameters(self):
        """测试创建空参数任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        task = manager.get_task(task_id)
        assert task.input_summary == {}

    def test_start_already_completed_task(self):
        """测试启动已完成的任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        manager.start_task(task_id)
        manager.complete_task(task_id, "完成", {})
        result = manager.start_task(task_id)
        assert result is False

    def test_complete_not_started_task(self):
        """测试完成未启动的任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        result = manager.complete_task(task_id, "完成", {})
        assert result is True

    def test_fail_not_started_task(self):
        """测试失败未启动的任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        result = manager.fail_task(task_id, "错误")
        assert result is True

    def test_pause_not_running_task(self):
        """测试暂停非运行中任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        result = manager.pause_task(task_id)
        assert result is False

    def test_cancel_already_cancelled_task(self):
        """测试取消已取消的任务"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        manager.cancel_task(task_id)
        result = manager.cancel_task(task_id)
        assert result is True

    def test_progress_boundary_values(self):
        """测试进度边界值"""
        manager = TaskStatusManager()
        task_id = manager.create_task("测试", TaskType.PROPERTY_ANALYSIS, {})
        
        manager.update_progress(task_id, -100)
        task = manager.get_task(task_id)
        assert task.progress == 0
        
        manager.update_progress(task_id, 200)
        task = manager.get_task(task_id)
        assert task.progress == 100

    def test_add_step_to_nonexistent_task(self):
        """测试向不存在的任务添加步骤"""
        manager = TaskStatusManager()
        with pytest.raises(ValueError):
            manager.add_execution_step("nonexistent", "agent", "desc")

    def test_generate_report_no_tasks(self):
        """测试无任务时生成报告"""
        manager = TaskStatusManager()
        report = manager.generate_aggregate_report()
        assert report is None


class TestProgressUpdaterEdge:
    """进度更新器边界测试"""

    @pytest.mark.asyncio
    async def test_empty_callbacks_list(self):
        """测试空回调列表"""
        manager = TaskStatusManager()
        updater = ProgressUpdater(manager)
        
        await updater.notify_progress_update("task1", "test", {})
        
    @pytest.mark.asyncio
    async def test_broadcast_nonexistent_task(self):
        """测试广播不存在的任务"""
        manager = TaskStatusManager()
        updater = ProgressUpdater(manager)
        from task_output.models import TaskStatus
        messages = []
        
        async def callback(tid, utype, data):
            messages.append((tid, utype, data))
        
        updater.add_callback(callback)
        await updater.broadcast_task_status("nonexistent", TaskStatus.RUNNING)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_broadcast_step_nonexistent_task(self):
        """测试广播不存在任务的步骤"""
        manager = TaskStatusManager()
        updater = ProgressUpdater(manager)
        messages = []
        
        async def callback(tid, utype, data):
            messages.append((tid, utype, data))
        
        updater.add_callback(callback)
        await updater.broadcast_step_status("nonexistent", "step1", StepStatus.COMPLETED)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_callback_with_exception(self):
        """测试回调抛出异常"""
        manager = TaskStatusManager()
        updater = ProgressUpdater(manager)
        
        async def failing_callback(tid, utype, data):
            raise RuntimeError("回调异常")
        
        async def success_callback(tid, utype, data):
            pass
        
        updater.add_callback(failing_callback)
        updater.add_callback(success_callback)
        
        await updater.notify_progress_update("task1", "test", {})
        
        assert success_callback in updater._callbacks


class TestIntegrationScenarios:
    """集成场景测试"""

    def test_full_task_lifecycle(self):
        """测试完整任务生命周期"""
        manager = TaskStatusManager()
        
        task_id = manager.create_task(
            "深圳学区房分析",
            TaskType.PROPERTY_ANALYSIS,
            {"city": "深圳", "area": "南山区"},
        )
        
        manager.start_task(task_id)
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.RUNNING
        
        manager.add_execution_step(task_id, "中书省", "解析需求")
        manager.add_log(task_id, "户部", "采集数据中")
        manager.add_intermediate_result(task_id, "中间结果", "数据已获取")
        
        manager.update_progress(task_id, 50)
        task = manager.get_task(task_id)
        assert task.progress == 50
        
        manager.complete_task(task_id, "分析完成", {"price": "9.8万/㎡"})
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
        
        report = manager.generate_aggregate_report()
        assert report is not None

    def test_full_session_lifecycle(self):
        """测试完整会话生命周期"""
        manager = SessionManager()
        
        session = manager.create_session("user001", PersonaRole.ZHOU_YU)
        assert session.is_active
        
        manager.add_message(session.session_id, MessageRole.USER, "你好")
        manager.add_message(session.session_id, MessageRole.ASSISTANT, "您好！")
        
        manager.set_context(session.session_id, "city", "深圳")
        assert manager.get_context(session.session_id, "city") == "深圳"
        
        manager.update_agent_state(
            session.session_id, "户部", 
            AgentState.WORKING,
            "采集中"
        )
        
        assert "户部" in manager.get_session(session.session_id).agent_states
        
        manager.close_session(session.session_id)
        assert not manager.get_session(session.session_id).is_active

    def test_emotion_based_response(self):
        """测试基于情绪的响应"""
        emotion_analyzer = EmotionAnalyzer()
        persona_manager = PersonaManager()
        
        anxious_result = emotion_analyzer.analyze("我很焦虑，不知道怎么办")
        response = persona_manager.format_response(
            PersonaRole.ZHOU_YU,
            "让我来帮您分析",
            anxious_result.emotion
        )
        assert "理解" in response or "担忧" in response or response == "让我来帮您分析"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
