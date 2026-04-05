from typing import Dict, Any, List
import asyncio
import json
from app.ai_agents.base_agent import BaseAgent
from app.ai_agents.data_lineage import lineage_tracker


class ReportGeneratorAgent(BaseAgent):
    """Agent specialized in generating structured property analysis reports"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "Agent specialized in generating structured property analysis reports"
        self.report_template = kwargs.get("report_template", "detailed")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation task"""
        try:
            # 发布开始事件
            self.publish_start_event(task)
            
            # Extract verification results from task
            verification_result = task.get("verification_result", {})
            verification_results = verification_result.get("verification_results", {})
            verification_report = verification_result.get("verification_report", {})
            
            # Get verified properties
            verified_properties = verification_results.get("verified_properties", [])
            
            # 发布进度事件
            self.publish_progress_event(0.1, "开始生成房产分析报告")
            
            # Generate report for each property
            property_reports = []
            report_stats = {
                "total_properties": len(verified_properties),
                "generated_reports": 0,
                "failed_reports": 0
            }
            
            total_properties = len(verified_properties)
            for i, property_data in enumerate(verified_properties):
                try:
                    # 发布进度事件
                    if total_properties > 0:
                        progress = 0.1 + (i / total_properties) * 0.7
                        self.publish_progress_event(progress, f"正在生成第 {i+1} 个房产的报告")
                    
                    report = await self.generate_property_report(property_data)
                    property_reports.append(report)
                    report_stats["generated_reports"] += 1
                except Exception as e:
                    report_stats["failed_reports"] += 1
                    print(f"Failed to generate report for property {i}: {str(e)}")
            
            # 发布进度事件
            self.publish_progress_event(0.8, "正在生成汇总报告")
            
            # Generate summary report
            summary_report = await self.generate_summary_report(
                property_reports,
                verification_report,
                report_stats
            )
            
            result = {
                "property_reports": property_reports,
                "summary_report": summary_report,
                "report_stats": report_stats
            }
            
            # 发布完成事件
            self.publish_complete_event(result)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            # 发布错误事件
            self.publish_error_event(str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_property_report(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed report for a single property"""
        # Extract property information
        name = property_data.get("name", "未知房产")
        address = property_data.get("address", "未知地址")
        price = property_data.get("price", 0)
        area = property_data.get("area", 0)
        property_type = property_data.get("property_type", "未知类型")
        age = property_data.get("age", 0)
        features = property_data.get("features", [])
        price_per_square = property_data.get("price_per_square", 0)
        
        # Get verification metadata
        verification_metadata = property_data.get("_verification_metadata", {})
        confidence = verification_metadata.get("confidence", 0.7)
        sources = verification_metadata.get("sources", ["unknown"])
        
        # Generate report sections
        report = {
            "property_name": name,
            "address": address,
            "report_id": f"REPORT_{hash(name + address)}",
            "generated_at": asyncio.get_event_loop().time(),
            "confidence_score": confidence,
            "data_sources": sources,
            "sections": {
                "basic_info": await self.generate_basic_info_section(property_data),
                "price_analysis": await self.generate_price_analysis_section(property_data),
                "market_position": await self.generate_market_position_section(property_data),
                "investment_potential": await self.generate_investment_potential_section(property_data),
                "risk_assessment": await self.generate_risk_assessment_section(property_data),
                "recommendations": await self.generate_recommendations_section(property_data)
            },
            "summary": self.generate_report_summary(property_data),
            "metadata": {
                "report_template": self.report_template,
                "verification_status": verification_metadata.get("verification_status", "unknown"),
                "data_quality": self.assess_data_quality(property_data)
            }
        }
        
        # Track data lineage transformation for report
        if "_lineage_node_id" in property_data:
            input_node_id = property_data["_lineage_node_id"]
            output_node_id = lineage_tracker.track_transformation(
                [input_node_id],
                report,
                "report_generation",
                self.name,
                {
                    "report_id": report["report_id"],
                    "property_name": name,
                    "address": address,
                    "confidence_score": confidence,
                    "sections_count": len(report["sections"]),
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
            report["_lineage_node_id"] = output_node_id
            
            # Track usage of the property data in report generation
            lineage_tracker.track_usage(
                input_node_id,
                "report_generation",
                {
                    "report_id": report["report_id"],
                    "agent": self.name,
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
        else:
            # Create new lineage node if no existing one
            output_node_id = lineage_tracker.create_data_node(
                report,
                "report",
                {
                    "agent": self.name,
                    "generation_timestamp": asyncio.get_event_loop().time(),
                    "report_id": report["report_id"],
                    "property_name": name,
                    "address": address
                }
            )
            report["_lineage_node_id"] = output_node_id
        
        return report
    
    async def generate_basic_info_section(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic information section"""
        return {
            "title": "基本信息",
            "content": {
                "房产名称": property_data.get("name", "未知"),
                "地址": property_data.get("address", "未知"),
                "房产类型": property_data.get("property_type", "未知"),
                "建筑面积": f"{property_data.get('area', 0)}㎡",
                "房龄": f"{property_data.get('age', 0)}年",
                "总价": f"{property_data.get('price', 0):,.2f}元",
                "单价": f"{property_data.get('price_per_square', 0):,.2f}元/㎡",
                "特色": property_data.get('features', [])
            }
        }
    
    async def generate_price_analysis_section(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate price analysis section"""
        price = property_data.get("price", 0)
        area = property_data.get("area", 0)
        price_per_square = property_data.get("price_per_square", 0)
        
        # Simulate market comparison
        market_average_price = self.simulate_market_average(property_data)
        price_deviation = ((price_per_square - market_average_price) / market_average_price) * 100
        
        return {
            "title": "价格分析",
            "content": {
                "总价": f"{price:,.2f}元",
                "单价": f"{price_per_square:,.2f}元/㎡",
                "市场均价": f"{market_average_price:,.2f}元/㎡",
                "价格偏差": f"{price_deviation:.2f}%",
                "价格评价": self.evaluate_price(price_deviation),
                "定价建议": self.generate_pricing_suggestion(price_deviation)
            }
        }
    
    async def generate_market_position_section(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market position section"""
        property_type = property_data.get("property_type", "未知")
        age = property_data.get("age", 0)
        features = property_data.get("features", [])
        
        return {
            "title": "市场定位",
            "content": {
                "房产类型": property_type,
                "房龄定位": self.evaluate_age_position(age),
                "特色优势": self.identify_feature_advantages(features),
                "目标客群": self.identify_target_audience(property_type, age, features),
                "市场竞争力": self.evaluate_market_competitiveness(property_data)
            }
        }
    
    async def generate_investment_potential_section(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate investment potential section"""
        property_type = property_data.get("property_type", "未知")
        age = property_data.get("age", 0)
        price_per_square = property_data.get("price_per_square", 0)
        features = property_data.get("features", [])
        
        return {
            "title": "投资潜力",
            "content": {
                "投资类型": self.recommend_investment_type(property_type),
                "预期回报率": self.estimate_return_rate(property_type, age),
                "升值潜力": self.evaluate_appreciation_potential(features),
                "租赁前景": self.evaluate_rental_prospects(property_type, features),
                "投资建议": self.generate_investment_advice(property_type, age, features)
            }
        }
    
    async def generate_risk_assessment_section(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment section"""
        age = property_data.get("age", 0)
        property_type = property_data.get("property_type", "未知")
        price_per_square = property_data.get("price_per_square", 0)
        
        return {
            "title": "风险评估",
            "content": {
                "房龄风险": self.assess_age_risk(age),
                "类型风险": self.assess_type_risk(property_type),
                "价格风险": self.assess_price_risk(price_per_square),
                "市场风险": self.assess_market_risk(),
                "风险等级": self.calculate_overall_risk(age, property_type, price_per_square)
            }
        }
    
    async def generate_recommendations_section(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations section"""
        property_type = property_data.get("property_type", "未知")
        age = property_data.get("age", 0)
        features = property_data.get("features", [])
        price_per_square = property_data.get("price_per_square", 0)
        
        return {
            "title": "建议与对策",
            "content": {
                "购买建议": self.generate_purchase_advice(property_type, age, price_per_square),
                "谈判策略": self.generate_negotiation_strategy(price_per_square),
                "装修建议": self.generate_renovation_suggestions(property_type, age),
                "持有策略": self.generate_holding_strategy(property_type),
                "注意事项": self.generate_cautions(features)
            }
        }
    
    async def generate_summary_report(self, property_reports: List[Dict[str, Any]], 
                                   verification_report: Dict[str, Any],
                                   report_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report for all properties"""
        # Calculate average values
        if property_reports:
            avg_price = sum(r["sections"]["price_analysis"]["content"]["单价"].replace('元/㎡', '').replace(',', '')
                          for r in property_reports if "price_analysis" in r["sections"])
            avg_price = avg_price / len(property_reports) if property_reports else 0
            
            # Count property types
            type_counts = {}
            for report in property_reports:
                prop_type = report["sections"]["basic_info"]["content"]["房产类型"]
                type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
        else:
            avg_price = 0
            type_counts = {}
        
        return {
            "title": "房产分析汇总报告",
            "generated_at": asyncio.get_event_loop().time(),
            "summary": {
                "分析房产数量": report_stats["total_properties"],
                "生成报告数量": report_stats["generated_reports"],
                "平均单价": f"{avg_price:,.2f}元/㎡",
                "房产类型分布": type_counts,
                "数据一致性评分": f"{verification_report.get('consistency_score', 0):.2f}",
                "数据来源": verification_report.get('summary', '未知')
            },
            "conclusions": self.generate_overall_conclusions(property_reports),
            "recommendations": self.generate_overall_recommendations(property_reports),
            "report_quality": self.assess_report_quality(report_stats)
        }
    
    def generate_report_summary(self, property_data: Dict[str, Any]) -> str:
        """Generate a summary of the property report"""
        name = property_data.get("name", "未知房产")
        address = property_data.get("address", "未知地址")
        price = property_data.get("price", 0)
        area = property_data.get("area", 0)
        property_type = property_data.get("property_type", "未知类型")
        features = property_data.get("features", [])
        
        feature_str = "、".join(features[:3]) if features else "无特色"
        
        return f"{name}（{address}）是一处{property_type}，建筑面积{area}㎡，总价{price:,.2f}元。{feature_str}。"
    
    def simulate_market_average(self, property_data: Dict[str, Any]) -> float:
        """Simulate market average price based on property type"""
        property_type = property_data.get("property_type", "未知")
        base_prices = {
            "住宅": 10000,
            "公寓": 8000,
            "别墅": 15000,
            "商铺": 12000,
            "写字楼": 9000
        }
        return base_prices.get(property_type, 8000)
    
    def evaluate_price(self, deviation: float) -> str:
        """Evaluate price based on deviation from market average"""
        if deviation < -10:
            return "价格偏低"
        elif deviation < -5:
            return "价格略低"
        elif deviation < 5:
            return "价格合理"
        elif deviation < 10:
            return "价格略高"
        else:
            return "价格偏高"
    
    def generate_pricing_suggestion(self, deviation: float) -> str:
        """Generate pricing suggestion based on price deviation"""
        if deviation > 10:
            return "建议议价空间较大，可尝试降价10%以上"
        elif deviation > 5:
            return "建议适度议价，可尝试降价5-10%"
        elif deviation > -5:
            return "价格合理，议价空间有限"
        else:
            return "价格具有优势，建议尽快决策"
    
    def evaluate_age_position(self, age: int) -> str:
        """Evaluate property age position"""
        if age <= 5:
            return "新房"
        elif age <= 10:
            return "次新房"
        elif age <= 20:
            return "成熟房"
        else:
            return "老旧房"
    
    def identify_feature_advantages(self, features: List[str]) -> List[str]:
        """Identify feature advantages"""
        advantage_keywords = ["近地铁", "带学位", "精装修", "拎包入住", "南北通透", "采光好", "安静"]
        return [f for f in features if any(keyword in f for keyword in advantage_keywords)]
    
    def identify_target_audience(self, property_type: str, age: int, features: List[str]) -> List[str]:
        """Identify target audience"""
        audience = []
        
        if property_type == "住宅":
            if age <= 10:
                audience.append("刚需购房者")
                audience.append("改善型购房者")
            if any("带学位" in f for f in features):
                audience.append("有学龄儿童的家庭")
            if any("近地铁" in f for f in features):
                audience.append("通勤族")
        elif property_type == "公寓":
            audience.append("单身白领")
            audience.append("投资者")
        elif property_type == "别墅":
            audience.append("高端改善型购房者")
            audience.append("高净值人群")
        
        return audience
    
    def evaluate_market_competitiveness(self, property_data: Dict[str, Any]) -> str:
        """Evaluate market competitiveness"""
        features = property_data.get("features", [])
        age = property_data.get("age", 0)
        price_per_square = property_data.get("price_per_square", 0)
        
        # Simulate market average
        market_avg = self.simulate_market_average(property_data)
        price_score = 1 if price_per_square < market_avg * 1.1 else 0
        age_score = 1 if age <= 10 else 0
        feature_score = min(len([f for f in features if any(k in f for k in ["近地铁", "带学位", "精装修"])]) / 3, 1)
        
        total_score = price_score + age_score + feature_score
        
        if total_score >= 2.5:
            return "竞争力强"
        elif total_score >= 1.5:
            return "竞争力中等"
        else:
            return "竞争力弱"
    
    def recommend_investment_type(self, property_type: str) -> str:
        """Recommend investment type based on property type"""
        recommendations = {
            "住宅": "长期持有或租赁",
            "公寓": "短期租赁",
            "别墅": "长期持有",
            "商铺": "商业租赁",
            "写字楼": "办公租赁"
        }
        return recommendations.get(property_type, "待定")
    
    def estimate_return_rate(self, property_type: str, age: int) -> str:
        """Estimate return rate based on property type and age"""
        base_rates = {
            "住宅": "3-5%",
            "公寓": "4-6%",
            "别墅": "2-4%",
            "商铺": "5-8%",
            "写字楼": "4-6%"
        }
        
        rate = base_rates.get(property_type, "3-5%")
        if age > 20:
            rate = rate.replace("5", "4").replace("6", "5").replace("8", "6")
        
        return rate
    
    def evaluate_appreciation_potential(self, features: List[str]) -> str:
        """Evaluate appreciation potential based on features"""
        appreciation_factors = ["近地铁", "带学位", "规划中", "发展中"]
        factor_count = sum(1 for f in features if any(factor in f for factor in appreciation_factors))
        
        if factor_count >= 2:
            return "升值潜力大"
        elif factor_count >= 1:
            return "升值潜力中等"
        else:
            return "升值潜力有限"
    
    def evaluate_rental_prospects(self, property_type: str, features: List[str]) -> str:
        """Evaluate rental prospects"""
        if property_type in ["公寓", "住宅"]:
            if any("近地铁" in f for f in features):
                return "租赁前景良好"
            else:
                return "租赁前景一般"
        elif property_type in ["商铺", "写字楼"]:
            return "租赁前景取决于位置"
        else:
            return "租赁前景一般"
    
    def generate_investment_advice(self, property_type: str, age: int, features: List[str]) -> str:
        """Generate investment advice"""
        if property_type == "住宅":
            if age <= 10:
                return "建议投资，长期持有"
            else:
                return "谨慎投资，关注价格"
        elif property_type == "公寓":
            return "适合短期投资，关注租赁市场"
        elif property_type == "商铺":
            return "需谨慎评估，关注人流量和商圈发展"
        else:
            return "建议根据具体情况评估"
    
    def assess_age_risk(self, age: int) -> str:
        """Assess age-related risk"""
        if age <= 10:
            return "低风险"
        elif age <= 20:
            return "中等风险"
        else:
            return "高风险，需关注房屋状况"
    
    def assess_type_risk(self, property_type: str) -> str:
        """Assess type-related risk"""
        risk_levels = {
            "住宅": "低风险",
            "公寓": "中等风险",
            "别墅": "低风险",
            "商铺": "高风险",
            "写字楼": "中等风险"
        }
        return risk_levels.get(property_type, "中等风险")
    
    def assess_price_risk(self, price_per_square: float) -> str:
        """Assess price-related risk"""
        if price_per_square > 20000:
            return "高风险，价格可能存在泡沫"
        elif price_per_square > 10000:
            return "中等风险"
        else:
            return "低风险"
    
    def assess_market_risk(self) -> str:
        """Assess general market risk"""
        # This would typically be based on actual market data
        return "中等风险，市场稳定"
    
    def calculate_overall_risk(self, age: int, property_type: str, price_per_square: float) -> str:
        """Calculate overall risk level"""
        age_risk = self.assess_age_risk(age)
        type_risk = self.assess_type_risk(property_type)
        price_risk = self.assess_price_risk(price_per_square)
        
        high_risk_count = sum(1 for r in [age_risk, type_risk, price_risk] if "高风险" in r)
        
        if high_risk_count >= 2:
            return "高风险"
        elif high_risk_count >= 1:
            return "中等风险"
        else:
            return "低风险"
    
    def generate_purchase_advice(self, property_type: str, age: int, price_per_square: float) -> str:
        """Generate purchase advice"""
        if property_type == "住宅":
            if age <= 10 and price_per_square < 15000:
                return "建议购买，性价比高"
            elif age <= 15 and price_per_square < 20000:
                return "可以购买，关注房屋状况"
            else:
                return "谨慎购买，建议议价"
        elif property_type == "公寓":
            return "适合投资，关注租赁回报率"
        else:
            return "建议根据具体需求评估"
    
    def generate_negotiation_strategy(self, price_per_square: float) -> str:
        """Generate negotiation strategy"""
        if price_per_square > 20000:
            return "建议议价10-15%，重点关注价格合理性"
        elif price_per_square > 15000:
            return "建议议价5-10%，关注房屋细节问题"
        else:
            return "议价空间有限，建议关注其他条款"
    
    def generate_renovation_suggestions(self, property_type: str, age: int) -> List[str]:
        """Generate renovation suggestions"""
        suggestions = []
        
        if age > 15:
            suggestions.append("检查水电管线，必要时更换")
            suggestions.append("更新厨卫设施")
        
        if property_type == "住宅":
            suggestions.append("优化空间布局")
            suggestions.append("提升收纳空间")
        elif property_type == "公寓":
            suggestions.append("现代简约风格装修")
            suggestions.append("注重功能性设计")
        
        return suggestions
    
    def generate_holding_strategy(self, property_type: str) -> str:
        """Generate holding strategy"""
        strategies = {
            "住宅": "长期持有，关注市场变化",
            "公寓": "可考虑3-5年持有后出售或长期出租",
            "别墅": "长期持有，作为资产配置",
            "商铺": "关注商圈发展，适时调整",
            "写字楼": "根据市场情况，5-8年评估一次"
        }
        return strategies.get(property_type, "根据市场情况调整")
    
    def generate_cautions(self, features: List[str]) -> List[str]:
        """Generate cautions"""
        cautions = []
        
        if not any("近地铁" in f for f in features):
            cautions.append("交通便利性可能不足")
        if not any("带学位" in f for f in features):
            cautions.append("需确认学区情况")
        if any("老旧" in f for f in features):
            cautions.append("需重点检查房屋结构和设施")
        
        return cautions
    
    def generate_overall_conclusions(self, property_reports: List[Dict[str, Any]]) -> List[str]:
        """Generate overall conclusions"""
        if not property_reports:
            return ["未生成足够的房产报告"]
        
        conclusions = []
        
        # Analyze price trends
        prices = [float(r["sections"]["price_analysis"]["content"]["单价"].replace('元/㎡', '').replace(',', ''))
                 for r in property_reports if "price_analysis" in r["sections"]]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        if avg_price > 15000:
            conclusions.append("分析的房产整体价格偏高")
        elif avg_price > 10000:
            conclusions.append("分析的房产价格处于中等水平")
        else:
            conclusions.append("分析的房产价格相对较低")
        
        # Analyze property types
        type_counts = {}
        for report in property_reports:
            prop_type = report["sections"]["basic_info"]["content"]["房产类型"]
            type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
        
        dominant_type = max(type_counts, key=type_counts.get)
        conclusions.append(f"{dominant_type}是主要的房产类型，占比{type_counts[dominant_type]/len(property_reports)*100:.1f}%")
        
        return conclusions
    
    def generate_overall_recommendations(self, property_reports: List[Dict[str, Any]]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        if not property_reports:
            return ["无法生成推荐"]
        
        recommendations.append("建议根据个人需求和预算选择合适的房产类型")
        recommendations.append("关注房产的核心优势，如交通、教育等配套")
        recommendations.append("购买前务必实地考察，了解房屋实际状况")
        recommendations.append("关注市场动态，选择合适的购房时机")
        
        return recommendations
    
    def assess_data_quality(self, property_data: Dict[str, Any]) -> str:
        """Assess data quality"""
        required_fields = ["name", "address", "price", "area", "property_type", "age"]
        present_fields = [f for f in required_fields if f in property_data and property_data[f]]
        
        quality_score = len(present_fields) / len(required_fields)
        
        if quality_score >= 0.8:
            return "数据质量高"
        elif quality_score >= 0.6:
            return "数据质量中等"
        else:
            return "数据质量较低"
    
    def assess_report_quality(self, report_stats: Dict[str, Any]) -> str:
        """Assess overall report quality"""
        if report_stats["failed_reports"] == 0:
            return "报告质量优秀"
        elif report_stats["failed_reports"] / report_stats["total_properties"] < 0.1:
            return "报告质量良好"
        else:
            return "报告质量一般"
