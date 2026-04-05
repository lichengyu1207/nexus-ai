from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class CertificateStatus(str, Enum):
    NOT_ISSUED = "未下证"
    ISSUED_NOT_TWO_YEARS = "已下证不满二"
    TWO_YEARS = "满二"
    FIVE_YEARS = "满五"


class LandType(str, Enum):
    ALLOCATED = "划拨"
    GRANTED = "出让"


class PropertyInput(BaseModel):
    city: str = Field(..., description="城市名称")
    district: str = Field(..., description="区域/片区")
    community: str = Field(..., description="小区名称")
    building: Optional[str] = Field(None, description="楼栋号")
    unit: Optional[str] = Field(None, description="单元号")
    room: Optional[str] = Field(None, description="房间号")
    area: float = Field(90, description="建筑面积（平方米）")
    certificate_status: CertificateStatus = Field(..., description="产权状况")
    land_type: LandType = Field(..., description="土地性质")
    is_resettlement: bool = Field(True, description="是否为安置房")
    
    class Config:
        json_schema_extra = {
            "example": {
                "city": "泰安市",
                "district": "高铁南片区",
                "community": "小堰堤社区",
                "building": "5号楼",
                "unit": "2单元",
                "room": "2202室",
                "area": 90,
                "certificate_status": "满二",
                "land_type": "划拨",
                "is_resettlement": True
            }
        }


class ReferenceCase(BaseModel):
    area: float = Field(..., description="面积（平方米）")
    price: int = Field(..., description="总价（元）")
    unit_price: int = Field(..., description="单价（元/平方米）")
    note: str = Field(..., description="备注信息")


class CommunityData(BaseModel):
    community_name: str = Field(..., description="小区名称")
    average_price: int = Field(..., description="小区均价（元/平方米）")
    comparable_community: Optional[str] = Field(None, description="可比小区名称")
    comparable_price: Optional[int] = Field(None, description="可比小区均价（元/平方米）")
    business_district_price: int = Field(..., description="商圈均价（元/平方米）")
    reference_cases: List[ReferenceCase] = Field(default_factory=list, description="参考案例")
    rental_reference: Optional[dict] = Field(None, description="租赁参考")
    data_source: str = Field(..., description="数据来源")
    update_time: str = Field(..., description="数据更新时间")


class EstimationFactors(BaseModel):
    base_price: int = Field(..., description="基准单价（元/平方米）")
    resettlement_discount: float = Field(1.0, description="安置房折价系数")
    certificate_discount: float = Field(1.0, description="产权折价系数")
    land_discount: float = Field(1.0, description="土地折价系数")
    final_unit_price: int = Field(..., description="最终单价（元/平方米）")


class EstimationResult(BaseModel):
    conservative_price: int = Field(..., description="保守估值（元）")
    conservative_unit_price: int = Field(..., description="保守单价（元/平方米）")
    price_range: List[int] = Field(..., description="合理价格区间[下限, 上限]（元）")
    reference_cases: List[ReferenceCase] = Field(default_factory=list, description="参考案例")
    estimation_factors: EstimationFactors = Field(..., description="估价因子说明")
    disclaimer: str = Field(..., description="免责声明")


class ValuationReport(BaseModel):
    property_info: PropertyInput = Field(..., description="房产信息")
    community_data: CommunityData = Field(..., description="小区数据")
    estimation_result: EstimationResult = Field(..., description="估价结果")
    report_date: str = Field(..., description="报告日期")
    report_id: str = Field(..., description="报告编号")
    disclaimer: str = Field(..., description="免责声明")
