"""
地图数据聚合服务
根据缩放级别聚合用户位置数据
支持缓存以优化性能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import json

from ..database import get_db_connection

logger = logging.getLogger(__name__)

MIN_USERS_THRESHOLD = 3

CACHE_TTL = 3600

_map_cache: Dict[str, Dict[str, Any]] = {}


def _get_cache_key(prefix: str, **kwargs) -> str:
    """生成缓存键"""
    key_data = json.dumps(kwargs, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    return f"{prefix}:{key_hash}"


def _get_from_cache(key: str) -> Optional[Any]:
    """从缓存获取数据"""
    cached = _map_cache.get(key)
    if cached:
        if datetime.now() < cached["expires"]:
            logger.debug(f"Cache hit: {key}")
            return cached["data"]
        else:
            del _map_cache[key]
    return None


def _set_cache(key: str, data: Any, ttl: int = CACHE_TTL) -> None:
    """设置缓存"""
    _map_cache[key] = {
        "data": data,
        "expires": datetime.now() + timedelta(seconds=ttl)
    }
    logger.debug(f"Cache set: {key}")


def clear_map_cache() -> None:
    """清除所有地图缓存"""
    global _map_cache
    _map_cache = {}
    logger.info("Map cache cleared")


def clear_cache_by_prefix(prefix: str) -> None:
    """清除指定前缀的缓存"""
    global _map_cache
    keys_to_delete = [k for k in _map_cache.keys() if k.startswith(prefix)]
    for key in keys_to_delete:
        del _map_cache[key]
    logger.info(f"Cleared {len(keys_to_delete)} cache entries with prefix: {prefix}")


PROVINCE_COORDINATES = {
    "北京市": (116.4074, 39.9042),
    "天津市": (117.1901, 39.1255),
    "河北省": (114.5025, 38.0455),
    "山西省": (112.5489, 37.8706),
    "内蒙古自治区": (111.6708, 40.8183),
    "辽宁省": (123.4291, 41.7968),
    "吉林省": (125.3245, 43.8868),
    "黑龙江省": (126.6424, 45.7569),
    "上海市": (121.4737, 31.2304),
    "江苏省": (118.7674, 32.0415),
    "浙江省": (120.1536, 30.2875),
    "安徽省": (117.2830, 31.8612),
    "福建省": (119.3062, 26.0753),
    "江西省": (115.8581, 28.6829),
    "山东省": (117.0009, 36.6758),
    "河南省": (113.6654, 34.7570),
    "湖北省": (114.2986, 30.5844),
    "湖南省": (112.9823, 28.1947),
    "广东省": (113.2644, 23.1291),
    "广西壮族自治区": (108.3200, 22.8240),
    "海南省": (110.3312, 20.0310),
    "重庆市": (106.5516, 29.5630),
    "四川省": (104.0657, 30.6595),
    "贵州省": (106.7135, 26.5783),
    "云南省": (102.7123, 25.0406),
    "西藏自治区": (91.1322, 29.6600),
    "陕西省": (108.9402, 34.3416),
    "甘肃省": (103.8236, 36.0580),
    "青海省": (101.7782, 36.6171),
    "宁夏回族自治区": (106.2782, 38.4664),
    "新疆维吾尔自治区": (87.6177, 43.7928),
    "台湾省": (121.5091, 25.0443),
    "香港特别行政区": (114.1694, 22.3193),
    "澳门特别行政区": (113.5439, 22.2006),
}


async def aggregate_by_province(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bounds: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """按省份聚合"""
    conn = await get_db_connection()
    try:
        conditions = ["province IS NOT NULL"]
        params = []
        
        if start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        cursor = await conn.execute(
            f"""
            SELECT province, COUNT(*) as count
            FROM user_locations
            {where_clause}
            GROUP BY province
            ORDER BY count DESC
            """,
            params
        )
        rows = await cursor.fetchall()
        
        features = []
        for row in rows:
            province = row["province"]
            coords = PROVINCE_COORDINATES.get(province, (0, 0))
            
            if coords[0] == 0 and coords[1] == 0:
                continue
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [coords[0], coords[1]]
                },
                "properties": {
                    "name": province,
                    "count": row["count"],
                    "level": "province"
                }
            })
        
        return features
    finally:
        await conn.close()


async def aggregate_by_city(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bounds: Optional[Dict[str, float]] = None,
    province: Optional[str] = None
) -> List[Dict[str, Any]]:
    """按城市聚合"""
    conn = await get_db_connection()
    try:
        conditions = ["city IS NOT NULL"]
        params = []
        
        if start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)
        if province:
            conditions.append("province = ?")
            params.append(province)
        if bounds:
            conditions.append("longitude >= ? AND longitude <= ?")
            conditions.append("latitude >= ? AND latitude <= ?")
            params.extend([bounds["west"], bounds["east"], bounds["south"], bounds["north"]])
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        cursor = await conn.execute(
            f"""
            SELECT city, province, 
                   AVG(longitude) as lng, 
                   AVG(latitude) as lat,
                   COUNT(*) as count
            FROM user_locations
            {where_clause}
            GROUP BY city
            ORDER BY count DESC
            """,
            params
        )
        rows = await cursor.fetchall()
        
        features = []
        for row in rows:
            if row["lng"] and row["lat"]:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row["lng"], row["lat"]]
                    },
                    "properties": {
                        "name": row["city"],
                        "province": row["province"],
                        "count": row["count"],
                        "level": "city"
                    }
                })
        
        return features
    finally:
        await conn.close()


async def aggregate_by_district(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bounds: Optional[Dict[str, float]] = None,
    city: Optional[str] = None
) -> List[Dict[str, Any]]:
    """按区县聚合"""
    conn = await get_db_connection()
    try:
        conditions = ["district IS NOT NULL"]
        params = []
        
        if start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)
        if city:
            conditions.append("city = ?")
            params.append(city)
        if bounds:
            conditions.append("longitude >= ? AND longitude <= ?")
            conditions.append("latitude >= ? AND latitude <= ?")
            params.extend([bounds["west"], bounds["east"], bounds["south"], bounds["north"]])
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        cursor = await conn.execute(
            f"""
            SELECT district, city, province,
                   AVG(longitude) as lng, 
                   AVG(latitude) as lat,
                   COUNT(*) as count
            FROM user_locations
            {where_clause}
            GROUP BY district
            ORDER BY count DESC
            """,
            params
        )
        rows = await cursor.fetchall()
        
        features = []
        for row in rows:
            if row["lng"] and row["lat"]:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [row["lng"], row["lat"]]
                    },
                    "properties": {
                        "name": row["district"],
                        "city": row["city"],
                        "province": row["province"],
                        "count": row["count"],
                        "level": "district"
                    }
                })
        
        return features
    finally:
        await conn.close()


async def get_point_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    bounds: Optional[Dict[str, float]] = None,
    limit: int = 500,
    min_users: int = MIN_USERS_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    获取点数据（小区级别）
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        bounds: 地图边界
        limit: 返回数量限制
        min_users: 最小用户数阈值（隐私保护）
        
    Returns:
        点数据列表
    """
    conn = await get_db_connection()
    try:
        conditions = ["longitude IS NOT NULL", "latitude IS NOT NULL"]
        params = []
        
        if start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)
        if bounds:
            conditions.append("longitude >= ? AND longitude <= ?")
            conditions.append("latitude >= ? AND latitude <= ?")
            params.extend([bounds["west"], bounds["east"], bounds["south"], bounds["north"]])
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        cursor = await conn.execute(
            f"""
            SELECT longitude, latitude, community, district, city, province,
                   created_at
            FROM user_locations
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params + [limit]
        )
        rows = await cursor.fetchall()
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        community_counts: Dict[str, Dict[str, Any]] = {}
        
        for row in rows:
            community_key = row["community"] or f"{row['district']}_{row['longitude']}_{row['latitude']}"
            
            if community_key not in community_counts:
                community_counts[community_key] = {
                    "longitude": row["longitude"],
                    "latitude": row["latitude"],
                    "community": row["community"],
                    "district": row["district"],
                    "city": row["city"],
                    "province": row["province"],
                    "count": 0,
                    "is_new": False,
                    "created_at": row["created_at"]
                }
            
            community_counts[community_key]["count"] += 1
            
            if row["created_at"] and row["created_at"] >= thirty_days_ago:
                community_counts[community_key]["is_new"] = True
        
        features = []
        for key, data in community_counts.items():
            if data["count"] < min_users:
                continue
            
            name = data["community"] or data["district"] or data["city"] or "未知位置"
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [data["longitude"], data["latitude"]]
                },
                "properties": {
                    "name": name,
                    "community": data["community"],
                    "district": data["district"],
                    "city": data["city"],
                    "province": data["province"],
                    "count": data["count"],
                    "level": "point",
                    "is_new": data["is_new"],
                    "created_at": data["created_at"]
                }
            })
        
        features.sort(key=lambda x: x["properties"]["count"], reverse=True)
        
        return features[:limit]
    finally:
        await conn.close()


async def get_new_locations(days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
    """
    获取新增位置列表
    
    Args:
        days: 天数阈值
        limit: 返回数量限制
        
    Returns:
        新增位置列表
    """
    conn = await get_db_connection()
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor = await conn.execute(
            """
            SELECT community, district, city, province, 
                   longitude, latitude, created_at,
                   COUNT(*) as count
            FROM user_locations
            WHERE created_at >= ?
            AND community IS NOT NULL
            GROUP BY community
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (cutoff, limit)
        )
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_map_data(
    zoom_level: int,
    bounds: Optional[Dict[str, float]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    根据缩放级别获取地图数据
    
    Args:
        zoom_level: 缩放级别 (1-14)
        bounds: 地图边界
        start_date: 开始日期
        end_date: 结束日期
        use_cache: 是否使用缓存
        
    Returns:
        GeoJSON FeatureCollection
    """
    cache_key = _get_cache_key(
        "map_data",
        zoom_level=zoom_level,
        bounds=bounds,
        start_date=start_date,
        end_date=end_date
    )
    
    if use_cache:
        cached = _get_from_cache(cache_key)
        if cached:
            return cached
    
    if zoom_level <= 4:
        features = await aggregate_by_province(start_date, end_date, bounds)
    elif zoom_level <= 7:
        features = await aggregate_by_city(start_date, end_date, bounds)
    elif zoom_level <= 10:
        features = await aggregate_by_district(start_date, end_date, bounds)
    else:
        features = await get_point_data(start_date, end_date, bounds)
    
    result = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "zoom_level": zoom_level,
            "aggregation_level": "province" if zoom_level <= 4 else 
                                  "city" if zoom_level <= 7 else 
                                  "district" if zoom_level <= 10 else "point",
            "total_features": len(features)
        }
    }
    
    _set_cache(cache_key, result)
    
    return result


async def get_heatmap_data(
    bounds: Optional[Dict[str, float]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    radius: int = 25
) -> List[Dict[str, Any]]:
    """
    获取热力图数据
    
    Args:
        bounds: 地图边界
        start_date: 开始日期
        end_date: 结束日期
        radius: 热力半径
        
    Returns:
        热力图数据点列表
    """
    conn = await get_db_connection()
    try:
        conditions = ["longitude IS NOT NULL", "latitude IS NOT NULL"]
        params = []
        
        if start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)
        if bounds:
            conditions.append("longitude >= ? AND longitude <= ?")
            conditions.append("latitude >= ? AND latitude <= ?")
            params.extend([bounds["west"], bounds["east"], bounds["south"], bounds["north"]])
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        cursor = await conn.execute(
            f"""
            SELECT longitude, latitude
            FROM user_locations
            {where_clause}
            """,
            params
        )
        rows = await cursor.fetchall()
        
        return [[row["longitude"], row["latitude"]] for row in rows]
    finally:
        await conn.close()


async def get_location_summary() -> Dict[str, Any]:
    """获取位置数据摘要"""
    conn = await get_db_connection()
    try:
        summary = {}
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_locations"
        )
        summary["total_locations"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_locations WHERE longitude IS NOT NULL"
        )
        summary["geocoded_locations"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT province, COUNT(*) as count
            FROM user_locations
            WHERE province IS NOT NULL
            GROUP BY province
            ORDER BY count DESC
            LIMIT 5
            """
        )
        summary["top_provinces"] = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(
            """
            SELECT city, COUNT(*) as count
            FROM user_locations
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY count DESC
            LIMIT 5
            """
        )
        summary["top_cities"] = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(
            """
            SELECT source, COUNT(*) as count
            FROM user_locations
            GROUP BY source
            """
        )
        summary["by_source"] = {row["source"]: row["count"] for row in await cursor.fetchall()}
        
        return summary
    finally:
        await conn.close()


async def get_map_stats() -> Dict[str, Any]:
    """
    获取地图统计数据
    
    Returns:
        地图统计数据
    """
    conn = await get_db_connection()
    try:
        stats = {}
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_locations"
        )
        stats["total_locations"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT source, COUNT(*) as count
            FROM user_locations
            GROUP BY source
            """
        )
        stats["by_source"] = {row["source"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            """
            SELECT city as name, COUNT(*) as count
            FROM user_locations
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY count DESC
            LIMIT 10
            """
        )
        stats["top_cities"] = [dict(row) for row in await cursor.fetchall()]
        
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        cursor = await conn.execute(
            """
            SELECT COUNT(DISTINCT community) as count
            FROM user_locations
            WHERE created_at >= ?
            AND community IS NOT NULL
            """,
            (cutoff,)
        )
        stats["new_communities_last_30d"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT province as name, COUNT(*) as count
            FROM user_locations
            WHERE province IS NOT NULL
            GROUP BY province
            ORDER BY count DESC
            LIMIT 10
            """
        )
        stats["top_provinces"] = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(
            """
            SELECT district as name, city, COUNT(*) as count
            FROM user_locations
            WHERE district IS NOT NULL
            GROUP BY district
            ORDER BY count DESC
            LIMIT 10
            """
        )
        stats["top_districts"] = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(
            """
            SELECT COUNT(*) as count FROM user_locations
            WHERE longitude IS NOT NULL AND latitude IS NOT NULL
            """
        )
        stats["geocoded_locations"] = (await cursor.fetchone())["count"]
        
        return stats
    finally:
        await conn.close()
