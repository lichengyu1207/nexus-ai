"""
咨询顾问代理
负责自然语言理解、对话管理、调用其他代理
"""
import json
import re
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from ..agents.collector import CollectorAgent
    from ..agents.analyst import AnalystAgent
    from ..agents.report_agent import ReportAgent
    from ..agents.bus import MessageBus
    from ..agents.message import AgentMessage, MessageType
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    logger.warning("Agent system not available, using standalone mode")


class NLUResult:
    """NLU分析结果"""
    def __init__(self, intent: str = None, entities: Dict = None, 
                 profile_updates: Dict = None, missing_fields: List = None,
                 confidence: float = 0.0):
        self.intent = intent or 'other'
        self.entities = entities or {}
        self.profile_updates = profile_updates or {}
        self.missing_fields = missing_fields or []
        self.confidence = confidence


class NLUEngine:
    """自然语言理解引擎"""
    
    INTENT_KEYWORDS = {
        'house_recommendation': ['推荐', '买房', '购房', '想买', '求推荐', '有什么好', '选房', '看房'],
        'area_info': ['区域', '小区', '地段', '哪里', '哪个区', '周边', '配套', '环境'],
        'policy': ['政策', '限购', '贷款', '首付', '利率', '公积金', '税费', '落户'],
        'price_inquiry': ['房价', '价格', '多少钱', '均价', '涨跌', '走势'],
        'loan_calc': ['贷款', '月供', '还款', '利息', '能贷多少'],
        'investment': ['投资', '升值', '保值', '回报', '租金'],
    }
    
    ENTITY_PATTERNS = {
        'budget': r'(\d+)(万|w|W)',
        'income': r'(月薪|月收入|月入)(\d+)(万|k|K)?',
        'area': r'(\d+)平(米)?',
        'rooms': r'(\d)(室|居|房)',
        'city': r'(深圳|广州|北京|上海|杭州|成都|武汉|南京|苏州|重庆|西安|长沙|郑州|东莞|佛山|珠海|惠州)',
    }
    
    DISTRICTS = {
        '深圳': ['南山', '福田', '罗湖', '宝安', '龙岗', '龙华', '坪山', '光明', '盐田', '大鹏'],
        '广州': ['天河', '越秀', '海珠', '荔湾', '白云', '黄埔', '番禺', '花都', '南沙', '增城', '从化'],
        '北京': ['朝阳', '海淀', '西城', '东城', '丰台', '石景山', '通州', '顺义', '昌平', '大兴', '房山'],
        '上海': ['浦东', '黄浦', '徐汇', '长宁', '静安', '普陀', '虹口', '杨浦', '闵行', '宝山', '嘉定'],
    }
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    async def analyze(self, message: str, history: List = None, profile: Dict = None) -> NLUResult:
        """
        分析用户消息，提取意图和实体
        优先使用规则引擎，复杂情况调用LLM
        """
        intent = self._classify_intent(message)
        entities = self._extract_entities(message)
        profile_updates = self._extract_profile_info(message, profile or {})
        
        if self.api_key and OPENAI_AVAILABLE:
            try:
                llm_result = await self._analyze_with_llm(message, history, profile)
                if llm_result.confidence > 0.7:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM分析失败，使用规则引擎: {e}")
        
        return NLUResult(
            intent=intent,
            entities=entities,
            profile_updates=profile_updates,
            confidence=0.8
        )
    
    def _classify_intent(self, message: str) -> str:
        """基于关键词的意图分类"""
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'other'
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, message)
            if matches:
                if entity_type == 'budget':
                    for match in matches:
                        amount = int(match[0])
                        entities['budget'] = amount * 10000
                        break
                elif entity_type == 'income':
                    for match in matches:
                        amount = int(match[1])
                        if match[2] in ['万', 'w', 'W']:
                            entities['monthly_income'] = amount * 10000
                        else:
                            entities['monthly_income'] = amount * 1000
                        break
                elif entity_type == 'area':
                    entities['house_area'] = int(matches[0][0])
                elif entity_type == 'rooms':
                    entities['rooms'] = int(matches[0][0])
                elif entity_type == 'city':
                    entities['city'] = matches[0]
        
        for city, districts in self.DISTRICTS.items():
            if city in message:
                entities['city'] = city
                for district in districts:
                    if district in message:
                        entities['district'] = district
                        break
        
        if '两居' in message or '两室' in message or '2室' in message:
            entities['rooms'] = 2
            entities['house_type'] = '两居室'
        elif '三居' in message or '三室' in message or '3室' in message:
            entities['rooms'] = 3
            entities['house_type'] = '三居室'
        elif '一居' in message or '一室' in message or '1室' in message:
            entities['rooms'] = 1
            entities['house_type'] = '一居室'
        
        return entities
    
    def _extract_profile_info(self, message: str, current_profile: Dict) -> Dict:
        """从消息中提取用户画像信息"""
        updates = {}
        
        age_patterns = [
            r'我(\d+)岁',
            r'今年(\d+)',
            r'(\d+)岁了',
        ]
        for pattern in age_patterns:
            match = re.search(pattern, message)
            if match:
                updates['age'] = int(match.group(1))
                break
        
        occupation_keywords = {
            '程序员': 'IT/互联网',
            '工程师': 'IT/互联网',
            '产品经理': 'IT/互联网',
            '教师': '教育',
            '老师': '教育',
            '医生': '医疗',
            '律师': '法律',
            '公务员': '政府/事业单位',
            '销售': '销售',
            '创业': '创业者',
        }
        for keyword, occupation in occupation_keywords.items():
            if keyword in message:
                updates['occupation'] = occupation
                break
        
        if '单身' in message:
            updates['family_structure'] = '单身'
        elif '结婚' in message or '夫妻' in message or '老婆' in message or '老公' in message:
            updates['family_structure'] = '夫妻'
            if '孩子' in message or '小孩' in message or '宝宝' in message:
                updates['family_structure'] = '有子女'
                updates['has_children'] = True
        
        if '首套' in message or '第一套' in message:
            updates['first_house'] = True
        
        return updates
    
    async def _analyze_with_llm(self, message: str, history: List, profile: Dict) -> NLUResult:
        """使用LLM进行深度分析"""
        if not self.api_key:
            return NLUResult()
        
        history_text = ""
        if history:
            history_text = "\n".join([
                f"{'用户' if h['role'] == 'user' else '助手'}: {h['content']}"
                for h in history[-5:]
            ])
        
        profile_text = json.dumps(profile, ensure_ascii=False) if profile else "暂无"
        
        prompt = f"""你是一个房产咨询助手的自然语言理解模块。请分析用户的消息，输出JSON格式的结果。

用户画像（已有信息）：
{profile_text}

对话历史：
{history_text}

用户当前消息：{message}

请提取并输出JSON：
{{
    "intent": "意图类型，可选值：house_recommendation(购房推荐)、area_info(区域信息)、policy(政策咨询)、price_inquiry(房价咨询)、loan_calc(贷款计算)、investment(投资咨询)、other",
    "entities": {{"city": "城市", "district": "区域", "budget": 预算数值, "rooms": 房间数, "house_type": "户型"}},
    "profile_updates": {{"age": 年龄, "occupation": "职业", "monthly_income": 月收入, "family_structure": "家庭结构"}},
    "missing_fields": ["缺少的关键字段列表"],
    "confidence": 0.0-1.0的置信度
}}

仅输出JSON，不要有其他解释。"""
        
        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return NLUResult(
                intent=result.get('intent', 'other'),
                entities=result.get('entities', {}),
                profile_updates=result.get('profile_updates', {}),
                missing_fields=result.get('missing_fields', []),
                confidence=result.get('confidence', 0.8)
            )
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return NLUResult()


class DialogueManager:
    """对话管理器 - 智能主动询问"""
    
    REQUIRED_FIELDS = {
        'house_recommendation': ['city', 'budget'],
        'area_info': ['city'],
        'policy': ['city'],
        'price_inquiry': ['city'],
        'loan_calc': ['budget'],
        'investment': ['city'],
    }
    
    QUESTION_TEMPLATES = {
        'city': [
            '请问您想了解哪个城市的房产信息？',
            '您考虑在哪个城市购房呢？',
            '您关注的城市是？比如深圳、广州、北京等。',
        ],
        'district': [
            '{city}的哪个区域您比较感兴趣？',
            '您想了解{city}哪个区的情况？',
        ],
        'budget': [
            '您的购房预算大概是多少？比如300万、500万？',
            '您计划花多少钱买房？',
            '预算范围是多少呢？这能帮我更精准地推荐。',
        ],
        'rooms': [
            '您需要几居室的房子？一居、两居还是三居？',
            '户型有什么要求吗？',
        ],
        'monthly_income': [
            '方便透露一下您的月收入吗？这有助于计算您的贷款能力。',
            '您的月收入大概是？我可以帮您算算月供。',
        ],
        'work_location': [
            '您在哪里工作？我可以帮您找通勤方便的小区。',
            '工作地点在哪个区域？',
        ],
    }
    
    def __init__(self):
        self.state = {
            'intent': None,
            'entities': {},
            'asked_fields': set(),
            'turn_count': 0
        }
    
    def update_state(self, intent: str, entities: Dict, profile: Dict):
        """更新对话状态"""
        self.state['intent'] = intent
        self.state['entities'].update(entities)
        self.state['turn_count'] += 1
        
        if profile:
            for field in ['city', 'budget_min', 'budget_max', 'monthly_income', 'work_city', 'work_district']:
                if profile.get(field) and field not in self.state['entities']:
                    if field == 'budget_max':
                        self.state['entities']['budget'] = profile[field]
                    else:
                        self.state['entities'][field] = profile[field]
    
    def get_missing_fields(self) -> List[str]:
        """获取缺少的关键字段"""
        intent = self.state['intent']
        if not intent or intent not in self.REQUIRED_FIELDS:
            return []
        
        required = self.REQUIRED_FIELDS[intent]
        missing = []
        
        for field in required:
            if field == 'budget':
                if not self.state['entities'].get('budget') and not self.state['entities'].get('budget_max'):
                    missing.append('budget')
            elif not self.state['entities'].get(field):
                missing.append(field)
        
        return [f for f in missing if f not in self.state['asked_fields']]
    
    def generate_question(self, missing_fields: List[str]) -> str:
        """生成智能追问"""
        if not missing_fields:
            return None
        
        field = missing_fields[0]
        self.state['asked_fields'].add(field)
        
        templates = self.QUESTION_TEMPLATES.get(field, ['您能提供更多信息吗？'])
        import random
        template = random.choice(templates)
        
        if '{city}' in template:
            city = self.state['entities'].get('city', '该城市')
            template = template.format(city=city)
        
        return template
    
    def should_ask_more(self) -> bool:
        """判断是否需要继续询问"""
        return self.state['turn_count'] < 5 and len(self.get_missing_fields()) > 0
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        return self.state.copy()


class ConsultantAgent:
    """咨询顾问代理"""
    
    CITY_DATA = {
        '深圳': {
            'avg_price': 65000,
            'districts': {
                '南山': {'avg_price': 95000, 'features': ['科技园', '深圳湾', '人才公园']},
                '福田': {'avg_price': 85000, 'features': ['CBD', '会展中心', '购物公园']},
                '罗湖': {'avg_price': 55000, 'features': ['老城区', '东门', '国贸']},
                '宝安': {'avg_price': 55000, 'features': ['机场', '会展', '新中心']},
                '龙岗': {'avg_price': 40000, 'features': ['大运', '坂田', '平湖']},
                '龙华': {'avg_price': 50000, 'features': ['红山', '深圳北', '龙华中心']},
            }
        },
        '广州': {
            'avg_price': 35000,
            'districts': {
                '天河': {'avg_price': 60000, 'features': ['珠江新城', '体育西', '岗顶']},
                '越秀': {'avg_price': 50000, 'features': ['老城区', '学区', '北京路']},
                '海珠': {'avg_price': 45000, 'features': ['琶洲', '广州塔', '江南西']},
            }
        },
        '北京': {
            'avg_price': 65000,
            'districts': {
                '朝阳': {'avg_price': 75000, 'features': ['CBD', '望京', '三里屯']},
                '海淀': {'avg_price': 85000, 'features': ['中关村', '五道口', '上地']},
                '西城': {'avg_price': 100000, 'features': ['金融街', '学区', '西单']},
            }
        },
        '上海': {
            'avg_price': 60000,
            'districts': {
                '浦东': {'avg_price': 65000, 'features': ['陆家嘴', '张江', '前滩']},
                '黄浦': {'avg_price': 100000, 'features': ['外滩', '南京路', '新天地']},
                '徐汇': {'avg_price': 80000, 'features': ['徐家汇', '衡山路', '漕河泾']},
            }
        }
    }
    
    def __init__(self):
        self.nlu_engine = NLUEngine()
        self.dialogue_manager = DialogueManager()
        self.bus = None
        self.collector = None
        self.analyst = None
        self.reporter = None
        
        if AGENTS_AVAILABLE:
            try:
                self.bus = MessageBus(task_id=f"consult-{str(uuid.uuid4())[:8]}")
                logger.info("Agent system initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize agent system: {e}")
    
    async def _call_collector_agent(self, entities: Dict) -> Dict:
        """调用数据采集代理获取房价数据"""
        if not AGENTS_AVAILABLE or not self.bus:
            return self._get_mock_price_data(entities)
        
        try:
            task_id = str(uuid.uuid4())
            collector = CollectorAgent("collector", task_id, self.bus)
            
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender="consultant",
                recipient="collector",
                type=MessageType.REQUEST,
                content={
                    "action": "collect",
                    "parsed": entities
                }
            )
            
            await collector.handle_message(message)
            return collector._last_response or self._get_mock_price_data(entities)
        except Exception as e:
            logger.error(f"Failed to call collector agent: {e}")
            return self._get_mock_price_data(entities)
    
    async def _call_analyst_agent(self, data: Dict, profile: Dict) -> Dict:
        """调用市场分析代理进行趋势分析"""
        if not AGENTS_AVAILABLE or not self.bus:
            return self._get_mock_analysis(data)
        
        try:
            task_id = str(uuid.uuid4())
            analyst = AnalystAgent("analyst", task_id, self.bus)
            
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender="consultant",
                recipient="analyst",
                type=MessageType.REQUEST,
                content={
                    "action": "analyze",
                    "data": data,
                    "profile": profile
                }
            )
            
            await analyst.handle_message(message)
            return analyst._last_response or self._get_mock_analysis(data)
        except Exception as e:
            logger.error(f"Failed to call analyst agent: {e}")
            return self._get_mock_analysis(data)
    
    async def _call_report_agent(self, analysis: Dict, session_id: str, user_id: str) -> Dict:
        """调用报告生成代理生成咨询报告"""
        if not AGENTS_AVAILABLE or not self.bus:
            return self._get_mock_report(analysis)
        
        try:
            task_id = str(uuid.uuid4())
            reporter = ReportAgent("reporter", task_id, self.bus, user_id=user_id)
            
            message = AgentMessage(
                id=str(uuid.uuid4()),
                sender="consultant",
                recipient="reporter",
                type=MessageType.REQUEST,
                content={
                    "action": "generate",
                    "analysis": analysis,
                    "session_id": session_id
                }
            )
            
            await reporter.handle_message(message)
            return reporter._last_response or self._get_mock_report(analysis)
        except Exception as e:
            logger.error(f"Failed to call report agent: {e}")
            return self._get_mock_report(analysis)
    
    def _get_mock_price_data(self, entities: Dict) -> Dict:
        """获取模拟房价数据"""
        city = entities.get('city', '深圳')
        return self.CITY_DATA.get(city, self.CITY_DATA['深圳'])
    
    def _get_mock_analysis(self, data: Dict) -> Dict:
        """获取模拟分析结果"""
        return {
            "trend": "stable",
            "recommendation": "建议关注核心区域",
            "risk_level": "medium"
        }
    
    def _get_mock_report(self, analysis: Dict) -> Dict:
        """获取模拟报告"""
        return {
            "summary": "咨询报告已生成",
            "recommendations": ["建议实地考察", "关注市场动态"]
        }
    
    async def process(self, user_message: str, session_id: str, user_id: str,
                      history: List = None, profile: Dict = None) -> Dict:
        """
        处理用户消息 - 智能对话流程
        返回: {reply, intent, entities, profile_updates, action}
        """
        nlu_result = await self.nlu_engine.analyze(
            message=user_message,
            history=history,
            profile=profile
        )
        
        self.dialogue_manager.update_state(
            intent=nlu_result.intent,
            entities=nlu_result.entities,
            profile=profile or {}
        )
        
        missing = self.dialogue_manager.get_missing_fields()
        if missing and self.dialogue_manager.should_ask_more():
            question = self.dialogue_manager.generate_question(missing)
            return {
                'reply': question,
                'intent': nlu_result.intent,
                'entities': nlu_result.entities,
                'profile_updates': nlu_result.profile_updates,
                'action': 'ask_more'
            }
        
        reply = await self._handle_intent(
            intent=nlu_result.intent,
            entities=self.dialogue_manager.state['entities'],
            profile=profile or {}
        )
        
        return {
            'reply': reply,
            'intent': nlu_result.intent,
            'entities': nlu_result.entities,
            'profile_updates': nlu_result.profile_updates,
            'action': 'done'
        }
    
    async def _handle_intent(self, intent: str, entities: Dict, profile: Dict) -> str:
        """根据意图生成回复"""
        handlers = {
            'house_recommendation': self._handle_recommendation,
            'area_info': self._handle_area_info,
            'policy': self._handle_policy,
            'price_inquiry': self._handle_price_inquiry,
            'loan_calc': self._handle_loan_calc,
            'investment': self._handle_investment,
        }
        
        handler = handlers.get(intent, self._handle_other)
        return await handler(entities, profile)
    
    async def _handle_recommendation(self, entities: Dict, profile: Dict) -> str:
        """处理购房推荐"""
        city = entities.get('city', '深圳')
        budget = entities.get('budget') or profile.get('budget_max')
        rooms = entities.get('rooms', 2)
        
        city_data = self.CITY_DATA.get(city, {})
        if not city_data:
            return f"抱歉，我暂时没有{city}的详细数据。您可以尝试询问深圳、广州、北京、上海等城市。"
        
        avg_price = city_data.get('avg_price', 50000)
        districts = city_data.get('districts', {})
        
        recommendations = []
        for district, data in districts.items():
            district_price = data.get('avg_price', avg_price)
            if budget:
                estimated_area = budget / district_price
                if estimated_area >= 50:
                    recommendations.append({
                        'district': district,
                        'avg_price': district_price,
                        'estimated_area': round(estimated_area),
                        'features': data.get('features', [])
                    })
            else:
                recommendations.append({
                    'district': district,
                    'avg_price': district_price,
                    'features': data.get('features', [])
                })
        
        if not recommendations:
            return f"根据您的预算，{city}目前可能较难找到合适的房源。建议您考虑：\n1. 适当增加预算\n2. 考虑周边城市\n3. 选择面积稍小的户型"
        
        recommendations.sort(key=lambda x: x.get('estimated_area', 0), reverse=True)
        top3 = recommendations[:3]
        
        reply = f"根据您的需求，为您推荐{city}以下区域：\n\n"
        for i, rec in enumerate(top3, 1):
            reply += f"**{i}. {rec['district']}**\n"
            reply += f"   - 均价：约{rec['avg_price']//10000}万/㎡\n"
            if rec.get('estimated_area'):
                reply += f"   - 预估面积：约{rec['estimated_area']}㎡\n"
            if rec.get('features'):
                reply += f"   - 特色：{', '.join(rec['features'])}\n"
            reply += "\n"
        
        reply += "💡 **温馨提示**：\n"
        reply += "- 以上为均价参考，具体房源价格会有浮动\n"
        reply += "- 建议实地看房，了解小区环境和配套\n"
        reply += "- 可点击下方按钮生成详细咨询报告"
        
        return reply
    
    async def _handle_area_info(self, entities: Dict, profile: Dict) -> str:
        """处理区域信息查询"""
        city = entities.get('city', '深圳')
        district = entities.get('district')
        
        city_data = self.CITY_DATA.get(city)
        if not city_data:
            return f"抱歉，我暂时没有{city}的详细数据。"
        
        if district:
            district_data = city_data['districts'].get(district)
            if district_data:
                reply = f"**{city}{district}区域信息**\n\n"
                reply += f"📍 均价：约{district_data['avg_price']//10000}万/㎡\n\n"
                reply += f"🌟 特色：\n"
                for feature in district_data.get('features', []):
                    reply += f"   - {feature}\n"
                return reply
        
        reply = f"**{city}各区域概览**\n\n"
        for d, data in city_data['districts'].items():
            reply += f"📍 **{d}**：均价约{data['avg_price']//10000}万/㎡\n"
            reply += f"   特色：{', '.join(data.get('features', []))}\n\n"
        
        return reply
    
    async def _handle_policy(self, entities: Dict, profile: Dict) -> str:
        """处理政策咨询"""
        city = entities.get('city', '深圳')
        
        policies = {
            '深圳': """
**深圳购房政策要点**：

📌 **限购政策**
- 深圳户籍：家庭限购2套，单身限购1套
- 非深户：需连续5年社保/个税，限购1套

📌 **首付比例**
- 首套房：30%
- 二套房：普通住宅50%，非普通住宅70%

📌 **贷款利率**
- 首套房：LPR-20BP（约3.95%）
- 二套房：LPR+60BP（约4.75%）

📌 **公积金贷款**
- 最高额度：个人50万，家庭90万
- 需连续缴存6个月以上

📌 **人才购房优惠**
- 高层次人才可申请购房补贴
- 部分区有人才房、安居房政策
""",
            '广州': """
**广州购房政策要点**：

📌 **限购政策**
- 广州户籍：家庭限购2套
- 非广州户籍：需连续5年社保/个税，限购1套

📌 **首付比例**
- 首套房：30%
- 二套房：50%

📌 **贷款利率**
- 首套房：约4.0%
- 二套房：约4.8%
""",
        }
        
        return policies.get(city, f"抱歉，我暂时没有{city}的详细政策信息。建议您咨询当地房管部门或专业中介。")
    
    async def _handle_price_inquiry(self, entities: Dict, profile: Dict) -> str:
        """处理房价咨询"""
        city = entities.get('city', '深圳')
        
        city_data = self.CITY_DATA.get(city)
        if not city_data:
            return f"抱歉，我暂时没有{city}的房价数据。"
        
        avg_price = city_data.get('avg_price', 0)
        
        reply = f"**{city}房价概览**\n\n"
        reply += f"📊 全市均价：约{avg_price//10000}万/㎡\n\n"
        reply += f"**各区房价排名**：\n"
        
        sorted_districts = sorted(
            city_data['districts'].items(),
            key=lambda x: x[1]['avg_price'],
            reverse=True
        )
        
        for i, (district, data) in enumerate(sorted_districts, 1):
            reply += f"{i}. {district}：{data['avg_price']//10000}万/㎡\n"
        
        reply += "\n📈 **趋势分析**：\n"
        reply += "- 近期市场整体趋于稳定\n"
        reply += "- 核心区域价格坚挺\n"
        reply += "- 外围区域有一定议价空间\n"
        
        return reply
    
    async def _handle_loan_calc(self, entities: Dict, profile: Dict) -> str:
        """处理贷款计算"""
        budget = entities.get('budget') or profile.get('budget_max', 3000000)
        income = entities.get('monthly_income') or profile.get('monthly_income', 20000)
        
        down_payment = budget * 0.3
        loan_amount = budget - down_payment
        
        annual_rate = 0.0395
        monthly_rate = annual_rate / 12
        months = 360
        
        monthly_payment = loan_amount * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
        
        total_payment = monthly_payment * months
        total_interest = total_payment - loan_amount
        
        affordable = monthly_payment < income * 0.5
        
        reply = f"**贷款计算结果**\n\n"
        reply += f"💰 **房屋总价**：{budget/10000:.0f}万\n"
        reply += f"💵 **首付（30%）**：{down_payment/10000:.0f}万\n"
        reply += f"🏦 **贷款金额**：{loan_amount/10000:.0f}万\n\n"
        reply += f"📅 **月供计算（30年等额本息）**：\n"
        reply += f"   - 月供：约{monthly_payment/10000:.2f}万（{monthly_payment:.0f}元）\n"
        reply += f"   - 总还款：{total_payment/10000:.0f}万\n"
        reply += f"   - 总利息：{total_interest/10000:.0f}万\n\n"
        
        if affordable:
            reply += f"✅ **评估结果**：月供占收入的{monthly_payment/income*100:.1f}%，在合理范围内（建议不超过50%）\n"
        else:
            reply += f"⚠️ **评估结果**：月供占收入的{monthly_payment/income*100:.1f}%，压力较大\n"
            reply += f"   建议：\n"
            reply += f"   - 增加首付比例\n"
            reply += f"   - 延长贷款年限\n"
            reply += f"   - 考虑降低购房预算\n"
        
        return reply
    
    async def _handle_investment(self, entities: Dict, profile: Dict) -> str:
        """处理投资咨询"""
        city = entities.get('city', '深圳')
        budget = entities.get('budget') or profile.get('budget_max')
        
        reply = f"**{city}房产投资分析**\n\n"
        reply += f"📊 **市场分析**：\n"
        reply += f"- {city}作为一线城市，长期价值稳定\n"
        reply += f"- 核心区域抗跌性强\n"
        reply += f"- 新兴区域有较大升值空间\n\n"
        
        reply += f"💡 **投资建议**：\n"
        reply += f"1. **核心区域**：保值性强，适合稳健投资\n"
        reply += f"2. **新兴区域**：升值潜力大，但风险较高\n"
        reply += f"3. **学区房**：需求稳定，流动性好\n\n"
        
        reply += f"⚠️ **风险提示**：\n"
        reply += f"- 政策调控风险\n"
        reply += f"- 市场波动风险\n"
        reply += f"- 流动性风险\n"
        reply += f"- 建议分散投资，控制杠杆\n"
        
        return reply
    
    async def _handle_other(self, entities: Dict, profile: Dict) -> str:
        """处理其他问题"""
        return """您好！我是房产咨询助手，可以帮您：

🏠 **购房推荐** - 告诉我您的预算和需求，为您推荐合适的区域
📍 **区域信息** - 查询各区域的房价、配套、特色
📋 **政策咨询** - 了解限购、贷款、公积金等政策
💰 **贷款计算** - 计算月供、首付、贷款能力
📈 **房价趋势** - 分析各区域房价走势

请问有什么可以帮您的？"""
    
    async def generate_report(self, session_id: str, user_id: str, 
                               history: List, profile: Dict) -> Dict:
        """生成咨询报告"""
        summary = "本次咨询主要涉及购房推荐和区域分析。"
        
        recommendations = [
            "建议实地考察意向区域",
            "关注近期市场动态",
            "合理规划贷款方案"
        ]
        
        if history:
            user_messages = [h for h in history if h['role'] == 'user']
            if user_messages:
                summary = f"本次咨询共{len(user_messages)}轮对话，主要讨论了购房相关问题。"
        
        return {
            'summary': summary,
            'recommendations': recommendations,
            'profile': profile,
            'history_count': len(history) if history else 0
        }
