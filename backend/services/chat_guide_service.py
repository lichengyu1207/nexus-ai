"""
智能咨询对话引导服务
基于场景识别的智能对话引导
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import random


class ChatGuideService:
    """智能咨询对话引导服务"""
    
    def __init__(self):
        self.scene_handlers = {}
        self._init_handlers()
    
    def _init_handlers(self):
        self.scene_handlers = {
            "mingpan_basic": self._handle_mingpan_basic,
            "time_unknown": self._handle_time_unknown,
            "time_known": self._handle_time_known,
            "star_explain": self._handle_star_explain,
            "wealth_star": self._handle_wealth_star,
            "marriage": self._handle_marriage,
            "city_direction": self._handle_city_direction,
            "wealth_bad": self._handle_wealth_bad,
            "job_change": self._handle_job_change,
            "career": self._handle_career,
            "element": self._handle_element,
            "authority": self._handle_authority,
            "property_sell": self._handle_property_sell,
            "property_buy": self._handle_property_buy,
            "property_school": self._handle_property_school,
            "property_new_old": self._handle_property_new_old,
            "property_budget": self._handle_property_budget,
            "property_payment": self._handle_property_payment,
            "mixed_full": self._handle_mixed_full,
            "mixed_trust": self._handle_mixed_trust,
            "chat_casual": self._handle_chat_casual,
            "chat_skeptical": self._handle_chat_skeptical,
            "chat_cost": self._handle_chat_cost,
            "chat_private": self._handle_chat_private,
            "chat_ai_real": self._handle_chat_ai_real,
            "chat_privacy": self._handle_chat_privacy,
        }
    
    def get_opening_message(self, personality: str = None) -> Dict[str, str]:
        if personality is None:
            personality = random.choice(["周瑜", "陆逊"])
        
        if personality == "周瑜":
            message = "哈哈，来啦！我是周瑜。你是想聊聊命盘，看看自己适合在哪安家？还是已经有中意的房子，想让我帮你参谋参谋？随便说，咱们就当朋友喝茶聊天。"
        else:
            message = "您好，我是陆逊。咱们这里不看虚的，只聊实在的——您是想先看看自己的命盘，看看哪座城市跟您有缘？还是手头有看中的房子，想听听意见？您说，我听。"
        
        return {
            "personality": personality,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_intent(self, user_message: str) -> tuple:
        msg = user_message.lower()
        
        if "命盘" in msg and "不懂" in msg:
            return "mingpan", "mingpan_basic"
        if "时辰" in msg and ("不知道" in msg or "不清楚" in msg):
            return "mingpan", "time_unknown"
        if "时辰" in msg and "戌时" in msg:
            return "mingpan", "time_known"
        if any(star in msg for star in ["天机", "紫微", "太阳", "太阴"]):
            return "mingpan", "star_explain"
        if "禄存" in msg or "财帛宫" in msg:
            return "mingpan", "wealth_star"
        if "夫妻宫" in msg or "婚姻" in msg:
            return "mingpan", "marriage"
        if "城市" in msg and "发展" in msg:
            return "mingpan", "city_direction"
        if "财运" in msg and "不好" in msg:
            return "mingpan", "wealth_bad"
        if "换工作" in msg:
            return "mingpan", "job_change"
        if "行业" in msg and "适合" in msg:
            return "mingpan", "career"
        if "缺木" in msg or "五行" in msg:
            return "mingpan", "element"
        if "天梁" in msg or "化权" in msg:
            return "mingpan", "authority"
        
        if "卖" in msg and "房" in msg:
            return "property", "property_sell"
        if "买" in msg and "房" in msg:
            return "property", "property_buy"
        if "学区" in msg:
            return "property", "property_school"
        if "新房" in msg or "二手房" in msg:
            return "property", "property_new_old"
        if "万" in msg and ("预算" in msg or "手头" in msg):
            return "property", "property_budget"
        if "全款" in msg or "贷款" in msg:
            return "property", "property_payment"
        
        if "命盘" in msg and ("房" in msg or "城市" in msg):
            return "mixed", "mixed_full"
        if "准吗" in msg or "不信" in msg:
            return "mixed", "mixed_trust"
        
        if "随便" in msg or "看看" in msg:
            return "chat", "chat_casual"
        if "收费" in msg or "多少钱" in msg:
            return "chat", "chat_cost"
        if "AI" in msg or "真人" in msg:
            return "chat", "chat_ai_real"
        if "隐私" in msg or "保存" in msg:
            return "chat", "chat_privacy"
        
        return "chat", "chat_casual"
    
    def generate_response(self, user_message: str, personality: str = "周瑜", context: Dict = None) -> Dict:
        category, scene = self.detect_intent(user_message)
        handler = self.scene_handlers.get(scene, self._handle_chat_casual)
        response = handler(user_message, personality, context or {})
        
        return {
            "personality": personality,
            "category": category,
            "scene": scene,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    def _handle_mingpan_basic(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "没事，您不用懂。您只要告诉我您的出生年月日时（阳历就行），或者您手上有没有用其他软件排好的盘？有图的话直接发我，我来解读。"
        return "您不需要懂命理，只需要提供信息。您可以把出生时间告诉我，或者如果您有其他软件排好的盘，直接发图给我，我来帮您解读。"
    
    def _handle_time_unknown(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "时辰不知道没关系，咱们先按子时看个大概，等您以后找到准确时辰再校正。重点是您最关心哪方面？财运、事业、姻缘，还是直接问买房适合哪座城市？"
        return "时辰不清楚的话，我们可以先用子时作为参考，之后有机会再校正。您现在最想了解的是哪个方面？财运、事业、姻缘，还是房产方向？"
    
    def _handle_time_known(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "戌时是晚上7-9点，对。您这信息够用了。那咱们先聊聊您最近最想解决的事？比如想换工作、想买房、还是感情上有点迷茫？"
        return "好的，时间信息有了。那我们聊聊您最近最关心的事吧？是工作、房子，还是其他方面？"
    
    def _handle_star_explain(self, msg: str, personality: str, ctx: Dict) -> str:
        if "天机" in msg:
            if personality == "周瑜":
                return "天机坐命的人，心思细腻、善于谋划，但容易想多做少。这不一定是坏事，关键看怎么用。您可以把天机想象成一台高配电脑——性能好，但得有人开机、有人用。您现在最想用它来解决什么问题？"
            return "天机星代表智慧和谋略。您天生善于分析，但有时会想得太多。关键是把想法变成行动。您现在最想解决什么问题？"
        return "这个星曜有它的特点，关键看怎么发挥。您想先了解哪个方面？"
    
    def _handle_wealth_star(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "哈哈，禄存是财星，但钱不是天上掉下来的。它代表您有'稳中求富'的潜力，靠本事、靠时间积累，而不是靠投机。您现在做的工作，是跟专业、技术相关的吗？"
        return "禄存在财帛宫，说明您的财运适合稳健积累。不是一夜暴富，而是靠专业和时间慢慢增长。您现在从事什么工作？"
    
    def _handle_marriage(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "有煞星不代表不顺，只是提醒您在感情上要多留个心眼，别轻易被表面现象迷惑。更重要的是，您的婚姻走势会随着您自身状态变化而变化。您现在单身还是有伴侣？方便聊聊吗？"
        return "夫妻宫的情况需要结合整体来看。您现在的感情状态怎么样？有什么具体想了解的？"
    
    def _handle_city_direction(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "这个好办。您先告诉我，您现在在哪个城市？或者您心里有没有想去的方向？比如南方、北方，还是沿海城市？结合您的命盘，咱们一起挑个最旺您的地方。"
        return "选择城市发展，要结合您的命盘方位。您现在在哪里？有没有倾向的方向？"
    
    def _handle_wealth_bad(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "财运不好，有时是路子不对，有时是时机未到。我先问问您，您觉得自己的收入主要靠什么？工资？生意？投资？还是其他？"
        return "财运的问题需要具体分析。您现在的主要收入来源是什么？"
    
    def _handle_job_change(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "换工作要看盘里流年，也看您现在的心态。您先说说，您现在工作最不满意的地方是什么？是钱少、没发展，还是人际关系？"
        return "换工作的时机需要结合您的流年运势。您现在工作最大的问题是什么？"
    
    def _handle_career(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "您命盘里有文昌文曲，适合跟知识、沟通、文化相关的行业，比如教育、咨询、策划。您现在做哪一行？或者您心里有想尝试的方向？"
        return "从您的命盘看，适合的行业方向比较明确。您现在从事什么工作？"
    
    def _handle_element(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "缺木确实往东、东南方向更顺。但具体到城市，还要看您的事业属性。比如东方有杭州、苏州，东南有上海、广州，您更倾向哪种城市？是喜欢快节奏，还是慢生活？"
        return "五行缺木的话，东方和东南方向更适合您。您对城市有什么偏好？"
    
    def _handle_authority(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "天梁化权，代表您容易在组织里获得权威，不一定是当官，也可能是专业领域里的权威、团队里的核心。您现在是在体制内还是企业？有没有带团队的经验？"
        return "天梁化权代表有领导潜质。您现在的工作环境怎么样？"
    
    def _handle_property_sell(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "当然可以。我先问您几个问题，方便我结合您的命盘和房子本身一起分析：您这套房多大？哪一年的？大概的预算想卖多少？还有，您卖房的目的是换房还是变现？"
        return "卖房需要综合考虑市场时机和您的个人情况。您能告诉我房子的大概情况吗？"
    
    def _handle_property_buy(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "苏州是个好地方，但决定对不对，不光看房子，还得看人。我先问问您，您现在是首套还是二套？准备自住还是投资？还有，您方便告诉我您的出生年吗？这样我能结合您的命盘，看看苏州是不是旺您。"
        return "买房是大事，需要结合您的命盘和实际情况。您能告诉我更多细节吗？"
    
    def _handle_property_school(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "教育资源好的城市很多，但得看哪个城市跟您有缘。您先说说，您对城市有什么偏好？比如南方还是北方，离家近还是远？还有，您孩子的出生年份？这样我帮您挑个最适合您家的地方。"
        return "学区房选择需要综合考虑教育资源和个人命盘。您有什么偏好？"
    
    def _handle_property_new_old(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "这要看您的命盘里是'稳'还是'活'。从您刚才说的信息看，您偏正财，求稳，所以二手房可能更适合您——看得见、摸得着，风险低。但如果您想搏一搏升值，有些新板块也有机会。您更看重安全，还是搏一把？"
        return "新房和二手房各有优势，需要结合您的风险偏好来选择。"
    
    def _handle_property_budget(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "100万的话，在杭州、苏州能买个小户型，在成都、长沙能买大一点的。关键看您想在哪发展。您命盘里适合东南方向，如果可能，我建议优先考虑杭州或苏州的次新房，虽然小，但保值。您想先看哪几个城市？"
        return "预算范围内，需要结合您的命盘方位来选择城市。您有倾向的方向吗？"
    
    def _handle_property_payment(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "全款稳，贷款活。您命盘正财旺，适合稳，但如果您有其他投资渠道，能跑赢房贷利率，那贷款更划算。您目前有其他投资吗？还是想保守一点？"
        return "全款还是贷款，要看您的资金安排和风险偏好。"
    
    def _handle_mixed_full(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "没问题，咱们一步到位。您先告诉我您的出生年月日时，还有您现在的城市和预算。我帮您先看命盘，再挑城市，最后筛房源。"
        return "好的，我们可以一站式解决。您能提供出生信息和预算吗？"
    
    def _handle_mixed_trust(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "准不准，得看您信不信'人房合一'这个理。我们不是算命，是把您命盘里的天赋、运势、方位，跟真实房产数据结合起来，让您少走弯路。您想先试试哪个环节？"
        return "我们的方法是将命盘分析与房产数据结合，帮您做出更合适的决策。"
    
    def _handle_chat_casual(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "那咱们就随便聊聊。我给您抛个引子：您有没有想过，自己这辈子最顺的事是什么？或者最想解决却一直没下手的事？咱们可以顺着这个聊开。"
        return "没关系，我们可以慢慢聊。您最近有没有什么想做的事？或者有什么困惑？"
    
    def _handle_chat_skeptical(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "信不信不重要，有用就行。我们把它当成一种梳理自己的工具，就像做心理测试一样，帮您更清楚自己的优势和卡点。您要是愿意，咱们就当玩个游戏，试试看有没有帮助。"
        return "试试看就知道了，我们不是算命，是帮您梳理方向。"
    
    def _handle_chat_cost(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "哈哈，第一次聊，免费！就是交个朋友。您要是觉得有用，以后深度分析可以升级。您先试试？"
        return "首次咨询是免费的，您可以先体验一下。"
    
    def _handle_chat_private(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "理解。那咱们就聊您愿意说的部分。比如，您可以直接问我一个您最关心的问题，我试着回答。或者您发一张您自己排好的命盘图，我只看图说话，不问您个人信息。"
        return "您可以只说您愿意说的，我们尊重您的隐私。"
    
    def _handle_chat_ai_real(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "周瑜":
            return "我是周瑜，他是陆逊，都是AI，但背后有我们团队设计的思维框架和几千个真实案例支撑。您就当跟一个读过很多盘的朋友聊天，不用有压力。"
        return "我们是AI助手，但有专业的思维框架和案例库支撑。您可以放心咨询。"
    
    def _handle_chat_privacy(self, msg: str, personality: str, ctx: Dict) -> str:
        if personality == "陆逊":
            return "您的隐私很重要。我们只会记录您自愿提供的信息，用于给您更好的建议。您可以随时要求删除。这次咱们聊的内容，您愿意让我记住吗？这样下次您再来，我能接着上次聊。"
        return "我们重视您的隐私，您可以控制哪些信息被记录。"


chat_guide_service = ChatGuideService()
