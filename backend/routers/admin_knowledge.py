"""
管理员文章管理API
包含文章列表、生成、编辑、发布、删除等功能
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import logging
import json

from backend.database_pg import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/communities", tags=["管理员-文章管理"])


class ArticleCreateRequest(BaseModel):
    community_id: str
    title: str
    summary: Optional[str] = None
    content: str
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    slug: Optional[str] = None


class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None


def datetime_to_str(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


@router.get("/articles")
async def list_articles(
    status: Optional[str] = Query(None, description="状态筛选: draft, published, archived"),
    city: Optional[str] = Query(None, description="城市筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取文章列表（管理员）"""
    async with get_db() as db:
        query = """
            SELECT a.id, a.community_id, a.title, a.summary, a.status, a.views,
                   a.seo_title, a.seo_description, a.seo_keywords, a.slug,
                   a.published_at, a.created_at, a.updated_at,
                   c.name as community_name,
                   ci.name as city_name, d.name as district_name
            FROM community_articles a
            JOIN communities c ON a.community_id = c.id
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if status:
            query += f" AND a.status = ${param_idx}"
            params.append(status)
            param_idx += 1
        
        if city:
            query += f" AND ci.name = ${param_idx}"
            params.append(city)
            param_idx += 1
        
        if keyword:
            query += f" AND (a.title ILIKE ${param_idx} OR c.name ILIKE ${param_idx})"
            params.append(f"%{keyword}%")
            param_idx += 1
        
        count_query = query.replace(
            "SELECT a.id, a.community_id, a.title, a.summary, a.status, a.views, a.seo_title, a.seo_description, a.seo_keywords, a.slug, a.published_at, a.created_at, a.updated_at, c.name as community_name, ci.name as city_name, d.name as district_name",
            "SELECT COUNT(*) as total"
        )
        
        query += " ORDER BY a.updated_at DESC NULLS LAST, a.created_at DESC"
        
        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"
        
        rows = await db.fetch(query, *params)
        total_row = await db.fetchone(count_query, *params)
        total = total_row['total'] if total_row else 0
        
        results = []
        for row in rows:
            results.append({
                "id": row['id'],
                "community_id": row['community_id'],
                "community_name": row['community_name'],
                "city": row['city_name'],
                "district": row['district_name'],
                "title": row['title'],
                "summary": row['summary'],
                "status": row['status'],
                "views": row['views'] or 0,
                "seo_title": row['seo_title'],
                "seo_description": row['seo_description'],
                "seo_keywords": row['seo_keywords'],
                "slug": row['slug'],
                "published_at": datetime_to_str(row['published_at']),
                "created_at": datetime_to_str(row['created_at']),
                "updated_at": datetime_to_str(row['updated_at'])
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


@router.get("/articles/{article_id}")
async def get_article_detail(article_id: str):
    """获取文章详情（管理员）"""
    async with get_db() as db:
        article = await db.fetchone("""
            SELECT a.*, c.name as community_name,
                   ci.name as city_name, d.name as district_name,
                   c.avg_price, c.address, c.completion_year,
                   c.developer, c.property_company, c.property_fee
            FROM community_articles a
            JOIN communities c ON a.community_id = c.id
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE a.id = $1
        """, article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
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
                "views": article['views'] or 0,
                "generated_by": article['generated_by'],
                "published_at": datetime_to_str(article['published_at']),
                "created_at": datetime_to_str(article['created_at']),
                "updated_at": datetime_to_str(article['updated_at']),
                "community_info": {
                    "avg_price": article['avg_price'],
                    "address": article['address'],
                    "completion_year": article['completion_year'],
                    "developer": article['developer'],
                    "property_company": article['property_company'],
                    "property_fee": article['property_fee']
                }
            }
        }


@router.post("/articles")
async def create_article(request: ArticleCreateRequest):
    """创建文章"""
    async with get_db() as db:
        community = await db.fetchone(
            "SELECT id FROM communities WHERE id = $1", request.community_id
        )
        if not community:
            raise HTTPException(status_code=404, detail="小区不存在")
        
        existing = await db.fetchone(
            "SELECT id FROM community_articles WHERE community_id = $1",
            request.community_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="该小区已有文章")
        
        article_id = str(uuid.uuid4())
        slug = request.slug or f"community-{request.community_id}"
        
        await db.execute("""
            INSERT INTO community_articles 
            (id, community_id, title, summary, content, seo_title, seo_description, seo_keywords, slug, status, generated_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft', 'admin')
        """, article_id, request.community_id, request.title, request.summary,
           request.content, request.seo_title, request.seo_description,
           request.seo_keywords, slug)
        
        return {
            "success": True,
            "data": {"id": article_id},
            "message": "文章创建成功"
        }


@router.put("/articles/{article_id}")
async def update_article(article_id: str, request: ArticleUpdateRequest):
    """更新文章"""
    async with get_db() as db:
        article = await db.fetchone(
            "SELECT id FROM community_articles WHERE id = $1", article_id
        )
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        updates = []
        params = [article_id]
        param_idx = 2
        
        if request.title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(request.title)
            param_idx += 1
        
        if request.summary is not None:
            updates.append(f"summary = ${param_idx}")
            params.append(request.summary)
            param_idx += 1
        
        if request.content is not None:
            updates.append(f"content = ${param_idx}")
            params.append(request.content)
            param_idx += 1
        
        if request.seo_title is not None:
            updates.append(f"seo_title = ${param_idx}")
            params.append(request.seo_title)
            param_idx += 1
        
        if request.seo_description is not None:
            updates.append(f"seo_description = ${param_idx}")
            params.append(request.seo_description)
            param_idx += 1
        
        if request.seo_keywords is not None:
            updates.append(f"seo_keywords = ${param_idx}")
            params.append(request.seo_keywords)
            param_idx += 1
        
        if request.slug is not None:
            updates.append(f"slug = ${param_idx}")
            params.append(request.slug)
            param_idx += 1
        
        if request.status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(request.status)
            param_idx += 1
            if request.status == 'published':
                updates.append("published_at = CURRENT_TIMESTAMP")
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE community_articles SET {', '.join(updates)} WHERE id = $1"
            await db.execute(query, *params)
        
        return {"success": True, "message": "文章更新成功"}


@router.post("/articles/{article_id}/publish")
async def publish_article(article_id: str):
    """发布文章"""
    async with get_db() as db:
        article = await db.fetchone(
            "SELECT id, title, content FROM community_articles WHERE id = $1", article_id
        )
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        if not article['title'] or not article['content']:
            raise HTTPException(status_code=400, detail="文章标题和内容不能为空")
        
        await db.execute("""
            UPDATE community_articles 
            SET status = 'published', published_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """, article_id)
        
        return {"success": True, "message": "文章已发布"}


@router.post("/articles/{article_id}/unpublish")
async def unpublish_article(article_id: str):
    """取消发布文章"""
    async with get_db() as db:
        await db.execute("""
            UPDATE community_articles 
            SET status = 'draft', updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """, article_id)
        
        return {"success": True, "message": "文章已取消发布"}


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str):
    """删除文章"""
    async with get_db() as db:
        await db.execute("DELETE FROM community_articles WHERE id = $1", article_id)
        return {"success": True, "message": "文章已删除"}


@router.post("/articles/generate/{community_id}")
async def generate_article(community_id: str):
    """生成小区文章"""
    async with get_db() as db:
        community = await db.fetchone("""
            SELECT c.*, ci.name as city_name, d.name as district_name
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            WHERE c.id = $1
        """, community_id)
        
        if not community:
            raise HTTPException(status_code=404, detail="小区不存在")
        
        existing = await db.fetchone(
            "SELECT id, status FROM community_articles WHERE community_id = $1",
            community_id
        )
        
        pois = await db.fetch("""
            SELECT poi_type, name, distance, rating
            FROM community_pois
            WHERE community_id = $1
            ORDER BY distance ASC
        """, community_id)
        
        prices = await db.fetch("""
            SELECT date, COALESCE(price, avg_price) as price
            FROM community_prices
            WHERE community_id = $1
            ORDER BY date DESC
            LIMIT 12
        """, community_id)
        
        city_name = community['city_name'] or '未知城市'
        district_name = community['district_name'] or ''
        community_name = community['name']
        avg_price = community['avg_price']
        address = community['address'] or ''
        completion_year = community['completion_year']
        developer = community['developer'] or ''
        property_company = community['property_company'] or ''
        property_fee = community['property_fee']
        total_units = community['total_units']
        green_rate = community['green_rate']
        volume_rate = community['volume_rate']
        building_type = community['building_type'] or ''
        description = community['description'] or ''
        
        poi_text = ""
        poi_by_type = {}
        for poi in pois:
            poi_type = poi['poi_type']
            if poi_type not in poi_by_type:
                poi_by_type[poi_type] = []
            poi_by_type[poi_type].append(f"{poi['name']}（距离{int(poi['distance'] or 0)}米）")
        
        poi_type_names = {
            'school': '教育资源',
            'hospital': '医疗资源',
            'subway': '交通出行',
            'mall': '商业配套',
            'park': '休闲娱乐'
        }
        
        for poi_type, items in poi_by_type.items():
            type_name = poi_type_names.get(poi_type, poi_type)
            poi_text += f"\n### {type_name}\n"
            for item in items[:3]:
                poi_text += f"- {item}\n"
        
        price_trend_text = ""
        if prices:
            price_trend_text = "\n近几个月价格走势：\n"
            for p in reversed(prices[:6]):
                price_trend_text += f"- {p['date']}: {int(p['price'])}元/㎡\n"
        
        title = f"{city_name}{district_name}{community_name}深度解析 | 房价、户型、周边配套"
        
        summary = f"{community_name}位于{city_name}{district_name}"
        if avg_price:
            summary += f"，均价约{int(avg_price)}元/㎡"
        if completion_year:
            summary += f"，建成于{completion_year}年"
        if developer:
            summary += f"，由{developer}开发"
        summary += "。"
        
        content = f"""# {title}

## 项目概述

{community_name}位于{city_name}{district_name}，{address}。{description or '这是一个优质的住宅小区。'}

## 基本信息

"""
        
        if developer:
            content += f"- **开发商**：{developer}\n"
        if property_company:
            content += f"- **物业公司**：{property_company}\n"
        if property_fee:
            content += f"- **物业费**：{property_fee}元/㎡/月\n"
        if completion_year:
            content += f"- **建成年代**：{completion_year}年\n"
        if total_units:
            content += f"- **总户数**：约{total_units}户\n"
        if green_rate:
            content += f"- **绿化率**：{green_rate*100:.1f}%\n"
        if volume_rate:
            content += f"- **容积率**：{volume_rate}\n"
        if building_type:
            content += f"- **建筑类型**：{building_type}\n"
        
        content += f"""
## 价格走势

{community_name}均价目前约{int(avg_price) if avg_price else '暂无'}元/㎡。{price_trend_text}

## 周边配套
{poi_text if poi_text else '暂无周边配套信息。'}

## 购房建议

{community_name}适合注重生活品质的购房者。项目位于{district_name or city_name}核心区域，周边配套完善，交通便利。建议购房者实地考察，了解具体户型和价格信息后做出决策。

---
*本文由房都督平台自动生成，仅供参考。数据更新时间：{datetime.now().strftime('%Y-%m-%d')}*
"""
        
        seo_title = title[:60] if len(title) > 60 else title
        seo_description = summary[:160] if len(summary) > 160 else summary
        seo_keywords = f"{community_name},{city_name}{district_name},房价,小区"
        if completion_year:
            seo_keywords += f",{completion_year}年建成"
        if 'school' in poi_by_type:
            seo_keywords += ",学区房"
        
        slug = f"{city_name.lower()}-{district_name.lower() if district_name else ''}-{community_name.lower()}".replace(' ', '-')
        
        article_id = str(uuid.uuid4())
        
        if existing:
            await db.execute("""
                UPDATE community_articles 
                SET title = $2, summary = $3, content = $4, seo_title = $5, 
                    seo_description = $6, seo_keywords = $7, slug = $8, 
                    status = 'draft', updated_at = CURRENT_TIMESTAMP, generated_by = 'auto'
                WHERE community_id = $1
            """, community_id, title, summary, content, seo_title, seo_description,
               seo_keywords, slug)
            article_id = existing['id']
        else:
            await db.execute("""
                INSERT INTO community_articles 
                (id, community_id, title, summary, content, seo_title, seo_description, seo_keywords, slug, status, generated_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft', 'auto')
            """, article_id, community_id, title, summary, content, seo_title, seo_description,
               seo_keywords, slug)
        
        return {
            "success": True,
            "data": {
                "id": article_id,
                "community_id": community_id,
                "title": title,
                "summary": summary,
                "status": "draft"
            },
            "message": "文章生成成功，请审核后发布"
        }


@router.get("/communities-without-article")
async def get_communities_without_article(
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取没有文章的小区列表"""
    async with get_db() as db:
        query = """
            SELECT c.id, c.name, c.alias, 
                   ci.name as city_name, d.name as district_name,
                   c.address, c.avg_price, c.completion_year, c.created_at
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN districts d ON c.district_id = d.id
            LEFT JOIN community_articles a ON c.id = a.community_id
            WHERE a.id IS NULL
        """
        params = []
        param_idx = 1
        
        if city:
            query += f" AND ci.name = ${param_idx}"
            params.append(city)
            param_idx += 1
        
        query += " ORDER BY c.created_at DESC"
        
        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"
        
        rows = await db.fetch(query, *params)
        
        count_query = """
            SELECT COUNT(*) as total
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN community_articles a ON c.id = a.community_id
            WHERE a.id IS NULL
        """
        count_params = []
        if city:
            count_query += " AND ci.name = $1"
            count_params.append(city)
        
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
                "completion_year": row['completion_year'],
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


@router.post("/articles/batch-generate")
async def batch_generate_articles(
    city: Optional[str] = Query(None, description="城市筛选"),
    limit: int = Query(10, ge=1, le=50, description="生成数量限制")
):
    """批量生成文章"""
    async with get_db() as db:
        query = """
            SELECT c.id
            FROM communities c
            LEFT JOIN cities ci ON c.city_id = ci.id
            LEFT JOIN community_articles a ON c.id = a.community_id
            WHERE a.id IS NULL
        """
        params = []
        if city:
            query += " AND ci.name = $1"
            params.append(city)
        
        query += f" LIMIT {limit}"
        
        rows = await db.fetch(query, *params)
        
        generated = []
        failed = []
        
        for row in rows:
            try:
                community_id = row['id']
                result = await generate_article(community_id)
                if result['success']:
                    generated.append(community_id)
            except Exception as e:
                failed.append({"community_id": row['id'], "error": str(e)})
        
        return {
            "success": True,
            "data": {
                "generated": generated,
                "generated_count": len(generated),
                "failed": failed,
                "failed_count": len(failed)
            },
            "message": f"成功生成 {len(generated)} 篇文章"
        }
