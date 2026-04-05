import React, { useState } from 'react';

interface FeedbackDialogProps {
  open: boolean;
  onClose: () => void;
}

const FeedbackDialog: React.FC<FeedbackDialogProps> = ({ open, onClose }) => {
  const [type, setType] = useState('general');
  const [content, setContent] = useState('');
  const [rating, setRating] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    if (!content.trim()) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      await fetch('http://localhost:8000/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          type,
          content,
          rating,
          page_url: window.location.href,
          user_agent: navigator.userAgent,
        }),
      });
      setSuccess(true);
      setContent('');
      setRating(5);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('提交反馈失败:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
          <div className="p-4 border-b">
            <h3 className="text-lg font-medium">提交反馈</h3>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">反馈类型</label>
              <div className="flex flex-wrap gap-4">
                {[
                  { value: 'general', label: '一般反馈' },
                  { value: 'bug', label: '问题报告' },
                  { value: 'feature', label: '功能建议' },
                  { value: 'other', label: '其他' },
                ].map((option) => (
                  <label key={option.value} className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="radio"
                      name="type"
                      value={option.value}
                      checked={type === option.value}
                      onChange={(e) => setType(e.target.value)}
                      className="text-primary"
                    />
                    <span className="text-sm">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">反馈内容</label>
              <textarea
                rows={4}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="请详细描述您的反馈..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">整体评分:</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRating(star)}
                    className={`text-2xl ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="p-4 border-t flex justify-end gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={!content.trim() || submitting}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primaryDark disabled:opacity-50"
            >
              {submitting ? '提交中...' : '提交'}
            </button>
          </div>
        </div>
      </div>

      {success && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg shadow-lg">
          感谢您的反馈！
        </div>
      )}
    </>
  );
};

const FeedbackButton: React.FC = () => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-primary text-white px-4 py-2 rounded-lg shadow-lg hover:bg-primaryDark transition-colors flex items-center gap-2"
      >
        <span>💬</span>
        反馈
      </button>
      <FeedbackDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
};

export default FeedbackButton;
export { FeedbackDialog };
