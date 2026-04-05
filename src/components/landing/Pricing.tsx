import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';

interface Plan {
  id: string;
  name: string;
  type: string;
  original_price: number;
  final_price: number;
  discount_reason: string | null;
  credits: number | null;
  duration_days: number;
  features: string[];
  is_popular: boolean;
}

const Pricing: React.FC = () => {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await api.get('/plans');
      const allPlans = response.data;
      const displayPlans = allPlans.filter((p: Plan) => 
        ['integral', 'professional', 'enterprise'].includes(p.type)
      );
      setPlans(displayPlans);
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return (price / 100).toFixed(0);
  };

  const handleCTA = (plan: Plan) => {
    if (plan.type === 'integral') {
      navigate('/recharge');
    } else if (plan.type === 'enterprise') {
      const wechat = 'YourWeChatID';
      window.open(`weixin://contacts/profile/${wechat}`, '_blank');
    } else {
      navigate('/recharge');
    }
  };

  const getCTAText = (plan: Plan) => {
    if (plan.type === 'integral') {
      return '立即购买';
    } else if (plan.type === 'enterprise') {
      return '联系销售';
    }
    return '立即升级';
  };

  const getPriceDisplay = (plan: Plan) => {
    if (plan.type === 'enterprise') {
      return '联系我们';
    }
    return formatPrice(plan.final_price);
  };

  const getPeriod = (plan: Plan) => {
    if (plan.type === 'integral') {
      return '';
    }
    if (plan.duration_days === 30) {
      return '/月';
    }
    if (plan.duration_days === 365) {
      return '/年';
    }
    return '';
  };

  if (isLoading) {
    return (
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <div className="h-10 bg-gray-200 rounded w-64 mx-auto mb-4 animate-pulse"></div>
            <div className="h-6 bg-gray-200 rounded w-96 mx-auto animate-pulse"></div>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-2xl shadow-lg p-8 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-24 mx-auto mb-4"></div>
                <div className="h-10 bg-gray-200 rounded w-20 mx-auto mb-4"></div>
                <div className="space-y-3 mb-8">
                  {[1, 2, 3].map((j) => (
                    <div key={j} className="h-4 bg-gray-200 rounded"></div>
                  ))}
                </div>
                <div className="h-10 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-20 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            简单透明的定价
          </h2>
          <p className="text-lg text-gray-600">
            选择适合你的方案，开始智能房产分析
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white rounded-2xl shadow-lg p-8 ${
                plan.is_popular ? 'ring-2 ring-primary-600 scale-105' : ''
              }`}
            >
              {plan.is_popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                  最受欢迎
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {plan.name}
                </h3>
                <div className="flex items-baseline justify-center gap-1">
                  {plan.type === 'enterprise' ? (
                    <span className="text-3xl font-bold text-gray-900">
                      {getPriceDisplay(plan)}
                    </span>
                  ) : (
                    <>
                      {plan.discount_reason && (
                        <span className="text-sm text-gray-400 line-through mr-1">
                          ¥{formatPrice(plan.original_price)}
                        </span>
                      )}
                      <span className="text-sm text-gray-500">¥</span>
                      <span className="text-4xl font-bold text-gray-900">
                        {getPriceDisplay(plan)}
                      </span>
                      {getPeriod(plan) && (
                        <span className="text-sm text-gray-500">
                          {getPeriod(plan)}
                        </span>
                      )}
                    </>
                  )}
                </div>
                {plan.discount_reason && (
                  <span className="inline-block mt-2 px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full">
                    {plan.discount_reason}
                  </span>
                )}
                {plan.type === 'integral' && plan.credits && (
                  <p className="text-sm text-gray-500 mt-1">
                    约 {(plan.final_price / 100 / plan.credits).toFixed(2)} 元/次
                  </p>
                )}
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2">
                    <CheckIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-gray-600">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleCTA(plan)}
                className={`w-full py-3 rounded-xl font-medium transition-colors ${
                  plan.is_popular
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                {getCTAText(plan)}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-gray-500 mt-8">
          所有方案均支持7天无理由退款
        </p>
      </div>
    </section>
  );
};

export default Pricing;
