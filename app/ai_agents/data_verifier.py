from typing import Dict, Any, List, Tuple
import asyncio
from app.ai_agents.base_agent import BaseAgent
from app.ai_agents.data_lineage import lineage_tracker


class DataVerifierAgent(BaseAgent):
    """Agent specialized in verifying data consistency across sources"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "Agent specialized in verifying data consistency across sources"
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.7)
        self.verification_rules = {
            "price": self.verify_price_consistency,
            "area": self.verify_area_consistency,
            "property_type": self.verify_property_type_consistency,
            "age": self.verify_age_consistency
        }
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data verification task"""
        try:
            # 发布开始事件
            self.publish_start_event(task)
            
            # Extract cleaned data from task
            # 支持多种输入格式
            cleaned_properties = []
            cleaning_report = {}
            
            # 格式1: 传统的cleaning_result格式
            if "cleaning_result" in task:
                cleaning_result = task.get("cleaning_result", {})
                cleaned_properties = cleaning_result.get("cleaned_properties", [])
                cleaning_report = cleaning_result.get("cleaning_report", {})
            # 格式2: 直接的cleaned_data格式（来自调度器）
            elif "cleaned_data" in task:
                cleaned_data = task.get("cleaned_data", {})
                # 检查cleaned_data的结构
                if isinstance(cleaned_data, list):
                    # 如果是列表，直接使用
                    cleaned_properties = cleaned_data
                elif isinstance(cleaned_data, dict):
                    # 如果是字典，检查是否有data字段
                    if "data" in cleaned_data:
                        cleaned_properties = cleaned_data.get("data", [])
                    else:
                        # 尝试提取所有可能的房产数据
                        for key, value in cleaned_data.items():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict) and ("name" in item or "address" in item):
                                        cleaned_properties.append(item)
            
            # 发布进度事件
            self.publish_progress_event(0.2, "开始验证数据一致性")
            
            # Verify data consistency
            verification_results = await self.verify_data_consistency(cleaned_properties)
            
            # 发布进度事件
            self.publish_progress_event(0.8, "正在生成验证报告")
            
            # Generate verification report
            verification_report = {
                "consistency_score": verification_results["consistency_score"],
                "verified_properties": len(verification_results["verified_properties"]),
                "conflicting_properties": len(verification_results["conflicting_properties"]),
                "resolved_conflicts": len(verification_results["resolved_conflicts"]),
                "unresolved_conflicts": len(verification_results["unresolved_conflicts"]),
                "verification_time": asyncio.get_event_loop().time(),
                "summary": self.generate_verification_summary(verification_results)
            }
            
            result = {
                "verification_results": verification_results,
                "verification_report": verification_report,
                "cleaned_properties_count": len(cleaned_properties)
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
    
    async def verify_data_consistency(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify data consistency across properties"""
        # 分离房产数据和其他类型的数据
        real_estate_properties = []
        other_data = []
        
        for item in properties:
            if isinstance(item, dict):
                # 检查是否是房产数据
                if "name" in item and "address" in item and ("price" in item or "area" in item):
                    real_estate_properties.append(item)
                else:
                    # 其他类型的数据
                    other_data.append(item)
        
        # 处理房产数据
        verified_properties = []
        conflicting_properties = []
        resolved_conflicts = []
        unresolved_conflicts = []
        
        total_conflicts = 0
        resolved_conflicts_count = 0
        
        if real_estate_properties:
            # Group properties by name and address for cross-source verification
            property_groups = self.group_properties(real_estate_properties)
            
            for group_key, group_properties in property_groups.items():
                if len(group_properties) == 1:
                    # Only one source, mark as verified with confidence
                    property_data = group_properties[0]
                    property_data["_verification_metadata"] = {
                        "confidence": 0.8,
                        "sources": [property_data.get("source", "unknown")],
                        "verification_status": "verified_single_source"
                    }
                    verified_properties.append(property_data)
                else:
                    # Multiple sources, verify consistency
                    verification_result = await self.verify_group_consistency(group_properties)
                    if verification_result["is_consistent"]:
                        # Consistent across sources
                        property_data = verification_result["resolved_property"]
                        property_data["_verification_metadata"] = {
                            "confidence": verification_result["confidence"],
                            "sources": verification_result["sources"],
                            "verification_status": "verified_multiple_sources"
                        }
                        verified_properties.append(property_data)
                    else:
                        # Conflicts detected
                        conflicting_properties.extend(group_properties)
                        if verification_result["resolved_property"]:
                            resolved_conflicts.append(verification_result["resolved_property"])
                            resolved_conflicts_count += 1
                        else:
                            unresolved_conflicts.extend(group_properties)
                        total_conflicts += 1
        
        # 处理其他类型的数据（直接标记为已验证）
        for item in other_data:
            item["_verification_metadata"] = {
                "confidence": 0.7,
                "sources": [item.get("source", "unknown")],
                "verification_status": "verified_other_data_type"
            }
            verified_properties.append(item)
        
        # Calculate overall consistency score
        if total_conflicts > 0:
            consistency_score = resolved_conflicts_count / total_conflicts
        else:
            consistency_score = 1.0
        
        return {
            "consistency_score": consistency_score,
            "verified_properties": verified_properties,
            "conflicting_properties": conflicting_properties,
            "resolved_conflicts": resolved_conflicts,
            "unresolved_conflicts": unresolved_conflicts,
            "total_groups": len(property_groups) if 'property_groups' in locals() else 0,
            "other_data_count": len(other_data)
        }
    
    def group_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group properties by name and address"""
        groups = {}
        
        for property_data in properties:
            name = property_data.get("name", "").strip()
            address = property_data.get("address", "").strip()
            group_key = f"{name}_{address}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(property_data)
        
        return groups
    
    async def verify_group_consistency(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify consistency within a group of properties"""
        conflicts = []
        resolved_values = {}
        sources = [p.get("source", "unknown") for p in properties]
        
        # Verify each field
        for field, verifier in self.verification_rules.items():
            field_values = [p.get(field) for p in properties if field in p]
            if len(field_values) > 1:
                verification_result = verifier(field_values)
                if not verification_result["is_consistent"]:
                    conflicts.append({
                        "field": field,
                        "values": field_values,
                        "reason": verification_result["reason"]
                    })
                resolved_values[field] = verification_result["resolved_value"]
            elif field_values:
                resolved_values[field] = field_values[0]
        
        # Create resolved property if possible
        resolved_property = None
        if conflicts:
            # Try to resolve conflicts
            if len(conflicts) < len(self.verification_rules):
                # Most fields are consistent, create resolved property
                resolved_property = properties[0].copy()
                resolved_property.update(resolved_values)
                resolved_property["_verification_metadata"] = {
                    "confidence": 0.6,
                    "sources": sources,
                    "verification_status": "resolved_conflicts",
                    "conflicts": conflicts
                }
        else:
            # No conflicts, create resolved property
            resolved_property = properties[0].copy()
            resolved_property.update(resolved_values)
            resolved_property["_verification_metadata"] = {
                "confidence": 0.95,
                "sources": sources,
                "verification_status": "fully_consistent"
            }
        
        # Track data lineage transformation for resolved property
        if resolved_property:
            # Collect input lineage node IDs
            input_node_ids = []
            for property_data in properties:
                if "_lineage_node_id" in property_data:
                    input_node_ids.append(property_data["_lineage_node_id"])
            
            if input_node_ids:
                # Track transformation from multiple sources
                output_node_id = lineage_tracker.track_transformation(
                    input_node_ids,
                    resolved_property,
                    "data_verification",
                    self.name,
                    {
                        "verification_status": resolved_property["_verification_metadata"]["verification_status"],
                        "confidence": resolved_property["_verification_metadata"]["confidence"],
                        "conflicts_count": len(conflicts),
                        "sources_count": len(sources),
                        "timestamp": asyncio.get_event_loop().time()
                    }
                )
                resolved_property["_lineage_node_id"] = output_node_id
            else:
                # Create new lineage node if no existing ones
                output_node_id = lineage_tracker.create_data_node(
                    resolved_property,
                    "verified_data",
                    {
                        "agent": self.name,
                        "verification_timestamp": asyncio.get_event_loop().time(),
                        "verification_status": resolved_property["_verification_metadata"]["verification_status"],
                        "confidence": resolved_property["_verification_metadata"]["confidence"]
                    }
                )
                resolved_property["_lineage_node_id"] = output_node_id
        
        return {
            "is_consistent": len(conflicts) == 0,
            "conflicts": conflicts,
            "resolved_property": resolved_property,
            "confidence": 1.0 - (len(conflicts) * 0.1),
            "sources": sources
        }
    
    def verify_price_consistency(self, prices: List[float]) -> Dict[str, Any]:
        """Verify price consistency across sources"""
        if not prices:
            return {"is_consistent": True, "resolved_value": None, "reason": "No prices provided"}
        
        # Calculate price range
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        average_price = sum(prices) / len(prices)
        
        # Check if prices are within 10% of each other
        if price_range / average_price <= 0.1:
            return {
                "is_consistent": True,
                "resolved_value": average_price,
                "reason": "Prices within 10% range"
            }
        else:
            return {
                "is_consistent": False,
                "resolved_value": average_price,
                "reason": f"Prices vary by more than 10% (range: {price_range/average_price:.2%})"
            }
    
    def verify_area_consistency(self, areas: List[float]) -> Dict[str, Any]:
        """Verify area consistency across sources"""
        if not areas:
            return {"is_consistent": True, "resolved_value": None, "reason": "No areas provided"}
        
        # Calculate area range
        min_area = min(areas)
        max_area = max(areas)
        area_range = max_area - min_area
        average_area = sum(areas) / len(areas)
        
        # Check if areas are within 5% of each other
        if area_range / average_area <= 0.05:
            return {
                "is_consistent": True,
                "resolved_value": average_area,
                "reason": "Areas within 5% range"
            }
        else:
            return {
                "is_consistent": False,
                "resolved_value": average_area,
                "reason": f"Areas vary by more than 5% (range: {area_range/average_area:.2%})"
            }
    
    def verify_property_type_consistency(self, property_types: List[str]) -> Dict[str, Any]:
        """Verify property type consistency across sources"""
        if not property_types:
            return {"is_consistent": True, "resolved_value": None, "reason": "No property types provided"}
        
        # Check if all property types are the same
        unique_types = set(property_types)
        if len(unique_types) == 1:
            return {
                "is_consistent": True,
                "resolved_value": property_types[0],
                "reason": "All property types match"
            }
        else:
            # Use the most common type
            from collections import Counter
            most_common = Counter(property_types).most_common(1)[0][0]
            return {
                "is_consistent": False,
                "resolved_value": most_common,
                "reason": f"Multiple property types found: {list(unique_types)}"
            }
    
    def verify_age_consistency(self, ages: List[int]) -> Dict[str, Any]:
        """Verify age consistency across sources"""
        if not ages:
            return {"is_consistent": True, "resolved_value": None, "reason": "No ages provided"}
        
        # Calculate age range
        min_age = min(ages)
        max_age = max(ages)
        age_range = max_age - min_age
        
        # Check if ages are within 2 years of each other
        if age_range <= 2:
            return {
                "is_consistent": True,
                "resolved_value": round(sum(ages) / len(ages)),
                "reason": "Ages within 2 year range"
            }
        else:
            return {
                "is_consistent": False,
                "resolved_value": round(sum(ages) / len(ages)),
                "reason": f"Ages vary by more than 2 years (range: {age_range} years)"
            }
    
    def generate_verification_summary(self, verification_results: Dict[str, Any]) -> str:
        """Generate a summary of the verification results"""
        consistency_score = verification_results["consistency_score"]
        total_groups = verification_results["total_groups"]
        verified = len(verification_results["verified_properties"])
        conflicting = len(verification_results["conflicting_properties"])
        resolved = len(verification_results["resolved_conflicts"])
        unresolved = len(verification_results["unresolved_conflicts"])
        
        if consistency_score >= 0.8:
            consistency_level = "高度一致"
        elif consistency_score >= 0.6:
            consistency_level = "基本一致"
        else:
            consistency_level = "存在较多冲突"
        
        return f"数据一致性: {consistency_level} (得分: {consistency_score:.2f})。共验证 {total_groups} 个房产，其中 {verified} 个验证通过，{conflicting} 个存在冲突，{resolved} 个冲突已解决，{unresolved} 个冲突未解决。"
