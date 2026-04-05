import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  MapPinIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  HomeIcon,
  BuildingOfficeIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ArrowRightIcon,
  SparklesIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import Mascot from '@/components/mascot/Mascot';
import { seoApi, SEOLandingData } from '@/services/seoApi';

const SEOLandingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [data, setData] = useState<SEOLandingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const query = searchParams.get('q') || '';

  useEffect(() => {
    if (query) {
      loadSEOData();
    } else {
      navigate('/');
    }
  }, [query]);

  useEffect(() => {
    if (data?.page_title) {
      document.title = data.page_title;
    }
    return () => {
      document.title = '房都督AI - 智能房产分析平台';
    };
  }, [data?.page_title]);

  const loadSEOData = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const result = await seoApi.getLandingData(query);
      setData(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = () => {
    sessionStorage.setItem('seo_query', query);
    navigate('/register');
  };

  const handleLogin = () => {
    sessionStorage.setItem('seo_query', query);
    navigate('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">正在加载分析数据...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || '加载失败'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">房</span>
            </div>
            <span className="font-bold text-xl text-gray-900">房都督AI</span>
          </div>
          
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                进入控制台
              </button>
            ) : (
              <>
                <button
                  onClick={handleLogin}
                  className="text-gray-600 hover:text-gray-900"
                >
                  登录
                </button>
                <button
                  onClick={handleRegister}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  免费注册
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            {data.query}分析报告
          </h1>
          <p className="text-gray-600">
            {data.location.city && (
              <span className="inline-flex items-center gap-1 mr-3">
                <MapPinIcon className="w-4 h-4 text-primary-500" />
                {data.location.city}
                {data.location.district && ` · ${data.location.district}`}
              </span>
            )}
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                <CurrencyDollarIcon className="w-5 h-5 text-primary-600" />
              </div>
              <span className="text-sm text-gray-500">均价</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {data.key_metrics.avg_price_per_sqm}万/㎡
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {data.key_metrics.price_range.min}万 - {data.key_metrics.price_range.max}万
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                {data.market_data.year_change > 0 ? (
                  <ArrowTrendingUpIcon className="w-5 h-5 text-green-600" />
                ) : (
                  <ArrowTrendingDownIcon className="w-5 h-5 text-red-600" />
                )}
              </div>
              <span className="text-sm text-gray-500">年涨幅</span>
            </div>
            <p className={`text-2xl font-bold ${data.market_data.year_change > 0 ? 'text-red-500' : 'text-green-500'}`}>
              {data.market_data.year_change > 0 ? '+' : ''}{data.market_data.year_change}%
            </p>
            <p className="text-xs text-gray-400 mt-1">{data.market_data.price_trend}</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <HomeIcon className="w-5 h-5 text-blue-600" />
              </div>
              <span className="text-sm text-gray-500">在售房源</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {data.key_metrics.total_listings}套
            </p>
            <p className="text-xs text-gray-400 mt-1">成交量{data.market_data.transaction_volume}</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <CalendarIcon className="w-5 h-5 text-purple-600" />
              </div>
              <span className="text-sm text-gray-500">平均成交周期</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {data.key_metrics.avg_days_on_market}天
            </p>
            <p className="text-xs text-gray-400 mt-1">流动性{data.market_data.liquidity}</p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="md:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-primary-500" />
              价格走势
            </h3>
            <div className="h-48 flex items-end gap-2">
              {data.price_chart_data.map((item, index) => {
                const maxPrice = Math.max(...data.price_chart_data.map(d => d.price));
                const height = (item.price / maxPrice) * 100;
                return (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-primary-500 rounded-t transition-all hover:bg-primary-600"
                      style={{ height: `${height}%` }}
                      title={`${item.month}: ${Math.round(item.price / 10000)}万/㎡`}
                    />
                    <span className="text-xs text-gray-400 mt-1">{item.month}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-yellow-500" />
              区域亮点
            </h3>
            <ul className="space-y-3">
              {data.market_data.highlights.map((highlight, index) => (
                <li key={index} className="flex items-start gap-2 text-gray-600">
                  <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="bg-gradient-to-r from-primary-500 to-primary-700 rounded-2xl p-8 text-white">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-2xl font-bold mb-2">{data.registration_cta.title}</h2>
              <p className="text-primary-100 mb-4">{data.registration_cta.subtitle}</p>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2">
                  <CheckIcon className="w-5 h-5" />
                  完整的市场分析报告
                </li>
                <li className="flex items-center gap-2">
                  <CheckIcon className="w-5 h-5" />
                  周边配套详情（学校、医院、商场）
                </li>
                <li className="flex items-center gap-2">
                  <CheckIcon className="w-5 h-5" />
                  专业投资建议和风险提示
                </li>
                <li className="flex items-center gap-2">
                  <CheckIcon className="w-5 h-5" />
                  导出PDF报告
                </li>
              </ul>
              <button
                onClick={handleRegister}
                className="flex items-center gap-2 px-6 py-3 bg-white text-primary-600 rounded-xl font-medium hover:bg-primary-50 transition-colors"
              >
                {data.registration_cta.button_text}
                <ArrowRightIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="flex justify-center">
              <div className="relative">
                <Mascot emotion="happy" size="xl" />
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-white rounded-full px-4 py-2 shadow-lg">
                  <p className="text-sm text-gray-600 whitespace-nowrap">{data.mascot_message}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-100 py-6 mt-12">
        <div className="max-w-6xl mx-auto px-4 text-center text-gray-500 text-sm">
          <p>© 2024 房都督AI - 智能房产分析平台</p>
          <p className="mt-1">数据仅供参考，不构成投资建议</p>
        </div>
      </footer>
    </div>
  );
};

export default SEOLandingPage;
