"""
需求解析代理
负责解析用户查询，提取关键信息
支持自然语言解析和智能推断
"""
from .base import BaseAgent
from .message import AgentMessage, MessageType
from ..services.entity_recognition import parse_natural_language, ParsedRequirement
from ..services.house_type_service import get_area_estimate, init_house_type_data
from ..services.price_estimator import estimate_price, init_district_price_data
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class RequirementAgent(BaseAgent):
    """
    需求解析代理
    解析用户查询，提取城市、区域、预算等信息
    支持自然语言解析和智能推断
    """
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"RequirementAgent received message from {message.sender}")
        
        if message.type == MessageType.REQUEST:
            action = message.content.get("action")
            
            if action == "parse":
                query = message.content.get("query", "")
                await self.record_step("开始解析需求", f"正在解析用户查询: {query[:50]}...", status="in_progress")
                
                parsed = await self._parse_requirement(query)
                
                await self.record_step("需求解析完成", f"提取到城市: {parsed.get('city')}, 区域: {parsed.get('district')}", status="completed", output_data={"parsed": parsed})
                
                await self.respond(message, {"parsed": parsed})
            
            elif action == "parse_with_inference":
                query = message.content.get("query", "")
                await self.record_step("开始智能解析", f"正在解析并推断用户需求: {query[:50]}...", status="in_progress")
                
                parsed = await self._parse_requirement_with_inference(query)
                
                inference_count = parsed.get("inference_count", 0)
                await self.record_step("智能解析完成", f"解析完成，进行了{inference_count}项智能推断", status="completed", output_data={"parsed": parsed})
                
                await self.respond(message, {"parsed": parsed})
            
            elif action == "get_missing_fields":
                query = message.content.get("query", "")
                await self.record_step("检查缺失字段", f"正在分析缺失信息: {query[:50]}...", status="in_progress")
                
                missing = await self._get_missing_fields(query)
                
                missing_count = len(missing.get("missing_fields", []))
                await self.record_step("缺失字段检查完成", f"发现{missing_count}个缺失字段", status="completed", output_data={"missing_fields": missing})
                
                await self.respond(message, {"missing_fields": missing})
    
    async def _parse_requirement(self, query: str) -> Dict[str, Any]:
        """
        解析用户需求（基础版）
        
        Args:
            query: 用户查询
            
        Returns:
            dict: 解析结果
        """
        parsed_result = parse_natural_language(query)
        
        result = {
            "raw_query": query,
            "city": self._extract_entity_value(parsed_result.city),
            "district": self._extract_entity_value(parsed_result.district),
            "community": self._extract_entity_value(parsed_result.community),
            "room_count": self._extract_entity_value(parsed_result.room_count),
            "hall_count": self._extract_entity_value(parsed_result.hall_count),
            "area_min": self._extract_entity_value(parsed_result.area_min),
            "area_max": self._extract_entity_value(parsed_result.area_max),
            "price_min": self._extract_entity_value(parsed_result.price_min),
            "price_max": self._extract_entity_value(parsed_result.price_max),
            "orientation": self._extract_entity_value(parsed_result.orientation),
            "floor_type": self._extract_entity_value(parsed_result.floor_type),
            "decoration": self._extract_entity_value(parsed_result.decoration),
            "is_school_district": self._extract_entity_value(parsed_result.is_school_district),
            "is_near_subway": self._extract_entity_value(parsed_result.is_near_subway),
            "special_requirements": parsed_result.special_requirements,
            "missing_fields": parsed_result.missing_fields,
            "confidence": self._calculate_confidence(parsed_result),
        }
        
        logger.info(f"Parsed requirement: {result}")
        
        return result
    
    async def _parse_requirement_with_inference(self, query: str) -> Dict[str, Any]:
        """
        解析用户需求并智能推断缺失字段
        
        Args:
            query: 用户查询
            
        Returns:
            dict: 解析结果（包含推断）
        """
        parsed_result = parse_natural_language(query)
        
        result = await self._parse_requirement(query)
        
        inferences = []
        
        if result.get("room_count") and not result.get("area_min"):
            hall_count = result.get("hall_count") or 1
            city = result.get("city")
            
            area_estimate = await get_area_estimate(
                room_count=result["room_count"],
                hall_count=hall_count,
                city=city
            )
            
            if area_estimate:
                result["area_min"] = area_estimate["min_area"]
                result["area_max"] = area_estimate["max_area"]
                result["area_avg"] = area_estimate["avg_area"]
                result["area_estimated"] = True
                result["area_confidence"] = area_estimate["confidence"]
                
                inferences.append({
                    "field": "area",
                    "inferred_value": {
                        "min": area_estimate["min_area"],
                        "max": area_estimate["max_area"],
                        "avg": area_estimate["avg_area"],
                        "common_areas": area_estimate.get("common_areas", [])
                    },
                    "confidence": area_estimate["confidence"],
                    "reasoning": f"根据{result['room_count']}室{hall_count}厅户型估算面积",
                    "data_source": area_estimate["source"],
                    "city_adjusted": area_estimate.get("city_adjusted", False)
                })
        
        if result.get("city") and not result.get("price_max"):
            city = result["city"]
            district = result.get("district")
            area = result.get("area_min", result.get("area_avg", 100))
            house_type = None
            if result.get("room_count"):
                hall_count = result.get("hall_count", 1)
                house_type = f"{result['room_count']}室{hall_count}厅"
            
            price_estimate = await estimate_price(
                city=city,
                district=district,
                area_min=result.get("area_min"),
                area_max=result.get("area_max"),
                house_type=house_type,
                special_requirements=result.get("special_requirements", [])
            )
            
            if price_estimate:
                result["price_min"] = price_estimate["total_price"]["min"]
                result["price_max"] = price_estimate["total_price"]["max"]
                result["price_avg"] = price_estimate["total_price"]["avg"]
                result["price_estimated"] = True
                result["price_confidence"] = price_estimate["confidence"]
                result["unit_price"] = price_estimate["adjusted_unit_price"]
                
                inferences.append({
                    "field": "price",
                    "inferred_value": price_estimate["total_price"],
                    "confidence": price_estimate["confidence"],
                    "reasoning": f"根据{city}{' ' + district if district else ''}房价估算",
                    "data_source": price_estimate["source"],
                    "unit_price": price_estimate["adjusted_unit_price"],
                    "adjustment_factor": price_estimate.get("adjustment_factor", 1.0)
                })
        
        result["inferences"] = inferences
        result["inference_count"] = len(inferences)
        
        logger.info(f"Parsed requirement with inference: {result}")
        
        return result
    
    async def _get_missing_fields(self, query: str) -> Dict[str, Any]:
        """
        获取缺失字段及建议
        
        Args:
            query: 用户查询
            
        Returns:
            dict: 缺失字段信息
        """
        parsed_result = parse_natural_language(query)
        
        missing_info = {
            "missing_fields": parsed_result.missing_fields,
            "suggestions": [],
            "questions": []
        }
        
        field_questions = {
            "city": "请问您想了解哪个城市的房产？",
            "district": "请问您有偏好的区域吗？",
            "room_count": "请问您需要几室的房子？",
            "area_min": "请问您对面积有什么要求？",
            "price_max": "请问您的预算大概是多少？",
        }
        
        field_suggestions = {
            "district": "您可以告诉我具体的区域，如南山区、福田区等",
            "room_count": "常见的户型有：两室一厅、三室两厅等",
            "area_min": "您可以描述面积范围，如90-120平",
            "price_max": "您可以告诉我预算，如300-500万",
        }
        
        for field in parsed_result.missing_fields:
            if field in field_questions:
                missing_info["questions"].append({
                    "field": field,
                    "question": field_questions[field]
                })
            if field in field_suggestions:
                missing_info["suggestions"].append({
                    "field": field,
                    "suggestion": field_suggestions[field]
                })
        
        return missing_info
    
    def _extract_entity_value(self, entity) -> Any:
        """提取实体值"""
        if entity is None:
            return None
        return entity.value
    
    def _calculate_confidence(self, parsed: ParsedRequirement) -> float:
        """计算整体置信度"""
        fields = [
            "city", "district", "community",
            "room_count", "hall_count",
            "area_min", "area_max",
            "price_min", "price_max",
        ]
        
        total_confidence = 0
        field_count = 0
        
        for field in fields:
            entity = getattr(parsed, field, None)
            if entity and entity.value is not None:
                total_confidence += entity.confidence
                field_count += 1
        
        if field_count == 0:
            return 0.0
        
        return round(total_confidence / field_count, 2)
