"""
任务分析模块
评估任务复杂度和提取任务特征
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskFeatures:
    """任务特征"""
    task_type: str  # 任务类型，如"问答"、"分析"、"生成"等
    text_length: int  # 文本长度
    keywords: List[str]  # 关键词
    complexity: float  # 复杂度分数 (0.0-1.0)


class TaskAnalyzer:
    """任务分析器"""
    
    def __init__(self):
        self.keyword_patterns = {
            "问答": ["多少", "什么", "如何", "怎样", "为什么", "吗", "?", "？"],
            "分析": ["分析", "评估", "预测", "趋势", "对比", "差异"],
            "生成": ["生成", "写", "创建", "设计", "规划"],
            "报告": ["报告", "总结", "详细", "全面"]
        }
    
    def analyze(self, query: str) -> TaskFeatures:
        """分析任务
        
        Args:
            query: 用户查询
            
        Returns:
            任务特征
        """
        logger.info(f"分析任务: {query}")
        
        # 提取任务类型
        task_type = self._detect_task_type(query)
        
        # 提取文本长度
        text_length = len(query)
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        # 评估复杂度
        complexity = self._evaluate_complexity(query, task_type, text_length, keywords)
        
        features = TaskFeatures(
            task_type=task_type,
            text_length=text_length,
            keywords=keywords,
            complexity=complexity
        )
        
        logger.info(f"任务分析结果: {features}")
        return features
    
    def _detect_task_type(self, query: str) -> str:
        """检测任务类型
        
        Args:
            query: 用户查询
            
        Returns:
            任务类型
        """
        # 基于关键词检测任务类型
        for task_type, patterns in self.keyword_patterns.items():
            for pattern in patterns:
                if pattern in query:
                    return task_type
        
        # 默认任务类型
        return "问答"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词
        
        Args:
            query: 用户查询
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取
        keywords = []
        
        # 地点关键词
        locations = ["深圳", "广州", "北京", "上海", "杭州", "成都", "武汉", "西安", "南京"]
        for location in locations:
            if location in query:
                # 提取完整地点，如"深圳南山区"
                for district in ["区", "县", "市", "省"]:
                    if district in query and location in query:
                        start_idx = query.find(location)
                        end_idx = query.find(district, start_idx)
                        if end_idx != -1:
                            keywords.append(query[start_idx:end_idx+1])
                        break
                if not any(location in keyword for keyword in keywords):
                    keywords.append(location)
        
        # 主题关键词
        topics = ["房价", "房产", "投资", "分析", "报告", "政策", "趋势", "预测"]
        for topic in topics:
            if topic in query and topic not in keywords:
                keywords.append(topic)
        
        return keywords
    
    def _evaluate_complexity(self, query: str, task_type: str, text_length: int, keywords: List[str]) -> float:
        """评估任务复杂度
        
        Args:
            query: 用户查询
            task_type: 任务类型
            text_length: 文本长度
            keywords: 关键词列表
            
        Returns:
            复杂度分数 (0.0-1.0)
        """
        # 基于多种因素评估复杂度
        complexity = 0.0
        
        # 文本长度因素 (0.0-0.3)
        length_factor = min(text_length / 100, 1.0) * 0.3
        complexity += length_factor
        
        # 任务类型因素 (0.0-0.4)
        task_type_factor = 0.0
        if task_type == "问答":
            task_type_factor = 0.1
        elif task_type == "分析":
            task_type_factor = 0.25
        elif task_type == "生成":
            task_type_factor = 0.3
        elif task_type == "报告":
            task_type_factor = 0.4
        complexity += task_type_factor
        
        # 关键词因素 (0.0-0.3)
        keyword_factor = min(len(keywords) / 5, 1.0) * 0.3
        complexity += keyword_factor
        
        # 归一化到0.0-1.0范围
        complexity = max(0.0, min(1.0, complexity))
        
        return complexity


# 全局分析器实例
task_analyzer: Optional[TaskAnalyzer] = None


def get_task_analyzer() -> TaskAnalyzer:
    """获取任务分析器实例"""
    global task_analyzer
    if task_analyzer is None:
        task_analyzer = TaskAnalyzer()
    return task_analyzer


def analyze_task(query: str) -> TaskFeatures:
    """分析任务"""
    analyzer = get_task_analyzer()
    return analyzer.analyze(query)
