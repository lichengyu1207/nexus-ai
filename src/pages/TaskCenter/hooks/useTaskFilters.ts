import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { TaskFilters, TaskSort, TaskStatus, TaskSortField, TaskSortOrder } from '../types';

const defaultFilters: TaskFilters = {
  status: [],
};

const defaultSort: TaskSort = {
  field: 'createdAt',
  order: 'desc',
};

export function useTaskFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<TaskFilters>(() => {
    const status = searchParams.get('status');
    const startDate = searchParams.get('startDate');
    const endDate = searchParams.get('endDate');
    const agentIds = searchParams.get('agentIds');
    const tags = searchParams.get('tags');
    const search = searchParams.get('search');

    return {
      status: status ? (status.split(',') as TaskStatus[]) : [],
      dateRange: startDate && endDate ? { start: startDate, end: endDate } : undefined,
      agentIds: agentIds ? agentIds.split(',') : undefined,
      tags: tags ? tags.split(',') : undefined,
      searchText: search || undefined,
    };
  });

  const [sort, setSort] = useState<TaskSort>(() => {
    const sortField = searchParams.get('sortField') as TaskSortField;
    const sortOrder = searchParams.get('sortOrder') as TaskSortOrder;

    return {
      field: sortField || defaultSort.field,
      order: sortOrder || defaultSort.order,
    };
  });

  const updateFilters = useCallback((newFilters: Partial<TaskFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(defaultFilters);
    setSort(defaultSort);
  }, []);

  const updateSort = useCallback((newSort: Partial<TaskSort>) => {
    setSort((prev) => ({ ...prev, ...newSort }));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.status.length > 0) {
      params.set('status', filters.status.join(','));
    }
    if (filters.dateRange) {
      params.set('startDate', filters.dateRange.start);
      params.set('endDate', filters.dateRange.end);
    }
    if (filters.agentIds && filters.agentIds.length > 0) {
      params.set('agentIds', filters.agentIds.join(','));
    }
    if (filters.tags && filters.tags.length > 0) {
      params.set('tags', filters.tags.join(','));
    }
    if (filters.searchText) {
      params.set('search', filters.searchText);
    }
    if (sort.field !== defaultSort.field) {
      params.set('sortField', sort.field);
    }
    if (sort.order !== defaultSort.order) {
      params.set('sortOrder', sort.order);
    }

    setSearchParams(params, { replace: true });
  }, [filters, sort, setSearchParams]);

  return {
    filters,
    sort,
    updateFilters,
    resetFilters,
    updateSort,
  };
}
