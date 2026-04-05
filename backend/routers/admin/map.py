"""
管理员地图API路由
提供用户位置聚合数据
"""
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from ...auth import require_admin
from ...services.map_aggregator import (
    get_map_data,
    get_heatmap_data,
    get_location_summary,
    get_new_locations,
    get_map_stats,
)
from ...database import AuditDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/map", tags=["admin-map"])


class MapBounds(BaseModel):
    """地图边界"""
    north: float = Field(..., description="北边界纬度")
    south: float = Field(..., description="南边界纬度")
    east: float = Field(..., description="东边界经度")
    west: float = Field(..., description="西边界经度")


class MapDataResponse(BaseModel):
    """地图数据响应"""
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class HeatmapResponse(BaseModel):
    """热力图响应"""
    data: List[List[float]]
    metadata: Dict[str, Any]


class LocationSummaryResponse(BaseModel):
    """位置摘要响应"""
    total_locations: int
    geocoded_locations: int
    top_provinces: List[Dict[str, Any]]
    top_cities: List[Dict[str, Any]]
    by_source: Dict[str, int]


@router.get("/data", response_model=MapDataResponse)
async def get_data(
    request: Request,
    zoom_level: int = Query(5, ge=1, le=18, description="缩放级别 (1-18)"),
    north: Optional[float] = Query(None, description="北边界纬度"),
    south: Optional[float] = Query(None, description="南边界纬度"),
    east: Optional[float] = Query(None, description="东边界经度"),
    west: Optional[float] = Query(None, description="西边界经度"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    admin: dict = Depends(require_admin)
):
    """
    获取地图聚合数据
    
    根据缩放级别返回不同粒度的聚合数据：
    - 1-4: 按省份聚合
    - 5-7: 按城市聚合
    - 8-10: 按区县聚合
    - 11-18: 返回点数据（最多500个）
    
    Args:
        request: 请求对象
        zoom_level: 缩放级别
        north, south, east, west: 地图边界（可选）
        start_date: 开始日期
        end_date: 结束日期
        admin: 管理员用户
        
    Returns:
        MapDataResponse: GeoJSON FeatureCollection
    """
    try:
        await AuditDB.create_log(
            log_id=str(__import__('uuid').uuid4()),
            user_id=admin.get('id', 'unknown'),
            action='ADMIN_MAP_VIEW',
            resource_type='map',
            resource_id=None,
            details={
                'zoom_level': zoom_level,
                'bounds': {'north': north, 'south': south, 'east': east, 'west': west} if all([north, south, east, west]) else None,
                'start_date': start_date,
                'end_date': end_date
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )
    except Exception as e:
        logger.warning(f"Failed to create audit log: {e}")
    
    bounds = None
    if all([north, south, east, west]):
        bounds = {
            "north": north,
            "south": south,
            "east": east,
            "west": west
        }
    
    data = await get_map_data(
        zoom_level=zoom_level,
        bounds=bounds,
        start_date=start_date,
        end_date=end_date
    )
    
    return MapDataResponse(**data)


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    north: Optional[float] = Query(None, description="北边界纬度"),
    south: Optional[float] = Query(None, description="南边界纬度"),
    east: Optional[float] = Query(None, description="东边界经度"),
    west: Optional[float] = Query(None, description="西边界经度"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    radius: int = Query(25, ge=5, le=50, description="热力半径"),
    admin: dict = Depends(require_admin)
):
    """
    获取热力图数据
    
    Args:
        north, south, east, west: 地图边界
        start_date: 开始日期
        end_date: 结束日期
        radius: 热力半径
        admin: 管理员用户
        
    Returns:
        HeatmapResponse: 热力图数据
    """
    bounds = None
    if all([north, south, east, west]):
        bounds = {
            "north": north,
            "south": south,
            "east": east,
            "west": west
        }
    
    data = await get_heatmap_data(
        bounds=bounds,
        start_date=start_date,
        end_date=end_date,
        radius=radius
    )
    
    return HeatmapResponse(
        data=data,
        metadata={
            "total_points": len(data),
            "radius": radius
        }
    )


@router.get("/summary", response_model=LocationSummaryResponse)
async def get_summary(admin: dict = Depends(require_admin)):
    """
    获取位置数据摘要
    
    Args:
        admin: 管理员用户
        
    Returns:
        LocationSummaryResponse: 位置摘要
    """
    summary = await get_location_summary()
    return LocationSummaryResponse(**summary)


@router.get("/stats")
async def get_stats(admin: dict = Depends(require_admin)):
    """
    获取地图统计数据
    
    Args:
        admin: 管理员用户
        
    Returns:
        地图统计数据
    """
    stats = await get_map_stats()
    return stats


@router.get("/new-locations")
async def get_new_locations_endpoint(
    days: int = Query(30, ge=1, le=90, description="天数"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    admin: dict = Depends(require_admin)
):
    """
    获取新增位置列表
    
    Args:
        days: 天数阈值（默认30天）
        limit: 返回数量限制
        admin: 管理员用户
        
    Returns:
        新增位置列表
    """
    locations = await get_new_locations(days=days, limit=limit)
    return {
        "locations": locations,
        "days": days,
        "total": len(locations)
    }


@router.get("/clusters")
async def get_clusters(
    zoom_level: int = Query(5, ge=1, le=18),
    north: Optional[float] = Query(None),
    south: Optional[float] = Query(None),
    east: Optional[float] = Query(None),
    west: Optional[float] = Query(None),
    cluster_radius: int = Query(50, ge=10, le=200, description="聚类半径（像素）"),
    admin: dict = Depends(require_admin)
):
    """
    获取聚类数据（用于点聚合显示）
    
    Args:
        zoom_level: 缩放级别
        bounds: 地图边界
        cluster_radius: 聚类半径
        admin: 管理员用户
        
    Returns:
        dict: 聚类数据
    """
    bounds = None
    if all([north, south, east, west]):
        bounds = {
            "north": north,
            "south": south,
            "east": east,
            "west": west
        }
    
    data = await get_map_data(
        zoom_level=zoom_level,
        bounds=bounds
    )
    
    return {
        "type": "FeatureCollection",
        "features": data["features"],
        "metadata": {
            **data["metadata"],
            "cluster_radius": cluster_radius
        }
    }


@router.get("/export")
async def export_map_data(
    format: str = Query("geojson", description="导出格式 (geojson/csv)"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """
    导出地图数据
    
    Args:
        format: 导出格式
        start_date: 开始日期
        end_date: 结束日期
        admin: 管理员用户
        
    Returns:
        导出文件
    """
    from fastapi.responses import StreamingResponse
    import io
    
    data = await get_map_data(
        zoom_level=11,
        start_date=start_date,
        end_date=end_date
    )
    
    if format == "csv":
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["经度", "纬度", "名称", "级别", "数量"])
        
        for feature in data["features"]:
            coords = feature["geometry"]["coordinates"]
            props = feature["properties"]
            writer.writerow([
                coords[0],
                coords[1],
                props.get("name", ""),
                props.get("level", ""),
                props.get("count", 1)
            ])
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=map_data_{start_date or 'all'}.csv"
            }
        )
    
    import json
    
    return StreamingResponse(
        io.BytesIO(json.dumps(data, ensure_ascii=False).encode('utf-8')),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=map_data_{start_date or 'all'}.geojson"
        }
    )
