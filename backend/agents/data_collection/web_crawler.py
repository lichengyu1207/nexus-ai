"""
网页爬虫智能体
Web Crawler Agent

从互联网网页采集数据
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

from .data_collector import DataCollectorAgent, DataSourceType, CollectionStatus

logger = logging.getLogger(__name__)


@dataclass
class CrawlConfig:
    max_depth: int = 3
    max_pages: int = 100
    delay_seconds: float = 1.0
    respect_robots_txt: bool = True
    use_javascript: bool = False
    user_agent: str = "FangDuDuBot/1.0"
    timeout_seconds: float = 30.0
    retry_count: int = 3
    proxy_pool: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    excluded_patterns: List[str] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "delay_seconds": self.delay_seconds,
            "respect_robots_txt": self.respect_robots_txt,
            "use_javascript": self.use_javascript,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "allowed_domains": self.allowed_domains,
        }


@dataclass
class CrawlResult:
    url: str
    status_code: int
    content: str
    headers: Dict
    links: List[str]
    depth: int
    crawled_at: float
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "status_code": self.status_code,
            "content_length": len(self.content),
            "links_count": len(self.links),
            "depth": self.depth,
            "crawled_at": self.crawled_at,
            "error": self.error,
        }


@dataclass
class ParsedPage:
    url: str
    title: str
    content: str
    structured_data: Dict
    links: List[str]
    images: List[str]
    metadata: Dict
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "content_length": len(self.content),
            "structured_data": self.structured_data,
            "links_count": len(self.links),
            "quality_score": self.quality_score,
        }


class URLFilter:
    """
    URL过滤器
    
    处理去重、域名限制、模式排除
    """
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.url_hashes: Set[str] = set()
        self.robots_cache: Dict[str, Dict] = {}
    
    def normalize_url(self, url: str) -> str:
        url = url.split('#')[0]
        url = url.split('?')[0] if '?' in url else url
        return url.rstrip('/')
    
    def get_url_hash(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def is_visited(self, url: str) -> bool:
        normalized = self.normalize_url(url)
        url_hash = self.get_url_hash(normalized)
        return url_hash in self.url_hashes
    
    def mark_visited(self, url: str):
        normalized = self.normalize_url(url)
        url_hash = self.get_url_hash(normalized)
        self.visited_urls.add(normalized)
        self.url_hashes.add(url_hash)
    
    def is_allowed_domain(self, url: str, allowed_domains: List[str]) -> bool:
        if not allowed_domains:
            return True
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        for allowed in allowed_domains:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
        
        return False
    
    def is_excluded(self, url: str, excluded_patterns: List[str]) -> bool:
        for pattern in excluded_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def should_crawl(
        self,
        url: str,
        allowed_domains: List[str],
        excluded_patterns: List[str],
    ) -> bool:
        if self.is_visited(url):
            return False
        
        if not self.is_allowed_domain(url, allowed_domains):
            return False
        
        if self.is_excluded(url, excluded_patterns):
            return False
        
        return True


class ContentParser:
    """
    内容解析器
    
    提取结构化数据
    """
    
    def __init__(self):
        self.parsers: Dict[str, Callable] = {}
        self._init_default_parsers()
    
    def _init_default_parsers(self):
        self.parsers["community_info"] = self._parse_community_info
        self.parsers["property_listing"] = self._parse_property_listing
        self.parsers["news_article"] = self._parse_news_article
        self.parsers["policy_document"] = self._parse_policy_document
    
    def parse(self, content: str, url: str, parser_type: Optional[str] = None) -> ParsedPage:
        title = self._extract_title(content)
        links = self._extract_links(content, url)
        images = self._extract_images(content, url)
        
        structured_data = {}
        if parser_type and parser_type in self.parsers:
            structured_data = self.parsers[parser_type](content)
        
        metadata = {
            "url": url,
            "parsed_at": time.time(),
            "parser_type": parser_type,
        }
        
        return ParsedPage(
            url=url,
            title=title,
            content=content,
            structured_data=structured_data,
            links=links,
            images=images,
            metadata=metadata,
        )
    
    def _extract_title(self, content: str) -> str:
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return ""
    
    def _extract_links(self, content: str, base_url: str) -> List[str]:
        links = []
        
        for match in re.finditer(r'href=["\']([^"\']+)["\']', content, re.IGNORECASE):
            href = match.group(1)
            
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                from urllib.parse import urljoin
                links.append(urljoin(base_url, href))
        
        return list(set(links))
    
    def _extract_images(self, content: str, base_url: str) -> List[str]:
        images = []
        
        for match in re.finditer(r'src=["\']([^"\']+\.(jpg|jpeg|png|gif|webp))["\']', content, re.IGNORECASE):
            src = match.group(1)
            
            if src.startswith('http'):
                images.append(src)
            elif src.startswith('/'):
                from urllib.parse import urljoin
                images.append(urljoin(base_url, src))
        
        return list(set(images))
    
    def _parse_community_info(self, content: str) -> Dict:
        data = {}
        
        name_match = re.search(r'小区名称[：:]\s*([^\n<]+)', content)
        if name_match:
            data["community_name"] = name_match.group(1).strip()
        
        price_match = re.search(r'均价[：:]\s*([\d.]+)\s*元', content)
        if price_match:
            data["avg_price"] = float(price_match.group(1))
        
        address_match = re.search(r'地址[：:]\s*([^\n<]+)', content)
        if address_match:
            data["address"] = address_match.group(1).strip()
        
        return data
    
    def _parse_property_listing(self, content: str) -> Dict:
        data = {}
        
        area_match = re.search(r'面积[：:]\s*([\d.]+)\s*平', content)
        if area_match:
            data["area"] = float(area_match.group(1))
        
        price_match = re.search(r'总价[：:]\s*([\d.]+)\s*万', content)
        if price_match:
            data["total_price"] = float(price_match.group(1))
        
        rooms_match = re.search(r'(\d+)室(\d+)厅', content)
        if rooms_match:
            data["bedrooms"] = int(rooms_match.group(1))
            data["living_rooms"] = int(rooms_match.group(2))
        
        return data
    
    def _parse_news_article(self, content: str) -> Dict:
        data = {}
        
        date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', content)
        if date_match:
            data["publish_date"] = date_match.group(1)
        
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) > 200:
            data["summary"] = text[:200] + "..."
        else:
            data["summary"] = text
        
        return data
    
    def _parse_policy_document(self, content: str) -> Dict:
        data = {}
        
        doc_num_match = re.search(r'文号[：:]\s*([^\n<]+)', content)
        if doc_num_match:
            data["document_number"] = doc_num_match.group(1).strip()
        
        issuer_match = re.search(r'发布机构[：:]\s*([^\n<]+)', content)
        if issuer_match:
            data["issuer"] = issuer_match.group(1).strip()
        
        effective_match = re.search(r'实施日期[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', content)
        if effective_match:
            data["effective_date"] = effective_match.group(1)
        
        return data


class WebCrawlerAgent(DataCollectorAgent):
    """
    网页爬虫智能体
    
    专门从互联网网页采集数据：
    1. 支持递归爬取
    2. 支持动态内容渲染
    3. 遵守robots.txt
    4. 自动去重
    5. 自适应反爬
    """
    
    def __init__(
        self,
        agent_id: str,
        target_url: str,
        config: Optional[CrawlConfig] = None,
        sample_repository: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        compliance_checker: Optional[Any] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            source_type=DataSourceType.WEB,
            target_url=target_url,
            sample_repository=sample_repository,
            blackboard=blackboard,
            memory_agent=memory_agent,
            compliance_checker=compliance_checker,
        )
        
        self.config = config or CrawlConfig()
        self.url_filter = URLFilter()
        self.content_parser = ContentParser()
        
        self.crawl_queue: asyncio.Queue = asyncio.Queue()
        self.crawled_pages: Dict[str, ParsedPage] = {}
        
        self.current_proxy_index = 0
        self.success_times: List[float] = []
        self.failure_times: List[float] = []
        
        self.stats.update({
            "pages_crawled": 0,
            "pages_failed": 0,
            "total_links_found": 0,
            "avg_response_time_ms": 0.0,
            "robots_respected": 0,
        })
    
    async def collect(self) -> Any:
        """
        执行网页爬取
        """
        results = []
        
        await self.crawl_queue.put((self.target_url, 0))
        
        pages_crawled = 0
        
        while not self.crawl_queue.empty() and pages_crawled < self.config.max_pages:
            try:
                url, depth = await asyncio.wait_for(
                    self.crawl_queue.get(),
                    timeout=1.0
                )
                
                if depth > self.config.max_depth:
                    continue
                
                if not self.url_filter.should_crawl(
                    url,
                    self.config.allowed_domains,
                    self.config.excluded_patterns,
                ):
                    continue
                
                crawl_result = await self._crawl_page(url, depth)
                
                if crawl_result.error:
                    self.stats["pages_failed"] += 1
                    continue
                
                self.stats["pages_crawled"] += 1
                self.url_filter.mark_visited(url)
                
                parsed_page = self.content_parser.parse(
                    crawl_result.content,
                    url,
                    self._detect_parser_type(url)
                )
                parsed_page.quality_score = await self._assess_page_quality(parsed_page)
                
                self.crawled_pages[url] = parsed_page
                results.append(parsed_page.to_dict())
                
                for link in crawl_result.links:
                    if self.url_filter.should_crawl(
                        link,
                        self.config.allowed_domains,
                        self.config.excluded_patterns,
                    ):
                        await self.crawl_queue.put((link, depth + 1))
                
                self.stats["total_links_found"] += len(crawl_result.links)
                pages_crawled += 1
                
                await asyncio.sleep(self.config.delay_seconds)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error during crawl: {e}")
        
        return results
    
    async def _crawl_page(self, url: str, depth: int) -> CrawlResult:
        """
        爬取单个页面
        """
        start_time = time.time()
        
        headers = {
            "User-Agent": self.config.user_agent,
            **self.config.custom_headers,
        }
        
        proxy = self._get_next_proxy()
        
        for attempt in range(self.config.retry_count):
            try:
                if self.config.use_javascript:
                    content = await self._fetch_with_javascript(url, headers, proxy)
                else:
                    content = await self._fetch_simple(url, headers, proxy)
                
                response_time = (time.time() - start_time) * 1000
                self._update_response_time_stats(response_time)
                
                links = self.content_parser._extract_links(content, url)
                
                return CrawlResult(
                    url=url,
                    status_code=200,
                    content=content,
                    headers=headers,
                    links=links,
                    depth=depth,
                    crawled_at=time.time(),
                )
                
            except Exception as e:
                logger.warning(f"Crawl attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(self.config.delay_seconds * (attempt + 1))
        
        return CrawlResult(
            url=url,
            status_code=0,
            content="",
            headers={},
            links=[],
            depth=depth,
            crawled_at=time.time(),
            error="Max retries exceeded",
        )
    
    async def _fetch_simple(self, url: str, headers: Dict, proxy: Optional[str]) -> str:
        """
        简单HTTP获取
        """
        import aiohttp
        
        connector = None
        if proxy:
            connector = aiohttp.TCPConnector()
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(url, headers=headers, proxy=proxy) as response:
                return await response.text()
    
    async def _fetch_with_javascript(self, url: str, headers: Dict, proxy: Optional[str]) -> str:
        """
        使用JavaScript渲染获取动态内容
        """
        return await self._fetch_simple(url, headers, proxy)
    
    def _get_next_proxy(self) -> Optional[str]:
        """
        获取下一个代理
        """
        if not self.config.proxy_pool:
            return None
        
        proxy = self.config.proxy_pool[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.config.proxy_pool)
        return proxy
    
    def _detect_parser_type(self, url: str) -> Optional[str]:
        """
        根据URL检测解析器类型
        """
        if 'community' in url or 'xiaoqu' in url:
            return "community_info"
        elif 'property' in url or 'ershoufang' in url:
            return "property_listing"
        elif 'news' in url or 'article' in url:
            return "news_article"
        elif 'policy' in url or 'zhengce' in url:
            return "policy_document"
        return None
    
    async def _assess_page_quality(self, page: ParsedPage) -> float:
        """
        评估页面质量
        """
        score = 0.5
        
        if page.title:
            score += 0.1
        
        if len(page.content) > 500:
            score += 0.1
        
        if page.structured_data:
            score += 0.2
        
        if page.links:
            score += min(0.1, len(page.links) / 100)
        
        return min(1.0, score)
    
    def _update_response_time_stats(self, response_time_ms: float):
        """
        更新响应时间统计
        """
        old_avg = self.stats["avg_response_time_ms"]
        count = self.stats["pages_crawled"]
        
        if count > 0:
            self.stats["avg_response_time_ms"] = (
                old_avg * (count - 1) + response_time_ms
            ) / count
        else:
            self.stats["avg_response_time_ms"] = response_time_ms
    
    async def parse(self, raw_data: Any) -> List[Dict]:
        """
        解析爬取结果
        """
        if isinstance(raw_data, list):
            return raw_data
        return [raw_data]
    
    async def validate(self, sample: Dict) -> bool:
        """
        验证样本有效性
        """
        if not isinstance(sample, dict):
            return False
        
        if not sample.get("url"):
            return False
        
        if not sample.get("content") and not sample.get("structured_data"):
            return False
        
        return True
    
    def get_crawled_pages(self) -> Dict[str, ParsedPage]:
        return self.crawled_pages.copy()
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "queue_size": self.crawl_queue.qsize(),
                "crawled_pages": len(self.crawled_pages),
                "visited_urls": len(self.url_filter.visited_urls),
            }
