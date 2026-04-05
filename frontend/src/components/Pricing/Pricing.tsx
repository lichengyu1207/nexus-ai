import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSourceStore } from '../../stores/sourceStore';

interface Plan {
  id: string;
  name: string;
  price: number;
  integral: number;
  description: string;
  features: string[];
  popular?: boolean;
  discount?: number;
}

const Pricing: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const { source } = useSourceStore();

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/plans');
      if (response.ok) {
        const data = await response.json();
        setPlans(data.plans || getDefaultPlans());
      } else {
        setPlans(getDefaultPlans());
      }
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      setPlans(getDefaultPlans());
    } finally {
      setLoading(false);
    }
  };

  const getDefaultPlans = (): Plan[] => [
    {
      id: 'free',
      name: '免费体验',
      price: 0,
      integral: 3,
      description: '新用户注册赠送',
      features: ['3次免费分析', '基础报告', '7天有效期'],
    },
    {
      id: 'basic',
      name: '体验包',
      price: 19,
      integral: 10,
      description: '适合初次体验',
      features: ['10次分析', '完整报告', '30天有效期', '优先客服'],
      popular: true,
    },
    {
      id: 'pro',
      name: '专业包',
      price: 49,
      integral: 30,
      description: '专业用户首选',
      features: ['30次分析', '完整报告', '90天有效期', '专属客服', '批量分析'],
      discount: source === 'laohai' ? 10 : 0,
    },
    {
      id: 'enterprise',
      name: '企业包',
      price: 199,
      integral: 150,
      description: '团队协作必备',
      features: ['150次分析', '完整报告', '365天有效期', '专属客服', '批量分析', 'API接口'],
    },
  ];

  const getDiscountedPrice = (plan: Plan) => {
    if (plan.discount && plan.discount > 0) {
      return plan.price - plan.discount;
    }
    return plan.price;
  };

  if (loading) {
    return (
      <div className="py-12">
        <div className="text-center">加载中...</div>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold mb-4">选择套餐</h2>
        <p className="text-gray-600">灵活的定价方案，满足不同需求</p>
        {source === 'laohai' && (
          <div className="mt-4 inline-block bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full">
            🎉 老骇粉丝专享：专业包立减10元！
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`bg-white rounded-2xl shadow-lg overflow-hidden relative ${
              plan.popular ? 'ring-2 ring-primary transform scale-105' : ''
            }`}
          >
            {plan.popular && (
              <div className="absolute top-0 left-0 right-0 bg-primary text-white text-center py-1 text-sm font-medium">
                最受欢迎
              </div>
            )}
            
            <div className={`p-6 ${plan.popular ? 'pt-10' : ''}`}>
              <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
              <p className="text-gray-500 text-sm mb-4">{plan.description}</p>
              
              <div className="mb-6">
                {plan.discount && plan.discount > 0 ? (
                  <div>
                    <span className="text-gray-400 line-through text-lg">¥{plan.price}</span>
                    <span className="text-3xl font-bold text-primary ml-2">¥{getDiscountedPrice(plan)}</span>
                  </div>
                ) : (
                  <span className="text-3xl font-bold">
                    {plan.price === 0 ? '免费' : `¥${plan.price}`}
                  </span>
                )}
                {plan.price > 0 && (
                  <span className="text-gray-500 text-sm ml-1">
                    / {plan.integral}积分
                  </span>
                )}
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-sm text-gray-600">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              <Link
                to={plan.price === 0 ? '/register' : '/dashboard/recharge'}
                className={`block w-full text-center py-3 rounded-lg font-medium transition-colors ${
                  plan.popular
                    ? 'bg-primary text-white hover:bg-primaryDark'
                    : 'border-2 border-primary text-primary hover:bg-primary hover:text-white'
                }`}
              >
                {plan.price === 0 ? '立即注册' : '立即购买'}
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center text-gray-500 text-sm">
        <p>所有套餐均支持支付宝、微信支付</p>
        <p className="mt-2">如有疑问，请联系客服：fangtan_ai</p>
      </div>
    </div>
  );
};

export default Pricing;
