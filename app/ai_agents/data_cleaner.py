from typing import Dict, Any, List
import asyncio
import re
from app.ai_agents.base_agent import BaseAgent
from app.ai_agents.data_lineage import lineage_tracker


class DataCleanerAgent(BaseAgent):
    """Agent specialized in cleaning and standardizing property data"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "Agent specialized in cleaning and standardizing property data"
        self.standardizers = {
            "price": self.standardize_price,
            "area": self.standardize_area,
            "property_type": self.standardize_property_type,
            "age": self.standardize_age,
            "address": self.standardize_address
        }
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data cleaning task"""
        try:
            # 发布开始事件
            self.publish_start_event(task)
            
            # Extract collected data from task
            collected_data = task.get("collected_data", {})
            raw_properties = collected_data.get("data", [])
            sources = collected_data.get("sources", [])
            
            # 发布进度事件
            self.publish_progress_event(0.1, "开始清洗和标准化数据")
            
            # Clean and standardize properties
            cleaned_properties = []
            cleaning_stats = {
                "total_properties": len(raw_properties),
                "successful_cleaned": 0,
                "failed_cleaned": 0,
                "standardization_errors": []
            }
            
            total_properties = len(raw_properties)
            for i, property_data in enumerate(raw_properties):
                try:
                    cleaned_property = await self.clean_property(property_data)
                    cleaned_properties.append(cleaned_property)
                    cleaning_stats["successful_cleaned"] += 1
                    
                    # 发布进度事件
                    if total_properties > 0:
                        progress = 0.1 + (i / total_properties) * 0.7
                        self.publish_progress_event(progress, f"正在清洗第 {i+1} 条数据")
                except Exception as e:
                    cleaning_stats["failed_cleaned"] += 1
                    cleaning_stats["standardization_errors"].append({
                        "property_index": i,
                        "error": str(e)
                    })
            
            # 发布进度事件
            self.publish_progress_event(0.8, "正在生成清洗报告")
            
            # Generate cleaning report
            cleaning_report = {
                "stats": cleaning_stats,
                "sources": sources,
                "cleaning_time": asyncio.get_event_loop().time(),
                "summary": f"成功清洗 {cleaning_stats['successful_cleaned']} 条数据，失败 {cleaning_stats['failed_cleaned']} 条"
            }
            
            result = {
                "cleaned_properties": cleaned_properties,
                "cleaning_report": cleaning_report
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
    
    async def clean_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize a single property"""
        cleaned = property_data.copy()
        
        # Apply standardizers to relevant fields
        for field, standardizer in self.standardizers.items():
            if field in cleaned:
                cleaned[field] = standardizer(cleaned[field])
        
        # Extract and standardize features
        if "features" in cleaned:
            cleaned["features"] = self.standardize_features(cleaned["features"])
        
        # Calculate price per square meter if both price and area are available
        if "price" in cleaned and "area" in cleaned:
            try:
                cleaned["price_per_square"] = cleaned["price"] / cleaned["area"]
            except (ZeroDivisionError, TypeError):
                cleaned["price_per_square"] = None
        
        # Add cleaning metadata
        cleaned["_cleaning_metadata"] = {
            "timestamp": asyncio.get_event_loop().time(),
            "cleaned_fields": list(self.standardizers.keys())
        }
        
        # Track data lineage transformation
        if "_lineage_node_id" in property_data:
            input_node_id = property_data["_lineage_node_id"]
            output_node_id = lineage_tracker.track_transformation(
                [input_node_id],
                cleaned,
                "data_cleaning",
                self.name,
                {
                    "cleaned_fields": list(self.standardizers.keys()),
                    "property_id": property_data.get("id", "unknown"),
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
            cleaned["_lineage_node_id"] = output_node_id
        else:
            # Create new lineage node if no existing one
            output_node_id = lineage_tracker.create_data_node(
                cleaned,
                "cleaned_data",
                {
                    "agent": self.name,
                    "cleaning_timestamp": asyncio.get_event_loop().time(),
                    "property_id": property_data.get("id", "unknown")
                }
            )
            cleaned["_lineage_node_id"] = output_node_id
        
        return cleaned
    
    def standardize_price(self, price: Any) -> float:
        """Standardize price to float in yuan"""
        if isinstance(price, (int, float)):
            return float(price)
        elif isinstance(price, str):
            # Remove currency symbols and commas
            price_str = re.sub(r'[¥,万元]', '', price)
            # Handle cases like "1200万"
            if '万' in price:
                try:
                    return float(price_str) * 10000
                except ValueError:
                    return 0.0
            try:
                return float(price_str)
            except ValueError:
                return 0.0
        return 0.0
    
    def standardize_area(self, area: Any) -> float:
        """Standardize area to float in square meters"""
        if isinstance(area, (int, float)):
            return float(area)
        elif isinstance(area, str):
            # Remove area units
            area_str = re.sub(r'[㎡平米]', '', area)
            try:
                return float(area_str)
            except ValueError:
                return 0.0
        return 0.0
    
    def standardize_property_type(self, property_type: Any) -> str:
        """Standardize property type"""
        if not property_type:
            return "未知"
        
        property_type_str = str(property_type).strip()
        
        # Map common variations to standard types
        type_mappings = {
            "住宅": ["住宅", "普通住宅", "商品住宅"],
            "公寓": ["公寓", "商住公寓", "酒店式公寓"],
            "别墅": ["别墅", "独栋别墅", "联排别墅"],
            "商铺": ["商铺", "商业", "店面"],
            "写字楼": ["写字楼", "办公", "商务楼"]
        }
        
        for standard_type, variations in type_mappings.items():
            for variation in variations:
                if variation in property_type_str:
                    return standard_type
        
        return property_type_str
    
    def standardize_age(self, age: Any) -> int:
        """Standardize age to integer in years"""
        if isinstance(age, (int, float)):
            return int(age)
        elif isinstance(age, str):
            # Remove age units
            age_str = re.sub(r'[年]', '', age)
            try:
                return int(age_str)
            except ValueError:
                return 0
        return 0
    
    def standardize_address(self, address: Any) -> str:
        """Standardize address format"""
        if not address:
            return ""
        
        address_str = str(address).strip()
        # Remove redundant whitespace
        address_str = re.sub(r'\s+', ' ', address_str)
        # Capitalize proper nouns (simplified)
        address_str = address_str.title()
        
        return address_str
    
    def standardize_features(self, features: Any) -> List[str]:
        """Standardize property features"""
        if not features:
            return []
        
        if isinstance(features, str):
            # Split string features
            feature_list = [f.strip() for f in features.split(',')]
        elif isinstance(features, list):
            feature_list = [str(f).strip() for f in features]
        else:
            return []
        
        # Remove empty features and duplicates
        feature_list = [f for f in feature_list if f]
        feature_list = list(set(feature_list))
        
        return feature_list
