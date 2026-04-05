"""
多任务意图识别模块

功能：从用户输入中识别出多个独立任务，并判断每个任务的类型
"""
import re
from typing import List, Dict, Optional, Tuple
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


@dataclass
class ParsedTask:
    type: TaskType
    confidence: float
    span: str
    start: int
    end: int


@dataclass
class ParseResult:
    tasks: List[ParsedTask]
    relations: List[Dict]
    original_text: str


TASK_PATTERNS = {
    TaskType.PROPERTY_ANALYSIS: [
        r"分析(.+?)房价",
        r"查(.+?)房价",
        r"(.+?)房价走势",
        r"评估(.+?)房产",
        r"分析(.+?)学区房",
        r"查(.+?)房源",
        r"对比(.+?)房价",
        r"(.+?)房产分析",
        r"房价分析",
        r"房产估值",
        r"分析(.+?)房价走势",
    ],
    TaskType.POLICY_QUERY: [
        r"查(.+?)政策",
        r"(.+?)政策",
        r"(.+?)购房政策",
        r"(.+?)限购",
        r"(.+?)贷款政策",
        r"政策查询",
        r"查一下(.+?)政策",
    ],
    TaskType.MINGPAN: [
        r"算(.+?)命盘",
        r"(.+?)命盘",
        r"算(.+?)运势",
        r"(.+?)事业运",
        r"(.+?)财运",
        r"(.+?)感情运",
        r"八字分析",
        r"紫微斗数",
        r"星座运势",
        r"算一下(.+?)命盘",
    ],
    TaskType.EMOTION: [
        r"陪我聊",
        r"聊天",
        r"倾诉",
        r"心情不好",
        r"压力大",
        r"焦虑",
        r"失眠",
    ],
    TaskType.REPORT_GENERATION: [
        r"生成报告",
        r"导出报告",
        r"下载报告",
        r"生成PDF",
        r"生成Excel",
    ],
    TaskType.TOOL_CALL: [
        r"计算器",
        r"汇率",
        r"天气",
        r"翻译",
    ],
}

TASK_KEYWORDS = {
    TaskType.PROPERTY_ANALYSIS: ["房价", "房产", "房源", "学区房", "二手房", "新房", "租房", "评估", "估值", "房子", "住宅", "公寓", "别墅", "商铺", "写字楼"],
    TaskType.POLICY_QUERY: ["政策", "限购", "贷款", "公积金", "契税", "首付", "税费"],
    TaskType.MINGPAN: ["命盘", "运势", "八字", "紫微", "星座", "事业运", "财运", "感情运", "算命", "风水"],
    TaskType.EMOTION: ["聊天", "倾诉", "心情", "压力", "焦虑", "失眠", "孤独"],
    TaskType.REPORT_GENERATION: ["报告", "PDF", "Excel", "导出", "下载"],
    TaskType.TOOL_CALL: ["计算", "汇率", "天气", "翻译"],
}

CONNECTORS = ["顺便", "还有", "再", "然后", "接着", "同时", "另外", "并且", "以及"]
SEPARATORS = ["，", "。", "；", "；", "\n", "\t"]


def split_by_connectors(text: str) -> List[str]:
    """根据连接词和分隔符分割文本"""
    segments = [text]
    
    for connector in CONNECTORS:
        new_segments = []
        for segment in segments:
            parts = re.split(f"({re.escape(connector)})", segment)
            current = ""
            for part in parts:
                if part.strip() and part.strip() not in CONNECTORS:
                    current += part
                elif part.strip() in CONNECTORS and current.strip():
                    new_segments.append(current.strip())
                    current = ""
            if current.strip():
                new_segments.append(current.strip())
        segments = new_segments
    
    final_segments = []
    for segment in segments:
        for sep in SEPARATORS:
            segment = segment.replace(sep, "|||")
        parts = segment.split("|||")
        final_segments.extend([p.strip() for p in parts if p.strip()])
    
    return [s.strip() for s in final_segments if s.strip()]


def match_task_type(text: str) -> Optional[Tuple[TaskType, float]]:
    """匹配任务类型"""
    scores: Dict[TaskType, float] = {}
    
    for task_type, patterns in TASK_PATTERNS.items():
        for pattern in patterns:
            try:
                if re.search(pattern, text):
                    scores[task_type] = scores.get(task_type, 0) + 0.5
            except Exception:
                continue
    
    for task_type, keywords in TASK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[task_type] = scores.get(task_type, 0) + 0.3
    
    if not scores:
        return None
    
    best_type = max(scores, key=scores.get)
    confidence = min(scores[best_type], 1.0)
    
    return best_type, confidence


def parse_intent(text: str) -> ParseResult:
    """
    解析用户输入，识别多个任务
    
    Args:
        text: 用户输入文本
        
    Returns:
        ParseResult: 包含任务列表和关系的结果
    """
    segments = split_by_connectors(text)
    tasks: List[ParsedTask] = []
    relations: List[Dict] = []
    
    current_pos = 0
    for segment in segments:
        match_result = match_task_type(segment)
        
        if match_result:
            task_type, confidence = match_result
            
            start = text.find(segment, current_pos)
            if start == -1:
                start = current_pos
            end = start + len(segment)
            current_pos = end
            
            task = ParsedTask(
                type=task_type,
                confidence=confidence,
                span=segment,
                start=start,
                end=end
            )
            tasks.append(task)
    
    if not tasks and text.strip():
        match_result = match_task_type(text)
        if match_result:
            task_type, confidence = match_result
            tasks.append(ParsedTask(
                type=task_type,
                confidence=confidence,
                span=text,
                start=0,
                end=len(text)
            ))
        else:
            tasks.append(ParsedTask(
                type=TaskType.UNKNOWN,
                confidence=0.5,
                span=text,
                start=0,
                end=len(text)
            ))
    
    return ParseResult(
        tasks=tasks,
        relations=relations,
        original_text=text
    )


def parse_intent_to_dict(text: str) -> Dict:
    """将解析结果转换为字典格式"""
    result = parse_intent(text)
    return {
        "tasks": [
            {
                "type": task.type.value,
                "confidence": task.confidence,
                "span": task.span
            }
            for task in result.tasks
        ],
        "relations": result.relations,
        "original_text": result.original_text
    }


if __name__ == "__main__":
    test_cases = [
        "帮我分析深圳南山区的房价走势，顺便查一下杭州最近的政策，再给我算一下我的命盘事业运",
        "我想看看我的命盘，顺便查一下上海的学区房",
        "分析房价",
        "帮我分析深圳和杭州的房价，再算一下我的命盘",
        "陪我聊聊，最近压力好大",
        "分析北京房价；查上海政策；算一下我的命盘",
    ]
    
    for test in test_cases:
        print(f"\n输入: {test}")
        result = parse_intent_to_dict(test)
        print(f"解析结果: {result}")
