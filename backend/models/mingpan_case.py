"""
命盘案例库数据模型
基于六维思维框架的结构化存储
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class PatternType(str, Enum):
    """格局类型"""
    FENG_YI = "凤仪型"
    SHE_LING = "蛇灵型"
    HE_XIAN = "鹤贤型"
    LONG_ZUN = "龙尊型"
    MIXED = "混合型"


class WealthType(str, Enum):
    """财运类型"""
    ZHENG_CAI = "正财型"
    PIAN_CAI = "偏财型"
    MIXED = "正偏兼有"


class MarriageLevel(str, Enum):
    """婚恋段位"""
    HIGH = "高段位"
    MEDIUM = "中段位"
    LOW = "低段位"


class CareerStage(str, Enum):
    """事业阶段"""
    BEFORE_30 = "30岁前-试错期"
    AFTER_30 = "30岁后-扎根期"
    AFTER_40 = "40岁后-做局期"


class RelationType(str, Enum):
    """人际关系类型"""
    NOURISHING = "滋养型"
    CONSUMING = "消耗型"
    NEUTRAL = "中性"


class ExecutionLevel(str, Enum):
    """执行力等级"""
    STRONG = "强"
    MEDIUM = "中"
    WEAK = "弱"


class CaseBase(BaseModel):
    """案例基础模型"""
    case_id: str = Field(default_factory=lambda: f"CASE-{uuid.uuid4().hex[:8].upper()}")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    anonymized_name: str = Field(..., description="匿名化姓名，如'县城姑娘A'")
    gender: str = Field(..., description="性别")
    birth_year: int = Field(..., description="出生年份")
    birth_place: str = Field(..., description="出生地")
    current_location: str = Field(..., description="现居地")
    
    background: str = Field(..., description="背景故事，老骇风格叙述")
    key_events: List[str] = Field(default_factory=list, description="关键事件节点")


class DimensionAnalysis(BaseModel):
    """六维分析模型"""
    
    dimension_1_pattern: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": None,
            "description": "",
            "evidence": [],
            "blockage": None,
            "suggestion": ""
        },
        description="第一维度：格局定基调"
    )
    
    dimension_2_wealth: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": None,
            "description": "",
            "income_source": "",
            "wealth_timeline": [],
            "warning": ""
        },
        description="第二维度：财运通道"
    )
    
    dimension_3_marriage: Dict[str, Any] = Field(
        default_factory=lambda: {
            "level": None,
            "self_positioning": "",
            "partner_expectation": "",
            "gap_analysis": "",
            "suggestion": ""
        },
        description="第三维度：姻缘逻辑"
    )
    
    dimension_4_career: Dict[str, Any] = Field(
        default_factory=lambda: {
            "stage": None,
            "current_industry": "",
            "industry_changes": [],
            "node_analysis": "",
            "next_step": ""
        },
        description="第四维度：事业路径"
    )
    
    dimension_5_relations: Dict[str, Any] = Field(
        default_factory=lambda: {
            "family_type": None,
            "key_relations": [],
            "energy_drains": [],
            "protection_strategy": ""
        },
        description="第五维度：人际过滤"
    )
    
    dimension_6_execution: Dict[str, Any] = Field(
        default_factory=lambda: {
            "level": None,
            "mindset": "",
            "circle_quality": "",
            "realization_rate": 0.0,
            "blockage": ""
        },
        description="第六维度：执行力心态"
    )


class CaseOutcome(BaseModel):
    """案例结果模型"""
    status: str = Field(..., description="当前状态：破局中/已破局/困局中")
    key_turning_point: str = Field(..., description="关键转折点")
    lessons_learned: List[str] = Field(default_factory=list, description="经验教训")
    verification_years: int = Field(default=0, description="验证年数")
    outcome_rating: int = Field(default=0, ge=0, le=100, description="结果评分0-100")


class CaseFull(CaseBase):
    """完整案例模型"""
    dimension_analysis: DimensionAnalysis = Field(default_factory=DimensionAnalysis)
    outcome: Optional[CaseOutcome] = None
    laohai_comment: str = Field(default="", description="老骇点评")
    tags: List[str] = Field(default_factory=list, description="标签")


class CaseCreateRequest(BaseModel):
    """案例创建请求"""
    anonymized_name: str
    gender: str
    birth_year: int
    birth_place: str
    current_location: str
    background: str
    key_events: List[str] = []
    dimension_analysis: Optional[DimensionAnalysis] = None
    tags: List[str] = []


class CaseSearchRequest(BaseModel):
    """案例搜索请求"""
    pattern_type: Optional[PatternType] = None
    wealth_type: Optional[WealthType] = None
    marriage_level: Optional[MarriageLevel] = None
    career_stage: Optional[CareerStage] = None
    relation_type: Optional[RelationType] = None
    execution_level: Optional[ExecutionLevel] = None
    gender: Optional[str] = None
    age_range: Optional[tuple] = None
    keyword: Optional[str] = None
    tags: List[str] = []


class CaseStatistics(BaseModel):
    """案例统计模型"""
    total_cases: int = 0
    pattern_distribution: Dict[str, int] = Field(default_factory=dict)
    wealth_distribution: Dict[str, int] = Field(default_factory=dict)
    execution_success_rate: Dict[str, float] = Field(default_factory=dict)
    common_blockages: List[Dict[str, Any]] = Field(default_factory=list)
    breakthrough_patterns: List[Dict[str, Any]] = Field(default_factory=list)


CASE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS mingpan_cases (
    case_id VARCHAR(20) PRIMARY KEY,
    anonymized_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    birth_year INTEGER NOT NULL,
    birth_place VARCHAR(100) NOT NULL,
    current_location VARCHAR(100) NOT NULL,
    background TEXT NOT NULL,
    key_events JSONB DEFAULT '[]',
    
    dimension_1_pattern JSONB DEFAULT '{}',
    dimension_2_wealth JSONB DEFAULT '{}',
    dimension_3_marriage JSONB DEFAULT '{}',
    dimension_4_career JSONB DEFAULT '{}',
    dimension_5_relations JSONB DEFAULT '{}',
    dimension_6_execution JSONB DEFAULT '{}',
    
    outcome_status VARCHAR(50),
    outcome_turning_point TEXT,
    outcome_lessons JSONB DEFAULT '[]',
    outcome_verification_years INTEGER DEFAULT 0,
    outcome_rating INTEGER DEFAULT 0,
    
    laohai_comment TEXT DEFAULT '',
    tags JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pattern_type ON mingpan_cases ((dimension_1_pattern->>'type'));
CREATE INDEX IF NOT EXISTS idx_wealth_type ON mingpan_cases ((dimension_2_wealth->>'type'));
CREATE INDEX IF NOT EXISTS idx_execution_level ON mingpan_cases ((dimension_6_execution->>'level'));
CREATE INDEX IF NOT EXISTS idx_gender ON mingpan_cases (gender);
CREATE INDEX IF NOT EXISTS idx_birth_year ON mingpan_cases (birth_year);
CREATE INDEX IF NOT EXISTS idx_outcome_status ON mingpan_cases (outcome_status);
CREATE INDEX IF NOT EXISTS idx_tags ON mingpan_cases USING GIN (tags);
"""


SAMPLE_CASES = [
    {
        "case_id": "CASE-FY0001",
        "anonymized_name": "县城姑娘A",
        "gender": "女",
        "birth_year": 1988,
        "birth_place": "湖南某县城",
        "current_location": "上海",
        "background": "这姑娘命盘一看就是凤仪型，天生会笼络人。但问题是她一开始蹲在县城，那点笼络能力只能用在家长里短上。后来她做了个决定——去上海。先打工、学技能、进圈子，三年后嫁了个金融精英。不是她运气好，是她先把局做大了。",
        "key_events": ["2012年决定去上海", "2015年进入高端社交圈", "2018年结婚"],
        "dimension_1_pattern": {
            "type": "凤仪型",
            "description": "天生会搞关系、会整合资源",
            "evidence": ["善于与人打交道", "能借力成事"],
            "blockage": "初期困在小地方，天赋无用武之地",
            "suggestion": "需要更大的舞台"
        },
        "dimension_2_wealth": {
            "type": "偏财型",
            "description": "靠圈子、靠机会",
            "income_source": "资源整合、人脉变现",
            "wealth_timeline": ["2015年开始积累人脉", "2018年后财富快速增长"],
            "warning": "需要持续维护人脉网络"
        },
        "dimension_3_marriage": {
            "level": "高段位",
            "self_positioning": "主动提升自己到更高圈层",
            "partner_expectation": "匹配自己提升后的段位",
            "gap_analysis": "通过自我提升消除了差距",
            "suggestion": "继续保持圈层优势"
        },
        "dimension_4_career": {
            "stage": "30岁后-扎根期",
            "current_industry": "社交资源整合",
            "industry_changes": ["县城→上海"],
            "node_analysis": "每次跳都是往更高阶圈子走",
            "next_step": "巩固现有资源，拓展新圈层"
        },
        "dimension_5_relations": {
            "family_type": "消耗型",
            "key_relations": [{"relation": "亲戚", "type": "消耗型", "impact": "初期阻碍"}],
            "energy_drains": ["老家亲戚的非议"],
            "protection_strategy": "不解释、不争辩、给钱、走人"
        },
        "dimension_6_execution": {
            "level": "强",
            "mindset": "目标清晰，行动果断",
            "circle_quality": "高质量",
            "realization_rate": 0.85,
            "blockage": "无"
        },
        "outcome_status": "已破局",
        "outcome_turning_point": "2012年决定离开县城去上海",
        "outcome_lessons": ["天赋需要舞台", "自我提升是改变命运的关键"],
        "outcome_verification_years": 10,
        "outcome_rating": 90,
        "laohai_comment": "这案例我看了很多遍。凤仪型的人，给她舞台她就能飞。但关键是——她自己先动起来了。很多人命盘不差，就是不动。命盘是地图，你得自己走。",
        "tags": ["凤仪型", "偏财", "高段位", "破局成功", "女性", "县城逆袭"]
    },
    {
        "case_id": "CASE-SL0002",
        "anonymized_name": "创业老板B",
        "gender": "男",
        "birth_year": 1985,
        "birth_place": "浙江某镇",
        "current_location": "杭州",
        "background": "蛇灵型的典型代表。前两次创业做啥赔啥，第三次踩准风口，三年翻盘。他不是运气好，是他一直趴在那个行业里，没换过。蛇灵型的人，耐得住寂寞，等得起机会。",
        "key_events": ["2010年第一次创业失败", "2014年第二次创业失败", "2017年第三次创业成功", "2020年公司估值过亿"],
        "dimension_1_pattern": {
            "type": "蛇灵型",
            "description": "耐得住寂寞，等得起机会",
            "evidence": ["连续创业不放弃", "深耕一个行业"],
            "blockage": "需要时间积累",
            "suggestion": "保持耐心，等待风口"
        },
        "dimension_2_wealth": {
            "type": "偏财型",
            "description": "靠机会、靠时机",
            "income_source": "创业收益",
            "wealth_timeline": ["2017年前持续亏损", "2017年后爆发式增长"],
            "warning": "风口来之前要有足够积累"
        },
        "dimension_3_marriage": {
            "level": "中段位",
            "self_positioning": "事业优先",
            "partner_expectation": "能理解创业艰辛",
            "gap_analysis": "创业初期因经济压力导致感情问题",
            "suggestion": "成功后需要重新平衡家庭"
        },
        "dimension_4_career": {
            "stage": "30岁后-扎根期",
            "current_industry": "电商",
            "industry_changes": ["传统零售→电商"],
            "node_analysis": "每次失败都在积累经验，第三次踩准节点",
            "next_step": "从做事转向做局"
        },
        "dimension_5_relations": {
            "family_type": "滋养型",
            "key_relations": [{"relation": "妻子", "type": "滋养型", "impact": "初期支持"}],
            "energy_drains": [],
            "protection_strategy": "成功后回馈家人"
        },
        "dimension_6_execution": {
            "level": "强",
            "mindset": "不怕失败，持续迭代",
            "circle_quality": "中等",
            "realization_rate": 0.80,
            "blockage": "初期资金不足"
        },
        "outcome_status": "已破局",
        "outcome_turning_point": "2017年第三次创业踩准风口",
        "outcome_lessons": ["蛇灵型需要时间", "深耕比频繁换赛道更重要"],
        "outcome_verification_years": 8,
        "outcome_rating": 85,
        "laohai_comment": "蛇灵型的人，最怕的就是耐不住。这哥们儿厉害在——他趴在行业里没动过。很多人创业失败一次就换赛道，结果永远在起跑线上。蛇灵型的命，就是要等，但要边等边积累。",
        "tags": ["蛇灵型", "偏财", "创业", "破局成功", "男性", "多次失败后成功"]
    },
    {
        "case_id": "CASE-HX0003",
        "anonymized_name": "基层医生C",
        "gender": "男",
        "birth_year": 1975,
        "birth_place": "山东某县",
        "current_location": "山东某市",
        "background": "鹤贤型的典型。从基层医生熬到院长，靠的是二十年不挪窝，把专业做透了。鹤贤型的人，看上去慢，但每一步都扎实。他们不追风口，风口追他们。",
        "key_events": ["1998年入职基层医院", "2008年成为科室主任", "2018年升任副院长", "2023年升任院长"],
        "dimension_1_pattern": {
            "type": "鹤贤型",
            "description": "稳扎稳打，靠手艺吃饭",
            "evidence": ["二十年不换赛道", "专业能力持续提升"],
            "blockage": "需要时间积累",
            "suggestion": "保持耐心，专业为王"
        },
        "dimension_2_wealth": {
            "type": "正财型",
            "description": "靠本事、靠时间、靠积累",
            "income_source": "工资、职称晋升",
            "wealth_timeline": ["收入逐年稳步增长"],
            "warning": "来得慢但稳"
        },
        "dimension_3_marriage": {
            "level": "中段位",
            "self_positioning": "稳定可靠",
            "partner_expectation": "匹配的稳定生活",
            "gap_analysis": "无显著差距",
            "suggestion": "保持现有节奏"
        },
        "dimension_4_career": {
            "stage": "40岁后-做局期",
            "current_industry": "医疗",
            "industry_changes": [],
            "node_analysis": "每个阶段都踩准了晋升节点",
            "next_step": "培养接班人，建立影响力"
        },
        "dimension_5_relations": {
            "family_type": "滋养型",
            "key_relations": [{"relation": "妻子", "type": "滋养型", "impact": "稳定后方"}],
            "energy_drains": [],
            "protection_strategy": "维护家庭稳定"
        },
        "dimension_6_execution": {
            "level": "强",
            "mindset": "长期主义，不急不躁",
            "circle_quality": "中等",
            "realization_rate": 0.90,
            "blockage": "无"
        },
        "outcome_status": "已破局",
        "outcome_turning_point": "坚持不换赛道，持续积累",
        "outcome_lessons": ["鹤贤型不需要追风口", "时间是最好的朋友"],
        "outcome_verification_years": 25,
        "outcome_rating": 88,
        "laohai_comment": "这案例我常拿来给年轻人看。很多人嫌慢，想走捷径。但鹤贤型的命，就是要熬。你让他去创业、去投机，反而会摔。认清楚自己是哪块料，比什么都重要。",
        "tags": ["鹤贤型", "正财", "体制内", "破局成功", "男性", "长期主义"]
    },
    {
        "case_id": "CASE-LZ0004",
        "anonymized_name": "企业家D",
        "gender": "男",
        "birth_year": 1980,
        "birth_place": "广东某村",
        "current_location": "深圳",
        "background": "龙尊型的代表。小混混出身最后做企业家，他不懂财务，但身边永远有人帮他跑腿。龙尊型的天赋不是做生意，是让人愿意跟着他。",
        "key_events": ["1998年混社会", "2005年开始做小生意", "2010年组建团队", "2018年公司上市"],
        "dimension_1_pattern": {
            "type": "龙尊型",
            "description": "天生有号召力，能让别人跟着干",
            "evidence": ["从小弟到老板", "团队忠诚度高"],
            "blockage": "初期缺乏正规教育",
            "suggestion": "找专业人才补短板"
        },
        "dimension_2_wealth": {
            "type": "偏财型",
            "description": "靠人脉、靠团队",
            "income_source": "企业经营",
            "wealth_timeline": ["2010年后快速增长"],
            "warning": "需要持续维护团队忠诚度"
        },
        "dimension_3_marriage": {
            "level": "中段位",
            "self_positioning": "事业为重",
            "partner_expectation": "能接受他的过去",
            "gap_analysis": "成功后择偶标准提升",
            "suggestion": "选择能理解他背景的伴侣"
        },
        "dimension_4_career": {
            "stage": "40岁后-做局期",
            "current_industry": "制造业",
            "industry_changes": ["混社会→小生意→企业"],
            "node_analysis": "每次转型都有贵人相助",
            "next_step": "培养接班人，考虑传承"
        },
        "dimension_5_relations": {
            "family_type": "混合型",
            "key_relations": [
                {"relation": "早期兄弟", "type": "滋养型", "impact": "创业支持"},
                {"relation": "部分亲戚", "type": "消耗型", "impact": "借钱不还"}
            ],
            "energy_drains": ["部分远亲的索取"],
            "protection_strategy": "设立边界，选择性帮助"
        },
        "dimension_6_execution": {
            "level": "强",
            "mindset": "敢想敢干，善于用人",
            "circle_quality": "高质量",
            "realization_rate": 0.85,
            "blockage": "无"
        },
        "outcome_status": "已破局",
        "outcome_turning_point": "2010年组建核心团队",
        "outcome_lessons": ["龙尊型要会用人才", "出身不重要，重要的是谁跟你"],
        "outcome_verification_years": 15,
        "outcome_rating": 92,
        "laohai_comment": "龙尊型的人，天生就是当老大的料。但他厉害的地方是——知道自己不懂财务，就找懂的人。很多人创业失败，就是因为什么都要自己抓。龙尊型的命，核心是'用人'，不是'做事'。",
        "tags": ["龙尊型", "偏财", "创业", "破局成功", "男性", "底层逆袭"]
    },
    {
        "case_id": "CASE-WARN01",
        "anonymized_name": "体制内炒股E",
        "gender": "男",
        "birth_year": 1982,
        "birth_place": "江苏某市",
        "current_location": "江苏某市",
        "background": "典型的反面案例。正财型的命，天天想赚偏财的钱。体制内工作稳定，但非要跑去炒股，把家底赔光。错把欲望当天赋。",
        "key_events": ["2005年进入体制", "2015年开始炒股", "2018年亏损严重", "2020年离婚"],
        "dimension_1_pattern": {
            "type": "鹤贤型",
            "description": "本适合稳扎稳打",
            "evidence": ["体制内工作稳定"],
            "blockage": "欲望与天赋错位",
            "suggestion": "回归正财路线"
        },
        "dimension_2_wealth": {
            "type": "正财型",
            "description": "本应靠积累",
            "income_source": "工资",
            "wealth_timeline": ["本应稳步增长"],
            "warning": "正财命想赚偏财钱，必翻车"
        },
        "dimension_3_marriage": {
            "level": "低段位",
            "self_positioning": "高估自己能力",
            "partner_expectation": "稳定生活",
            "gap_analysis": "因炒股亏损导致家庭破裂",
            "suggestion": "先修复财务，再考虑感情"
        },
        "dimension_4_career": {
            "stage": "30岁后-扎根期",
            "current_industry": "体制内",
            "industry_changes": [],
            "node_analysis": "本应稳步晋升，被炒股打乱",
            "next_step": "回归主业，止损"
        },
        "dimension_5_relations": {
            "family_type": "消耗型",
            "key_relations": [{"relation": "前妻", "type": "消耗型", "impact": "离婚"}],
            "energy_drains": ["财务压力", "家庭破裂"],
            "protection_strategy": "先稳定自己"
        },
        "dimension_6_execution": {
            "level": "弱",
            "mindset": "贪婪，缺乏自知",
            "circle_quality": "低质量",
            "realization_rate": 0.20,
            "blockage": "欲望蒙蔽判断"
        },
        "outcome_status": "困局中",
        "outcome_turning_point": "2015年开始炒股",
        "outcome_lessons": ["认清自己的财运类型", "不要用正财的命去赌偏财"],
        "outcome_verification_years": 8,
        "outcome_rating": 20,
        "laohai_comment": "这案例我每次讲都有人点头。正财的命，就老老实实积累。你让他去炒股、去投机，就是送钱。不是他不够聪明，是他根本不是那块料。认清自己，比什么都重要。",
        "tags": ["鹤贤型", "正财", "反面案例", "困局中", "男性", "炒股亏损"]
    }
]
