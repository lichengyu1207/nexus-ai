from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Property, PriceHistory
from app.core import redis_cache, acquire_lock, release_lock


class PropertyDAO:
    """小区数据访问对象"""
    
    def __init__(self, db: Session):
        """
        初始化PropertyDAO
        
        Args:
            db: SQLAlchemy会话对象
        """
        self.db = db
    
    @redis_cache(ttl=300, key_prefix="prop:dao:")
    async def get_property_by_name(self, city: str, name: str) -> Optional[Dict[str, Any]]:
        """
        根据小区名称查询小区信息
        
        Args:
            city: 城市名称
            name: 小区名称
            
        Returns:
            Optional[Dict[str, Any]]: 小区信息字典，如果不存在则返回None
        """
        # 生成锁名称
        lock_name = f"property:{city}:{name}"
        
        try:
            # 尝试获取锁
            lock_acquired = await acquire_lock(lock_name, timeout=5, expire=10)
            
            if lock_acquired:
                try:
                    # 查询小区信息
                    property_obj = self.db.query(Property).filter(
                        Property.city == city,
                        Property.name == name
                    ).first()
                    
                    if not property_obj:
                        # 缓存空值，避免缓存击穿
                        return None
                    
                    # 构建返回结果
                    result = {
                        "id": property_obj.id,
                        "city": property_obj.city,
                        "name": property_obj.name,
                        "address": property_obj.address,
                        "built_year": property_obj.built_year,
                        "property_type": property_obj.property_type,
                        "developer": property_obj.developer,
                        "property_management": property_obj.property_management,
                        "greening_rate": property_obj.greening_rate,
                        "plot_ratio": property_obj.plot_ratio,
                        "total_houses": property_obj.total_houses,
                        "parking_spaces": property_obj.parking_spaces,
                        "created_at": property_obj.created_at.isoformat() if property_obj.created_at else None,
                        "updated_at": property_obj.updated_at.isoformat() if property_obj.updated_at else None,
                        "price_histories": [
                            {
                                "id": ph.id,
                                "price": ph.price,
                                "price_date": ph.price_date.isoformat() if ph.price_date else None,
                                "source": ph.source,
                                "created_at": ph.created_at.isoformat() if ph.created_at else None
                            }
                            for ph in property_obj.price_histories
                        ]
                    }
                    
                    return result
                finally:
                    # 释放锁
                    await release_lock(lock_name)
            else:
                # 未获取到锁，直接返回None或等待
                # 这里简单返回None，实际应用中可以实现等待机制
                return None
        except Exception as e:
            # 发生异常时，确保锁被释放
            try:
                await release_lock(lock_name)
            except:
                pass
            raise e
    
    def create_property(self, property_data: Dict[str, Any]) -> Property:
        """
        创建小区信息
        
        Args:
            property_data: 小区信息字典
            
        Returns:
            Property: 创建的小区对象
        """
        # 创建小区对象
        property_obj = Property(**property_data)
        
        # 添加到数据库
        self.db.add(property_obj)
        self.db.commit()
        self.db.refresh(property_obj)
        
        return property_obj
    
    def update_property(self, property_id: int, property_data: Dict[str, Any]) -> Optional[Property]:
        """
        更新小区信息
        
        Args:
            property_id: 小区ID
            property_data: 小区信息字典
            
        Returns:
            Optional[Property]: 更新后的小区对象，如果不存在则返回None
        """
        # 查询小区
        property_obj = self.db.query(Property).filter(Property.id == property_id).first()
        
        if not property_obj:
            return None
        
        # 更新属性
        for key, value in property_data.items():
            if hasattr(property_obj, key):
                setattr(property_obj, key, value)
        
        # 提交更新
        self.db.commit()
        self.db.refresh(property_obj)
        
        return property_obj
    
    def delete_property(self, property_id: int) -> bool:
        """
        删除小区信息
        
        Args:
            property_id: 小区ID
            
        Returns:
            bool: 是否删除成功
        """
        # 查询小区
        property_obj = self.db.query(Property).filter(Property.id == property_id).first()
        
        if not property_obj:
            return False
        
        # 删除小区
        self.db.delete(property_obj)
        self.db.commit()
        
        return True
    
    def search_properties(self, city: str, keyword: str, limit: int = 10) -> List[Property]:
        """
        搜索小区
        
        Args:
            city: 城市名称
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Property]: 搜索到的小区列表
        """
        # 搜索小区
        properties = self.db.query(Property).filter(
            Property.city == city,
            or_(
                Property.name.contains(keyword),
                Property.address.contains(keyword)
            )
        ).limit(limit).all()
        
        return properties
    
    def add_price_history(self, property_id: int, price: float, price_date: str, source: str) -> PriceHistory:
        """
        添加价格历史
        
        Args:
            property_id: 小区ID
            price: 价格
            price_date: 价格日期
            source: 数据来源
            
        Returns:
            PriceHistory: 创建的价格历史对象
        """
        # 创建价格历史对象
        price_history = PriceHistory(
            property_id=property_id,
            price=price,
            price_date=price_date,
            source=source
        )
        
        # 添加到数据库
        self.db.add(price_history)
        self.db.commit()
        self.db.refresh(price_history)
        
        return price_history
    
    def get_price_history(self, property_id: int, limit: int = 10) -> List[PriceHistory]:
        """
        获取价格历史
        
        Args:
            property_id: 小区ID
            limit: 返回结果数量限制
            
        Returns:
            List[PriceHistory]: 价格历史列表
        """
        # 查询价格历史
        price_histories = self.db.query(PriceHistory).filter(
            PriceHistory.property_id == property_id
        ).order_by(
            PriceHistory.price_date.desc()
        ).limit(limit).all()
        
        return price_histories


# 导出
def create_property_dao(db: Session) -> PropertyDAO:
    """
    创建PropertyDAO实例
    
    Args:
        db: SQLAlchemy会话对象
        
    Returns:
        PropertyDAO: PropertyDAO实例
    """
    return PropertyDAO(db)


__all__ = ["PropertyDAO", "create_property_dao"]
