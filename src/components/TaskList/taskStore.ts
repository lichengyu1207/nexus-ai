import { create } from 'zustand';
import type { TaskStatus } from './types';

interface TaskListState {
  statusFilter: TaskStatus | '';
  sortOrder: 'asc' | 'desc';
  page: number;
  selectedIds: Set<string>;
  hasMore: boolean;
  setStatusFilter: (status: TaskStatus | '') => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  resetPage: () => void;
  setHasMore: (hasMore: boolean) => void;
  toggleSelect: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelected: () => void;
}

export const useTaskListStore = create<TaskListState>((set) => ({
  statusFilter: '',
  sortOrder: 'desc',
  page: 1,
  selectedIds: new Set(),
  hasMore: true,
  setStatusFilter: (status) => set({ statusFilter: status, page: 1, selectedIds: new Set() }),
  setSortOrder: (order) => set({ sortOrder: order, page: 1, selectedIds: new Set() }),
  resetPage: () => set({ page: 1 }),
  setHasMore: (hasMore) => set({ hasMore }),
  toggleSelect: (id) =>
    set((state) => {
      const newSet = new Set(state.selectedIds);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      return { selectedIds: newSet };
    }),
  selectAll: (ids) => set({ selectedIds: new Set(ids) }),
  clearSelected: () => set({ selectedIds: new Set() }),
}));
