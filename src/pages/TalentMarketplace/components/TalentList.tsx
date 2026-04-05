import { useCallback, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import type { Talent } from '../types';
import { TalentCard } from './TalentCard';

export interface TalentListProps {
  talents: Talent[];
  isLoading: boolean;
  isFetchingNextPage: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
  onTalentClick?: (talent: Talent) => void;
  onInvite?: (talent: Talent) => void;
}

const CARD_HEIGHT = 220;
const GRID_COLS = 3;

export function TalentList({
  talents,
  isLoading,
  isFetchingNextPage,
  hasMore,
  onLoadMore,
  onTalentClick,
  onInvite,
}: TalentListProps) {
  const listRef = useRef<List>(null);

  const handleItemsRendered = useCallback(
    ({ visibleStopIndex }: { visibleStopIndex: number }) => {
      if (hasMore && !isFetchingNextPage && visibleStopIndex >= talents.length - 3) {
        onLoadMore();
      }
    },
    [hasMore, isFetchingNextPage, talents.length, onLoadMore]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (talents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring' }}
          className="text-5xl mb-3"
        >
          👥
        </motion.div>
        <p className="text-sm">暂无匹配的人才</p>
        <p className="text-xs text-gray-500 mt-1">尝试调整筛选条件</p>
      </div>
    );
  }

  const rows = Math.ceil(talents.length / GRID_COLS);

  const Row = ({
    index,
    style,
  }: {
    index: number;
    style: React.CSSProperties;
  }) => {
    const startIndex = index * GRID_COLS;
    const rowTalents = talents.slice(startIndex, startIndex + GRID_COLS);

    return (
      <div style={style} className="flex gap-4 px-4">
        {rowTalents.map((talent) => (
          <div key={talent.id} className="flex-1">
            <TalentCard
              talent={talent}
              onClick={() => onTalentClick?.(talent)}
              onInvite={() => onInvite?.(talent)}
            />
          </div>
        ))}
        {rowTalents.length < GRID_COLS &&
          Array.from({ length: GRID_COLS - rowTalents.length }).map((_, i) => (
            <div key={`empty-${i}`} className="flex-1" />
          ))}
      </div>
    );
  };

  return (
    <div className="relative">
      <List
        ref={listRef}
        height={600}
        itemCount={rows}
        itemSize={CARD_HEIGHT}
        width="100%"
        onItemsRendered={handleItemsRendered}
      >
        {Row}
      </List>

      <AnimatePresence>
        {isFetchingNextPage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex justify-center py-4"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <ArrowPathIcon className="w-5 h-5 text-amber-400" />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
