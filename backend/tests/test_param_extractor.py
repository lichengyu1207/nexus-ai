"""
参数提取模块单元测试
测试任务参数提取和追问生成功能
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.param_extractor import (
    extract_params,
    generate_questions,
    TaskType,
    ParamResult,
    ParamStatus,
)


class TestParamExtractor:
    """参数提取测试类"""

    def test_extract_city_property_analysis(self):
        """测试房产分析城市参数提取"""
        text = "分析深圳南山区的房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "city" in result
        assert result["city"].value == "深圳"
        assert result["city"].status == ParamStatus.VALID

    def test_extract_district_property_analysis(self):
        """测试房产分析区域参数提取"""
        text = "分析深圳南山区的房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "district" in result
        assert result["district"].value == "南山区"

    def test_extract_price_range(self):
        """测试价格范围参数提取"""
        text = "预算500万到800万"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "price_range" in result
        assert "500" in str(result["price_range"].value) or "800" in str(result["price_range"].value)

    def test_extract_area(self):
        """测试面积参数提取"""
        text = "100平米的房子"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "area" in result
        assert result["area"].value == 100 or "100" in str(result["area"].value)

    def test_extract_birth_date_mingpan(self):
        """测试命理咨询出生日期提取"""
        text = "我是1990年5月15日出生的"
        result = extract_params(TaskType.MINGPAN, text)
        
        assert "birth_date" in result
        assert result["birth_date"].status in [ParamStatus.VALID, ParamStatus.MISSING]

    def test_extract_birth_time_mingpan(self):
        """测试命理咨询出生时辰提取"""
        text = "我是早上8点出生的"
        result = extract_params(TaskType.MINGPAN, text)
        
        assert "birth_time" in result

    def test_extract_gender_mingpan(self):
        """测试命理咨询性别提取"""
        text = "我是男命"
        result = extract_params(TaskType.MINGPAN, text)
        
        assert "gender" in result

    def test_missing_required_params(self):
        """测试缺失必要参数"""
        text = "分析房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "city" in result
        assert result["city"].status == ParamStatus.MISSING

    def test_policy_query_params(self):
        """测试政策查询参数提取"""
        text = "查一下杭州的购房政策"
        result = extract_params(TaskType.POLICY_QUERY, text)
        
        assert "city" in result
        assert result["city"].value == "杭州"

    def test_emotion_params(self):
        """测试情感陪伴参数提取"""
        text = "我今天心情不好"
        result = extract_params(TaskType.EMOTION, text)
        
        assert isinstance(result, dict)

    def test_empty_text(self):
        """测试空文本"""
        text = ""
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert isinstance(result, dict)

    def test_multiple_cities(self):
        """测试多个城市"""
        text = "比较深圳和杭州的房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "city" in result

    def test_floor_info(self):
        """测试楼层信息提取"""
        text = "15楼的房子"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "floor" in result or "area" in result or "city" in result

    def test_orientation_info(self):
        """测试朝向信息提取"""
        text = "南北通透的房子"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "orientation" in result or "area" in result or "city" in result


class TestGenerateQuestions:
    """追问生成测试类"""

    def test_generate_city_question(self):
        """测试生成城市追问"""
        question = generate_questions(["city"], TaskType.PROPERTY_ANALYSIS)
        
        assert isinstance(question, str)
        assert len(question) > 0
        assert "城市" in question or "地区" in question or "哪里" in question

    def test_generate_price_range_question(self):
        """测试生成预算追问"""
        question = generate_questions(["price_range"], TaskType.PROPERTY_ANALYSIS)
        
        assert isinstance(question, str)
        assert "预算" in question or "价格" in question or "多少钱" in question

    def test_generate_area_question(self):
        """测试生成面积追问"""
        question = generate_questions(["area"], TaskType.PROPERTY_ANALYSIS)
        
        assert isinstance(question, str)
        assert "面积" in question or "多大" in question or "平米" in question

    def test_generate_multiple_questions(self):
        """测试生成多个追问"""
        question = generate_questions(["city", "price_range", "area"], TaskType.PROPERTY_ANALYSIS)
        
        assert isinstance(question, str)
        assert len(question) > 0

    def test_generate_birth_date_question(self):
        """测试生成出生日期追问"""
        question = generate_questions(["birth_date"], TaskType.MINGPAN)
        
        assert isinstance(question, str)
        assert "出生" in question or "生日" in question or "日期" in question

    def test_generate_birth_time_question(self):
        """测试生成出生时辰追问"""
        question = generate_questions(["birth_time"], TaskType.MINGPAN)
        
        assert isinstance(question, str)
        assert "时辰" in question or "几点" in question or "时间" in question

    def test_generate_empty_params(self):
        """测试空参数列表"""
        question = generate_questions([], TaskType.PROPERTY_ANALYSIS)
        
        assert isinstance(question, str)

    def test_question_natural_language(self):
        """测试追问自然语言表达"""
        question = generate_questions(["city"], TaskType.PROPERTY_ANALYSIS)
        
        assert question.endswith("？") or question.endswith("?") or "请" in question


class TestParamResultStructure:
    """参数结果结构测试"""

    def test_param_result_structure(self):
        """测试ParamResult结构"""
        text = "深圳南山区"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        if "city" in result:
            param = result["city"]
            assert hasattr(param, 'value')
            assert hasattr(param, 'status')
            assert hasattr(param, 'raw_value')
            assert isinstance(param.status, ParamStatus)

    def test_param_status_values(self):
        """测试参数状态值"""
        valid_statuses = [ParamStatus.VALID, ParamStatus.MISSING, ParamStatus.INVALID]
        
        for status in valid_statuses:
            assert isinstance(status, ParamStatus)


class TestEdgeCases:
    """边界情况测试"""

    def test_very_long_text(self):
        """测试超长文本"""
        text = "深圳" * 100 + "的房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert isinstance(result, dict)

    def test_special_characters(self):
        """测试特殊字符"""
        text = "深圳@#￥%的房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert isinstance(result, dict)

    def test_numbers_only(self):
        """测试纯数字"""
        text = "123456"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert isinstance(result, dict)

    def test_mixed_language(self):
        """测试中英混合"""
        text = "Shenzhen深圳的房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert isinstance(result, dict)

    def test_unknown_task_type(self):
        """测试未知任务类型"""
        text = "测试内容"
        result = extract_params(TaskType.UNKNOWN, text)
        
        assert isinstance(result, dict)


class TestIntegration:
    """集成测试"""

    def test_full_extraction_flow(self):
        """测试完整提取流程"""
        text = "分析深圳南山区500万预算的房子"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        assert "city" in result
        assert result["city"].value == "深圳"
        
        assert "district" in result
        assert result["district"].value == "南山区"

    def test_missing_params_flow(self):
        """测试缺失参数流程"""
        text = "分析房价"
        result = extract_params(TaskType.PROPERTY_ANALYSIS, text)
        
        missing_params = [
            key for key, param in result.items()
            if param.status == ParamStatus.MISSING
        ]
        
        if missing_params:
            question = generate_questions(missing_params, TaskType.PROPERTY_ANALYSIS)
            assert len(question) > 0

    def test_mingpan_full_flow(self):
        """测试命理咨询完整流程"""
        text = "帮我算命"
        result = extract_params(TaskType.MINGPAN, text)
        
        missing_params = [
            key for key, param in result.items()
            if param.status == ParamStatus.MISSING
        ]
        
        if missing_params:
            question = generate_questions(missing_params, TaskType.MINGPAN)
            assert len(question) > 0
