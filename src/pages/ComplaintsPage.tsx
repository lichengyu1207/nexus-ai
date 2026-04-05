import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ExclamationTriangleIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

interface Complaint {
  id: string;
  type: string;
  related_id: string | null;
  description: string;
  status: string;
  admin_reply: string | null;
  created_at: string;
  handled_at: string | null;
  related_log?: {
    action_type: string;
    total_tokens: number;
    cost_integral: number;
    created_at: string;
  };
}

const ComplaintsPage: React.FC = () => {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);
  const [formData, setFormData] = useState({
    type: 'token_refund',
    related_id: '',
    description: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadComplaints = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/complaints');
      setComplaints(response.data.complaints);
    } catch {
      showToast.error('加载申诉列表失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadComplaints();
  }, [loadComplaints]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.description.trim()) {
      showToast.error('请填写申诉描述');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('/complaints', formData);
      showToast.success('申诉已提交');
      setShowForm(false);
      setFormData({ type: 'token_refund', related_id: '', description: '' });
      loadComplaints();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '提交失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewDetail = async (complaintId: string) => {
    try {
      const response = await api.get(`/complaints/${complaintId}`);
      setSelectedComplaint(response.data);
    } catch {
      showToast.error('获取详情失败');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
      case 'resolved':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'rejected':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '处理中',
      resolved: '已解决',
      rejected: '已拒绝',
    };
    return labels[status] || status;
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'resolved':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      token_refund: '积分退还',
      quality: '服务质量',
      other: '其他问题',
    };
    return labels[type] || type;
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return <LoadingCard message="加载申诉列表..." />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ChatBubbleLeftRightIcon className="w-7 h-7 text-primary-600" />
            申诉中心
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            对积分消耗或服务有异议？提交申诉，我们会尽快处理
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <PlusIcon className="w-5 h-5" />
          提交申诉
        </button>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">提交申诉</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  申诉类型
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                >
                  <option value="token_refund">积分退还</option>
                  <option value="quality">服务质量</option>
                  <option value="other">其他问题</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  关联消费记录ID（可选）
                </label>
                <input
                  type="text"
                  value={formData.related_id}
                  onChange={(e) => setFormData({ ...formData, related_id: e.target.value })}
                  placeholder="如需申诉特定消费记录，请填写记录ID"
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  申诉描述 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="请详细描述您的问题..."
                  rows={4}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {isSubmitting ? '提交中...' : '提交申诉'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedComplaint && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">申诉详情</h2>
              <button
                onClick={() => setSelectedComplaint(null)}
                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusClass(selectedComplaint.status)}`}>
                  {getStatusLabel(selectedComplaint.status)}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {getTypeLabel(selectedComplaint.type)}
                </span>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">申诉内容</h3>
                <p className="mt-1 text-gray-900 dark:text-white">{selectedComplaint.description}</p>
              </div>

              {selectedComplaint.related_log && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">关联消费记录</h3>
                  <div className="text-sm space-y-1">
                    <p><span className="text-gray-500">操作类型：</span>{selectedComplaint.related_log.action_type}</p>
                    <p><span className="text-gray-500">Token数量：</span>{selectedComplaint.related_log.total_tokens}</p>
                    <p><span className="text-gray-500">消耗积分：</span>{selectedComplaint.related_log.cost_integral}</p>
                    <p><span className="text-gray-500">创建时间：</span>{formatTime(selectedComplaint.related_log.created_at)}</p>
                  </div>
                </div>
              )}

              {selectedComplaint.admin_reply && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                  <h3 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">管理员回复</h3>
                  <p className="text-blue-900 dark:text-blue-100">{selectedComplaint.admin_reply}</p>
                </div>
              )}

              <div className="text-sm text-gray-500 dark:text-gray-400">
                <p>提交时间：{formatTime(selectedComplaint.created_at)}</p>
                {selectedComplaint.handled_at && (
                  <p>处理时间：{formatTime(selectedComplaint.handled_at)}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {complaints.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <ChatBubbleLeftRightIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">暂无申诉记录</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">如有问题，请点击上方按钮提交申诉</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {complaints.map((complaint) => (
              <div
                key={complaint.id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                onClick={() => handleViewDetail(complaint.id)}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(complaint.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusClass(complaint.status)}`}>
                          {getStatusLabel(complaint.status)}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {getTypeLabel(complaint.type)}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        {formatTime(complaint.created_at)}
                      </span>
                    </div>
                    <p className="mt-2 text-gray-900 dark:text-white line-clamp-2">
                      {complaint.description}
                    </p>
                    {complaint.admin_reply && (
                      <p className="mt-2 text-sm text-blue-600 dark:text-blue-400 line-clamp-1">
                        回复：{complaint.admin_reply}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplaintsPage;
