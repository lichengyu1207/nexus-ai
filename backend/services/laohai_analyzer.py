"""
命盘案例库高级分析服务
老骇风格深度分析和报告生成
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import random


class LaohaiAnalyzer:
    """老骇风格分析器"""
    
    def __init__(self):
        self.case_library = []
        self.dimension_weights = {
            "pattern": 0.25,
            "wealth": 0.15,
            "marriage": 0.15,
            "career": 0.20,
            "relations": 0.10,
            "execution": 0.15
        }
    
    def load_cases(self, cases: List[Dict[str, Any]]):
        """加载案例库"""
        self.case_library = cases
    
    def analyze_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度分析单个案例
        
        Returns:
            包含深度分析和破局建议的字典
        """
        pattern_analysis = self._analyze_dimension_pattern(case)
        wealth_analysis = self._analyze_dimension_wealth(case)
        marriage_analysis = self._analyze_dimension_marriage(case)
        career_analysis = self._analyze_dimension_career(case)
        relations_analysis = self._analyze_dimension_relations(case)
        execution_analysis = self._analyze_dimension_execution(case)
        
        overall_score = self._calculate_overall_score(
            pattern_analysis, wealth_analysis, marriage_analysis,
            career_analysis, relations_analysis, execution_analysis
        )
        
        breakthrough_suggestions = self._generate_breakthrough_suggestions(case)
        
        similar_cases = self._find_similar_cases(case)
        
        return {
            "case_id": case.get("case_id"),
            "analysis_timestamp": datetime.now().isoformat(),
            "dimension_scores": {
                "pattern": pattern_analysis,
                "wealth": wealth_analysis,
                "marriage": marriage_analysis,
                "career": career_analysis,
                "relations": relations_analysis,
                "execution": execution_analysis
            },
            "overall_score": overall_score,
            "breakthrough_suggestions": breakthrough_suggestions,
            "similar_cases": similar_cases,
            "laohai_comment": self._generate_laohai_comment(case, overall_score)
        }
    
    def _analyze_dimension_pattern(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """分析第一维度：格局"""
        pattern = case.get("dimension_1_pattern", {})
        pattern_type = pattern.get("type", "未知")
        
        analysis = {
            "type": pattern_type,
            "strength": 0.0,
            "blockage_indicators": [],
            "opportunity_indicators": [],
            "advice": ""
        }
        
        if pattern.get("blockage"):
            analysis["blockage_indicators"].append(pattern.get("blockage"))
            analysis["strength"] = 0.3
        else:
            analysis["strength"] = 0.8
        
        if pattern.get("suggestion"):
            analysis["advice"] = pattern.get("suggestion")
        
        if pattern_type == "凤仪型":
            analysis["opportunity_indicators"].append("需要更大的舞台")
        elif pattern_type == "蛇灵型":
            analysis["opportunity_indicators"].append("需要等待时机，同时积累")
        elif pattern_type == "鹤贤型":
            analysis["opportunity_indicators"].append("需要持续深耕")
        elif pattern_type == "龙尊型":
            analysis["opportunity_indicators"].append("需要组建团队")
        
        return analysis
    
    def _analyze_dimension_wealth(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """分析第二维度：财运"""
        wealth = case.get("dimension_2_wealth", {})
        wealth_type = wealth.get("type", "未知")
        
        analysis = {
            "type": wealth_type,
            "match_score": 0.0,
            "risk_indicators": [],
            "advice": ""
        }
        
        if wealth.get("warning"):
            analysis["risk_indicators"].append(wealth.get("warning"))
            analysis["match_score"] = 0.5
        else:
            analysis["match_score"] = 0.8
        
        if wealth_type == "正财型":
            analysis["advice"] = "稳稳当当积累，别想一夜暴富"
        elif wealth_type == "偏财型":
            analysis["advice"] = "等待机会，但别all in"
        
        return analysis
    
    def _analyze_dimension_marriage(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """分析第三维度：姻缘"""
        marriage = case.get("dimension_3_marriage", {})
        level = marriage.get("level", "未知")
        
        analysis = {
            "level": level,
            "gap_score": 0.0,
            "issues": [],
            "advice": ""
        }
        
        if marriage.get("gap_analysis"):
            analysis["issues"].append(marriage.get("gap_analysis"))
            analysis["gap_score"] = 0.4
        else:
            analysis["gap_score"] = 0.9
        
        if level == "低段位":
            analysis["advice"] = "先提升自己，别急着找对象"
        elif level == "中段位":
            analysis["advice"] = "保持现有节奏，等待机会"
        elif level == "高段位":
            analysis["advice"] = "你已经准备好了，缘分会来"
        
        return analysis
    
    def _analyze_dimension_career(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """分析第四维度：事业"""
        career = case.get("dimension_4_career", {})
        stage = career.get("stage", "未知")
        
        analysis = {
            "stage": stage,
            "readiness_score": 0.0,
            "transition_indicators": [],
            "advice": ""
        }
        
        if career.get("next_step"):
            analysis["transition_indicators"].append(career.get("next_step"))
            analysis["readiness_score"] = 0.7
        
        if "30岁前" in stage:
            analysis["advice"] = "可以试错，但要往更高阶跳"
        elif "30岁后" in stage:
            analysis["advice"] = "扎根，别老想跳"
        elif "40岁后" in stage:
            analysis["advice"] = "从做事变成做人"
        
        return analysis
    
    def _analyze_dimension_relations(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """分析第五维度：人际"""
        relations = case.get("dimension_5_relations", {})
        family_type = relations.get("family_type", "未知")
        
        analysis = {
            "family_type": family_type,
            "energy_score": 0.0,
            "drains": [],
            "advice": ""
        }
        
        drains = relations.get("energy_drains", [])
        if drains:
            analysis["drains"] = drains
            analysis["energy_score"] = 0.3
        else:
            analysis["energy_score"] = 0.9
        
        if family_type == "消耗型":
            analysis["advice"] = "物理隔离，保护能量场"
        elif family_type == "滋养型":
            analysis["advice"] = "珍惜身边人"
        else:
            analysis["advice"] = "保持边界"
        
        return analysis
    
    def _analyze_dimension_execution(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """分析第六维度：执行力"""
        execution = case.get("dimension_6_execution", {})
        level = execution.get("level", "未知")
        
        analysis = {
            "level": level,
            "realization_rate": execution.get("realization_rate", 0.0),
            "blockage": "",
            "advice": ""
        }
        
        if execution.get("blockage"):
            analysis["blockage"] = execution.get("blockage")
        
        if level == "强":
            analysis["advice"] = "继续保持，你比大多数人强"
        elif level == "中":
            analysis["advice"] = "再坚持一下，就能突破"
        elif level == "弱":
            analysis["advice"] = "先从一件小事做起，别想太多"
        
        return analysis
    
    def _calculate_overall_score(self, *dimension_analyses) -> Dict[str, Any]:
        """计算综合评分"""
        total_score = 0.0
        weights = list(self.dimension_weights.values())
        
        for i, analysis in enumerate(dimension_analyses):
            score = 0.0
            if i == 0:  # pattern
                score = analysis.get("strength", 0.5)
            elif i == 1:  # wealth
                score = analysis.get("match_score", 0.5)
            elif i == 2:  # marriage
                score = analysis.get("gap_score", 0.5)
            elif i == 3:  # career
                score = analysis.get("readiness_score", 0.5)
            elif i == 4:  # relations
                score = analysis.get("energy_score", 0.5)
            elif i == 5:  # execution
                score = analysis.get("realization_rate", 0.5)
            
            total_score += score * weights[i]
        
        return {
            "score": round(total_score * 100, 1),
            "level": "优秀" if total_score > 0.8 else "良好" if total_score > 0.6 else "需努力",
            "breakthrough_priority": self._get_breakthrough_priority(dimension_analyses)
        }
    
    def _get_breakthrough_priority(self, dimension_analyses) -> List[str]:
        """获取突破优先级"""
        priorities = []
        
        if dimension_analyses[0].get("strength", 0) < 0.5:
            priorities.append("格局定调")
        if dimension_analyses[5].get("realization_rate", 0) < 0.5:
            priorities.append("执行力提升")
        if dimension_analyses[4].get("energy_score", 0) < 0.5:
            priorities.append("人际过滤")
        if dimension_analyses[2].get("gap_score", 0) < 0.5:
            priorities.append("姻缘提升")
        
        return priorities if priorities else ["保持现有优势"]
    
    def _generate_breakthrough_suggestions(self, case: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成破局建议"""
        suggestions = []
        
        pattern = case.get("dimension_1_pattern", {})
        if pattern.get("type") == "凤仪型":
            suggestions.append({
                "dimension": "格局",
                "suggestion": "凤仪型的人天生会搞关系，但需要舞台。如果现在被困在基层，先想办法跳到更高的圈层。记住，圈子决定命运。"
            })
        
        execution = case.get("dimension_6_execution", {})
        if execution.get("level") == "弱":
            suggestions.append({
                "dimension": "执行力",
                "suggestion": "别想太多，先做一件小事。哪怕每天只做十分钟，坚持三个月，你会发现不一样。"
            })
        
        relations = case.get("dimension_5_relations", {})
        if relations.get("family_type") == "消耗型":
            suggestions.append({
                "dimension": "人际",
                "suggestion": "对于消耗型的人，直接物理隔离。不要试图改变他们，你改变不了。你能做的，是保护好自己的能量场。"
            })
        
        wealth = case.get("dimension_2_wealth", {})
        if wealth.get("type") == "正财型" and "炒股" in case.get("background", ""):
            suggestions.append({
                "dimension": "财运",
                "suggestion": "正财的命，就踏踏实实积累。别眼红偏财，那不是你的赛道。贪字的另一边是贫。"
            })
        
        if not suggestions:
            suggestions.append({
                "dimension": "综合",
                "suggestion": "你的命盘整体不错，关键是要动起来。命盘是地图，你是司机。地图再好，也得有人走。"
            })
        
        return suggestions
    
    def _find_similar_cases(self, case: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        """查找相似案例"""
        if not self.case_library:
            return []
        
        target_pattern = case.get("dimension_1_pattern", {}).get("type")
        target_gender = case.get("gender")
        
        similar = []
        for c in self.case_library:
            if c.get("case_id") == case.get("case_id"):
                continue
            
            if c.get("dimension_1_pattern", {}).get("type") == target_pattern:
                if c.get("gender") == target_gender:
                    similar.append({
                        "case_id": c.get("case_id"),
                        "name": c.get("anonymized_name"),
                        "pattern": c.get("dimension_1_pattern", {}).get("type"),
                        "outcome": c.get("outcome_status"),
                        "rating": c.get("outcome_rating", 0),
                        "key_lesson": c.get("outcome_lessons", [""])[0] if c.get("outcome_lessons") else ""
                    })
        
        similar.sort(key=lambda x: -x.get("rating", 0))
        return similar[:limit]
    
    def _generate_laohai_comment(self, case: Dict[str, Any], overall_score: Dict[str, Any]) -> str:
        """生成老骇风格点评"""
        name = case.get("anonymized_name", "这 人")
        outcome = case.get("outcome_status", "未知")
        pattern = case.get("dimension_1_pattern", {}).get("type", "未知")
        
        comments = []
        
        if outcome == "已破局":
            comments.append(f"{name}这案例我看了，典型的{pattern}破局。")
            comments.append("很多人命盘不差，就是不动。")
            comments.append("但{name}动起来了，所以成了。")
        elif outcome == "困局中":
            comments.append(f"{name}这案例，还在困局里。")
            blockages = case.get("dimension_1_pattern", {}).get("blockage")
            if blockages:
                comments.append(f"卡点在{blockages}。")
            comments.append("命盘是地图，你得自己走。")
        else:
            comments.append(f"{name}这案例，在破局路上。")
            comments.append("继续观察，看看能不能突破。")
        
        level = overall_score.get("level", "未知")
        comments.append(f"综合评分{overall_score.get('score', 0)}分，{level}。")
        
        return " ".join(comments)
    
    def generate_comparative_report(self, case_ids: List[str]) -> Dict[str, Any]:
        """生成对比分析报告"""
        cases = []
        for cid in case_ids:
            for c in self.case_library:
                if c.get("case_id") == cid:
                    cases.append(c)
                    break
        
        if not cases:
            return {"error": "未找到相关案例"}
        
        comparison = {
            "title": "命盘案例对比分析",
            "generated_at": datetime.now().isoformat(),
            "cases": []
        }
        
        for case in cases:
            comparison["cases"].append({
                "case_id": case.get("case_id"),
                "name": case.get("anonymized_name"),
                "pattern": case.get("dimension_1_pattern", {}).get("type"),
                "wealth": case.get("dimension_2_wealth", {}).get("type"),
                "execution": case.get("dimension_6_execution", {}).get("level"),
                "outcome": case.get("outcome_status"),
                "rating": case.get("outcome_rating", 0)
            })
        
        patterns = [c.get("dimension_1_pattern", {}).get("type") for c in cases]
        from collections import Counter
        pattern_dist = Counter(patterns)
        
        outcomes = [c.get("outcome_status") for c in cases]
        outcome_dist = Counter(outcomes)
        
        comparison["summary"] = {
            "pattern_distribution": dict(pattern_dist),
            "outcome_distribution": dict(outcome_dist),
            "avg_rating": sum(c.get("outcome_rating", 0) for c in cases) / len(cases) if cases else 0
        }
        
        comparison["laohai_insight"] = self._generate_comparative_insight(cases)
        
        return comparison
    
    def _generate_comparative_insight(self, cases: List[Dict]) -> str:
        """生成对比洞察"""
        if len(cases) < 2:
            return ""
        
        success_cases = [c for c in cases if c.get("outcome_status") == "已破局"]
        
        if not success_cases:
            return "这批案例都还在困局中，需要找到突破口。"
        
        patterns = [c.get("dimension_1_pattern", {}).get("type") for c in success_cases]
        executions = [c.get("dimension_6_execution", {}).get("level") for c in success_cases]
        
        insight = f"这{len(cases)}个案例里，{len(success_cases)}个已经破局。破局的人有个共同点——"
        
        from collections import Counter
        pattern_counts = Counter(patterns)
        if pattern_counts:
            most_common_pattern = pattern_counts.most_common(1)[0][0]
            insight += f"{most_common_pattern}占比较多。"
        
        exec_counts = Counter(executions)
        if exec_counts:
            strong_count = exec_counts.get("强", 0)
            if strong_count > len(success_cases) / 2:
                insight += "执行力强的占比高。"
        
        insight += "所以我常说，命盘是地图，你是司机。地图再好，也得有人走。"
        
        return insight


def generate_typical_case_report(case_type: str) -> str:
    """
    根据案例类型生成典型报告摘要
    
    Args:
        case_type: 案例类型（凤仪型/蛇灵型/鹤贤型/龙尊型）
    
    Returns:
        老骇风格报告
    """
    reports = {
        "凤仪型": """
# 凤仪型命盘典型案例分析

## 老骇说

凤仪型的人，我这些年见了太多了。

特点就一个：天生会搞关系、会整合资源。你让她去搞技术，她能憋死。你给她一个圈子，她能玩转。

但凤仪型的人有个致命问题：容易飘。

为什么？
因为她们太容易通过关系得到好处了，就不愿意下沉去做实事。

## 典型案例

案例A：县城姑娘嫁进上海太太圈
- 背景：凤仪型，县城出身，无资源
- 关键：去上海，先打工、学技能、进圈子
- 结果：嫁了金融精英，阶层跨越

案例B：销售冠军年年换公司
- 背景：凤仪型，业绩第一
- 问题：只会搞关系，不学专业
- 结果：35岁后竞争力下降

## 破局关键

凤仪型要成事，必须做到三点：

1. **扎进去**：别光学关系，要学真本事
2. **选对圈**：跟对的人，用对的方式
3. **守住**：别飘，别以为自己了不起

记住，关系是放大器，不是根基。
根基不稳，关系越好，摔得越疼。

---

老骇
2026.03.23
""",
        "蛇灵型": """
# 蛇灵型命盘典型案例分析

## 老骇说

蛇灵型的人，是最耐得住寂寞的。

特点就一个：等得起机会，扛得住失败。你让他今天投明天赚，他做不到。但你让他等三年五年，他能等。

为什么？
因为蛇灵型的人明白一个道理：机会是等出来的，不是找出来的。

## 典型案例

案例A：创业三次终成功
- 背景：蛇灵型，连续创业失败两次
- 关键：第三次踩准风口，等到了
- 结果：三年翻盘，公司估值过亿

案例B：技术宅十年磨一剑
- 背景：蛇灵型，在一个行业深耕十年
- 关键：等行业爆发
- 结果：成为行业专家，收入翻十倍

## 破局关键

蛇灵型要成事，必须做到三点：

1. **趴住别动**：别频繁换赛道
2. **边等边积累**：等待期间别闲着
3. **敢下注**：机会来了要敢出手

记住，蛇灵型的命，就是一个字：等。
但等不是躺平，是一边等一边磨刀。

---

老骇
2026.03.23
""",
        "鹤贤型": """
# 鹤贤型命盘典型案例分析

## 老骇说

鹤贤型的人，是最稳的。

特点就一个：稳扎稳打，靠手艺吃饭。你让他去投机、去创业，他不敢。他就愿意在一个地方慢慢熬。

为什么？
因为鹤贤型的人明白一个道理：慢就是快。

## 典型案例

案例A：基层医生熬成院长
- 背景：鹤贤型，二十年不换单位
- 关键：把专业做透
- 结果：退休时比谁都稳

案例B：技术专家越老越香
- 背景：鹤贤型，一个技术领域深耕三十年
- 关键：专业壁垒
- 结果：60岁被返聘，年薪百万

## 破局关键

鹤贤型要成事，必须做到三点：

1. **别眼红**：看到别人暴富别动摇
2. **持续学**：即使稳，也要跟上时代
3. **建口碑**：专业领域建立个人品牌

记住，鹤贤型不需要追风口。
风口来了，会主动找你。

---

老骇
2026.03.23
""",
        "龙尊型": """
# 龙尊型命盘典型案例分析

## 老骇说

龙尊型的人，是最有领袖气质的。

特点就一个：天生有号召力，能让别人跟着他干。你让他去写代码，他写不过别人。但你让他去管人，一管一个服。

为什么？
因为龙尊型的人懂得一个道理：一个人的力量是有限的，一群人的力量是无穷的。

## 典型案例

案例A：混混做成企业家
- 背景：龙尊型，小混混出身
- 关键：让人愿意跟着他
- 结果：不懂财务，但有人帮他跑腿

案例B：销售做成团队老大
- 背景：龙尊型，个人业绩一般
- 关键：组建并管理团队
- 结果：团队业绩第一

## 破局关键

龙尊型要成事，必须做到三点：

1. **会用人**：找专业的人补自己的短板
2. **大方**：利益要分享，别独吞
3. **立规矩**：恩威并施，别当老好人

记住，龙尊型的命，核心是"用人"，不是"做事"。
事要别人做，你做"人"。

---

老骇
2026.03.23
"""
    }
    
    return reports.get(case_type, "未找到相关案例类型")


def generate_insight_report(keyword: str) -> str:
    """
    生成特定主题的洞察报告
    
    Args:
        keyword: 关键词（如：县城逆袭、创业失败、体制内）
    
    Returns:
        老骇风格洞察报告
    """
    insights = {
        "县城逆袭": """
# 县城青年的逆袭之路

## 老骇说

县城青年要逆袭，难不难？

说难也难，说容易也容易。

难在哪？
资源少、圈子low、视野窄。
容易在哪？
只要你能跳出县城，就成功了一半。

## 核心逻辑

县城逆袭就三步：

**第一步：跳出县城**
不是让你换个县城，是让你去大城市。
哪怕先去打工，也要先去。

**第二步：建立新圈子**
在县城，你接触的是县城思维。
去了大城市，你接触的是大城市思维。
思维变了，命运才能变。

**第三步：变现圈子**
在大城市积累的人脉、资源、认知，
最后要变成你能变现的东西。

## 典型案例

那个县城姑娘，去上海先进工厂，
后来学技能、进圈子，最后嫁精英。
她不是运气好，是每一步都踩对了。

---

老骇
2026.03.23
""",
        "创业失败": """
# 创业失败者的共同特征

## 老骇说

创业失败的，我见的太多了。

十个创业的，能成一个就不错了。
为什么成功率这么低？

因为创业成功需要的素质，
跟打工需要的素质，完全不一样。

## 共同特征

**1. 以为有钱就能成**
错。钱是必要条件，不是充分条件。

**2. 以为技术好就能成**
错。技术是好，但你要会卖、会管人。

**3. 以为勤奋就能成**
错。勤奋要有方向，方向错了，越勤奋越惨。

**4. 以为坚持就能成**
错。坚持要有底线，底线破了，越坚持越亏。

## 真正能成的

就一种人：
知道自己几斤几两，
知道自己能做什么、不能做什么，
懂得找人来补短板。

---

老骇
2026.03.23
""",
        "体制内": """
# 体制内的生存法则

## 老骇说

体制内的人，分两种：

一种是打算一辈子待着的，
一种是打算骑驴找马的。

这两种人，生存法则不一样。

## 一辈子待着的

法则一：别太显眼，也别太落后
法则二：跟对领导，比干好工作重要
法则三：评职称、升职级，要会经营
法则四：别把领导当朋友，别把同事当敌人

## 骑驴找马的

法则一：别让工作占用太多时间
法则二：利用体制内资源建立人脉
法则三：悄悄学技能，骑驴找马
法则四：一旦决定走，就干脆点

## 最怕的一种

就是"既想走，又不敢走"的人。
天天抱怨，又天天混日子。
这种人，在哪都不会有出头之日。

---

老骇
2026.03.23
"""
    }
    
    return insights.get(keyword, "未找到相关主题")


laohai_analyzer = LaohaiAnalyzer()
