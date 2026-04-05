import React, { useState } from 'react';
import { SigninPanel } from '../components/Points/SigninPanel';
import { MembershipExchange } from '../components/Points/MembershipExchange';
import { InviteFriends } from '../components/Points/InviteFriends';
import { useAuth } from '../hooks/useAuth';

type TabType = 'signin' | 'membership' | 'invite';

export const PointsCenterPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('signin');

  const tabs: { key: TabType; label: string; icon: string }[] = [
    { key: 'signin', label: '每日签到', icon: '📅' },
    { key: 'membership', label: '兑换会员', icon: '👑' },
    { key: 'invite', label: '邀请好友', icon: '🎁' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">积分中心</h1>
              <p className="text-gray-500 mt-1">获取积分，兑换会员权益</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">当前积分</div>
              <div className="text-3xl font-bold text-blue-600">{user?.integral || 0}</div>
              <div className="text-xs text-gray-400">≈ {(user?.integral || 0) * 100} Token</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="flex border-b">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-1 py-4 px-6 text-center font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-6">
            {activeTab === 'signin' && <SigninPanel />}
            {activeTab === 'membership' && <MembershipExchange />}
            {activeTab === 'invite' && <InviteFriends />}
          </div>
        </div>

        <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
          <h3 className="font-bold text-gray-800 mb-4">积分获取途径</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl">📅</div>
              <div>
                <div className="font-medium text-gray-800">每日签到</div>
                <div className="text-sm text-gray-500">连续签到获得更多积分</div>
                <div className="text-xs text-blue-600 mt-1">最高+200积分/天</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
              <div className="text-2xl">🎁</div>
              <div>
                <div className="font-medium text-gray-800">邀请好友</div>
                <div className="text-sm text-gray-500">邀请好友注册成功</div>
                <div className="text-xs text-green-600 mt-1">+100积分/人</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl">📝</div>
              <div>
                <div className="font-medium text-gray-800">上传数据</div>
                <div className="text-sm text-gray-500">上传房产数据经审核</div>
                <div className="text-xs text-purple-600 mt-1">+10积分/条</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PointsCenterPage;
