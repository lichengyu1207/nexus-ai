import React, { memo } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { Memory, MemoryType } from '../types';

interface MemoryCardProps {
  memory: Memory;
  onClick: (id: string) => void;
  onStarToggle: (id: string, importance: number) => void;
  selected?: boolean;
}

const typeConfig: Record<MemoryType, { icon: string; color: string; label: string }> = {
  episodic: { icon: '📅', color: 'text-blue-400', label: '情景' },
  semantic: { icon: '🧠', color: 'text-purple-400', label: '语义' },
  procedural: { icon: '⚙️', color: 'text-green-400', label: '程序性' },
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '昨天';
  if (diffDays < 7) return `${diffDays} 天前`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`;
  return date.toLocaleDateString('zh-CN');
};

const truncateContent = (content: string, maxLength: number = 80): string => {
  const stripped = content.replace(/[#*`_\[\]]/g, '').trim();
  if (stripped.length <= maxLength) return stripped;
  return stripped.slice(0, maxLength) + '...';
};

const StarRating: React.FC<{
  importance: number;
  onChange: (value: number) => void;
}> = memo(({ importance, onChange }) => {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <motion.button
          key={star}
          onClick={(e) => {
            e.stopPropagation();
            onChange(star);
          }}
          className={clsx(
            'text-sm transition-transform',
            star <= importance ? 'text-primary' : 'text-text-secondary/30'
          )}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.9 }}
          role="button"
          aria-label={`${star} 星`}
          aria-pressed={star <= importance}
        >
          ★
        </motion.button>
      ))}
    </div>
  );
});

StarRating.displayName = 'StarRating';

export const MemoryCard: React.FC<MemoryCardProps> = memo(({
  memory,
  onClick,
  onStarToggle,
  selected,
}) => {
  const config = typeConfig[memory.type];
  const displayTitle = memory.title || truncateContent(memory.content, 50);

  return (
    <motion.div
      onClick={() => onClick(memory.id)}
      className={clsx(
        'p-4 rounded-xl border cursor-pointer transition-all duration-200',
        'bg-bg-secondary/60 backdrop-blur-md',
        selected
          ? 'border-primary/70 shadow-lg shadow-primary/10'
          : 'border-border-light hover:border-primary/30 hover:shadow-lg'
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      role="button"
      tabIndex={0}
      aria-label={`记忆: ${displayTitle}`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg" aria-hidden="true">{config.icon}</span>
          <span className={clsx('text-xs px-2 py-0.5 rounded-full bg-current/10', config.color)}>
            {config.label}
          </span>
        </div>
        <StarRating
          importance={memory.importance}
          onChange={(value) => onStarToggle(memory.id, value)}
        />
      </div>

      <h3 className="text-sm font-medium text-text-primary mb-2 line-clamp-2">
        {displayTitle}
      </h3>

      <p className="text-xs text-text-secondary line-clamp-3 mb-3">
        {truncateContent(memory.content, 120)}
      </p>

      {memory.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {memory.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded-full bg-bg-tertiary/50 text-text-secondary"
            >
              #{tag}
            </span>
          ))}
          {memory.tags.length > 3 && (
            <span className="text-xs text-text-secondary">
              +{memory.tags.length - 3}
            </span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-text-secondary">
        <div className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{formatDate(memory.createdAt)}</span>
        </div>
        {memory.associations.memories.length > 0 && (
          <div className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <span>{memory.associations.memories.length} 关联</span>
          </div>
        )}
      </div>
    </motion.div>
  );
});

MemoryCard.displayName = 'MemoryCard';

export default MemoryCard;
