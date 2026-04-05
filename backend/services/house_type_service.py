"""
户型面积估算服务
根据户型估算面积范围
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..database import get_db_connection

logger = logging.getLogger(__name__)


DEFAULT_AREA_STATS = {
    "1室0厅": {"min_area": 25, "max_area": 45, "avg_area": 35, "common_areas": [30, 35, 40]},
    "1室1厅": {"min_area": 30, "max_area": 55, "avg_area": 42, "common_areas": [35, 40, 45, 50]},
    "2室0厅": {"min_area": 40, "max_area": 65, "avg_area": 52, "common_areas": [45, 50, 55, 60]},
    "2室1厅": {"min_area": 50, "max_area": 85, "avg_area": 68, "common_areas": [55, 60, 65, 70, 75, 80]},
    "2室2厅": {"min_area": 60, "max_area": 100, "avg_area": 80, "common_areas": [70, 75, 80, 85, 90]},
    "3室1厅": {"min_area": 70, "max_area": 115, "avg_area": 90, "common_areas": [80, 85, 90, 95, 100, 105, 110]},
    "3室2厅": {"min_area": 85, "max_area": 140, "avg_area": 110, "common_areas": [95, 100, 105, 110, 115, 120, 125, 130]},
    "3室3厅": {"min_area": 100, "max_area": 160, "avg_area": 130, "common_areas": [110, 120, 130, 140, 150]},
    "4室1厅": {"min_area": 100, "max_area": 150, "avg_area": 125, "common_areas": [110, 120, 130, 140]},
    "4室2厅": {"min_area": 120, "max_area": 180, "avg_area": 145, "common_areas": [130, 140, 150, 160, 170]},
    "4室3厅": {"min_area": 140, "max_area": 220, "avg_area": 175, "common_areas": [150, 160, 170, 180, 190, 200]},
    "5室2厅": {"min_area": 150, "max_area": 250, "avg_area": 190, "common_areas": [160, 175, 190, 200, 220]},
    "5室3厅": {"min_area": 180, "max_area": 300, "avg_area": 230, "common_areas": [200, 220, 240, 260, 280]},
}

CITY_AREA_MULTIPLIERS = {
    "北京": 0.95,
    "上海": 0.95,
    "深圳": 0.9,
    "广州": 1.0,
    "杭州": 1.0,
    "成都": 1.1,
    "武汉": 1.1,
    "南京": 1.0,
    "苏州": 1.05,
    "重庆": 1.15,
}


async def init_house_type_data():
    """初始化户型面积数据"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM house_type_area_stats"
        )
        result = await cursor.fetchone()
        
        if result["count"] > 0:
            logger.info("户型面积数据已存在，跳过初始化")
            return
        
        for house_type, stats in DEFAULT_AREA_STATS.items():
            import uuid
            await conn.execute(
                """
                INSERT INTO house_type_area_stats (
                    id, type, min_area, max_area, avg_area, common_areas, city, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    house_type,
                    stats["min_area"],
                    stats["max_area"],
                    stats["avg_area"],
                    json.dumps(stats["common_areas"]),
                    None,
                    "默认统计"
                )
            )
        
        await conn.commit()
        logger.info(f"初始化户型面积数据完成，共 {len(DEFAULT_AREA_STATS)} 条")
    finally:
        await conn.close()


async def get_area_estimate(
    room_count: int,
    hall_count: int = 1,
    city: str = None
) -> Dict[str, Any]:
    """
    获取面积估算
    
    Args:
        room_count: 室数
        hall_count: 厅数
        city: 城市（可选，用于调整估算）
        
    Returns:
        面积估算结果
    """
    if hall_count is None:
        hall_count = 1
    house_type = f"{room_count}室{hall_count}厅"
    
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM house_type_area_stats WHERE type = ? AND (city = ? OR city IS NULL)",
            (house_type, city)
        )
        row = await cursor.fetchone()
        
        if row:
            result = {
                "house_type": house_type,
                "min_area": row["min_area"] or 50,
                "max_area": row["max_area"] or 100,
                "avg_area": row["avg_area"] or 75,
                "common_areas": json.loads(row["common_areas"]) if row["common_areas"] else [],
                "source": row["source"] or "数据库",
                "confidence": 0.8
            }
        else:
            default_stats = DEFAULT_AREA_STATS.get(house_type)
            if default_stats:
                result = {
                    "house_type": house_type,
                    **default_stats,
                    "source": "默认统计",
                    "confidence": 0.7
                }
            else:
                estimated_avg = 30 + room_count * 30 + hall_count * 15
                result = {
                    "house_type": house_type,
                    "min_area": estimated_avg - 20,
                    "max_area": estimated_avg + 30,
                    "avg_area": estimated_avg,
                    "common_areas": [estimated_avg - 10, estimated_avg, estimated_avg + 10],
                    "source": "公式估算",
                    "confidence": 0.5
                }
        
        if city and city in CITY_AREA_MULTIPLIERS:
            multiplier = CITY_AREA_MULTIPLIERS[city]
            result["min_area"] = round((result.get("min_area") or 50) * multiplier, 1)
            result["max_area"] = round((result.get("max_area") or 100) * multiplier, 1)
            result["avg_area"] = round((result.get("avg_area") or 75) * multiplier, 1)
            result["city_adjusted"] = True
            result["city_multiplier"] = multiplier
        
        result["recommended_min"] = result.get("min_area") or 50
        result["recommended_max"] = result.get("max_area") or 100
        result["recommended_avg"] = result.get("avg_area") or 75
        
        return result
    finally:
        await conn.close()


async def get_all_house_types(city: str = None) -> List[Dict[str, Any]]:
    """
    获取所有户型面积统计
    
    Args:
        city: 城市（可选）
        
    Returns:
        户型列表
    """
    conn = await get_db_connection()
    try:
        if city:
            cursor = await conn.execute(
                "SELECT * FROM house_type_area_stats WHERE city = ? OR city IS NULL ORDER BY avg_area",
                (city,)
            )
        else:
            cursor = await conn.execute(
                "SELECT * FROM house_type_area_stats ORDER BY avg_area"
            )
        
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "type": row["type"],
                "min_area": row["min_area"],
                "max_area": row["max_area"],
                "avg_area": row["avg_area"],
                "common_areas": json.loads(row["common_areas"]) if row["common_areas"] else [],
                "city": row["city"],
                "source": row["source"]
            }
            for row in rows
        ]
    finally:
        await conn.close()


async def add_house_type_stat(
    house_type: str,
    min_area: float,
    max_area: float,
    avg_area: float,
    common_areas: List[float],
    city: str = None,
    source: str = None
) -> bool:
    """
    添加户型面积统计
    
    Args:
        house_type: 户型
        min_area: 最小面积
        max_area: 最大面积
        avg_area: 平均面积
        common_areas: 常见面积列表
        city: 城市
        source: 数据来源
        
    Returns:
        是否成功
    """
    import uuid
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            INSERT INTO house_type_area_stats (
                id, type, min_area, max_area, avg_area, common_areas, city, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                house_type,
                min_area,
                max_area,
                avg_area,
                json.dumps(common_areas),
                city,
                source
            )
        )
        await conn.commit()
        return True
    except Exception as e:
        logger.error(f"添加户型面积统计失败: {e}")
        return False
    finally:
        await conn.close()


def normalize_house_type(room_count: int, hall_count: int = None) -> str:
    """
    标准化户型名称
    
    Args:
        room_count: 室数
        hall_count: 厅数
        
    Returns:
        标准化户型名称
    """
    if hall_count is None:
        hall_count = 1
    
    return f"{room_count}室{hall_count}厅"


def parse_house_type(house_type: str) -> tuple:
    """
    解析户型字符串
    
    Args:
        house_type: 户型字符串
        
    Returns:
        (室数, 厅数)
    """
    import re
    
    match = re.match(r"(\d)室(\d)?厅?", house_type)
    if match:
        room = int(match.group(1))
        hall = int(match.group(2)) if match.group(2) else 1
        return room, hall
    
    return None, None
