import { motion } from 'framer-motion';
import { StarIcon, PlayIcon } from '@heroicons/react/24/outline';
import type { Skill } from '../types';
import { SKILL_CATEGORIES } from '../types';

export interface SkillCardProps {
  skill: Skill;
  onClick?: () => void;
  onSubscribe?: () => void;
}

export function SkillCard({ skill, onClick, onSubscribe }: SkillCardProps) {
  const categoryConfig = SKILL_CATEGORIES[skill.category];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className="bg-white/5 border border-white/10 rounded-xl p-4 cursor-pointer transition-all hover:border-amber-500/30 hover:shadow-lg hover:shadow-amber-500/5"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-base font-semibold text-white">{skill.name}</h3>
          <span className="text-xs text-gray-500">
            {categoryConfig?.label ?? skill.category}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <StarIcon className="w-4 h-4 text-amber-400 fill-amber-400" />
          <span className="text-sm text-gray-300">{skill.rating.toFixed(1)}</span>
        </div>
      </div>

      <p className="text-sm text-gray-400 line-clamp-2 mb-3">{skill.description}</p>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {skill.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="px-2 py-0.5 text-xs bg-white/5 text-gray-400 rounded-full"
          >
            {tag}
          </span>
        ))}
        {skill.tags.length > 3 && (
          <span className="px-2 py-0.5 text-xs bg-white/5 text-gray-500 rounded-full">
            +{skill.tags.length - 3}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <PlayIcon className="w-3 h-3" />
          {skill.callCount.toLocaleString()} 次调用
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-amber-400">¥{skill.price}</span>
          <span className="text-xs text-gray-500">
            {skill.priceType === 'per_use' ? '/次' : '/月'}
          </span>
        </div>
      </div>

      {onSubscribe && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={(e) => {
            e.stopPropagation();
            onSubscribe();
          }}
          className="mt-3 w-full py-2 text-sm font-medium bg-amber-500/20 text-amber-400 rounded-lg hover:bg-amber-500/30 transition-colors"
        >
          {skill.priceType === 'per_use' ? '立即调用' : '订阅'}
        </motion.button>
      )}
    </motion.div>
  );
}
