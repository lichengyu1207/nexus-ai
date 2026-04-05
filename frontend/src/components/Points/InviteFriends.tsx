import React, { useState, useEffect } from 'react';
import { pointsApi, InviteStats } from '../../api/points';

export const InviteFriends: React.FC = () => {
  const [stats, setStats] = useState<InviteStats | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await pointsApi.getInviteStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load invite stats:', error);
    }
  };

  const handleCopy = async () => {
    if (!stats?.invite_link) return;
    
    try {
      await navigator.clipboard.writeText(stats.invite_link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 max-w-lg mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">邀请好友</h2>
        <p className="text-gray-500">邀请好友注册，双方都可获得积分奖励</p>
      </div>

      <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg p-4 mb-6 text-white">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-3xl font-bold">{stats?.invited_count || 0}</div>
            <div className="text-sm opacity-80">已邀请人数</div>
          </div>
          <div>
            <div className="text-3xl font-bold">{stats?.total_reward || 0}</div>
            <div className="text-sm opacity-80">累计获得积分</div>
          </div>
        </div>
      </div>

      {stats?.invite_code ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              您的专属邀请码
            </label>
            <div className="flex">
              <input
                type="text"
                value={stats.invite_code}
                readOnly
                className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg bg-gray-50"
              />
              <button
                onClick={() => navigator.clipboard.writeText(stats.invite_code || '')}
                className="px-4 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-lg hover:bg-gray-200"
              >
                复制
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              邀请链接
            </label>
            <div className="flex">
              <input
                type="text"
                value={stats.invite_link || ''}
                readOnly
                className="flex-1 px-4 py-2 border border-gray-300 rounded-l-lg bg-gray-50 text-sm truncate"
              />
              <button
                onClick={handleCopy}
                className={`px-4 py-2 border border-l-0 border-gray-300 rounded-r-lg ${
                  copied ? 'bg-green-500 text-white' : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {copied ? '已复制' : '复制'}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={async () => {
            await pointsApi.createInvite();
            loadStats();
          }}
          className="w-full py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600"
        >
          生成邀请码
        </button>
      )}

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-800 mb-2">邀请规则</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• 分享邀请链接给好友</li>
          <li>• 好友通过链接注册成功后，您获得 <span className="text-blue-600 font-bold">100积分</span></li>
          <li>• 好友也可获得 <span className="text-blue-600 font-bold">50积分</span> 奖励</li>
          <li>• 邀请人数无上限，多邀多得</li>
        </ul>
      </div>
    </div>
  );
};

export default InviteFriends;
