# -*- coding: utf-8 -*-
"""
扣子数据接收API路由
用于接收扣子的信息流、数据、爬虫结果并转化到Pssq数据库
"""
from fastapi import APIRouter, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
import json

from ..services.kouzi import KouziService, get_kouzi_config
from ..services.kouzi.models import ReceiveResult, TransformResult

router = APIRouter(prefix="/kouzi", tags=["扣子数据接收"])

kouzi_service = KouziService()


class StreamReceiveRequest(BaseModel):
    source_type: str = Field(..., description="数据源类型")
    source_name: str = Field(..., description="数据源名称")
    content: Dict[str, Any] = Field(..., description="数据内容")
    content_type: str = Field(default="json", description="内容类型")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")


class BatchReceiveRequest(BaseModel):
    items: List[StreamReceiveRequest] = Field(..., description="批量数据项")


class CrawlerResultRequest(BaseModel):
    crawler_id: str = Field(..., description="爬虫ID")
    crawler_type: str = Field(..., description="爬虫类型")
    target_url: str = Field(..., description="目标URL")
    raw_data: Dict[str, Any] = Field(..., description="原始数据")
    parsed_data: Optional[Dict[str, Any]] = Field(default=None, description="解析后数据")
    images: Optional[List[Dict[str, Any]]] = Field(default=None, description="图片列表")
    documents: Optional[List[Dict[str, Any]]] = Field(default=None, description="文档列表")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class TransformRequest(BaseModel):
    stream_id: str = Field(..., description="数据流ID")
    transform_type: str = Field(default="auto", description="转化类型")
    mapping: Optional[Dict[str, str]] = Field(default=None, description="字段映射")


class WebhookPayload(BaseModel):
    event_type: str = Field(..., description="事件类型")
    timestamp: Optional[datetime] = Field(default=None, description="时间戳")
    data: Dict[str, Any] = Field(..., description="数据内容")
    signature: Optional[str] = Field(default=None, description="签名")


@router.post("/stream/receive", summary="接收单个数据流")
async def receive_stream(request: StreamReceiveRequest):
    result = await kouzi_service.receiver.receive_stream(
        source_type=request.source_type,
        source_name=request.source_name,
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata,
        priority=request.priority
    )
    
    return result.to_dict()


@router.post("/stream/batch", summary="批量接收数据流")
async def receive_batch(request: BatchReceiveRequest):
    items = [
        {
            "source_type": item.source_type,
            "source_name": item.source_name,
            "content": item.content,
            "content_type": item.content_type,
            "metadata": item.metadata,
            "priority": item.priority
        }
        for item in request.items
    ]
    
    results = await kouzi_service.receiver.receive_batch(items)
    
    return {
        "success": True,
        "total": len(results),
        "results": [r.to_dict() for r in results]
    }


@router.post("/stream/receive-transform", summary="接收并自动转化")
async def receive_and_transform(request: StreamReceiveRequest):
    result = await kouzi_service.receive_and_transform(
        source_type=request.source_type,
        source_name=request.source_name,
        content=request.content,
        content_type=request.content_type,
        metadata=request.metadata
    )
    
    return result


@router.post("/crawler/result", summary="接收爬虫结果")
async def receive_crawler_result(request: CrawlerResultRequest):
    result = await kouzi_service.crawler_handler.handle_crawler_result(
        crawler_id=request.crawler_id,
        crawler_type=request.crawler_type,
        target_url=request.target_url,
        raw_data=request.raw_data,
        parsed_data=request.parsed_data,
        images=request.images,
        documents=request.documents,
        metadata=request.metadata
    )
    
    return result.to_dict()


@router.post("/crawler/result-transform", summary="接收爬虫结果并转化")
async def receive_crawler_and_transform(request: CrawlerResultRequest):
    result = await kouzi_service.receive_crawler_and_transform(
        crawler_id=request.crawler_id,
        crawler_type=request.crawler_type,
        target_url=request.target_url,
        raw_data=request.raw_data,
        parsed_data=request.parsed_data,
        images=request.images,
        documents=request.documents,
        metadata=request.metadata
    )
    
    return result


@router.post("/crawler/task", summary="创建爬虫任务")
async def create_crawler_task(
    crawler_type: str,
    target_url: str,
    metadata: Optional[Dict[str, Any]] = None
):
    crawler_id = await kouzi_service.crawler_handler.create_crawl_task(
        crawler_type=crawler_type,
        target_url=target_url,
        metadata=metadata
    )
    
    if crawler_id:
        return {
            "success": True,
            "crawler_id": crawler_id,
            "message": "Crawler task created successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create crawler task")


@router.get("/crawler/status/{crawler_id}", summary="获取爬虫任务状态")
async def get_crawler_status(crawler_id: str):
    data = await kouzi_service.crawler_handler.get_crawler_data(crawler_id)
    
    if data:
        return data.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Crawler task not found")


@router.post("/crawler/retry/{crawler_id}", summary="重试失败的爬虫任务")
async def retry_crawler_task(crawler_id: str):
    success = await kouzi_service.crawler_handler.retry_failed_crawl(crawler_id)
    
    return {
        "success": success,
        "message": "Crawler task queued for retry" if success else "Retry limit exceeded"
    }


@router.post("/transform", summary="手动转化数据")
async def transform_data(request: TransformRequest):
    stream = await kouzi_service.receiver.get_stream(request.stream_id)
    
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if request.transform_type == "property":
        result = await kouzi_service.transformer.transform_to_property(
            stream, request.mapping
        )
    elif request.transform_type == "market_data":
        result = await kouzi_service.transformer.transform_to_market_data(
            stream, request.mapping
        )
    else:
        result = await kouzi_service.transformer.auto_transform(stream)
    
    return result.to_dict()


@router.post("/webhook/{webhook_type}", summary="Webhook接收端点")
async def receive_webhook(
    webhook_type: str,
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    result = await kouzi_service.process_webhook(
        webhook_type=webhook_type,
        payload=payload.dict(),
        signature=x_signature or payload.signature
    )
    
    return result


@router.post("/webhook/property/stream", summary="房产信息流Webhook")
async def property_stream_webhook(request: Request):
    payload = await request.json()
    signature = request.headers.get("X-Signature")
    
    result = await kouzi_service.process_webhook(
        webhook_type="property_stream",
        payload=payload,
        signature=signature
    )
    
    return result


@router.post("/webhook/crawler/callback", summary="爬虫回调Webhook")
async def crawler_callback_webhook(request: Request):
    payload = await request.json()
    signature = request.headers.get("X-Signature")
    
    result = await kouzi_service.process_webhook(
        webhook_type="crawler_callback",
        payload=payload,
        signature=signature
    )
    
    return result


@router.post("/webhook/market/data", summary="市场数据Webhook")
async def market_data_webhook(request: Request):
    payload = await request.json()
    signature = request.headers.get("X-Signature")
    
    result = await kouzi_service.process_webhook(
        webhook_type="market_data",
        payload=payload,
        signature=signature
    )
    
    return result


@router.get("/stream/{stream_id}", summary="获取数据流详情")
async def get_stream(stream_id: str):
    stream = await kouzi_service.receiver.get_stream(stream_id)
    
    if stream:
        return stream.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Stream not found")


@router.get("/stream/pending", summary="获取待处理数据流")
async def get_pending_streams(limit: int = 100):
    streams = await kouzi_service.receiver.get_pending_streams(limit)
    
    return {
        "success": True,
        "count": len(streams),
        "streams": [s.to_dict() for s in streams]
    }


@router.get("/statistics", summary="获取统计数据")
async def get_statistics():
    stats = await kouzi_service.get_statistics()
    
    return {
        "success": True,
        "statistics": stats
    }


@router.get("/health", summary="健康检查")
async def health_check():
    health = await kouzi_service.health_check()
    
    return health


@router.get("/config", summary="获取配置信息")
async def get_config():
    config = get_kouzi_config()
    
    return {
        "success": True,
        "config": config.to_dict()
    }


@router.post("/reset", summary="重置服务")
async def reset_service():
    await kouzi_service.close()
    
    return {
        "success": True,
        "message": "Service reset successfully"
    }
