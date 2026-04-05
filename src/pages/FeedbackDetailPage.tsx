import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, ChatBubbleLeftRightIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

const FEEDBACK_TYPES: Record<string, string> = {
  feedback: '功能反馈',
  suggestion: '建议',
  bug: '问题报告',
  complaint: '投诉',
};

const FEEDBACK_STATUS: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  processing: { label: '处理中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  rejected: { label: '已拒绝', color: 'bg-gray-100 text-gray-700' },
};

const FeedbackDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadFeedback();
    }
  }, [id]);

  const loadFeedback = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/feedback/${id}`);
      setFeedback(response.data);
    } catch (error) {
      showToast.error('获取反馈详情失败');
      navigate('/feedback');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!feedback) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        <div className="text-center text-gray-500">
          <p>反馈不存在</p>
        </div>
      </div>
    );
  }

  const statusConfig = FEEDBACK_STATUS[feedback.status] || FEEDBACK_STATUS.pending;

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <button
        onClick={() => navigate('/feedback')}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-6"
      >
        <ArrowLeftIcon className="w-4 h-4" />
        返回反馈列表
      </button>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                {feedback.title || '反馈详情'}
              </h1>
              <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                <span>{FEEDBACK_TYPES[feedback.type] || feedback.type}</span>
                <span>·</span>
                <span>{formatDate(feedback.created_at)}</span>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm ${statusConfig.color}`}>
              {statusConfig.label}
            </span>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">反馈内容</h3>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
              <p className="whitespace-pre-wrap text-gray-900 dark:text-white">{feedback.content}</p>
            </div>
          </div>

          {feedback.attachments && feedback.attachments.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">附件</h3>
              <div className="grid grid-cols-4 gap-3">
                {feedback.attachments.map((url: string, index: number) => (
                  <a
                    key={index}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <img
                      src={url}
                      alt={`附件 ${index + 1}`}
                      className="w-full h-24 object-cover rounded-lg hover:opacity-80 transition-opacity"
                    />
                  </a>
                ))}
              </div>
            </div>
          )}

          {feedback.admin_reply && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                <div className="flex items-center gap-2">
                  <ChatBubbleLeftRightIcon className="w-4 h-4" />
                  管理员回复
                </div>
              </h3>
              <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-xl p-4">
                <p className="whitespace-pre-wrap text-blue-900 dark:text-blue-100">
                  {feedback.admin_reply}
                </p>
                {feedback.replied_at && (
                  <p className="text-xs text-blue-500 mt-2">
                    回复时间：{formatDate(feedback.replied_at)}
                  </p>
                )}
              </div>
            </div>
          )}

          {feedback.status === 'resolved' && (
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <CheckCircleIcon className="w-5 h-5" />
              <span>此反馈已处理完成</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeedbackDetailPage;
