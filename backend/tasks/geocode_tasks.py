"""
地理编码后台任务模块
用于异步执行地理编码操作
"""
import uuid
import logging
from typing import Optional, Dict, Any

from ..services.geocoder import geocode_address, get_geocoder
from ..database import LocationDB, ReportDB

logger = logging.getLogger(__name__)


async def geocode_and_save_location(
    user_id: str,
    address: str,
    source: str,
    report_id: Optional[str] = None
) -> Optional[str]:
    """
    地理编码并保存位置
    
    Args:
        user_id: 用户ID
        address: 地址字符串
        source: 来源 (registration, interest, report)
        report_id: 报告ID（可选，用于更新报告的location_id）
        
    Returns:
        位置ID，失败返回None
    """
    if not address or not address.strip():
        return None
    
    address = address.strip()
    
    try:
        result = await geocode_address(address)
        
        if not result:
            logger.warning(f"地理编码失败: {address}")
            return None
        
        location_id = str(uuid.uuid4())
        
        success = await LocationDB.create_location(
            location_id=location_id,
            user_id=user_id,
            source=source,
            address=address,
            country=result.get("country"),
            province=result.get("province"),
            city=result.get("city"),
            district=result.get("district"),
            street=result.get("street"),
            community=result.get("community"),
            longitude=result.get("longitude"),
            latitude=result.get("latitude")
        )
        
        if not success:
            logger.error(f"保存位置失败: {address}")
            return None
        
        logger.info(f"位置保存成功: {address} -> {result.get('formatted_address')}")
        
        if report_id:
            await update_report_location(report_id, location_id)
        
        return location_id
        
    except Exception as e:
        logger.error(f"地理编码任务失败: {e}")
        return None


async def update_report_location(report_id: str, location_id: str) -> bool:
    """
    更新报告的位置ID
    
    Args:
        report_id: 报告ID
        location_id: 位置ID
        
    Returns:
        是否成功
    """
    try:
        conn = await LocationDB._get_connection() if hasattr(LocationDB, '_get_connection') else None
        
        from ..database import get_db_connection
        conn = await get_db_connection()
        
        await conn.execute(
            "UPDATE reports SET location_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (location_id, report_id)
        )
        await conn.commit()
        await conn.close()
        
        logger.info(f"报告位置更新成功: report={report_id}, location={location_id}")
        return True
        
    except Exception as e:
        logger.error(f"更新报告位置失败: {e}")
        return False


async def batch_geocode_addresses(
    addresses: list,
    user_id: str,
    source: str
) -> Dict[str, Optional[str]]:
    """
    批量地理编码
    
    Args:
        addresses: 地址列表
        user_id: 用户ID
        source: 来源
        
    Returns:
        地址 -> 位置ID 的映射
    """
    geocoder = get_geocoder()
    results = await geocoder.batch_geocode(addresses, concurrency=5)
    
    location_ids = {}
    
    for address, result in results.items():
        if result:
            location_id = str(uuid.uuid4())
            
            success = await LocationDB.create_location(
                location_id=location_id,
                user_id=user_id,
                source=source,
                address=address,
                country=result.get("country"),
                province=result.get("province"),
                city=result.get("city"),
                district=result.get("district"),
                street=result.get("street"),
                community=result.get("community"),
                longitude=result.get("longitude"),
                latitude=result.get("latitude")
            )
            
            if success:
                location_ids[address] = location_id
            else:
                location_ids[address] = None
        else:
            location_ids[address] = None
    
    return location_ids


def create_geocode_task(
    user_id: str,
    address: str,
    source: str,
    report_id: Optional[str] = None
):
    """
    创建地理编码后台任务
    
    Args:
        user_id: 用户ID
        address: 地址
        source: 来源
        report_id: 报告ID
        
    Returns:
        后台任务函数
    """
    async def task():
        await geocode_and_save_location(user_id, address, source, report_id)
    
    return task


async def extract_address_from_requirement(requirement: Dict[str, Any]) -> Optional[str]:
    """
    从需求中提取地址
    
    Args:
        requirement: 需求数据
        
    Returns:
        地址字符串
    """
    if not requirement:
        return None
    
    address_parts = []
    
    if requirement.get("province"):
        address_parts.append(requirement["province"])
    if requirement.get("city"):
        address_parts.append(requirement["city"])
    if requirement.get("district"):
        address_parts.append(requirement["district"])
    if requirement.get("community"):
        address_parts.append(requirement["community"])
    if requirement.get("address"):
        address_parts.append(requirement["address"])
    
    if address_parts:
        return "".join(address_parts)
    
    if requirement.get("location"):
        return requirement["location"]
    
    if requirement.get("property_address"):
        return requirement["property_address"]
    
    return None


async def extract_address_from_collected_data(collected_data: Dict[str, Any]) -> Optional[str]:
    """
    从采集数据中提取地址
    
    Args:
        collected_data: 采集数据
        
    Returns:
        地址字符串
    """
    if not collected_data:
        return None
    
    if collected_data.get("address"):
        return collected_data["address"]
    
    if collected_data.get("property_info", {}).get("address"):
        return collected_data["property_info"]["address"]
    
    if collected_data.get("location"):
        return collected_data["location"]
    
    return None
