import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AssetDetail, AssetVersion, Permission } from '../types';

const API_BASE = '/api/assets';

async function fetchAssetDetail(id: string): Promise<AssetDetail> {
  const response = await fetch(`${API_BASE}/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch asset detail');
  }
  return response.json();
}

async function fetchAssetVersions(id: string): Promise<AssetVersion[]> {
  const response = await fetch(`${API_BASE}/${id}/versions`);
  if (!response.ok) {
    throw new Error('Failed to fetch asset versions');
  }
  return response.json();
}

async function restoreVersion(assetId: string, version: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${assetId}/versions/${version}/restore`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to restore version');
  }
}

async function fetchAssetPermissions(id: string): Promise<Permission[]> {
  const response = await fetch(`${API_BASE}/${id}/permissions`);
  if (!response.ok) {
    throw new Error('Failed to fetch asset permissions');
  }
  return response.json();
}

async function updatePermissions(
  id: string,
  permissions: Partial<Permission>[]
): Promise<Permission[]> {
  const response = await fetch(`${API_BASE}/${id}/permissions`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ permissions }),
  });
  if (!response.ok) {
    throw new Error('Failed to update permissions');
  }
  return response.json();
}

export function useAssetDetail(id: string | null) {
  const queryClient = useQueryClient();

  const detailQuery = useQuery({
    queryKey: ['asset-detail', id],
    queryFn: () => fetchAssetDetail(id!),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
  });

  const versionsQuery = useQuery({
    queryKey: ['asset-versions', id],
    queryFn: () => fetchAssetVersions(id!),
    enabled: !!id,
  });

  const permissionsQuery = useQuery({
    queryKey: ['asset-permissions', id],
    queryFn: () => fetchAssetPermissions(id!),
    enabled: !!id,
  });

  const restoreMutation = useMutation({
    mutationFn: ({ assetId, version }: { assetId: string; version: number }) =>
      restoreVersion(assetId, version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['asset-versions', id] });
    },
  });

  const updatePermissionsMutation = useMutation({
    mutationFn: (permissions: Partial<Permission>[]) =>
      updatePermissions(id!, permissions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-permissions', id] });
    },
  });

  return {
    detail: detailQuery.data,
    versions: versionsQuery.data ?? [],
    permissions: permissionsQuery.data ?? [],
    isLoading: detailQuery.isLoading,
    isLoadingVersions: versionsQuery.isLoading,
    isLoadingPermissions: permissionsQuery.isLoading,
    error: detailQuery.error,
    restoreVersion: restoreMutation.mutate,
    updatePermissions: updatePermissionsMutation.mutate,
    isRestoring: restoreMutation.isPending,
    isUpdatingPermissions: updatePermissionsMutation.isPending,
    refetch: detailQuery.refetch,
    refetchVersions: versionsQuery.refetch,
    refetchPermissions: permissionsQuery.refetch,
  };
}
