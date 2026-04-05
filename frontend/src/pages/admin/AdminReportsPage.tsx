import React, { useState, useEffect } from 'react';

interface Report {
  id: string;
  reporter_id: string;
  reporter_email: string;
  reported_type: 'report' | 'comment' | 'user';
  reported_id: string;
  reason: string;
  description: string;
  status: 'pending' | 'processing' | 'resolved' | 'rejected';
  admin_notes: string;
  created_at: string;
  processed_at: string;
  processed_by: string;
}

interface ReportStats {
  total: number;
  pending: number;
  processing: number;
  resolved: number;
  rejected: number;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  processing: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

const statusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  resolved: '已处理',
  rejected: '已驳回',
};

const typeLabels: Record<string, string> = {
  report: '分析报告',
  comment: '评论',
  user: '用户',
};

const AdminReportsPage: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<ReportStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [adminNotes, setAdminNotes] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchReports();
    fetchStats();
  }, [page, statusFilter, typeFilter]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      params.append('limit', '20');
      params.append('offset', String((page - 1) * 20));
      if (statusFilter) params.append('status', statusFilter);
      if (typeFilter) params.append('type', typeFilter);

      const response = await fetch(`http://localhost:8000/api/admin/reports?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setReports(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/reports/stats', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const openDetail = (report: Report) => {
    setSelectedReport(report);
    setNewStatus(report.status);
    setAdminNotes(report.admin_notes || '');
    setShowModal(true);
  };

  const handleUpdate = async () => {
    if (!selectedReport) return;

    setProcessing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/reports/${selectedReport.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status: newStatus,
          admin_notes: adminNotes,
        }),
      });

      if (response.ok) {
        alert('更新成功');
        setShowModal(false);
        fetchReports();
        fetchStats();
      } else {
        const error = await response.json();
        alert(error.detail || '更新失败');
      }
    } catch (error) {
      console.error('Failed to update:', error);
      alert('更新失败');
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteContent = async () => {
    if (!selectedReport) return;
    if (!confirm('确定要删除被举报的内容吗？此操作不可撤销！')) return;

    setProcessing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/reports/${selectedReport.id}/delete-content`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          admin_notes: adminNotes,
        }),
      });

      if (response.ok) {
        alert('内容已删除');
        setShowModal(false);
        fetchReports();
        fetchStats();
      } else {
        const error = await response.json();
        alert(error.detail || '删除失败');
      }
    } catch (error) {
      console.error('Failed to delete content:', error);
      alert('删除失败');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">举报管理</h1>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter(''); setPage(1); }}>
            <div className="text-sm text-gray-500">总举报</div>
            <div className="text-2xl font-bold">{stats.total}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter('pending'); setPage(1); }}>
            <div className="text-sm text-gray-500">待处理</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter('processing'); setPage(1); }}>
            <div className="text-sm text-gray-500">处理中</div>
            <div className="text-2xl font-bold text-blue-600">{stats.processing}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter('resolved'); setPage(1); }}>
            <div className="text-sm text-gray-500">已处理</div>
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter('rejected'); setPage(1); }}>
            <div className="text-sm text-gray-500">已驳回</div>
            <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex flex-wrap gap-4">
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2"
          >
            <option value="">全部类型</option>
            <option value="report">分析报告</option>
            <option value="comment">评论</option>
            <option value="user">用户</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2"
          >
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="processing">处理中</option>
            <option value="resolved">已处理</option>
            <option value="rejected">已驳回</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">举报人</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">原因</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center">加载中...</td>
              </tr>
            ) : reports.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">暂无数据</td>
              </tr>
            ) : (
              reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {report.reporter_email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {typeLabels[report.reported_type] || report.reported_type}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {report.reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${statusColors[report.status]}`}>
                      {statusLabels[report.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => openDetail(report)}
                      className="text-primary hover:underline"
                    >
                      查看详情
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        <div className="bg-white px-4 py-3 flex items-center justify-between border-t">
          <div className="text-sm text-gray-500">共 {total} 条记录</div>
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
              disabled={reports.length < 20}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {showModal && selectedReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-bold">举报详情</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-500">举报人</div>
                  <div>{selectedReport.reporter_email}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">举报类型</div>
                  <div>{typeLabels[selectedReport.reported_type]}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">举报时间</div>
                  <div>{new Date(selectedReport.created_at).toLocaleString('zh-CN')}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">被举报ID</div>
                  <div className="font-mono text-sm">{selectedReport.reported_id}</div>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">举报原因</div>
                <div className="bg-gray-50 rounded p-3">{selectedReport.reason}</div>
              </div>

              {selectedReport.description && (
                <div>
                  <div className="text-sm text-gray-500 mb-1">详细描述</div>
                  <div className="bg-gray-50 rounded p-3 whitespace-pre-wrap">{selectedReport.description}</div>
                </div>
              )}

              <hr />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">更新状态</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="pending">待处理</option>
                  <option value="processing">处理中</option>
                  <option value="resolved">已处理</option>
                  <option value="rejected">已驳回</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">处理备注</label>
                <textarea
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  rows={3}
                  placeholder="记录处理过程..."
                />
              </div>
            </div>

            <div className="flex justify-between mt-6">
              <button
                onClick={handleDeleteContent}
                disabled={processing || selectedReport.status === 'resolved'}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                删除被举报内容
              </button>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdate}
                  disabled={processing}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primaryDark disabled:opacity-50"
                >
                  {processing ? '处理中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminReportsPage;
