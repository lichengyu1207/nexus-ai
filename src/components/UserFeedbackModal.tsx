import React, { useState } from 'react';
import {
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  LightBulbIcon,
  BugAntIcon,
  ExclamationTriangleIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface UserFeedbackModalProps {
  onClose: () => void;
  onSubmitted?: () => void;
}

const FEEDBACK_TYPES = [
  { value: 'feedback', label: '功能反馈', icon: ChatBubbleLeftRightIcon, color: 'text-blue-500' },
  { value: 'suggestion', label: '建议', icon: LightBulbIcon, color: 'text-yellow-500' },
  { value: 'bug', label: '问题报告', icon: BugAntIcon, color: 'text-red-500' },
  { value: 'complaint', label: '投诉', icon: ExclamationTriangleIcon, color: 'text-orange-500' },
];

const UserFeedbackModal: React.FC<UserFeedbackModalProps> = ({ onClose, onSubmitted }) => {
  const [type, setType] = useState<string>('feedback');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!content.trim()) {
      showToast.error('请填写反馈内容');
      return;
    }

    if (content.length < 10) {
      showToast.error('反馈内容至少10个字符');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('feedback', {
        type,
        title: title || undefined,
        content,
      });
      showToast.success('反馈提交成功，感谢您的宝贵意见！');
      onSubmitted?.();
      onClose();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">提交反馈</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              反馈类型
            </label>
            <div className="grid grid-cols-2 gap-2">
              {FEEDBACK_TYPES.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.value}
                    onClick={() => setType(t.value)}
                    className={`flex items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                      type === t.value
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${t.color}`} />
                    <span className="text-sm font-medium">{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              标题（可选）
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="简要描述您的反馈"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              maxLength={100}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              详细内容 *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="请详细描述您的反馈、建议或遇到的问题..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 resize-none"
              rows={5}
              maxLength={2000}
            />
            <p className="text-xs text-gray-400 mt-1">{content.length}/2000</p>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              感谢您的反馈！我们会认真对待每一条意见，并在必要时通过站内信回复您。
            </p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !content.trim()}
            className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
            {submitting ? '提交中...' : '提交反馈'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserFeedbackModal;
