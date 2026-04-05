import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_URL = 'https://www.fangtanai.com';

const staticPages = [
  { path: '/', priority: 1.0, changefreq: 'daily' },
  { path: '/about', priority: 0.8, changefreq: 'monthly' },
  { path: '/help', priority: 0.7, changefreq: 'weekly' },
  { path: '/contact', priority: 0.6, changefreq: 'monthly' },
  { path: '/privacy', priority: 0.3, changefreq: 'yearly' },
  { path: '/terms', priority: 0.3, changefreq: 'yearly' },
  { path: '/login', priority: 0.5, changefreq: 'monthly' },
  { path: '/register', priority: 0.5, changefreq: 'monthly' },
  { path: '/property-analysis', priority: 0.9, changefreq: 'daily' },
  { path: '/report', priority: 0.8, changefreq: 'daily' },
];

function generateSitemap() {
  const today = new Date().toISOString().split('T')[0];

  const urlset = staticPages.map(page => `  <url>
    <loc>${SITE_URL}${page.path}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`).join('\n');

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlset}
</urlset>`;

  const publicDir = path.join(__dirname, '..', 'public');
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  fs.writeFileSync(path.join(publicDir, 'sitemap.xml'), sitemap);
  console.log('✅ sitemap.xml generated successfully');
}

generateSitemap();
