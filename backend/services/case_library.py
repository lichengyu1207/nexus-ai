# -*- coding: utf-8 -*-
"""
房都督案例库系统
存储和管理4000+真实案例，支持智能检索和匹配
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CaseType(str, Enum):
    """案例类型"""
    DESTINY = "destiny"           # 命盘类
    PROPERTY = "property"         # 房产类
    COMBINED = "combined"         # 复合类（命盘+房产）
    EMOTION = "emotion"           # 情感类
    CAREER = "career"             # 事业类
    FINANCE = "finance"           # 财运类

class CaseStatus(str, Enum):
    """案例状态"""
    DRAFT = "draft"               # 草稿
    PUBLISHED = "published"       # 已发布
    ARCHIVED = "archived"         # 已归档

@dataclass
class SixDimensionAnalysis:
    """六维框架分析"""
    pattern: Dict[str, Any] = field(default_factory=dict)      # 格局（天赋方向）
    wealth: Dict[str, Any] = field(default_factory=dict)       # 财运（正偏财属性）
    marriage: Dict[str, Any] = field(default_factory=dict)     # 姻缘（感情模式）
    career: Dict[str, Any] = field(default_factory=dict)       # 事业（节点选择）
    social: Dict[str, Any] = field(default_factory=dict)       # 人际（滋养与消耗）
    execution: Dict[str, Any] = field(default_factory=dict)    # 执行力（心态与行动）

@dataclass
class UserProfile:
    """用户画像（脱敏）"""
    birth_year: int                      # 出生年份
    zodiac: str                          # 生肖
    birth_month: Optional[int] = None    # 出生月份
    birth_day: Optional[int] = None      # 出生日
    birth_hour: Optional[str] = None     # 出生时辰
    gender: Optional[str] = None         # 性别
    city: Optional[str] = None           # 当前城市
    profession: Optional[str] = None     # 职业
    budget: Optional[str] = None         # 预算范围

@dataclass
class CaseRecord:
    """案例记录"""
    id: str                                          # 案例ID
    case_type: CaseType                              # 案例类型
    status: CaseStatus = CaseStatus.PUBLISHED        # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 用户画像
    user_profile: UserProfile = None                 # 用户画像（脱敏）
    
    # 问题信息
    question: str = ""                               # 用户原始问题
    question_category: str = ""                      # 问题分类
    question_subcategory: str = ""                   # 问题子分类
    
    # 分析过程
    analysis: SixDimensionAnalysis = None            # 六维分析
    dialogue_history: List[Dict[str, str]] = field(default_factory=list)  # 对话历史
    
    # 建议与结果
    recommendations: List[Dict[str, Any]] = field(default_factory=list)   # 建议列表
    action_steps: List[Dict[str, Any]] = field(default_factory=list)      # 行动步骤
    final_decision: str = ""                         # 用户最终决策
    outcome: str = ""                                # 结果跟踪
    
    # 元数据
    tags: List[str] = field(default_factory=list)    # 标签
    rating: Optional[int] = None                     # 用户评分（1-5）
    feedback: str = ""                               # 用户反馈
    referenced_by: List[str] = field(default_factory=list)  # 被引用的案例ID

class CaseLibrary:
    """
    案例库管理器
    负责案例的存储、检索、匹配
    """
    
    def __init__(self, data_dir: str = "data/cases"):
        self.data_dir = data_dir
        self.cases: Dict[str, CaseRecord] = {}
        self.index_by_zodiac: Dict[str, List[str]] = {}      # 按生肖索引
        self.index_by_type: Dict[str, List[str]] = {}        # 按类型索引
        self.index_by_category: Dict[str, List[str]] = {}    # 按问题分类索引
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_cases()
    
    def _load_cases(self):
        """加载已有案例"""
        index_file = os.path.join(self.data_dir, "index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    for case_id in index_data.get("case_ids", []):
                        case_file = os.path.join(self.data_dir, f"{case_id}.json")
                        if os.path.exists(case_file):
                            with open(case_file, 'r', encoding='utf-8') as cf:
                                case_data = json.load(cf)
                                case = self._dict_to_case(case_data)
                                self.cases[case_id] = case
                                self._update_indexes(case)
                logger.info(f"Loaded {len(self.cases)} cases from library")
            except Exception as e:
                logger.error(f"Error loading cases: {e}")
    
    def _dict_to_case(self, data: Dict) -> CaseRecord:
        """字典转案例对象"""
        user_profile = None
        if data.get("user_profile"):
            user_profile = UserProfile(**data["user_profile"])
        
        analysis = None
        if data.get("analysis"):
            analysis = SixDimensionAnalysis(**data["analysis"])
        
        case = CaseRecord(
            id=data["id"],
            case_type=CaseType(data["case_type"]),
            status=CaseStatus(data.get("status", "published")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            user_profile=user_profile,
            question=data.get("question", ""),
            question_category=data.get("question_category", ""),
            question_subcategory=data.get("question_subcategory", ""),
            analysis=analysis,
            dialogue_history=data.get("dialogue_history", []),
            recommendations=data.get("recommendations", []),
            action_steps=data.get("action_steps", []),
            final_decision=data.get("final_decision", ""),
            outcome=data.get("outcome", ""),
            tags=data.get("tags", []),
            rating=data.get("rating"),
            feedback=data.get("feedback", ""),
            referenced_by=data.get("referenced_by", [])
        )
        return case
    
    def _update_indexes(self, case: CaseRecord):
        """更新索引"""
        # 按生肖索引
        if case.user_profile and case.user_profile.zodiac:
            zodiac = case.user_profile.zodiac
            if zodiac not in self.index_by_zodiac:
                self.index_by_zodiac[zodiac] = []
            self.index_by_zodiac[zodiac].append(case.id)
        
        # 按类型索引
        case_type = case.case_type.value
        if case_type not in self.index_by_type:
            self.index_by_type[case_type] = []
        self.index_by_type[case_type].append(case.id)
        
        # 按问题分类索引
        if case.question_category:
            cat = case.question_category
            if cat not in self.index_by_category:
                self.index_by_category[cat] = []
            self.index_by_category[cat].append(case.id)
    
    def add_case(self, case: CaseRecord) -> str:
        """添加案例"""
        self.cases[case.id] = case
        self._update_indexes(case)
        self._save_case(case)
        self._save_index()
        logger.info(f"Added case: {case.id}")
        return case.id
    
    def _save_case(self, case: CaseRecord):
        """保存单个案例"""
        case_file = os.path.join(self.data_dir, f"{case.id}.json")
        case_dict = asdict(case)
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case_dict, f, ensure_ascii=False, indent=2)
    
    def _save_index(self):
        """保存索引"""
        index_file = os.path.join(self.data_dir, "index.json")
        index_data = {
            "case_ids": list(self.cases.keys()),
            "total_count": len(self.cases),
            "updated_at": datetime.now().isoformat()
        }
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def get_case(self, case_id: str) -> Optional[CaseRecord]:
        """获取案例"""
        return self.cases.get(case_id)
    
    def search_similar_cases(
        self,
        zodiac: str = None,
        case_type: CaseType = None,
        question_category: str = None,
        tags: List[str] = None,
        limit: int = 5
    ) -> List[CaseRecord]:
        """
        搜索相似案例
        
        Args:
            zodiac: 生肖
            case_type: 案例类型
            question_category: 问题分类
            tags: 标签列表
            limit: 返回数量限制
        
        Returns:
            相似案例列表
        """
        candidates = set()
        
        # 按生肖筛选
        if zodiac and zodiac in self.index_by_zodiac:
            candidates.update(self.index_by_zodiac[zodiac])
        
        # 按类型筛选
        if case_type:
            type_cases = set(self.index_by_type.get(case_type.value, []))
            if candidates:
                candidates &= type_cases
            else:
                candidates = type_cases
        
        # 按问题分类筛选
        if question_category and question_category in self.index_by_category:
            cat_cases = set(self.index_by_category[question_category])
            if candidates:
                candidates &= cat_cases
            else:
                candidates = cat_cases
        
        # 如果没有筛选条件，返回所有案例
        if not candidates:
            candidates = set(self.cases.keys())
        
        # 按标签匹配度排序
        results = []
        for case_id in candidates:
            case = self.cases.get(case_id)
            if case:
                score = 0
                if tags:
                    matching_tags = set(tags) & set(case.tags)
                    score = len(matching_tags)
                if case.rating:
                    score += case.rating
                results.append((case, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取案例库统计信息"""
        stats = {
            "total_cases": len(self.cases),
            "by_type": {},
            "by_zodiac": {},
            "by_category": {},
            "avg_rating": 0,
            "high_rating_count": 0  # 评分>=4的案例数
        }
        
        ratings = []
        for case in self.cases.values():
            # 按类型统计
            type_key = case.case_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            # 按生肖统计
            if case.user_profile and case.user_profile.zodiac:
                zodiac = case.user_profile.zodiac
                stats["by_zodiac"][zodiac] = stats["by_zodiac"].get(zodiac, 0) + 1
            
            # 按分类统计
            if case.question_category:
                cat = case.question_category
                stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            
            # 评分统计
            if case.rating:
                ratings.append(case.rating)
                if case.rating >= 4:
                    stats["high_rating_count"] += 1
        
        if ratings:
            stats["avg_rating"] = sum(ratings) / len(ratings)
        
        return stats


# 全局案例库实例
case_library = CaseLibrary()
