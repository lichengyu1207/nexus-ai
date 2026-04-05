from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ReportBase(BaseModel):
    property_id: str
    title: str
    content: str


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class Report(ReportBase):
    id: str
    property_address: str
    status: str
    created_at: datetime
    updated_at: datetime
    generated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReportInDB(Report):
    pass