import { useQuery } from '@tanstack/react-query';
import type { AuditLogEntry, AuditLogFilters, AuditLogResponse } from '../types';

interface UseAuditLogsParams {
  page?: number;
  filters?: AuditLogFilters;
  enabled?: boolean;
}

async function fetchAuditLogs(
  page: number,
  filters?: AuditLogFilters
): Promise<AuditLogResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('limit', '20');

  if (filters?.startDate) {
    params.append('startDate', filters.startDate);
  }
  if (filters?.endDate) {
    params.append('endDate', filters.endDate);
  }
  if (filters?.actor) {
    params.append('actor', filters.actor);
  }
  if (filters?.actionType) {
    params.append('actionType', filters.actionType);
  }
  if (filters?.result) {
    params.append('result', filters.result);
  }

  const response = await fetch(`/api/admin/audit-logs?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch audit logs');
  }
  return response.json();
}

async function exportAuditLogs(filters?: AuditLogFilters): Promise<Blob> {
  const params = new URLSearchParams();

  if (filters?.startDate) {
    params.append('startDate', filters.startDate);
  }
  if (filters?.endDate) {
    params.append('endDate', filters.endDate);
  }
  if (filters?.actor) {
    params.append('actor', filters.actor);
  }
  if (filters?.actionType) {
    params.append('actionType', filters.actionType);
  }
  if (filters?.result) {
    params.append('result', filters.result);
  }

  const response = await fetch(`/api/admin/audit-logs/export?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to export audit logs');
  }
  return response.blob();
}

export function useAuditLogs({
  page = 1,
  filters,
  enabled = true,
}: UseAuditLogsParams) {
  const query = useQuery<AuditLogResponse, Error>({
    queryKey: ['auditLogs', page, filters],
    queryFn: () => fetchAuditLogs(page, filters),
    enabled,
    staleTime: 30000,
  });

  const handleExport = async () => {
    const blob = await exportAuditLogs(filters);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return {
    logs: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    nextPage: query.data?.nextPage,
    isLoading: query.isLoading,
    error: query.error,
    exportLogs: handleExport,
    refetch: query.refetch,
  };
}
