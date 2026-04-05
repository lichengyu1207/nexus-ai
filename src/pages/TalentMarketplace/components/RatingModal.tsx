import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, StarIcon } from '@heroicons/react/24/outline';
import type { Review } from '../types';

export interface RatingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<Review>) => void;
  isLoading?: boolean;
  talentId: string;
  talentName?: string;
}

export function RatingModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  talentId,
  talentName,
}: RatingModalProps) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [hoveredRating, setHoveredRating] = useState(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      toTalentId: talentId,
      rating,
      comment,
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-gray-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <div>
                <h2 className="text-lg font-semibold text-white">提交评价</h2>
                {talentName && (
                  <p className="text-sm text-gray-400">为 {talentName} 评分</p>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-3 text-center">
                  您的评分
                </label>
                <div className="flex justify-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      onMouseEnter={() => setHoveredRating(star)}
                      onMouseLeave={() => setHoveredRating(0)}
                      className="p-1 transition-transform hover:scale-110"
                    >
                      <StarIcon
                        className={`w-10 h-10 transition-colors ${
                          star <= (hoveredRating || rating)
                            ? 'text-amber-400 fill-amber-400'
                            : 'text-gray-600'
                        }`}
                      />
                    </button>
                  ))}
                </div>
                <p className="text-center text-sm text-gray-500 mt-2">
                  {rating === 5 && '非常满意'}
                  {rating === 4 && '比较满意'}
                  {rating === 3 && '一般'}
                  {rating === 2 && '不太满意'}
                  {rating === 1 && '非常不满意'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  评价内容
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 resize-none"
                  placeholder="分享您的合作体验..."
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className={`
                    flex-1 py-2 text-sm font-medium rounded-lg transition-colors
                    ${
                      isLoading
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-amber-500 text-gray-900 hover:bg-amber-400'
                    }
                  `}
                >
                  {isLoading ? '提交中...' : '提交评价'}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
