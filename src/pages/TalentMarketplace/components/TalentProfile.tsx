import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, StarIcon } from '@heroicons/react/24/outline';
import { CheckBadgeIcon, MapPinIcon } from '@heroicons/react/24/solid';
import type { Talent, Review } from '../types';
import { TALENT_TYPE_CONFIG, AVAILABILITY_CONFIG } from '../types';

export interface TalentProfileProps {
  talent: Talent;
  reviews: Review[];
  isOpen: boolean;
  onClose: () => void;
  onInvite: () => void;
}

const RatingStars = ({ rating }: { rating: number }) => {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <StarIcon
          key={star}
          className={`w-5 h-5 ${
            star <= rating ? 'text-amber-400 fill-amber-400' : 'text-gray-600'
          }`}
        />
      ))}
    </div>
  );
};

export function TalentProfile({ talent, reviews, isOpen, onClose, onInvite }: TalentProfileProps) {
  const typeConfig = TALENT_TYPE_CONFIG[talent.type];
  const availabilityConfig = AVAILABILITY_CONFIG[talent.availability];

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
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-[500px] bg-gray-900 border-l border-white/10 shadow-2xl z-50 overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  {talent.avatar ? (
                    <img
                      src={talent.avatar}
                      alt={talent.name}
                      className="w-20 h-20 rounded-full object-cover border-2 border-white/10"
                    />
                  ) : (
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-500/20 to-amber-600/20 flex items-center justify-center text-4xl border-2 border-white/10">
                      {typeConfig.icon}
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl font-bold text-white">{talent.name}</h2>
                      {talent.verified && (
                        <CheckBadgeIcon className="w-5 h-5 text-blue-400" />
                      )}
                    </div>
                    <p className="text-gray-400">{talent.title}</p>
                    <span className={`text-xs px-2 py-0.5 rounded ${typeConfig.color} bg-white/5`}>
                      {typeConfig.label}
                    </span>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <XMarkIcon className="w-5 h-5 text-gray-400" />
                </button>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <RatingStars rating={talent.rating} />
                  <p className="text-xs text-gray-500 mt-1">{talent.reviewCount} 条评价</p>
                </div>
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-amber-400">¥{talent.price}</p>
                  <p className="text-xs text-gray-500">/小时</p>
                </div>
                <div className="bg-white/5 rounded-lg p-3 text-center">
                  <p className={`text-sm font-medium ${availabilityConfig.color}`}>
                    {availabilityConfig.label}
                  </p>
                  <p className="text-xs text-gray-500">可用性</p>
                </div>
              </div>

              {talent.location && (
                <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
                  <MapPinIcon className="w-4 h-4" />
                  {talent.location}
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">技能标签</h3>
                <div className="flex flex-wrap gap-2">
                  {talent.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-3 py-1 text-sm bg-amber-500/10 text-amber-400 rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {talent.bio && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">个人简介</h3>
                  <p className="text-sm text-gray-300 leading-relaxed">{talent.bio}</p>
                </div>
              )}

              {talent.portfolio && talent.portfolio.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-400 mb-2">作品集</h3>
                  <div className="space-y-2">
                    {talent.portfolio.map((link, index) => (
                      <a
                        key={index}
                        href={link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-sm text-amber-400 hover:text-amber-300 truncate"
                      >
                        {link}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">最新评价</h3>
                {reviews.length > 0 ? (
                  <div className="space-y-3">
                    {reviews.slice(0, 5).map((review) => (
                      <div key={review.id} className="bg-white/5 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <RatingStars rating={review.rating} />
                          <span className="text-xs text-gray-500">
                            {new Date(review.createdAt).toLocaleDateString('zh-CN')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300">{review.comment}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">暂无评价</p>
                )}
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onInvite}
                className="w-full py-3 text-base font-medium bg-amber-500 text-gray-900 rounded-lg hover:bg-amber-400 transition-colors"
              >
                发送邀约
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
