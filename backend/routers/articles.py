"""
内容营销系统 - 文章API
"""
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
import logging

from backend.auth import get_current_user_optional, require_admin

router = APIRouter(prefix="/api/articles", tags=["articles"])
logger = logging.getLogger(__name__)


def generate_slug(title: str) -> str:
    """生成URL友好的slug"""
    import re
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug[:100]


@router.get("")
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    status: str = Query("published"),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取文章列表"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        where_clauses = []
        params = []
        
        if status and not user:
            where_clauses.append("status = ?")
            params.append("published")
        elif status:
            where_clauses.append("status = ?")
            params.append(status)
        
        if category:
            where_clauses.append("category = ?")
            params.append(category)
        
        if tag:
            where_clauses.append("tags LIKE ?")
            params.append(f'%"{tag}"%')
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM articles {where_clause}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT id, title, slug, summary, cover_image, category, tags,
                   view_count, like_count, comment_count, is_featured,
                   published_at, created_at
            FROM articles 
            {where_clause}
            ORDER BY is_featured DESC, published_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        articles = []
        async for row in cursor:
            articles.append({
                "id": row["id"],
                "title": row["title"],
                "slug": row["slug"],
                "summary": row["summary"],
                "cover_image": row["cover_image"],
                "category": row["category"],
                "tags": json.loads(row["tags"]) if row["tags"] else [],
                "view_count": row["view_count"],
                "like_count": row["like_count"],
                "comment_count": row["comment_count"],
                "is_featured": bool(row["is_featured"]),
                "published_at": row["published_at"],
                "created_at": row["created_at"]
            })
        
        return {
            "articles": articles,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    request: Request,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取文章详情"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT * FROM articles WHERE id = ? OR slug = ?
        """, (article_id, article_id))
        
        article = await cursor.fetchone()
        if not article:
            return {"error": "Article not found"}
        
        await conn.execute("""
            UPDATE articles SET view_count = view_count + 1 WHERE id = ?
        """, (article["id"],))
        await conn.commit()
        
        return {
            "id": article["id"],
            "title": article["title"],
            "slug": article["slug"],
            "content": article["content"],
            "summary": article["summary"],
            "cover_image": article["cover_image"],
            "category": article["category"],
            "tags": json.loads(article["tags"]) if article["tags"] else [],
            "author_id": article["author_id"],
            "view_count": article["view_count"] + 1,
            "like_count": article["like_count"],
            "comment_count": article["comment_count"],
            "is_featured": bool(article["is_featured"]),
            "status": article["status"],
            "published_at": article["published_at"],
            "created_at": article["created_at"],
            "updated_at": article["updated_at"]
        }
    finally:
        await conn.close()


@router.post("")
async def create_article(
    data: Dict[str, Any],
    admin: dict = Depends(require_admin)
):
    """创建文章（管理员）"""
    from ..database import get_db_connection
    
    article_id = str(uuid.uuid4())
    title = data.get("title", "")
    base_slug = data.get("slug") or generate_slug(title)
    slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
    content = data.get("content", "")
    summary = data.get("summary", "")
    cover_image = data.get("cover_image", "")
    category = data.get("category", "news")
    tags = json.dumps(data.get("tags", []), ensure_ascii=False)
    status = data.get("status", "draft")
    is_featured = 1 if data.get("is_featured") else 0
    published_at = datetime.utcnow().isoformat() if status == "published" else None
    
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT INTO articles 
            (id, title, slug, content, summary, cover_image, category, tags, 
             author_id, status, is_featured, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (article_id, title, slug, content, summary, cover_image, category, tags,
              admin["id"], status, is_featured, published_at))
        await conn.commit()
        
        return {
            "id": article_id,
            "title": title,
            "slug": slug,
            "status": status
        }
    finally:
        await conn.close()


@router.put("/{article_id}")
async def update_article(
    article_id: str,
    data: Dict[str, Any],
    admin: dict = Depends(require_admin)
):
    """更新文章（管理员）"""
    from ..database import get_db_connection
    
    title = data.get("title")
    content = data.get("content")
    summary = data.get("summary")
    cover_image = data.get("cover_image")
    category = data.get("category")
    tags = json.dumps(data.get("tags"), ensure_ascii=False) if data.get("tags") else None
    status = data.get("status")
    is_featured = 1 if data.get("is_featured") else 0
    
    conn = await get_db_connection()
    try:
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
            slug = generate_slug(title)
            updates.append("slug = ?")
            params.append(slug)
        if content:
            updates.append("content = ?")
            params.append(content)
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)
        if cover_image is not None:
            updates.append("cover_image = ?")
            params.append(cover_image)
        if category:
            updates.append("category = ?")
            params.append(category)
        if tags:
            updates.append("tags = ?")
            params.append(tags)
        if status:
            updates.append("status = ?")
            params.append(status)
            if status == "published":
                updates.append("published_at = ?")
                params.append(datetime.utcnow().isoformat())
        
        updates.append("is_featured = ?")
        params.append(is_featured)
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.append(article_id)
        
        await conn.execute(f"""
            UPDATE articles SET {', '.join(updates)} WHERE id = ?
        """, params)
        await conn.commit()
        
        return {"success": True, "id": article_id}
    finally:
        await conn.close()


@router.delete("/{article_id}")
async def delete_article(
    article_id: str,
    admin: dict = Depends(require_admin)
):
    """删除文章（管理员）"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        await conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        await conn.execute("DELETE FROM article_comments WHERE article_id = ?", (article_id,))
        await conn.commit()
        
        return {"success": True}
    finally:
        await conn.close()


@router.post("/{article_id}/comments")
async def add_comment(
    article_id: str,
    data: Dict[str, Any],
    request: Request,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """添加评论"""
    from ..database import get_db_connection
    
    comment_id = str(uuid.uuid4())
    content = data.get("content", "")
    parent_id = data.get("parent_id")
    user_id = user["id"] if user else None
    ip_address = request.client.host if request.client else None
    
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT INTO article_comments 
            (id, article_id, user_id, parent_id, content, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (comment_id, article_id, user_id, parent_id, content, ip_address))
        
        await conn.execute("""
            UPDATE articles SET comment_count = comment_count + 1 WHERE id = ?
        """, (article_id,))
        
        await conn.commit()
        
        return {
            "id": comment_id,
            "content": content,
            "status": "pending"
        }
    finally:
        await conn.close()


@router.get("/{article_id}/comments")
async def get_comments(
    article_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """获取文章评论"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        offset = (page - 1) * page_size
        cursor = await conn.execute("""
            SELECT id, user_id, parent_id, content, created_at
            FROM article_comments 
            WHERE article_id = ? AND status = 'approved'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (article_id, page_size, offset))
        
        comments = []
        async for row in cursor:
            comments.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "parent_id": row["parent_id"],
                "content": row["content"],
                "created_at": row["created_at"]
            })
        
        return {"comments": comments}
    finally:
        await conn.close()


@router.get("/admin/list")
async def admin_list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """管理员获取文章列表"""
    from ..database import get_db_connection
    
    conn = await get_db_connection()
    try:
        where_clause = "WHERE status = ?" if status else ""
        params = [status] if status else []
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM articles {where_clause}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT id, title, slug, category, status, view_count, 
                   like_count, comment_count, is_featured, published_at, created_at
            FROM articles 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        articles = []
        async for row in cursor:
            articles.append({
                "id": row["id"],
                "title": row["title"],
                "slug": row["slug"],
                "category": row["category"],
                "status": row["status"],
                "view_count": row["view_count"],
                "like_count": row["like_count"],
                "comment_count": row["comment_count"],
                "is_featured": bool(row["is_featured"]),
                "published_at": row["published_at"],
                "created_at": row["created_at"]
            })
        
        return {
            "articles": articles,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()
