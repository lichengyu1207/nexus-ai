import { useRef, useCallback, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import type { Notification } from './types';
import { NotificationItem } from './NotificationItem';

export interface NotificationListProps {
  notifications: Notification[];
  isLoading: boolean;
  isFetchingNextPage: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
  onClick?: (notification: Notification) => void;
  height?: number;
}

interface RowData {
  notifications: Notification[];
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
  onClick?: (notification: Notification) => void;
}

const ITEM_HEIGHT = 100;

const NotificationRow = ({
  index,
  style,
  data,
}: {
  index: number;
  style: React.CSSProperties;
  data: RowData;
}) => {
  const notification = data.notifications[index];
  if (!notification) return null;

  return (
    <div style={style}>
      <NotificationItem
        notification={notification}
        onMarkRead={data.onMarkRead}
        onDelete={data.onDelete}
        onClick={data.onClick}
      />
    </div>
  );
};

export function NotificationList({
  notifications,
  isLoading,
  isFetchingNextPage,
  hasMore,
  onLoadMore,
  onMarkRead,
  onDelete,
  onClick,
  height = 400,
}: NotificationListProps) {
  const listRef = useRef<List>(null);

  const handleItemsRendered = useCallback(
    ({ visibleStopIndex }: { visibleStopIndex: number }) => {
      if (
        hasMore &&
        !isFetchingNextPage &&
        visibleStopIndex >= notifications.length - 5
      ) {
        onLoadMore();
      }
    },
    [hasMore, isFetchingNextPage, notifications.length, onLoadMore]
  );

  useEffect(() => {
    if (listRef.current && notifications.length > 0) {
      listRef.current.scrollToItem(0);
    }
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <ArrowPathIcon className="w-8 h-8 text-amber-400" />
        </motion.div>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring' }}
          className="text-4xl mb-2"
        >
          🔔
        </motion.div>
        <p className="text-sm">暂无通知</p>
      </div>
    );
  }

  const itemData: RowData = {
    notifications,
    onMarkRead,
    onDelete,
    onClick,
  };

  return (
    <div className="relative">
      <List
        ref={listRef}
        height={height}
        itemCount={notifications.length}
        itemSize={ITEM_HEIGHT}
        width="100%"
        itemData={itemData}
        onItemsRendered={handleItemsRendered}
        role="list"
      >
        {NotificationRow}
      </List>

      <AnimatePresence>
        {isFetchingNextPage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute bottom-0 left-0 right-0 flex justify-center py-2 bg-gradient-to-t from-gray-900 to-transparent"
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
