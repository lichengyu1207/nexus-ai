import { useQuery } from '@tanstack/react-query';
import type { QualityStats, QualityMetric, QualityTrend } from '../types';

const API_BASE = '/api/assets';

async function fetchQualityStats(): Promise<QualityStats> {
  const response = await fetch(`${API_BASE}/quality-stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch quality stats');
  }
  return response.json();
}

async function fetchAssetQualityMetric(assetId: string): Promise<QualityMetric> {
  const response = await fetch(`${API_BASE}/${assetId}/quality`);
  if (!response.ok) {
    throw new Error('Failed to fetch asset quality metric');
  }
  return response.json();
}

async function fetchQualityTrend(
  assetId: string,
  period: '7d' | '30d' | '90d' = '30d'
): Promise<QualityTrend[]> {
  const response = await fetch(`${API_BASE}/${assetId}/quality/trend?period=${period}`);
  if (!response.ok) {
    throw new Error('Failed to fetch quality trend');
  }
  return response.json();
}

export interface UseQualityStatsOptions {
  refetchInterval?: number;
}

export function useQualityStats(options: UseQualityStatsOptions = {}) {
  const { refetchInterval = 10 * 60 * 1000 } = options;

  const query = useQuery({
    queryKey: ['quality-stats'],
    queryFn: fetchQualityStats,
    refetchInterval,
    staleTime: 5 * 60 * 1000,
  });

  return {
    stats: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

export interface UseAssetQualityOptions {
  assetId: string | null;
  period?: '7d' | '30d' | '90d';
}

export function useAssetQuality(options: UseAssetQualityOptions) {
  const { assetId, period = '30d' } = options;

  const metricQuery = useQuery({
    queryKey: ['asset-quality', assetId],
    queryFn: () => fetchAssetQualityMetric(assetId!),
    enabled: !!assetId,
  });

  const trendQuery = useQuery({
    queryKey: ['asset-quality-trend', assetId, period],
    queryFn: () => fetchQualityTrend(assetId!, period),
    enabled: !!assetId,
  });

  return {
    metric: metricQuery.data,
    trend: trendQuery.data ?? [],
    isLoadingMetric: metricQuery.isLoading,
    isLoadingTrend: trendQuery.isLoading,
    error: metricQuery.error || trendQuery.error,
    refetchMetric: metricQuery.refetch,
    refetchTrend: trendQuery.refetch,
  };
}
