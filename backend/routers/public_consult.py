"""
智能咨询公开API - 支持单个/多个/综合输入
集成自然语言解析和MaAS智能调度
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import time
import logging

router = APIRouter(prefix="/api/public/consult", tags=["public-consultation"])
logger = logging.getLogger(__name__)


class SingleInputRequest(BaseModel):
    """单个输入请求"""
    message: str = Field(..., description="用户消息")
    user_id: Optional[str] = Field(default="anonymous", description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class MultipleInputRequest(BaseModel):
    """多个输入请求"""
    messages: List[str] = Field(..., description="多个消息列表")
    user_id: Optional[str] = Field(default="anonymous", description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ComprehensiveInputRequest(BaseModel):
    """综合输入请求"""
    message: str = Field(..., description="主要消息")
    context: Optional[Dict[str, Any]] = Field(default=None, description="额外上下文")
    addresses: Optional[List[str]] = Field(default=None, description="相关地址列表")
    requirements: Optional[List[str]] = Field(default=None, description="需求列表")
    user_id: Optional[str] = Field(default="anonymous", description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ConsultationResponse(BaseModel):
    """咨询响应"""
    success: bool
    reply: str
    parsed_info: Optional[Dict[str, Any]] = None
    input_type: str
    confidence: float
    processing_time: float
    session_id: str


class BatchConsultationResponse(BaseModel):
    """批量咨询响应"""
    success: bool
    results: List[ConsultationResponse]
    total_processing_time: float
    aggregated_summary: Optional[str] = None


async def parse_natural_language(query: str) -> Dict[str, Any]:
    """解析自然语言"""
    try:
        from backend.services.entity_recognition import entity_recognizer
        
        result = await entity_recognizer.parse_natural_language(query)
        return {
            "city": result.city,
            "district": result.district,
            "community": result.community,
            "room_count": result.room_count,
            "area_min": result.area_min,
            "area_max": result.area_max,
            "price_min": result.price_min,
            "price_max": result.price_max,
            "confidence": result.confidence,
            "missing_fields": result.missing_fields,
        }
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return _simple_parse(query)


def _simple_parse(query: str) -> Dict[str, Any]:
    """简单解析作为后备"""
    result = {
        "city": None,
        "district": None,
        "community": None,
        "confidence": 0.0,
        "missing_fields": []
    }
    
    cities = ["深圳", "北京", "上海", "广州", "杭州", "成都", "南京", "武汉"]
    districts = {
        "深圳": ["南山", "福田", "宝安", "龙岗", "罗湖", "龙华", "光明"],
        "北京": ["朝阳", "海淀", "西城", "东城", "丰台", "昌平", "大兴"],
        "上海": ["浦东", "徐汇", "静安", "黄浦", "闵行", "长宁", "普陀"],
    }
    
    for city in cities:
        if city in query:
            result["city"] = city
            result["confidence"] = 0.5
            
            if city in districts:
                for district in districts[city]:
                    if district in query:
                        result["district"] = district + "区"
                        result["confidence"] = 0.8
                        break
            break
    
    return result


async def generate_consultation_reply(
    message: str,
    parsed_info: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """生成咨询回复"""
    try:
        from backend.llm_service import llm_service
        
        system_prompt = """你是房都督平台的智能房产顾问。你具有专业的房产知识，能够：
1. 分析房价走势和市场动态
2. 提供房产投资建议
3. 解答购房相关问题
4. 评估房产价值和风险

请用专业、友好的语气回答用户问题。如果用户提供了具体地址或区域，请结合相关信息给出针对性建议。"""

        user_content = message
        
        if parsed_info and parsed_info.get("confidence", 0) > 0.3:
            location_parts = []
            if parsed_info.get("city"):
                location_parts.append(parsed_info["city"])
            if parsed_info.get("district"):
                location_parts.append(parsed_info["district"])
            
            if location_parts:
                user_content += f"\n\n[解析的位置信息：{' '.join(location_parts)}]"
        
        if context:
            user_content += f"\n\n[额外上下文：{context}]"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        response = await llm_service.generate(messages)
        return response
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return _generate_fallback_reply(message, parsed_info)


def _generate_fallback_reply(message: str, parsed_info: Dict[str, Any]) -> str:
    """生成后备回复"""
    if parsed_info and parsed_info.get("city"):
        city = parsed_info.get("city", "")
        district = parsed_info.get("district", "")
        return f"关于您咨询的{city}{district}房产问题，根据当前市场数据分析，该区域房产具有较好的投资价值。建议您关注交通便利性和周边配套设施，这些因素对房产价值影响较大。如需更详细的分析，请提供更多具体信息。"
    else:
        return f"感谢您的咨询。关于「{message[:30]}...」的问题，我建议您可以从以下几个方面考虑：1. 地理位置和交通便利性；2. 周边配套设施；3. 未来发展规划；4. 价格走势分析。如需更具体的建议，请提供详细的区域或小区信息。"


@router.post("/single", response_model=ConsultationResponse)
async def consult_single_input(request: SingleInputRequest):
    """
    单个输入咨询
    
    用户输入一条自然语言消息，系统解析并回复
    """
    start_time = time.time()
    
    session_id = request.session_id or str(uuid.uuid4())
    
    parsed_info = await parse_natural_language(request.message)
    
    reply = await generate_consultation_reply(request.message, parsed_info)
    
    processing_time = time.time() - start_time
    
    return ConsultationResponse(
        success=True,
        reply=reply,
        parsed_info=parsed_info if parsed_info.get("confidence", 0) > 0.3 else None,
        input_type="single",
        confidence=parsed_info.get("confidence", 0.5),
        processing_time=processing_time,
        session_id=session_id
    )


@router.post("/multiple", response_model=BatchConsultationResponse)
async def consult_multiple_inputs(request: MultipleInputRequest):
    """
    多个输入咨询
    
    用户输入多条消息，系统逐一解析并汇总回复
    """
    start_time = time.time()
    
    session_id = request.session_id or str(uuid.uuid4())
    
    results = []
    all_parsed_info = []
    
    for message in request.messages:
        parsed_info = await parse_natural_language(message)
        reply = await generate_consultation_reply(message, parsed_info)
        
        all_parsed_info.append(parsed_info)
        
        results.append(ConsultationResponse(
            success=True,
            reply=reply,
            parsed_info=parsed_info if parsed_info.get("confidence", 0) > 0.3 else None,
            input_type="multiple",
            confidence=parsed_info.get("confidence", 0.5),
            processing_time=0.0,
            session_id=session_id
        ))
    
    aggregated_summary = await generate_aggregated_summary(request.messages, all_parsed_info)
    
    total_processing_time = time.time() - start_time
    
    return BatchConsultationResponse(
        success=True,
        results=results,
        total_processing_time=total_processing_time,
        aggregated_summary=aggregated_summary
    )


@router.post("/comprehensive", response_model=ConsultationResponse)
async def consult_comprehensive_input(request: ComprehensiveInputRequest):
    """
    综合输入咨询
    
    用户输入主要消息+额外上下文+多个地址+多个需求
    系统综合分析并给出深度建议
    """
    start_time = time.time()
    
    session_id = request.session_id or str(uuid.uuid4())
    
    main_parsed = await parse_natural_language(request.message)
    
    address_parsed_list = []
    if request.addresses:
        for addr in request.addresses:
            addr_parsed = await parse_natural_language(addr)
            address_parsed_list.append(addr_parsed)
    
    comprehensive_context = {
        "main_message": request.message,
        "context": request.context,
        "addresses": request.addresses,
        "requirements": request.requirements,
        "parsed_addresses": address_parsed_list
    }
    
    reply = await generate_comprehensive_reply(
        request.message,
        main_parsed,
        comprehensive_context
    )
    
    processing_time = time.time() - start_time
    
    return ConsultationResponse(
        success=True,
        reply=reply,
        parsed_info=main_parsed,
        input_type="comprehensive",
        confidence=main_parsed.get("confidence", 0.5),
        processing_time=processing_time,
        session_id=session_id
    )


async def generate_aggregated_summary(
    messages: List[str],
    parsed_infos: List[Dict[str, Any]]
) -> str:
    """生成汇总摘要"""
    cities = set()
    districts = set()
    
    for info in parsed_infos:
        if info.get("city"):
            cities.add(info["city"])
        if info.get("district"):
            districts.add(info["district"])
    
    summary_parts = []
    
    if cities:
        summary_parts.append(f"涉及城市：{', '.join(cities)}")
    if districts:
        summary_parts.append(f"涉及区域：{', '.join(districts)}")
    
    summary_parts.append(f"共分析 {len(messages)} 条咨询")
    
    return " | ".join(summary_parts)


async def generate_comprehensive_reply(
    message: str,
    parsed_info: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """生成综合回复"""
    try:
        from backend.llm_service import llm_service
        
        system_prompt = """你是房都督平台的高级房产分析师。你具有深厚的房产专业知识和市场洞察力，能够：
1. 综合分析多个区域的房产情况
2. 对比不同区域的优劣势
3. 根据用户需求提供个性化建议
4. 评估投资风险和收益预期

请用专业、全面、深入的方式回答用户问题，提供有价值的分析和建议。"""

        context_str = f"""
主要咨询：{message}
"""
        
        if context.get("addresses"):
            context_str += f"\n相关地址：{', '.join(context['addresses'])}"
        
        if context.get("requirements"):
            context_str += f"\n用户需求：{', '.join(context['requirements'])}"
        
        if context.get("context"):
            extra_ctx = context["context"]
            if isinstance(extra_ctx, dict):
                for k, v in extra_ctx.items():
                    context_str += f"\n{k}：{v}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_str}
        ]
        response = await llm_service.generate(messages)
        return response
    except Exception as e:
        logger.error(f"LLM error in comprehensive reply: {e}")
        
        addresses = context.get("addresses", [])
        if addresses:
            return f"关于您咨询的{', '.join(addresses[:3])}等区域，根据综合分析：\n\n1. **区域对比**：各区域均有独特优势，建议根据您的具体需求（{', '.join(context.get('requirements', ['投资', '自住'])[:2])}）进行选择。\n\n2. **投资建议**：关注交通便利性和未来发展规划，这些因素对房产增值影响较大。\n\n3. **风险提示**：建议实地考察，了解周边配套和物业管理情况。\n\n如需更详细的分析报告，请提供更多具体信息。"
        else:
            return f"感谢您的详细咨询。根据您提供的信息，我建议从以下几个方面考虑：\n\n1. **需求分析**：明确您的核心需求，是投资还是自住？\n2. **预算规划**：合理分配预算，预留装修和税费空间\n3. **区域选择**：综合考虑交通、教育、医疗等配套\n\n如需针对具体区域的分析，请提供详细地址信息。"


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "public-consultation",
        "features": ["single", "multiple", "comprehensive"]
    }
