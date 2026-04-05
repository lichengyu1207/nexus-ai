import React, { useState, useEffect } from 'react';

interface IntegralLog {
  id: string;
  user_id: string;
  username: string;
  email: string;
  change: number;
  balance_after: number;
  reason: string;
  admin_note: string;
  created_at: string;
}

interface Stats {
  total_issued: number;
  total_consumed: number;
  current_total: number;
}

const AdminIntegralPage: React.FC = () => {
  const [logs, setLogs] = useState<IntegralLog[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchEmail, setSearchEmail] = useState('');
  
  // 调整积分表单
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [adjustEmail, setAdjustEmail] = useState('');
  const [adjustAmount, setAdjustAmount] = useState(0);
  const [adjustReason, setAdjustReason] = useState('');
  const [adjusting, setAdjusting] = useState(false);

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [logsRes, statsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/admin/integral/logs?page=${page}&page_size=20`, { headers }),
        fetch('http://localhost:8000/api/admin/integral/stats', { headers })
      ]);
      
      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(data.logs || []);
        setTotal(data.total || 0);
      }
      
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdjust = async () => {
    if (!adjustEmail || adjustAmount === 0 || !adjustReason) {
      alert('请填写完整信息');
      return;
    }
    
    setAdjusting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/integral/adjust', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: adjustEmail,
          amount: adjustAmount,
          reason: adjustReason
        })
      });
      
      if (response.ok) {
        alert('积分调整成功');
        setShowAdjustModal(false);
        setAdjustEmail('');
        setAdjustAmount(0);
        setAdjustReason('');
        fetchData();
      } else {
        const error = await response.json();
        alert(error.detail || '调整失败');
      }
    } catch (error) {
      console.error('Failed to adjust:', error);
      alert('调整失败');
    } finally {
      setAdjusting(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">积分管理</h1>
      
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">总发放积分</div>
          <div className="text-2xl font-bold text-green-600">{stats?.total_issued || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">总消耗积分</div>
          <div className="text-2xl font-bold text-red-600">{stats?.total_consumed || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">当前总积分</div>
          <div className="text-2xl font-bold text-blue-600">{stats?.current_total || 0}</div>
        </div>
      </div>
      
      {/* 操作按钮 */}
      <div className="mb-4">
        <button
          onClick={() => setShowAdjustModal(true)}
          className="bg-primary text-white px-4 py-2 rounded hover:bg-primary/90"
        >
          调整积分
        </button>
      </div>
      
      {/* 积分日志表格 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">变动</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">余额</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">原因</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center">加载中...</td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">暂无数据</td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div>{log.username || log.email}</div>
                    <div className="text-gray-500 text-xs">{log.email}</div>
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
                    {log.admin_note && <div className="text-xs text-gray-400">备注: {log.admin_note}</div>}
                  </td>
                </tr>
              ))
            )}
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
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={logs.length < 20}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
      
      {/* 调整积分弹窗 */}
      {showAdjustModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">调整积分</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用户邮箱</label>
                <input
                  type="email"
                  value={adjustEmail}
                  onChange={(e) => setAdjustEmail(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  placeholder="输入用户邮箱"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">调整数量</label>
                <input
                  type="number"
                  value={adjustAmount}
                  onChange={(e) => setAdjustAmount(parseInt(e.target.value) || 0)}
                  className="w-full border rounded px-3 py-2"
                  placeholder="正数为增加，负数为减少"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">原因</label>
                <textarea
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  rows={3}
                  placeholder="请输入调整原因"
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowAdjustModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleAdjust}
                disabled={adjusting}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50"
              >
                {adjusting ? '处理中...' : '确认调整'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminIntegralPage;
