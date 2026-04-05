import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BrainIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  ClockIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface MemoryData {
  id: string;
  summary: string;
  content: string;
  createdAt: string;
  importance: 'low' | 'medium' | 'high';
  tags?: string[];
  source?: string;
}

interface MemoryCardProps {
  memory: MemoryData;
  onFeedback?: (memoryId: string, helpful: boolean) => void;
  defaultExpanded?: boolean;
  showInline?: boolean;
}

const importanceConfigs = {
  low: {
    color: 'text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    borderColor: 'border-gray-200 dark:border-gray-700',
    label: '一般',
  },
  medium: {
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    label: '重要',
  },
  high: {
    color: 'text-amber-500',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    borderColor: 'border-amber-200 dark:border-amber-800',
    label: '关键',
  },
};

const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  onFeedback,
  defaultExpanded = false,
  showInline = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [feedback, setFeedback] = useState<'helpful' | 'not_helpful' | null>(null);
  const [showFeedbackAnimation, setShowFeedbackAnimation] = useState(false);

  const importanceConfig = importanceConfigs[memory.importance];

  const handleFeedback = (helpful: boolean) => {
    setFeedback(helpful ? 'helpful' : 'not_helpful');
    setShowFeedbackAnimation(true);
    onFeedback?.(memory.id, helpful);

    setTimeout(() => setShowFeedbackAnimation(false), 1000);
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const cardContent = (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`
        rounded-xl border overflow-hidden transition-all
        ${importanceConfig.bgColor} ${importanceConfig.borderColor}
        ${showInline ? 'text-sm' : ''}
      `}
    >
      <div
        className={`p-4 cursor-pointer ${!showInline ? 'hover:bg-white/50 dark:hover:bg-gray-900/50' : ''}`}
        onClick={() => !showInline && setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              className={`p-1.5 rounded-lg ${importanceConfig.bgColor}`}
            >
              <BrainIcon className={`w-4 h-4 ${importanceConfig.color}`} />
            </motion.div>
            <div>
              <span className={`text-xs font-medium ${importanceConfig.color}`}>
                记忆检索
              </span>
              <span className="text-xs text-gray-400 ml-2">
                {importanceConfig.label}
              </span>
            </div>
          </div>

          {!showInline && (
            <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
              {isExpanded ? (
                <ChevronUpIcon className="w-4 h-4" />
              ) : (
                <ChevronDownIcon className="w-4 h-4" />
              )}
            </button>
          )}
        </div>

        <p className={`mt-2 text-gray-700 dark:text-gray-300 ${showInline ? 'line-clamp-2' : ''}`}>
          {memory.summary}
        </p>

        {memory.tags && memory.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {memory.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-0.5 bg-white/50 dark:bg-gray-800/50 rounded-full text-xs text-gray-500"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <ClockIcon className="w-3.5 h-3.5" />
            {formatTime(memory.createdAt)}
          </div>

          {showFeedbackAnimation && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className="flex items-center gap-1 text-xs text-green-500"
            >
              <SparklesIcon className="w-3.5 h-3.5" />
              感谢反馈
            </motion.div>
          )}

          {!showInline && (
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleFeedback(true);
                }}
                className={`p-1 rounded-lg transition-colors ${
                  feedback === 'helpful'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-green-500'
                }`}
                title="有帮助"
              >
                <HandThumbUpIcon className="w-4 h-4" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleFeedback(false);
                }}
                className={`p-1 rounded-lg transition-colors ${
                  feedback === 'not_helpful'
                    ? 'bg-red-100 dark:bg-red-900/30 text-red-600'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-500'
                }`}
                title="无帮助"
              >
                <HandThumbDownIcon className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && !showInline && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200 dark:border-gray-700"
          >
            <div className="p-4 bg-white/50 dark:bg-gray-900/50">
              <h5 className="text-xs font-medium text-gray-500 mb-2">完整内容</h5>
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {memory.content}
              </p>

              {memory.source && (
                <div className="mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
                  <span className="text-xs text-gray-400">来源: {memory.source}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );

  if (showInline) {
    return cardContent;
  }

  return (
    <motion.div
      layout
      className="relative"
    >
      {cardContent}
    </motion.div>
  );
};

export default MemoryCard;
