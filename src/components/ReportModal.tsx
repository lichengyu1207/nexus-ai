import React, { useState } from 'react';
import {
  XMarkIcon,
  ExclamationTriangleIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface ReportModalProps {
  reportedType: 'report' | 'comment' | 'user';
  reportedId: string;
  reportedTitle?: string;
  onClose: () => void;
  onSubmitted?: () => void;
}

const REASON_OPTIONS = [
  { value: 'inappropriate', label: '不当内容' },
  { value: 'spam', label: '垃圾信息' },
  { value: 'fraud', label: '涉嫌欺诈' },
  { value: 'copyright', label: '版权问题' },
  { value: 'privacy', label: '隐私侵犯' },
  { value: 'other', label: '其他原因' },
];

const TYPE_LABELS = {
  report: '分析报告',
  comment: '评论',
  user: '用户',
};

const ReportModal: React.FC<ReportModalProps> = ({
  reportedType,
  reportedId,
  reportedTitle,
  onClose,
  onSubmitted,
}) => {
  const [reason, setReason] = useState<string>('');
  const [details, setDetails] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const handleSubmit = async () => {
    if (!reason) {
      showToast.error('请选择举报原因');
      return;
    }

    if (!confirmed) {
      showToast.error('请确认举报内容真实有效');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('reports', {
        reported_type: reportedType,
        reported_id: reportedId,
        reason,
        details: details || undefined,
      });
      showToast.success('举报已提交，我们会尽快处理');
      onSubmitted?.();
      onClose();
    } catch (error: any) {
      const message = error.response?.data?.detail || '提交失败';
      showToast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
            举报{TYPE_LABELS[reportedType]}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {reportedTitle && (
          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400">举报内容</p>
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {reportedTitle}
            </p>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              举报原因 *
            </label>
            <div className="space-y-2">
              {REASON_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="reason"
                    value={option.value}
                    checked={reason === option.value}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-4 h-4 text-primary-600"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              补充说明（可选）
            </label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="请提供更多详细信息帮助我们处理..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 resize-none"
              rows={3}
              maxLength={1000}
            />
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3">
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-2">
              请确保举报内容真实有效。恶意举报可能会导致账号受到限制。
            </p>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-sm text-yellow-800 dark:text-yellow-200 font-medium">
                我确认举报内容真实有效
              </span>
            </label>
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
            disabled={submitting || !reason || !confirmed}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
            {submitting ? '提交中...' : '提交举报'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportModal;
