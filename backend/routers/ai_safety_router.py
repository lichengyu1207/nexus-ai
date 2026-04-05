"""
AI安全合规防护系统 - API路由
提供模型滥用防护、内容审核、水印、RAG等接口
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-safety", tags=["ai-safety"])


class InputAuditRequest(BaseModel):
    user_input: str
    context: Optional[Dict[str, Any]] = None
    enable_rag: bool = True


class OutputProcessRequest(BaseModel):
    output: str
    content_type: str = "text"
    add_watermark: bool = True


class KnowledgeAddRequest(BaseModel):
    knowledge_id: str
    content: str
    source: str
    category: str
    credibility: float = 1.0


class TextAuditRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """获取AI安全合规系统统计信息"""
    from ..ai_safety import ai_safety_system
    
    return ai_safety_system.get_system_stats()


@router.post("/audit/input")
async def audit_user_input(request: InputAuditRequest) -> Dict[str, Any]:
    """
    审核用户输入
    - 检测滥用风险
    - 可选RAG增强
    - 返回审核结果和处理建议
    """
    from ..ai_safety import ai_safety_system, ContentType
    
    try:
        result = ai_safety_system.process_user_input(
            user_input=request.user_input,
            context=request.context,
            enable_rag=request.enable_rag
        )
        return result
    except Exception as e:
        logger.error(f"Input audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/output")
async def process_model_output(request: OutputProcessRequest) -> Dict[str, Any]:
    """
    处理模型输出
    - 流式内容审核
    - 添加AI生成标识水印
    """
    from ..ai_safety import ai_safety_system, ContentType
    
    try:
        content_type = ContentType.TEXT
        if request.content_type == "image":
            content_type = ContentType.IMAGE
        elif request.content_type == "audio":
            content_type = ContentType.AUDIO
        elif request.content_type == "video":
            content_type = ContentType.VIDEO
        elif request.content_type == "document":
            content_type = ContentType.DOCUMENT
        
        result = ai_safety_system.process_model_output(
            output=request.output,
            content_type=content_type,
            add_watermark=request.add_watermark
        )
        return result
    except Exception as e:
        logger.error(f"Output process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/text")
async def audit_text_content(request: TextAuditRequest) -> Dict[str, Any]:
    """单独审核文本内容"""
    from ..ai_safety import ai_safety_system
    
    try:
        result = ai_safety_system.multimodal_auditor.audit_text(
            text=request.text,
            context=request.context
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"Text audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watermark/generate")
async def generate_watermark(
    content: str,
    content_type: str = "text",
    visible: bool = True
) -> Dict[str, Any]:
    """生成内容水印"""
    from ..ai_safety import ai_safety_system, ContentType
    
    try:
        ct = ContentType.TEXT
        if content_type == "image":
            ct = ContentType.IMAGE
        
        watermark = ai_safety_system.watermarker.generate_watermark(
            content=content,
            content_type=ct,
            visible=visible
        )
        
        watermarked = ai_safety_system.watermarker.embed_watermark(content, watermark)
        
        return {
            "watermark": watermark.to_dict(),
            "watermarked_content": watermarked
        }
    except Exception as e:
        logger.error(f"Watermark generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watermark/verify")
async def verify_watermark(content: str) -> Dict[str, Any]:
    """验证内容水印"""
    from ..ai_safety import ai_safety_system
    
    try:
        is_ai_generated, details = ai_safety_system.watermarker.verify_watermark(content)
        return {
            "is_ai_generated": is_ai_generated,
            "details": details
        }
    except Exception as e:
        logger.error(f"Watermark verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def get_knowledge_stats() -> Dict[str, Any]:
    """获取知识库统计"""
    from ..ai_safety import ai_safety_system
    
    return ai_safety_system.rag_enhancer.knowledge_base.get_stats()


@router.post("/knowledge/add")
async def add_knowledge(request: KnowledgeAddRequest) -> Dict[str, Any]:
    """添加知识到RAG知识库"""
    from ..ai_safety import ai_safety_system
    
    try:
        ai_safety_system.add_knowledge(
            knowledge_id=request.knowledge_id,
            content=request.content,
            source=request.source,
            category=request.category,
            credibility=request.credibility
        )
        return {"success": True, "message": "知识添加成功"}
    except Exception as e:
        logger.error(f"Knowledge add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/retrieve")
async def retrieve_knowledge(
    query: str,
    top_k: int = Query(5, ge=1, le=20)
) -> List[Dict[str, Any]]:
    """从知识库检索相关知识"""
    from ..ai_safety import ai_safety_system
    
    try:
        results = ai_safety_system.rag_enhancer.knowledge_base.retrieve(query, top_k)
        return results
    except Exception as e:
        logger.error(f"Knowledge retrieve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/enhance")
async def enhance_with_rag(
    query: str,
    system_prompt: str = ""
) -> Dict[str, Any]:
    """使用RAG增强提示词"""
    from ..ai_safety import ai_safety_system
    
    try:
        enhanced_prompt, sources = ai_safety_system.rag_enhancer.enhance_prompt(
            user_query=query,
            system_prompt=system_prompt
        )
        return {
            "enhanced_prompt": enhanced_prompt,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"RAG enhance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/abuse/patterns")
async def get_abuse_patterns() -> Dict[str, Any]:
    """获取滥用检测模式列表"""
    from ..ai_safety import AbuseCategory
    
    patterns = {}
    for category in AbuseCategory:
        patterns[category.value] = {
            "name": category.name,
            "description": _get_category_description(category)
        }
    
    return {"categories": patterns}


def _get_category_description(category) -> str:
    descriptions = {
        "drugs": "毒品相关内容",
        "fraud": "诈骗相关内容",
        "gambling": "赌博相关内容",
        "discrimination": "歧视性内容",
        "violence": "暴力相关内容",
        "pornography": "色情内容",
        "political_sensitive": "政治敏感内容",
        "personal_info": "个人信息泄露",
        "prompt_injection": "提示词注入攻击",
        "jailbreak": "越狱攻击",
        "harmful_instruction": "有害指令",
        "misinformation": "虚假信息",
    }
    return descriptions.get(category.value, category.value)


@router.get("/audit/history")
async def get_audit_history(
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """获取审核历史记录"""
    from ..ai_safety import ai_safety_system
    
    history = ai_safety_system.multimodal_auditor.get_audit_history(limit)
    return {
        "history": history,
        "total": len(history)
    }


@router.post("/streaming/reset")
async def reset_streaming_auditor() -> Dict[str, Any]:
    """重置流式审核器"""
    from ..ai_safety import ai_safety_system
    
    ai_safety_system.streaming_auditor.reset()
    return {"success": True, "message": "流式审核器已重置"}


@router.get("/config")
async def get_safety_config() -> Dict[str, Any]:
    """获取安全配置"""
    from ..ai_safety import ai_safety_system
    
    return {
        "abuse_protection": {
            "enabled": True,
            "action_rules": {
                "safe": "allow",
                "low": "allow_with_warning",
                "medium": "observe",
                "high": "intercept",
                "critical": "block"
            }
        },
        "watermark": {
            "enabled": True,
            "visible_default": True,
            "generator_name": ai_safety_system.watermarker.config.get("generator_name", "房都督AI")
        },
        "rag": {
            "enabled": True,
            "default_top_k": 5
        },
        "streaming_audit": {
            "enabled": True,
            "chunk_size": ai_safety_system.streaming_auditor.config.get("chunk_size", 100),
            "window_size": ai_safety_system.streaming_auditor.config.get("window_size", 200)
        }
    }
