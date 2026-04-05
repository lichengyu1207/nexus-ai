from typing import Dict, Any, List
import asyncio
import statistics
from app.ai_agents.base_agent import BaseAgent


class MarketAnalystAgent(BaseAgent):
    """Agent specialized in analyzing property market data and providing insights"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "Agent specialized in analyzing property market data and providing insights"
        self.metrics = [
            "price_trend",
            "supply_demand",
            "investment_return",
            "market_sentiment",
            "value_assessment"
        ]
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market analysis task"""
        try:
            # 发布开始事件
            self.publish_start_event(task)
            
            # Extract verified data from task
            verification_result = task.get("verification_result", {})
            verified_properties = verification_result.get("verified_properties", [])
            
            if not verified_properties:
                # 如果没有验证数据，尝试从其他字段获取
                verified_properties = self._extract_properties_from_task(task)
            
            # 发布进度事件
            self.publish_progress_event(0.2, "开始分析市场数据")
            
            # Analyze market data
            market_analysis = await self.analyze_market(verified_properties)
            
            # 发布进度事件
            self.publish_progress_event(0.6, "正在生成市场分析报告")
            
            # Generate analysis report
            analysis_report = {
                "properties_count": len(verified_properties),
                "market_analysis": market_analysis,
                "metadata": {
                    "analysis_time": asyncio.get_event_loop().time(),
                    "metrics_analyzed": self.metrics,
                    "confidence_score": self.calculate_confidence(market_analysis, verified_properties)
                }
            }
            
            # 发布完成事件
            self.publish_complete_event(analysis_report)
            
            return {
                "success": True,
                "result": analysis_report
            }
            
        except Exception as e:
            # 发布错误事件
            self.publish_error_event(str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_market(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market data and provide insights"""
        analysis = {}
        
        # 分析价格趋势
        price_trend = await self.analyze_price_trend(properties)
        if price_trend:
            analysis["price_trend"] = price_trend
        
        # 分析供需情况
        supply_demand = await self.analyze_supply_demand(properties)
        if supply_demand:
            analysis["supply_demand"] = supply_demand
        
        # 分析投资回报率
        investment_return = await self.analyze_investment_return(properties)
        if investment_return:
            analysis["investment_return"] = investment_return
        
        # 分析市场情绪
        market_sentiment = await self.analyze_market_sentiment(properties)
        if market_sentiment:
            analysis["market_sentiment"] = market_sentiment
        
        # 分析价值评估
        value_assessment = await self.analyze_value_assessment(properties)
        if value_assessment:
            analysis["value_assessment"] = value_assessment
        
        return analysis
    
    async def analyze_price_trend(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price trends based on property data"""
        price_trend = {}
        
        # 计算平均价格
        prices = []
        price_per_square = []
        
        for prop in properties:
            if "price" in prop and prop["price"] > 0:
                prices.append(prop["price"])
            if "price_per_square" in prop and prop["price_per_square"] > 0:
                price_per_square.append(prop["price_per_square"])
        
        if prices:
            price_trend["average_price"] = statistics.mean(prices)
            price_trend["median_price"] = statistics.median(prices)
            price_trend["price_std_dev"] = statistics.stdev(prices) if len(prices) > 1 else 0
        
        if price_per_square:
            price_trend["average_price_per_square"] = statistics.mean(price_per_square)
            price_trend["median_price_per_square"] = statistics.median(price_per_square)
            price_trend["price_per_square_std_dev"] = statistics.stdev(price_per_square) if len(price_per_square) > 1 else 0
        
        # 分析价格分布
        if prices:
            price_trend["price_distribution"] = self._analyze_price_distribution(prices)
        
        # 分析价格与房龄关系
        price_age_correlation = self._analyze_price_age_correlation(properties)
        if price_age_correlation:
            price_trend["price_age_correlation"] = price_age_correlation
        
        return price_trend
    
    async def analyze_supply_demand(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze supply and demand dynamics"""
        supply_demand = {}
        
        # 分析房源类型分布
        property_types = {}
        for prop in properties:
            prop_type = prop.get("property_type", "未知")
            property_types[prop_type] = property_types.get(prop_type, 0) + 1
        supply_demand["property_type_distribution"] = property_types
        
        # 分析面积分布
        area_distribution = self._analyze_area_distribution(properties)
        if area_distribution:
            supply_demand["area_distribution"] = area_distribution
        
        # 分析房龄分布
        age_distribution = self._analyze_age_distribution(properties)
        if age_distribution:
            supply_demand["age_distribution"] = age_distribution
        
        # 估算供需平衡
        supply_demand["supply_estimate"] = len(properties)
        # 这里可以添加更复杂的供需分析逻辑
        
        return supply_demand
    
    async def analyze_investment_return(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze investment return potential"""
        investment_return = {}
        
        # 计算潜在租金回报率
        rental_yields = []
        for prop in properties:
            if "price" in prop and prop["price"] > 0:
                # 估算租金（简化模型）
                estimated_rent = self._estimate_monthly_rent(prop)
                if estimated_rent > 0:
                    annual_rent = estimated_rent * 12
                    yield_rate = (annual_rent / prop["price"]) * 100
                    rental_yields.append(yield_rate)
        
        if rental_yields:
            investment_return["average_rental_yield"] = statistics.mean(rental_yields)
            investment_return["median_rental_yield"] = statistics.median(rental_yields)
        
        # 分析投资类型适合度
        investment_return["investment_fitness"] = self._analyze_investment_fitness(properties)
        
        # 估算投资回收期
        if rental_yields:
            average_yield = statistics.mean(rental_yields)
            if average_yield > 0:
                investment_return["estimated_payback_period"] = 100 / average_yield
        
        return investment_return
    
    async def analyze_market_sentiment(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market sentiment"""
        market_sentiment = {}
        
        # 基于价格和房龄分析市场情绪
        sentiment_score = self._calculate_sentiment_score(properties)
        market_sentiment["sentiment_score"] = sentiment_score
        market_sentiment["sentiment_label"] = self._get_sentiment_label(sentiment_score)
        
        # 分析市场活跃度
        market_sentiment["market_activity"] = self._analyze_market_activity(properties)
        
        return market_sentiment
    
    async def analyze_value_assessment(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze property value assessment"""
        value_assessment = {}
        
        # 计算价值评分
        property_values = []
        for prop in properties:
            value_score = self._calculate_property_value_score(prop)
            property_values.append({
                "property_id": prop.get("id", "unknown"),
                "value_score": value_score,
                "value_label": self._get_value_label(value_score)
            })
        
        value_assessment["property_values"] = property_values
        
        # 分析价值分布
        if property_values:
            scores = [pv["value_score"] for pv in property_values]
            value_assessment["average_value_score"] = statistics.mean(scores)
            value_assessment["value_distribution"] = self._analyze_value_distribution(scores)
        
        return value_assessment
    
    def _extract_properties_from_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract properties from task if no verification result"""
        properties = []
        
        # 尝试从不同字段提取
        if "cleaned_properties" in task:
            properties = task["cleaned_properties"]
        elif "collected_data" in task:
            properties = task["collected_data"].get("data", [])
        
        return properties
    
    def _analyze_price_distribution(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze price distribution"""
        if not prices:
            return {}
        
        # 简单的价格分布分析
        sorted_prices = sorted(prices)
        distribution = {
            "min": sorted_prices[0],
            "max": sorted_prices[-1],
            "percentiles": {
                "25th": sorted_prices[int(len(sorted_prices) * 0.25)],
                "50th": sorted_prices[int(len(sorted_prices) * 0.5)],
                "75th": sorted_prices[int(len(sorted_prices) * 0.75)]
            }
        }
        
        return distribution
    
    def _analyze_price_age_correlation(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze correlation between price and age"""
        price_age_pairs = []
        for prop in properties:
            if "price" in prop and "age" in prop:
                price_age_pairs.append((prop["price"], prop["age"]))
        
        if len(price_age_pairs) < 2:
            return {}
        
        # 简单的相关性分析
        prices = [p[0] for p in price_age_pairs]
        ages = [p[1] for p in price_age_pairs]
        
        # 计算相关系数
        correlation = self._calculate_correlation(prices, ages)
        
        return {
            "correlation_coefficient": correlation,
            "trend": "negative" if correlation < -0.3 else "positive" if correlation > 0.3 else "neutral"
        }
    
    def _analyze_area_distribution(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze area distribution"""
        areas = []
        for prop in properties:
            if "area" in prop and prop["area"] > 0:
                areas.append(prop["area"])
        
        if not areas:
            return {}
        
        sorted_areas = sorted(areas)
        return {
            "min": sorted_areas[0],
            "max": sorted_areas[-1],
            "average": statistics.mean(areas),
            "median": statistics.median(areas)
        }
    
    def _analyze_age_distribution(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze age distribution"""
        ages = []
        for prop in properties:
            if "age" in prop and prop["age"] > 0:
                ages.append(prop["age"])
        
        if not ages:
            return {}
        
        sorted_ages = sorted(ages)
        return {
            "min": sorted_ages[0],
            "max": sorted_ages[-1],
            "average": statistics.mean(ages),
            "median": statistics.median(ages)
        }
    
    def _estimate_monthly_rent(self, property_data: Dict[str, Any]) -> float:
        """Estimate monthly rent based on property data"""
        # 简化的租金估算模型
        price = property_data.get("price", 0)
        area = property_data.get("area", 0)
        age = property_data.get("age", 0)
        
        if price <= 0:
            return 0
        
        # 基于房价的租金估算（年租金约为房价的2-3%）
        annual_rent = price * 0.025
        monthly_rent = annual_rent / 12
        
        # 根据房龄调整
        if age > 20:
            monthly_rent *= 0.9
        elif age < 5:
            monthly_rent *= 1.1
        
        return monthly_rent
    
    def _analyze_investment_fitness(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze investment fitness for different property types"""
        fitness = {}
        
        # 按类型分析投资适合度
        type_fitness = {}
        for prop in properties:
            prop_type = prop.get("property_type", "未知")
            if prop_type not in type_fitness:
                type_fitness[prop_type] = []
            
            # 计算适合度评分
            fitness_score = self._calculate_investment_fitness_score(prop)
            type_fitness[prop_type].append(fitness_score)
        
        # 计算每种类型的平均适合度
        for prop_type, scores in type_fitness.items():
            if scores:
                fitness[prop_type] = {
                    "average_fitness": statistics.mean(scores),
                    "count": len(scores)
                }
        
        return fitness
    
    def _calculate_investment_fitness_score(self, property_data: Dict[str, Any]) -> float:
        """Calculate investment fitness score"""
        score = 0.0
        
        # 基于价格、面积、房龄等因素计算
        price = property_data.get("price", 0)
        area = property_data.get("area", 0)
        age = property_data.get("age", 0)
        
        # 简单的评分模型
        if price > 0 and area > 0:
            price_per_square = price / area
            # 价格适中的房产投资适合度更高
            if 10000 <= price_per_square <= 30000:
                score += 0.3
        
        # 房龄适中
        if 5 <= age <= 15:
            score += 0.3
        
        # 面积适中
        if 60 <= area <= 120:
            score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_sentiment_score(self, properties: List[Dict[str, Any]]) -> float:
        """Calculate market sentiment score"""
        if not properties:
            return 0.5
        
        # 基于价格趋势和房龄分析情绪
        price_age_correlation = self._analyze_price_age_correlation(properties)
        correlation = price_age_correlation.get("correlation_coefficient", 0)
        
        # 情绪评分范围：0-1，0表示悲观，1表示乐观
        # 负相关（新房价格更高）通常表示市场乐观
        sentiment_score = 0.5 - correlation * 0.3
        
        return max(0, min(1, sentiment_score))
    
    def _get_sentiment_label(self, score: float) -> str:
        """Get sentiment label based on score"""
        if score >= 0.7:
            return "乐观"
        elif score >= 0.4:
            return "中性"
        else:
            return "悲观"
    
    def _analyze_market_activity(self, properties: List[Dict[str, Any]]) -> str:
        """Analyze market activity level"""
        if not properties:
            return "低"
        
        # 基于房源数量和价格分布分析活跃度
        if len(properties) > 50:
            return "高"
        elif len(properties) > 20:
            return "中"
        else:
            return "低"
    
    def _calculate_property_value_score(self, property_data: Dict[str, Any]) -> float:
        """Calculate property value score"""
        score = 0.0
        
        # 基于多个因素计算价值评分
        price = property_data.get("price", 0)
        area = property_data.get("area", 0)
        age = property_data.get("age", 0)
        features = property_data.get("features", [])
        
        # 价格合理性
        if price > 0 and area > 0:
            price_per_square = price / area
            # 价格适中
            if 10000 <= price_per_square <= 30000:
                score += 0.3
        
        # 房龄
        if age <= 10:
            score += 0.2
        elif age <= 20:
            score += 0.1
        
        # 面积
        if 60 <= area <= 120:
            score += 0.2
        
        # 特色
        score += min(len(features) * 0.05, 0.3)
        
        return min(score, 1.0)
    
    def _get_value_label(self, score: float) -> str:
        """Get value label based on score"""
        if score >= 0.8:
            return "高价值"
        elif score >= 0.6:
            return "中等价值"
        else:
            return "低价值"
    
    def _analyze_value_distribution(self, scores: List[float]) -> Dict[str, Any]:
        """Analyze value score distribution"""
        if not scores:
            return {}
        
        distribution = {
            "high_value": len([s for s in scores if s >= 0.8]),
            "medium_value": len([s for s in scores if 0.6 <= s < 0.8]),
            "low_value": len([s for s in scores if s < 0.6])
        }
        
        return distribution
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        # 简单的相关性计算
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator_x = sum((xi - mean_x) ** 2 for xi in x)
        denominator_y = sum((yi - mean_y) ** 2 for yi in y)
        
        if denominator_x == 0 or denominator_y == 0:
            return 0
        
        correlation = numerator / (denominator_x ** 0.5 * denominator_y ** 0.5)
        return correlation
    
    def calculate_confidence(self, analysis: Dict[str, Any], properties: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for analysis"""
        if not properties:
            return 0.3
        
        # 基于分析的指标数量和房源数量计算置信度
        analyzed_metrics = len([v for v in analysis.values() if v])
        metrics_score = analyzed_metrics / len(self.metrics)
        
        # 基于房源数量的置信度
        properties_score = min(len(properties) / 10, 1.0)
        
        # 综合置信度
        confidence = (metrics_score * 0.6 + properties_score * 0.4) * 0.8 + 0.2
        
        return min(confidence, 1.0)
