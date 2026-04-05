"""
地理树节点API
用于城市数据可视化树状系统
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_db_connection
from backend.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/geo", tags=["地理树"])


class GeoNode(BaseModel):
    id: str
    name: str
    type: str
    stats: Dict[str, Any] = {}
    hasChildren: bool
    path: Optional[str] = None


class GeoNodeDetail(BaseModel):
    id: str
    name: str
    type: str
    stats: Dict[str, Any] = {}
    hasChildren: bool
    path: Optional[str] = None
    parent_id: Optional[str] = None
    parent_name: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    created_at: Optional[datetime] = None


class SearchResult(BaseModel):
    id: str
    name: str
    type: str
    path: str
    score: float


@router.get("/tree/roots", response_model=List[GeoNode])
async def get_roots(user=Depends(require_admin)):
    """获取根节点（所有省份）"""
    conn = await get_db_connection()
    
    try:
        cursor = await conn.execute('''
            SELECT p.id, p.name, 'province' as type,
                   COALESCE(ps.city_count, 0) as city_count,
                   COALESCE(ps.district_count, 0) as district_count,
                   COALESCE(ps.community_count, 0) as community_count,
                   COALESCE(ps.user_count, 0) as user_count,
                   COALESCE(ps.house_count, 0) as house_count
            FROM provinces p
            LEFT JOIN province_stats ps ON p.id = ps.province_id
            ORDER BY p.name
        ''')
        rows = await cursor.fetchall()
        
        return [
            GeoNode(
                id=row['id'],
                name=row['name'],
                type='province',
                stats={
                    'cityCount': row['city_count'],
                    'districtCount': row['district_count'],
                    'communityCount': row['community_count'],
                    'userCount': row['user_count'],
                    'houseCount': row['house_count']
                },
                hasChildren=True
            )
            for row in rows
        ]
        
    finally:
        await conn.close()


@router.get("/tree/children", response_model=List[GeoNode])
async def get_children(
    parentId: str,
    parentType: str,
    user=Depends(require_admin)
):
    """获取子节点"""
    conn = await get_db_connection()
    
    try:
        children = []
        
        if parentType == 'province':
            cursor = await conn.execute('''
                SELECT c.id, c.name, 'city' as type,
                       COALESCE(cs.district_count, 0) as district_count,
                       COALESCE(cs.community_count, 0) as community_count,
                       COALESCE(cs.user_count, 0) as user_count,
                       COALESCE(cs.house_count, 0) as house_count
                FROM cities c
                LEFT JOIN city_stats_new cs ON c.id = cs.city_id
                WHERE c.province_id = ?
                ORDER BY c.name
            ''', (parentId,))
            rows = await cursor.fetchall()
            children = [
                GeoNode(
                    id=row['id'],
                    name=row['name'],
                    type='city',
                    stats={
                        'districtCount': row['district_count'],
                        'communityCount': row['community_count'],
                        'userCount': row['user_count'],
                        'houseCount': row['house_count']
                    },
                    hasChildren=True
                )
                for row in rows
            ]
        
        elif parentType == 'city':
            cursor = await conn.execute('''
                SELECT d.id, d.name, 'district' as type,
                       COALESCE(ds.street_count, 0) as street_count,
                       COALESCE(ds.community_count, 0) as community_count,
                       COALESCE(ds.user_count, 0) as user_count,
                       COALESCE(ds.house_count, 0) as house_count
                FROM districts d
                LEFT JOIN district_stats ds ON d.id = ds.district_id
                WHERE d.city_id = ?
                ORDER BY d.name
            ''', (parentId,))
            rows = await cursor.fetchall()
            children = [
                GeoNode(
                    id=row['id'],
                    name=row['name'],
                    type='district',
                    stats={
                        'streetCount': row['street_count'],
                        'communityCount': row['community_count'],
                        'userCount': row['user_count'],
                        'houseCount': row['house_count']
                    },
                    hasChildren=True
                )
                for row in rows
            ]
        
        elif parentType == 'district':
            cursor = await conn.execute('''
                SELECT s.id, s.name, 'street' as type,
                       COALESCE(ss.community_count, 0) as community_count,
                       COALESCE(ss.user_count, 0) as user_count,
                       COALESCE(ss.house_count, 0) as house_count
                FROM streets s
                LEFT JOIN street_stats ss ON s.id = ss.street_id
                WHERE s.district_id = ?
                ORDER BY s.name
            ''', (parentId,))
            rows = await cursor.fetchall()
            children = [
                GeoNode(
                    id=row['id'],
                    name=row['name'],
                    type='street',
                    stats={
                        'communityCount': row['community_count'],
                        'userCount': row['user_count'],
                        'houseCount': row['house_count']
                    },
                    hasChildren=True
                )
                for row in rows
            ]
        
        elif parentType == 'street':
            cursor = await conn.execute('''
                SELECT c.id, c.name, 'community' as type,
                       c.address,
                       c.avg_price,
                       c.lng, c.lat,
                       COALESCE(cst.house_count, 0) as house_count
                FROM communities c
                LEFT JOIN community_stats cst ON c.id = cst.community_id
                WHERE c.street_id = ?
                ORDER BY c.name
            ''', (parentId,))
            rows = await cursor.fetchall()
            children = [
                GeoNode(
                    id=row['id'],
                    name=row['name'],
                    type='community',
                    stats={
                        'address': row['address'],
                        'avgPrice': row['avg_price'],
                        'houseCount': row['house_count'] or 0
                    },
                    hasChildren=False
                )
                for row in rows
            ]
        
        return children
        
    finally:
        await conn.close()


@router.get("/node/{node_id}", response_model=GeoNodeDetail)
async def get_node_detail(
    node_id: str,
    nodeType: str,
    user=Depends(require_admin)
):
    """获取节点详情"""
    conn = await get_db_connection()
    
    try:
        node = None
        
        if nodeType == 'province':
            cursor = await conn.execute(
                "SELECT id, name FROM provinces WHERE id = ?", (node_id,)
            )
            row = await cursor.fetchone()
            if row:
                node = GeoNodeDetail(
                    id=row['id'],
                    name=row['name'],
                    type='province',
                    stats={},
                    hasChildren=True
                )
        
        elif nodeType == 'city':
            cursor = await conn.execute('''
                SELECT c.id, c.name, c.province_id, p.name as province_name
                FROM cities c
                JOIN provinces p ON c.province_id = p.id
                WHERE c.id = ?
            ''', (node_id,))
            row = await cursor.fetchone()
            if row:
                node = GeoNodeDetail(
                    id=row['id'],
                    name=row['name'],
                    type='city',
                    stats={},
                    hasChildren=True,
                    parent_id=row['province_id'],
                    parent_name=row['province_name']
                )
        
        elif nodeType == 'district':
            cursor = await conn.execute('''
                SELECT d.id, d.name, d.city_id, c.name as city_name
                FROM districts d
                JOIN cities c ON d.city_id = c.id
                WHERE d.id = ?
            ''', (node_id,))
            row = await cursor.fetchone()
            if row:
                node = GeoNodeDetail(
                    id=row['id'],
                    name=row['name'],
                    type='district',
                    stats={},
                    hasChildren=True,
                    parent_id=row['city_id'],
                    parent_name=row['city_name']
                )
        
        elif nodeType == 'street':
            cursor = await conn.execute('''
                SELECT s.id, s.name, s.district_id, d.name as district_name
                FROM streets s
                JOIN districts d ON s.district_id = d.id
                WHERE s.id = ?
            ''', (node_id,))
            row = await cursor.fetchone()
            if row:
                node = GeoNodeDetail(
                    id=row['id'],
                    name=row['name'],
                    type='street',
                    stats={},
                    hasChildren=True,
                    parent_id=row['district_id'],
                    parent_name=row['district_name']
                )
        
        elif nodeType == 'community':
            cursor = await conn.execute('''
                SELECT c.id, c.name, c.address, c.avg_price, c.lng, c.lat
                FROM communities c
                WHERE c.id = ?
            ''', (node_id,))
            row = await cursor.fetchone()
            if row:
                node = GeoNodeDetail(
                    id=row['id'],
                    name=row['name'],
                    type='community',
                    stats={
                        'address': row['address'],
                        'avgPrice': row['avg_price']
                    },
                    hasChildren=False,
                    coordinates={'lng': row['lng'], 'lat': row['lat']} if row['lng'] and row['lat'] else None
                )
        
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        return node
        
    finally:
        await conn.close()


@router.get("/search", response_model=List[SearchResult])
async def search_geo(
    q: str,
    limit: int = 10,
    user=Depends(require_admin)
):
    """搜索地理实体"""
    conn = await get_db_connection()
    
    try:
        results = []
        pattern = f"%{q}%"
        
        cursor = await conn.execute('''
            SELECT id, name, 'province' as type, name as path
            FROM provinces
            WHERE name LIKE ?
            ORDER BY name
            LIMIT ?
        ''', (pattern, limit // 2))
        rows = await cursor.fetchall()
        results.extend([
            SearchResult(id=row['id'], name=row['name'], type='province', path=row['path'], score=1.0)
            for row in rows
        ])
        
        cursor = await conn.execute('''
            SELECT c.id, c.name, 'city' as type, 
                   p.name || '/' || c.name as path
            FROM cities c
            JOIN provinces p ON c.province_id = p.id
            WHERE c.name LIKE ?
            ORDER BY c.name
            LIMIT ?
        ''', (pattern, limit // 2))
        rows = await cursor.fetchall()
        results.extend([
            SearchResult(id=row['id'], name=row['name'], type='city', path=row['path'], score=0.9)
            for row in rows
        ])
        
        cursor = await conn.execute('''
            SELECT d.id, d.name, 'district' as type,
                   p.name || '/' || c.name || '/' || d.name as path
            FROM districts d
            JOIN cities c ON d.city_id = c.id
            JOIN provinces p ON c.province_id = p.id
            WHERE d.name LIKE ?
            ORDER BY d.name
            LIMIT ?
        ''', (pattern, limit // 2))
        rows = await cursor.fetchall()
        results.extend([
            SearchResult(id=row['id'], name=row['name'], type='district', path=row['path'], score=0.8)
            for row in rows
        ])
        
        cursor = await conn.execute('''
            SELECT cm.id, cm.name, 'community' as type,
                   p.name || '/' || c.name || '/' || d.name || '/' || cm.name as path
            FROM communities cm
            JOIN districts d ON cm.district_id = d.id
            JOIN cities c ON d.city_id = c.id
            JOIN provinces p ON c.province_id = p.id
            WHERE cm.name LIKE ?
            ORDER BY cm.name
            LIMIT ?
        ''', (pattern, limit // 2))
        rows = await cursor.fetchall()
        results.extend([
            SearchResult(id=row['id'], name=row['name'], type='community', path=row['path'], score=0.7)
            for row in rows
        ])
        
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
        
    finally:
        await conn.close()
