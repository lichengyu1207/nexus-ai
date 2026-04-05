"""
命盘与房产综合决策服务
将命盘解读与房产建议深度结合
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class MingpanPropertyDecisionService:
    """命盘房产综合决策服务"""
    
    def __init__(self):
        self.element_directions = {
            "木": {
                "favorable": ["东方", "东南方", "南方"],
                "unfavorable": ["西方", "西北方"],
                "cities": ["杭州", "苏州", "上海", "广州", "深圳", "南京"],
                "features": ["绿化好", "环境优美", "新兴产业", "教育配套"],
                "colors": ["绿色", "青色"]
            },
            "火": {
                "favorable": ["南方", "东南方", "东方"],
                "unfavorable": ["北方", "西北方"],
                "cities": ["广州", "深圳", "厦门", "海口", "南宁"],
                "features": ["阳光充足", "商业繁华", "交通便利"],
                "colors": ["红色", "紫色"]
            },
            "土": {
                "favorable": ["中央", "西南方", "东北方"],
                "unfavorable": ["东方", "东南方"],
                "cities": ["成都", "重庆", "武汉", "长沙", "郑州"],
                "features": ["地势平坦", "配套成熟", "交通便利"],
                "colors": ["黄色", "棕色"]
            },
            "金": {
                "favorable": ["西方", "西北方", "北方"],
                "unfavorable": ["南方", "东南方"],
                "cities": ["北京", "天津", "西安", "兰州", "乌鲁木齐"],
                "features": ["金融中心", "政府机构", "高端社区"],
                "colors": ["白色", "金色"]
            },
            "水": {
                "favorable": ["北方", "西方", "西北方"],
                "unfavorable": ["西南方", "东北方"],
                "cities": ["北京", "大连", "青岛", "哈尔滨", "沈阳"],
                "features": ["临水", "智慧产业", "科研机构"],
                "colors": ["黑色", "蓝色"]
            }
        }
        
        self.star_traits = {
            "天机": {
                "career": ["策划", "咨询", "教育", "知识付费"],
                "wealth": "正财型，靠专业积累",
                "housing": "适合文化氛围浓、知识密集的城市",
                "advice": "多思少行是短板，需要外力推动落地"
            },
            "紫微": {
                "career": ["管理", "创业", "政府", "大型企业"],
                "wealth": "偏财型，靠机会和资源",
                "housing": "适合有规范治理、大型企业多的城市",
                "advice": "有领导潜力，需要完成从执行到管理的转变"
            },
            "太阳": {
                "career": ["公职", "教育", "传媒", "公益"],
                "wealth": "正财型，靠名声和影响力",
                "housing": "适合阳光充足、发展前景好的城市",
                "advice": "适合在台前发展，不宜幕后"
            },
            "太阴": {
                "career": ["财务", "艺术", "设计", "房产"],
                "wealth": "正财型，靠积累和稳健投资",
                "housing": "适合环境优美、生活节奏慢的城市",
                "advice": "适合稳健投资，不宜冒险"
            },
            "贪狼": {
                "career": ["销售", "娱乐", "餐饮", "人脉行业"],
                "wealth": "偏财型，靠机会和社交",
                "housing": "适合商业繁华、人脉资源多的城市",
                "advice": "容易贪多，需要专注一个赛道"
            },
            "巨门": {
                "career": ["律师", "教师", "传媒", "咨询"],
                "wealth": "正财型，靠口才和专业",
                "housing": "适合教育资源丰富、法治环境好的城市",
                "advice": "口才好但容易得罪人，注意人际"
            },
            "天相": {
                "career": ["行政", "人事", "金融", "服务"],
                "wealth": "正财型，靠稳定职业",
                "housing": "适合配套成熟、生活便利的城市",
                "advice": "适合在规范组织中发展"
            },
            "天梁": {
                "career": ["医疗", "教育", "公益", "顾问"],
                "wealth": "正财型，靠专业和口碑",
                "housing": "适合医疗教育资源丰富的城市",
                "advice": "在外地发展容易遇贵人"
            },
            "七杀": {
                "career": ["军警", "体育", "创业", "技术"],
                "wealth": "偏财型，靠胆量和行动",
                "housing": "适合竞争激烈、机会多的城市",
                "advice": "行动力强，但需要控制风险"
            },
            "破军": {
                "career": ["创新", "改革", "销售", "开拓"],
                "wealth": "偏财型，靠突破和变化",
                "housing": "适合新兴城市、发展中的区域",
                "advice": "适合打破常规，但需要稳定后方"
            }
        }
        
        self.city_profiles = {
            "杭州": {
                "element": "木",
                "features": ["互联网+", "文化", "教育", "宜居"],
                "avg_price": "3-5万/㎡",
                "suitable_patterns": ["天机", "太阴", "天梁"],
                "talent_policy": "人才引进补贴最高100万"
            },
            "苏州": {
                "element": "木",
                "features": ["制造业", "文化", "宜居", "教育"],
                "avg_price": "2-4万/㎡",
                "suitable_patterns": ["天机", "天相", "太阴"],
                "talent_policy": "人才购房补贴最高50万"
            },
            "上海": {
                "element": "木",
                "features": ["金融", "国际化", "教育", "医疗"],
                "avg_price": "5-10万/㎡",
                "suitable_patterns": ["紫微", "太阳", "贪狼"],
                "talent_policy": "落户政策宽松"
            },
            "广州": {
                "element": "火",
                "features": ["商贸", "包容", "美食", "机会多"],
                "avg_price": "3-5万/㎡",
                "suitable_patterns": ["贪狼", "七杀", "破军"],
                "talent_policy": "人才绿卡制度"
            },
            "深圳": {
                "element": "火",
                "features": ["科技", "创新", "年轻", "机会多"],
                "avg_price": "5-8万/㎡",
                "suitable_patterns": ["七杀", "破军", "紫微"],
                "talent_policy": "人才房优先购买"
            },
            "成都": {
                "element": "土",
                "features": ["宜居", "美食", "文化", "生活成本低"],
                "avg_price": "1.5-3万/㎡",
                "suitable_patterns": ["太阴", "天相", "天梁"],
                "talent_policy": "人才公寓优先购买"
            },
            "北京": {
                "element": "水",
                "features": ["政治", "教育", "医疗", "资源集中"],
                "avg_price": "6-10万/㎡",
                "suitable_patterns": ["紫微", "太阳", "天梁"],
                "talent_policy": "积分落户"
            },
            "南京": {
                "element": "木",
                "features": ["教育", "文化", "宜居", "历史"],
                "avg_price": "2.5-4万/㎡",
                "suitable_patterns": ["天机", "太阴", "天梁"],
                "talent_policy": "人才购房补贴"
            }
        }
    
    def analyze_comprehensive(
        self,
        mingpan_info: Dict[str, Any],
        budget: Dict[str, Any],
        requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        综合分析命盘与房产决策
        
        Args:
            mingpan_info: 命盘信息（主星、宫位、五行等）
            budget: 预算信息（总价范围、首付比例等）
            requirements: 其他需求（城市偏好、户型等）
            
        Returns:
            综合决策报告
        """
        mingpan_analysis = self._analyze_mingpan(mingpan_info)
        
        property_analysis = self._analyze_property_needs(
            mingpan_analysis, budget, requirements
        )
        
        city_recommendations = self._recommend_cities(
            mingpan_analysis, budget
        )
        
        timing_advice = self._analyze_timing(mingpan_info)
        
        report = self._generate_comprehensive_report(
            mingpan_analysis,
            property_analysis,
            city_recommendations,
            timing_advice
        )
        
        return {
            "mingpan_analysis": mingpan_analysis,
            "property_analysis": property_analysis,
            "city_recommendations": city_recommendations,
            "timing_advice": timing_advice,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_mingpan(self, mingpan_info: Dict) -> Dict:
        """分析命盘信息"""
        analysis = {
            "main_traits": [],
            "element": None,
            "wealth_type": None,
            "career_direction": [],
            "favorable_directions": [],
            "housing_preferences": []
        }
        
        main_stars = mingpan_info.get("main_stars", [])
        for star in main_stars:
            if star in self.star_traits:
                trait = self.star_traits[star]
                analysis["main_traits"].append({
                    "star": star,
                    "career": trait["career"],
                    "wealth": trait["wealth"],
                    "housing": trait["housing"],
                    "advice": trait["advice"]
                })
                analysis["career_direction"].extend(trait["career"])
                analysis["housing_preferences"].append(trait["housing"])
        
        element = mingpan_info.get("element", "木")
        analysis["element"] = element
        
        if element in self.element_directions:
            elem_info = self.element_directions[element]
            analysis["favorable_directions"] = elem_info["favorable"]
            analysis["unfavorable_directions"] = elem_info.get("unfavorable", [])
            analysis["favorable_cities"] = elem_info["cities"]
            analysis["housing_features"] = elem_info["features"]
        
        wealth_palace = mingpan_info.get("palaces", {}).get("财帛宫", {})
        if wealth_palace:
            stars = wealth_palace.get("stars", [])
            if "禄存" in stars or "太阴" in stars:
                analysis["wealth_type"] = "正财型"
            elif "贪狼" in stars or "破军" in stars:
                analysis["wealth_type"] = "偏财型"
            else:
                analysis["wealth_type"] = "正偏兼有"
        
        return analysis
    
    def _analyze_property_needs(
        self,
        mingpan_analysis: Dict,
        budget: Dict,
        requirements: Dict = None
    ) -> Dict:
        """分析房产需求"""
        analysis = {
            "budget_assessment": {},
            "location_preference": [],
            "property_type": [],
            "risk_level": "中等"
        }
        
        total_budget = budget.get("total", 200)
        income = budget.get("annual_income", 30)
        
        ratio = total_budget / income if income > 0 else 10
        if ratio <= 8:
            analysis["budget_assessment"]["level"] = "安全"
            analysis["budget_assessment"]["advice"] = "预算合理，可从容选择"
        elif ratio <= 10:
            analysis["budget_assessment"]["level"] = "适中"
            analysis["budget_assessment"]["advice"] = "预算略紧，需精打细算"
        else:
            analysis["budget_assessment"]["level"] = "风险"
            analysis["budget_assessment"]["advice"] = "预算偏高，需谨慎评估"
        
        wealth_type = mingpan_analysis.get("wealth_type", "正财型")
        if wealth_type == "正财型":
            analysis["risk_level"] = "保守"
            analysis["property_type"].append("成熟地段、配套齐全")
            analysis["property_type"].append("不求暴涨，但求保值")
        elif wealth_type == "偏财型":
            analysis["risk_level"] = "激进"
            analysis["property_type"].append("新兴区域、潜力板块")
            analysis["property_type"].append("可博取增值空间")
        else:
            analysis["risk_level"] = "中等"
            analysis["property_type"].append("核心区域+潜力板块组合")
        
        favorable_dirs = mingpan_analysis.get("favorable_directions", [])
        analysis["location_preference"] = favorable_dirs
        
        return analysis
    
    def _recommend_cities(
        self,
        mingpan_analysis: Dict,
        budget: Dict
    ) -> List[Dict]:
        """推荐城市"""
        recommendations = []
        
        element = mingpan_analysis.get("element", "木")
        main_traits = mingpan_analysis.get("main_traits", [])
        favorable_cities = mingpan_analysis.get("favorable_cities", [])
        
        total_budget = budget.get("total", 200)
        
        for city_name, city_info in self.city_profiles.items():
            if city_name not in favorable_cities:
                continue
            
            match_score = 0
            match_reasons = []
            
            if city_info["element"] == element:
                match_score += 30
                match_reasons.append(f"五行匹配（{element}）")
            
            for trait in main_traits:
                if trait["star"] in city_info["suitable_patterns"]:
                    match_score += 20
                    match_reasons.append(f"命星{trait['star']}适合")
            
            price_range = city_info["avg_price"]
            if total_budget >= 300:
                match_score += 20
            elif total_budget >= 200 and "3-5" in price_range:
                match_score += 15
            elif total_budget >= 100 and "1.5" in price_range:
                match_score += 15
            
            recommendations.append({
                "city": city_name,
                "match_score": match_score,
                "match_reasons": match_reasons,
                "avg_price": city_info["avg_price"],
                "features": city_info["features"],
                "talent_policy": city_info["talent_policy"],
                "element_match": city_info["element"] == element
            })
        
        recommendations.sort(key=lambda x: -x["match_score"])
        
        return recommendations[:5]
    
    def _analyze_timing(self, mingpan_info: Dict) -> Dict:
        """分析购房时机"""
        timing = {
            "current_phase": "",
            "favorable_years": [],
            "advice": ""
        }
        
        age = mingpan_info.get("age", 30)
        
        if age < 30:
            timing["current_phase"] = "试错期"
            timing["advice"] = "可以租房为主，积累资金和经验，30岁后再考虑买房"
        elif age < 40:
            timing["current_phase"] = "扎根期"
            timing["advice"] = "适合买房扎根，选择有发展潜力的城市和板块"
        else:
            timing["current_phase"] = "做局期"
            timing["advice"] = "可考虑改善型住房或投资性房产"
        
        return timing
    
    def _generate_comprehensive_report(
        self,
        mingpan_analysis: Dict,
        property_analysis: Dict,
        city_recommendations: List[Dict],
        timing_advice: Dict
    ) -> str:
        """生成综合报告"""
        element = mingpan_analysis.get("element", "木")
        wealth_type = mingpan_analysis.get("wealth_type", "正财型")
        favorable_dirs = mingpan_analysis.get("favorable_directions", [])
        main_traits = mingpan_analysis.get("main_traits", [])
        
        report = f"""# 命盘与房产综合决策报告

## 一、命盘核心解读

**五行属性**：{element}
**财运类型**：{wealth_type}
**有利方位**：{', '.join(favorable_dirs)}

### 主星特质
"""
        
        for trait in main_traits:
            report += f"""
**{trait['star']}**：
- 适合职业：{', '.join(trait['career'])}
- 财运特点：{trait['wealth']}
- 住房偏好：{trait['housing']}
- 老骇建议：{trait['advice']}
"""
        
        report += f"""
## 二、房产决策建议

### 方位选择
根据您的五行{element}属性，优先考虑**{', '.join(favorable_dirs)}**方向的城市。

### 城市推荐
"""
        
        for i, city in enumerate(city_recommendations[:3], 1):
            report += f"""
**{i}. {city['city']}**
- 匹配度：{city['match_score']}分
- 匹配理由：{', '.join(city['match_reasons'])}
- 均价：{city['avg_price']}
- 城市特点：{', '.join(city['features'])}
- 人才政策：{city['talent_policy']}
"""
        
        risk_level = property_analysis.get("risk_level", "中等")
        budget_level = property_analysis.get("budget_assessment", {}).get("level", "适中")
        
        report += f"""
### 风险评估
- 风险等级：{risk_level}
- 预算评估：{budget_level}

## 三、购房时机

**当前阶段**：{timing_advice['current_phase']}
**建议**：{timing_advice['advice']}

## 四、周瑜总结

您的命盘像一张地图，已经标出了天赋方向——{main_traits[0]['career'][0] if main_traits else '待分析'}为主，{wealth_type}，选{favorable_dirs[0] if favorable_dirs else '东南'}方向城市，买稳健资产。

## 五、陆逊补充

地图画好了，路怎么走，还得靠你自己。我们平台会帮您记住每一次选择，用海马体记忆系统为您存档。

---

**房都督平台**：如需进一步细化，我们可以根据您的具体八字推演更精确的买房时间节点，接入真实房产数据筛选房源。
"""
        
        return report


mingpan_property_decision_service = MingpanPropertyDecisionService()
