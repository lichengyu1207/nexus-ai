"""
任务参数提取模块

功能：从用户输入中提取任务参数，如城市、预算、面积等
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    PROPERTY_ANALYSIS = "property_analysis"
    POLICY_QUERY = "policy_query"
    MINGPAN = "mingpan"
    EMOTION = "emotion"
    REPORT_GENERATION = "report_generation"
    TOOL_CALL = "tool_call"
    UNKNOWN = "unknown"


class ParamStatus(str, Enum):
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"


@dataclass
class ParamResult:
    value: Any
    status: ParamStatus
    raw_value: str


CITY_PATTERNS = [
    r"深圳", r"北京", r"上海", r"广州", r"杭州", r"成都", r"武汉", r"南京",
    r"苏州", r"西安", r"重庆", r"天津", r"长沙", r"郑州", r"青岛",
    r"厦门", r"宁波", r"福州", r"济南", r"合肥", r"昆明", r"大连",
]

DISTRICT_PATTERNS = [
    r"南山区", r"福田区", r"罗湖区", r"宝安区", r"龙岗区",
    r"朝阳区", r"海淀区", r"西城区", r"东城区", r"丰台区",
    r"浦东新区", r"黄浦区", r"徐汇区", r"静安区", r"闵行区",
]

PRICE_PATTERNS = [
    r"(\d+)万", r"(\d+)万?(\d+)万", r"(\d+)万到(\d+)万",
    r"预算(\d+)", r"总价(\d+)",
]

AREA_PATTERNS = [
    r"(\d+)平米", r"(\d+)平", r"(\d+)㎡",
    r"面积(\d+)",
]

DATE_PATTERNS = [
    r"(\d{4})年(\d{1,2})月(\d{1,2})日",
    r"(\d{4})-(\d{1,2})-(\d{1,2})",
    r"(\d{4})/(\d{1,2})/(\d{1,2})",
]

TIME_PATTERNS = [
    r"子时|丑时|寅时|卯时|辰时|巳时|午时|未时|申时|酉时|戌时|亥时",
    r"(\d{1,2})点",
]

GENDER_PATTERNS = [
    r"男命", r"女命", r"我是男的", r"我是女的",
    r"男", r"女",
]


def extract_city(text: str) -> Optional[str]:
    for pattern in CITY_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_district(text: str) -> Optional[str]:
    for pattern in DISTRICT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_price_range(text: str) -> Optional[str]:
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_area(text: str) -> Optional[int]:
    for pattern in AREA_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def extract_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_time(text: str) -> Optional[str]:
    for pattern in TIME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_gender(text: str) -> Optional[str]:
    for pattern in GENDER_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_params(task_type: TaskType, text: str) -> Dict[str, ParamResult]:
    params: Dict[str, ParamResult] = {}
    
    if task_type == TaskType.PROPERTY_ANALYSIS:
        city = extract_city(text)
        params["city"] = ParamResult(
            value=city,
            status=ParamStatus.VALID if city else ParamStatus.MISSING,
            raw_value=city or ""
        )
        
        district = extract_district(text)
        params["district"] = ParamResult(
            value=district,
            status=ParamStatus.VALID if district else ParamStatus.MISSING,
            raw_value=district or ""
        )
        
        price = extract_price_range(text)
        params["price_range"] = ParamResult(
            value=price,
            status=ParamStatus.VALID if price else ParamStatus.MISSING,
            raw_value=price or ""
        )
        
        area = extract_area(text)
        params["area"] = ParamResult(
            value=area,
            status=ParamStatus.VALID if area else ParamStatus.MISSING,
            raw_value=str(area) if area else ""
        )
        
    elif task_type == TaskType.POLICY_QUERY:
        city = extract_city(text)
        params["city"] = ParamResult(
            value=city,
            status=ParamStatus.VALID if city else ParamStatus.MISSING,
            raw_value=city or ""
        )
        
    elif task_type == TaskType.MINGPAN:
        date = extract_date(text)
        params["birth_date"] = ParamResult(
            value=date,
            status=ParamStatus.VALID if date else ParamStatus.MISSING,
            raw_value=date or ""
        )
        
        time = extract_time(text)
        params["birth_time"] = ParamResult(
            value=time,
            status=ParamStatus.VALID if time else ParamStatus.MISSING,
            raw_value=time or ""
        )
        
        gender = extract_gender(text)
        params["gender"] = ParamResult(
            value=gender,
            status=ParamStatus.VALID if gender else ParamStatus.MISSING,
            raw_value=gender or ""
        )
        
    return params


def get_missing_params(params: Dict[str, ParamResult]) -> List[str]:
    return [key for key, value in params.items() if value.status == ParamStatus.MISSING]


QUESTION_TEMPLATES = {
    "city": "请问您想分析哪个城市？",
    "district": "请问您想分析哪个区域？",
    "price_range": "请问您的预算大概是多少？",
    "area": "请问您想要的面积大概是多少？",
    "birth_date": "请问您的出生日期是？",
    "birth_time": "请问您的出生时辰是？",
    "gender": "请问您的性别是？",
}


def generate_questions(missing_params: List[str], task_type: TaskType) -> str:
    if not missing_params:
        return ""
    
    questions = []
    for param in missing_params:
        if param in QUESTION_TEMPLATES:
            questions.append(QUESTION_TEMPLATES[param])
    
    if questions:
        return " ".join(questions)
    
    return "请提供更多信息以便为您分析。"


def extract_params_to_dict(task_type: TaskType, text: str) -> Dict:
    params = extract_params(task_type, text)
    missing_params = get_missing_params(params)
    question = generate_questions(missing_params, task_type)
    
    return {
        "params": {key: {"value": v.value, "status": v.status.value} for key, v in params.items()},
        "missing_params": missing_params,
        "question": question,
        "is_complete": len(missing_params) == 0
    }
