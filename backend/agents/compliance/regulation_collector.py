"""
法规采集智能体
从官方渠道采集最新法律法规
"""
import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RegulationSource(str, Enum):
    NPC = "npc"
    STATE_COUNCIL = "state_council"
    MINISTRY_HOUSE = "mohurd"
    SAMR = "samr"
    CAC = "cac"
    LOCAL_GOV = "local_gov"
    COURT = "court"


class RegulationType(str, Enum):
    LAW = "law"
    REGULATION = "regulation"
    RULE = "rule"
    INTERPRETATION = "interpretation"
    GUIDELINE = "guideline"
    STANDARD = "standard"


class RegulationDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    source: RegulationSource
    regulation_type: RegulationType
    document_number: Optional[str] = None
    publish_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    content: str = ""
    content_hash: str = ""
    url: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    related_industries: List[str] = Field(default_factory=list)
    status: str = "effective"
    version: int = 1
    collected_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class SourceConfig(BaseModel):
    source_id: str
    source_type: RegulationSource
    base_url: str
    list_url_pattern: str = ""
    content_url_pattern: str = ""
    update_frequency: int = 24
    last_crawled: Optional[datetime] = None
    enabled: bool = True


class RegulationCollectorAgent:
    SOURCE_CONFIGS = {
        RegulationSource.NPC: {
            "base_url": "http://www.npc.gov.cn",
            "list_url": "/npc/c2/c30834/list.shtml",
            "name": "全国人大"
        },
        RegulationSource.STATE_COUNCIL: {
            "base_url": "http://www.gov.cn",
            "list_url": "/zhengce/zhengceku/index.htm",
            "name": "国务院"
        },
        RegulationSource.MINISTRY_HOUSE: {
            "base_url": "https://www.mohurd.gov.cn",
            "list_url": "/gongkai/fdzdj/index.html",
            "name": "住建部"
        },
        RegulationSource.SAMR: {
            "base_url": "https://www.samr.gov.cn",
            "list_url": "/xwzx/gsxw/index.html",
            "name": "市场监管总局"
        },
        RegulationSource.CAC: {
            "base_url": "http://www.cac.gov.cn",
            "list_url": "/xxfb/zzcjd/index.htm",
            "name": "网信办"
        },
        RegulationSource.COURT: {
            "base_url": "https://www.court.gov.cn",
            "list_url": "/shenpan/index.html",
            "name": "最高人民法院"
        }
    }
    
    REAL_ESTATE_KEYWORDS = [
        "房地产", "不动产", "房屋", "住宅", "土地", "物业", "房产",
        "估价", "评估", "交易", "租赁", "抵押", "产权", "登记",
        "商品房", "二手房", "保障房", "公积金", "契税", "房产税"
    ]
    
    def __init__(
        self,
        agent_id: str,
        name: str = "RegulationCollector",
        db_pool: Optional[Any] = None,
        notification_service: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.db_pool = db_pool
        self.notification_service = notification_service
        
        self.collected_documents: Dict[str, RegulationDocument] = {}
        self.source_configs: Dict[RegulationSource, SourceConfig] = {}
        self._init_source_configs()
        
        self.crawl_interval = timedelta(hours=24)
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    def _init_source_configs(self):
        for source_type, config in self.SOURCE_CONFIGS.items():
            self.source_configs[source_type] = SourceConfig(
                source_id=f"source_{source_type.value}",
                source_type=source_type,
                base_url=config["base_url"],
                list_url_pattern=config.get("list_url", ""),
                update_frequency=24
            )
    
    async def initialize(self):
        self.logger.info(f"RegulationCollectorAgent {self.agent_id} initialized")
    
    async def collect_from_source(
        self,
        source: RegulationSource,
        limit: int = 50
    ) -> List[RegulationDocument]:
        documents = []
        
        config = self.source_configs.get(source)
        if not config or not config.enabled:
            return documents
        
        try:
            mock_documents = await self._mock_crawl(source, limit)
            
            for doc_data in mock_documents:
                content_hash = self._compute_hash(doc_data.get("content", ""))
                
                doc = RegulationDocument(
                    title=doc_data.get("title", ""),
                    source=source,
                    regulation_type=RegulationType(doc_data.get("type", "rule")),
                    document_number=doc_data.get("document_number"),
                    publish_date=doc_data.get("publish_date"),
                    effective_date=doc_data.get("effective_date"),
                    content=doc_data.get("content", ""),
                    content_hash=content_hash,
                    url=doc_data.get("url"),
                    keywords=doc_data.get("keywords", []),
                    related_industries=doc_data.get("industries", [])
                )
                
                existing = self.collected_documents.get(doc.document_number or doc.title)
                if existing:
                    if existing.content_hash != content_hash:
                        doc.version = existing.version + 1
                        doc.updated_at = datetime.now()
                        documents.append(doc)
                        self.collected_documents[doc.document_number or doc.title] = doc
                else:
                    documents.append(doc)
                    self.collected_documents[doc.document_number or doc.title] = doc
            
            config.last_crawled = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error collecting from {source}: {e}")
        
        return documents
    
    async def _mock_crawl(
        self,
        source: RegulationSource,
        limit: int
    ) -> List[Dict[str, Any]]:
        mock_docs = []
        
        base_docs = [
            {
                "title": "中华人民共和国城市房地产管理法",
                "type": "law",
                "document_number": "主席令第29号",
                "publish_date": datetime(2019, 8, 26),
                "effective_date": datetime(2020, 1, 1),
                "content": "为了加强对城市房地产的管理，维护房地产市场秩序...",
                "keywords": ["房地产", "管理", "开发", "交易"],
                "industries": ["real_estate"]
            },
            {
                "title": "不动产登记暂行条例",
                "type": "regulation",
                "document_number": "国务院令第656号",
                "publish_date": datetime(2014, 11, 24),
                "effective_date": datetime(2015, 3, 1),
                "content": "为整合不动产登记职责，规范登记行为...",
                "keywords": ["不动产", "登记", "产权"],
                "industries": ["real_estate"]
            },
            {
                "title": "房地产估价机构管理办法",
                "type": "rule",
                "document_number": "住建部令第14号",
                "publish_date": datetime(2013, 6, 29),
                "effective_date": datetime(2013, 10, 1),
                "content": "为了规范房地产估价机构行为，维护房地产估价市场秩序...",
                "keywords": ["房地产估价", "机构", "资质"],
                "industries": ["real_estate", "valuation"]
            },
            {
                "title": "个人信息保护法",
                "type": "law",
                "document_number": "主席令第91号",
                "publish_date": datetime(2021, 8, 20),
                "effective_date": datetime(2021, 11, 1),
                "content": "为了保护个人信息权益，规范个人信息处理活动...",
                "keywords": ["个人信息", "隐私", "数据处理"],
                "industries": ["all"]
            },
            {
                "title": "数据安全法",
                "type": "law",
                "document_number": "主席令第84号",
                "publish_date": datetime(2021, 6, 10),
                "effective_date": datetime(2021, 9, 1),
                "content": "为了规范数据处理活动，保障数据安全...",
                "keywords": ["数据安全", "数据处理", "分类分级"],
                "industries": ["all"]
            }
        ]
        
        for doc in base_docs[:limit]:
            mock_docs.append(doc)
        
        return mock_docs
    
    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def collect_all_sources(self) -> Dict[str, List[RegulationDocument]]:
        results = {}
        
        for source in RegulationSource:
            documents = await self.collect_from_source(source)
            if documents:
                results[source.value] = documents
        
        return results
    
    async def check_updates(self) -> List[Dict[str, Any]]:
        updates = []
        
        for source, config in self.source_configs.items():
            if not config.enabled:
                continue
            
            last_crawled = config.last_crawled
            if last_crawled:
                hours_since = (datetime.now() - last_crawled).total_seconds() / 3600
                if hours_since < config.update_frequency:
                    continue
            
            new_docs = await self.collect_from_source(source, limit=10)
            
            for doc in new_docs:
                if doc.version > 1:
                    updates.append({
                        "type": "update",
                        "document": doc.dict(),
                        "source": source.value
                    })
                else:
                    updates.append({
                        "type": "new",
                        "document": doc.dict(),
                        "source": source.value
                    })
        
        return updates
    
    async def search_regulations(
        self,
        keywords: List[str],
        source: Optional[RegulationSource] = None,
        regulation_type: Optional[RegulationType] = None
    ) -> List[RegulationDocument]:
        results = []
        
        for doc in self.collected_documents.values():
            if source and doc.source != source:
                continue
            
            if regulation_type and doc.regulation_type != regulation_type:
                continue
            
            doc_keywords = set(doc.keywords)
            search_keywords = set(keywords)
            
            if doc_keywords & search_keywords:
                results.append(doc)
                continue
            
            for keyword in keywords:
                if keyword in doc.title or keyword in doc.content:
                    results.append(doc)
                    break
        
        return results
    
    async def get_regulation(self, document_id: str) -> Optional[RegulationDocument]:
        for doc in self.collected_documents.values():
            if doc.id == document_id:
                return doc
        return None
    
    async def start_continuous_collection(self):
        self._running = True
        asyncio.create_task(self._collection_loop())
    
    async def stop_continuous_collection(self):
        self._running = False
    
    async def _collection_loop(self):
        while self._running:
            try:
                updates = await self.check_updates()
                
                if updates and self.notification_service:
                    for update in updates:
                        await self.notification_service.notify({
                            "type": "regulation_update",
                            "data": update
                        })
                
                await asyncio.sleep(self.crawl_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(3600)
    
    def get_statistics(self) -> Dict[str, Any]:
        by_source = {}
        for doc in self.collected_documents.values():
            source = doc.source.value
            by_source[source] = by_source.get(source, 0) + 1
        
        by_type = {}
        for doc in self.collected_documents.values():
            reg_type = doc.regulation_type.value
            by_type[reg_type] = by_type.get(reg_type, 0) + 1
        
        return {
            "total_documents": len(self.collected_documents),
            "by_source": by_source,
            "by_type": by_type,
            "sources_enabled": len([c for c in self.source_configs.values() if c.enabled])
        }
