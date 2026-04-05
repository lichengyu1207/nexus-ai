import React, { useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MemoryCard } from './MemoryCard';
import { Memory } from '../types';

interface MemoryCardListProps {
  memories: Memory[];
  onMemoryClick: (id: string) => void;
  onStarToggle: (id: string, importance: number) => void;
  selectedId: string | null;
  loading: boolean;
  hasMore: boolean;
  loadMore: () => void;
}

const LoadingSkeleton: React.FC = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {[1, 2, 3, 4, 5, 6].map((i) => (
      <div
        key={i}
        className="h-48 rounded-xl bg-bg-secondary/40 animate-pulse border border-border-light"
      />
    ))}
  </div>
);

const EmptyState: React.FC = () => (
  <div className="flex flex-col items-center justify-center py-16 text-text-secondary">
    <svg className="w-16 h-16 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    <p className="text-lg font-medium mb-1">暂无记忆</p>
    <p className="text-sm">调整筛选条件或创建新记忆</p>
  </div>
);

export const MemoryCardList: React.FC<MemoryCardListProps> = ({
  memories,
  onMemoryClick,
  onStarToggle,
  selectedId,
  loading,
  hasMore,
  loadMore,
}) => {
  const observerRef = useRef<IntersectionObserver | null>(null);

  const lastCardRef = useCallback(
    (node: HTMLDivElement) => {
      if (loading) return;

      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          loadMore();
        }
      });

      if (node) {
        observerRef.current.observe(node);
      }
    },
    [loading, hasMore, loadMore]
  );

  if (loading && memories.length === 0) {
    return (
      <div className="p-6">
        <LoadingSkeleton />
      </div>
    );
  }

  if (memories.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {memories.map((memory, index) => (
            <motion.div
              key={memory.id}
              ref={index === memories.length - 1 ? lastCardRef : undefined}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: index * 0.05 }}
            >
              <MemoryCard
                memory={memory}
                onClick={onMemoryClick}
                onStarToggle={onStarToggle}
                selected={selectedId === memory.id}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {loading && memories.length > 0 && (
        <div className="flex justify-center py-8">
          <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>
      )}

      {!hasMore && memories.length > 0 && (
        <div className="py-8 text-center text-xs text-text-secondary">
          已加载全部 {memories.length} 条记忆
        </div>
      )}
    </div>
  );
};

export default MemoryCardList;
