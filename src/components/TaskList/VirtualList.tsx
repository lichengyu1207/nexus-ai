import React, { useRef, useCallback, useEffect, useState } from 'react';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoading?: boolean;
  loadingComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
}

function VirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  onLoadMore,
  hasMore = false,
  isLoading = false,
  loadingComponent,
  emptyComponent,
}: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const totalHeight = items.length * itemHeight;
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    items.length - 1,
    Math.floor((scrollTop + containerHeight) / itemHeight) + 2
  );
  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !onLoadMore || !hasMore) return;

    const handleScrollEvent = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      if (scrollHeight - scrollTop - clientHeight < 200 && !isLoading) {
        onLoadMore();
      }
    };

    container.addEventListener('scroll', handleScrollEvent);
    return () => container.removeEventListener('scroll', handleScrollEvent);
  }, [onLoadMore, hasMore, isLoading]);

  if (items.length === 0 && !isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        {emptyComponent || (
          <div className="text-center text-gray-500 dark:text-gray-400 py-12">
            <p className="text-lg">暂无任务</p>
            <p className="text-sm mt-1">点击右上角"新建任务"开始</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="overflow-y-auto"
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => renderItem(item, startIndex + index))}
        </div>
      </div>
      {isLoading && (
        <div className="py-4 flex justify-center">
          {loadingComponent || (
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-amber-500 border-t-transparent" />
          )}
        </div>
      )}
    </div>
  );
}

export default VirtualList;
