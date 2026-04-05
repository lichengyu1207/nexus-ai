from typing import Dict, Any, List
import asyncio
import re
from app.ai_agents.base_agent import BaseAgent


class RequirementAnalyzerAgent(BaseAgent):
    """Agent specialized in analyzing user queries and extracting structured requirements"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "Agent specialized in analyzing user queries and extracting structured requirements"
        self.keywords = {
            "区域": ["位于", "在", "地址", "小区", "地段", "板块", "片区", "区域"],
            "预算": ["预算", "价格", "多少钱", "价位", "总价", "首付", "月供"],
            "房型": ["房型", "户型", "几房", "几室", "面积", "平方", "平方米"],
            "房龄": ["房龄", "几年", "年份", "建成", "建筑年代"],
            "用途": ["自住", "投资", "出租", "学区", "养老", "改善", "刚需"]
        }
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirement analysis task"""
        try:
            # 发布开始事件
            self.publish_start_event(task)
            
            # Extract query from task
            query = task.get("query", "")
            if not query:
                # 如果没有查询，尝试从其他字段构建
                query = self._build_query_from_fields(task)
            
            # 发布进度事件
            self.publish_progress_event(0.2, "开始分析用户查询")
            
            # Analyze query and extract requirements
            requirements = await self.analyze_query(query)
            
            # 发布进度事件
            self.publish_progress_event(0.6, "正在提取结构化需求")
            
            # Extract additional fields from task
            structured_requirements = {
                "query": query,
                "structured": requirements,
                "metadata": {
                    "analysis_time": asyncio.get_event_loop().time(),
                    "confidence": self.calculate_confidence(requirements),
                    "extracted_fields": list(requirements.keys())
                }
            }
            
            # 发布完成事件
            self.publish_complete_event(structured_requirements)
            
            return {
                "success": True,
                "result": structured_requirements
            }
            
        except Exception as e:
            # 发布错误事件
            self.publish_error_event(str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze user query and extract structured requirements"""
        requirements = {}
        
        # 分析区域
        area = await self.extract_area(query)
        if area:
            requirements["area"] = area
        
        # 分析预算
        budget = await self.extract_budget(query)
        if budget:
            requirements["budget"] = budget
        
        # 分析房型
        house_type = await self.extract_house_type(query)
        if house_type:
            requirements["house_type"] = house_type
        
        # 分析房龄
        age = await self.extract_age(query)
        if age:
            requirements["age"] = age
        
        # 分析用途
        purpose = await self.extract_purpose(query)
        if purpose:
            requirements["purpose"] = purpose
        
        return requirements
    
    async def extract_area(self, query: str) -> str:
        """Extract area information from query"""
        # 如果查询很短（比如只有小区名），直接返回整个查询作为区域
        if len(query) <= 20 and not any(char in query for char in ['市', '区', '县', '号', '单元', '室']):
            # 可能只是一个小区名
            return query
        
        # 简单的区域提取逻辑，实际项目中可能需要更复杂的NLP处理
        # 这里使用正则表达式匹配常见的区域模式
        area_patterns = [
            r"(位于|在|分析)([一-龥]+?[区市县街道镇小区社区])",
            r"([一-龥]+?[区市县街道镇小区社区])(的)?房子",
            r"([一-龥]+?[区市县街道镇小区社区])(的)?房价",
            r"([一-龥]+?[小区社区])"
        ]
        
        for pattern in area_patterns:
            match = re.search(pattern, query)
            if match:
                # 返回匹配的区域部分
                for group in match.groups():
                    if group and any(char.isalpha() for char in group):
                        # 过滤掉方位词
                        if group not in ["位于", "在", "的", "分析"]:
                            return group
        
        # 如果没有匹配到，返回整个查询作为区域
        return query
    
    async def extract_budget(self, query: str) -> Dict[str, Any]:
        """Extract budget information from query"""
        budget = {}
        
        # 匹配价格范围
        price_patterns = [
            r"(\d+)万(到|至|到)(\d+)万",
            r"(\d+)万以下",
            r"(\d+)万以上",
            r"预算(\d+)万",
            r"价格(\d+)万"
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, query)
            if match:
                if len(match.groups()) == 3:
                    # 价格范围
                    budget["min"] = float(match.group(1))
                    budget["max"] = float(match.group(3))
                else:
                    # 单一价格或价格上限/下限
                    price = float(match.group(1))
                    if "以下" in query:
                        budget["max"] = price
                    elif "以上" in query:
                        budget["min"] = price
                    else:
                        budget["exact"] = price
                break
        
        return budget if budget else ""
    
    async def extract_house_type(self, query: str) -> Dict[str, Any]:
        """Extract house type information from query"""
        house_type = {}
        
        # 匹配房型
        room_patterns = [
            r"(\d+)房(\d+)厅",
            r"(\d+)室(\d+)厅",
            r"(\d+)房",
            r"(\d+)室"
        ]
        
        for pattern in room_patterns:
            match = re.search(pattern, query)
            if match:
                if len(match.groups()) == 2:
                    house_type["rooms"] = int(match.group(1))
                    house_type["halls"] = int(match.group(2))
                else:
                    house_type["rooms"] = int(match.group(1))
                break
        
        # 匹配面积
        area_pattern = r"(\d+)平方(米)?"
        area_match = re.search(area_pattern, query)
        if area_match:
            house_type["area"] = float(area_match.group(1))
        
        return house_type if house_type else ""
    
    async def extract_age(self, query: str) -> int:
        """Extract house age information from query"""
        # 匹配房龄
        age_patterns = [
            r"房龄(\d+)年",
            r"(\d+)年房龄",
            r"建成于(\d{4})年",
            r"(\d{4})年建成"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, query)
            if match:
                age = match.group(1)
                if len(age) == 4:
                    # 年份，计算房龄
                    current_year = 2026  # 实际项目中应该使用当前年份
                    return current_year - int(age)
                else:
                    # 直接是房龄
                    return int(age)
        
        return 0
    
    async def extract_purpose(self, query: str) -> List[str]:
        """Extract house purpose information from query"""
        purposes = []
        
        purpose_keywords = {
            "自住": ["自住", "自己住", "刚需"],
            "投资": ["投资", "升值", "回报率"],
            "出租": ["出租", "租金", "租客"],
            "学区": ["学区", "学校", "上学", "教育"],
            "养老": ["养老", " elderly", "晚年"],
            "改善": ["改善", " bigger", "更好"],
            "刚需": ["刚需", "首次购房", "首套"]
        }
        
        for purpose, keywords in purpose_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    purposes.append(purpose)
                    break
        
        return purposes
    
    def _build_query_from_fields(self, task: Dict[str, Any]) -> str:
        """Build query from structured fields"""
        fields = []
        if task.get("address"):
            fields.append(f"位于{task['address']}")
        if task.get("property_type"):
            fields.append(f"{task['property_type']}")
        if task.get("area"):
            fields.append(f"面积{task['area']}平方米")
        if task.get("age"):
            fields.append(f"房龄{task['age']}年")
        if task.get("description"):
            fields.append(task['description'])
        
        return "，".join(fields)
    
    def calculate_confidence(self, requirements: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted requirements"""
        if not requirements:
            return 0.3
        
        # 基于提取的字段数量计算置信度
        max_fields = len(self.keywords)
        extracted_fields = len([v for v in requirements.values() if v])
        base_confidence = extracted_fields / max_fields
        
        # 调整置信度
        confidence = min(base_confidence * 0.8 + 0.2, 1.0)
        return round(confidence, 2)
