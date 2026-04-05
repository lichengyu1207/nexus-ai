import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { MetricSeries, TimeRange, MetricSummary } from '../types';

interface UseMetricsOptions {
  metrics: string[];
  timeRange: TimeRange;
  step?: number;
  refreshInterval?: number;
}

async function fetchMetrics(
  metrics: string[],
  from: number,
  to: number,
  step: number
): Promise<MetricSeries[]> {
  const params = new URLSearchParams({
    metrics: metrics.join(','),
    from: from.toString(),
    to: to.toString(),
    step: step.toString(),
  });
  
  const response = await fetch(`/api/monitoring/metrics?${params}`);
  if (!response.ok) throw new Error('Failed to fetch metrics');
  return response.json();
}

export function useMetrics({
  metrics,
  timeRange,
  step = 60,
  refreshInterval = 30000,
}: UseMetricsOptions) {
  const [summaries, setSummaries] = useState<MetricSummary[]>([]);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['metrics', metrics, timeRange.from, timeRange.to, step],
    queryFn: () => fetchMetrics(metrics, timeRange.from, timeRange.to, step),
    staleTime: refreshInterval,
    refetchInterval: refreshInterval,
  });

  useEffect(() => {
    if (data) {
      const newSummaries = data.map((series) => {
        const latestValue = series.data[series.data.length - 1]?.value || 0;
        const previousValue = series.data[series.data.length - 2]?.value || latestValue;
        const trendValue = previousValue > 0 
          ? ((latestValue - previousValue) / previousValue) * 100 
          : 0;
        
        let status: 'normal' | 'warning' | 'critical' = 'normal';
        if (series.unit === '%') {
          if (latestValue >= 90) status = 'critical';
          else if (latestValue >= 70) status = 'warning';
        }

        return {
          name: series.metric,
          value: latestValue,
          unit: series.unit,
          trend: trendValue > 1 ? 'up' : trendValue < -1 ? 'down' : 'stable',
          trendValue: Math.abs(trendValue),
          status,
        };
      });
      setSummaries(newSummaries);
    }
  }, [data]);

  const refresh = useCallback(() => {
    refetch();
  }, [refetch]);

  return {
    data,
    summaries,
    isLoading,
    error,
    refresh,
  };
}

export default useMetrics;
