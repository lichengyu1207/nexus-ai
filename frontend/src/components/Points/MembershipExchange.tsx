import React, { useState, useEffect } from 'react';
import { pointsApi, MembershipPrices, MembershipStatus } from '../../api/points';
import { useAuth } from '../../hooks/useAuth';

interface MembershipCardProps {
  type: string;
  info: { price: number; days: number; name: string };
  currentIntegral: number;
  currentMembership?: MembershipStatus;
  onExchange: (type: string) => void;
  loading: boolean;
}

const MembershipCard: React.FC<MembershipCardProps> = ({
  type,
  info,
  currentIntegral,
  currentMembership,
  onExchange,
  loading,
}) => {
  const canAfford = currentIntegral >= info.price;
  const isActive = currentMembership?.membership_type === type && currentMembership?.is_active;

  const features = {
    experience: ['无限次分析', '报告导出', '基础咨询', '3天有效期'],
    monthly: ['体验会员权益', '高级数据', '实时行情', '30天有效期'],
    quarterly: ['月度会员权益', 'VIP咨询通道', '优先支持', '90天有效期'],
    annual: ['季度会员权益', '专属顾问', '定制报告', '365天有效期'],
  };

  return (
    <div
      className={`bg-white rounded-xl shadow-lg p-6 border-2 transition-all ${
        isActive ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-100 hover:border-blue-200'
      }`}
    >
      {isActive && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span className="bg-blue-500 text-white text-xs px-3 py-1 rounded-full">
            当前会员
          </span>
        </div>
      )}

      <div className="text-center mb-4">
        <h3 className="text-xl font-bold text-gray-800">{info.name}</h3>
        <div className="mt-2">
          <span className="text-3xl font-bold text-blue-600">{info.price}</span>
          <span className="text-gray-500 ml-1">积分</span>
        </div>
        <p className="text-sm text-gray-500 mt-1">{info.days}天有效期</p>
      </div>

      <ul className="space-y-2 mb-6">
        {features[type as keyof typeof features]?.map((feature, index) => (
          <li key={index} className="flex items-center text-sm text-gray-600">
            <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            {feature}
          </li>
        ))}
      </ul>

      <button
        onClick={() => onExchange(type)}
        disabled={loading || !canAfford || isActive}
        className={`w-full py-2 rounded-lg font-medium transition-colors ${
          isActive
            ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
            : canAfford
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}
      >
        {isActive ? '当前会员' : canAfford ? '立即兑换' : '积分不足'}
      </button>
    </div>
  );
};

export const MembershipExchange: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [prices, setPrices] = useState<MembershipPrices | null>(null);
  const [membership, setMembership] = useState<MembershipStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [pricesData, membershipData] = await Promise.all([
        pointsApi.getMembershipPrices(),
        pointsApi.getMembershipStatus(),
      ]);
      setPrices(pricesData);
      setMembership(membershipData);
    } catch (error) {
      console.error('Failed to load membership data:', error);
    }
  };

  const handleExchange = async (type: string) => {
    if (!prices || loading) return;

    const info = prices[type];
    if (!info || (user?.integral || 0) < info.price) return;

    setLoading(true);
    setMessage(null);

    try {
      await pointsApi.exchangeMembership(type);
      setMessage({ type: 'success', text: `兑换成功！${info.name}已生效` });
      await Promise.all([loadData(), refreshUser?.()]);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      setMessage({ type: 'error', text: err.response?.data?.detail || '兑换失败' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">积分兑换会员</h2>
        <p className="text-gray-500">使用积分兑换会员，享受更多权益</p>
        <div className="mt-4 inline-flex items-center bg-blue-50 px-4 py-2 rounded-lg">
          <span className="text-gray-600">当前积分：</span>
          <span className="text-2xl font-bold text-blue-600 ml-2">{user?.integral || 0}</span>
        </div>
      </div>

      {message && (
        <div
          className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}
        >
          {message.text}
        </div>
      )}

      {membership?.is_active && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex justify-between items-center">
            <div>
              <span className="text-gray-600">当前会员：</span>
              <span className="font-bold text-blue-600 ml-2">
                {membership.membership_type === 'experience' ? '体验会员' :
                 membership.membership_type === 'monthly' ? '月度会员' :
                 membership.membership_type === 'quarterly' ? '季度会员' :
                 membership.membership_type === 'annual' ? '年度会员' : '免费用户'}
              </span>
            </div>
            <div className="text-gray-600">
              剩余 <span className="font-bold text-blue-600">{membership.remaining_days}</span> 天
            </div>
          </div>
        </div>
      )}

      {prices && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(prices).map(([type, info]) => (
            <MembershipCard
              key={type}
              type={type}
              info={info}
              currentIntegral={user?.integral || 0}
              currentMembership={membership || undefined}
              onExchange={handleExchange}
              loading={loading}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MembershipExchange;
