import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { HealthCheck, HealthStatus } from '../types';

async function fetchHealthChecks(): Promise<HealthCheck[]> {
  const response = await fetch('/api/monitoring/health');
  if (!response.ok) throw new Error('Failed to fetch health checks');
  return response.json();
}

async function triggerHealthCheck(): Promise<HealthCheck[]> {
  const response = await fetch('/api/monitoring/health/check', {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to trigger health check');
  return response.json();
}

export function useHealthChecks() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['health-checks'],
    queryFn: fetchHealthChecks,
    staleTime: 300000, // 5 minutes
    refetchInterval: 60000, // 1 minute
  });

  const triggerMutation = useMutation({
    mutationFn: triggerHealthCheck,
    onSuccess: (newData) => {
      queryClient.setQueryData(['health-checks'], newData);
    },
  });

  const getStatusCounts = () => {
    if (!data) return { healthy: 0, degraded: 0, down: 0 };
    
    return data.reduce(
      (acc, check) => {
        acc[check.status]++;
        return acc;
      },
      { healthy: 0, degraded: 0, down: 0 } as Record<HealthStatus, number>
    );
  };

  const getOverallStatus = (): HealthStatus => {
    const counts = getStatusCounts();
    if (counts.down > 0) return 'down';
    if (counts.degraded > 0) return 'degraded';
    return 'healthy';
  };

  return {
    checks: data || [],
    isLoading,
    error,
    refetch,
    triggerCheck: triggerMutation.mutate,
    isTriggering: triggerMutation.isPending,
    getStatusCounts,
    getOverallStatus,
  };
}

export default useHealthChecks;
