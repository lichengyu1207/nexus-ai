import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TaskFilters } from './components/TaskFilters';
import { TaskToolbar } from './components/TaskToolbar';
import { TaskList } from './components/TaskList';
import { TaskDetailSidebar } from './components/TaskDetailSidebar';
import { BatchActionModal } from './components/BatchActionModal';
import { NewTaskModal } from './components/NewTaskModal';
import { useTaskList } from './hooks/useTaskList';
import { useTaskFilters } from './hooks/useTaskFilters';
import { useBatchActions } from './hooks/useBatchActions';
import type { ViewMode, BatchAction, NewTaskPayload, TaskSortField, TaskSortOrder } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const mockAgents = [
  { id: 'agent-1', name: '估值智能体' },
  { id: 'agent-2', name: '数据分析智能体' },
  { id: 'agent-3', name: '报告生成智能体' },
  { id: 'agent-4', name: '风险评估智能体' },
];

function TaskCenterContent() {
  const navigate = useNavigate();
  const { filters, sort, updateFilters, resetFilters, updateSort } = useTaskFilters();
  const { tasks, total, isLoading, isFetching, hasNextPage, fetchNextPage, isFetchingNextPage, refetch } = useTaskList({
    filters,
    sort,
  });
  const { executeBatchAction, isPending } = useBatchActions();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [detailTaskId, setDetailTaskId] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [batchModal, setBatchModal] = useState<{ isOpen: boolean; action: BatchAction }>({
    isOpen: false,
    action: 'retry',
  });
  const [isNewTaskOpen, setIsNewTaskOpen] = useState(false);

  const selectedCount = selectedIds.size;
  const canCompare = selectedCount >= 2 && selectedCount <= 5;

  const handleSelectTask = useCallback((taskId: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(taskId);
      } else {
        next.delete(taskId);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback((selected: boolean) => {
    if (selected) {
      setSelectedIds(new Set(tasks.map((t) => t.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [tasks]);

  const handleTaskClick = useCallback((taskId: string) => {
    setDetailTaskId(taskId);
    setIsDetailOpen(true);
  }, []);

  const handleTaskRetry = useCallback(async (taskId: string) => {
    await executeBatchAction('retry', [taskId]);
    refetch();
  }, [executeBatchAction, refetch]);

  const handleTaskDelete = useCallback(async (taskId: string) => {
    await executeBatchAction('delete', [taskId]);
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.delete(taskId);
      return next;
    });
    refetch();
  }, [executeBatchAction, refetch]);

  const handleBatchAction = useCallback((action: BatchAction) => {
    setBatchModal({ isOpen: true, action });
  }, []);

  const handleBatchConfirm = useCallback(async () => {
    await executeBatchAction(batchModal.action, Array.from(selectedIds));
    setSelectedIds(new Set());
    setBatchModal({ isOpen: false, action: 'retry' });
    refetch();
  }, [batchModal.action, selectedIds, executeBatchAction, refetch]);

  const handleCompare = useCallback(() => {
    const ids = Array.from(selectedIds).join(',');
    navigate(`/tasks/compare?ids=${ids}`);
  }, [selectedIds, navigate]);

  const handleNewTask = useCallback(() => {
    setIsNewTaskOpen(true);
  }, []);

  const handleNewTaskSubmit = useCallback(async (payload: NewTaskPayload) => {
    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const data = await response.json();
        setIsNewTaskOpen(false);
        navigate(`/tasks/${data.id}`);
      }
    } catch (e) {
      console.error('Failed to create task:', e);
    }
  }, [navigate]);

  const handleSearch = useCallback((text: string) => {
    updateFilters({ searchText: text || undefined });
  }, [updateFilters]);

  const handleSortChange = useCallback((field: TaskSortField, order: TaskSortOrder) => {
    updateSort({ field, order });
  }, [updateSort]);

  const handleViewFullDetail = useCallback((taskId: string) => {
    setIsDetailOpen(false);
    navigate(`/tasks/${taskId}`);
  }, [navigate]);

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <TaskFilters
        filters={filters}
        onFilterChange={updateFilters}
        onReset={resetFilters}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="px-6 py-4 border-b border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">任务中心</h1>
              <p className="text-gray-400 text-sm mt-1">
                共 {total} 个任务
              </p>
            </div>
            <div className="flex items-center gap-2">
              {selectedCount > 0 && (
                <motion.span
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-sm"
                >
                  已选择 {selectedCount} 项
                </motion.span>
              )}
            </div>
          </div>
        </header>

        <TaskToolbar
          selectedCount={selectedCount}
          onBatchRetry={() => handleBatchAction('retry')}
          onBatchDelete={() => handleBatchAction('delete')}
          onBatchExport={() => handleBatchAction('export')}
          onCompare={handleCompare}
          onNewTask={handleNewTask}
          onSearch={handleSearch}
          onSortChange={handleSortChange}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          sortField={sort.field}
          sortOrder={sort.order}
          canCompare={canCompare}
        />

        <main className="flex-1 overflow-y-auto">
          <TaskList
            tasks={tasks}
            isLoading={isLoading}
            isFetching={isFetching}
            hasNextPage={hasNextPage}
            fetchNextPage={fetchNextPage}
            isFetchingNextPage={isFetchingNextPage}
            selectedIds={selectedIds}
            onSelectTask={handleSelectTask}
            onTaskClick={handleTaskClick}
            onTaskRetry={handleTaskRetry}
            onTaskDelete={handleTaskDelete}
            viewMode={viewMode}
          />
        </main>
      </div>

      <TaskDetailSidebar
        taskId={detailTaskId}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        onViewFullDetail={handleViewFullDetail}
        onRetry={handleTaskRetry}
        onDelete={handleTaskDelete}
      />

      <BatchActionModal
        isOpen={batchModal.isOpen}
        action={batchModal.action}
        count={selectedCount}
        onConfirm={handleBatchConfirm}
        onCancel={() => setBatchModal({ isOpen: false, action: 'retry' })}
        isPending={isPending}
      />

      <NewTaskModal
        isOpen={isNewTaskOpen}
        onClose={() => setIsNewTaskOpen(false)}
        onSubmit={handleNewTaskSubmit}
        isPending={false}
        agents={mockAgents}
      />
    </div>
  );
}

export default function TaskCenter() {
  return (
    <QueryClientProvider client={queryClient}>
      <TaskCenterContent />
    </QueryClientProvider>
  );
}
