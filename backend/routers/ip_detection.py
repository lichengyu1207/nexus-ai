"""
IP地理位置检测API
"""
from fastapi import APIRouter, Request
from typing import Dict, Any
import logging

router = APIRouter(prefix="/api", tags=["ip"])
logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def detect_country_from_ip(ip: str) -> str:
    """根据IP检测国家/地区"""
    if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
        return "CN"
    
    ip_parts = ip.split(".")
    if len(ip_parts) != 4:
        return "CN"
    
    first_octet = int(ip_parts[0])
    
    if first_octet >= 1 and first_octet <= 126:
        return "US"
    elif first_octet >= 128 and first_octet <= 191:
        return "US"
    elif first_octet >= 192 and first_octet <= 223:
        if int(ip_parts[1]) >= 0 and int(ip_parts[1]) <= 127:
            return "US"
        else:
            return "CN"
    
    return "CN"


@router.get("/ip/detect")
async def detect_ip_location(request: Request) -> Dict[str, Any]:
    """检测IP位置并返回推荐语言"""
    ip = get_client_ip(request)
    country = detect_country_from_ip(ip)
    
    language_map = {
        "CN": "zh-CN",
        "TW": "zh-TW",
        "HK": "zh-HK",
        "US": "en-US",
        "GB": "en-GB",
        "AU": "en-US",
        "CA": "en-US",
        "NZ": "en-US",
    }
    
    recommended_language = language_map.get(country, "zh-CN")
    
    return {
        "ip": ip,
        "country": country,
        "recommended_language": recommended_language,
        "supported_languages": [
            {"code": "zh-CN", "name": "简体中文"},
            {"code": "en-US", "name": "English"},
        ]
    }
