import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeftIcon, 
  StarIcon, 
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  DocumentTextIcon,
  BriefcaseIcon
} from '@heroicons/react/24/outline';
import { CheckBadgeIcon, MapPinIcon } from '@heroicons/react/24/solid';
import { useQuery } from '@tanstack/react-query';
import type { Talent } from '../types';
import { TALENT_TYPE_CONFIG, AVAILABILITY_CONFIG } from '../types';
import { useReviews } from '../hooks/useReviews';

async function fetchTalent(id: string): Promise<Talent> {
  const response = await fetch(`/api/talents/${id}`);
  if (!response.ok) throw new Error('Failed to fetch talent');
  return response.json();
}

const RatingStars = ({ rating, size = 'md' }: { rating: number; size?: 'sm' | 'md' | 'lg' }) => {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-6 h-6' : 'w-5 h-5';
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <StarIcon
          key={star}
          className={`${sizeClass} ${
            star <= rating ? 'text-amber-400 fill-amber-400' : 'text-gray-600'
          }`}
        />
      ))}
    </div>
  );
};

export function TalentProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const { data: talent, isLoading, error } = useQuery({
    queryKey: ['talent', id],
    queryFn: () => fetchTalent(id!),
    enabled: !!id,
  });
  
  const { reviews, averageRating, ratingDistribution, isLoading: reviewsLoading } = useReviews({ talentId: id });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-slate-800 rounded w-1/4" />
            <div className="h-64 bg-slate-800 rounded-xl" />
            <div className="h-32 bg-slate-800 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !talent) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">加载人才详情失败</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-amber-500 text-slate-900 rounded-lg"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  const typeConfig = TALENT_TYPE_CONFIG[talent.type];
  const availabilityConfig = AVAILABILITY_CONFIG[talent.availability];

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <motion.button
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          返回人才库
        </motion.button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 overflow-hidden"
        >
          <div className="p-8 border-b border-slate-700/50">
            <div className="flex items-start gap-6">
              {talent.avatar ? (
                <img
                  src={talent.avatar}
                  alt={talent.name}
                  className="w-24 h-24 rounded-full object-cover border-2 border-amber-500/30"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-4xl">
                  {typeConfig.icon}
                </div>
              )}
              
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-2xl font-bold text-white">{talent.name}</h1>
                  {talent.verified && (
                    <span className="flex items-center gap-1 px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs">
                      <CheckBadgeIcon className="w-4 h-4" />
                      已认证
                    </span>
                  )}
                  <span className={`px-2 py-1 text-xs rounded-full ${typeConfig.color} bg-slate-700/50`}>
                    {typeConfig.label}
                  </span>
                </div>
                
                <p className="text-slate-300 mb-3">{talent.title}</p>
                
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2">
                    <RatingStars rating={talent.rating} />
                    <span className="text-slate-300">{talent.rating.toFixed(1)}</span>
                    <span className="text-slate-500">({talent.reviewCount} 条评价)</span>
                  </div>
                  <span className="text-amber-400 font-semibold text-lg">
                    ¥{talent.price}/小时
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-px bg-slate-700/50">
            <div className="bg-slate-800/50 p-4 text-center">
              <p className={`text-lg font-semibold ${availabilityConfig.color}`}>
                {availabilityConfig.label}
              </p>
              <p className="text-xs text-slate-500">可用性</p>
            </div>
            <div className="bg-slate-800/50 p-4 text-center">
              <p className="text-lg font-semibold text-white">
                {talent.portfolio?.length ?? 0}
              </p>
              <p className="text-xs text-slate-500">作品集</p>
            </div>
            <div className="bg-slate-800/50 p-4 text-center">
              <p className="text-lg font-semibold text-white">
                {talent.skills.length}
              </p>
              <p className="text-xs text-slate-500">技能</p>
            </div>
          </div>

          {talent.location && (
            <div className="px-8 py-4 border-b border-slate-700/50 flex items-center gap-2 text-slate-400">
              <MapPinIcon className="w-5 h-5" />
              {talent.location}
            </div>
          )}

          <div className="p-8 space-y-8">
            <div>
              <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <DocumentTextIcon className="w-5 h-5 text-amber-400" />
                个人简介
              </h2>
              <p className="text-slate-300 leading-relaxed">
                {talent.bio || '暂无简介'}
              </p>
            </div>

            <div>
              <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <BriefcaseIcon className="w-5 h-5 text-amber-400" />
                技能标签
              </h2>
              <div className="flex flex-wrap gap-2">
                {talent.skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-3 py-1.5 text-sm bg-amber-500/10 text-amber-400 rounded-full border border-amber-500/20"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {talent.portfolio && talent.portfolio.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-white mb-3">作品集</h2>
                <div className="grid grid-cols-2 gap-3">
                  {talent.portfolio.map((link, index) => (
                    <a
                      key={index}
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-3 bg-slate-700/30 rounded-lg text-amber-400 hover:bg-slate-700/50 transition-colors text-sm truncate"
                    >
                      {link}
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <StarIcon className="w-5 h-5 text-amber-400" />
                评价 ({reviews.length})
              </h2>
              
              {reviewsLoading ? (
                <div className="animate-pulse space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-20 bg-slate-700/30 rounded-lg" />
                  ))}
                </div>
              ) : reviews.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-8 p-4 bg-slate-700/30 rounded-lg">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-amber-400">
                        {averageRating.toFixed(1)}
                      </p>
                      <RatingStars rating={averageRating} size="sm" />
                      <p className="text-xs text-slate-500 mt-1">{reviews.length} 条评价</p>
                    </div>
                    <div className="flex-1 space-y-1">
                      {ratingDistribution.map(({ rating, count, percentage }) => (
                        <div key={rating} className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 w-8">{rating} 星</span>
                          <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500 rounded-full"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-500 w-8">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    {reviews.slice(0, 10).map((review) => (
                      <div key={review.id} className="p-4 bg-slate-700/30 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <RatingStars rating={review.rating} size="sm" />
                          <span className="text-xs text-slate-500">
                            {new Date(review.createdAt).toLocaleDateString('zh-CN')}
                          </span>
                        </div>
                        <p className="text-sm text-slate-300">{review.comment}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">暂无评价</p>
              )}
            </div>
          </div>

          <div className="p-6 border-t border-slate-700/50 flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 py-3 bg-amber-500 text-slate-900 font-semibold rounded-xl hover:bg-amber-400 transition-colors flex items-center justify-center gap-2"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
              发送邀约
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 py-3 border border-amber-500/50 text-amber-400 font-semibold rounded-xl hover:bg-amber-500/10 transition-colors flex items-center justify-center gap-2"
            >
              <ChatBubbleLeftRightIcon className="w-5 h-5" />
              发起聊天
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
