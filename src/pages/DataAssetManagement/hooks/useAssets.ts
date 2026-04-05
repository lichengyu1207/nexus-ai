import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Asset, AssetListResponse } from '../types';

const API_BASE = '/api/assets';

async function fetchAssets(params: {
  parentId?: string;
  type?: string;
  page?: number;
  limit?: number;
  search?: string;
}): Promise<AssetListResponse> {
  const searchParams = new URLSearchParams();
  if (params.parentId) searchParams.append('parentId', params.parentId);
  if (params.type) searchParams.append('type', params.type);
  if (params.page) searchParams.append('page', String(params.page));
  if (params.limit) searchParams.append('limit', String(params.limit));
  if (params.search) searchParams.append('search', params.search);

  const response = await fetch(`${API_BASE}?${searchParams}`);
  if (!response.ok) {
    throw new Error('Failed to fetch assets');
  }
  return response.json();
}

async function createAsset(data: Partial<Asset>): Promise<Asset> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create asset');
  }
  return response.json();
}

async function updateAsset(id: string, data: Partial<Asset>): Promise<Asset> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update asset');
  }
  return response.json();
}

async function deleteAsset(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete asset');
  }
}

export interface UseAssetsOptions {
  parentId?: string;
  type?: string;
  page?: number;
  limit?: number;
  search?: string;
}

export function useAssets(options: UseAssetsOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['assets', options],
    queryFn: () => fetchAssets(options),
  });

  const createMutation = useMutation({
    mutationFn: createAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['asset-tree'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Asset> }) =>
      updateAsset(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['asset-detail'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['asset-tree'] });
    },
  });

  return {
    assets: query.data?.assets ?? [],
    total: query.data?.total ?? 0,
    page: query.data?.page ?? 1,
    hasMore: query.data?.hasMore ?? false,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    createAsset: createMutation.mutate,
    updateAsset: updateMutation.mutate,
    deleteAsset: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
