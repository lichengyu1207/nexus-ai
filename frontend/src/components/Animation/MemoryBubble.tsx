/**
 * 记忆气泡组件
 * Memory Bubble Component
 * 
 * 在侧边展示当前会话相关的记忆气泡
 */

import React, { useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface MemoryBubbleData {
  id: string;
  summary: string;
  confidence: number;
  source: string;
  content: string;
  timestamp: Date;
  type: 'relevant' | 'recent' | 'suggested';
}

export interface MemoryBubbleProps {
  memories: MemoryBubbleData[];
  onInsert?: (memory: MemoryBubbleData) => void;
  onClose?: (memoryId: string) => void;
  maxVisible?: number;
  className?: string;
}

const typeConfig = {
  relevant: { label: '相关记忆', color: '#3B82F6', icon: '🔗' },
  recent: { label: '最近记忆', color: '#10B981', icon: '🕐' },
  suggested: { label: '建议参考', color: '#F59E0B', icon: '💡' },
};

const MemoryBubbleItem: React.FC<{
  memory: MemoryBubbleData;
  onInsert: () => void;
  onClose: () => void;
}> = memo(({ memory, onInsert, onClose }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = typeConfig[memory.type];

  return (
    <motion.div
      className="relative bg-white rounded-xl shadow-lg overflow-hidden"
      initial={{ opacity: 0, x: 50, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 50, scale: 0.9 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      layout
    >
      <motion.div
        className="absolute top-0 left-0 h-full w-1"
        style={{ backgroundColor: config.color }}
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ delay: 0.1 }}
      />
      
      <div className="p-3 pl-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span>{config.icon}</span>
            <span 
              className="text-xs font-medium"
              style={{ color: config.color }}
            >
              {config.label}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <span className="text-xs text-gray-400">置信度</span>
              <div className="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: config.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${memory.confidence * 100}%` }}
                />
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-5 h-5 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>
        
        <motion.div
          className="cursor-pointer"
          onHoverStart={() => setIsExpanded(true)}
          onHoverEnd={() => setIsExpanded(false)}
        >
          <p className="text-sm text-gray-700 line-clamp-2">
            {memory.summary}
          </p>
          
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <p className="text-xs text-gray-500 mb-2">
                    {memory.content}
                  </p>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>来源: {memory.source}</span>
                    <span>{memory.timestamp.toLocaleTimeString()}</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
        
        <motion.button
          className="mt-2 w-full py-1.5 text-xs font-medium rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-600"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onInsert}
        >
          插入到对话
        </motion.button>
      </div>
    </motion.div>
  );
});

MemoryBubbleItem.displayName = 'MemoryBubbleItem';

const MemoryBubble: React.FC<MemoryBubbleProps> = memo(({
  memories,
  onInsert,
  onClose,
  maxVisible = 5,
  className = '',
}) => {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [showNewIndicator, setShowNewIndicator] = useState(false);

  const visibleMemories = memories
    .filter(m => !dismissedIds.has(m.id))
    .slice(0, maxVisible);

  const handleInsert = useCallback((memory: MemoryBubbleData) => {
    onInsert?.(memory);
  }, [onInsert]);

  const handleClose = useCallback((memoryId: string) => {
    setDismissedIds(prev => new Set([...prev, memoryId]));
    onClose?.(memoryId);
  }, [onClose]);

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <AnimatePresence mode="popLayout">
        {visibleMemories.map((memory, index) => (
          <motion.div
            key={memory.id}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ delay: index * 0.1 }}
          >
            <MemoryBubbleItem
              memory={memory}
              onInsert={() => handleInsert(memory)}
              onClose={() => handleClose(memory.id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
      
      {memories.length > maxVisible && (
        <motion.div
          className="text-center text-xs text-gray-400 py-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          还有 {memories.length - maxVisible} 条记忆...
        </motion.div>
      )}
      
      {visibleMemories.length === 0 && (
        <motion.div
          className="text-center py-8 text-gray-400"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="text-3xl mb-2">💭</div>
          <p className="text-sm">暂无相关记忆</p>
        </motion.div>
      )}
    </div>
  );
});

MemoryBubble.displayName = 'MemoryBubble';

export default MemoryBubble;
