import { motion } from 'framer-motion';
import type { End } from '../types';

interface EndTabsProps {
  ends: End[];
  selectedEndId: string;
  onSelectEnd: (endId: string) => void;
}

const endIcons: Record<string, string> = {
  university: '🎓',
  enterprise: '🏢',
  government: '🏛️',
  association: '🤝',
  public: '👥',
};

export function EndTabs({ ends, selectedEndId, onSelectEnd }: EndTabsProps) {
  return (
    <div className="flex border-b border-gray-200/20 bg-slate-900/50 backdrop-blur-sm">
      <div className="flex overflow-x-auto scrollbar-hide">
        {ends.map((end) => {
          const isSelected = end.id === selectedEndId;
          return (
            <button
              key={end.id}
              role="tab"
              aria-selected={isSelected}
              onClick={() => onSelectEnd(end.id)}
              className={`
                relative flex items-center gap-2 px-6 py-4 text-sm font-medium
                transition-colors duration-200 whitespace-nowrap
                ${isSelected ? 'text-amber-400' : 'text-gray-400 hover:text-gray-200'}
              `}
            >
              <span className="text-lg">{endIcons[end.name] || '📌'}</span>
              <span>{end.displayName}</span>
              {end.unreadCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="flex items-center justify-center min-w-[20px] h-5 px-1.5
                    bg-red-500 text-white text-xs rounded-full"
                >
                  {end.unreadCount > 99 ? '99+' : end.unreadCount}
                </motion.span>
              )}
              {isSelected && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400"
                  initial={false}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
