import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface IntegralLog {
  id: string;
  change: number;
  balance_after: number;
  reason: string;
  created_at: string;
}

interface UserInfo {
  id: string;
  email: string;
  username: string;
  integral: number;
  membership_level: string;
  membership_expires: string | null;
}

const IntegralPage: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [logs, setLogs] = useState<IntegralLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [userRes, logsRes] = await Promise.all([
        fetch('http://localhost:8000/api/auth/me', { headers }),
        fetch(`http://localhost:8000/api/integral/logs?page=${page}&page_size=20`, { headers })
      ]);
      
      if (userRes.ok) {
        const userData = await userRes.json();
        setUser(userData);
      }
      
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setLogs(logsData.logs || []);
        setTotal(logsData.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  if (loading && !user) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">我的积分</h1>
      
      {/* 积分概览卡片 */}
      <div className="bg-gradient-to-r from-primary to-blue-600 rounded-lg shadow-lg p-6 mb-6 text-white">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-white/80 text-sm">当前积分余额</p>
            <p className="text-4xl font-bold mt-1">{user?.integral || 0}</p>
          </div>
          <div className="text-right">
            <div className="bg-white/20 rounded-full px-4 py-2 inline-block">
              <span className="text-sm">{user?.membership_level || '免费用户'}</span>
            </div>
            {user?.membership_expires && (
              <p className="text-sm text-white/70 mt-2">
                有效期至 {new Date(user.membership_expires).toLocaleDateString('zh-CN')}
              </p>
            )}
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-white/20">
          <Link
            to="/dashboard/recharge"
            className="bg-white text-primary px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
          >
            立即充值
          </Link>
        </div>
      </div>
      
      {/* 积分说明 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-medium mb-4">积分说明</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl mb-2">🏠</div>
            <h3 className="font-medium">房产分析</h3>
            <p className="text-sm text-gray-500">每次分析消耗 1 积分</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl mb-2">📊</div>
            <h3 className="font-medium">对比分析</h3>
            <p className="text-sm text-gray-500">每次对比消耗 2 积分</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-2xl mb-2">🎁</div>
            <h3 className="font-medium">新用户赠送</h3>
            <p className="text-sm text-gray-500">注册即送 3 积分</p>
          </div>
        </div>
      </div>
      
      {/* 积分变动记录 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-medium">积分变动记录</h2>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无积分记录</div>
        ) : (
          <>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">变动</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">余额</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">原因</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={log.change > 0 ? 'text-green-600' : 'text-red-600'}>
                        {log.change > 0 ? '+' : ''}{log.change}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.balance_after}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {log.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {/* 分页 */}
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t">
              <div className="text-sm text-gray-500">
                共 {total} 条记录
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  上一页
                </button>
                <span className="px-3 py-1">第 {page} 页</span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={logs.length < 20}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  下一页
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default IntegralPage;
