# -*- coding: utf-8 -*-
"""
六维框架对话引导系统
基于4000+案例库的智能对话模板
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)

class DialogueStyle(str, Enum):
    """对话风格"""
    ZHOU_YU = "zhou_yu"      # 周瑜风格：直接、犀利、有冲击力
    LU_XUN = "lu_xun"        # 陆逊风格：温和、细腻、有温度

class QuestionCategory(str, Enum):
    """问题分类"""
    # 命盘相关
    BASIC_INFO = "basic_info"           # 基础信息
    WEALTH = "wealth"                   # 财运
    CAREER = "career"                   # 事业
    MARRIAGE = "marriage"               # 姻缘
    SOCIAL = "social"                   # 人际与心态
    
    # 房产相关
    CITY_CHOICE = "city_choice"         # 城市选择
    BUY_TIMING = "buy_timing"           # 买房时机
    HOUSE_STRATEGY = "house_strategy"   # 选房策略
    BUDGET_LOAN = "budget_loan"         # 预算与贷款
    
    # 混合类
    COMBINED = "combined"               # 综合决策

@dataclass
class DialogueTemplate:
    """对话模板"""
    category: QuestionCategory
    question_pattern: str               # 用户问题模式
    style: DialogueStyle                # 回复风格
    response: str                       # 回复模板
    follow_up_questions: List[str] = field(default_factory=list)  # 追问问题
    related_dimensions: List[str] = field(default_factory=list)   # 相关维度

class SixDimensionDialogueSystem:
    """
    六维框架对话系统
    基于案例库的智能对话引导
    """
    
    def __init__(self):
        self.templates: Dict[str, List[DialogueTemplate]] = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载对话模板"""
        # 基础信息类
        self.templates["basic_info"] = [
            DialogueTemplate(
                category=QuestionCategory.BASIC_INFO,
                question_pattern="不知道出生时辰",
                style=DialogueStyle.ZHOU_YU,
                response="没事，时辰不知道，咱们先按子时看个大概。等您以后找到准确时辰再校正，不影响大局。您最关心哪方面？财运、事业、姻缘，还是直接问买房适合哪座城市？",
                follow_up_questions=[
                    "您最想了解的是哪个方面？",
                    "您最近有什么特别想解决的事吗？"
                ],
                related_dimensions=["格局"]
            ),
            DialogueTemplate(
                category=QuestionCategory.BASIC_INFO,
                question_pattern="只知道生日",
                style=DialogueStyle.ZHOU_YU,
                response="能，时辰影响细节，但大方向还是准的。咱们先按子时走，以后您找到时辰了，再校正。您先说说您最想通过命盘了解什么？",
                follow_up_questions=[
                    "您最近在纠结什么事？",
                    "有没有什么一直想问但没问出口的问题？"
                ],
                related_dimensions=["格局"]
            ),
            DialogueTemplate(
                category=QuestionCategory.BASIC_INFO,
                question_pattern="五行缺",
                style=DialogueStyle.ZHOU_YU,
                response="缺{element}往{direction}走确实顺。但{direction}城市那么多，具体选哪个，还要看您的事业属性和生活偏好。您是想去{direction}发展，还是已经有心仪的城市了？",
                follow_up_questions=[
                    "您对哪个城市比较感兴趣？",
                    "您现在做什么工作？"
                ],
                related_dimensions=["格局", "财运"]
            ),
        ]
        
        # 财运类
        self.templates["wealth"] = [
            DialogueTemplate(
                category=QuestionCategory.WEALTH,
                question_pattern="什么时候能发财",
                style=DialogueStyle.ZHOU_YU,
                response="您先告诉我，您觉得自己是'正财'型还是'偏财'型？正财是稳扎稳打，偏财是机会型。很多人问发财，其实是想知道自己该走哪条路。您平时赚钱，是靠工资多，还是靠投资、副业多？",
                follow_up_questions=[
                    "您现在的收入结构是怎样的？",
                    "您觉得自己的优势是什么？"
                ],
                related_dimensions=["财运", "事业"]
            ),
            DialogueTemplate(
                category=QuestionCategory.WEALTH,
                question_pattern="适合炒股|投资",
                style=DialogueStyle.LU_XUN,
                response="从您命盘看，正财星旺，偏财星弱，炒股这类投机不太适合您。如果您想投资，建议选稳健型的，比如基金定投、买核心地段房产。您目前有在关注什么投资渠道吗？",
                follow_up_questions=[
                    "您能承受多大的风险？",
                    "您的投资期限是多久？"
                ],
                related_dimensions=["财运", "事业"]
            ),
            DialogueTemplate(
                category=QuestionCategory.WEALTH,
                question_pattern="存不住钱",
                style=DialogueStyle.LU_XUN,
                response="财星旺不代表能存住钱，还要看有没有库。就像水龙头大，但没池子，水就流走了。您现在花钱的主要地方是什么？是投资、消费，还是人情？",
                follow_up_questions=[
                    "您每月最大的开支是什么？",
                    "您有没有记账的习惯？"
                ],
                related_dimensions=["财运", "执行力"]
            ),
        ]
        
        # 事业类
        self.templates["career"] = [
            DialogueTemplate(
                category=QuestionCategory.CAREER,
                question_pattern="换工作|跳槽",
                style=DialogueStyle.LU_XUN,
                response="换不换，看您现在卡在哪儿。是钱少、没发展、还是人际关系？还有，您现在多大？30岁前可以试错，30岁后要选赛道。您方便说说现在的情况吗？",
                follow_up_questions=[
                    "您现在工作多久了？",
                    "您最不满意现在工作的哪一点？"
                ],
                related_dimensions=["事业", "财运"]
            ),
            DialogueTemplate(
                category=QuestionCategory.CAREER,
                question_pattern="适合什么行业",
                style=DialogueStyle.ZHOU_YU,
                response="您命盘里有文昌文曲，适合知识、沟通、文化类行业；有武曲，适合金融、技术、管理类。您平时对什么领域感兴趣？或者您现在做什么工作？",
                follow_up_questions=[
                    "您平时最擅长什么？",
                    "您有没有想尝试的新方向？"
                ],
                related_dimensions=["事业", "格局"]
            ),
            DialogueTemplate(
                category=QuestionCategory.CAREER,
                question_pattern="创业",
                style=DialogueStyle.ZHOU_YU,
                response="创业要看时机、资源、心态。从盘里看，您有{traits}。但创业最怕的是'想太多做太少'。您目前有没有看好的方向？或者已经试过什么项目？",
                follow_up_questions=[
                    "您创业的启动资金有多少？",
                    "您有合伙人吗？"
                ],
                related_dimensions=["事业", "财运", "执行力"]
            ),
        ]
        
        # 姻缘类
        self.templates["marriage"] = [
            DialogueTemplate(
                category=QuestionCategory.MARRIAGE,
                question_pattern="遇不到对的人|单身",
                style=DialogueStyle.ZHOU_YU,
                response="您先别急。姻缘不是找对的人，而是您到了哪个段位，自然遇到哪个段位的人。您现在的生活圈、收入、心态，大概在什么水平？",
                follow_up_questions=[
                    "您平时的社交圈是怎样的？",
                    "您对另一半有什么期待？"
                ],
                related_dimensions=["姻缘", "人际"]
            ),
            DialogueTemplate(
                category=QuestionCategory.MARRIAGE,
                question_pattern="夫妻宫有煞|婚姻不顺",
                style=DialogueStyle.LU_XUN,
                response="有煞星不代表一定不顺，只是提醒您要多留个心眼，别被表面现象迷惑。您现在单身还是有伴侣？方便聊聊您的感情经历吗？",
                follow_up_questions=[
                    "您之前的感情经历是怎样的？",
                    "您觉得感情中最大的问题是什么？"
                ],
                related_dimensions=["姻缘", "人际"]
            ),
            DialogueTemplate(
                category=QuestionCategory.MARRIAGE,
                question_pattern="正缘|对的人",
                style=DialogueStyle.LU_XUN,
                response="您先别急着下'算不算正缘'这个结论。正缘不是一道判断题，而是一段过程。命盘里看两个人合不合，要看生肖、八字、日柱、流年，还要看两个人的心。您愿意说说您现在的情况吗？",
                follow_up_questions=[
                    "您们在一起多久了？",
                    "您觉得对方最吸引您的是什么？"
                ],
                related_dimensions=["姻缘", "人际"]
            ),
        ]
        
        # 城市选择类
        self.templates["city_choice"] = [
            DialogueTemplate(
                category=QuestionCategory.CITY_CHOICE,
                question_pattern="适合哪个城市",
                style=DialogueStyle.LU_XUN,
                response="这要看您的命盘方位和事业属性。您五行属{element}，往{direction}方向更顺。您心里有没有想去的城市？比如杭州、苏州、上海、广州？",
                follow_up_questions=[
                    "您对哪个城市比较感兴趣？",
                    "您现在做什么工作？"
                ],
                related_dimensions=["格局", "事业"]
            ),
            DialogueTemplate(
                category=QuestionCategory.CITY_CHOICE,
                question_pattern="老家还是大城市",
                style=DialogueStyle.ZHOU_YU,
                response="您命盘里迁移宫有吉星，适合外出闯荡；如果有擎羊、陀罗，可能更适合在熟悉的地方扎根。您现在的行业，在大城市机会多吗？",
                follow_up_questions=[
                    "您老家有什么发展机会？",
                    "您在大城市有亲友吗？"
                ],
                related_dimensions=["事业", "人际"]
            ),
        ]
        
        # 买房时机类
        self.templates["buy_timing"] = [
            DialogueTemplate(
                category=QuestionCategory.BUY_TIMING,
                question_pattern="现在买房合适吗",
                style=DialogueStyle.LU_XUN,
                response="市场有波动，但您买房是自住还是投资？自住的话，只要您觉得安定下来了，就合适。投资的话，要看时机。您方便说说您现在的现金流情况吗？",
                follow_up_questions=[
                    "您买房的目的是什么？",
                    "您首付准备好了吗？"
                ],
                related_dimensions=["财运", "事业"]
            ),
            DialogueTemplate(
                category=QuestionCategory.BUY_TIMING,
                question_pattern="房价在跌|观望",
                style=DialogueStyle.LU_XUN,
                response="如果您是刚需，不用太纠结短期涨跌。如果您是改善或投资，可以观望。您现在的住房情况怎么样？",
                follow_up_questions=[
                    "您是首套还是改善？",
                    "您计划持有多久？"
                ],
                related_dimensions=["财运"]
            ),
        ]
        
        # 综合决策类
        self.templates["combined"] = [
            DialogueTemplate(
                category=QuestionCategory.COMBINED,
                question_pattern="命盘.*买房|买房.*命盘",
                style=DialogueStyle.LU_XUN,
                response="没问题，咱们一步到位。您先告诉我您的出生年月日时，还有您现在的城市和预算。我帮您先看命盘，再挑城市，最后筛房源。",
                follow_up_questions=[
                    "您的出生信息是？",
                    "您的预算大概多少？"
                ],
                related_dimensions=["格局", "财运", "事业"]
            ),
            DialogueTemplate(
                category=QuestionCategory.COMBINED,
                question_pattern="换城市.*换房|换房.*换城市",
                style=DialogueStyle.LU_XUN,
                response="这正是我们最擅长的。您把您现在的情况告诉我，比如您在哪里工作，大概收入，想往哪个方向走，还有您的出生年月。我帮您把命盘、城市、房子串起来看。",
                follow_up_questions=[
                    "您现在在哪个城市？",
                    "您想换城市的原因是什么？"
                ],
                related_dimensions=["格局", "事业", "财运"]
            ),
        ]
    
    def match_template(self, user_input: str) -> Optional[DialogueTemplate]:
        """
        匹配对话模板
        
        Args:
            user_input: 用户输入
        
        Returns:
            匹配的模板，如果没有匹配则返回None
        """
        user_input_lower = user_input.lower()
        
        for category, templates in self.templates.items():
            for template in templates:
                patterns = template.question_pattern.split("|")
                for pattern in patterns:
                    if pattern in user_input_lower:
                        return template
        
        return None
    
    def generate_response(
        self,
        user_input: str,
        user_context: Dict[str, Any] = None,
        style: DialogueStyle = None
    ) -> Dict[str, Any]:
        """
        生成回复
        
        Args:
            user_input: 用户输入
            user_context: 用户上下文（命盘信息、历史对话等）
            style: 指定回复风格
        
        Returns:
            包含回复、追问、相关维度的字典
        """
        template = self.match_template(user_input)
        
        if template:
            response = template.response
            
            # 填充模板变量
            if user_context:
                response = self._fill_template(response, user_context)
            
            # 随机选择一个追问
            follow_up = None
            if template.follow_up_questions:
                follow_up = random.choice(template.follow_up_questions)
            
            return {
                "response": response,
                "style": template.style.value,
                "follow_up": follow_up,
                "related_dimensions": template.related_dimensions,
                "category": template.category.value
            }
        
        # 没有匹配的模板，返回通用引导
        return self._generate_generic_response(user_input, style)
    
    def _fill_template(self, template: str, context: Dict[str, Any]) -> str:
        """填充模板变量"""
        # 简单的变量替换
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        return template
    
    def _generate_generic_response(
        self,
        user_input: str,
        style: DialogueStyle = None
    ) -> Dict[str, Any]:
        """生成通用回复"""
        if style == DialogueStyle.ZHOU_YU:
            response = "您的问题我收到了。咱们一步步来，先说说您现在最纠结的是什么？是事业、感情，还是买房换城市？"
        else:
            response = "我感受到了您话里的重量。您愿意说出来，已经是迈出的第一步。我们慢慢聊，不急。您先说说您最近在纠结什么？"
        
        return {
            "response": response,
            "style": style.value if style else DialogueStyle.LU_XUN.value,
            "follow_up": "您最想解决的是什么问题？",
            "related_dimensions": ["格局"],
            "category": "general"
        }
    
    def get_six_dimension_questions(self, dimension: str) -> List[str]:
        """
        获取六维框架的引导问题
        
        Args:
            dimension: 维度名称
        
        Returns:
            该维度的引导问题列表
        """
        questions = {
            "格局": [
                "您觉得自己最大的优势是什么？",
                "您平时最擅长做什么事？",
                "您有没有什么事是一做就很顺的？"
            ],
            "财运": [
                "您现在的收入主要来源是什么？",
                "您花钱的习惯是怎样的？",
                "您有没有投资或副业？"
            ],
            "姻缘": [
                "您现在的感情状态是怎样的？",
                "您对另一半有什么期待？",
                "您之前的感情经历对您有什么影响？"
            ],
            "事业": [
                "您现在的工作满意吗？",
                "您未来三年想达到什么目标？",
                "您觉得自己的职业发展空间大吗？"
            ],
            "人际": [
                "您身边有没有特别支持您的人？",
                "您平时跟朋友相处是怎样的模式？",
                "您觉得自己的社交圈怎么样？"
            ],
            "执行力": [
                "您平时做决定快吗？",
                "您有没有想了很多但一直没行动的事？",
                "您觉得自己的行动力怎么样？"
            ]
        }
        
        return questions.get(dimension, [])


# 全局对话系统实例
dialogue_system = SixDimensionDialogueSystem()
