"""
数据工程API路由
提供数据采集、清洗、增强、标注、评估等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-engine", tags=["data-engine"])


class RunPipelineRequest(BaseModel):
    export_limit: Optional[int] = None
    augment: bool = True
    augment_multiplier: int = 2
    min_quality: float = 0.5
    output_format: str = "chat"


class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    intent: str
    persona: str
    confidence: float


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取数据工程统计信息"""
    from ..data_engineering.pipeline import data_pipeline
    
    return {
        "stats": data_pipeline.stats,
        "total_samples": data_pipeline.stats.get("evaluated", 0),
    }


@router.get("/registry")
async def list_registry() -> List[Dict[str, Any]]:
    """列出所有已注册的数据集版本"""
    from ..data_engineering.pipeline import DataRegistryManager
    
    manager = DataRegistryManager()
    registries = manager.list_all()
    return [r.to_dict() for r in registries]


@router.post("/run")
async def run_pipeline(request: RunPipelineRequest) -> Dict[str, Any]:
    """运行数据工程流水线"""
    from ..data_engineering.pipeline import data_pipeline
    
    try:
        result = data_pipeline.run(
            export_limit=request.export_limit,
            augment=request.augment,
            augment_multiplier=request.augment_multiplier,
            min_quality=request.min_quality,
            output_format=request.output_format
        )
        return result
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify_text(request: ClassifyRequest) -> ClassifyResponse:
    """对文本进行意图和角色分类"""
    from ..data_engineering.pipeline import IntentClassifier, PersonaClassifier
    
    intent_classifier = IntentClassifier()
    persona_classifier = PersonaClassifier()
    
    intent, intent_conf = intent_classifier.classify(request.text)
    persona, persona_conf = persona_classifier.classify(request.text)
    
    return ClassifyResponse(
        intent=intent,
        persona=persona,
        confidence=(intent_conf + persona_conf) / 2
    )


@router.get("/samples")
async def get_samples(
    limit: int = Query(100, ge=1, le=1000),
    min_quality: float = Query(0.0, ge=0.0, le=1.0)
) -> Dict[str, Any]:
    """获取数据样本列表"""
    from ..data_engineering.pipeline import DataExporter
    
    exporter = DataExporter()
    samples = exporter.export_all(limit=limit)
    
    result = []
    for sample in samples[:limit]:
        sample_dict = sample.to_dict()
        if sample.quality_score >= min_quality:
            result.append(sample_dict)
    
    return {
        "samples": result,
        "total": len(result)
    }


@router.get("/quality-report")
async def get_quality_report() -> Dict[str, Any]:
    """获取数据质量报告"""
    from ..data_engineering.pipeline import DataExporter, DataQualityEvaluator
    
    exporter = DataExporter()
    samples = exporter.export_all(limit=1000)
    
    evaluator = DataQualityEvaluator()
    report = evaluator.evaluate_batch(samples)
    
    return report


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """获取数据工程配置"""
    from ..data_engineering.pipeline import DataConfig
    
    return {
        "data_dir": DataConfig.DATA_DIR,
        "raw_dir": DataConfig.RAW_DIR,
        "processed_dir": DataConfig.PROCESSED_DIR,
        "annotated_dir": DataConfig.ANNOTATED_DIR,
        "final_dir": DataConfig.FINAL_DIR,
        "augmented_dir": DataConfig.AUGMENTED_DIR,
        "persona_styles": {
            "zhouyu": DataConfig.ZHOUYU_STYLE,
            "luxun": DataConfig.LUXUN_STYLE
        }
    }
