"""
意图识别模块单元测试
测试自然语言任务解析功能
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.intent_parser import (
    parse_intent,
    TaskType,
    ParseResult,
    ParsedTask,
)


class TestIntentParser:
    """意图识别测试类"""

    def test_single_property_analysis(self):
        """测试单个房产分析任务识别"""
        text = "帮我分析深圳南山区的房价走势"
        result = parse_intent(text)
        
        assert isinstance(result, ParseResult)
        assert len(result.tasks) >= 1
        
        task = result.tasks[0]
        assert task.type == TaskType.PROPERTY_ANALYSIS
        assert task.confidence >= 0.5

    def test_single_policy_query(self):
        """测试单个政策查询任务识别"""
        text = "查一下杭州最近的购房政策"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.type == TaskType.POLICY_QUERY
        assert task.confidence >= 0.5

    def test_single_mingpan_query(self):
        """测试单个命理咨询任务识别"""
        text = "帮我算一下我的命盘事业运"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.type == TaskType.MINGPAN
        assert task.confidence >= 0.5

    def test_single_emotion_query(self):
        """测试单个情感陪伴任务识别"""
        text = "我今天心情不好，想找人聊聊"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.type == TaskType.EMOTION

    def test_multiple_tasks_with_connectors(self):
        """测试使用连接词的多任务识别"""
        text = "帮我分析深圳南山区的房价走势，顺便查一下杭州最近的政策"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 2
        
        task_types = [t.type for t in result.tasks]
        assert TaskType.PROPERTY_ANALYSIS in task_types
        assert TaskType.POLICY_QUERY in task_types

    def test_multiple_tasks_with_semicolon(self):
        """测试使用分号分隔的多任务识别"""
        text = "分析北京房价；查上海政策；算一下我的命盘"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 2

    def test_multiple_tasks_with_newline(self):
        """测试使用换行分隔的多任务识别"""
        text = """
        分析深圳房价走势
        查一下杭州政策
        算我的命盘
        """
        result = parse_intent(text)
        
        assert len(result.tasks) >= 2

    def test_unknown_intent(self):
        """测试未知意图识别"""
        text = "今天天气怎么样"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 1
        assert result.tasks[0].type in [TaskType.UNKNOWN, TaskType.TOOL_CALL]

    def test_empty_input(self):
        """测试空输入"""
        text = ""
        result = parse_intent(text)
        
        assert isinstance(result, ParseResult)
        assert len(result.tasks) == 0

    def test_whitespace_only_input(self):
        """测试纯空白输入"""
        text = "   \n\t  "
        result = parse_intent(text)
        
        assert len(result.tasks) == 0

    def test_complex_multi_task(self):
        """测试复杂多任务场景"""
        text = "帮我分析深圳南山区的房价走势，顺便查一下杭州最近的政策，再给我算一下我的命盘事业运"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 2
        
        task_types = [t.type for t in result.tasks]
        assert TaskType.PROPERTY_ANALYSIS in task_types

    def test_report_generation_intent(self):
        """测试报告生成意图识别"""
        text = "帮我生成一份房产分析报告"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.type in [TaskType.REPORT_GENERATION, TaskType.PROPERTY_ANALYSIS]

    def test_tool_call_intent(self):
        """测试工具调用意图识别"""
        text = "调用地图API查询位置"
        result = parse_intent(text)
        
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.type in [TaskType.TOOL_CALL, TaskType.UNKNOWN]

    def test_confidence_threshold(self):
        """测试置信度阈值"""
        text = "分析房价"
        result = parse_intent(text)
        
        for task in result.tasks:
            assert 0 <= task.confidence <= 1

    def test_span_extraction(self):
        """测试文本片段提取"""
        text = "帮我分析深圳南山区的房价走势"
        result = parse_intent(text)
        
        for task in result.tasks:
            assert isinstance(task.span, str)
            assert len(task.span) > 0

    def test_real_estate_keywords(self):
        """测试房产相关关键词识别"""
        keywords = [
            "房价", "房产", "房子", "住宅", "公寓", 
            "别墅", "商铺", "写字楼", "学区房"
        ]
        
        for keyword in keywords:
            text = f"帮我分析{keyword}的情况"
            result = parse_intent(text)
            
            assert len(result.tasks) >= 1
            assert result.tasks[0].type == TaskType.PROPERTY_ANALYSIS, f"Failed for keyword: {keyword}"

    def test_policy_keywords(self):
        """测试政策相关关键词识别"""
        keywords = ["政策", "限购", "贷款", "首付", "税费"]
        
        for keyword in keywords:
            text = f"查一下{keyword}相关内容"
            result = parse_intent(text)
            
            assert len(result.tasks) >= 1
            assert result.tasks[0].type == TaskType.POLICY_QUERY, f"Failed for keyword: {keyword}"

    def test_mingpan_keywords(self):
        """测试命理相关关键词识别"""
        keywords = ["命盘", "八字", "运势", "风水", "算命", "星座"]
        
        for keyword in keywords:
            text = f"帮我算一下{keyword}"
            result = parse_intent(text)
            
            assert len(result.tasks) >= 1
            assert result.tasks[0].type == TaskType.MINGPAN, f"Failed for keyword: {keyword}"


class TestParseResultStructure:
    """测试解析结果数据结构"""

    def test_parse_result_structure(self):
        """测试ParseResult结构"""
        text = "分析深圳房价"
        result = parse_intent(text)
        
        assert hasattr(result, 'tasks')
        assert hasattr(result, 'relations')
        assert isinstance(result.tasks, list)
        assert isinstance(result.relations, list)

    def test_parsed_task_structure(self):
        """测试ParsedTask结构"""
        text = "分析深圳房价"
        result = parse_intent(text)
        
        if len(result.tasks) > 0:
            task = result.tasks[0]
            assert hasattr(task, 'type')
            assert hasattr(task, 'confidence')
            assert hasattr(task, 'span')
            assert isinstance(task.type, TaskType)
            assert isinstance(task.confidence, float)
            assert isinstance(task.span, str)


class TestEdgeCases:
    """边界情况测试"""

    def test_very_long_input(self):
        """测试超长输入"""
        text = "帮我分析房价 " * 100
        result = parse_intent(text)
        
        assert isinstance(result, ParseResult)

    def test_special_characters(self):
        """测试特殊字符"""
        text = "分析深圳房价！！！@#$%"
        result = parse_intent(text)
        
        assert isinstance(result, ParseResult)

    def test_mixed_language(self):
        """测试中英混合"""
        text = "分析Shenzhen的房价"
        result = parse_intent(text)
        
        assert isinstance(result, ParseResult)

    def test_numbers_in_input(self):
        """测试包含数字的输入"""
        text = "分析100平米房子的价格"
        result = parse_intent(text)
        
        assert isinstance(result, ParseResult)
        assert len(result.tasks) >= 1
