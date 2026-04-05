"""
管理员地理位置管理API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from ...auth import require_super_admin
from ...database import LocationDB, get_db_connection
from ...services.geocoder import geocode_address

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/locations", tags=["admin-locations"])


class LocationResponse(BaseModel):
    """位置响应模型"""
    id: str
    user_id: str
    source: str
    address: str
    country: Optional[str]
    province: Optional[str]
    city: Optional[str]
    district: Optional[str]
    street: Optional[str]
    community: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    geocoded_at: Optional[str]
    created_at: Optional[str]
    user_email: Optional[str] = None


class LocationListResponse(BaseModel):
    """位置列表响应"""
    locations: List[LocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LocationUpdate(BaseModel):
    """位置更新模型"""
    address: Optional[str] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    community: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class LocationStatsResponse(BaseModel):
    """位置统计响应"""
    total: int
    geocoded: int
    not_geocoded: int
    by_source: Dict[str, int]
    by_province: List[Dict[str, Any]]


@router.get("", response_model=LocationListResponse)
async def list_locations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    is_geocoded: Optional[bool] = Query(None),
    province: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin: dict = Depends(require_super_admin)
):
    """
    获取位置列表
    
    Args:
        page: 页码
        page_size: 每页数量
        user_id: 用户ID筛选
        source: 来源筛选
        is_geocoded: 是否已地理编码
        province: 省份筛选
        city: 城市筛选
        search: 搜索关键词
        admin: 超级管理员
        
    Returns:
        LocationListResponse: 位置列表
    """
    conn = await get_db_connection()
    try:
        conditions = []
        params = []
        
        if user_id:
            conditions.append("l.user_id = ?")
            params.append(user_id)
        if source:
            conditions.append("l.source = ?")
            params.append(source)
        if is_geocoded is not None:
            if is_geocoded:
                conditions.append("l.longitude IS NOT NULL")
            else:
                conditions.append("l.longitude IS NULL")
        if province:
            conditions.append("l.province = ?")
            params.append(province)
        if city:
            conditions.append("l.city = ?")
            params.append(city)
        if search:
            conditions.append("(l.address LIKE ? OR l.community LIKE ? OR l.city LIKE ?)")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as count FROM user_locations l {where_clause}",
            params
        )
        total = (await count_cursor.fetchone())["count"]
        
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        cursor = await conn.execute(
            f"""
            SELECT l.*, u.email as user_email
            FROM user_locations l
            LEFT JOIN users u ON l.user_id = u.id
            {where_clause}
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset]
        )
        rows = await cursor.fetchall()
        
        locations = []
        for row in rows:
            locations.append(LocationResponse(
                id=row["id"],
                user_id=row["user_id"],
                source=row["source"],
                address=row["address"],
                country=row["country"],
                province=row["province"],
                city=row["city"],
                district=row["district"],
                street=row["street"],
                community=row["community"],
                longitude=row["longitude"],
                latitude=row["latitude"],
                geocoded_at=row["geocoded_at"],
                created_at=row["created_at"],
                user_email=row["user_email"]
            ))
        
        return LocationListResponse(
            locations=locations,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    finally:
        await conn.close()


@router.get("/stats", response_model=LocationStatsResponse)
async def get_location_stats(admin: dict = Depends(require_super_admin)):
    """
    获取位置统计
    
    Args:
        admin: 超级管理员
        
    Returns:
        LocationStatsResponse: 位置统计
    """
    conn = await get_db_connection()
    try:
        stats = {}
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_locations"
        )
        stats["total"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_locations WHERE longitude IS NOT NULL"
        )
        stats["geocoded"] = (await cursor.fetchone())["count"]
        
        stats["not_geocoded"] = stats["total"] - stats["geocoded"]
        
        cursor = await conn.execute(
            "SELECT source, COUNT(*) as count FROM user_locations GROUP BY source"
        )
        stats["by_source"] = {row["source"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            """
            SELECT province, COUNT(*) as count
            FROM user_locations
            WHERE province IS NOT NULL
            GROUP BY province
            ORDER BY count DESC
            LIMIT 10
            """
        )
        stats["by_province"] = [dict(row) for row in await cursor.fetchall()]
        
        return LocationStatsResponse(**stats)
    finally:
        await conn.close()


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    admin: dict = Depends(require_super_admin)
):
    """
    获取单个位置详情
    
    Args:
        location_id: 位置ID
        admin: 超级管理员
        
    Returns:
        LocationResponse: 位置详情
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT l.*, u.email as user_email
            FROM user_locations l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE l.id = ?
            """,
            (location_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="位置不存在")
        
        return LocationResponse(
            id=row["id"],
            user_id=row["user_id"],
            source=row["source"],
            address=row["address"],
            country=row["country"],
            province=row["province"],
            city=row["city"],
            district=row["district"],
            street=row["street"],
            community=row["community"],
            longitude=row["longitude"],
            latitude=row["latitude"],
            geocoded_at=row["geocoded_at"],
            created_at=row["created_at"],
            user_email=row["user_email"]
        )
    finally:
        await conn.close()


@router.put("/{location_id}")
async def update_location(
    location_id: str,
    update_data: LocationUpdate,
    admin: dict = Depends(require_super_admin)
):
    """
    更新位置信息
    
    Args:
        location_id: 位置ID
        update_data: 更新数据
        admin: 超级管理员
        
    Returns:
        更新结果
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM user_locations WHERE id = ?",
            (location_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="位置不存在")
        
        update_fields = []
        params = []
        
        if update_data.address is not None:
            update_fields.append("address = ?")
            params.append(update_data.address)
        if update_data.country is not None:
            update_fields.append("country = ?")
            params.append(update_data.country)
        if update_data.province is not None:
            update_fields.append("province = ?")
            params.append(update_data.province)
        if update_data.city is not None:
            update_fields.append("city = ?")
            params.append(update_data.city)
        if update_data.district is not None:
            update_fields.append("district = ?")
            params.append(update_data.district)
        if update_data.street is not None:
            update_fields.append("street = ?")
            params.append(update_data.street)
        if update_data.community is not None:
            update_fields.append("community = ?")
            params.append(update_data.community)
        if update_data.longitude is not None:
            update_fields.append("longitude = ?")
            params.append(update_data.longitude)
        if update_data.latitude is not None:
            update_fields.append("latitude = ?")
            params.append(update_data.latitude)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有要更新的字段")
        
        params.append(location_id)
        
        await conn.execute(
            f"UPDATE user_locations SET {', '.join(update_fields)} WHERE id = ?",
            params
        )
        await conn.commit()
        
        logger.info(f"Location updated: {location_id} by {admin.get('id')}")
        
        return {"message": "更新成功", "location_id": location_id}
    finally:
        await conn.close()


@router.post("/{location_id}/geocode")
async def regeocode_location(
    location_id: str,
    admin: dict = Depends(require_super_admin)
):
    """
    重新地理编码
    
    Args:
        location_id: 位置ID
        admin: 超级管理员
        
    Returns:
        地理编码结果
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM user_locations WHERE id = ?",
            (location_id,)
        )
        location = await cursor.fetchone()
        
        if not location:
            raise HTTPException(status_code=404, detail="位置不存在")
        
        result = await geocode_address(location["address"])
        
        if not result:
            raise HTTPException(status_code=400, detail="地理编码失败")
        
        await conn.execute(
            """
            UPDATE user_locations SET
                country = ?, province = ?, city = ?, district = ?,
                street = ?, community = ?, longitude = ?, latitude = ?,
                geocoded_at = ?
            WHERE id = ?
            """,
            (
                result.get("country"),
                result.get("province"),
                result.get("city"),
                result.get("district"),
                result.get("street"),
                result.get("community"),
                result.get("longitude"),
                result.get("latitude"),
                datetime.now().isoformat(),
                location_id
            )
        )
        await conn.commit()
        
        logger.info(f"Location re-geocoded: {location_id} by {admin.get('id')}")
        
        return {
            "message": "地理编码成功",
            "location_id": location_id,
            "result": result
        }
    finally:
        await conn.close()


@router.delete("/{location_id}")
async def delete_location(
    location_id: str,
    admin: dict = Depends(require_super_admin)
):
    """
    删除位置
    
    Args:
        location_id: 位置ID
        admin: 超级管理员
        
    Returns:
        删除结果
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM user_locations WHERE id = ?",
            (location_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="位置不存在")
        
        await conn.execute(
            "UPDATE reports SET location_id = NULL WHERE location_id = ?",
            (location_id,)
        )
        
        await conn.execute(
            "DELETE FROM user_locations WHERE id = ?",
            (location_id,)
        )
        await conn.commit()
        
        logger.info(f"Location deleted: {location_id} by {admin.get('id')}")
        
        return {"message": "删除成功", "location_id": location_id}
    finally:
        await conn.close()


@router.post("/batch-geocode")
async def batch_geocode(
    admin: dict = Depends(require_super_admin)
):
    """
    批量重新地理编码失败的地址
    
    Args:
        admin: 超级管理员
        
    Returns:
        批量处理结果
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT id, address FROM user_locations
            WHERE longitude IS NULL
            LIMIT 50
            """
        )
        locations = await cursor.fetchall()
        
        success_count = 0
        fail_count = 0
        
        for location in locations:
            try:
                result = await geocode_address(location["address"])
                
                if result:
                    await conn.execute(
                        """
                        UPDATE user_locations SET
                            country = ?, province = ?, city = ?, district = ?,
                            street = ?, community = ?, longitude = ?, latitude = ?,
                            geocoded_at = ?
                        WHERE id = ?
                        """,
                        (
                            result.get("country"),
                            result.get("province"),
                            result.get("city"),
                            result.get("district"),
                            result.get("street"),
                            result.get("community"),
                            result.get("longitude"),
                            result.get("latitude"),
                            datetime.now().isoformat(),
                            location["id"]
                        )
                    )
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Failed to geocode {location['id']}: {e}")
                fail_count += 1
        
        await conn.commit()
        
        logger.info(f"Batch geocode completed: {success_count} success, {fail_count} failed by {admin.get('id')}")
        
        return {
            "message": "批量地理编码完成",
            "success_count": success_count,
            "fail_count": fail_count,
            "total_processed": len(locations)
        }
    finally:
        await conn.close()
