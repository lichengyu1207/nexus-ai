"""
用户来源追踪服务
识别用户来源并提供差异化体验
"""
from typing import Optional, Dict, Any
from datetime import datetime
from backend.database import get_db
import logging

logger = logging.getLogger(__name__)

# 用户来源类型
class UserSource:
    FOUNDER_IP = "founder_ip"        # 创始人IP引流（知乎、公众号等）
    CASUAL = "casual"                # 偶然点击
    SEO = "seo"                      # SEO搜索
    URGENT = "urgent"                # 刚需用户
    DIRECT = "direct"                # 直接访问
    REFERRAL = "referral"            # 朋友推荐

# 来源配置
SOURCE_CONFIG = {
    UserSource.FOUNDER_IP: {
        "name": "创始人IP引流",
        "welcome_message": "老骇的朋友，你好！",
        "free_integral": 5,          # 粉丝专属5次免费分析
        "bonus_label": "粉丝专属福利",
        "mascot_emotion": "happy",
        "mascot_message": "感谢关注！这是为你准备的专属礼物～",
    },
    UserSource.CASUAL: {
        "name": "新朋友",
        "welcome_message": "欢迎来到房都督AI！",
        "free_integral": 3,
        "bonus_label": None,
        "mascot_emotion": "curious",
        "mascot_message": "咦？新朋友！点我开始分析吧～",
    },
    UserSource.SEO: {
        "name": "搜索用户",
        "welcome_message": "我找到你关心的区域了！",
        "free_integral": 3,
        "bonus_label": None,
        "mascot_emotion": "thinking",
        "mascot_message": "我已经帮你分析了这个区域，注册即可查看完整报告。",
    },
    UserSource.URGENT: {
        "name": "刚需用户",
        "welcome_message": "时间宝贵，我们直接开始！",
        "free_integral": 3,
        "bonus_label": None,
        "mascot_emotion": "professional",
        "mascot_message": "专业分析，助您决策。",
    },
    UserSource.REFERRAL: {
        "name": "推荐用户",
        "welcome_message": "朋友推荐来的？欢迎！",
        "free_integral": 4,          # 推荐用户多1次
        "bonus_label": "推荐福利",
        "mascot_emotion": "happy",
        "mascot_message": "你的朋友也在这里哦～",
    },
    UserSource.DIRECT: {
        "name": "直接访问",
        "welcome_message": "欢迎来到房都督AI！",
        "free_integral": 3,
        "bonus_label": None,
        "mascot_emotion": "default",
        "mascot_message": "开始你的房产分析之旅吧！",
    },
}

# URL参数到来源的映射
URL_SOURCE_MAPPING = {
    "zhihu": UserSource.FOUNDER_IP,
    "weixin": UserSource.FOUNDER_IP,
    "weibo": UserSource.FOUNDER_IP,
    "bilibili": UserSource.FOUNDER_IP,
    "laohai": UserSource.FOUNDER_IP,
    "ad": UserSource.CASUAL,
    "ads": UserSource.CASUAL,
    "seo": UserSource.SEO,
    "search": UserSource.SEO,
    "urgent": UserSource.URGENT,
    "buy": UserSource.URGENT,
    "ref": UserSource.REFERRAL,
    "invite": UserSource.REFERRAL,
}


def detect_source_from_url(url_params: Dict[str, str]) -> str:
    """
    从URL参数检测用户来源
    
    Args:
        url_params: URL查询参数字典
        
    Returns:
        用户来源类型
    """
    # 检查 source 参数
    source = url_params.get("source", "").lower()
    if source in URL_SOURCE_MAPPING:
        return URL_SOURCE_MAPPING[source]
    
    # 检查 ref 参数
    ref = url_params.get("ref", "").lower()
    if ref in URL_SOURCE_MAPPING:
        return URL_SOURCE_MAPPING[ref]
    
    # 检查 utm_source 参数
    utm_source = url_params.get("utm_source", "").lower()
    if utm_source in URL_SOURCE_MAPPING:
        return URL_SOURCE_MAPPING[utm_source]
    
    # 检查特定路径
    if "from-laohai" in url_params.get("path", ""):
        return UserSource.FOUNDER_IP
    
    return UserSource.DIRECT


def get_source_config(source: str) -> Dict[str, Any]:
    """
    获取来源配置
    
    Args:
        source: 用户来源类型
        
    Returns:
        来源配置字典
    """
    source_aliases = {
        "laohai": UserSource.FOUNDER_IP,
        "zhihu": UserSource.FOUNDER_IP,
        "weixin": UserSource.FOUNDER_IP,
        "weibo": UserSource.FOUNDER_IP,
        "bilibili": UserSource.FOUNDER_IP,
        "social": UserSource.CASUAL,
        "ads": UserSource.CASUAL,
        "ad": UserSource.CASUAL,
        "seo": UserSource.SEO,
        "search": UserSource.SEO,
        "urgent": UserSource.URGENT,
        "buy": UserSource.URGENT,
        "ref": UserSource.REFERRAL,
        "invite": UserSource.REFERRAL,
        "referral": UserSource.REFERRAL,
        "friend": UserSource.REFERRAL,
        "casual": UserSource.CASUAL,
        "direct": UserSource.DIRECT,
    }
    normalized_source = source_aliases.get(source, source)
    return SOURCE_CONFIG.get(normalized_source, SOURCE_CONFIG[UserSource.DIRECT])


async def record_user_source(
    user_id: str,
    source: str,
    url_params: Optional[Dict[str, str]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """
    记录用户来源
    
    Args:
        user_id: 用户ID
        source: 用户来源
        url_params: URL参数
        ip_address: IP地址
        user_agent: 用户代理
        
    Returns:
        是否成功
    """
    try:
        async with get_db() as conn:
            # 创建 user_sources 表（如果不存在）
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sources (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url_params TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_sources_user_id ON user_sources(user_id)")
            
            # 插入记录
            import uuid
            import json
            
            await conn.execute(
                """
                INSERT INTO user_sources (id, user_id, source, url_params, ip_address, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    user_id,
                    source,
                    json.dumps(url_params) if url_params else None,
                    ip_address,
                    user_agent,
                    datetime.utcnow().isoformat()
                )
            )
            
            await conn.commit()
            logger.info(f"Recorded user source: user={user_id}, source={source}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to record user source: {e}")
        return False


async def get_user_source(user_id: str) -> Optional[str]:
    """
    获取用户来源
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户来源类型
    """
    try:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT source FROM user_sources WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row["source"] if row else UserSource.DIRECT
    except Exception as e:
        logger.error(f"Failed to get user source: {e}")
        return UserSource.DIRECT


async def get_initial_integral(source: str) -> int:
    """
    根据来源获取初始积分
    
    Args:
        source: 用户来源
        
    Returns:
        初始积分数量
    """
    # 处理来源别名映射
    source_aliases = {
        "laohai": UserSource.FOUNDER_IP,
        "zhihu": UserSource.FOUNDER_IP,
        "weixin": UserSource.FOUNDER_IP,
        "weibo": UserSource.FOUNDER_IP,
        "bilibili": UserSource.FOUNDER_IP,
        "social": UserSource.CASUAL,
        "ads": UserSource.CASUAL,
        "ad": UserSource.CASUAL,
        "seo": UserSource.SEO,
        "search": UserSource.SEO,
        "urgent": UserSource.URGENT,
        "buy": UserSource.URGENT,
        "ref": UserSource.REFERRAL,
        "invite": UserSource.REFERRAL,
        "referral": UserSource.REFERRAL,
        "friend": UserSource.REFERRAL,
    }
    
    # 转换别名到标准来源
    normalized_source = source_aliases.get(source, source)
    config = get_source_config(normalized_source)
    return config.get("free_integral", 3)
