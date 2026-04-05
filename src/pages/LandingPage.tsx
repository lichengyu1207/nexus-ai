import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  SparklesIcon,
  ChartBarIcon,
  MapPinIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  MagnifyingGlassIcon,
  DocumentDuplicateIcon,
  ArrowsRightLeftIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import Mascot from '@/components/mascot/Mascot';
import WelcomeModal from '@/components/WelcomeModal';
import PreviewResultCard from '@/components/PreviewResultCard';
import HowItWorks from '@/components/landing/HowItWorks';
import Pricing from '@/components/landing/Pricing';
import FAQ from '@/components/landing/FAQ';
import Footer from '@/components/landing/Footer';
import TrustBadges from '@/components/landing/TrustBadges';
import Testimonials from '@/components/landing/Testimonials';
import { DemoShowcase } from '@/components/demo';
import { BottomShowcase } from '@/components/bottomShowcase';
import { InternationalShowcase } from '@/components/showcase';
import { previewApi, PreviewResult } from '@/services/previewApi';
import { initSourceTracking, getStoredSource } from '@/utils/sourceTracker';

const LandingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [showWelcome, setShowWelcome] = useState(false);
  
  const [previewQuery, setPreviewQuery] = useState('');
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const source = searchParams.get('source') || searchParams.get('ref') || searchParams.get('utm_source');
  const seoQuery = searchParams.get('q');
  const isFounderIP = ['zhihu', 'weixin', 'weibo', 'bilibili', 'laohai'].includes(source || '');

  useEffect(() => {
    if (seoQuery) {
      navigate(`/search?q=${encodeURIComponent(seoQuery)}`, { replace: true });
      return;
    }
    
    initSourceTracking();
    
    if (source) {
      const storedSource = getStoredSource();
      if (!storedSource || storedSource === 'direct') {
        localStorage.setItem('user_source', source);
      }
    }
  }, [source, seoQuery, navigate]);

  useEffect(() => {
    if (isAuthenticated && !localStorage.getItem('welcome_shown')) {
      setShowWelcome(true);
      localStorage.setItem('welcome_shown', 'true');
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const savedQuery = sessionStorage.getItem('preview_query');
    if (savedQuery && isAuthenticated) {
      sessionStorage.removeItem('preview_query');
      navigate('/dashboard', { state: { initialQuery: savedQuery } });
    }
  }, [isAuthenticated, navigate]);

  const handleStartAnalysis = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/login', { state: { from: { pathname: '/dashboard' } } });
    }
  };

  const handlePreviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!previewQuery.trim()) return;
    
    setIsPreviewLoading(true);
    setShowPreview(true);
    
    try {
      const result = await previewApi.createPreview(previewQuery);
      setPreviewResult(result);
    } catch (error) {
      console.error('Preview failed:', error);
      setShowPreview(false);
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleClosePreview = () => {
    setShowPreview(false);
    setPreviewResult(null);
  };

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
              <>
                <span className="text-gray-600">你好，{user?.full_name || user?.email}</span>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  进入控制台
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => navigate('/login')}
                  className="text-gray-600 hover:text-gray-900"
                >
                  登录
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  免费注册
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            {isFounderIP && (
              <div className="inline-flex items-center gap-2 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full text-sm font-medium mb-4">
                <SparklesIcon className="w-4 h-4" />
                老骇的朋友专属福利
              </div>
            )}
            
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              {isFounderIP ? (
                <>老骇的朋友，你好！</>
              ) : (
                <>输入地址，3分钟看懂房子值不值</>
              )}
            </h1>
            
            <p className="text-2xl md:text-3xl font-semibold text-gray-800 mb-8 leading-relaxed">
              {isFounderIP ? (
                <>感谢关注！这是为你准备的专属礼物——房都督AI帮你分析房产价值，避开买房坑。</>
              ) : (
                <>AI智能分析房产价值、周边配套、投资潜力，让买房决策更简单。</>
              )}
            </p>

            {!isAuthenticated && (
              <form onSubmit={handlePreviewSubmit} className="mb-6">
                <div className="relative">
                  <input
                    type="text"
                    value={previewQuery}
                    onChange={(e) => setPreviewQuery(e.target.value)}
                    placeholder="输入地址试试，如：深圳南山区学区房"
                    className="w-full px-5 py-4 pr-14 text-lg border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent shadow-sm"
                  />
                  <button
                    type="submit"
                    disabled={isPreviewLoading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50"
                  >
                    {isPreviewLoading ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <MagnifyingGlassIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  无需注册，先看看分析结果
                </p>
              </form>
            )}
            
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleStartAnalysis}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
              >
                {isAuthenticated ? '开始分析' : '免费注册，获取完整报告'}
                <ArrowRightIcon className="w-5 h-5" />
              </button>
              
              {isAuthenticated && (
                <>
                  <button
                    onClick={() => navigate('/dashboard?batch=true')}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                  >
                    <DocumentDuplicateIcon className="w-5 h-5" />
                    批量分析
                  </button>
                  <button
                    onClick={() => navigate('/compare')}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                  >
                    <ArrowsRightLeftIcon className="w-5 h-5" />
                    房源对比
                  </button>
                </>
              )}
            </div>
            
            <div className="mt-6 flex items-center gap-2 text-gray-500">
              <ShieldCheckIcon className="w-5 h-5 text-green-500" />
              <span>
                {isFounderIP ? '粉丝专属：5次免费分析' : '新用户赠送3次免费分析'}
              </span>
            </div>
          </div>
          
          <div className="flex justify-center">
            <div className="relative">
              <Mascot
                emotion={isFounderIP ? 'happy' : 'default'}
                size="xl"
                animate
              />
              <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-white rounded-full px-4 py-2 shadow-lg">
                <p className="text-sm text-gray-600 whitespace-nowrap">
                  {isFounderIP ? '感谢关注！试试分析吧～' : '想知道你家房子值多少钱？'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 国际版动态宣传栏 */}
      <section className="py-8">
        <InternationalShowcase autoPlay={true} />
      </section>

      {/* Demo Showcase - 智能体工作剧场 */}
      <section className="py-8">
        <DemoShowcase />
      </section>

      {/* Trust Badges */}
      <section className="bg-white border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4">
          <TrustBadges />
        </div>
      </section>

      {showPreview && (
        <section className="max-w-6xl mx-auto px-4 pb-16">
          {isPreviewLoading && !previewResult ? (
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-12 text-center max-w-2xl mx-auto">
              <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">正在分析中...</p>
            </div>
          ) : previewResult ? (
            <PreviewResultCard result={previewResult} onClose={handleClosePreview} />
          ) : null}
        </section>
      )}

      <section className="bg-white py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            一站式房产分析服务
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <ChartBarIcon className="w-8 h-8 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">智能估值</h3>
              <p className="text-gray-600">
                基于大数据和AI算法，精准分析房产价值
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MapPinIcon className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">周边配套</h3>
              <p className="text-gray-600">
                学校、医院、商场、交通，一目了然
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <ShieldCheckIcon className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">风险预警</h3>
              <p className="text-gray-600">
                识别潜在风险，帮你避开买房坑
              </p>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 mt-8">
            <div className="text-center p-6 bg-blue-50 rounded-2xl">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <DocumentDuplicateIcon className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">批量分析</h3>
              <p className="text-gray-600">
                一次输入多个地址，同时分析多个房源，节省时间
              </p>
            </div>
            
            <div className="text-center p-6 bg-orange-50 rounded-2xl">
              <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <ArrowsRightLeftIcon className="w-8 h-8 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">房源对比</h3>
              <p className="text-gray-600">
                多房源横向对比，价格、学区、交通一目了然
              </p>
            </div>
          </div>
        </div>
      </section>

      <HowItWorks />

      {/* IP计划推广 */}
      <section className="py-16 bg-gradient-to-r from-purple-50 to-pink-50">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 bg-purple-100 text-purple-800 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <SparklesIcon className="w-4 h-4" />
            内容创作者专属
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            IP达人计划
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            成为IP达人，分享专属链接，用户通过您的链接注册即可获得佣金收益
          </p>
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl font-bold text-purple-600 mb-2">30%</div>
              <div className="text-gray-600">佣金比例</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl font-bold text-purple-600 mb-2">T+7</div>
              <div className="text-gray-600">结算周期</div>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="text-3xl font-bold text-purple-600 mb-2">¥100</div>
              <div className="text-gray-600">最低提现</div>
            </div>
          </div>
          <button
            onClick={() => navigate('/ip-apply')}
            className="px-8 py-4 bg-purple-600 text-white rounded-xl font-medium text-lg hover:bg-purple-700 transition-colors"
          >
            立即申请加入
          </button>
        </div>
      </section>

      <Testimonials />

      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            准备好开始了吗？
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            只需输入地址，即可获得专业分析报告
          </p>
          <button
            onClick={handleStartAnalysis}
            className="px-8 py-4 bg-primary-600 text-white rounded-xl font-medium text-lg hover:bg-primary-700 transition-colors"
          >
            {isAuthenticated ? '开始分析' : '免费注册，立即体验'}
          </button>
        </div>
      </section>

      <Pricing />
      <FAQ />
      <BottomShowcase />
      <Footer />

      {showWelcome && (
        <WelcomeModal
          isOpen={showWelcome}
          onClose={() => setShowWelcome(false)}
          username={user?.full_name || undefined}
        />
      )}
    </div>
  );
};

export default LandingPage;
