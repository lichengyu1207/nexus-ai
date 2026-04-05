"""
法规解析智能体
将法规文本解析为结构化的合规规则
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RuleCategory(str, Enum):
    DATA_PRIVACY = "data_privacy"
    DATA_SECURITY = "data_security"
    REAL_ESTATE = "real_estate"
    AI_GOVERNANCE = "ai_governance"
    FINANCIAL = "financial"
    CONTRACT = "contract"
    CONSUMER_PROTECTION = "consumer_protection"


class ComplianceLevel(str, Enum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"


class ComplianceRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_document_id: str
    source_article: str
    category: RuleCategory
    compliance_level: ComplianceLevel
    rule_text: str
    conditions: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)
    penalties: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    applicability: Dict[str, Any] = Field(default_factory=dict)
    check_method: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ParsedRegulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    title: str
    structure: Dict[str, Any]
    rules: List[ComplianceRule] = Field(default_factory=list)
    definitions: Dict[str, str] = Field(default_factory=dict)
    cross_references: List[str] = Field(default_factory=list)
    parsed_at: datetime = Field(default_factory=datetime.now)


class ArticleParser:
    ARTICLE_PATTERNS = [
        (r'第([一二三四五六七八九十百]+)条', 'numbered'),
        (r'第(\d+)条', 'numbered_digit'),
        (r'([一二三四五六七八九十]+)、', 'itemized'),
        (r'（([一二三四五六七八九十]+)）', 'sub_itemized'),
    ]
    
    def parse(self, content: str) -> Dict[str, Any]:
        articles = {}
        
        article_pattern = r'第([一二三四五六七八九十百]+)条[^\n]*\n([\s\S]*?)(?=第[一二三四五六七八九十百]+条|$)'
        matches = re.finditer(article_pattern, content)
        
        for match in matches:
            article_num = self._chinese_to_number(match.group(1))
            article_content = match.group(2).strip()
            
            articles[f"第{match.group(1)}条"] = {
                "number": article_num,
                "content": article_content,
                "paragraphs": self._parse_paragraphs(article_content)
            }
        
        return articles
    
    def _parse_paragraphs(self, content: str) -> List[Dict[str, Any]]:
        paragraphs = []
        
        para_pattern = r'([一二三四五六七八九十]+)、([^\n]+)'
        matches = re.finditer(para_pattern, content)
        
        for match in matches:
            paragraphs.append({
                "number": self._chinese_to_number(match.group(1)),
                "text": match.group(2).strip()
            })
        
        return paragraphs
    
    def _chinese_to_number(self, chinese: str) -> int:
        mapping = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '二十': 20, '三十': 30, '四十': 40, '五十': 50,
            '百': 100
        }
        
        if chinese in mapping:
            return mapping[chinese]
        
        if '十' in chinese:
            parts = chinese.split('十')
            tens = mapping.get(parts[0], 1) if parts[0] else 1
            ones = mapping.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            return tens * 10 + ones
        
        return 0


class ObligationExtractor:
    OBLIGATION_PATTERNS = [
        (r'应当([^。，]+)', ComplianceLevel.MANDATORY),
        (r'必须([^。，]+)', ComplianceLevel.MANDATORY),
        (r'不得([^。，]+)', ComplianceLevel.PROHIBITED),
        (r'禁止([^。，]+)', ComplianceLevel.PROHIBITED),
        (r'可以([^。，]+)', ComplianceLevel.CONDITIONAL),
        (r'鼓励([^。，]+)', ComplianceLevel.RECOMMENDED),
    ]
    
    CONDITION_PATTERNS = [
        r'在([^，。]+)条件下',
        r'如([^，。]+)',
        r'若([^，。]+)',
        r'当([^，。]+)时',
    ]
    
    EXCEPTION_PATTERNS = [
        r'但([^，。]+)除外',
        r'除([^，。]+)外',
        r'法律另有规定的除外',
    ]
    
    PENALTY_PATTERNS = [
        r'处([^，。]+)罚款',
        r'责令([^，。]+)',
        r'吊销([^，。]+)',
        r'追究([^，。]+)责任',
        r'构成犯罪的',
    ]
    
    def extract_obligations(
        self,
        article_content: str,
        article_ref: str,
        document_id: str
    ) -> List[ComplianceRule]:
        rules = []
        
        for pattern, level in self.OBLIGATION_PATTERNS:
            matches = re.finditer(pattern, article_content)
            for match in matches:
                obligation_text = match.group(0)
                
                conditions = self._extract_conditions(article_content, match.start())
                exceptions = self._extract_exceptions(article_content)
                penalties = self._extract_penalties(article_content)
                
                category = self._determine_category(obligation_text)
                
                rule = ComplianceRule(
                    source_document_id=document_id,
                    source_article=article_ref,
                    category=category,
                    compliance_level=level,
                    rule_text=obligation_text,
                    conditions=conditions,
                    exceptions=exceptions,
                    penalties=penalties,
                    keywords=self._extract_keywords(obligation_text)
                )
                
                rules.append(rule)
        
        return rules
    
    def _extract_conditions(
        self,
        content: str,
        position: int
    ) -> List[str]:
        conditions = []
        
        prefix = content[:position]
        for pattern in self.CONDITION_PATTERNS:
            matches = re.finditer(pattern, prefix)
            for match in matches:
                conditions.append(match.group(0))
        
        return conditions
    
    def _extract_exceptions(self, content: str) -> List[str]:
        exceptions = []
        
        for pattern in self.EXCEPTION_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                exceptions.append(match.group(0))
        
        return exceptions
    
    def _extract_penalties(self, content: str) -> List[str]:
        penalties = []
        
        for pattern in self.PENALTY_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                penalties.append(match.group(0))
        
        return penalties
    
    def _determine_category(self, text: str) -> RuleCategory:
        category_keywords = {
            RuleCategory.DATA_PRIVACY: ["个人信息", "隐私", "敏感信息", "数据主体"],
            RuleCategory.DATA_SECURITY: ["数据安全", "网络安全", "信息安全", "加密"],
            RuleCategory.REAL_ESTATE: ["房地产", "不动产", "房屋", "土地", "产权"],
            RuleCategory.AI_GOVERNANCE: ["人工智能", "算法", "自动化决策", "深度合成"],
            RuleCategory.FINANCIAL: ["金融", "资金", "贷款", "担保"],
            RuleCategory.CONTRACT: ["合同", "协议", "约定", "违约"],
            RuleCategory.CONSUMER_PROTECTION: ["消费者", "用户权益", "知情权"],
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return RuleCategory.CONTRACT
    
    def _extract_keywords(self, text: str) -> List[str]:
        keywords = []
        
        important_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        
        stop_words = {'应当', '必须', '不得', '禁止', '可以', '鼓励', '以及', '或者', '但是', '如果'}
        
        for word in important_words:
            if word not in stop_words and len(word) >= 2:
                keywords.append(word)
        
        return list(set(keywords))[:10]


class DefinitionExtractor:
    DEFINITION_PATTERNS = [
        r'([^，。]+)，是指([^。]+)',
        r'([^，。]+)：指([^。]+)',
        r'([^，。]+)即([^。]+)',
    ]
    
    def extract(self, content: str) -> Dict[str, str]:
        definitions = {}
        
        for pattern in self.DEFINITION_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) <= 20:
                    definitions[term] = definition
        
        return definitions


class CrossReferenceExtractor:
    REFERENCE_PATTERNS = [
        r'《([^》]+)》',
        r'依据([^，。]+)',
        r'参照([^，。]+)',
    ]
    
    def extract(self, content: str) -> List[str]:
        references = []
        
        for pattern in self.REFERENCE_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                ref = match.group(1).strip()
                if ref and len(ref) <= 50:
                    references.append(ref)
        
        return list(set(references))


class RegulationParserAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "RegulationParser",
        llm_client: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.llm_client = llm_client
        
        self.article_parser = ArticleParser()
        self.obligation_extractor = ObligationExtractor()
        self.definition_extractor = DefinitionExtractor()
        self.cross_reference_extractor = CrossReferenceExtractor()
        
        self.parsed_regulations: Dict[str, ParsedRegulation] = {}
        self.rules_index: Dict[str, List[ComplianceRule]] = {}
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"RegulationParserAgent {self.agent_id} initialized")
    
    async def parse_regulation(
        self,
        document: Dict[str, Any]
    ) -> ParsedRegulation:
        document_id = document.get("id", str(uuid4()))
        title = document.get("title", "")
        content = document.get("content", "")
        
        structure = self.article_parser.parse(content)
        
        rules = []
        for article_ref, article_data in structure.items():
            article_content = article_data.get("content", "")
            
            article_rules = self.obligation_extractor.extract_obligations(
                article_content,
                article_ref,
                document_id
            )
            rules.extend(article_rules)
        
        definitions = self.definition_extractor.extract(content)
        
        cross_references = self.cross_reference_extractor.extract(content)
        
        parsed = ParsedRegulation(
            document_id=document_id,
            title=title,
            structure=structure,
            rules=rules,
            definitions=definitions,
            cross_references=cross_references
        )
        
        self.parsed_regulations[document_id] = parsed
        
        for rule in rules:
            category = rule.category.value
            if category not in self.rules_index:
                self.rules_index[category] = []
            self.rules_index[category].append(rule)
        
        return parsed
    
    async def batch_parse(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[ParsedRegulation]:
        results = []
        
        for doc in documents:
            try:
                parsed = await self.parse_regulation(doc)
                results.append(parsed)
            except Exception as e:
                self.logger.error(f"Error parsing document {doc.get('id')}: {e}")
        
        return results
    
    async def get_rules_by_category(
        self,
        category: RuleCategory
    ) -> List[ComplianceRule]:
        return self.rules_index.get(category.value, [])
    
    async def get_rules_by_level(
        self,
        level: ComplianceLevel
    ) -> List[ComplianceRule]:
        rules = []
        
        for category_rules in self.rules_index.values():
            for rule in category_rules:
                if rule.compliance_level == level:
                    rules.append(rule)
        
        return rules
    
    async def search_rules(
        self,
        query: str,
        category: Optional[RuleCategory] = None,
        level: Optional[ComplianceLevel] = None
    ) -> List[ComplianceRule]:
        results = []
        
        search_rules = []
        if category:
            search_rules = self.rules_index.get(category.value, [])
        else:
            for cat_rules in self.rules_index.values():
                search_rules.extend(cat_rules)
        
        for rule in search_rules:
            if level and rule.compliance_level != level:
                continue
            
            if query.lower() in rule.rule_text.lower():
                results.append(rule)
                continue
            
            for keyword in rule.keywords:
                if query.lower() in keyword.lower():
                    results.append(rule)
                    break
        
        return results
    
    async def check_compliance_requirement(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        applicable_rules = []
        
        for category_rules in self.rules_index.values():
            for rule in category_rules:
                for keyword in rule.keywords:
                    if keyword in action:
                        applicable_rules.append({
                            "rule": rule.dict(),
                            "matched_keyword": keyword,
                            "compliance_level": rule.compliance_level.value
                        })
                        break
        
        return applicable_rules
    
    async def get_parsed_regulation(
        self,
        document_id: str
    ) -> Optional[ParsedRegulation]:
        return self.parsed_regulations.get(document_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        total_rules = sum(len(rules) for rules in self.rules_index.values())
        
        by_category = {
            category: len(rules)
            for category, rules in self.rules_index.items()
        }
        
        by_level = {}
        for rules in self.rules_index.values():
            for rule in rules:
                level = rule.compliance_level.value
                by_level[level] = by_level.get(level, 0) + 1
        
        return {
            "total_parsed_documents": len(self.parsed_regulations),
            "total_rules": total_rules,
            "rules_by_category": by_category,
            "rules_by_level": by_level
        }
