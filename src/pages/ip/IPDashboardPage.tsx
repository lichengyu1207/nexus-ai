import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface IPDashboard {
  status: string;
  total_referrals: number;
  total_commissions: number;
  pending_commissions: number;
  withdrawn_commissions: number;
  referral_link: string;
}

const IPDashboardPage: React.FC = () => {
  const [dashboard, setDashboard] = useState<IPDashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/ip/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setDashboard(data);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">加载中...</div>;
  }

  if (!dashboard) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <h1 className="text-2xl font-bold mb-4">IP达人计划</h1>
          <p className="text-gray-500 mb-6">您还不是IP达人，请先申请加入</p>
          <Link
            to="/ip-apply"
            className="inline-block bg-primary text-white px-6 py-3 rounded-lg hover:bg-primaryDark"
          >
            立即申请
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">IP达人中心</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-gray-500 text-sm">推广人数</div>
          <div className="text-2xl font-bold">{dashboard.total_referrals}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-gray-500 text-sm">总佣金</div>
          <div className="text-2xl font-bold">¥{dashboard.total_commissions}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-gray-500 text-sm">待结算</div>
          <div className="text-2xl font-bold">¥{dashboard.pending_commissions}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-gray-500 text-sm">已提现</div>
          <div className="text-2xl font-bold">¥{dashboard.withdrawn_commissions}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">推广链接</h2>
        <div className="flex items-center gap-2">
          <input
            type="text"
            readOnly
            value={dashboard.referral_link}
            className="flex-1 border rounded-lg px-4 py-2 bg-gray-50"
          />
          <button
            onClick={() => {
              navigator.clipboard.writeText(dashboard.referral_link);
              alert('已复制到剪贴板');
            }}
            className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primaryDark"
          >
            复制
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">状态</h2>
        <span className={`px-3 py-1 rounded-full text-sm ${
          dashboard.status === 'active' ? 'bg-green-100 text-green-700' :
          dashboard.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
          'bg-red-100 text-red-700'
        }`}>
          {dashboard.status === 'active' ? '已激活' :
           dashboard.status === 'pending' ? '审核中' : '已禁用'}
        </span>
      </div>
    </div>
  );
};

export default IPDashboardPage;
