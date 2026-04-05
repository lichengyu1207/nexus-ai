"""
图片上传服务 API路由
支持房源图片、配套图片、小区图片等多种类型的图片上传
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import os
import logging
import asyncio
from PIL import Image
import io

logger = logging.getLogger(__name__)

from ..auth import get_current_user

router = APIRouter(prefix="/api/images", tags=["图片上传"])

UPLOAD_BASE_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

IMAGE_CATEGORIES = {
    "house": "房源图片",
    "community": "小区图片",
    "poi": "配套图片",
    "floor_plan": "户型图",
    "environment": "环境图片",
    "document": "证件图片",
    "avatar": "用户头像",
    "general": "通用图片"
}

def ensure_upload_dir(category: str = "general") -> str:
    upload_dir = os.path.join(UPLOAD_BASE_DIR, category)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def validate_image(content: bytes, filename: str) -> tuple[bool, str]:
    if not filename:
        return False, "文件名不能为空"
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式，允许的格式: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if len(content) > MAX_FILE_SIZE:
        return False, f"文件大小超过限制，最大允许 {MAX_FILE_SIZE // (1024*1024)}MB"
    
    try:
        if ext != ".svg":
            img = Image.open(io.BytesIO(content))
            img.verify()
    except Exception as e:
        return False, f"无效的图片文件: {str(e)}"
    
    return True, ""

async def process_image(content: bytes, filename: str, category: str, resize: bool = True) -> Dict[str, Any]:
    ext = os.path.splitext(filename)[1].lower()
    upload_dir = ensure_upload_dir(category)
    
    file_id = uuid.uuid4().hex[:12]
    new_filename = f"{file_id}{ext}"
    filepath = os.path.join(upload_dir, new_filename)
    
    original_size = len(content)
    width, height = 0, 0
    
    if ext != ".svg" and resize:
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            max_dimension = 1920
            if max(width, height) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                width, height = new_width, new_height
            
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            content = output.getvalue()
            
            new_filename = f"{file_id}.jpg"
            filepath = os.path.join(upload_dir, new_filename)
            
        except Exception as e:
            logger.warning(f"图片处理失败，使用原始文件: {e}")
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    url = f"/uploads/{category}/{new_filename}"
    
    return {
        "file_id": file_id,
        "filename": new_filename,
        "original_filename": filename,
        "url": url,
        "size": len(content),
        "original_size": original_size,
        "width": width,
        "height": height,
        "category": category,
        "created_at": datetime.utcnow().isoformat()
    }

class ImageUploadResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class MultiImageUploadResponse(BaseModel):
    success: bool
    message: str
    total: int
    uploaded: int
    failed: int
    images: List[Dict[str, Any]]



@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    category: str = Form("general", description="图片分类"),
    resize: bool = Form(True, description="是否自动压缩"),
    current_user: dict = Depends(get_current_user)
):
    """
    上传单张图片
    
    支持的图片分类:
    - house: 房源图片
    - community: 小区图片
    - poi: 配套图片
    - floor_plan: 户型图
    - environment: 环境图片
    - document: 证件图片
    - avatar: 用户头像
    - general: 通用图片
    """
    if category not in IMAGE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"不支持的图片分类: {category}")
    
    content = await file.read()
    
    is_valid, error_msg = validate_image(content, file.filename or "image.jpg")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        result = await process_image(content, file.filename or "image.jpg", category, resize)
        
        return ImageUploadResponse(
            success=True,
            message="图片上传成功",
            data=result
        )
    except Exception as e:
        logger.error(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")

@router.post("/upload/batch", response_model=MultiImageUploadResponse)
async def upload_images_batch(
    files: List[UploadFile] = File(..., description="图片文件列表"),
    category: str = Form("general", description="图片分类"),
    resize: bool = Form(True, description="是否自动压缩"),
    current_user: dict = Depends(get_current_user)
):
    """
    批量上传图片
    
    一次最多上传10张图片
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="一次最多上传10张图片")
    
    if category not in IMAGE_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"不支持的图片分类: {category}")
    
    uploaded_images = []
    failed_count = 0
    
    for file in files:
        try:
            content = await file.read()
            is_valid, error_msg = validate_image(content, file.filename or "image.jpg")
            
            if not is_valid:
                failed_count += 1
                logger.warning(f"文件 {file.filename} 验证失败: {error_msg}")
                continue
            
            result = await process_image(content, file.filename or "image.jpg", category, resize)
            uploaded_images.append(result)
            
        except Exception as e:
            failed_count += 1
            logger.error(f"文件 {file.filename} 上传失败: {e}")
    
    return MultiImageUploadResponse(
        success=True,
        message=f"成功上传 {len(uploaded_images)} 张图片",
        total=len(files),
        uploaded=len(uploaded_images),
        failed=failed_count,
        images=uploaded_images
    )

@router.post("/house/{house_id}/upload")
async def upload_house_image(
    house_id: str,
    file: UploadFile = File(..., description="房源图片"),
    image_type: str = Form("exterior", description="图片类型: exterior-外观, interior-室内, floor_plan-户型"),
    description: Optional[str] = Form(None, description="图片描述"),
    current_user: dict = Depends(get_current_user)
):
    """
    上传房源图片
    
    将图片与房源关联存储
    """
    import asyncpg
    
    content = await file.read()
    is_valid, error_msg = validate_image(content, file.filename or "image.jpg")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        result = await process_image(content, file.filename or "image.jpg", "house", True)
        
        conn = await asyncpg.connect(
            "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"
        )
        
        try:
            image_id = str(uuid.uuid4())
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS house_images (
                    id VARCHAR(50) PRIMARY KEY,
                    house_id VARCHAR(50) NOT NULL,
                    image_url TEXT NOT NULL,
                    image_type VARCHAR(50),
                    description TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    uploaded_by VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                INSERT INTO house_images (id, house_id, image_url, image_type, description, file_size, width, height, uploaded_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, image_id, house_id, result["url"], image_type, description,
                result["size"], result["width"], result["height"], current_user["id"])
            
        finally:
            await conn.close()
        
        return {
            "success": True,
            "message": "房源图片上传成功",
            "image_id": image_id,
            "house_id": house_id,
            "image_url": result["url"],
            "image_type": image_type
        }
        
    except Exception as e:
        logger.error(f"房源图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")

@router.get("/house/{house_id}/images")
async def get_house_images(house_id: str):
    """获取房源的所有图片"""
    import asyncpg
    
    try:
        conn = await asyncpg.connect(
            "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"
        )
        
        try:
            images = await conn.fetch("""
                SELECT id, image_url, image_type, description, file_size, width, height, created_at
                FROM house_images
                WHERE house_id = $1
                ORDER BY created_at DESC
            """, house_id)
            
            return {
                "success": True,
                "house_id": house_id,
                "total": len(images),
                "images": [dict(img) for img in images]
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"获取房源图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除图片"""
    import asyncpg
    
    try:
        conn = await asyncpg.connect(
            "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"
        )
        
        try:
            image = await conn.fetchrow("""
                SELECT id, image_url, uploaded_by FROM house_images WHERE id = $1
            """, image_id)
            
            if not image:
                raise HTTPException(status_code=404, detail="图片不存在")
            
            await conn.execute("DELETE FROM house_images WHERE id = $1", image_id)
            
            filepath = image["image_url"].lstrip("/")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return {"success": True, "message": "图片已删除"}
            
        finally:
            await conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除图片失败: {str(e)}")

@router.get("/categories")
async def get_image_categories():
    """获取支持的图片分类"""
    return {
        "success": True,
        "categories": [
            {"key": k, "name": v} for k, v in IMAGE_CATEGORIES.items()
        ]
    }
