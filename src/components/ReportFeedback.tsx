import React, { useState } from 'react';
import { HandThumbUpIcon, HandThumbDownIcon } from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpSolidIcon, HandThumbDownIcon as HandThumbDownSolidIcon } from '@heroicons/react/24/solid';
import showToast from '@/utils/toast';

interface ReportFeedbackProps {
  reportId: string;
  onFeedbackSubmit?: (feedback: { rating: 'positive' | 'negative'; comment?: string }) => void;
}

const ReportFeedback: React.FC<ReportFeedbackProps> = ({ reportId, onFeedbackSubmit }) => {
  const [rating, setRating] = useState<'positive' | 'negative' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRating = async (newRating: 'positive' | 'negative') => {
    setRating(newRating);
    setShowComment(true);
  };

  const handleSubmit = async () => {
    if (!rating) return;
    
    setIsSubmitting(true);
    try {
      // API call would go here
      // await api.post(`/reports/${reportId}/feedback`, { rating, comment });
      
      showToast.success('感谢您的反馈！');
      onFeedbackSubmit?.({ rating, comment });
      setShowComment(false);
    } catch {
      showToast.error('提交失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="border-t border-gray-100 pt-6 mt-6">
      <div className="flex items-center justify-between">
        <p className="text-gray-600">这份报告对您有帮助吗？</p>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => handleRating('positive')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              rating === 'positive'
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {rating === 'positive' ? (
              <HandThumbUpSolidIcon className="w-5 h-5" />
            ) : (
              <HandThumbUpIcon className="w-5 h-5" />
            )}
            <span>有用</span>
          </button>
          
          <button
            onClick={() => handleRating('negative')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              rating === 'negative'
                ? 'bg-red-100 text-red-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {rating === 'negative' ? (
              <HandThumbDownSolidIcon className="w-5 h-5" />
            ) : (
              <HandThumbDownIcon className="w-5 h-5" />
            )}
            <span>需改进</span>
          </button>
        </div>
      </div>

      {showComment && (
        <div className="mt-4 p-4 bg-gray-50 rounded-xl">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="请告诉我们您的建议（可选）"
            className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            rows={3}
          />
          <div className="flex justify-end mt-3 space-x-3">
            <button
              onClick={() => setShowComment(false)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {isSubmitting ? '提交中...' : '提交反馈'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportFeedback;
