import React from 'react';
import { Link } from 'react-router-dom';

const cities = [
  { id: 'shenzhen', name: '深圳', pinyin: 'shenzhen' },
  { id: 'shanghai', name: '上海', pinyin: 'shanghai' },
  { id: 'beijing', name: '北京', pinyin: 'beijing' },
  { id: 'guangzhou', name: '广州', pinyin: 'guangzhou' },
  { id: 'hangzhou', name: '杭州', pinyin: 'hangzhou' },
  { id: 'chengdu', name: '成都', pinyin: 'chengdu' },
  { id: 'nanjing', name: '南京', pinyin: 'nanjing' },
  { id: 'wuhan', name: '武汉', pinyin: 'wuhan' },
];

const hotCommunities = [
  { name: '深圳华润城', city: 'shenzhen', price: '12.5万/㎡' },
  { name: '上海汤臣一品', city: 'shanghai', price: '28.0万/㎡' },
  { name: '北京星河湾', city: 'beijing', price: '15.8万/㎡' },
  { name: '广州汇景新城', city: 'guangzhou', price: '8.5万/㎡' },
  { name: '杭州西溪诚园', city: 'hangzhou', price: '6.2万/㎡' },
];

const guideArticles = [
  { title: '首付计算器', slug: 'down-payment-calculator' },
  { title: '贷款流程详解', slug: 'loan-process' },
  { title: '购房税费明细', slug: 'purchase-taxes' },
  { title: '看房技巧指南', slug: 'house-viewing-tips' },
  { title: '二手房交易流程', slug: 'second-hand-process' },
];

const knowledgeArticles = [
  { title: '什么是容积率', slug: 'what-is-plot-ratio' },
  { title: '得房率怎么算', slug: 'how-to-calculate-efficiency-rate' },
  { title: '学区房政策解读', slug: 'school-district-policy' },
  { title: '房产证办理流程', slug: 'property-certificate-process' },
  { title: '公积金贷款条件', slug: 'housing-fund-loan' },
];

const Footer: React.FC = () => {
  return (
    <footer className="bg-fluent-deepOcean-500 border-t border-fluent-deepOcean-400">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-fluent-gold-400 text-sm font-medium">📍 热门城市</span>
          </div>
          <div className="flex flex-wrap gap-3">
            {cities.map(city => (
              <Link
                key={city.id}
                to={`/city/${city.pinyin}`}
                className="px-3 py-1.5 bg-fluent-deepOcean-400/50 text-fluent-deepOcean-100 rounded-lg text-sm hover:bg-fluent-gold-500 hover:text-fluent-deepOcean-500 transition-all duration-300"
              >
                {city.name}房产
              </Link>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>🏘️</span>
              <span>热门小区</span>
            </h3>
            <ul className="space-y-3">
              {hotCommunities.map((community, index) => (
                <li key={index}>
                  <Link
                    to={`/community/${community.city}/${encodeURIComponent(community.name)}`}
                    className="text-fluent-deepOcean-200 hover:text-fluent-gold-400 transition-colors text-sm flex items-center justify-between group"
                  >
                    <span>{community.name}</span>
                    <span className="text-xs text-fluent-deepOcean-300 group-hover:text-fluent-gold-300">
                      {community.price}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>📖</span>
              <span>购房指南</span>
            </h3>
            <ul className="space-y-3">
              {guideArticles.map((article, index) => (
                <li key={index}>
                  <Link
                    to={`/guide/${article.slug}`}
                    className="text-fluent-deepOcean-200 hover:text-fluent-gold-400 transition-colors text-sm"
                  >
                    {article.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span>📚</span>
              <span>房产知识库</span>
            </h3>
            <ul className="space-y-3">
              {knowledgeArticles.map((article, index) => (
                <li key={index}>
                  <Link
                    to={`/knowledge/${article.slug}`}
                    className="text-fluent-deepOcean-200 hover:text-fluent-gold-400 transition-colors text-sm"
                  >
                    {article.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-fluent-deepOcean-400 pt-6 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-fluent-gold-400 text-sm font-medium">🗺️ 城市专题</span>
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            {cities.map(city => (
              <Link
                key={city.id}
                to={`/city/${city.pinyin}`}
                className="text-fluent-deepOcean-300 hover:text-fluent-gold-400 transition-colors"
              >
                {city.name}房产
              </Link>
            ))}
          </div>
        </div>

        <div className="border-t border-fluent-deepOcean-400 pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-6 text-sm text-fluent-deepOcean-300">
              <Link to="/about" className="hover:text-fluent-gold-400 transition-colors">
                关于我们
              </Link>
              <Link to="/contact" className="hover:text-fluent-gold-400 transition-colors">
                联系我们
              </Link>
              <Link to="/privacy" className="hover:text-fluent-gold-400 transition-colors">
                隐私政策
              </Link>
              <Link to="/terms" className="hover:text-fluent-gold-400 transition-colors">
                服务条款
              </Link>
              <Link to="/sitemap" className="hover:text-fluent-gold-400 transition-colors">
                站点地图
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <a href="#" className="w-8 h-8 bg-fluent-deepOcean-400 rounded-lg flex items-center justify-center text-fluent-deepOcean-200 hover:bg-fluent-gold-500 hover:text-fluent-deepOcean-500 transition-all text-xs">
                微信
              </a>
              <a href="#" className="w-8 h-8 bg-fluent-deepOcean-400 rounded-lg flex items-center justify-center text-fluent-deepOcean-200 hover:bg-fluent-gold-500 hover:text-fluent-deepOcean-500 transition-all text-xs">
                微博
              </a>
            </div>
          </div>
          <div className="mt-6 text-center text-sm text-fluent-deepOcean-400">
            <p>© 2026 房都督 - 专业的AI房产分析平台 | 保留所有权利</p>
            <p className="mt-2 text-xs">
              提供深圳、上海、北京、广州等城市房价分析、小区评测、购房指南等专业服务
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
