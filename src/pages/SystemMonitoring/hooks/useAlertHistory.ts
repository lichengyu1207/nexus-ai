import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { AlertEvent, AlertStatus, AlertSeverity } from '../types';

interface UseAlertHistoryOptions {
  from?: number;
  to?: number;
  status?: AlertStatus;
  severity?: AlertSeverity;
  page?: number;
  pageSize?: number;
}

interface AlertHistoryResponse {
  events: AlertEvent[];
  total: number;
  page: number;
  pageSize: number;
}

async function fetchAlertHistory(options: UseAlertHistoryOptions): Promise<AlertHistoryResponse> {
  const params = new URLSearchParams();
  
  if (options.from) params.set('from', options.from.toString());
  if (options.to) params.set('to', options.to.toString());
  if (options.status) params.set('status', options.status);
  if (options.severity) params.set('severity', options.severity);
  if (options.page) params.set('page', options.page.toString());
  if (options.pageSize) params.set('pageSize', options.pageSize.toString());

  const response = await fetch(`/api/monitoring/alerts/history?${params}`);
  if (!response.ok) throw new Error('Failed to fetch alert history');
  return response.json();
}

export function useAlertHistory(options: UseAlertHistoryOptions = {}) {
  const [page, setPage] = useState(options.page || 1);
  const pageSize = options.pageSize || 20;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['alert-history', options.from, options.to, options.status, options.severity, page, pageSize],
    queryFn: () => fetchAlertHistory({ ...options, page, pageSize }),
    staleTime: 10000,
  });

  const nextPage = () => {
    if (data && page * pageSize < data.total) {
      setPage(page + 1);
    }
  };

  const prevPage = () => {
    if (page > 1) {
      setPage(page - 1);
    }
  };

  const goToPage = (newPage: number) => {
    if (data && newPage > 0 && newPage <= Math.ceil(data.total / pageSize)) {
      setPage(newPage);
    }
  };

  return {
    events: data?.events || [],
    total: data?.total || 0,
    page,
    pageSize,
    totalPages: data ? Math.ceil(data.total / pageSize) : 0,
    isLoading,
    error,
    refetch,
    nextPage,
    prevPage,
    goToPage,
  };
}

export default useAlertHistory;
