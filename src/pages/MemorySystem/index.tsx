import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { useMemories } from './hooks/useMemories';
import { useUpdateImportance } from './hooks/useUpdateImportance';
import { MemoryFilterSidebar } from './components/MemoryFilterSidebar';
import { MemoryCardList } from './components/MemoryCardList';
import { MemoryDetailDrawer } from './components/MemoryDetailDrawer';
import { MemoryGraphView } from './components/MemoryGraphView';
import { SearchBar } from './components/SearchBar';
import { MemoryFilters, ViewMode, SortBy } from './types';

const mockDateRange = {
  earliest: '2023-01-01T00:00:00Z',
  latest: '2024-12-31T23:59:59Z',
};

export const MemorySystem: React.FC = () => {
  const [filters, setFilters] = useState<MemoryFilters>({});
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [sortBy, setSortBy] = useState<SortBy>('time');
  const [selectedMemoryId, setSelectedMemoryId] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useMemories(filters);

  const updateImportance = useUpdateImportance();

  const allMemories = useMemo(() => {
    const memories = data?.pages.flatMap((page) => page.items) ?? [];
    
    if (sortBy === 'importance') {
      return [...memories].sort((a, b) => b.importance - a.importance);
    }
    return [...memories].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  }, [data, sortBy]);

  const totalCount = data?.pages[0]?.total ?? 0;

  const handleFilterChange = useCallback((newFilters: MemoryFilters) => {
    setFilters(newFilters);
  }, []);

  const handleMemoryClick = useCallback((id: string) => {
    setSelectedMemoryId(id);
    setIsDetailOpen(true);
  }, []);

  const handleStarToggle = useCallback(
    (id: string, importance: number) => {
      updateImportance.mutate({ memoryId: id, importance });
    },
    [updateImportance]
  );

  const handleCloseDetail = useCallback(() => {
    setIsDetailOpen(false);
  }, []);

  const handleSearch = useCallback(
    (query: string) => {
      setSearchQuery(query);
      setFilters((prev) => ({ ...prev, searchText: query || undefined }));
    },
    []
  );

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const handleNavigateToMemory = useCallback(
    (id: string) => {
      setSelectedMemoryId(id);
    },
    []
  );

  return (
    <div className="h-screen flex bg-bg-primary">
      <MemoryFilterSidebar
        filters={filters}
        onFilterChange={handleFilterChange}
        totalCount={totalCount}
        dateRange={mockDateRange}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-border-light bg-bg-secondary/30">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-text-primary">记忆库</h1>
              <span className="text-sm text-text-secondary">
                {totalCount.toLocaleString()} 条记忆
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('card')}
                className={clsx(
                  'p-2 rounded-lg transition-all',
                  viewMode === 'card'
                    ? 'bg-primary/20 text-primary'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                )}
                aria-label="卡片模式"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={clsx(
                  'p-2 rounded-lg transition-all',
                  viewMode === 'graph'
                    ? 'bg-primary/20 text-primary'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                )}
                aria-label="图谱模式"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </button>
              <div className="w-px h-6 bg-border-light mx-2" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="px-3 py-1.5 text-sm bg-bg-secondary/60 border border-border-light rounded-lg text-text-primary focus:outline-none focus:border-primary/50"
              >
                <option value="time">按时间排序</option>
                <option value="importance">按重要度排序</option>
              </select>
              <button className="px-4 py-2 text-sm bg-primary text-bg-primary rounded-lg hover:bg-primary-dark transition-colors">
                + 新建记忆
              </button>
            </div>
          </div>

          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onSearch={handleSearch}
            placeholder="搜索记忆内容、标签..."
          />
        </div>

        <div className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={viewMode}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {viewMode === 'card' ? (
                <MemoryCardList
                  memories={allMemories}
                  onMemoryClick={handleMemoryClick}
                  onStarToggle={handleStarToggle}
                  selectedId={selectedMemoryId}
                  loading={isLoading}
                  hasMore={hasNextPage ?? false}
                  loadMore={handleLoadMore}
                />
              ) : (
                <div className="h-full p-6">
                  <MemoryGraphView
                    memories={allMemories}
                    onNodeClick={handleMemoryClick}
                    highlightNodeIds={selectedMemoryId ? [selectedMemoryId] : []}
                  />
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      <MemoryDetailDrawer
        memoryId={selectedMemoryId}
        isOpen={isDetailOpen}
        onClose={handleCloseDetail}
        onNavigateToMemory={handleNavigateToMemory}
      />
    </div>
  );
};

export default MemorySystem;
