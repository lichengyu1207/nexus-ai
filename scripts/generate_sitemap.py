"""
SEO站点地图生成脚本
生成小区知识库和文章的sitemap.xml
"""
import asyncio
import os
from datetime import datetime
from backend.database_pg import get_db

SITEMAP_DIR = "public/sitemaps"
BASE_URL = os.getenv("BASE_URL", "https://fangdudu.com")


async def generate_sitemaps():
    """生成站点地图"""
    print("=" * 60)
    print("SEO站点地图生成")
    print("=" * 60)
    
    os.makedirs(SITEMAP_DIR, exist_ok=True)
    
    async with get_db() as db:
        print("\n1. 生成小区页面站点地图...")
        communities = await db.fetch("""
            SELECT c.id, c.name, c.last_updated, a.id as article_id, a.slug, a.updated_at as article_updated
            FROM communities c
            LEFT JOIN community_articles a ON c.id = a.community_id AND a.status = 'published'
            ORDER BY c.last_updated DESC NULLS LAST
        """)
        
        community_urls = []
        article_urls = []
        
        for row in communities:
            community_urls.append({
                "loc": f"{BASE_URL}/communities/{row['id']}",
                "lastmod": row['last_updated'] or row.get('created_at'),
                "changefreq": "weekly",
                "priority": "0.7"
            })
            
            if row['article_id']:
                article_url = row['slug'] if row['slug'] else row['article_id']
                article_urls.append({
                    "loc": f"{BASE_URL}/community/article/{article_url}",
                    "lastmod": row['article_updated'] or row['last_updated'],
                    "changefreq": "monthly",
                    "priority": "0.8"
                })
        
        print(f"   找到 {len(community_urls)} 个小区页面")
        print(f"   找到 {len(article_urls)} 个文章页面")
        
        print("\n2. 生成城市页面站点地图...")
        cities = await db.fetch("""
            SELECT id, city_name FROM city_configs ORDER BY sort_order
        """)
        
        city_urls = []
        for city in cities:
            city_urls.append({
                "loc": f"{BASE_URL}/communities?city={city['city_name']}",
                "changefreq": "daily",
                "priority": "0.9"
            })
        
        print(f"   找到 {len(city_urls)} 个城市页面")
        
        print("\n3. 写入站点地图文件...")
        
        def format_date(dt):
            if dt is None:
                return datetime.now().strftime("%Y-%m-%d")
            if isinstance(dt, datetime):
                return dt.strftime("%Y-%m-%d")
            return str(dt)[:10]
        
        def generate_sitemap_xml(urls: list, filename: str):
            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
            for url in urls:
                xml_content += f'''  <url>
    <loc>{url['loc']}</loc>
    <lastmod>{format_date(url.get('lastmod'))}</lastmod>
    <changefreq>{url.get('changefreq', 'weekly')}</changefreq>
    <priority>{url.get('priority', '0.5')}</priority>
  </url>
'''
            
            xml_content += '</urlset>'
            
            filepath = os.path.join(SITEMAP_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            return filepath
        
        community_file = generate_sitemap_xml(community_urls, 'sitemap_communities.xml')
        print(f"   小区站点地图: {community_file}")
        
        article_file = generate_sitemap_xml(article_urls, 'sitemap_articles.xml')
        print(f"   文章站点地图: {article_file}")
        
        city_file = generate_sitemap_xml(city_urls, 'sitemap_cities.xml')
        print(f"   城市站点地图: {city_file}")
        
        print("\n4. 生成站点地图索引文件...")
        sitemap_index = '''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
        sitemap_files = [
            ('sitemap_communities.xml', len(community_urls)),
            ('sitemap_articles.xml', len(article_urls)),
            ('sitemap_cities.xml', len(city_urls)),
        ]
        
        for filename, count in sitemap_files:
            sitemap_index += f'''  <sitemap>
    <loc>{BASE_URL}/sitemaps/{filename}</loc>
    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
  </sitemap>
'''
        
        sitemap_index += '</sitemapindex>'
        
        index_file = os.path.join(SITEMAP_DIR, 'sitemap.xml')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(sitemap_index)
        
        print(f"   站点地图索引: {index_file}")
        
        print("\n5. 生成 robots.txt...")
        robots_content = f'''User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/

Sitemap: {BASE_URL}/sitemaps/sitemap.xml
'''
        
        robots_file = "public/robots.txt"
        with open(robots_file, 'w', encoding='utf-8') as f:
            f.write(robots_content)
        
        print(f"   robots.txt: {robots_file}")
        
        print("\n" + "=" * 60)
        print("站点地图生成完成！")
        print("=" * 60)
        print(f"\n统计信息：")
        print(f"  - 小区页面: {len(community_urls)}")
        print(f"  - 文章页面: {len(article_urls)}")
        print(f"  - 城市页面: {len(city_urls)}")
        print(f"  - 总计: {len(community_urls) + len(article_urls) + len(city_urls)}")


if __name__ == "__main__":
    asyncio.run(generate_sitemaps())
