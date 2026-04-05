import React, { useState, useEffect } from 'react';
import {
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  CheckCircleIcon,
  ClockIcon,
  XMarkIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

type TabType = 'feedback' | 'reports';

interface Feedback {
  id: string;
  user_id: string;
  type: string;
  title: string;
  content: string;
  status: string;
  admin_reply: string;
  created_at: string;
  email: string;
  full_name: string;
  username: string;
}

interface Report {
  id: string;
  reporter_id: string;
  reported_type: string;
  reported_id: string;
  reason: string;
  details: string;
  status: string;
  admin_notes: string;
  action_taken: string;
  created_at: string;
  reporter_email: string;
  reporter_name: string;
}

const FEEDBACK_STATUS: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  processing: { label: '处理中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  rejected: { label: '已拒绝', color: 'bg-gray-100 text-gray-700' },
};

const REPORT_STATUS: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  investigating: { label: '调查中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  dismissed: { label: '已驳回', color: 'bg-gray-100 text-gray-700' },
};

const FEEDBACK_TYPES: Record<string, string> = {
  feedback: '功能反馈',
  suggestion: '建议',
  bug: '问题报告',
  complaint: '投诉',
};

const REPORT_REASONS: Record<string, string> = {
  inappropriate: '不当内容',
  spam: '垃圾信息',
  fraud: '涉嫌欺诈',
  copyright: '版权问题',
  privacy: '隐私侵犯',
  other: '其他原因',
};

const UserCommunicationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('feedback');
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [replyContent, setReplyContent] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab, statusFilter, typeFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'feedback') {
        const params = new URLSearchParams();
        if (statusFilter) params.append('status', statusFilter);
        if (typeFilter) params.append('type', typeFilter);
        const [listRes, statsRes] = await Promise.all([
          api.get(`/admin/feedback?${params}`),
          api.get('/admin/feedback/stats'),
        ]);
        setFeedbacks(listRes.data.items || []);
        setStats(statsRes.data || {});
      } else {
        const params = new URLSearchParams();
        if (statusFilter) params.append('status', statusFilter);
        if (typeFilter) params.append('reported_type', typeFilter);
        const [listRes, statsRes] = await Promise.all([
          api.get(`/admin/reports?${params}`),
          api.get('/admin/reports/stats'),
        ]);
        setReports(listRes.data.items || []);
        setStats(statsRes.data || {});
      }
    } catch (error) {
      showToast.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReplyFeedback = async () => {
    if (!selectedItem || !replyContent.trim()) {
      showToast.error('请填写回复内容');
      return;
    }

    setSubmitting(true);
    try {
      await api.put(`/admin/feedback/${selectedItem.id}`, {
        status: newStatus || selectedItem.status,
        admin_reply: replyContent,
      });
      showToast.success('回复成功');
      setSelectedItem(null);
      setReplyContent('');
      fetchData();
    } catch (error) {
      showToast.error('回复失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleProcessReport = async () => {
    if (!selectedItem) return;

    setSubmitting(true);
    try {
      await api.put(`/admin/reports/${selectedItem.id}`, {
        status: newStatus || selectedItem.status,
        admin_notes: replyContent || undefined,
        action_taken: undefined,
      });
      showToast.success('处理成功');
      setSelectedItem(null);
      setReplyContent('');
      fetchData();
    } catch (error) {
      showToast.error('处理失败');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">用户沟通管理</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">总数</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total || 0}</p>
            </div>
            {activeTab === 'feedback' ? (
              <ChatBubbleLeftRightIcon className="w-8 h-8 text-primary-500" />
            ) : (
              <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">待处理</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.pending || 0}</p>
            </div>
            <ClockIcon className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">已处理</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.by_status?.resolved || stats.by_status?.dismissed || 0}
              </p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">本周新增</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.recent_week || '-'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          <button
            onClick={() => { setActiveTab('feedback'); setStatusFilter(''); setTypeFilter(''); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'feedback'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            💬 用户反馈
          </button>
          <button
            onClick={() => { setActiveTab('reports'); setStatusFilter(''); setTypeFilter(''); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'reports'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            🚨 内容举报
          </button>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <FunnelIcon className="w-5 h-5 text-gray-400" />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">全部状态</option>
          {activeTab === 'feedback' ? (
            Object.entries(FEEDBACK_STATUS).map(([key, { label }]) => (
              <option key={key} value={key}>{label}</option>
            ))
          ) : (
            Object.entries(REPORT_STATUS).map(([key, { label }]) => (
              <option key={key} value={key}>{label}</option>
            ))
          )}
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">全部类型</option>
          {activeTab === 'feedback' ? (
            Object.entries(FEEDBACK_TYPES).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))
          ) : (
            <>
              <option value="report">分析报告</option>
              <option value="comment">评论</option>
              <option value="user">用户</option>
            </>
          )}
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : activeTab === 'feedback' ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left font-medium">用户</th>
                <th className="px-4 py-3 text-left font-medium">类型</th>
                <th className="px-4 py-3 text-left font-medium">标题</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-left font-medium">时间</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {feedbacks.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3">{item.full_name || item.username || item.email}</td>
                  <td className="px-4 py-3">{FEEDBACK_TYPES[item.type] || item.type}</td>
                  <td className="px-4 py-3 max-w-xs truncate">{item.title || item.content.slice(0, 30)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${FEEDBACK_STATUS[item.status]?.color}`}>
                      {FEEDBACK_STATUS[item.status]?.label || item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => { setSelectedItem(item); setNewStatus(item.status); }}
                      className="text-primary-600 hover:text-primary-700"
                    >
                      查看/回复
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left font-medium">举报人</th>
                <th className="px-4 py-3 text-left font-medium">类型</th>
                <th className="px-4 py-3 text-left font-medium">原因</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-left font-medium">时间</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {reports.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3">{item.reporter_name || item.reporter_email}</td>
                  <td className="px-4 py-3">
                    {item.reported_type === 'report' ? '报告' : 
                     item.reported_type === 'comment' ? '评论' : '用户'}
                  </td>
                  <td className="px-4 py-3">{REPORT_REASONS[item.reason] || item.reason}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${REPORT_STATUS[item.status]?.color}`}>
                      {REPORT_STATUS[item.status]?.label || item.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{formatDate(item.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => { setSelectedItem(item); setNewStatus(item.status); }}
                      className="text-primary-600 hover:text-primary-700"
                    >
                      处理
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/30" onClick={() => setSelectedItem(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {activeTab === 'feedback' ? '反馈详情' : '举报详情'}
              </h3>
              <button onClick={() => setSelectedItem(null)} className="p-1 hover:bg-gray-100 rounded">
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">提交者</p>
                  <p className="font-medium">
                    {activeTab === 'feedback' 
                      ? (selectedItem.full_name || selectedItem.username || selectedItem.email)
                      : (selectedItem.reporter_name || selectedItem.reporter_email)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">提交时间</p>
                  <p className="font-medium">{formatDate(selectedItem.created_at)}</p>
                </div>
              </div>

              {activeTab === 'feedback' ? (
                <>
                  <div>
                    <p className="text-gray-500 text-sm">标题</p>
                    <p className="font-medium">{selectedItem.title || '无标题'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-sm">内容</p>
                    <p className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">{selectedItem.content}</p>
                  </div>
                  {selectedItem.admin_reply && (
                    <div>
                      <p className="text-gray-500 text-sm">管理员回复</p>
                      <p className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">{selectedItem.admin_reply}</p>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div>
                    <p className="text-gray-500 text-sm">举报原因</p>
                    <p className="font-medium">{REPORT_REASONS[selectedItem.reason] || selectedItem.reason}</p>
                  </div>
                  {selectedItem.details && (
                    <div>
                      <p className="text-gray-500 text-sm">补充说明</p>
                      <p className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">{selectedItem.details}</p>
                    </div>
                  )}
                  {selectedItem.admin_notes && (
                    <div>
                      <p className="text-gray-500 text-sm">处理备注</p>
                      <p className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">{selectedItem.admin_notes}</p>
                    </div>
                  )}
                </>
              )}

              <div>
                <p className="text-gray-500 text-sm mb-1">更新状态</p>
                <div className="flex flex-wrap gap-2">
                  {activeTab === 'feedback' ? (
                    Object.entries(FEEDBACK_STATUS).map(([key, { label, color }]) => (
                      <button
                        key={key}
                        onClick={() => setNewStatus(key)}
                        className={`px-3 py-1.5 rounded text-sm ${
                          newStatus === key ? `${color} ring-2 ring-offset-1` : 'bg-gray-100 dark:bg-gray-700'
                        }`}
                      >
                        {label}
                      </button>
                    ))
                  ) : (
                    Object.entries(REPORT_STATUS).map(([key, { label, color }]) => (
                      <button
                        key={key}
                        onClick={() => setNewStatus(key)}
                        className={`px-3 py-1.5 rounded text-sm ${
                          newStatus === key ? `${color} ring-2 ring-offset-1` : 'bg-gray-100 dark:bg-gray-700'
                        }`}
                      >
                        {label}
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div>
                <p className="text-gray-500 text-sm mb-1">
                  {activeTab === 'feedback' ? '回复内容' : '处理备注'}
                </p>
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 resize-none"
                  rows={4}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setSelectedItem(null)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={activeTab === 'feedback' ? handleReplyFeedback : handleProcessReport}
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <PaperAirplaneIcon className="w-4 h-4" />
                {submitting ? '提交中...' : '提交'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserCommunicationPage;
