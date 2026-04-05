"""
区域信息API路由
提供区域介绍、交通、配套、发展前景等信息
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
import uuid

from ..database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/district-info", tags=["district-info"])


class DistrictInfoResponse(BaseModel):
    """区域信息响应模型"""
    id: str
    city: str
    district: Optional[str] = None
    introduction: Optional[str] = None
    transportation: Optional[str] = None
    education: Optional[str] = None
    commercial: Optional[str] = None
    future_plan: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None


class DistrictInfoListResponse(BaseModel):
    """区域信息列表响应模型"""
    city: str
    districts: List[DistrictInfoResponse]
    total: int


class DistrictInfoCreate(BaseModel):
    """创建区域信息请求模型"""
    city: str
    district: Optional[str] = None
    introduction: Optional[str] = None
    transportation: Optional[str] = None
    education: Optional[str] = None
    commercial: Optional[str] = None
    future_plan: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None


@router.get("", response_model=DistrictInfoListResponse)
async def get_district_info_list(
    city: str = Query(..., description="城市名称"),
    district: Optional[str] = Query(None, description="区域名称（可选）")
):
    """
    获取区域信息列表
    
    Args:
        city: 城市名称
        district: 区域名称（可选，用于精确匹配）
        
    Returns:
        DistrictInfoListResponse: 区域信息列表
    """
    conn = await get_db_connection()
    try:
        if district:
            cursor = await conn.execute(
                """
                SELECT * FROM city_district_info 
                WHERE city = ? AND district = ?
                """,
                (city, district)
            )
        else:
            cursor = await conn.execute(
                """
                SELECT * FROM city_district_info 
                WHERE city = ?
                ORDER BY district
                """,
                (city,)
            )
        
        rows = await cursor.fetchall()
        
        districts = []
        for row in rows:
            pros = json.loads(row["pros"]) if row["pros"] else []
            cons = json.loads(row["cons"]) if row["cons"] else []
            
            districts.append(DistrictInfoResponse(
                id=row["id"],
                city=row["city"],
                district=row["district"],
                introduction=row["introduction"],
                transportation=row["transportation"],
                education=row["education"],
                commercial=row["commercial"],
                future_plan=row["future_plan"],
                pros=pros,
                cons=cons
            ))
        
        return DistrictInfoListResponse(
            city=city,
            districts=districts,
            total=len(districts)
        )
    finally:
        await conn.close()


@router.get("/detail", response_model=DistrictInfoResponse)
async def get_district_info_detail(
    city: str = Query(..., description="城市名称"),
    district: str = Query(..., description="区域名称")
):
    """
    获取单个区域详细信息
    
    Args:
        city: 城市名称
        district: 区域名称
        
    Returns:
        DistrictInfoResponse: 区域详细信息
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT * FROM city_district_info 
            WHERE city = ? AND district = ?
            """,
            (city, district)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="未找到该区域信息")
        
        pros = json.loads(row["pros"]) if row["pros"] else []
        cons = json.loads(row["cons"]) if row["cons"] else []
        
        return DistrictInfoResponse(
            id=row["id"],
            city=row["city"],
            district=row["district"],
            introduction=row["introduction"],
            transportation=row["transportation"],
            education=row["education"],
            commercial=row["commercial"],
            future_plan=row["future_plan"],
            pros=pros,
            cons=cons
        )
    finally:
        await conn.close()


@router.post("", response_model=DistrictInfoResponse)
async def create_district_info(data: DistrictInfoCreate):
    """
    创建区域信息（管理员接口）
    
    Args:
        data: 区域信息数据
        
    Returns:
        DistrictInfoResponse: 创建的区域信息
    """
    conn = await get_db_connection()
    try:
        info_id = str(uuid.uuid4())
        pros_json = json.dumps(data.pros, ensure_ascii=False) if data.pros else None
        cons_json = json.dumps(data.cons, ensure_ascii=False) if data.cons else None
        
        await conn.execute(
            """
            INSERT INTO city_district_info (
                id, city, district, introduction, transportation,
                education, commercial, future_plan, pros, cons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                info_id, data.city, data.district, data.introduction,
                data.transportation, data.education, data.commercial,
                data.future_plan, pros_json, cons_json
            )
        )
        await conn.commit()
        
        return DistrictInfoResponse(
            id=info_id,
            city=data.city,
            district=data.district,
            introduction=data.introduction,
            transportation=data.transportation,
            education=data.education,
            commercial=data.commercial,
            future_plan=data.future_plan,
            pros=data.pros,
            cons=data.cons
        )
    finally:
        await conn.close()


@router.put("/{info_id}", response_model=DistrictInfoResponse)
async def update_district_info(info_id: str, data: DistrictInfoCreate):
    """
    更新区域信息（管理员接口）
    
    Args:
        info_id: 区域信息ID
        data: 更新数据
        
    Returns:
        DistrictInfoResponse: 更新后的区域信息
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM city_district_info WHERE id = ?",
            (info_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="区域信息不存在")
        
        pros_json = json.dumps(data.pros, ensure_ascii=False) if data.pros else None
        cons_json = json.dumps(data.cons, ensure_ascii=False) if data.cons else None
        
        await conn.execute(
            """
            UPDATE city_district_info SET
                city = ?, district = ?, introduction = ?, transportation = ?,
                education = ?, commercial = ?, future_plan = ?, pros = ?, cons = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                data.city, data.district, data.introduction, data.transportation,
                data.education, data.commercial, data.future_plan, pros_json, cons_json,
                info_id
            )
        )
        await conn.commit()
        
        return DistrictInfoResponse(
            id=info_id,
            city=data.city,
            district=data.district,
            introduction=data.introduction,
            transportation=data.transportation,
            education=data.education,
            commercial=data.commercial,
            future_plan=data.future_plan,
            pros=data.pros,
            cons=data.cons
        )
    finally:
        await conn.close()


@router.delete("/{info_id}")
async def delete_district_info(info_id: str):
    """
    删除区域信息（管理员接口）
    
    Args:
        info_id: 区域信息ID
        
    Returns:
        dict: 删除结果
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id FROM city_district_info WHERE id = ?",
            (info_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="区域信息不存在")
        
        await conn.execute(
            "DELETE FROM city_district_info WHERE id = ?",
            (info_id,)
        )
        await conn.commit()
        
        return {"success": True, "message": "区域信息已删除"}
    finally:
        await conn.close()


@router.get("/cities", response_model=List[str])
async def get_available_cities():
    """
    获取有区域信息的城市列表
    
    Returns:
        List[str]: 城市列表
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT DISTINCT city FROM city_district_info ORDER BY city"
        )
        rows = await cursor.fetchall()
        return [row["city"] for row in rows]
    finally:
        await conn.close()


async def init_district_info_data():
    """初始化一线城市核心区域信息数据"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) as count FROM city_district_info")
        result = await cursor.fetchone()
        
        if result["count"] > 0:
            logger.info("区域信息数据已存在，跳过初始化")
            return
        
        default_data = [
            {
                "city": "深圳",
                "district": "南山区",
                "introduction": "南山区是深圳的高新技术产业基地和科技创新中心，聚集了大量科技企业和创新人才。区内有深圳大学、南方科技大学等高校，以及腾讯、大疆等知名企业总部。",
                "transportation": "地铁1号线、2号线、5号线、7号线、9号线、11号线、12号线、13号线贯穿全区。深圳湾口岸连接香港，交通便利。",
                "education": "拥有深圳大学、南方科技大学、哈尔滨工业大学（深圳）等高校。中小学教育资源丰富，包括深圳中学、南山外国语学校等名校。",
                "commercial": "海岸城、万象天地、深圳湾万象城、来福士广场等大型商业综合体。科技园、后海、前海等商务区繁荣。",
                "future_plan": "前海深港现代服务业合作区、深圳湾超级总部基地、西丽湖国际科教城等重点发展区域，未来发展潜力巨大。",
                "pros": ["科技创新中心", "教育资源丰富", "交通便利", "商业配套完善", "环境优美"],
                "cons": ["房价较高", "生活成本高", "部分区域拥堵"]
            },
            {
                "city": "深圳",
                "district": "福田区",
                "introduction": "福田区是深圳的中心城区，是深圳的行政、文化、金融和国际交往中心。区内有深圳证券交易所、市民中心等地标建筑。",
                "transportation": "地铁1号线、2号线、3号线、4号线、5号线、7号线、9号线、10号线、11号线交汇，福田高铁站连接全国。皇岗口岸、福田口岸连接香港。",
                "education": "深圳外国语学校、福田外国语学校、红岭中学等优质学校。深圳图书馆、音乐厅等文化设施集中。",
                "commercial": "COCO Park、中心城、卓悦中心、平安金融中心等商业地标。华强北电子市场闻名全国。",
                "future_plan": "香蜜湖新金融中心、河套深港科技创新合作区等重点规划，持续提升中心城区地位。",
                "pros": ["城市中心", "交通枢纽", "金融中心", "配套完善", "教育资源优质"],
                "cons": ["房价高企", "人口密集", "停车位紧张"]
            },
            {
                "city": "深圳",
                "district": "宝安区",
                "introduction": "宝安区是深圳的西部中心，拥有深圳宝安国际机场和前海合作区部分区域。近年来发展迅速，是深圳重点发展的区域之一。",
                "transportation": "地铁1号线、5号线、11号线、12号线、20号线。宝安机场连接全球，深中通道连接中山。",
                "education": "宝安中学、新安中学等优质学校。深圳职业技术学院等高校。",
                "commercial": "壹方城、海雅缤纷城、宝安万达等大型商业。宝安中心区发展迅速。",
                "future_plan": "前海合作区扩容、海洋新城、国际会展城等重大规划，发展前景广阔。",
                "pros": ["发展潜力大", "交通便利", "房价相对较低", "配套日趋完善"],
                "cons": ["部分区域配套待完善", "距离市中心较远"]
            },
            {
                "city": "北京",
                "district": "朝阳区",
                "introduction": "朝阳区是北京的城市副中心，是北京的经济强区和国际化窗口。区内有CBD、三里屯、望京等知名商圈，使馆区集中于此。",
                "transportation": "地铁1号线、6号线、10号线、14号线等多条线路贯穿。首都机场位于区内，交通便利。",
                "education": "北京八十中、朝阳外国语学校等优质学校。中国传媒大学、对外经贸大学等高校。",
                "commercial": "国贸CBD、三里屯、望京SOHO、SKP等商业地标。使馆区国际化氛围浓厚。",
                "future_plan": "CBD东扩、第四使馆区、金盏国际合作服务区等规划，持续提升国际化水平。",
                "pros": ["国际化程度高", "商业繁荣", "交通便利", "就业机会多"],
                "cons": ["房价较高", "交通拥堵", "生活成本高"]
            },
            {
                "city": "北京",
                "district": "海淀区",
                "introduction": "海淀区是北京的科教文化中心，聚集了清华、北大等顶尖高校和中关村科技园区。是中国科技创新的重要策源地。",
                "transportation": "地铁4号线、10号线、13号线、16号线等。北京北站连接张家口、呼和浩特等地。",
                "education": "清华大学、北京大学、中国人民大学等顶尖高校。人大附中、清华附中、北大附中等名校云集。",
                "commercial": "中关村、五道口、西直门等商圈。科技企业总部集中。",
                "future_plan": "中关村科学城、海淀北部新区等规划，打造全球科技创新高地。",
                "pros": ["教育资源顶级", "科技创新中心", "文化氛围浓厚", "人才聚集"],
                "cons": ["房价极高", "学位竞争激烈", "部分区域老旧"]
            },
            {
                "city": "上海",
                "district": "浦东新区",
                "introduction": "浦东新区是上海的金融中心和改革开放前沿，陆家嘴金融贸易区、张江高科技园区、浦东国际机场均位于此。是中国最具活力的经济区域之一。",
                "transportation": "地铁2号线、4号线、6号线、7号线、9号线、11号线、12号线、13号线、14号线、16号线、18号线。浦东机场、磁悬浮列车连接市区。",
                "education": "上海纽约大学、上海科技大学等高校。上海中学东校、建平中学等优质学校。",
                "commercial": "陆家嘴金融中心、世纪大道、张江、前滩等商圈。国金中心、正大广场等商业地标。",
                "future_plan": "临港新片区、张江科学城扩区、前滩国际商务区等重大规划，发展空间广阔。",
                "pros": ["经济活力强", "发展空间大", "国际化程度高", "基础设施完善"],
                "cons": ["区域面积大", "部分区域配套待完善", "通勤距离长"]
            },
            {
                "city": "上海",
                "district": "黄浦区",
                "introduction": "黄浦区是上海的中心城区，是上海的行政、金融、文化中心。外滩、南京路、人民广场等上海地标均位于此。",
                "transportation": "地铁1号线、2号线、8号线、10号线、13号线等交汇。人民广场是上海地铁枢纽。",
                "education": "上海中学、格致中学、大同中学等百年名校。教育资源优质。",
                "commercial": "南京路步行街、淮海路、新天地、豫园等商业地标。外滩金融集聚带。",
                "future_plan": "外滩金融集聚带、南京路商圈升级等规划，巩固中心城区地位。",
                "pros": ["地理位置核心", "商业繁荣", "文化底蕴深厚", "教育资源优质"],
                "cons": ["房价极高", "人口密集", "老建筑较多"]
            },
            {
                "city": "广州",
                "district": "天河区",
                "introduction": "天河区是广州的城市中心，是广州的金融、商务、科技中心。珠江新城、天河CBD是广州的城市名片。",
                "transportation": "地铁1号线、3号线、5号线、6号线、21号线等。广州东站连接珠三角各地。",
                "education": "华南师范大学附属中学、广州中学等名校。暨南大学、华南理工大学等高校。",
                "commercial": "珠江新城、天河城、正佳广场、太古汇等商业地标。CBD商务氛围浓厚。",
                "future_plan": "国际金融城、天河智慧城等规划，持续提升中心城区能级。",
                "pros": ["城市中心", "商业繁荣", "交通便利", "就业机会多"],
                "cons": ["房价较高", "交通拥堵", "生活节奏快"]
            },
            {
                "city": "杭州",
                "district": "西湖区",
                "introduction": "西湖区因西湖而得名，是杭州的文化旅游中心和科教创新高地。区内有西湖、西溪湿地等著名景点，浙江大学等高校。",
                "transportation": "地铁1号线、2号线、3号线、5号线、6号线、10号线、19号线。杭州西站连接长三角各地。",
                "education": "浙江大学、浙江工业大学等高校。杭州第二中学、学军中学等名校。",
                "commercial": "西溪银泰、城西银泰、西溪天街等商业综合体。文三路电子一条街。",
                "future_plan": "云栖小镇、紫金港科技城、三墩北等重点发展区域，科创产业蓬勃发展。",
                "pros": ["环境优美", "教育资源丰富", "文化底蕴深厚", "科创产业发达"],
                "cons": ["房价较高", "部分区域拥堵", "老小区较多"]
            },
            {
                "city": "成都",
                "district": "高新区",
                "introduction": "成都高新区是成都的科技创新中心和经济发展引擎，聚集了大量科技企业和创新人才。是成都最具活力的经济区域。",
                "transportation": "地铁1号线、5号线、6号线、7号线、8号线、18号线。成都南站连接全国。",
                "education": "成都七中初中、石室天府中学等优质学校。四川大学、电子科技大学等高校周边。",
                "commercial": "环球中心、SKP、银泰城等大型商业。天府软件园、金融城等商务区。",
                "future_plan": "新川创新科技园、天府国际生物城等规划，打造西部创新高地。",
                "pros": ["发展潜力大", "就业机会多", "环境优美", "配套完善"],
                "cons": ["房价上涨快", "部分区域待成熟", "通勤距离长"]
            },
            {
                "city": "南京",
                "district": "建邺区",
                "introduction": "建邺区是南京的城市新中心，河西新城所在地。是南京的金融、商务、会展中心，现代化程度高。",
                "transportation": "地铁2号线、10号线、S3号线。南京南站连接全国高铁网络。",
                "education": "金陵中学河西分校、南京外国语学校河西分校等优质学校。",
                "commercial": "河西万达、金鹰世界、华采天地等商业综合体。国际博览中心。",
                "future_plan": "河西金融集聚区、鱼嘴商务区等规划，打造南京城市新名片。",
                "pros": ["规划先进", "环境优美", "配套完善", "发展潜力大"],
                "cons": ["房价较高", "生活成本上升", "部分区域待成熟"]
            },
            {
                "city": "苏州",
                "district": "工业园区",
                "introduction": "苏州工业园区是中新两国政府合作项目，是中国最具竞争力的开发区之一。城市规划先进，产业发达，环境优美。",
                "transportation": "地铁1号线、3号线、5号线。苏州园区站连接上海。",
                "education": "苏州中学园区校、星海实验中学等优质学校。西交利物浦大学、苏州大学独墅湖校区。",
                "commercial": "苏州中心、久光百货、圆融时代广场等商业地标。金鸡湖商圈。",
                "future_plan": "金鸡湖商务区、独墅湖科教创新区等规划，持续提升国际化水平。",
                "pros": ["规划先进", "环境优美", "国际化程度高", "产业发达"],
                "cons": ["房价较高", "部分区域待成熟", "通勤距离长"]
            }
        ]
        
        for data in default_data:
            info_id = str(uuid.uuid4())
            pros_json = json.dumps(data["pros"], ensure_ascii=False)
            cons_json = json.dumps(data["cons"], ensure_ascii=False)
            
            await conn.execute(
                """
                INSERT INTO city_district_info (
                    id, city, district, introduction, transportation,
                    education, commercial, future_plan, pros, cons
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    info_id, data["city"], data["district"], data["introduction"],
                    data["transportation"], data["education"], data["commercial"],
                    data["future_plan"], pros_json, cons_json
                )
            )
        
        await conn.commit()
        logger.info(f"初始化区域信息数据完成，共 {len(default_data)} 条")
    finally:
        await conn.close()
