import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import WelcomeMessage from '../components/common/WelcomeMessage';
import HowItWorks from '../components/common/HowItWorks';
import FAQ from '../components/common/FAQ';
import PolicySection from '../components/common/PolicySection';
import RegionalDynamics from '../components/common/RegionalDynamics';
import { useSourceStore } from '../stores';
import { TypewriterText } from '../components/Animation/TypewriterText';
import { DemoButton } from '../components/Demo';

interface UserInfo {
  id: string;
  email: string;
  username: string;
  role: string;
  integral: number;
  source: string | null;
  source_name: string | null;
  bonus_label: string | null;
  membership_level: string;
}

interface Plan {
  id: string;
  name: string;
  price: number;
  original_price?: number;
  credits: number;
  features: string[];
  popular?: boolean;
  discount_label?: string;
}

const HomePage: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState<Plan[]>([]);
  const { source } = useSourceStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchUser();
    fetchPlans();
  }, []);

  const fetchUser = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/plans');
      if (response.ok) {
        const data = await response.json();
        setPlans(data.plans || defaultPlans);
      }
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  const defaultPlans: Plan[] = [
    {
      id: 'free',
      name: '免费体验',
      price: 0,
      credits: 3,
      features: ['3次免费分析', '基础报告', '7天有效期'],
    },
    {
      id: 'basic',
      name: '积分包',
      price: 19,
      original_price: 29,
      credits: 10,
      features: ['10次分析', '完整报告', '数据溯源', '30天有效期'],
      popular: true,
    },
    {
      id: 'pro',
      name: '专业版',
      price: 199,
      original_price: 299,
      credits: 100,
      features: ['100次分析/月', '高级报告', '批量分析', '优先支持'],
      discount_label: source === 'laohai' ? '粉丝专享价' : undefined,
    },
    {
      id: 'enterprise',
      name: '企业版',
      price: 999,
      credits: -1,
      features: ['无限分析', 'API接入', '专属客服', '定制报告'],
    },
  ];

  const getHeroContent = () => {
    const contents: Record<string, { title: string; subtitle: string; cta: string }> = {
      laohai: {
        title: '老骇的朋友，欢迎你！',
        subtitle: '专属粉丝福利：注册即送5次免费分析体验',
        cta: '立即体验',
      },
      seo: {
        title: '找到您心仪的房产分析',
        subtitle: 'AI智能分析，3分钟看懂房子值不值',
        cta: '开始分析',
      },
      social: {
        title: '欢迎来自社交媒体的朋友',
        subtitle: '专业房产分析，助您做出明智决策',
        cta: '免费试用',
      },
      default: {
        title: 'AI智能房产分析平台',
        subtitle: '多智能体协同，3分钟生成专业房产分析报告',
        cta: '免费体验',
      },
    };
    return contents[source || 'default'] || contents.default;
  };

  const heroContent = getHeroContent();

  const handleStartAnalysis = () => {
    if (user) {
      navigate('/dashboard/property-analysis');
    } else {
      navigate('/register');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-fluent-ivory-50 to-white">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-fluent-deepOcean-500/5 via-transparent to-fluent-gold-500/5" />
        <div className="absolute top-20 left-10 w-72 h-72 bg-fluent-gold-500/10 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-fluent-deepOcean-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
        
        <div className="container mx-auto px-4 py-16 md:py-24 relative">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="flex-1 text-center lg:text-left">
              {user && (
                <div className="mb-6">
                  <WelcomeMessage
                    source={user.source}
                    sourceName={user.source_name}
                    bonusLabel={user.bonus_label}
                    username={user.username}
                  />
                </div>
              )}
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-fluent-deepOcean-500 mb-6 leading-tight">
                {heroContent.title}
              </h1>
              
              <div className="text-xl md:text-2xl text-fluent-deepOcean-400 mb-4 h-12 animate-fade-in-up">
                <TypewriterText
                  texts={[
                    '多智能体协同分析',
                    '3分钟生成专业报告',
                    '数据可溯源可验证',
                    '让房产决策更明智',
                    'AI赋能房产投资'
                  ]}
                  speed={80}
                  deleteSpeed={40}
                  pauseTime={3000}
                  cursorChar="|"
                  className="font-semibold"
                />
              </div>
              
              <p className="text-lg text-fluent-deepOcean-300 mb-8 max-w-2xl">
                {heroContent.subtitle}
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <button
                  onClick={handleStartAnalysis}
                  className="group relative px-8 py-4 bg-fluent-gold-500 text-fluent-deepOcean-500 font-semibold rounded-xl overflow-hidden transition-all duration-300 hover:shadow-gold-glow hover:scale-105"
                >
                  <span className="relative z-10">{heroContent.cta}</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
                <DemoButton />
                <Link
                  to="/pricing"
                  className="px-8 py-4 border-2 border-fluent-deepOcean-500 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-500 hover:text-white font-semibold rounded-xl transition-all duration-300"
                >
                  查看定价
                </Link>
              </div>

              <div className="mt-8 flex items-center justify-center lg:justify-start gap-8 text-sm text-fluent-deepOcean-300">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-fluent-jade-500 flex items-center justify-center text-white text-xs">✓</span>
                  <span>免费体验</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-fluent-jade-500 flex items-center justify-center text-white text-xs">✓</span>
                  <span>无需信用卡</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-fluent-jade-500 flex items-center justify-center text-white text-xs">✓</span>
                  <span>即时出报告</span>
                </div>
              </div>
            </div>

            <div className="flex-1 relative">
              <div className="relative w-full max-w-lg mx-auto">
                <div className="absolute inset-0 bg-gradient-to-r from-fluent-gold-500/20 to-fluent-deepOcean-500/20 rounded-3xl transform rotate-3 blur-sm" />
                <div className="relative acrylic rounded-3xl shadow-fluent-xl p-6 border border-white/30">
                  <div className="text-center mb-4">
                    <span className="text-6xl">🏠</span>
                  </div>
                  <div className="space-y-3">
                    <div className="h-3 bg-fluent-deepOcean-100 rounded-full w-full overflow-hidden">
                      <div className="h-full w-4/5 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-500 rounded-full animate-shimmer" />
                    </div>
                    <div className="h-3 bg-fluent-deepOcean-100 rounded-full w-4/5 overflow-hidden">
                      <div className="h-full w-3/5 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-500 rounded-full animate-shimmer" style={{ animationDelay: '0.5s' }} />
                    </div>
                    <div className="h-3 bg-fluent-deepOcean-100 rounded-full w-3/5 overflow-hidden">
                      <div className="h-full w-2/3 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-500 rounded-full animate-shimmer" style={{ animationDelay: '1s' }} />
                    </div>
                  </div>
                  <div className="mt-6 grid grid-cols-3 gap-3">
                    <div className="bg-fluent-jade-50 rounded-xl p-3 text-center border border-fluent-jade-200/50">
                      <p className="text-2xl font-bold text-fluent-jade-600">98%</p>
                      <p className="text-xs text-fluent-deepOcean-400">置信度</p>
                    </div>
                    <div className="bg-fluent-deepOcean-50 rounded-xl p-3 text-center border border-fluent-deepOcean-200/50">
                      <p className="text-2xl font-bold text-fluent-deepOcean-600">12</p>
                      <p className="text-xs text-fluent-deepOcean-400">数据源</p>
                    </div>
                    <div className="bg-fluent-gold-50 rounded-xl p-3 text-center border border-fluent-gold-200/50">
                      <p className="text-2xl font-bold text-fluent-gold-600">3min</p>
                      <p className="text-xs text-fluent-deepOcean-400">分析时间</p>
                    </div>
                  </div>
                </div>
                
                <div className="absolute -bottom-4 -right-4 w-20 h-20 bg-fluent-gold-500 rounded-full flex items-center justify-center text-4xl shadow-gold-glow animate-float cursor-pointer hover:scale-110 transition-transform">
                  🐶
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-fluent-deepOcean-500 mb-12">核心功能</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="group acrylic rounded-2xl p-6 hover:shadow-fluent-lg transition-all duration-300 border border-white/30 hover:border-fluent-gold-300">
              <div className="w-14 h-14 bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 rounded-xl flex items-center justify-center text-2xl mb-4 shadow-fluent-md group-hover:scale-110 transition-transform">
                🤖
              </div>
              <h3 className="text-xl font-semibold text-fluent-deepOcean-500 mb-3">多智能体协同</h3>
              <p className="text-fluent-deepOcean-300">
                需求分析师、数据采集师、市场分析师等多个AI智能体协同工作，确保分析的全面性和准确性。
              </p>
            </div>

            <div className="group acrylic rounded-2xl p-6 hover:shadow-fluent-lg transition-all duration-300 border border-white/30 hover:border-fluent-gold-300">
              <div className="w-14 h-14 bg-gradient-to-br from-fluent-jade-400 to-fluent-jade-600 rounded-xl flex items-center justify-center text-2xl mb-4 shadow-fluent-md group-hover:scale-110 transition-transform">
                📊
              </div>
              <h3 className="text-xl font-semibold text-fluent-deepOcean-500 mb-3">实时报告生成</h3>
              <p className="text-fluent-deepOcean-300">
                10-15分钟内生成详细的分析报告，包含市场分析、价格评估、投资建议等多个维度。
              </p>
            </div>

            <div className="group acrylic rounded-2xl p-6 hover:shadow-fluent-lg transition-all duration-300 border border-white/30 hover:border-fluent-gold-300">
              <div className="w-14 h-14 bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 rounded-xl flex items-center justify-center text-2xl mb-4 shadow-fluent-md group-hover:scale-110 transition-transform">
                🔍
              </div>
              <h3 className="text-xl font-semibold text-fluent-deepOcean-500 mb-3">数据可溯源</h3>
              <p className="text-fluent-deepOcean-300">
                每个结论都能追踪到原始数据来源，标注置信度，让您的决策更有依据。
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 mica">
        <div className="container mx-auto px-4">
          <HowItWorks />
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-fluent-deepOcean-500 mb-4">选择适合您的方案</h2>
          <p className="text-center text-fluent-deepOcean-300 mb-12">
            灵活的定价方案，满足不同需求
            {source === 'laohai' && (
              <span className="block mt-2 text-fluent-gold-500 font-medium">
                🎁 老骇粉丝专享：所有套餐额外赠送20%积分！
              </span>
            )}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {(plans.length > 0 ? plans : defaultPlans).map((plan) => (
              <div
                key={plan.id}
                className={`relative acrylic rounded-2xl p-6 border transition-all duration-300 hover:shadow-fluent-lg ${
                  plan.popular ? 'border-fluent-gold-400 shadow-gold-glow scale-105' : 'border-white/30 hover:border-fluent-gold-300'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-4 py-1 rounded-full text-sm font-semibold shadow-fluent-sm">
                    最受欢迎
                  </div>
                )}
                {plan.discount_label && (
                  <div className="absolute -top-3 right-4 bg-fluent-jade-500 text-white px-3 py-1 rounded-full text-xs">
                    {plan.discount_label}
                  </div>
                )}

                <h3 className="text-xl font-semibold text-fluent-deepOcean-500 mb-2">{plan.name}</h3>
                
                <div className="mb-4">
                  <span className="text-4xl font-bold text-fluent-deepOcean-500">¥{plan.price}</span>
                  {plan.original_price && (
                    <span className="text-fluent-deepOcean-300 line-through ml-2">
                      ¥{plan.original_price}
                    </span>
                  )}
                </div>

                <p className="text-fluent-deepOcean-300 mb-4">
                  {plan.credits === -1 ? '无限次分析' : `${plan.credits}次分析`}
                </p>

                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm text-fluent-deepOcean-400">
                      <span className="w-5 h-5 rounded-full bg-fluent-jade-500 flex items-center justify-center text-white text-xs">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => navigate(user ? '/dashboard/recharge' : '/register')}
                  className={`w-full py-3 rounded-xl font-semibold transition-all duration-300 ${
                    plan.popular
                      ? 'bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 hover:shadow-gold-glow'
                      : 'bg-fluent-deepOcean-100 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-200'
                  }`}
                >
                  {plan.price === 0 ? '免费开始' : '立即购买'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 mica">
        <div className="container mx-auto px-4">
          <FAQ />
        </div>
      </section>

      <PolicySection />

      <RegionalDynamics />

      <section className="py-16 bg-gradient-to-r from-fluent-deepOcean-500 to-fluent-deepOcean-600 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 256 256%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%224%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22/%3E%3C/svg%3E')] opacity-5" />
        <div className="container mx-auto px-4 text-center relative">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            准备好开始您的房产分析之旅了吗？
          </h2>
          <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
            加入10万+用户，让AI帮您做出更明智的房产决策
          </p>
          <button
            onClick={handleStartAnalysis}
            className="bg-fluent-gold-500 text-fluent-deepOcean-500 hover:bg-fluent-gold-400 font-semibold py-4 px-8 rounded-xl transition-all duration-300 shadow-gold-glow hover:scale-105"
          >
            {user ? '开始分析' : '免费注册'}
          </button>
        </div>
      </section>

      <section className="py-12 bg-white border-t border-fluent-deepOcean-100">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center group">
              <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">🔒</div>
              <p className="font-medium text-fluent-deepOcean-500">数据加密</p>
              <p className="text-sm text-fluent-deepOcean-300">银行级安全</p>
            </div>
            <div className="text-center group">
              <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">👥</div>
              <p className="font-medium text-fluent-deepOcean-500">10万+用户</p>
              <p className="text-sm text-fluent-deepOcean-300">信赖之选</p>
            </div>
            <div className="text-center group">
              <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">⚡</div>
              <p className="font-medium text-fluent-deepOcean-500">秒级响应</p>
              <p className="text-sm text-fluent-deepOcean-300">快速分析</p>
            </div>
            <div className="text-center group">
              <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">🕐</div>
              <p className="font-medium text-fluent-deepOcean-500">7×24服务</p>
              <p className="text-sm text-fluent-deepOcean-300">全天在线</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
