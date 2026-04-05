import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

interface CommunityData {
  name: string;
  city: string;
  district: string;
  price: number;
  priceChange: number;
  description: string;
  facilities: string[];
  transport: string[];
  education: string[];
  reviews: Array<{
    user: string;
    rating: number;
    content: string;
    date: string;
  }>;
}

const mockCommunities: Record<string, CommunityData> = {
  '深圳华润城': {
    name: '华润城',
    city: 'shenzhen',
    district: '南山',
    price: 125000,
    priceChange: 3.2,
    description: '华润城是深圳南山区的大型综合体项目，包含住宅、商业、办公等多种业态。项目规划完善，绿化率高，是深圳知名的高端住宅社区。',
    facilities: ['万象城购物中心', '华润万家', '南山外国语学校', '深圳湾体育中心'],
    transport: ['地铁1号线高新园站', '地铁2号线科苑站'],
    education: ['南山外国语学校', '南山实验学校'],
    reviews: [
      { user: '张先生', rating: 5, content: '环境优美，物业管理到位，交通便利', date: '2024-01-15' },
      { user: '李女士', rating: 4, content: '户型设计合理，采光好，就是价格有点贵', date: '2024-02-20' },
    ],
  },
  '上海汤臣一品': {
    name: '汤臣一品',
    city: 'shanghai',
    district: '浦东',
    price: 280000,
    priceChange: 2.5,
    description: '汤臣一品是上海浦东陆家嘴金融贸易区的顶级豪宅，拥有无敌江景视野，是上海最贵的住宅之一。',
    facilities: ['陆家嘴中心绿地', '正大广场', '金茂大厦'],
    transport: ['地铁2号线陆家嘴站'],
    education: ['浦东外国语学校', '建平中学'],
    reviews: [
      { user: '王先生', rating: 5, content: '顶级豪宅，服务一流，视野无敌', date: '2024-01-10' },
    ],
  },
};

const CommunityPage: React.FC = () => {
  const { cityId, communityName } = useParams<{ cityId: string; communityName: string }>();
  const [community, setCommunity] = useState<CommunityData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const decodedName = decodeURIComponent(communityName || '');
    const key = `${cityId === 'shenzhen' ? '深圳' : ''}${decodedName}`;
    
    if (mockCommunities[key]) {
      setCommunity(mockCommunities[key]);
    }
    setLoading(false);
  }, [cityId, communityName]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="w-12 h-12 border-4 border-fluent-gold-400 border-t-fluent-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!community) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <h1 className="text-2xl font-bold text-fluent-deepOcean-500 mb-4">小区页面开发中</h1>
        <p className="text-fluent-deepOcean-300 mb-6">该小区的详情页面正在建设中，敬请期待！</p>
        <Link to="/" className="text-fluent-gold-500 hover:text-fluent-gold-600">
          返回首页 →
        </Link>
      </div>
    );
  }

  const formatPrice = (price: number) => {
    return (price / 10000).toFixed(1) + '万';
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <nav className="text-sm text-fluent-deepOcean-300 mb-6">
        <Link to="/" className="hover:text-fluent-gold-500">首页</Link>
        <span className="mx-2">›</span>
        <Link to={`/city/${community.city}`} className="hover:text-fluent-gold-500">
          {community.city === 'shenzhen' ? '深圳房产' : community.city === 'shanghai' ? '上海房产' : '北京房产'}
        </Link>
        <span className="mx-2">›</span>
        <span className="text-fluent-deepOcean-500">{community.name}</span>
      </nav>

      <div className="acrylic rounded-2xl shadow-fluent-lg p-8 border border-white/30 mb-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-fluent-deepOcean-500 mb-2">
              {community.name}房价走势 - {community.name}周边配套 - {community.name}优缺点
            </h1>
            <p className="text-fluent-deepOcean-300">
              {community.city === 'shenzhen' ? '深圳' : '上海'}{community.district}区 | 均价 {formatPrice(community.price)}/㎡
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-fluent-deepOcean-300">环比变化</p>
            <p className={`text-xl font-semibold ${community.priceChange >= 0 ? 'text-red-500' : 'text-fluent-jade-500'}`}>
              {community.priceChange >= 0 ? '+' : ''}{community.priceChange}%
            </p>
          </div>
        </div>

        <p className="text-fluent-deepOcean-400 mb-6">{community.description}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
            <h3 className="font-semibold text-fluent-deepOcean-500 mb-3 flex items-center gap-2">
              <span>🛒</span>
              <span>周边配套</span>
            </h3>
            <ul className="space-y-2">
              {community.facilities.map((facility, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-fluent-deepOcean-400">
                  <span className="text-fluent-gold-500">✓</span>
                  <span>{facility}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
            <h3 className="font-semibold text-fluent-deepOcean-500 mb-3 flex items-center gap-2">
              <span>🚇</span>
              <span>交通出行</span>
            </h3>
            <ul className="space-y-2">
              {community.transport.map((t, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-fluent-deepOcean-400">
                  <span className="text-fluent-gold-500">🚇</span>
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-fluent-deepOcean-50 rounded-xl p-4">
            <h3 className="font-semibold text-fluent-deepOcean-500 mb-3 flex items-center gap-2">
              <span>🎓</span>
              <span>教育资源</span>
            </h3>
            <ul className="space-y-2">
              {community.education.map((edu, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-fluent-deepOcean-400">
                  <span className="text-fluent-gold-500">📚</span>
                  <span>{edu}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30 mb-8">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span>⭐</span>
            <span>用户评价</span>
          </h2>
          <div className="space-y-4">
            {community.reviews.map((review, index) => (
              <div key={index} className="p-4 bg-fluent-deepOcean-50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-fluent-deepOcean-500">{review.user}</span>
                  <div className="flex items-center gap-1">
                    {[...Array(review.rating)].map((_, i) => (
                      <span key={i} className="text-fluent-gold-500">★</span>
                    ))}
                  </div>
                </div>
                <p className="text-sm text-fluent-deepOcean-400">{review.content}</p>
                <p className="text-xs text-fluent-deepOcean-300 mt-2">{review.date}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30 text-center">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4">
            需要{community.name}的详细分析报告？
          </h2>
          <p className="text-fluent-deepOcean-300 mb-6">
            AI房产顾问为您提供{community.name}深度评测、价格走势分析、投资建议
          </p>
          <Link
            to="/register"
            className="inline-block bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-8 py-3 rounded-xl font-medium hover:shadow-gold-glow transition-all duration-300"
          >
            免费获取AI分析报告
          </Link>
        </div>
      </div>
    </div>
  );
};

export default CommunityPage;
