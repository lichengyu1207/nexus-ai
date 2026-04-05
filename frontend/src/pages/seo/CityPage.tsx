import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

interface CityData {
  name: string;
  pinyin: string;
  avgPrice: number;
  priceChange: number;
  description: string;
  hotCommunities: Array<{
    name: string;
    price: number;
    change: number;
    district: string;
  }>;
  policies: Array<{
    title: string;
    summary: string;
    date: string;
  }>;
}

const cityDataMap: Record<string, CityData> = {
  shenzhen: {
    name: '深圳',
    pinyin: 'shenzhen',
    avgPrice: 68500,
    priceChange: 2.3,
    description: '深圳是中国改革开放的前沿城市，房地产市场活跃，房价位居全国前列。南山区、福田区为核心区域，房价最高。',
    hotCommunities: [
      { name: '华润城', price: 125000, change: 3.2, district: '南山' },
      { name: '深圳湾一号', price: 180000, change: 1.8, district: '南山' },
      { name: '香蜜湖一号', price: 150000, change: 2.1, district: '福田' },
      { name: '华侨城', price: 95000, change: -0.5, district: '南山' },
      { name: '前海时代', price: 110000, change: 4.5, district: '前海' },
    ],
    policies: [
      { title: '深圳购房资格政策', summary: '非深户需连续缴纳5年社保，深户限购2套', date: '2024-01-15' },
      { title: '深圳公积金贷款政策', summary: '最高可贷90万，利率3.1%', date: '2024-02-20' },
      { title: '深圳二手房指导价政策', summary: '各小区指导价定期更新，影响贷款评估', date: '2024-03-10' },
    ],
  },
  shanghai: {
    name: '上海',
    pinyin: 'shanghai',
    avgPrice: 72000,
    priceChange: 1.8,
    description: '上海是中国的经济中心，房地产市场成熟稳定。浦东新区、静安区、黄浦区为核心区域。',
    hotCommunities: [
      { name: '汤臣一品', price: 280000, change: 2.5, district: '浦东' },
      { name: '翠湖天地', price: 220000, change: 1.2, district: '黄浦' },
      { name: '华山夏都', price: 180000, change: 0.8, district: '静安' },
      { name: '仁恒河滨城', price: 120000, change: 1.5, district: '浦东' },
      { name: '中远两湾城', price: 85000, change: -0.3, district: '普陀' },
    ],
    policies: [
      { title: '上海购房资格政策', summary: '非沪户需连续缴纳5年社保，沪户限购2套', date: '2024-01-10' },
      { title: '上海公积金贷款政策', summary: '最高可贷120万，利率3.1%', date: '2024-02-15' },
      { title: '上海房产税政策', summary: '人均60㎡免征，超面积按0.6%征收', date: '2024-03-05' },
    ],
  },
  beijing: {
    name: '北京',
    pinyin: 'beijing',
    avgPrice: 65000,
    priceChange: 1.2,
    description: '北京是中国的首都，教育资源丰富，学区房价格高昂。西城区、海淀区为核心区域。',
    hotCommunities: [
      { name: '星河湾', price: 158000, change: 2.8, district: '朝阳' },
      { name: '万柳书院', price: 180000, change: 3.2, district: '海淀' },
      { name: '中海紫御公馆', price: 140000, change: 1.5, district: '西城' },
      { name: '泛海国际', price: 120000, change: 0.9, district: '朝阳' },
      { name: '融创壹号院', price: 135000, change: 2.1, district: '朝阳' },
    ],
    policies: [
      { title: '北京购房资格政策', summary: '非京户需连续缴纳5年社保，京户限购2套', date: '2024-01-12' },
      { title: '北京公积金贷款政策', summary: '最高可贷120万，利率3.1%', date: '2024-02-18' },
      { title: '北京学区房政策', summary: '多校划片政策实施，学区房溢价收窄', date: '2024-03-08' },
    ],
  },
};

const CityPage: React.FC = () => {
  const { cityId } = useParams<{ cityId: string }>();
  const [cityData, setCityData] = useState<CityData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (cityId && cityDataMap[cityId]) {
      setCityData(cityDataMap[cityId]);
    }
    setLoading(false);
  }, [cityId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="w-12 h-12 border-4 border-fluent-gold-400 border-t-fluent-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!cityData) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <h1 className="text-2xl font-bold text-fluent-deepOcean-500 mb-4">城市页面开发中</h1>
        <p className="text-fluent-deepOcean-300 mb-6">该城市的房产专题页面正在建设中，敬请期待！</p>
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
        <span className="text-fluent-deepOcean-500">{cityData.name}房产</span>
      </nav>

      <div className="acrylic rounded-2xl shadow-fluent-lg p-8 border border-white/30 mb-8">
        <h1 className="text-3xl font-bold text-fluent-deepOcean-500 mb-4">
          {cityData.name}房产 - {cityData.name}房价走势 - {cityData.name}购房指南
        </h1>
        <p className="text-fluent-deepOcean-300 mb-6">{cityData.description}</p>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 text-center">
            <p className="text-sm text-fluent-deepOcean-300">全市均价</p>
            <p className="text-2xl font-bold text-fluent-deepOcean-500">{formatPrice(cityData.avgPrice)}/㎡</p>
          </div>
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 text-center">
            <p className="text-sm text-fluent-deepOcean-300">环比变化</p>
            <p className={`text-2xl font-bold ${cityData.priceChange >= 0 ? 'text-red-500' : 'text-fluent-jade-500'}`}>
              {cityData.priceChange >= 0 ? '+' : ''}{cityData.priceChange}%
            </p>
          </div>
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 text-center">
            <p className="text-sm text-fluent-deepOcean-300">热门小区</p>
            <p className="text-2xl font-bold text-fluent-deepOcean-500">{cityData.hotCommunities.length}+</p>
          </div>
          <div className="bg-fluent-deepOcean-50 rounded-xl p-4 text-center">
            <p className="text-sm text-fluent-deepOcean-300">政策解读</p>
            <p className="text-2xl font-bold text-fluent-deepOcean-500">{cityData.policies.length}篇</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span>🏘️</span>
            <span>{cityData.name}热门小区</span>
          </h2>
          <div className="space-y-3">
            {cityData.hotCommunities.map((community, index) => (
              <Link
                key={index}
                to={`/community/${cityData.pinyin}/${encodeURIComponent(community.name)}`}
                className="flex items-center justify-between p-3 bg-fluent-deepOcean-50 rounded-xl hover:bg-fluent-gold-50 transition-colors group"
              >
                <div>
                  <p className="font-medium text-fluent-deepOcean-500 group-hover:text-fluent-gold-600">
                    {community.name}
                  </p>
                  <p className="text-sm text-fluent-deepOcean-300">{community.district}区</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-fluent-deepOcean-500">{formatPrice(community.price)}/㎡</p>
                  <p className={`text-sm ${community.change >= 0 ? 'text-red-500' : 'text-fluent-jade-500'}`}>
                    {community.change >= 0 ? '+' : ''}{community.change}%
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
          <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4 flex items-center gap-2">
            <span>📜</span>
            <span>{cityData.name}购房政策</span>
          </h2>
          <div className="space-y-4">
            {cityData.policies.map((policy, index) => (
              <div key={index} className="p-4 bg-fluent-deepOcean-50 rounded-xl">
                <h3 className="font-medium text-fluent-deepOcean-500 mb-1">{policy.title}</h3>
                <p className="text-sm text-fluent-deepOcean-300 mb-2">{policy.summary}</p>
                <p className="text-xs text-fluent-deepOcean-400">{policy.date}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30 text-center">
        <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-4">
          需要{cityData.name}房产专业分析？
        </h2>
        <p className="text-fluent-deepOcean-300 mb-6">
          AI房产顾问为您提供{cityData.name}房价走势分析、小区评测、购房建议
        </p>
        <Link
          to="/register"
          className="inline-block bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-8 py-3 rounded-xl font-medium hover:shadow-gold-glow transition-all duration-300"
        >
          免费体验AI分析
        </Link>
      </div>
    </div>
  );
};

export default CityPage;
