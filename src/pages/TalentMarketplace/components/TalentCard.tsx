import { motion, memo } from 'framer-motion';
import { CheckBadgeIcon, StarIcon, MapPinIcon } from '@heroicons/react/24/solid';
import type { Talent } from '../types';
import { TALENT_TYPE_CONFIG, AVAILABILITY_CONFIG } from '../types';

export interface TalentCardProps {
  talent: Talent;
  onClick?: () => void;
  onInvite?: () => void;
}

const RatingStars = ({ rating }: { rating: number }) => {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <StarIcon
          key={star}
          className={`w-4 h-4 ${
            star <= rating ? 'text-amber-400' : 'text-gray-600'
          }`}
        />
      ))}
      <span className="ml-1 text-sm text-gray-400">({rating.toFixed(1)})</span>
    </div>
  );
};

const TalentCardComponent = ({ talent, onClick, onInvite }: TalentCardProps) {
  const typeConfig = TALENT_TYPE_CONFIG[talent.type];
  const availabilityConfig = AVAILABILITY_CONFIG[talent.availability];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className="bg-white/5 border border-white/10 rounded-xl p-4 cursor-pointer transition-all hover:border-amber-500/30 hover:shadow-lg hover:shadow-amber-500/5"
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="relative">
          {talent.avatar ? (
            <img
              src={talent.avatar}
              alt={talent.name}
              className="w-14 h-14 rounded-full object-cover border-2 border-white/10"
            />
          ) : (
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-amber-500/20 to-amber-600/20 flex items-center justify-center text-2xl border-2 border-white/10">
              {typeConfig.icon}
            </div>
          )}
          {talent.verified && (
            <CheckBadgeIcon className="absolute -bottom-1 -right-1 w-5 h-5 text-blue-400 bg-gray-900 rounded-full" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-white truncate">{talent.name}</h3>
            <span className={`text-xs px-1.5 py-0.5 rounded ${typeConfig.color} bg-white/5`}>
              {typeConfig.label}
            </span>
          </div>
          <p className="text-sm text-gray-400 truncate mt-0.5">{talent.title}</p>
          <RatingStars rating={talent.rating} />
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {(talent.skills || []).slice(0, 4).map((skill) => (
          <span
            key={skill}
            className="px-2 py-0.5 text-xs bg-amber-500/10 text-amber-400 rounded-full"
          >
            {skill}
          </span>
        ))}
        {((talent.skills || [])).length > 4 && (
          <span className="px-2 py-0.5 text-xs bg-white/5 text-gray-400 rounded-full">
            +{((talent.skills || [])).length - 4}
          </span>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`text-xs ${availabilityConfig.color}`}>
            {availabilityConfig.label}
          </span>
          {talent.location && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <MapPinIcon className="w-3 h-3" />
              {talent.location}
            </span>
          )}
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-amber-400">¥{talent.price}</span>
          <span className="text-xs text-gray-500">/小时</span>
        </div>
      </div>

      {onInvite && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={(e) => {
            e.stopPropagation();
            onInvite();
          }}
          className="mt-3 w-full py-2 text-sm font-medium bg-amber-500 text-gray-900 rounded-lg hover:bg-amber-400 transition-colors"
        >
          发送邀约
        </motion.button>
      )}
    </motion.div>
  );
};

export const TalentCard = memo(TalentCardComponent);
