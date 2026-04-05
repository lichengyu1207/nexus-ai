import React, { useState, useEffect } from 'react';
import {
  ShieldCheckIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface PrivacyLog {
  id: string;
  user_id: string;
  email: string;
  username: string;
  full_name: string;
  policy_version: string;
  policy_title: string;
  ip_address: string;
  user_agent: string;
  agreed_at: string;
}

interface PrivacyStats {
  total_agreements: number;
  unique_users: number;
  by_version: Record<string, number>;
  trend_30_days: Array<{ date: string; count: number }>;
  recent_week: number;
  recent_month: number;
}

const CompliancePage: React.FC = () => {
  const [logs, setLogs] = useState<PrivacyLog[]>([]);
  const [stats, setStats] = useState<PrivacyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  
  const [userId, setUserId] = useState('');
  const [policyVersion, setPolicyVersion] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    loadData();
  }, [page]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [logsRes, statsRes] = await Promise.all([
        fetchLogs(),
        api.get('/admin/compliance/privacy-logs/stats'),
      ]);
      setStats(statsRes.data || {});
    } catch (error) {
      showToast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (policyVersion) params.append('policy_version', policyVersion);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('limit', pageSize.toString());
    params.append('offset', ((page - 1) * pageSize).toString());
    
    const response = await api.get(`/admin/compliance/privacy-logs?${params}`);
    setLogs(response.data.items || []);
    setTotal(response.data.total || 0);
    return response.data;
  };

  const handleSearch = () => {
    setPage(1);
    fetchLogs();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      if (policyVersion) params.append('policy_version', policyVersion);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await api.get(`/admin/compliance/privacy-logs/export?${params}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `privacy_logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showToast.success('导出成功');
    } catch (error) {
      showToast.error('导出失败');
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">合规管理</h1>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
          {exporting ? '导出中...' : '导出 CSV'}
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <ShieldCheckIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">总同意记录</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{stats.total_agreements}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">同意用户数</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{stats.unique_users}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">近7天新增</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">{stats.recent_week}</p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">近30天新增</p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">{stats.recent_month}</p>
          </div>
        </div>
      )}

      {stats?.by_version && Object.keys(stats.by_version).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">版本分布</h2>
          <div className="space-y-3">
            {Object.entries(stats.by_version).map(([version, count]) => {
              const total = Object.values(stats.by_version).reduce((a, b) => a + b, 0);
              const percentage = total > 0 ? (count / total) * 100 : 0;
              return (
                <div key={version}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">版本 {version}</span>
                    <span className="text-gray-900 dark:text-white font-medium">{count}</span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4 flex-wrap">
            <FunnelIcon className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="用户ID"
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm w-40"
            />
            <input
              type="text"
              value={policyVersion}
              onChange={(e) => setPolicyVersion(e.target.value)}
              placeholder="政策版本"
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm w-32"
            />
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
            />
            <span className="text-gray-400">至</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
            >
              搜索
            </button>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无记录</div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">用户</th>
                  <th className="px-4 py-3 text-left font-medium">政策版本</th>
                  <th className="px-4 py-3 text-left font-medium">IP地址</th>
                  <th className="px-4 py-3 text-left font-medium">同意时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {log.full_name || log.username || log.email || log.user_id}
                        </p>
                        {log.email && (
                          <p className="text-xs text-gray-500">{log.email}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium">{log.policy_version}</p>
                        {log.policy_title && (
                          <p className="text-xs text-gray-500">{log.policy_title}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{log.ip_address || '-'}</td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(log.agreed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50"
                >
                  上一页
                </button>
                <span className="text-sm text-gray-500">
                  第 {page} / {totalPages} 页（共 {total} 条）
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CompliancePage;
