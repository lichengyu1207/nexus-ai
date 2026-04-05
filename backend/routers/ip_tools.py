"""
IP内容生成工具API
"""
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from datetime import datetime
import uuid
import logging

from ..auth import get_current_user
from ..database import get_db_connection

router = APIRouter(prefix="/api/ip", tags=["ip-tools"])
logger = logging.getLogger(__name__)


@router.post("/generate-article")
async def generate_article(data: Dict[str, Any], user: dict = Depends(get_current_user)):
    """根据地址生成文章"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM ip_partners WHERE user_id = ? AND status = 'active'",
            (user["id"],)
        )
        ip = await cursor.fetchone()
        if not ip:
            return {"error": "您还不是活跃的IP合作伙伴"}
        
        location = data.get("location", "")
        title = f"{location}房产分析报告"
        content = f"""# {title}

## 区域概述
{location}位于城市核心区域，交通便利，配套设施完善。

## 市场分析
- 平均房价：约25,000元/平方米
- 年涨幅：约5-8%

## 投资建议
1. 适合刚需和改善型需求
2. 长期看好

---
*本报告由房都督AI生成*"""
        
        article_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO ip_articles (id, ip_id, title, content, location, status) VALUES (?, ?, ?, ?, ?, 'draft')",
            (article_id, ip["id"], title, content, location)
        )
        await conn.commit()
        return {"success": True, "article": {"id": article_id, "title": title, "content": content}}
    finally:
        await conn.close()


@router.get("/articles")
async def get_ip_articles(page: int = Query(1, ge=1), page_size: int = Query(20), user: dict = Depends(get_current_user)):
    """获取IP的文章列表"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT id FROM ip_partners WHERE user_id = ?", (user["id"],))
        ip = await cursor.fetchone()
        if not ip:
            return {"error": "您还不是IP合作伙伴"}
        
        cursor = await conn.execute("SELECT COUNT(*) as total FROM ip_articles WHERE ip_id = ?", (ip["id"],))
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(
            "SELECT * FROM ip_articles WHERE ip_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (ip["id"], page_size, offset)
        )
        articles = [{"id": r["id"], "title": r["title"], "location": r["location"], "status": r["status"], "created_at": r["created_at"]} async for r in cursor]
        return {"articles": articles, "total": total}
    finally:
        await conn.close()


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    """删除文章"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT a.id FROM ip_articles a JOIN ip_partners p ON a.ip_id = p.id WHERE a.id = ? AND p.user_id = ?",
            (article_id, user["id"])
        )
        if not await cursor.fetchone():
            return {"error": "文章不存在"}
        await conn.execute("DELETE FROM ip_articles WHERE id = ?", (article_id,))
        await conn.commit()
        return {"success": True}
    finally:
        await conn.close()
