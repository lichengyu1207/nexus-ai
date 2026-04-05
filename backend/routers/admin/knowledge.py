"""
知识库管理API路由
包含：户型面积管理、区域房价管理、区域介绍管理
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime
import uuid

from ...auth import get_current_user, require_admin
from ...database import get_db_connection

router = APIRouter(prefix="/api/admin/knowledge", tags=["admin-knowledge"])

# ==================== 户型面积管理 ====================

@router.get("/area-stats")
async def list_area_stats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: Optional[str] = Query(None),
    layout_type: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """获取户型面积统计列表"""
    conn = await get_db_connection()
    try:
        offset = (page - 1) * page_size
        conditions = []
        params = []
        
        if city:
            conditions.append("city = ?")
            params.append(city)
        if layout_type:
            conditions.append("type = ?")
            params.append(layout_type)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_query = f"SELECT COUNT(*) FROM house_type_area_stats WHERE {where_clause}"
        cursor = await conn.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        query = f"""
            SELECT id, city, type, avg_area, min_area, max_area, source, created_at
            FROM house_type_area_stats
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "city": row[1],
                "layout_type": row[2],
                "avg_area": row[3],
                "min_area": row[4],
                "max_area": row[5],
                "source": row[6],
                "created_at": row[7]
            })
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    finally:
        await conn.close()

@router.post("/area-stats")
async def create_area_stat(
    data: dict,
    admin: dict = Depends(require_admin)
):
    """创建户型面积统计"""
    conn = await get_db_connection()
    try:
        stat_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        await conn.execute("""
            INSERT INTO area_stats (id, city, district, layout_type, avg_area, min_area, max_area, sample_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stat_id,
            data.get("city"),
            data.get("district"),
            data.get("layout_type"),
            data.get("avg_area"),
            data.get("min_area"),
            data.get("max_area"),
            data.get("sample_count", 0),
            now,
            now
        ))
        await conn.commit()
        
        return {"id": stat_id, "message": "创建成功"}
    finally:
        await conn.close()

@router.put("/area-stats/{stat_id}")
async def update_area_stat(
    stat_id: str,
    data: dict,
    admin: dict = Depends(require_admin)
):
    """更新户型面积统计"""
    conn = await get_db_connection()
    try:
        now = datetime.now().isoformat()
        
        await conn.execute("""
            UPDATE area_stats
            SET city = ?, district = ?, layout_type = ?, avg_area = ?, min_area = ?, max_area = ?, sample_count = ?, updated_at = ?
            WHERE id = ?
        """, (
            data.get("city"),
            data.get("district"),
            data.get("layout_type"),
            data.get("avg_area"),
            data.get("min_area"),
            data.get("max_area"),
            data.get("sample_count", 0),
            now,
            stat_id
        ))
        await conn.commit()
        
        return {"message": "更新成功"}
    finally:
        await conn.close()

@router.delete("/area-stats/{stat_id}")
async def delete_area_stat(
    stat_id: str,
    admin: dict = Depends(require_admin)
):
    """删除户型面积统计"""
    conn = await get_db_connection()
    try:
        await conn.execute("DELETE FROM area_stats WHERE id = ?", (stat_id,))
        await conn.commit()
        
        return {"message": "删除成功"}
    finally:
        await conn.close()

# ==================== 区域房价管理 ====================

@router.get("/price-stats")
async def list_price_stats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """获取区域房价统计列表"""
    conn = await get_db_connection()
    try:
        offset = (page - 1) * page_size
        conditions = []
        params = []
        
        if city:
            conditions.append("city = ?")
            params.append(city)
        if district:
            conditions.append("district = ?")
            params.append(district)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_query = f"SELECT COUNT(*) FROM price_stats WHERE {where_clause}"
        cursor = await conn.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        query = f"""
            SELECT id, city, district, avg_price, min_price, max_price, price_per_sqm, trend, sample_count, created_at, updated_at
            FROM price_stats
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "city": row[1],
                "district": row[2],
                "avg_price": row[3],
                "min_price": row[4],
                "max_price": row[5],
                "price_per_sqm": row[6],
                "trend": row[7],
                "sample_count": row[8],
                "created_at": row[9],
                "updated_at": row[10]
            })
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    finally:
        await conn.close()

@router.post("/price-stats")
async def create_price_stat(
    data: dict,
    admin: dict = Depends(require_admin)
):
    """创建区域房价统计"""
    conn = await get_db_connection()
    try:
        stat_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        await conn.execute("""
            INSERT INTO price_stats (id, city, district, avg_price, min_price, max_price, price_per_sqm, trend, sample_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stat_id,
            data.get("city"),
            data.get("district"),
            data.get("avg_price"),
            data.get("min_price"),
            data.get("max_price"),
            data.get("price_per_sqm"),
            data.get("trend"),
            data.get("sample_count", 0),
            now,
            now
        ))
        await conn.commit()
        
        return {"id": stat_id, "message": "创建成功"}
    finally:
        await conn.close()

@router.put("/price-stats/{stat_id}")
async def update_price_stat(
    stat_id: str,
    data: dict,
    admin: dict = Depends(require_admin)
):
    """更新区域房价统计"""
    conn = await get_db_connection()
    try:
        now = datetime.now().isoformat()
        
        await conn.execute("""
            UPDATE price_stats
            SET city = ?, district = ?, avg_price = ?, min_price = ?, max_price = ?, price_per_sqm = ?, trend = ?, sample_count = ?, updated_at = ?
            WHERE id = ?
        """, (
            data.get("city"),
            data.get("district"),
            data.get("avg_price"),
            data.get("min_price"),
            data.get("max_price"),
            data.get("price_per_sqm"),
            data.get("trend"),
            data.get("sample_count", 0),
            now,
            stat_id
        ))
        await conn.commit()
        
        return {"message": "更新成功"}
    finally:
        await conn.close()

@router.delete("/price-stats/{stat_id}")
async def delete_price_stat(
    stat_id: str,
    admin: dict = Depends(require_admin)
):
    """删除区域房价统计"""
    conn = await get_db_connection()
    try:
        await conn.execute("DELETE FROM price_stats WHERE id = ?", (stat_id,))
        await conn.commit()
        
        return {"message": "删除成功"}
    finally:
        await conn.close()

# ==================== 区域介绍管理 ====================

@router.get("/district-info")
async def list_district_info(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """获取区域介绍列表"""
    conn = await get_db_connection()
    try:
        offset = (page - 1) * page_size
        conditions = []
        params = []
        
        if city:
            conditions.append("city = ?")
            params.append(city)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_query = f"SELECT COUNT(*) FROM district_info WHERE {where_clause}"
        cursor = await conn.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        query = f"""
            SELECT id, city, district, description, features, transportation, education, healthcare, commercial, created_at, updated_at
            FROM district_info
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "city": row[1],
                "district": row[2],
                "description": row[3],
                "features": row[4],
                "transportation": row[5],
                "education": row[6],
                "healthcare": row[7],
                "commercial": row[8],
                "created_at": row[9],
                "updated_at": row[10]
            })
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    finally:
        await conn.close()

@router.post("/district-info")
async def create_district_info(
    data: dict,
    admin: dict = Depends(require_admin)
):
    """创建区域介绍"""
    conn = await get_db_connection()
    try:
        info_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        await conn.execute("""
            INSERT INTO district_info (id, city, district, description, features, transportation, education, healthcare, commercial, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            info_id,
            data.get("city"),
            data.get("district"),
            data.get("description"),
            data.get("features"),
            data.get("transportation"),
            data.get("education"),
            data.get("healthcare"),
            data.get("commercial"),
            now,
            now
        ))
        await conn.commit()
        
        return {"id": info_id, "message": "创建成功"}
    finally:
        await conn.close()

@router.put("/district-info/{info_id}")
async def update_district_info(
    info_id: str,
    data: dict,
    admin: dict = Depends(require_admin)
):
    """更新区域介绍"""
    conn = await get_db_connection()
    try:
        now = datetime.now().isoformat()
        
        await conn.execute("""
            UPDATE district_info
            SET city = ?, district = ?, description = ?, features = ?, transportation = ?, education = ?, healthcare = ?, commercial = ?, updated_at = ?
            WHERE id = ?
        """, (
            data.get("city"),
            data.get("district"),
            data.get("description"),
            data.get("features"),
            data.get("transportation"),
            data.get("education"),
            data.get("healthcare"),
            data.get("commercial"),
            now,
            info_id
        ))
        await conn.commit()
        
        return {"message": "更新成功"}
    finally:
        await conn.close()

@router.delete("/district-info/{info_id}")
async def delete_district_info(
    info_id: str,
    admin: dict = Depends(require_admin)
):
    """删除区域介绍"""
    conn = await get_db_connection()
    try:
        await conn.execute("DELETE FROM district_info WHERE id = ?", (info_id,))
        await conn.commit()
        
        return {"message": "删除成功"}
    finally:
        await conn.close()
