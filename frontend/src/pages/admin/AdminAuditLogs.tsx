import React, { useState, useEffect } from 'react';

interface AuditLog {
  id: string;
  user_id: string;
  username: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  email?: string;
  full_name?: string;
}

interface AuditStats {
  action_stats: { action_type: string; count: number }[];
  status_stats: { status: string; count: number }[];
  daily_stats: { date: string; count: number }[];
  active_users: { username: string; count: number }[];
}

const AdminAuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [actionType, setActionType] = useState('');
  const [actionTypes, setActionTypes] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'logs' | 'stats'>('logs');

  useEffect(() => {
    fetchLogs();
    fetchActionTypes();
  }, [page, rowsPerPage, actionType]);

  useEffect(() => {
    if (activeTab === 'stats') {
      fetchStats();
    }
  }, [activeTab]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const offset = page * rowsPerPage;
      let url = `http://localhost:8000/api/audit/logs?limit=${rowsPerPage}&offset=${offset}`;
      if (actionType) {
        url += `&action_type=${actionType}`;
      }
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const result = await res.json();
        setLogs(result.logs || []);
        setTotal(result.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/audit/stats?days=7', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const result = await res.json();
        setStats(result);
      }
    } catch (error) {
      console.error('Failed to fetch audit stats:', error);
    }
  };

  const fetchActionTypes = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/audit/actions', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const result = await res.json();
        setActionTypes(result.action_types || []);
      }
    } catch (error) {
      console.error('Failed to fetch action types:', error);
    }
  };

  const getActionColor = (action: string): string => {
    const colors: Record<string, string> = {
      login: 'bg-green-100 text-green-700',
      logout: 'bg-gray-100 text-gray-700',
      register: 'bg-blue-100 text-blue-700',
      create: 'bg-blue-100 text-blue-700',
      update: 'bg-yellow-100 text-yellow-700',
      delete: 'bg-red-100 text-red-700',
      view: 'bg-purple-100 text-purple-700',
      export: 'bg-indigo-100 text-indigo-700',
    };
    return colors[action.toLowerCase()] || 'bg-gray-100 text-gray-700';
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">📜 审计日志</h1>

      {/* 标签切换 */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('logs')}
          className={`px-4 py-2 rounded-lg font-medium ${
            activeTab === 'logs'
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          日志列表
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-4 py-2 rounded-lg font-medium ${
            activeTab === 'stats'
              ? 'bg-primary text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          统计分析
        </button>
      </div>

      {activeTab === 'logs' ? (
        <div className="bg-white rounded-lg shadow">
          {/* 筛选器 */}
          <div className="p-4 border-b flex gap-4">
            <select
              value={actionType}
              onChange={(e) => {
                setActionType(e.target.value);
                setPage(0);
              }}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="">全部操作</option>
              {actionTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* 日志列表 */}
          {loading ? (
            <div className="flex justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left py-3 px-4 font-medium">时间</th>
                      <th className="text-left py-3 px-4 font-medium">用户</th>
                      <th className="text-left py-3 px-4 font-medium">操作</th>
                      <th className="text-left py-3 px-4 font-medium">资源</th>
                      <th className="text-left py-3 px-4 font-medium">IP地址</th>
                      <th className="text-left py-3 px-4 font-medium">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 text-gray-600">
                          {formatDate(log.created_at)}
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            <p className="font-medium">{log.username || log.email || '-'}</p>
                            {log.full_name && (
                              <p className="text-xs text-gray-500">{log.full_name}</p>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-xs ${getActionColor(log.action)}`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-600">
                          {log.resource_type && (
                            <span>
                              {log.resource_type}
                              {log.resource_id && `: ${log.resource_id.substring(0, 8)}...`}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-gray-600">
                          {log.ip_address || '-'}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700">
                            成功
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* 分页 */}
              <div className="p-4 border-t flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">每页行数:</span>
                  <select
                    value={rowsPerPage}
                    onChange={(e) => {
                      setRowsPerPage(parseInt(e.target.value, 10));
                      setPage(0);
                    }}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">
                    {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, total)} 共 {total} 条
                  </span>
                  <button
                    onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={(page + 1) * rowsPerPage >= total}
                    className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      ) : (
        /* 统计分析 */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 操作类型统计 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">操作类型分布</h3>
            {stats?.action_stats ? (
              <div className="space-y-3">
                {stats.action_stats.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm">{item.action_type}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary rounded-full h-2"
                          style={{
                            width: `${Math.min(100, (item.count / (stats.action_stats[0]?.count || 1)) * 100)}%`
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600 w-12 text-right">{item.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">加载中...</p>
            )}
          </div>

          {/* 活跃用户 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium mb-4">活跃用户 (Top 10)</h3>
            {stats?.active_users ? (
              <div className="space-y-3">
                {stats.active_users.map((user, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm">{user.username}</span>
                    <span className="text-sm text-gray-600">{user.count} 次操作</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">加载中...</p>
            )}
          </div>

          {/* 每日统计 */}
          <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
            <h3 className="text-lg font-medium mb-4">每日操作统计 (近7天)</h3>
            {stats?.daily_stats ? (
              <div className="flex items-end gap-2 h-40">
                {stats.daily_stats.map((item, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="bg-primary rounded-t w-full"
                      style={{
                        height: `${Math.max(10, (item.count / Math.max(...stats.daily_stats.map(d => d.count))) * 100)}%`
                      }}
                    ></div>
                    <span className="text-xs text-gray-500 mt-2">{item.date.slice(5)}</span>
                    <span className="text-xs text-gray-600">{item.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">加载中...</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAuditLogs;
