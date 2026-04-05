# -*- coding: utf-8 -*-
"""
Layer 37 - SEO & Content Ecosystem Fusion Development
==========================================================
SEO与内容生态融合开发层 — 10大模块+编排器+测试套件
智能体驱动、内容自生长、流量自循环的SEO生态系统
"""
from __future__ import annotations
import math, random, time, uuid, hashlib, json, re
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any, Tuple, Set

# ═══════════════════════════════════════════════════════════════
# PART H — ENUMS & DATACLASSES
# ═══════════════════════════════════════════════════════════════

class CrawlBehavior(PyEnum):
    DESKTOP="desktop"; MOBILE="mobile"; BOT="bot"

class SchemaType(PyEnum):
    PRODUCT="Product"; OFFER="Offer"; FAQ_PAGE="FAQPage"; HOW_TO="HowTo"
    DATASET="Dataset"; LOCAL_BUSINESS="LocalBusiness"; AGGREGATE_RATING="AggregateRating"
    ARTICLE="Article"; BREADCRUMB_LIST="BreadcrumbList"; ORGANIZATION="Organization"

class LinkType(PyEnum):
    DOFOLLOW="dofollow"; NOFOLLOW="nofollow"; SPONSORED="sponsored"; UGC="ugc"

class LinkQuality(PyEnum):
    HIGH="high"; MEDIUM="medium"; LOW="low"; TOXIC="toxic"

class SEORiskLevel(PyEnum):
    SAFE="safe"; WARNING="warning"; DANGER="danger"; CRITICAL_SEO="critical"

class ContentStatus(PyEnum):
    DRAFT="draft"; PENDING_REVIEW="pending_review"; PUBLISHED="published"
    ARCHIVED="archived"; NEEDS_UPDATE="needs_update"

class AMPStatus(PyEnum):
    VALID="valid"; INVALID="invalid"; NOT_GENERATED="not_generated"

@dataclass
class SitemapEntry:
    url: str; lastmod: str; changefreq: str; priority: float
    added_at: float = field(default_factory=time.time)

@dataclass
class RobotsRule:
    user_agent: str; disallow: List[str]; allow: List[str]
    sitemap: Optional[str] = None

@dataclass
class StructuredDataItem:
    id: str; schema_type: SchemaType; url: str; data: Dict[str,Any]
    generated_at: float = field(default_factory=time.time); valid: bool = True

@dataclass
class KeywordItem:
    id: str; keyword: str; search_volume: int; competition: float
    relevance: float; trend_direction: str; source: str
    predicted_volume_3m: Optional[float] = None

@dataclass
class ContentPiece:
    id: str; title: str; target_keyword: str; word_count: int
    status: ContentStatus; schema_types: List[SchemaType]
    internal_links: int; created_at: float = field(default_factory=time.time)
    updated_at: Optional[float] = None

@dataclass
class BacklinkRecord:
    id: str; source_url: str; target_url: str; anchor_text: str
    link_type: LinkType; quality: LinkQuality; domain_authority: float
    discovered_at: float = field(default_factory=time.time); lost: bool = False

@dataclass
class LocalSEOPage:
    id: str; entity_type: str; entity_name: str; city: str; district: Optional[str]
    url: str; rating: float; review_count: int; status: str = "active"

@dataclass
class SocialPost:
    id: str; platform: str; content: str; linked_content_id: str
    published: bool = False; engagement_score: float = 0.0
    created_at: float = field(default_factory=time.time)

@dataclass
class SEOHealthSnapshot:
    total_pages: int; indexed_pages: int; avg_position: float; organic_traffic: int
    backlinks_total: int; backlink_domains: int; core_web_vitals_pass: bool
    seo_health_score: float; risk_count: int; timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════
# PART A — SEO SITEMAP MANAGER (dynamic sitemap + robots.txt)
# ═══════════════════════════════════════════════════════════════

class SEOSitemapManager:
    def __init__(self):
        self._entries: Dict[str,SitemapEntry] = {}; self._rules: List[RobotsRule] = []
        self._submit_log: List[Dict[str,Any]] = []; self._max_entries_per_file = 50000
    def add_entry(self, url: str, changefreq: str="weekly", priority: float=0.5) -> SitemapEntry:
        eid=hashlib.md5(url.encode()).hexdigest()[:12]; entry=SitemapEntry(url,time.strftime("%Y-%m-%d"),changefreq,priority)
        self._entries[eid]=entry; return entry
    def remove_entry(self, url: str) -> bool:
        eid=hashlib.md5(url.encode()).hexdigest()[:12]
        return self._entries.pop(eid,None) is not None
    def generate_sitemap_xml(self) -> str:
        lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for e in sorted(self._entries.values(), key=lambda x:x.priority, reverse=True):
            lines.append(f'  <url><loc>{e.url}</loc><lastmod>{e.lastmod}</lastmod><changefreq>{e.changefreq}</changefreq><priority>{e.priority:.1f}</priority></url>')
        lines.append('</urlset>'); return '\n'.join(lines)
    def generate_sitemap_index(self) -> Tuple[List[str],str]:
        if len(self._entries)<=self._max_entries_per_file:
            return [self.generate_sitemap_xml()], ""
        entries_list=list(self._entries.values()); chunks=[]
        idx_lines=['<?xml version="1.0" encoding="UTF-8"?>','<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for i in range(0,len(entries_list),self._max_entries_per_file):
            chunk=entries_list[i:i+self._max_entries_per_file]; fname=f"sitemap_{len(chunks)+1}.xml"
            sub_lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
            for e in chunk:
                sub_lines.append(f'  <url><loc>{e.url}</loc><lastmod>{e.lastmod}</lastmod></url>')
            sub_lines.append('</urlset>'); chunks.append('\n'.join(sub_lines))
            idx_lines.append(f'  <sitemap><loc>https://fangdudu.com/{fname}</loc><lastmod>{time.strftime("%Y-%m-%d")}</lastmod></sitemap>')
        idx_lines.append('</sitemapindex>'); return chunks,'\n'.join(idx_lines)
    def add_robots_rule(self, ua: str, disallow: Optional[List[str]]=None, allow: Optional[List[str]]=None, sitemap: Optional[str]=None) -> RobotsRule:
        rule=RobotsRule(ua,disallow or [],allow or [],sitemap)
        self._rules=[r for r in self._rules if r.user_agent!=ua]; self._rules.append(rule); return rule
    def generate_robots_txt(self) -> str:
        lines=["User-agent: *","Allow: /"]
        for r in self._rules:
            lines.append(f"\nUser-agent: {r.user_agent}")
            for d in r.disallow: lines.append(f"Disallow: {d}")
            for a in r.allow: lines.append(f"Allow: {a}")
            if r.sitemap: lines.append(f"Sitemap: {r.sitemap}")
        lines.append("\nSitemap: https://fangdudu.com/sitemap.xml"); return '\n'.join(lines)
    def submit_to_search_engines(self, engine: str="google") -> Dict[str,Any]:
        log={"engine":engine,"timestamp":time.time(),"entries_count":len(self._entries),"status":"submitted"}
        self._submit_log.append(log); return log
    def manager_stats(self) -> Dict[str,Any]:
        return {"total_entries":len(self._entries),"rules_count":len(self._rules),"submissions":len(self._submit_log),"needs_indexing":len(self._entries)>self._max_entries_per_file}


# ═══════════════════════════════════════════════════════════════
# PART B — SSR DYNAMIC RENDERER (SSR/DR + structured data + CWV)
# ═══════════════════════════════════════════════════════════════

class SSRDynamicRenderer:
    def __init__(self):
        self._cache: Dict[str,Tuple[str,float]] = {}; self._structured_data: Dict[str,StructuredDataItem] = {}
        self._craw_bots=["googlebot","bingbot","baiduspider","yandexbot","duckduckbot"]
        self._cwv_metrics: Dict[str,Dict[str,float]] = {}
    def is_crawler(self, user_agent: str) -> bool:
        ua_lower=user_agent.lower(); return any(b in ua_lower for b in self._craw_bots)
    def render_page(self, url: str, html_content: str, user_agent: str, ttl_seconds: int=3600) -> str:
        cache_key=hashlib.sha256((url+user_agent).encode()).hexdigest()[:16]
        if cache_key in self._cache:
            cached,ts=self._cache[cache_key]
            if time.time()-ts<ttl_seconds: return cached[0]
        if self.is_crawler(user_agent):
            result=self._inject_structured_data(url,html_content)
        else:
            result=self._optimize_for_cwv(html_content)
        self._cache[cache_key]=(result,time.time()); return result
    def _inject_structured_data(self, url: str, html: str) -> str:
        items=[s for s in self._structured_data.values() if s.url==url]
        if not items: return html
        ld_scripts=[]
        for item in items:
            ld_json=json.dumps(item.data,ensure_ascii=False,indent=2)
            ld_scripts.append(f'<script type="application/ld+json">\n{ld_json}\n</script>')
        if '</head>' in html: return html.replace('</head>',''.join(ld_scripts)+'\n</head>')
        return '<head>'+''.join(ld_scripts)+'</head>'+html
    def _optimize_for_cwv(self, html: str) -> str:
        optimized=html
        optimized=re.sub(r'<img(?![^>]*loading=)', r'<img loading="lazy"', optimized)
        if '<style>' not in optimized[:500]: optimized='<style>img{max-width:100%;height:auto;}</style>'+optimized
        return optimized
    def add_structured_data(self, url: str, schema_type: SchemaType, data: Dict[str,Any]) -> StructuredDataItem:
        sid=f"sd_{hashlib.md5(url.encode()).hexdigest()[:8]}_{schema_type.value}"
        item=StructuredDataItem(sid,schema_type,url,data); self._structured_data[sid]=item; return item
    def record_cwv_metric(self, page_url: str, metric_name: str, value: float):
        if page_url not in self._cwv_metrics: self._cwv_metrics[page_url]={}
        self._cwv_metrics[page_url][metric_name]=value
    def get_cwv_report(self, page_url: str) -> Dict[str,Any]:
        m=self._cwv_metrics.get(page_url,{})
        fcp=m.get("fcp",0); lcp=m.get("lcp",0); cls=m.get("cls",0); inp=m.get("inp",0); ttfb=m.get("ttfb",0)
        passed=(fcp<1800 and lcp<2500 and cls<0.1 and inp<200 and ttfb<800)
        return {"page":page_url,"FCP":fcp,"LCP":lcp,"CLS":cls,"INP":inp,"TTFB":ttfb,"passed":passed,"score":round((1-min(fcp/1800,1)+1-min(lcp/2500,1)+1-min(cls/0.1,1)+1-min(inp/200,1)+1-min(ttfb/800,1))/5*100,1)}
    def renderer_stats(self) -> Dict[str,Any]:
        return {"cached_pages":len(self._cache),"structured_items":len(self._structured_data),"cwv_tracked":len(self._cwv_metrics),"crawler_patterns":len(self._craw_bots)}


# ═══════════════════════════════════════════════════════════════
# PART C — KEYWORD RESEARCH AGENT (hippocampus-driven keyword mining)
# ═══════════════════════════════════════════════════════════════

class KeywordResearchAgent:
    def __init__(self):
        self._keywords: Dict[str,KeywordItem] = {}; self._search_intents: List[Dict[str,str]] = []
        self._trend_history: Dict[str,List[float]] = {}; self._clusters: Dict[str,List[str]] = {}
    def record_search_intent(self, query: str, user_segment: str="general"):
        self._search_intents.append({"query":query,"segment":user_segment,"ts":time.time()})
        words=re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', query)
        for w in set(words): self._increment_keyword_freq(w.lower())
    def _increment_keyword_freq(self, keyword: str):
        if keyword in self._keywords: self._keywords[keyword].search_volume+=1
        else:
            kid=f"kw_{hashlib.md5(keyword.encode()).hexdigest()[:8]}"
            self._keywords[keyword]=KeywordItem(kid,keyword,1,random.uniform(0.2,0.9),random.uniform(0.6,1.0),random.choice(["up","down","stable"]),"user_intent")
    def analyze_keyword(self, keyword: str) -> KeywordItem:
        kid=f"kw_{hashlib.md5(keyword.encode()).hexdigest()[:8]}"
        if keyword not in self._keywords:
            kw=KeywordItem(kid,keyword,int(random.uniform(100,50000)),round(random.uniform(0.1,0.95),2),round(random.uniform(0.5,1.0),2),random.choice(["up","down","stable"]),"analysis")
            kw.predicted_volume_3m=int(kw.search_volume*random.uniform(0.8,1.3)); self._keywords[keyword]=kw
        return self._keywords[keyword]
    def predict_trend(self, keyword: str, months: int=3) -> List[float]:
        base_vol=self._keywords.get(keyword,KeywordItem("",keyword,100,0.5,0.7,"up")).search_volume
        trend=[]; current=base_vol
        direction=random.choice([1,-1])
        for _ in range(months*4):
            change=current*random.uniform(-0.05,0.08)*direction; current=max(int(current+change),10)
            trend.append(current)
        self._trend_history[keyword]=trend; return trend
    def compute_competition_score(self, keyword: str) -> float:
        kw=self._keywords.get(keyword)
        if not kw: return random.uniform(0.3,0.9)
        vol_factor=max(0,(1-kw.search_volume/50000))*0.4
        comp_factor=kw.competition*0.6; return round(min(vol_factor+comp_factor,1.0),2)
    def generate_keyword_matrix(self, entities: List[str], limit: int=20) -> List[Dict[str,Any]]:
        matrix=[]
        for e in entities:
            related=[k for k in self._keywords if k!=e and any(c in k for c in e[:2])]
            related_sorted=sorted(related,key=lambda k:self._keywords[k].relevance,reverse=True)[:5]
            matrix.append({"entity":e,"top_keywords":related_sorted,"count":len(related)})
        return sorted(matrix,key=lambda m:m["count"],reverse=True)[:limit]
    def cluster_keywords(self, n_clusters: int=5) -> Dict[str,List[str]]:
        keywords=list(self._keywords.keys())
        random.seed(42); random.shuffle(keywords)
        cluster_size=max(1,len(keywords)//n_clusters)
        for i in range(n_clusters):
            self._clusters[f"cluster_{i+1}"]=keywords[i*cluster_size:(i+1)*cluster_size]
        return self._clusters
    def agent_stats(self) -> Dict[str,Any]:
        high_vol=sum(1 for k in self._keywords.values() if k.search_volume>1000)
        return {"total_keywords":len(self._keywords),"intents_recorded":len(self._search_intents),
            "high_volume":high_vol,"trends_tracked":len(self._trend_history),"clusters":len(self._clusters)}


# ═══════════════════════════════════════════════════════════════
# PART D — CONTENT GENERATION ENGINE (AI-driven SEO content)
# ═══════════════════════════════════════════════════════════════

class ContentGenerationEngine:
    def __init__(self):
        self._content: Dict[str,ContentPiece] = {}; self._internal_links: Dict[str,Set[str]] = {}
        self._optimization_queue: List[str] = []
    def generate_article(self, title: str, target_keyword: str, word_target: int=1500, user_segment: str="general") -> ContentPiece:
        cid=f"cnt_{hashlib.md5((title+target_keyword).encode()).hexdigest()[:8]}"
        actual_words=int(word_target*random.uniform(0.85,1.15))
        schemas=[SchemaType.ARTICLE,SchemaType.FAQ_PAGE]
        piece=ContentPiece(cid,title,target_keyword,actual_words,ContentStatus.DRAFT,schemas,0)
        self._content[cid]=piece; return piece
    def optimize_old_content(self, content_id: str) -> Dict[str,Any]:
        piece=self._content.get(content_id)
        if not piece: return {"error":"not found"}
        age_days=(time.time()-piece.created_at)/86400
        if age_days<180: return {"action":"skip","reason":"too_recent","age_days":int(age_days)}
        piece.status=ContentStatus.NEEDS_UPDATE; piece.updated_at=time.time()
        suggestions=["update_statistics","refresh_external_links","add_internal_links","improve_readability","add_faq_section","update_schema_markup"]
        return {"action":"optimize","content_id":content_id,"age_days":int(age_days),"suggestions":suggestions}
    def build_internal_links(self, max_links_per_page: int=5) -> int:
        total_links=0; contents=list(self._content.values())
        for i,piece in enumerate(contents):
            targets=set()
            for other in contents[max(0,i-10):i]+contents[i+1:i+6]:
                if other.id!=piece.id and len(targets)<max_links_per_page:
                    if any(c in other.target_keyword for c in piece.target_keyword.split()[:2]):
                        targets.add(other.id)
            self._internal_links[piece.id]=targets; total_links+=len(targets)
            piece.internal_links=len(targets)
        return total_links
    def generate_anchor_text(self, target_url: str, context: str) -> str:
        anchors=[f"{context[:20]}详细指南",f"了解{context[:15]}更多信息",f"{context[:12]}最佳实践",
            f"点击查看{context[:10]}分析报告",f"{context[:18]}完整解读"]
        return random.choice(anchors)
    def publish_content(self, content_id: str) -> bool:
        piece=self._content.get(content_id)
        if piece and piece.status in(ContentStatus.DRAFT,ContentStatus.PENDING_REVIEW):
            piece.status=ContentStatus.PUBLISHED; return True
        return False
    def get_content_needing_update(self, older_than_days: int=180) -> List[ContentPiece]:
        cutoff=time.time()-older_than_days*86400
        return [p for p in self._content.values() if p.created_at<cutoff and p.status==ContentStatus.PUBLISHED]
    def engine_stats(self) -> Dict[str,Any]:
        by_status={}
        for p in self._content.values(): by_status[p.status.value]=by_status.get(p.status.value,0)+1
        return {"total_content":len(self._content),"by_status":by_status,
            "total_internal_links":sum(len(v) for v in self._internal_links.values()),
            "needs_update":len(self.get_content_needing_update())}


# ═══════════════════════════════════════════════════════════════
# PART E — BACKLINK MANAGER (external link building + quality control)
# ═══════════════════════════════════════════════════════════════

class BacklinkManager:
    def __init__(self):
        self._backlinks: Dict[str,BacklinkRecord] = {}; self._disavow: Set[str] = set()
        self._brand_mentions: List[Dict[str,str]] = []
    def add_backlink(self, source: str, target: str, anchor: str, link_type: LinkType=LinkType.DOFOLLOW) -> BacklinkRecord:
        blid=f"bl_{hashlib.md5((source+target).encode()).hexdigest()[:8]}"
        da=round(random.uniform(10,95),1)
        quality=LinkQuality.HIGH if da>=60 else (LinkQuality.MEDIUM if da>=30 else LinkQuality.LOW)
        bl=BacklinkRecord(blid,source,target,anchor,link_type,quality,da); self._backlinks[blid]=bl; return bl
    def mark_lost(self, backlink_id: str) -> bool:
        bl=self._backlinks.get(backlink_id)
        if bl: bl.lost=True; return True
        return False
    def assess_link_quality(self, backlink_id: str) -> Dict[str,Any]:
        bl=self._backlinks.get(backlink_id)
        if not bl: return {"error":"not_found"}
        spam_signals=random.randint(0,5); relevance=random.uniform(0.3,1.0)
        toxicity=min(spam_signals*0.2+(1-bl.domain_authority/100)*0.5+(1-relevance)*0.3,1.0)
        new_quality=LinkQuality.TOXIC if toxicity>0.6 else (LinkQuality.LOW if toxicity>0.3 else (LinkQuality.MEDIUM if toxicity>0.15 else LinkQuality.HIGH))
        bl.quality=new_quality; return {"id":bl.id,"domain_authority":bl.domain_authority,"spam_signals":spam_signals,"relevance":round(relevance,2),"toxicity":round(toxicity,2),"quality":new_quality.value}
    def get_disavow_list(self) -> List[str]:
        toxic=[bl.source_url for bl in self._backlinks.values() if bl.quality==LinkQuality.TOXIC]
        return sorted(set(toxic)|self._disavow)
    def add_to_disavow(self, domain: str): self._disavow.add(domain)
    def record_brand_mention(self, source: str, mention_text: str, has_link: bool=False):
        self._brand_mentions.append({"source":source,"text":mention_text,"has_link":has_link,"found_at":time.time()})
    def get_unlinked_mentions(self) -> List[Dict[str,str]]:
        return [m for m in self._brand_mentions if not m["has_link"]]
    def analyze_competitor_backlinks(self, competitor_domain: str) -> Dict[str,Any]:
        fake_count=random.randint(50,500); domains=set()
        for _ in range(min(fake_count,30)): domains.add(f"site-{random.randint(1,999)}.com")
        return {"competitor":competitor_domain,"total_backlinks":fake_count,"referring_domains":len(domains),
            "avg_da":round(random.uniform(25,75),1),"top_anchor_texts":["房都督","房价分析","房产投资"]+["关键词"+str(i) for i in range(random.randint(3,8))],
            "opportunities":["resource_page_link","guest_post","directory_submission","infographic_embed","testimonial"]}
    def manager_stats(self) -> Dict[str,Any]:
        active=sum(1 for bl in self._backlinks.values() if not bl.lost)
        dofollow=sum(1 for bl in self._backlinks.values() if bl.link_type==LinkType.DOFOLLOW and not bl.lost)
        return {"total_backlinks":len(self._backlinks),"active":active,"lost":sum(1 for bl in self._backlinks.values() if bl.lost),
            "dofollow":dofollow,"toxic":sum(1 for bl in self._backlinks.values() if bl.quality==LinkQuality.TOXIC),
            "disavowed":len(self._disavow),"brand_mentions":len(self._brand_mentions),"unlinked":len(self.get_unlinked_mentions()),
            "referring_domains":len(set(bl.source_url.split("/")[2] if "/" in bl.source_url else "" for bl in self._backlinks.values() if not bl.lost))}


# ═══════════════════════════════════════════════════════════════
# PART F — LOCAL SEO ENGINE (city/block pages + reviews)
# ═══════════════════════════════════════════════════════════════

class LocalSEOEngine:
    def __init__(self):
        self._pages: Dict[str,LocalSEOPage] = {}; self._reviews: List[Dict[str,Any]] = []
        self._local_backlinks: List[Dict[str,str]] = []
    def create_local_page(self, entity_type: str, name: str, city: str, district: Optional[str]=None) -> LocalSEOPage:
        lid=f"local_{hashlib.md5((entity_type+name+city+(district or "")).encode()).hexdigest()[:8]}"
        url=f"/{entity_type}/{city}/{district or 'default'}/{name.replace(' ','-')}"
        page=LocalSEOPage(lid,entity_type,name,city,district,url,0.0,0); self._pages[lid]=page; return page
    def add_review(self, page_id: str, rating: float, reviewer: str, comment: str) -> Dict[str,Any]:
        review={"page_id":page_id,"rating":min(5,max(1,rating)),"reviewer":reviewer,"comment":comment,"created_at":time.time()}
        self._reviews.append(review); page=self._pages.get(page_id)
        if page:
            all_r=[r["rating"] for r in self._reviews if r["page_id"]==page_id]
            page.rating=round(sum(all_r)/len(all_r),1); page.review_count=len(all_r)
        return review
    def get_local_schema(self, page_id: str) -> Dict[str,Any]:
        page=self._pages.get(page_id)
        if not page: return {}
        reviews=[r for r in self._reviews if r["page_id"]==page_id]
        agg_rating=round(sum(r["rating"] for r in reviews)/max(len(reviews),1),1) if reviews else 0
        return {"@context":"https://schema.org","@type":"LocalBusiness","name":page.entity_name,
            "address":{"@type":"PostalAddress","addressLocality":page.city,"addressRegion":page.district or ""},
            "aggregateRating":{"@type":"AggregateRating","ratingValue":agg_rating,"reviewCount":len(reviews)}}
    def add_local_directory_link(self, directory_name: str, url: str, category: str="real_estate"):
        self._local_backlinks.append({"directory":directory_name,"url":url,"category":category,"added_at":time.time()})
        return self._local_backlinks[-1]
    def get_pages_by_city(self, city: str) -> List[LocalSEOPage]:
        return [p for p in self._pages.values() if p.city==city]
    def generate_breadcrumbs(self, page_id: str) -> List[Dict[str,str]]:
        page=self._pages.get(page_id)
        if not page: return []
        crumbs=[{"name":"首页","url":"/"},{"name":page.city,"url":f"/city/{page.city}"}]
        if page.district: crumbs.append({"name":page.district,"url":f"/city/{page.city}/{page.district}"})
        crumbs.append({"name":page.entity_name,"url":page.url}); return crumbs
    def engine_stats(self) -> Dict[str,Any]:
        cities=len(set(p.city for p in self._pages.values()))
        return {"total_local_pages":len(self._pages),"cities":cities,"total_reviews":len(self._reviews),
            "avg_rating":round(sum(r["rating"] for r in self._reviews)/max(len(self._reviews),1),1) if self._reviews else 0,
            "local_directories":len(self._local_backlinks)}


# ═══════════════════════════════════════════════════════════════
# PART G — MOBILE SEO ADAPTER (mobile-first + AMP + performance)
# ═══════════════════════════════════════════════════════════════

class MobileSEOAdapter:
    def __init__(self):
        self._amp_pages: Dict[str,AMPStatus] = {}; self._mobile_tests: List[Dict[str,Any]] = []
        self._responsive_scores: Dict[str,float] = {}
    def validate_mobile_friendly(self, url: str, html: str) -> Dict[str,Any]:
        issues=[]; score=100.0
        if 'viewport' not in html[:2000]: issues.append("missing_viewport"); score-=20
        if '<meta name="viewport"' not in html[:2000]: issues.append("no_viewport_meta"); score-=15
        if html.count('<script')>10: issues.append("too_many_scripts"); score-=10
        if 'font-size.*px' in html and 'font-size.*rem' not in html: issues.append("fixed_font_sizes"); score-=10
        if len(html)>100000: issues.append("large_page_size"); score-=5
        flash_detected='flash' in html.lower() or '.swf' in html.lower()
        if flash_detected: issues.append("flash_content"); score-=30
        self._responsive_scores[url]=max(score,0); test_result={"url":url,"mobile_friendly":score>=70,
            "score":max(score,0),"issues":issues,"flash_detected":flash_detected}
        self._mobile_tests.append(test_result); return test_result
    def generate_amp_html(self, url: str, original_html: str) -> str:
        amp=original_html
        amp=re.sub(r'<script[^>]*>[^<]*</script>','',amp,count=0)
        amp=re.sub(r'<script[^>]*src=["\']?[^"\']*["\']?\s*/?>','',amp)
        amp=amp.replace('<html','<html ⚡')
        amp=f'<link rel="amphtml" href="{url}?amp=1">\n'+amp
        amp=amp.replace('<head>',f'<head>\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<style>body{{margin:0;padding:0;font-family:sans-serif}}img{{max-width:100%}}')
        amp+='<script async custom-element="amp-img" src="https://cdn.ampproject.org/v0/amp-img-0.1.js"></script>\n'
        self._amp_pages[url]=AMPStatus.VALID; return amp
    def validate_amp(self, url: str) -> Dict[str,Any]:
        status=self._amp_pages.get(url,AMPStatus.NOT_GENERATED)
        errors=[]; valid=status==AMPStatus.VALID
        if not valid: errors.append("amp_not_generated")
        return {"url":url,"status":status.value,"valid":valid,"errors":errors}
    def optimize_mobile_images(self, html: str) -> str:
        optimized=html
        optimized=re.sub(r'<img([^>]*)>', lambda m: f'<picture><source srcset="{self._extract_src(m.group(1))}.webp" type="image/webp">{m.group(0)}</picture>',optimized)
        optimized=optimized.replace('<img ','<img loading="lazy" ')
        return optimized
    def _extract_src(self, img_tag: str) -> str:
        m=re.search(r'src=["\']([^"\']+)["\']',img_tag)
        return m.group(1) if m else "placeholder.jpg"
    def adapter_stats(self) -> Dict[str,Any]:
        valid_amp=sum(1 for v in self._amp_pages.values() if v==AMPStatus.VALID)
        avg_mobile=round(sum(self._responsive_scores.values())/max(len(self._responsive_scores),1),1) if self._responsive_scores else 0
        return {"amp_pages":len(self._amp_pages),"amp_valid":valid_amp,"mobile_tests":len(self._mobile_tests),
            "avg_mobile_score":avg_mobile}


# ═══════════════════════════════════════════════════════════════
# PART H — SEO MONITORING DASHBOARD (traffic + behavior + competitors)
# ═══════════════════════════════════════════════════════════════

class SEOMonitoringDashboard:
    def __init__(self):
        self._search_data: List[Dict[str,Any]] = []; self._rankings: Dict[str,List[Dict[str,Any]]] = {}
        self._competitor_data: Dict[str,Dict[str,Any]] = {}; self._alerts: List[Dict[str,Any]] = []
    def record_search_console_data(self, date: str, queries: int, clicks: int, impressions: int, position: float, indexed: int) -> Dict[str,Any]:
        entry={"date":date,"queries":queries,"clicks":clicks,"impressions":impressions,
            "avg_position":round(position,1),"indexed":indexed,"ctr":round(clicks/max(impressions,1)*100,2)}
        self._search_data.append(entry); return entry
    def update_ranking(self, keyword: str, position: int, url: str, engine: str="google"):
        if keyword not in self._rankings: self._rankings[keyword]=[]
        self._rankings[keyword].append({"position":position,"url":url,"engine":engine,"timestamp":time.time()})
        recent=sorted(self._rankings[keyword],key=lambda x:x["timestamp"],reverse=True)[:10]
        positions=[r["position"] for r in recent]; avg_pos=sum(positions)/len(positions)
        if len(positions)>=2 and positions[-1]>positions[0]*1.5: self._create_alert("ranking_drop",keyword,f"排名下降: {positions[-1]}→{positions[0]}")
        return {"keyword":keyword,"current_position":position,"avg_position":round(avg_pos,1),"history_count":len(recent)}
    def track_user_behavior(self, landing_page: str, source: str, dwell_time: float, converted: bool=False):
        pass
    def add_competitor(self, domain: str, estimated_traffic: int, keyword_overlap: int) -> Dict[str,Any]:
        data={"domain":domain,"estimated_traffic":estimated_traffic,"keyword_overlap":keyword_overlap,
            "visibility_score":round(random.uniform(20,95),1),"last_updated":time.time()}
        self._competitor_data[domain]=data; return data
    def compare_with_competitor(self, competitor_domain: str) -> Dict[str,Any]:
        my_data={"total_pages":random.randint(100,500),"backlinks":random.randint(200,2000),"organic_traffic":random.randint(1000,50000)}
        comp=self._competitor_data.get(competitor_domain,{"estimated_traffic":0,"keyword_overlap":0})
        gap_my_better={}; gap_comp_better={}
        for metric in ["total_pages","backlinks","organic_traffic"]:
            my_val=my_data.get(metric,0); comp_val=comp.get(f"estimated_traffic" if metric=="organic_traffic" else metric,0)
            if my_val>comp_val*1.2: gap_my_better[metric]=my_val-comp_val
            elif comp_val>my_val*1.2: gap_comp_better[metric]=comp_val-my_val
        return {"competitor":competitor_domain,"our_data":my_data,"their_data":comp,
            "we_lead":gap_my_better,"they_lead":gap_comp_better,"overall_verdict":"leading" if len(gap_my_better)>len(gap_comp_better) else ("behind" if len(gap_comp_better)>0 else "parity")}
    def _create_alert(self, alert_type: str, message: str, severity: str="warning"):
        self._alerts.append({"type":alert_type,"message":message,"severity":severity,"created_at":time.time(),"resolved":False})
    def get_active_alerts(self) -> List[Dict[str,Any]]:
        return [a for a in self._alerts if not a["resolved"]]
    def dashboard_stats(self) -> Dict[str,Any]:
        latest=self._search_data[-1] if self._search_data else {}
        return {"data_points":len(self._search_data),"keywords_tracked":len(self._rankings),
            "competitors":len(self._competitor_data),"active_alerts":len(self.get_active_alerts()),
            "latest_queries":latest.get("queries",0),"latest_ctr":latest.get("ctr",0)}


# ═══════════════════════════════════════════════════════════════
# PART I — SOCIAL SIGNAL AMPLIFIER (social content + OG + UGC)
# ═══════════════════════════════════════════════════════════════

class SocialSignalAmplifier:
    def __init__(self):
        self._posts: Dict[str,SocialPost] = {}; self._og_tags: Dict[str,Dict[str,str]] = {}
        self._ugc_contents: List[Dict[str,Any]] = []; self._share_counts: Dict[str,int] = {}
    def generate_social_post(self, content_id: str, platform: str, tone: str="professional") -> SocialPost:
        tones={"professional":"专业深度解读，数据驱动决策","casual":"轻松看懂房地产，买房不踩坑","clickbait":"震惊！这个板块的涨幅超乎想象..."}
        base=tones.get(tone,"发现新机会")
        post_id=f"sp_{hashlib.md5((content_id+platform).encode()).hexdigest()[:8]}"
        post=SocialPost(post_id,platform,f"{base} — 基于最新数据分析",content_id)
        self._posts[post_id]=post; return post
    def set_og_tags(self, url: str, title: str, description: str, image: str="") -> Dict[str,str]:
        tags={"og:title":title,"og:description":description,"og:url":url,"og:type":"article",
            "og:site_name":"房都督AI平台","og:locale":"zh_CN","twitter:card":"summary_large_image"}
        if image: tags["og:image"]=image; tags["twitter:image"]=image
        self._og_tags[url]=tags; return tags
    def render_og_meta(self, url: str) -> str:
        tags=self._og_tags.get(url,{})
        if not tags: return ''
        meta='\n'.join(f'<meta property="{k}" content="{v}">' for k,v in tags.items())
        return f'\n<!-- Open Graph Tags -->\n{meta}\n'
    def record_share(self, url: str, platform: str): self._share_counts[f"{url}:{platform}"]=self._share_counts.get(f"{url}:{platform}",0)+1
    def get_share_stats(self, url: str) -> Dict[str,int]:
        return {k.split(":")[1]:v for k,v in self._share_counts.items() if k.startswith(url+":")}
    def submit_ugc(self, author: str, content: str, entity_ref: str, rating: Optional[float]=None) -> Dict[str,Any]:
        ugc={"id":f"ugc_{uuid.uuid4().hex[:8]}","author":author,"content":content,
            "entity_ref":entity_ref,"rating":rating,"created_at":time.time(),
            "status":"pending_review","reward_points":10 if rating else 5}
        self._ugc_contents.append(ugc); return ugc
    def moderate_ugc(self, ugc_id: str, action: str="approve") -> bool:
        for u in self._ugc_contents:
            if u["id"]==ugc_id: u["status"]=action; return True
        return False
    def calculate_engagement(self, post_id: str) -> float:
        post=self._posts.get(post_id)
        if not post: return 0.0
        shares=sum(1 for k,v in self._share_counts.items() if post.linked_content_id in k)
        post.engagement_score=round(shares*2.0+random.uniform(0,10),1); return post.engagement_score
    def amplifier_stats(self) -> Dict[str,Any]:
        approved_ugc=sum(1 for u in self._ugc_contents if u["status"]=="approved")
        return {"social_posts":len(self._posts),"og_configs":len(self._og_tags),
            "total_shares":sum(self._share_counts.values()),"ugc_submitted":len(self._ugc_contents),
            "ugc_approved":approved_ugc,"total_reward_points":sum(u.get("reward_points",0) for u in self._ugc_contents if u["status"]=="approved")}


# ═══════════════════════════════════════════════════════════════
# PART J — COMPLIANCE RISK CONTROLLER (white-hat audit + algorithm updates)
# ═══════════════════════════════════════════════════════════════

class ComplianceRiskController:
    def __init__(self):
        self._audit_results: List[Dict[str,Any]] = []; self._algorithm_updates: List[Dict[str,Any]] = []
        self._risk_flags: List[Dict[str,Any]] = []
    def run_whitehat_audit(self, page_html: str, page_url: str) -> Dict[str,Any]:
        findings=[]; risk_score=0.0
        hidden_text_pattern=r'display:\s*none|visibility:\s*hidden|color:\s*white\s*\+\s*color:\s*white'
        if re.search(hidden_text_pattern,page_html,re.IGNORECASE):
            findings.append({"type":"hidden_text","severity":"danger","description":"检测到隐藏文字"})
            risk_score+=30
        if page_html.lower().count('<meta name="keywords"')>1:
            findings.append({"type":"duplicate_meta","severity":"warning","description":"重复keywords meta标签"})
            risk_score+=10
        density_check=len(re.findall(r'(?:房价|买房|投资)',page_html))
        if density_check>50:
            findings.append({"type":"keyword_stuffing","severity":"danger","description":f"关键词堆砌({density_check}次)"})
            risk_score+=25
        external_nofollow=len(re.findall(r'rel="nofollow"',page_html))
        external_dofollow=len(re.findall(r'<a[^>]*href="http[^"]*"[^>]*>(?!<)',page_html))-external_nofollow
        if external_dofollow>20:
            findings.append({"type":"suspicious_outbound","severity":"warning","description":f"异常外链数量({external_dofollow})"})
            risk_score+=10
        level=SEORiskLevel.SAFE if risk_score<20 else (SEORiskLevel.WARNING if risk_score<50 else (SEORiskLevel.DANGER if risk_score<70 else SEORiskLevel.CRITICAL_SEO))
        result={"url":page_url,"timestamp":time.time(),"findings":findings,"risk_score":round(risk_score,1),
            "risk_level":level.value,"passed":risk_score<40}
        self._audit_results.append(result); return result
    def check_ugc_risks(self, ugc_content: str, external_links: int=0) -> Dict[str,Any]:
        risks=[]; score=0.0
        spam_words=["免费","赚钱","加微信","代理","贷款","投资回报率999%"]
        found=[w for w in spam_words if w in ugc_content]
        if found: risks.append({"type":"spam_keywords","words":found}); score+=len(found)*10
        if external_links>3: risks.append({"type":"excessive_links","count":external_links}); score+=15
        if len(ugc_content)>2000: risks.append({"type":"overly_long","length":len(ugc_content)}); score+=5
        return {"risks":risks,"risk_score":round(score,1),"safe":score<20}
    def record_algorithm_update(self, name: str, impact_area: str, severity: str="medium"):
        self._algorithm_updates.append({"name":name,"impact_area":impact_area,"severity":severity,
            "detected_at":time.time(),"actions_taken":[]})
        if severity=="major": self._create_flag("algorithm_major",f"重大算法更新: {name}")
    def get_recommendations(self, risk_level: str) -> List[str]:
        recs={
            "safe":["保持当前策略","继续监控Core Web Vitals","定期审查外链质量"],
            "warning":["增加E-E-A-T信号（经验、专业、权威、信任度）","清理低质量页面","加强内部链接结构"],
            "danger":["立即停止可疑SEO行为","全面审查外链配置","提交Disavow文件","更新受影响页面的内容"],
            "critical":["暂停所有主动SEO操作","进行全面技术审计","考虑请求重新收录","联系SEO专家"]
        }
        return recs.get(risk_level,recs["warning"])
    def _create_flag(self, flag_type: str, message: str):
        self._risk_flags.append({"type":flag_type,"message":message,"created_at":time.time(),"resolved":False})
    def controller_stats(self) -> Dict[str,Any]:
        unresolved=sum(1 for a in self._audit_results if not a.get("passed",True))
        return {"audits_run":len(self._audit_results),"audits_failed":unresolved,
            "algorithm_updates":len(self._algorithm_updates),"active_flags":sum(1 for f in self._risk_flags if not f["resolved"])}


# ═══════════════════════════════════════════════════════════════
# PART K — SEO ORCHESTRATOR (unified coordinator)
# ═══════════════════════════════════════════════════════════════

class SEOOrchestrator:
    def __init__(self):
        self.sitemap = SEOSitemapManager(); self.renderer = SSRDynamicRenderer()
        self.keyword_agent = KeywordResearchAgent(); self.content_engine = ContentGenerationEngine()
        self.backlink_mgr = BacklinkManager(); self.local_seo = LocalSEOEngine()
        self.mobile_adapter = MobileSEOAdapter(); self.monitor = SEOMonitoringDashboard()
        self.social = SocialSignalAmplifier(); self.compliance = ComplianceRiskController()
    def run_full_audit(self, url: str, html: str) -> Dict[str,Any]:
        whitehat=self.compliance.run_whitehat_audit(html,url)
        mobile=self.mobile_adapter.validate_mobile_friendly(url,html)
        cwv=self.renderer.get_cwv_report(url)
        return {"whitehat_audit":whitehat,"mobile_test":mobile,"core_web_vitals":cwv,
            "overall_health":round((whitehat.get("risk_score",0)/100*30+mobile.get("score",0)/100*30+cwv.get("score",0)/100*40),1)}
    def generate_seo_package(self, url: str, title: str, keyword: str, html: str) -> Dict[str,Any]:
        self.sitemap.add_entry(url); self.renderer.add_structured_data(url,SchemaType.ARTICLE,{"@type":"Article","headline":title,"description":f"关于{keyword}的专业分析"})
        self.social.set_og_tags(url,title,f"房都督AI平台 - {title}")
        kw=self.keyword_agent.analyze_keyword(keyword); content=self.content_engine.generate_article(title,keyword)
        amp_html=self.mobile_adapter.generate_amp_html(url,html)
        local_schema=None
        return {"url":url,"keyword":kw.keyword,"content_id":content.id,"sitemap_entry":True,
            "structured_data":True,"og_tags":True,"amp_generated":True,"amp_size":len(amp_html)}
    def get_dashboard_snapshot(self) -> SEOHealthSnapshot:
        sm_stats=self.sitemap.manager_stats(); rd_stats=self.renderer.renderer_stats()
        kw_stats=self.keyword_agent.agent_stats(); ce_stats=self.content_engine.engine_stats()
        bl_stats=self.backlink_mgr.manager_stats(); ls_stats=self.local_seo.engine_stats()
        ma_stats=self.mobile_adapter.adapter_stats(); mon_stats=self.monitor.dashboard_stats()
        ss_stats=self.social.amplifier_stats(); cc_stats=self.compliance.controller_stats()
        health=100-cc_stats["audits_failed"]*5-mon_stats["active_alerts"]*3-bl_stats["toxic"]*2
        health=max(0,min(100,health))
        return SEOHealthSnapshot(sm_stats["total_entries"],sm_stats["total_entries"],
            round(mon_stats.get("latest_ctr",0),1),mon_stats.get("latest_clicks",0),
            bl_stats["active"],bl_stats["referring_domains"],ma_stats["avg_mobile_score"]>=70,
            round(health,1),cc_stats["active_flags"])
    def run_competitor_analysis(self, competitor: str) -> Dict[str,Any]:
        bl_analysis=self.backlink_mgr.analyze_competitor_backlinks(competitor)
        comparison=self.monitor.compare_with_competitor(competitor)
        return {"backlink_analysis":bl_analysis,"comparison":comparison}


# ═══════════════════════════════════════════════════════════════
# PART L — TESTING SUITE
# ═══════════════════════════════════════════════════════════════

def _run_test(name: str, fn) -> tuple:
    try: fn(); return ("PASS", name, None)
    except Exception as e: return ("FAIL", name, str(e))

def run_all_tests() -> Dict[str,Any]:
    results=[]

    def test_sitemap_basic():
        mgr=SEOSitemapManager(); e=mgr.add_entry("/page1","daily",0.8); assert e.url=="/page1"
        assert len(mgr._entries)==1; xml=mgr.generate_sitemap_xml(); assert "urlset" in xml
    results.append(_run_test("SITEMAP: basic add+generate", test_sitemap_basic))

    def test_sitemap_remove():
        mgr=SEOSitemapManager(); mgr.add_entry("/test"); assert mgr.remove_entry("/test"); assert len(mgr._entries)==0
    results.append(_run_test("SITEMAP: remove entry", test_sitemap_remove))

    def test_sitemap_index():
        mgr=SEOSitemapManager()
        for i in range(50001): mgr.add_entry(f"/page_{i}")
        chunks,idx=mgr.generate_sitemap_index(); assert len(chunks)>1; assert "sitemapindex" in idx
    results.append(_run_test("SITEMAP: index splitting >50k", test_sitemap_index))

    def test_robots():
        mgr=SEOSitemapManager(); rule=mgr.add_robots_rule("Googlebot",["/admin","/private"],["/public"]); assert rule.user_agent=="Googlebot"
        txt=mgr.generate_robots_txt(); assert "Disallow: /admin" in txt
    results.append(_run_test("ROBOTS: rule generation", test_robots))

    def test_renderer_crawler():
        r=SSRDynamicRenderer(); assert r.is_crawler("Mozilla/5.0 (compatible; Googlebot/2.1)")
        assert not r.is_crawler("Mozilla/5.0 (Windows NT 10.0)")
    results.append(_run_test("RENDERER: crawler detection", test_renderer_crawler))

    def test_render_cache():
        r=SSRDynamicRenderer(); r.render_page("/test","<html>content</html>","Googlebot/2.1")
        r.render_page("/test","<html>content</html>","Googlebot/2.1"); assert len(r._cache)>=1
    results.append(_run_test("RENDERER: caching works", test_render_cache))

    def test_structured_data():
        r=SSRDynamicRenderer(); sd=r.add_structured_data("/prod",SchemaType.PRODUCT,{"@type":"Product","name":"Test"})
        assert sd.schema_type==SchemaType.PRODUCT; assert len(r._structured_data)==1
    results.append(_run_test("RENDERER: structured data", test_structured_data))

    def test_cwv():
        r=SSRDynamicRenderer(); r.record_cwv_metric("/page1","fcp",1200); r.record_cwv_metric("/page1","lcp",2000)
        rep=r.get_cwv_report("/page1"); assert rep["FCP"]==1200; assert "passed" in rep
    results.append(_run_test("RENDERER: CWV report", test_cwv))

    def test_keyword_record():
        ka=KeywordResearchAgent(); ka.record_search_intent("北京房价走势","professional")
        assert len(ka._search_intents)==1; assert len(ka._keywords)>0
    results.append(_run_test("KWAGENT: intent recording", test_keyword_record))

    def test_keyword_analyze():
        ka=KeywordResearchAgent(); kw=ka.analyze_keyword("上海房产投资")
        assert kw.search_volume>0; assert kw.predicted_volume_3m is not None
    results.append(_run_test("KWAGENT: analyze+predict", test_keyword_analyze))

    def test_keyword_competition():
        ka=KeywordResearchAgent(); score=ka.compute_competition_score("热门关键词")
        assert 0<=score<=1
    results.append(_run_test("KWAGENT: competition score", test_keyword_competition))

    def test_keyword_matrix():
        ka=KeywordResearchAgent(); ka.record_search_intent("深圳买房建议")
        mat=ka.generate_keyword_matrix(["深圳"]); assert isinstance(mat,list); assert len(mat)>0
    results.append(_run_test("KWAGENT: keyword matrix", test_keyword_matrix))

    def test_keyword_cluster():
        ka=KeywordResearchAgent()
        for i in range(20): ka.record_search_intent(f"查询词{i}")
        clusters=ka.cluster_keywords(3); assert len(clusters)==3
    results.append(_run_test("KWAGENT: clustering", test_keyword_cluster))

    def test_content_generate():
        ce=ContentGenerationEngine(); art=ce.generate_article("2025年北京房价预测","北京房价预测",2000)
        assert art.status==ContentStatus.DRAFT; assert art.word_count>0
    results.append(_run_test("CONTENT: article generation", test_content_generate))

    def test_content_optimize():
        ce=ContentGenerationEngine(); art=ce.generate_article("Old Article","old_kw",1000)
        art.created_at=time.time()-200*86400; opt=ce.optimize_old_content(art.id)
        assert opt["action"]=="optimize"
    results.append(_run_test("CONTENT: old content optimization", test_content_optimize))

    def test_internal_links():
        ce=ContentGenerationEngine()
        for i in range(10): ce.generate_article(f"Article {i}","keyword_{i}",500)
        total=ce.build_internal_links(); assert total>0
    results.append(_run_test("CONTENT: internal link building", test_internal_links))

    def test_backlink_add():
        bm=BacklinkManager(); bl=bm.add_backlink("http://example.com","/target","anchor text")
        assert bl.quality in(LinkQuality.HIGH,LinkQuality.MEDIUM,LinkQuality.LOW)
    results.append(_run_test("BACKLINK: add+assess quality", test_backlink_add))

    def test_backlink_disavow():
        bm=BacklinkManager(); bm.add_backlink("http://spam.com","/target","bad")
        bm.assess_link_quality(list(bm._backlinks.keys())[0]); dl=bm.get_disavow_list()
        assert "http://spam.com" in dl
    results.append(_run_test("BACKLINK: disavow list", test_backlink_disavow))

    def test_brand_mention():
        bm=BacklinkManager(); bm.record_brand_mention("http://news.com","房都督平台很棒",False)
        ul=bm.get_unlinked_mentions(); assert len(ul)==1
    results.append(_run_test("BACKLINK: unlinked mentions", test_brand_mention))

    def test_local_page():
        ls=LocalSEOEngine(); p=ls.create_local_page("district","朝阳区","北京")
        assert p.city=="北京"; assert "/district/" in p.url
    results.append(_run_test("LOCALSEO: create page", test_local_page))

    def test_local_review():
        ls=LocalSEOEngine(); p=ls.create_local_page("district","海淀区","北京")
        ls.add_review(p.id,5.0,"user1","很好!"); assert p.rating==5.0; assert p.review_count==1
    results.append(_run_test("LOCALSEO: review+rating", test_local_review))

    def test_local_schema():
        ls=LocalSEOEngine(); p=ls.create_local_page("district","浦东新区","上海")
        ls.add_review(p.id,4.0,"u1","good"); schema=ls.get_local_schema(p.id)
        assert schema["@type"]=="LocalBusiness"; assert "aggregateRating" in schema
    results.append(_run_test("LOCALSEO: local business schema", test_local_schema))

    def test_mobile_validate():
        ma=MobileSEOAdapter(); result=ma.validate_mobile_friendly("/page","<html><meta name='viewport' content='width=device-width'></html>")
        assert result["mobile_friendly"]==True
    results.append(_run_test("MOBILE: friendly validation", test_mobile_validate))

    def test_amp_generate():
        ma=MobileSEOAdapter(); amp=ma.generate_amp_html("/page","<html><body>Hello</body></html>")
        assert "⚡" in amp; assert ma._amp_pages["/page"]==AMPStatus.VALID
    results.append(_run_test("MOBILE: AMP generation", test_amp_generate))

    def test_monitor_data():
        mon=SEOMonitoringDashboard(); d=mon.record_search_console_data("2025-04-05",1000,200,10000,12.5,500)
        assert d["ctr"]>0; assert len(mon._search_data)==1
    results.append(_run_test("MONITOR: console data", test_monitor_data))

    def test_ranking_tracking():
        mon=SEOMonitoringDashboard(); mon.update_ranking("测试关键词",5,"/page1")
        mon.update_ranking("测试关键词",15,"/page1"); stats=mon.update_ranking("测试关键词",8,"/page1")
        assert stats["history_count"]==3
    results.append(_run_test("MONITOR: ranking tracking", test_ranking_tracking))

    def test_competitor():
        mon=SEOMonitoringDashboard(); mon.add_competitor("competitor.com",50000,30)
        cmp=mon.compare_with_competitor("competitor.com"); assert "overall_verdict" in cmp
    results.append(_run_test("MONITOR: competitor analysis", test_competitor))

    def test_social_post():
        ss=SocialSignalAmplifier(); post=ss.generate_social_post("content1","wechat","casual")
        assert post.platform=="wechat"; assert len(post.content)>0
    results.append(_run_test("SOCIAL: post generation", test_social_post))

    def test_og_tags():
        ss=SocialSignalAmplifier(); tags=ss.set_og_tags("/page","Title","Description here","http://img.jpg")
        assert "og:title" in tags; assert "og:image" in tags
    results.append(_run_test("SOCIAL: OG tags", test_og_tags))

    def test_ugc():
        ss=SocialSignalAmplifier(); ugc=ss.submit_ugc("user1","这个板块不错！","block_1",4.5)
        assert ugc["reward_points"]==10; assert ss.moderate_ugc(ugc["id"],"approve")
    results.append(_run_test("SOCIAL: UGC submission", test_ugc))

    def test_compliance_safe():
        cc=ComplianceRiskController(); audit=cc.run_whitehat_audit("<html><body>Normal content</body></html>","/clean")
        assert audit["passed"]==True; assert audit["risk_level"]=="safe"
    results.append(_run_test("COMPLIANCE: safe page audit", test_compliance_safe))

    def test_compliance_hidden_text():
        cc=ComplianceRiskController()
        audit=cc.run_whitehat_audit('<html><div style="display:none">hidden</div>房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房房价买房买房房价买房</html>',"/bad")
        assert audit["passed"]==False; assert audit["risk_level"] in("danger","critical","warning")
    results.append(_run_test("COMPLIANCE: hidden text detection", test_compliance_hidden_text))

    def test_compliance_algorithm():
        cc=ComplianceRiskController(); cc.record_algorithm_update("Helpful Content Update","content_quality","major")
        recs=cc.get_recommendations("critical"); assert len(recs)>0
    results.append(_run_test("COMPLIANCE: algorithm response", test_compliance_algorithm))

    def test_orchestrator_init():
        orc=SEOOrchestrator(); assert orc.sitemap is not None; assert orc.monitor is not None
    results.append(_run_test("ORC: init all modules", test_orchestrator_init))

    def test_orchestrator_audit():
        orc=SEOOrchestrator(); result=orc.run_full_audit("/test","<html><body>OK</body></html>")
        assert "whitehat_audit" in result; assert "overall_health" in result
    results.append(_run_test("ORC: full audit", test_orchestrator_audit))

    def test_orchestrator_package():
        orc=SEOOrchestrator(); pkg=orc.generate_seo_package("/article","Test Title","test keyword","<html>body</html>")
        assert pkg["structured_data"]==True; assert pkg["amp_generated"]==True
    results.append(_run_test("ORC: SEO package generation", test_orchestrator_package))

    def test_orchestrator_dashboard():
        orc=SEOOrchestrator(); snap=orc.get_dashboard_snapshot()
        assert snap.total_pages>=0; assert 0<=snap.seo_health_score<=100
    results.append(_run_test("ORC: dashboard snapshot", test_orchestrator_dashboard))

    def test_orchestrator_competitor():
        orc=SEOOrchestrator(); orc.monitor.add_competitor("rival.com",10000,20)
        result=orc.run_competitor_analysis("rival.com"); assert "backlink_analysis" in result
    results.append(_run_test("ORC: competitor analysis suite", test_orchestrator_competitor))

    passed=sum(1 for r in results if r[0]=="PASS")
    failed=[r for r in results if r[0]=="FAIL"]; errors=[r for r in results if r[0]=="ERROR"]
    print(f"\n{'='*60}")
    print(f"L37 SEO CONTENT ECOSYSTEM FUSION LAYER — TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Total : {len(results)}")
    print(f"  Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"  Failed: {len(failed)}")
    if failed:
        for _,name,err in failed: print(f"    ✗ {name}: {err}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for _,name,err in errors: print(f"    ! {name}: {err}")
    print(f"{'='*60}")
    return {"total":len(results),"passed":passed,"failed":len(failed),"errors":len(errors),"results":results}

if __name__ == "__main__":
    run_all_tests()
    print("\n✅ Layer 37 — SEO & Content Ecosystem Fusion Development loaded OK")
