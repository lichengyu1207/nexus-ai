"""
数据工程API路由
提供数据采集、清洗、增强、标注、评估等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import os
import sqlite3
from datetime import datetime
import logging

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..data_engine import (
    DataConfig, DataExporter, DataCleaner, TextPreprocessor,
    DataAugmentor, PersonaClassifier, IntentClassifier,
    DataQualityEvaluator, DatasetFormatter, DataPipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-engine", tags=["data-engine"])


class ExportDataRequest(BaseModel):
    source: str
    limit: Optional[int] = 100
    output_format: str = "instruction"
    min_quality: float = 0.5
    augment: bool = True
    augment_multiplier: int = 2


class ExportResponse(BaseModel):
    exported: int
    cleaned: int
    preprocessed: int
    augmented: int
    classified: int
    evaluated: int
    total_samples: int
    stats: Dict


class RunPipelineRequest(BaseModel):
    export_limit: Optional[int] = None
    augment: bool = True
    augment_multiplier: int = 2
    min_quality: float = 0.5
    output_format: str = "instruction"


    include_persona: bool = False


    persona_ratio: float = 0.5


class CleanRequest(BaseModel):
    remove_duplicates: bool = False
    remove_empty: bool = False
    min_length: int = 10
    max_length: int = 10000


class ClassifyRequest(BaseModel):
    text: str
    intent: Optional[str] = None


    persona: Optional[str] = None


class ClassifyResponse(BaseModel):
    intent: str
    persona: Optional[str]
    confidence: float


class EvaluateRequest(BaseModel):
    text: str
    intent: Optional[str] = None
    persona: Optional[str] = None


class EvaluateResponse(BaseModel):
    intent: str
    persona: Optional[str]
    confidence: float
    quality_score: float


class QualityReportRequest(BaseModel):
    pass


class PersonaSample(BaseModel):
    text: str
    persona: str
    style_keywords: List[str]
    phrases: List[str]
    greeting: str


@router.post("/export")
async def export_data(
    request: ExportDataRequest,
    current_user: dict = Depends(lambda: get_current_user())
) -> Dict:
        pipeline = DataPipeline()
        await pipeline.run(
            export_limit=request.export_limit,
            augment=request.augment,
            min_quality=request.min_quality,
            output_format=request.output_format,
            include_persona=request.include_persona,
            persona_ratio=request.persona_ratio
        )
        
        return {
            "exported": pipeline.stats['exported'],
            "cleaned": pipeline.stats['cleaned'],
            "preprocessed": pipeline.stats['preprocessed'],
            "augmented": pipeline.stats['augmented'],
            "classified": pipeline.stats['classified'],
            "evaluated": pipeline.stats['evaluated'],
            "total_samples": pipeline.stats['total_samples'],
        }


@router.post("/clean")
async def clean_data(
    request: CleanRequest,
    current_user: dict = Depends(lambda: get_current_user)
) -> Dict:
        pipeline = DataPipeline()
        pipeline.clean()
        
        return {
            "cleaned": pipeline.stats['cleaned'],
            "total_samples": pipeline.stats['total_samples']
        }


@router.post("/preprocess")
async def preprocess_data(
    request: PreprocessRequest,
    current_user: dict = Depends(lambda: get_current_user)
) -> Dict:
        pipeline = DataPipeline()
        pipeline.preprocess()
        
        return {
            "preprocessed": pipeline.stats['preprocessed'],
            "total_samples": pipeline.stats['total_samples']
        }


@router.post("/augment")
async def augment_data(
    request: AugmentRequest,
    current_user: dict = Depends(lambda: get_current_user)
) -> Dict:
        pipeline = DataPipeline()
        pipeline.augment(
            augment_multiplier=request.augment_multiplier,
            min_quality=request.min_quality,
        )
        
        return {
            "augmented": pipeline.stats['augmented'],
            "total_samples": pipeline.stats['total_samples']
        }


@router.post("/classify")
async def classify_data(
    request: ClassifyRequest,
    current_user: dict = Depends(lambda: get_current_user)
) -> ClassifyResponse:
        samples = pipeline.intent_classifier.classify_batch(
            [request.text], intent=request.intent, persona=request.persona
        )
        for s in samples:
            results.append({
                "text": s.text,
                "intent": r.intent,
                "persona": r.persona,
                "confidence": r.confidence
            })
        
        return ClassifyResponse(
            results=results,
            total=len(results)
        )


@router.post("/evaluate")
async def evaluate_data(
    request: EvaluateRequest,
    current_user: dict = Depends(lambda: get_current_user)
) -> Dict:
        pipeline = DataPipeline()
        results = pipeline.evaluator.evaluate_batch(
            [request.text], intent=request.intent, persona=request.persona
        )
        for r in results:
            results.append({
                "text": r.text,
                "intent": r.intent,
                "persona": r.persona,
                "confidence": r.confidence,
                "quality_score": r.quality_score
            })
        
        return EvaluateResponse(
            results=results,
            total=len(results)
        )


@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(lambda: get_current_user)
) -> Dict:
        pipeline = DataPipeline()
        return pipeline.get_stats()


@router.get("/registry")
async def list_registry(
    current_user: dict = Depends(lambda: get_current_user)
) -> List[Dict]:
        manager = DataRegistryManager()
        return manager.list_all()


@router.get("/report")
async def get_report(
    current_user: dict = Depends(lambda: get_current_user)
) -> Dict:
        pipeline = DataPipeline()
        return {
            "stats": pipeline.get_stats(),
            "samples": {
                "exported": samples["exported"],
                "cleaned": samples["cleaned"],
                "preprocessed": samples["preprocessed"],
                "augmented": samples["augmented"],
                "classified": samples["classified"],
                "evaluated": samples["evaluated"],
                "total_samples": len(samples),
                "quality_score": sum(
                    s.quality_score for s in samples if s.quality_score is not None
                else 0.0
                for s in samples
                ]
            )
        }
