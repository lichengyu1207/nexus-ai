"""
小区知识库与SEO内容系统 - API路由
包含搜索、详情、文章管理、收藏等功能
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from backend.database_pg import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/communities", tags=["知识库"])


class CommunitySearchRequest(BaseModel):
    keyword: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = "updated"  # updated, price, views


class CommunityResponse(BaseModel):
    id: str
    name: str
    alias: Optional[str]
    city: Optional[str]
    district: Optional[str]
    address: Optional[str]
    avg_price: Optional[float]
    price_unit: Optional[str]
    total_units: Optional[int]
    completion_year: Optional[int]
    developer: Optional[str]
    property_company: Optional[str]
    property_fee: Optional[float]
    green_rate: Optional[float]
    volume_rate: Optional[float]
    building_type: Optional[str]
    description: Optional[str]
    view_count: int
    favorite_count: int
    has_article: bool
    created_at: Optional[str]


class PriceTrendPoint(BaseModel):
    date: str
    price: float


class POIItem(BaseModel):
    id: str
    poi_type: str
    name: str
    address: Optional[str]
    distance: Optional[float]
    rating: Optional[float]


class CommunityDetailResponse(BaseModel):
    id: str
    name: str
    alias: Optional[str]
    city: Optional[str]
    district: Optional[str]
    address: Optional[str]
    lng: Optional[float]
    lat: Optional[float]
    avg_price: Optional[float]
    price_unit: Optional[str]
    total_units: Optional[int]
    completion_year: Optional[int]
    developer: Optional[str]
    property_company: Optional[str]
    property_fee: Optional[float]
    green_rate: Optional[float]
    volume_rate: Optional[float]
    parking_ratio: Optional[float]
    building_type: Optional[str]
    heating_type: Optional[str]
    description: Optional[str]
    data_source: Optional[str]
    confidence: Optional[float]
    view_count: int
    favorite_count: int
    price_trend: List[PriceTrendPoint]
    pois: Dict[str, List[POIItem]]
    article: Optional[Dict[str, Any]]
    created_at: Optional[str]


class ArticleResponse(BaseModel):
    id: str
    community_id: str
    title: str
    summary: Optional[str]
    content: str
    seo_title: Optional[str]
    seo_description: Optional[str]
    seo_keywords: Optional[str]
    slug: Optional[str]
    status: str
    views: int
    published_at: Optional[str]
    created_at: Optional[str]


class ArticleGenerateRequest(BaseModel):
    community_id: str
    template: Optional[str] = "default"


class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    status: Optional[str] = None


def datetime_to_str(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


@router.get("/search")
async def search_communities(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    city: Optional[str] = Query(None, description="城市"),
    district: Optional[str] = Query(None, description="区域"),
    price_min: Optional[float] = Query(None, description="最低价格"),
    price_max: Optional[float] = Query(None, description="最高价格"),
    year_min: Optional[int] = Query(None, description="最早建成年份"),
    year_max: Optional[int] = Query(None, description="最晚建成年份"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("updated", description="排序方式: updated, price, views")
):
    """搜索小区知识库"""
    async with get_db() as db:
        query = """
            SELECT c.id, c.name, c.alias, 
                   ci.name as city_name, d.name as district_name,
                   c.address, c.avg_price, c.price_unit, c.total_units,
                   c.completion_year, c.developer, c.property_company,
                   c.property_fee, c.green_rate, c.volume_rate, c.building_type,
                   c.description, c.view_count, c.favorite_count, c.created_at,
                   CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END as has_article
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            LEFT JOIN community_articles a ON c.id = a.community_id AND a.status = 'published'
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if keyword:
            query += f" AND (c.name ILIKE ${param_idx} OR c.alias ILIKE ${param_idx} OR c.address ILIKE ${param_idx})"
            params.append(f"%{keyword}%")
            param_idx += 1
        
        if city:
            query += f" AND (ci.name = ${param_idx} OR c.city_id = ${param_idx})"
            params.append(city)
            param_idx += 1
        
        if district:
            query += f" AND (d.name = ${param_idx} OR c.district_id = ${param_idx})"
            params.append(district)
            param_idx += 1
        
        if price_min is not None:
            query += f" AND c.avg_price >= ${param_idx}"
            params.append(price_min)
            param_idx += 1
        
        if price_max is not None:
            query += f" AND c.avg_price <= ${param_idx}"
            params.append(price_max)
            param_idx += 1
        
        if year_min is not None:
            query += f" AND c.completion_year >= ${param_idx}"
            params.append(year_min)
            param_idx += 1
        
        if year_max is not None:
            query += f" AND c.completion_year <= ${param_idx}"
            params.append(year_max)
            param_idx += 1
        
        if sort_by == "price":
            query += " ORDER BY c.avg_price DESC NULLS LAST"
        elif sort_by == "views":
            query += " ORDER BY c.view_count DESC"
        else:
            query += " ORDER BY c.last_updated DESC NULLS LAST, c.created_at DESC"
        
        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"
        
        rows = await db.fetch(query, *params)
        
        count_query = """
            SELECT COUNT(*) as total
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE 1=1
        """
        count_params = []
        param_idx = 1
        
        if keyword:
            count_query += f" AND (c.name ILIKE ${param_idx} OR c.alias ILIKE ${param_idx} OR c.address ILIKE ${param_idx})"
            count_params.append(f"%{keyword}%")
            param_idx += 1
        
        if city:
            count_query += f" AND (ci.name = ${param_idx} OR c.city_id = ${param_idx})"
            count_params.append(city)
            param_idx += 1
        
        if district:
            count_query += f" AND (d.name = ${param_idx} OR c.district_id = ${param_idx})"
            count_params.append(district)
            param_idx += 1
        
        if price_min is not None:
            count_query += f" AND c.avg_price >= ${param_idx}"
            count_params.append(price_min)
            param_idx += 1
        
        if price_max is not None:
            count_query += f" AND c.avg_price <= ${param_idx}"
            count_params.append(price_max)
            param_idx += 1
        
        if year_min is not None:
            count_query += f" AND c.completion_year >= ${param_idx}"
            count_params.append(year_min)
            param_idx += 1
        
        if year_max is not None:
            count_query += f" AND c.completion_year <= ${param_idx}"
            count_params.append(year_max)
            param_idx += 1
        
        total_row = await db.fetchone(count_query, *count_params)
        total = total_row['total'] if total_row else 0
        
        results = []
        for row in rows:
            results.append({
                "id": row['id'],
                "name": row['name'],
                "alias": row['alias'],
                "city": row['city_name'],
                "district": row['district_name'],
                "address": row['address'],
                "avg_price": row['avg_price'],
                "price_unit": row['price_unit'] or '元/㎡',
                "total_units": row['total_units'],
                "completion_year": row['completion_year'],
                "developer": row['developer'],
                "property_company": row['property_company'],
                "property_fee": row['property_fee'],
                "green_rate": row['green_rate'],
                "volume_rate": row['volume_rate'],
                "building_type": row['building_type'],
                "description": row['description'],
                "view_count": row['view_count'] or 0,
                "favorite_count": row['favorite_count'] or 0,
                "has_article": bool(row['has_article']),
                "created_at": datetime_to_str(row['created_at'])
            })
        
        return {
            "success": True,
            "data": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }


@router.get("/cities")
async def get_hot_cities():
    """获取热门城市列表"""
    async with get_db() as db:
        rows = await db.fetch("""
            SELECT id, city_name, province, avg_price, hot_districts, is_hot, sort_order
            FROM city_configs
            ORDER BY sort_order, is_hot DESC, city_name
        """)
        
        cities = []
        for row in rows:
            cities.append({
                "id": row['id'],
                "name": row['city_name'],
                "province": row['province'],
                "avg_price": row['avg_price'],
                "hot_districts": row['hot_districts'],
                "is_hot": bool(row['is_hot'])
            })
        
        return {"success": True, "data": cities}


@router.get("/{community_id}")
async def get_community_detail(community_id: str):
    """获取小区详情"""
    async with get_db() as db:
        row = await db.fetchone("""
            SELECT c.*, 
                   ci.name as city_name, d.name as district_name, s.name as street_name
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            LEFT JOIN streets s ON c.street_id = s.id
            WHERE c.id = $1
        """, community_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="小区不存在")
        
        await db.execute(
            "UPDATE communities SET view_count = COALESCE(view_count, 0) + 1 WHERE id = $1",
            community_id
        )
        
        price_rows = await db.fetch("""
            SELECT date, COALESCE(price, avg_price) as price
            FROM community_prices
            WHERE community_id = $1
            ORDER BY date ASC
            LIMIT 24
        """, community_id)
        
        price_trend = []
        for pr in price_rows:
            price_trend.append({
                "date": str(pr['date']),
                "price": pr['price']
            })
        
        poi_rows = await db.fetch("""
            SELECT id, poi_type, name, address, distance, rating
            FROM community_pois
            WHERE community_id = $1
            ORDER BY distance ASC
        """, community_id)
        
        pois = {}
        for poi in poi_rows:
            poi_type = poi['poi_type']
            if poi_type not in pois:
                pois[poi_type] = []
            pois[poi_type].append({
                "id": poi['id'],
                "poi_type": poi_type,
                "name": poi['name'],
                "address": poi['address'],
                "distance": poi['distance'],
                "rating": poi['rating']
            })
        
        article = await db.fetchone("""
            SELECT id, title, summary, content, seo_title, seo_description, 
                   seo_keywords, slug, status, views, published_at, created_at
            FROM community_articles
            WHERE community_id = $1 AND status = 'published'
        """, community_id)
        
        article_data = None
        if article:
            article_data = {
                "id": article['id'],
                "title": article['title'],
                "summary": article['summary'],
                "content": article['content'],
                "seo_title": article['seo_title'],
                "seo_description": article['seo_description'],
                "seo_keywords": article['seo_keywords'],
                "slug": article['slug'],
                "status": article['status'],
                "views": article['views'],
                "published_at": datetime_to_str(article['published_at']),
                "created_at": datetime_to_str(article['created_at'])
            }
        
        return {
            "success": True,
            "data": {
                "id": row['id'],
                "name": row['name'],
                "alias": row['alias'],
                "city": row['city_name'],
                "district": row['district_name'],
                "street": row['street_name'],
                "address": row['address'],
                "lng": row['lng'],
                "lat": row['lat'],
                "avg_price": row['avg_price'],
                "price_unit": row['price_unit'] or '元/㎡',
                "total_units": row['total_units'],
                "completion_year": row['completion_year'],
                "developer": row['developer'],
                "property_company": row['property_company'],
                "property_fee": row['property_fee'],
                "green_rate": row['green_rate'],
                "volume_rate": row['volume_rate'],
                "parking_ratio": row['parking_ratio'],
                "building_type": row['building_type'],
                "heating_type": row['heating_type'],
                "description": row['description'],
                "data_source": row['data_source'],
                "confidence": row['confidence'],
                "view_count": row['view_count'] or 0,
                "favorite_count": row['favorite_count'] or 0,
                "price_trend": price_trend,
                "pois": pois,
                "article": article_data,
                "created_at": datetime_to_str(row['created_at'])
            }
        }


@router.get("/{community_id}/price-trend")
async def get_price_trend(community_id: str, months: int = Query(12, ge=1, le=36)):
    """获取价格趋势数据"""
    async with get_db() as db:
        rows = await db.fetch("""
            SELECT date, COALESCE(price, avg_price) as price, price_unit, source
            FROM community_prices
            WHERE community_id = $1
            ORDER BY date DESC
            LIMIT $2
        """, community_id, months)
        
        trend = []
        for row in reversed(rows):
            trend.append({
                "date": str(row['date']),
                "price": row['price'],
                "price_unit": row['price_unit'],
                "source": row['source']
            })
        
        return {"success": True, "data": trend}


@router.post("/{community_id}/favorite")
async def toggle_favorite(community_id: str, user_id: str = Query(..., description="用户ID")):
    """收藏/取消收藏小区"""
    async with get_db() as db:
        existing = await db.fetchone(
            "SELECT id FROM user_favorite_communities WHERE user_id = $1 AND community_id = $2",
            user_id, community_id
        )
        
        if existing:
            await db.execute(
                "DELETE FROM user_favorite_communities WHERE user_id = $1 AND community_id = $2",
                user_id, community_id
            )
            await db.execute(
                "UPDATE communities SET favorite_count = GREATEST(0, COALESCE(favorite_count, 0) - 1) WHERE id = $1",
                community_id
            )
            return {"success": True, "action": "unfavorited", "message": "已取消收藏"}
        else:
            await db.execute(
                "INSERT INTO user_favorite_communities (id, user_id, community_id) VALUES ($1, $2, $3)",
                str(uuid.uuid4()), user_id, community_id
            )
            await db.execute(
                "UPDATE communities SET favorite_count = COALESCE(favorite_count, 0) + 1 WHERE id = $1",
                community_id
            )
            return {"success": True, "action": "favorited", "message": "已收藏"}


@router.get("/user/{user_id}/favorites")
async def get_user_favorites(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取用户收藏列表"""
    async with get_db() as db:
        offset = (page - 1) * page_size
        
        rows = await db.fetch("""
            SELECT c.id, c.name, c.alias, 
                   ci.name as city_name, d.name as district_name,
                   c.address, c.avg_price, c.price_unit, c.completion_year,
                   c.developer, c.property_company, c.view_count, c.favorite_count,
                   f.created_at as favorited_at
            FROM user_favorite_communities f
            JOIN communities c ON f.community_id = c.id
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE f.user_id = $1
            ORDER BY f.created_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, page_size, offset)
        
        total_row = await db.fetchone(
            "SELECT COUNT(*) as total FROM user_favorite_communities WHERE user_id = $1",
            user_id
        )
        total = total_row['total'] if total_row else 0
        
        results = []
        for row in rows:
            results.append({
                "id": row['id'],
                "name": row['name'],
                "alias": row['alias'],
                "city": row['city_name'],
                "district": row['district_name'],
                "address": row['address'],
                "avg_price": row['avg_price'],
                "price_unit": row['price_unit'] or '元/㎡',
                "completion_year": row['completion_year'],
                "developer": row['developer'],
                "property_company": row['property_company'],
                "view_count": row['view_count'] or 0,
                "favorite_count": row['favorite_count'] or 0,
                "favorited_at": datetime_to_str(row['favorited_at'])
            })
        
        return {
            "success": True,
            "data": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }


@router.get("/article/{article_id}")
async def get_article(article_id: str):
    """获取文章详情"""
    async with get_db() as db:
        article = await db.fetchone("""
            SELECT a.*, c.name as community_name,
                   ci.name as city_name, d.name as district_name
            FROM community_articles a
            JOIN communities c ON a.community_id = c.id
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE a.id = $1 AND a.status = 'published'
        """, article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        await db.execute(
            "UPDATE community_articles SET views = COALESCE(views, 0) + 1 WHERE id = $1",
            article_id
        )
        
        return {
            "success": True,
            "data": {
                "id": article['id'],
                "community_id": article['community_id'],
                "community_name": article['community_name'],
                "city": article['city_name'],
                "district": article['district_name'],
                "title": article['title'],
                "summary": article['summary'],
                "content": article['content'],
                "seo_title": article['seo_title'],
                "seo_description": article['seo_description'],
                "seo_keywords": article['seo_keywords'],
                "slug": article['slug'],
                "status": article['status'],
                "views": (article['views'] or 0) + 1,
                "published_at": datetime_to_str(article['published_at']),
                "created_at": datetime_to_str(article['created_at'])
            }
        }


@router.get("/article/slug/{slug}")
async def get_article_by_slug(slug: str):
    """通过slug获取文章详情（SEO友好URL）"""
    async with get_db() as db:
        article = await db.fetchone("""
            SELECT a.*, c.name as community_name,
                   ci.name as city_name, d.name as district_name
            FROM community_articles a
            JOIN communities c ON a.community_id = c.id
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE a.slug = $1 AND a.status = 'published'
        """, slug)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        await db.execute(
            "UPDATE community_articles SET views = COALESCE(views, 0) + 1 WHERE id = $1",
            article['id']
        )
        
        return {
            "success": True,
            "data": {
                "id": article['id'],
                "community_id": article['community_id'],
                "community_name": article['community_name'],
                "city": article['city_name'],
                "district": article['district_name'],
                "title": article['title'],
                "summary": article['summary'],
                "content": article['content'],
                "seo_title": article['seo_title'],
                "seo_description": article['seo_description'],
                "seo_keywords": article['seo_keywords'],
                "slug": article['slug'],
                "status": article['status'],
                "views": (article['views'] or 0) + 1,
                "published_at": datetime_to_str(article['published_at']),
                "created_at": datetime_to_str(article['created_at'])
            }
        }


@router.post("/{community_id}/review")
async def add_review(
    community_id: str,
    user_id: str = Query(..., description="用户ID"),
    rating: int = Query(..., ge=1, le=5, description="评分"),
    content: str = Query(..., description="评论内容"),
    is_anonymous: bool = Query(False, description="是否匿名")
):
    """添加小区评论"""
    async with get_db() as db:
        community = await db.fetchone(
            "SELECT id FROM communities WHERE id = $1", community_id
        )
        if not community:
            raise HTTPException(status_code=404, detail="小区不存在")
        
        review_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO community_reviews (id, community_id, user_id, rating, content, is_anonymous)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, review_id, community_id, user_id, rating, content, 1 if is_anonymous else 0)
        
        return {
            "success": True,
            "data": {
                "id": review_id,
                "community_id": community_id,
                "rating": rating,
                "content": content,
                "is_anonymous": is_anonymous
            },
            "message": "评论已提交"
        }


@router.get("/{community_id}/reviews")
async def get_reviews(
    community_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """获取小区评论列表"""
    async with get_db() as db:
        offset = (page - 1) * page_size
        
        rows = await db.fetch("""
            SELECT id, user_id, rating, content, is_anonymous, created_at
            FROM community_reviews
            WHERE community_id = $1 AND status = 'active'
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """, community_id, page_size, offset)
        
        total_row = await db.fetchone(
            "SELECT COUNT(*) as total FROM community_reviews WHERE community_id = $1 AND status = 'active'",
            community_id
        )
        total = total_row['total'] if total_row else 0
        
        avg_row = await db.fetchone(
            "SELECT AVG(rating) as avg_rating FROM community_reviews WHERE community_id = $1 AND status = 'active'",
            community_id
        )
        avg_rating = round(avg_row['avg_rating'], 1) if avg_row and avg_row['avg_rating'] else 0
        
        results = []
        for row in rows:
            results.append({
                "id": row['id'],
                "user_id": row['user_id'][:8] + '***' if row['is_anonymous'] else row['user_id'],
                "rating": row['rating'],
                "content": row['content'],
                "is_anonymous": bool(row['is_anonymous']),
                "created_at": datetime_to_str(row['created_at'])
            })
        
        return {
            "success": True,
            "data": results,
            "stats": {
                "total": total,
                "avg_rating": avg_rating
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
