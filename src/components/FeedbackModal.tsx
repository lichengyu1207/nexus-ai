import React, { useState, useEffect } from 'react';
import {
  XMarkIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  CheckCircleIcon,
  ChatBubbleLeftRightIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpSolidIcon, HandThumbDownIcon as HandThumbDownSolidIcon } from '@heroicons/react/24/solid';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface FeedbackModalProps {
  reportId: string;
  onClose: () => void;
  onSubmitted?: () => void;
}

interface IssueCategory {
  key: string;
  label: string;
}

const ISSUE_CATEGORIES: IssueCategory[] = [
  { key: 'price_accuracy', label: '价格准确性' },
  { key: 'area_estimate', label: '面积估算' },
  { key: 'location_info', label: '周边配套信息' },
  { key: 'market_analysis', label: '市场分析' },
  { key: 'investment_advice', label: '投资建议' },
  { key: 'data_completeness', label: '数据完整性' },
  { key: 'other', label: '其他问题' },
];

const FeedbackModal: React.FC<FeedbackModalProps> = ({ reportId, onClose, onSubmitted }) => {
  const [rating, setRating] = useState<1 | 2 | null>(null);
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [comment, setComment] = useState('');
  const [contactAllowed, setContactAllowed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [existingFeedback, setExistingFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkExistingFeedback();
  }, [reportId]);

  const checkExistingFeedback = async () => {
    try {
      const response = await api.get(`/api/reports/${reportId}/feedback`);
      if (response.data) {
        setExistingFeedback(response.data);
        setRating(response.data.rating);
        setSelectedIssues(response.data.issues || []);
        setComment(response.data.comment || '');
        setContactAllowed(response.data.contact_allowed || false);
      }
    } catch (error) {
      // No existing feedback, which is fine
    } finally {
      setLoading(false);
    }
  };

  const toggleIssue = (issueKey: string) => {
    setSelectedIssues(prev =>
      prev.includes(issueKey)
        ? prev.filter(i => i !== issueKey)
        : [...prev, issueKey]
    );
  };

  const handleSubmit = async () => {
    if (rating === null) {
      showToast.error('请选择满意度评价');
      return;
    }

    if (rating === 1 && selectedIssues.length === 0) {
      showToast.error('请至少选择一个问题类型');
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/api/reports/${reportId}/feedback`, {
        rating,
        issues: rating === 1 ? selectedIssues : [],
        comment: comment || null,
        contact_allowed: contactAllowed,
      });

      setSubmitted(true);
      showToast.success('感谢您的反馈！');
      onSubmitted?.();
    } catch (error: any) {
      const message = error.response?.data?.detail || '提交失败，请稍后重试';
      showToast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="fixed inset-0 bg-black/30" onClick={onClose} />
        <div className="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
          <div className="animate-pulse flex flex-col items-center">
            <div className="w-12 h-12 bg-gray-200 rounded-full mb-4" />
            <div className="h-4 bg-gray-200 rounded w-32 mb-2" />
            <div className="h-3 bg-gray-200 rounded w-48" />
          </div>
        </div>
      </div>
    );
  }

  if (submitted || existingFeedback) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="fixed inset-0 bg-black/30" onClick={onClose} />
        <div className="relative bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 rounded-lg hover:bg-gray-100"
          >
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>

          <div className="text-center py-4">
            <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              感谢您的反馈！
            </h3>
            <p className="text-gray-500 text-sm">
              您的反馈将帮助我们改进分析质量
            </p>

            {existingFeedback && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg text-left">
                <div className="flex items-center gap-2 mb-2">
                  {existingFeedback.rating === 2 ? (
                    <HandThumbUpSolidIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <HandThumbDownSolidIcon className="w-5 h-5 text-red-500" />
                  )}
                  <span className="text-sm font-medium">
                    {existingFeedback.rating === 2 ? '满意' : '不满意'}
                  </span>
                </div>
                {existingFeedback.issues && existingFeedback.issues.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {existingFeedback.issues.map((issue: string) => (
                      <span key={issue} className="px-2 py-0.5 bg-gray-200 rounded text-xs">
                        {ISSUE_CATEGORIES.find(c => c.key === issue)?.label || issue}
                      </span>
                    ))}
                  </div>
                )}
                {existingFeedback.comment && (
                  <p className="text-sm text-gray-600 mt-2">{existingFeedback.comment}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">报告准确吗？</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100"
          >
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-4 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              您对这份报告满意吗？
            </label>
            <div className="flex gap-4">
              <button
                onClick={() => setRating(2)}
                className={`flex-1 flex items-center justify-center gap-2 py-4 rounded-lg border-2 transition-all ${
                  rating === 2
                    ? 'border-green-500 bg-green-50 text-green-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }`}
              >
                {rating === 2 ? (
                  <HandThumbUpSolidIcon className="w-6 h-6" />
                ) : (
                  <HandThumbUpIcon className="w-6 h-6" />
                )}
                <span className="font-medium">满意 👍</span>
              </button>
              
              <button
                onClick={() => setRating(1)}
                className={`flex-1 flex items-center justify-center gap-2 py-4 rounded-lg border-2 transition-all ${
                  rating === 1
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }`}
              >
                {rating === 1 ? (
                  <HandThumbDownSolidIcon className="w-6 h-6" />
                ) : (
                  <HandThumbDownIcon className="w-6 h-6" />
                )}
                <span className="font-medium">不满意 👎</span>
              </button>
            </div>
          </div>

          {rating === 1 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                请选择问题类型（可多选）
              </label>
              <div className="grid grid-cols-2 gap-2">
                {ISSUE_CATEGORIES.map((category) => (
                  <button
                    key={category.key}
                    onClick={() => toggleIssue(category.key)}
                    className={`px-3 py-2 rounded-lg text-sm text-left transition-all ${
                      selectedIssues.includes(category.key)
                        ? 'bg-primary-100 text-primary-700 border border-primary-300'
                        : 'bg-gray-50 text-gray-600 border border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {selectedIssues.includes(category.key) && (
                      <span className="mr-1">✓</span>
                    )}
                    {category.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              详细说明（可选）
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={
                rating === 1
                  ? '请描述具体问题，帮助我们改进...'
                  : '您有什么建议或想法？'
              }
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
          </div>

          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              id="contact-allowed"
              checked={contactAllowed}
              onChange={(e) => setContactAllowed(e.target.checked)}
              className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="contact-allowed" className="text-sm text-gray-600">
              <EnvelopeIcon className="w-4 h-4 inline mr-1" />
              允许我们联系您了解详情（用于改进服务质量）
            </label>
          </div>

          <div className="bg-blue-50 rounded-lg p-3 flex items-start gap-2">
            <ChatBubbleLeftRightIcon className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-700">
              <p className="font-medium">您的反馈很重要</p>
              <p className="text-blue-600 mt-1">
                我们会认真对待每一条反馈，用于优化分析模型和提升服务质量。
              </p>
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-100 p-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || rating === null}
            className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? '提交中...' : '提交反馈'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal;
