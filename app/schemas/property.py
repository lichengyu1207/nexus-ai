from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PropertyBase(BaseModel):
    address: str
    type: str
    area: float
    age: int
    description: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    address: Optional[str] = None
    type: Optional[str] = None
    area: Optional[float] = None
    age: Optional[int] = None
    description: Optional[str] = None


class Property(PropertyBase):
    id: str
    price: Optional[float] = None
    market_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PropertyInDB(Property):
    pass