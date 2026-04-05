"""
命盘解读服务
基于六维思维框架，提供结构化、白话、有温度的分析
支持周瑜/陆逊人格化输出
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import random


class MingpanReadingService:
    """命盘解读服务"""
    
    def __init__(self):
        self.personality_styles = {
            "周瑜": {
                "style": "豪爽直接，一针见血",
                "prefix": ["哈哈", "我跟你说", "其实吧", "你要知道"],
                "suffix": ["别急", "听我慢慢说", "咱们不聊虚的"],
                "tone": "鼓励但有力度"
            },
            "陆逊": {
                "style": "稳重细腻，补充完善",
                "prefix": ["我补充一句", "换个角度看", "另外", "还有一点"],
                "suffix": ["这是关键", "记住这点", "很重要"],
                "tone": "温和但有深度"
            }
        }
        
        self.dimension_templates = {
            "pattern": {
                "凤仪型": {
                    "description": "天生会搞关系、会整合资源",
                    "advice": "给她搭建圈子的机会，她就能成事",
                    "warning": "容易飘，需要下沉做实事"
                },
                "蛇灵型": {
                    "description": "耐得住寂寞，等得起机会",
                    "advice": "趴在行业里别动，边等边积累",
                    "warning": "最怕耐不住，频繁换赛道"
                },
                "鹤贤型": {
                    "description": "稳扎稳打，靠手艺吃饭",
                    "advice": "专业深耕，越老越值钱",
                    "warning": "别眼红别人暴富，你的路是养出来的"
                },
                "龙尊型": {
                    "description": "天生有号召力，能驾驭人势",
                    "advice": "组建团队，让别人跟着你干",
                    "warning": "要会用人，别什么都自己抓"
                }
            },
            "wealth": {
                "正财型": {
                    "description": "靠本事、靠时间、靠积累",
                    "advice": "选一个领域深耕，钱会随时间长出来",
                    "warning": "别想一夜暴富，那不是你的路"
                },
                "偏财型": {
                    "description": "靠机会、靠圈子、靠胆量",
                    "advice": "等待时机，机会来了敢下注",
                    "warning": "风险高，一波一波，要有底线"
                }
            }
        }
    
    def analyze_user_query(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析用户查询，返回结构化解读
        
        Args:
            query: 用户输入的问题或描述
            user_context: 用户上下文（历史记忆、基本信息等）
            
        Returns:
            结构化解读结果
        """
        intent = self._detect_intent(query)
        
        key_info = self._extract_key_info(query)
        
        dimension_analysis = self._analyze_dimensions(key_info, user_context)
        
        personalized_output = self._generate_personalized_output(
            dimension_analysis, intent, user_context
        )
        
        return {
            "intent": intent,
            "key_info": key_info,
            "dimension_analysis": dimension_analysis,
            "personalized_output": personalized_output,
            "timestamp": datetime.now().isoformat()
        }
    
    def _detect_intent(self, query: str) -> str:
        """检测用户意图"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["财运", "赚钱", "发财", "钱"]):
            return "财运分析"
        elif any(kw in query_lower for kw in ["姻缘", "感情", "婚姻", "对象"]):
            return "姻缘分析"
        elif any(kw in query_lower for kw in ["事业", "工作", "职业", "行业"]):
            return "事业分析"
        elif any(kw in query_lower for kw in ["天赋", "格局", "适合", "擅长"]):
            return "天赋分析"
        elif any(kw in query_lower for kw in ["人际", "朋友", "亲戚", "六亲"]):
            return "人际分析"
        elif any(kw in query_lower for kw in ["执行", "心态", "行动", "改变"]):
            return "执行力分析"
        else:
            return "整体分析"
    
    def _extract_key_info(self, query: str) -> Dict[str, Any]:
        """提取关键信息"""
        info = {
            "mentioned_stars": [],
            "mentioned_palaces": [],
            "mentioned_elements": [],
            "age_hint": None,
            "gender_hint": None,
            "situation_keywords": []
        }
        
        stars = ["天机", "紫微", "太阳", "太阴", "贪狼", "巨门", "天相", "天梁", 
                 "七杀", "破军", "廉贞", "武曲", "天府", "太阴", "天同"]
        for star in stars:
            if star in query:
                info["mentioned_stars"].append(star)
        
        palaces = ["命宫", "财帛宫", "夫妻宫", "官禄宫", "交友宫", "迁移宫", "福德宫"]
        for palace in palaces:
            if palace in query:
                info["mentioned_palaces"].append(palace)
        
        age_patterns = [
            (r"(\d+)岁", "exact"),
            (r"(\d+)后", "after"),
            (r"(\d+)前", "before"),
        ]
        for pattern, atype in age_patterns:
            match = re.search(pattern, query)
            if match:
                info["age_hint"] = {"age": int(match.group(1)), "type": atype}
                break
        
        if "男" in query or "他" in query:
            info["gender_hint"] = "男"
        elif "女" in query or "她" in query:
            info["gender_hint"] = "女"
        
        situation_keywords = ["创业", "打工", "体制内", "跳槽", "转行", "炒股", 
                             "买房", "结婚", "离婚", "失业", "升职"]
        for kw in situation_keywords:
            if kw in query:
                info["situation_keywords"].append(kw)
        
        return info
    
    def _analyze_dimensions(self, key_info: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """六维分析"""
        analysis = {}
        
        stars = key_info.get("mentioned_stars", [])
        if "天机" in stars:
            analysis["pattern"] = {
                "type": "蛇灵型/鹤贤型混合",
                "description": "心思细腻、善于谋略，但容易想得多做得少",
                "strength": "逻辑分析、信息整合能力强",
                "weakness": "多思少行，需要外力推动",
                "score": 0.7
            }
        elif "紫微" in stars:
            analysis["pattern"] = {
                "type": "龙尊型",
                "description": "天生有领导气质，能驾驭人势",
                "strength": "号召力强，善于整合资源",
                "weakness": "可能过于强势，需要学会用人",
                "score": 0.8
            }
        elif "贪狼" in stars or "廉贞" in stars:
            analysis["pattern"] = {
                "type": "凤仪型",
                "description": "善于笼络资源，人际交往能力强",
                "strength": "会搞关系，能借力成事",
                "weakness": "容易飘，需要下沉做实事",
                "score": 0.75
            }
        else:
            analysis["pattern"] = {
                "type": "待确认",
                "description": "需要更多信息来判断你的格局类型",
                "strength": "待分析",
                "weakness": "待分析",
                "score": 0.5
            }
        
        palaces = key_info.get("mentioned_palaces", [])
        if "财帛宫" in palaces:
            analysis["wealth"] = {
                "type": "需结合具体星耀判断",
                "description": "财帛宫被提及，财运是关注重点",
                "advice": "正财偏财需看具体配置",
                "score": 0.6
            }
        else:
            analysis["wealth"] = {
                "type": "正财型",
                "description": "适合靠专业积累，稳步增长",
                "advice": "深耕一个领域，钱会随时间长出来",
                "score": 0.7
            }
        
        if "夫妻宫" in palaces:
            analysis["marriage"] = {
                "level": "中段位",
                "description": "夫妻宫被关注，姻缘是当前重点",
                "gap": "需要评估自我认知与期望的匹配度",
                "score": 0.6
            }
        else:
            analysis["marriage"] = {
                "level": "待评估",
                "description": "姻缘状况需要更多信息",
                "gap": "先提升自己，姻缘自然来",
                "score": 0.5
            }
        
        age_hint = key_info.get("age_hint")
        if age_hint:
            age = age_hint.get("age", 30)
            if age < 30:
                stage = "30岁前-试错期"
                advice = "可以换行业、试错，但每次换都要往更高阶跳"
            elif age < 40:
                stage = "30岁后-扎根期"
                advice = "选赛道，扎根，做到前20%"
            else:
                stage = "40岁后-做局期"
                advice = "从做事变成做人，培养接班人"
            analysis["career"] = {
                "stage": stage,
                "advice": advice,
                "score": 0.65
            }
        else:
            analysis["career"] = {
                "stage": "待确认",
                "advice": "需要了解你的年龄和当前状态",
                "score": 0.5
            }
        
        analysis["relations"] = {
            "type": "混合型",
            "description": "身边滋养型和消耗型各占一半",
            "advice": "主动维护滋养型关系，对消耗型保持距离",
            "score": 0.6
        }
        
        analysis["execution"] = {
            "level": "中",
            "description": "看得懂道理，但执行上有差距",
            "advice": "从一件小事开始，每天坚持",
            "score": 0.55
        }
        
        return analysis
    
    def _generate_personalized_output(
        self, 
        dimension_analysis: Dict, 
        intent: str,
        user_context: Dict = None
    ) -> Dict[str, str]:
        """生成人格化输出"""
        output = {
            "opening": "",
            "dimensions": {},
            "summary": "",
            "next_steps": []
        }
        
        output["opening"] = self._generate_opening(intent)
        
        for dim_name, dim_data in dimension_analysis.items():
            output["dimensions"][dim_name] = self._generate_dimension_output(
                dim_name, dim_data
            )
        
        output["summary"] = self._generate_summary(dimension_analysis)
        
        output["next_steps"] = self._generate_next_steps(dimension_analysis)
        
        return output
    
    def _generate_opening(self, intent: str) -> str:
        """生成开场白"""
        openings = {
            "财运分析": [
                "周瑜：哈哈，问财运的，十个有九个。但你问对了——不是问什么时候发财，是问钱从哪来。",
                "陆逊：我补充一句，财运这事，先搞清楚你是正财还是偏财，比问什么时候发财重要。"
            ],
            "姻缘分析": [
                "周瑜：姻缘这事，很多人以为是运气，其实是段位匹配。你到了哪个段位，就遇到哪个段位的人。",
                "陆逊：感情这东西最容易让人失去理性。咱们用逻辑拆一拆，别被情绪带着走。"
            ],
            "事业分析": [
                "周瑜：事业不是选行业，是踩节点。30岁前试错，30岁后扎根，40岁后做局。",
                "陆逊：我见过太多人，选对了行业但踩错了节点，结果白忙一场。"
            ],
            "整体分析": [
                "周瑜：看盘这事，有人看成算命，有人看成地图。我们帮你当地图——先看看你站在哪个路口。",
                "陆逊：我们整理了几千个案例，总结出六个维度。把问题往这六个方向套，自然就清楚自己的位置了。"
            ]
        }
        
        return "\n".join(openings.get(intent, openings["整体分析"]))
    
    def _generate_dimension_output(self, dim_name: str, dim_data: Dict) -> str:
        """生成单个维度的输出"""
        dim_titles = {
            "pattern": "你的天赋赛道",
            "wealth": "你的钱从哪来",
            "marriage": "你的姻缘逻辑",
            "career": "你的事业节点",
            "relations": "你身边的人",
            "execution": "你的执行力与心态"
        }
        
        title = dim_titles.get(dim_name, dim_name)
        
        zhouyu_comment = self._generate_zhouyu_comment(dim_name, dim_data)
        luxun_comment = self._generate_luxun_comment(dim_name, dim_data)
        
        return f"### {title}\n\n**系统分析**：\n> {dim_data.get('description', '待分析')}\n\n**周瑜点评**：{zhouyu_comment}\n\n**陆逊补充**：{luxun_comment}"
    
    def _generate_zhouyu_comment(self, dim_name: str, dim_data: Dict) -> str:
        """生成周瑜风格点评"""
        comments = {
            "pattern": f"你身上的天赋是{dim_data.get('type', '待确认')}，{dim_data.get('description', '')}。但记住，天赋不等于命运，关键是怎么用。",
            "wealth": f"你的财运类型是{dim_data.get('type', '待确认')}。{dim_data.get('advice', '')}。别眼红别人的路，走好自己的路。",
            "marriage": f"姻缘这事，{dim_data.get('description', '')}。{dim_data.get('gap', '')}。先提升自己，姻缘自然来。",
            "career": f"你现在处于{dim_data.get('stage', '待确认')}。{dim_data.get('advice', '')}。别再跳了，选一个赛道深耕。",
            "relations": f"你身边的人，{dim_data.get('description', '')}。{dim_data.get('advice', '')}。保护好自己的能量场。",
            "execution": f"你的执行力{dim_data.get('level', '待确认')}。{dim_data.get('advice', '')}。从一件小事开始，别想太多。"
        }
        return comments.get(dim_name, "需要更多信息来分析。")
    
    def _generate_luxun_comment(self, dim_name: str, dim_data: Dict) -> str:
        """生成陆逊风格补充"""
        comments = {
            "pattern": f"换个角度看，{dim_data.get('weakness', '')}。这是你需要突破的地方。",
            "wealth": f"另外，{dim_data.get('type', '')}的人，最怕的就是错把欲望当天赋。认清自己，比什么都重要。",
            "marriage": f"还有一点，感情这事急不来。你先把自己的局做大，自然会吸引同频的人。",
            "career": f"记住，事业不是选一个干一辈子，是在正确的时间节点，踩上正确的节奏。",
            "relations": f"滋养型的人带你往上走，消耗型的人只会拖后腿。分清楚，很重要。",
            "execution": f"心态差的人，机会来了也接不住。建议从记录每天做成的事开始，慢慢建立信心。"
        }
        return comments.get(dim_name, "这是关键，要重视。")
    
    def _generate_summary(self, dimension_analysis: Dict) -> str:
        """生成总结"""
        pattern = dimension_analysis.get("pattern", {}).get("type", "待确认")
        wealth = dimension_analysis.get("wealth", {}).get("type", "待确认")
        
        summary = f"""**周瑜**：命盘不是判官，是地图。你现在的位置，我们帮你标出来了：你擅长的是{pattern}，财运类型是{wealth}。需要的是选准赛道、深耕下去，同时过滤消耗型关系，提升执行力。

**陆逊**：地图画好了，路怎么走，还得靠你自己。我们会用海马体记忆系统，帮你记住你走过的每一步，让你回头看时，知道自己怎么走到今天的。

**房都督平台**：如需进一步细化某个维度，或查看与你类似的案例（我们案例库里有4000多个），告诉我你的具体问题，我们接着聊。"""
        
        return summary
    
    def _generate_next_steps(self, dimension_analysis: Dict) -> List[str]:
        """生成下一步建议"""
        steps = []
        
        pattern_score = dimension_analysis.get("pattern", {}).get("score", 0.5)
        if pattern_score < 0.6:
            steps.append("建议先完成格局测试，确定你的天赋类型")
        
        execution_score = dimension_analysis.get("execution", {}).get("score", 0.5)
        if execution_score < 0.6:
            steps.append("从今天开始，每天记录三件做成的事，提升执行力")
        
        relations_score = dimension_analysis.get("relations", {}).get("score", 0.5)
        if relations_score < 0.6:
            steps.append("梳理身边人际关系，区分滋养型和消耗型")
        
        if not steps:
            steps.append("保持现有节奏，继续深耕")
            steps.append("定期回顾目标，调整方向")
        
        return steps


mingpan_reading_service = MingpanReadingService()
