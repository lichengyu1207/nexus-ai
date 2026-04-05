import React, { useState, useEffect, useCallback } from 'react';
import {
  ClipboardDocumentListIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChartBarIcon,
  UserIcon,
  DocumentTextIcon,
  GiftIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

interface Upload {
  id: string;
  user_id: string;
  username: string;
  email: string;
  data_type_id: string;
  data_type_name: string;
  raw_data: Record<string, any>;
  submitted_at: string;
  status: string;
  reward_tokens: number | null;
  reward_integral: number | null;
  reviewed_at: string | null;
  review_notes: string | null;
  reviewer_name: string | null;
}

interface Stats {
  summary: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
    approval_rate: number;
    total_reward_integral: number;
  };
  by_type: Array<{ type: string; count: number }>;
  daily_trend: Array<{ date: string; count: number }>;
}

const AdminUploadsPage: React.FC = () => {
  const [pendingUploads, setPendingUploads] = useState<Upload[]>([]);
  const [historyUploads, setHistoryUploads] = useState<Upload[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'history' | 'stats'>('pending');
  const [selectedUpload, setSelectedUpload] = useState<Upload | null>(null);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject' | null>(null);
  const [reviewForm, setReviewForm] = useState({
    reward_tokens: 10,
    review_notes: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [historyFilter, setHistoryFilter] = useState({ status: '', data_type: '' });

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [pendingRes, historyRes, statsRes] = await Promise.all([
        api.get('/uploads/admin/pending', { params: { limit: 50 } }),
        api.get('/uploads/admin/history', { params: { limit: 20, ...historyFilter } }),
        api.get('/uploads/admin/stats'),
      ]);
      
      setPendingUploads(pendingRes.data.uploads || []);
      setHistoryUploads(historyRes.data.uploads || []);
      setStats(statsRes.data);
    } catch {
      showToast.error('加载数据失败');
    } finally {
      setIsLoading(false);
    }
  }, [historyFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleReview = async () => {
    if (!selectedUpload || !reviewAction) return;
    
    if (reviewAction === 'approve' && (!reviewForm.reward_tokens || reviewForm.reward_tokens <= 0)) {
      showToast.error('请填写奖励Token数');
      return;
    }
    
    if (reviewAction === 'reject' && !reviewForm.review_notes) {
      showToast.error('请填写拒绝原因');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await api.post(`/uploads/admin/${selectedUpload.id}/review`, {
        action: reviewAction,
        reward_tokens: reviewAction === 'approve' ? reviewForm.reward_tokens : undefined,
        review_notes: reviewForm.review_notes,
      });
      
      showToast.success(reviewAction === 'approve' ? '审核通过，积分已发放' : '已拒绝');
      setSelectedUpload(null);
      setReviewAction(null);
      setReviewForm({ reward_tokens: 10, review_notes: '' });
      loadData();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '操作失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openReviewModal = (upload: Upload, action: 'approve' | 'reject') => {
    setSelectedUpload(upload);
    setReviewAction(action);
    setReviewForm({
      reward_tokens: 10,
      review_notes: '',
    });
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
    };
    return labels[status] || status;
  };

  if (isLoading) {
    return <LoadingCard message="加载中..." />;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ClipboardDocumentListIcon className="w-7 h-7 text-primary-600" />
            上传数据审核
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            审核用户上传的房产数据，通过后自动发放积分奖励
          </p>
        </div>
        {stats && (
          <div className="flex items-center gap-4">
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg px-4 py-2">
              <div className="text-xs text-yellow-600 dark:text-yellow-400">待审核</div>
              <div className="text-xl font-bold text-yellow-700 dark:text-yellow-300">{stats.summary.pending}</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg px-4 py-2">
              <div className="text-xs text-green-600 dark:text-green-400">通过率</div>
              <div className="text-xl font-bold text-green-700 dark:text-green-300">{stats.summary.approval_rate}%</div>
            </div>
          </div>
        )}
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {[
            { key: 'pending', label: '待审核', icon: ClockIcon, count: stats?.summary.pending || 0 },
            { key: 'history', label: '审核历史', icon: DocumentTextIcon },
            { key: 'stats', label: '统计报表', icon: ChartBarIcon },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
              {tab.count > 0 && (
                <span className="bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 text-xs px-2 py-0.5 rounded-full">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'pending' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {pendingUploads.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircleIcon className="w-12 h-12 text-green-300 dark:text-green-600 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">暂无待审核数据</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {pendingUploads.map(upload => (
                <div key={upload.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {upload.data_type_name}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          提交于 {formatTime(upload.submitted_at)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-3">
                        <UserIcon className="w-4 h-4" />
                        {upload.username || upload.email}
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-sm">
                        <pre className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                          {JSON.stringify(upload.raw_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => openReviewModal(upload, 'approve')}
                        className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                      >
                        <CheckCircleIcon className="w-4 h-4" />
                        通过
                      </button>
                      <button
                        onClick={() => openReviewModal(upload, 'reject')}
                        className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                      >
                        <XCircleIcon className="w-4 h-4" />
                        拒绝
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="flex gap-4">
            <select
              value={historyFilter.status}
              onChange={(e) => setHistoryFilter(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
            >
              <option value="">全部状态</option>
              <option value="approved">已通过</option>
              <option value="rejected">已拒绝</option>
            </select>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">用户</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">类型</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">状态</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">奖励</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">审核时间</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400">审核人</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {historyUploads.map(upload => (
                  <tr key={upload.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{upload.username || upload.email}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{upload.data_type_name}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusClass(upload.status)}`}>
                        {getStatusLabel(upload.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {upload.reward_integral ? (
                        <span className="text-green-600 dark:text-green-400">{upload.reward_integral.toFixed(2)} 积分</span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{formatTime(upload.reviewed_at)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{upload.reviewer_name || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'stats' && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="text-sm text-gray-500 dark:text-gray-400">总上传数</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{stats.summary.total}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="text-sm text-gray-500 dark:text-gray-400">已通过</div>
            <div className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">{stats.summary.approved}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="text-sm text-gray-500 dark:text-gray-400">已拒绝</div>
            <div className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">{stats.summary.rejected}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="text-sm text-gray-500 dark:text-gray-400">发放积分</div>
            <div className="text-3xl font-bold text-primary-600 dark:text-primary-400 mt-2">
              {stats.summary.total_reward_integral.toFixed(2)}
            </div>
          </div>

          <div className="col-span-full bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">按类型分布</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {stats.by_type.map(item => (
                <div key={item.type} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400">{item.type}</div>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">{item.count}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {selectedUpload && reviewAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {reviewAction === 'approve' ? '审核通过' : '拒绝数据'}
            </h2>

            <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="text-sm text-gray-500 dark:text-gray-400">数据类型</div>
              <div className="font-medium text-gray-900 dark:text-white">{selectedUpload.data_type_name}</div>
            </div>

            {reviewAction === 'approve' ? (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  奖励Token数 <span className="text-red-500">*</span>
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={reviewForm.reward_tokens}
                    onChange={(e) => setReviewForm(prev => ({ ...prev, reward_tokens: parseInt(e.target.value) || 0 }))}
                    min={1}
                    className="flex-1 px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                  />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    = {(reviewForm.reward_tokens / 100).toFixed(2)} 积分
                  </span>
                </div>
              </div>
            ) : null}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {reviewAction === 'approve' ? '审核备注' : '拒绝原因'} {reviewAction === 'reject' && <span className="text-red-500">*</span>}
              </label>
              <textarea
                value={reviewForm.review_notes}
                onChange={(e) => setReviewForm(prev => ({ ...prev, review_notes: e.target.value }))}
                rows={3}
                placeholder={reviewAction === 'approve' ? '可选填写审核备注' : '请填写拒绝原因'}
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white resize-none"
              />
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setSelectedUpload(null);
                  setReviewAction(null);
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={handleReview}
                disabled={isSubmitting}
                className={`px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                  reviewAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {isSubmitting ? '处理中...' : '确认'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUploadsPage;
