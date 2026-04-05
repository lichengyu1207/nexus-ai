import React, { useState, useEffect } from 'react';

interface Feedback {
  id: string;
  user_id: string;
  username: string;
  email: string;
  type: string;
  title: string;
  content: string;
  status: string;
  admin_reply: string;
  created_at: string;
  replied_at: string;
}

interface Stats {
  total: number;
  pending: number;
  processing: number;
  resolved: number;
  rejected: number;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  resolved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800'
};

const statusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  resolved: '已解决',
  rejected: '已拒绝'
};

const typeLabels: Record<string, string> = {
  bug: 'Bug报告',
  feature: '功能建议',
  question: '问题咨询',
  complaint: '投诉',
  other: '其他'
};

const AdminFeedbackPage: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchFeedbacks();
    fetchStats();
  }, [page, statusFilter, typeFilter]);

  const fetchFeedbacks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      params.append('limit', '20');
      params.append('offset', String((page - 1) * 20));
      if (statusFilter) params.append('status', statusFilter);
      if (typeFilter) params.append('type', typeFilter);
      if (search) params.append('search', search);
      
      const response = await fetch(`http://localhost:8000/api/admin/feedback?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFeedbacks(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch feedbacks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/admin/feedback/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchFeedbacks();
  };

  const openDetail = async (feedback: Feedback) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/feedback/${feedback.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedFeedback(data);
        setNewStatus(data.status);
        setReplyContent(data.admin_reply || '');
        setShowDetailModal(true);
      }
    } catch (error) {
      console.error('Failed to fetch feedback detail:', error);
    }
  };

  const handleReply = async () => {
    if (!selectedFeedback) return;
    
    if (!replyContent.trim()) {
      alert('请输入回复内容');
      return;
    }
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/feedback/${selectedFeedback.id}/reply`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: newStatus,
          admin_reply: replyContent
        })
      });
      
      if (response.ok) {
        alert('回复成功');
        setShowDetailModal(false);
        fetchFeedbacks();
        fetchStats();
      } else {
        const error = await response.json();
        alert(error.detail || '回复失败');
      }
    } catch (error) {
      console.error('Failed to reply:', error);
      alert('回复失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedFeedback) return;
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/feedback/${selectedFeedback.id}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: newStatus,
          admin_reply: replyContent
        })
      });
      
      if (response.ok) {
        alert('状态更新成功');
        setShowDetailModal(false);
        fetchFeedbacks();
        fetchStats();
      } else {
        const error = await response.json();
        alert(error.detail || '更新失败');
      }
    } catch (error) {
      console.error('Failed to update status:', error);
      alert('更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">反馈管理</h1>
      
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter(''); setPage(1); }}>
            <div className="text-sm text-gray-500">总反馈</div>
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
            <div className="text-sm text-gray-500">已解决</div>
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md" onClick={() => { setStatusFilter('rejected'); setPage(1); }}>
            <div className="text-sm text-gray-500">已拒绝</div>
            <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
          </div>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full border rounded px-3 py-2"
              placeholder="搜索反馈内容、标题、用户..."
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2"
          >
            <option value="">全部类型</option>
            <option value="bug">Bug报告</option>
            <option value="feature">功能建议</option>
            <option value="question">问题咨询</option>
            <option value="complaint">投诉</option>
            <option value="other">其他</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2"
          >
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="processing">处理中</option>
            <option value="resolved">已解决</option>
            <option value="rejected">已拒绝</option>
          </select>
          <button
            onClick={handleSearch}
            className="bg-primary text-white px-4 py-2 rounded hover:bg-primary/90"
          >
            搜索
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标题</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center">加载中...</td>
              </tr>
            ) : feedbacks.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">暂无数据</td>
              </tr>
            ) : (
              feedbacks.map((feedback) => (
                <tr key={feedback.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(feedback.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div>{feedback.username || '未知用户'}</div>
                    <div className="text-gray-500 text-xs">{feedback.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {typeLabels[feedback.type] || feedback.type}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="max-w-xs truncate">{feedback.title}</div>
                    <div className="text-gray-500 text-xs truncate max-w-xs">{feedback.content}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${statusColors[feedback.status] || 'bg-gray-100'}`}>
                      {statusLabels[feedback.status] || feedback.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => openDetail(feedback)}
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
              disabled={feedbacks.length < 20}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
      
      {showDetailModal && selectedFeedback && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-bold">反馈详情</h3>
              <button
                onClick={() => setShowDetailModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-500">用户</div>
                  <div>{selectedFeedback.username || '未知'}</div>
                  <div className="text-sm text-gray-500">{selectedFeedback.email}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">类型</div>
                  <div>{typeLabels[selectedFeedback.type] || selectedFeedback.type}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">提交时间</div>
                  <div>{new Date(selectedFeedback.created_at).toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">状态</div>
                  <span className={`px-2 py-1 text-xs rounded-full ${statusColors[selectedFeedback.status]}`}>
                    {statusLabels[selectedFeedback.status]}
                  </span>
                </div>
              </div>
              
              <div>
                <div className="text-sm text-gray-500 mb-1">标题</div>
                <div className="font-medium">{selectedFeedback.title}</div>
              </div>
              
              <div>
                <div className="text-sm text-gray-500 mb-1">内容</div>
                <div className="bg-gray-50 rounded p-3 whitespace-pre-wrap">{selectedFeedback.content}</div>
              </div>
              
              {selectedFeedback.admin_reply && (
                <div>
                  <div className="text-sm text-gray-500 mb-1">管理员回复</div>
                  <div className="bg-blue-50 rounded p-3 whitespace-pre-wrap">{selectedFeedback.admin_reply}</div>
                  {selectedFeedback.replied_at && (
                    <div className="text-xs text-gray-400 mt-1">
                      回复时间: {new Date(selectedFeedback.replied_at).toLocaleString()}
                    </div>
                  )}
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
                  <option value="resolved">已解决</option>
                  <option value="rejected">已拒绝</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">回复内容</label>
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  rows={4}
                  placeholder="输入回复内容..."
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleUpdateStatus}
                disabled={submitting}
                className="px-4 py-2 border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                仅更新状态
              </button>
              <button
                onClick={handleReply}
                disabled={submitting || !replyContent.trim()}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50"
              >
                {submitting ? '处理中...' : '回复并更新'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminFeedbackPage;
