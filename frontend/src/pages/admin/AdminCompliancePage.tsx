import React, { useState, useEffect } from 'react';

interface PrivacyLog {
  id: string;
  user_id: string;
  email: string;
  policy_version: string;
  agreed_at: string;
  ip_address: string;
  user_agent: string;
}

const AdminCompliancePage: React.FC = () => {
  const [logs, setLogs] = useState<PrivacyLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [dateRange, setDateRange] = useState({
    start: '',
    end: '',
  });

  useEffect(() => {
    fetchLogs();
  }, [page]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);

      const response = await fetch(`http://localhost:8000/api/admin/compliance/privacy-logs?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchLogs();
  };

  const exportCSV = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);

      const response = await fetch(`http://localhost:8000/api/admin/compliance/export?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `privacy_logs_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
      } else {
        alert('导出失败');
      }
    } catch (error) {
      console.error('Failed to export:', error);
      alert('导出失败');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">合规管理</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-medium mb-4">隐私政策同意记录</h2>
        
        <div className="flex flex-wrap gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">结束日期</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="border rounded px-3 py-2"
            />
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={handleSearch}
              className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
            >
              搜索
            </button>
            <button
              onClick={exportCSV}
              className="border border-gray-300 px-4 py-2 rounded hover:bg-gray-50"
            >
              导出CSV
            </button>
          </div>
        </div>

        <div className="mb-4 text-sm text-gray-500">
          共 {total} 条记录
        </div>

        {loading ? (
          <div className="text-center py-10">加载中...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">政策版本</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP地址</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User Agent</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                      暂无记录
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(log.agreed_at).toLocaleString('zh-CN')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div>{log.email}</div>
                        <div className="text-xs text-gray-400">{log.user_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                          v{log.policy_version}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {log.ip_address}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={log.user_agent}>
                        {log.user_agent}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex justify-between items-center mt-4">
          <div className="text-sm text-gray-500">
            第 {page} 页
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

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium mb-4">数据导出</h2>
        <p className="text-gray-600 mb-4">
          根据GDPR等法规要求，用户有权获取其个人数据副本。您可以通过用户管理页面导出单个用户数据。
        </p>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            <strong>注意：</strong>导出的数据包含敏感信息，请妥善保管，不得泄露给第三方。
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminCompliancePage;
