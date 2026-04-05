import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { TreeNode } from '../types';

const API_BASE = '/api/assets/tree';

async function fetchAssetTree(): Promise<TreeNode[]> {
  const response = await fetch(API_BASE);
  if (!response.ok) {
    throw new Error('Failed to fetch asset tree');
  }
  return response.json();
}

async function createFolder(data: {
  name: string;
  parentId?: string;
  type: 'folder';
}): Promise<TreeNode> {
  const response = await fetch('/api/assets/folders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create folder');
  }
  return response.json();
}

async function updateFolder(
  id: string,
  data: { name?: string; parentId?: string }
): Promise<TreeNode> {
  const response = await fetch(`/api/assets/folders/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update folder');
  }
  return response.json();
}

async function deleteFolder(id: string): Promise<void> {
  const response = await fetch(`/api/assets/folders/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete folder');
  }
}

async function moveAsset(data: {
  assetId: string;
  targetFolderId?: string;
}): Promise<void> {
  const response = await fetch('/api/assets/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to move asset');
  }
}

export function useAssetTree() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['asset-tree'],
    queryFn: fetchAssetTree,
    staleTime: 5 * 60 * 1000,
  });

  const createFolderMutation = useMutation({
    mutationFn: createFolder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-tree'] });
    },
  });

  const updateFolderMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; parentId?: string } }) =>
      updateFolder(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-tree'] });
    },
  });

  const deleteFolderMutation = useMutation({
    mutationFn: deleteFolder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-tree'] });
    },
  });

  const moveAssetMutation = useMutation({
    mutationFn: moveAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-tree'] });
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });

  return {
    tree: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    createFolder: createFolderMutation.mutate,
    updateFolder: updateFolderMutation.mutate,
    deleteFolder: deleteFolderMutation.mutate,
    moveAsset: moveAssetMutation.mutate,
    isCreatingFolder: createFolderMutation.isPending,
    isUpdatingFolder: updateFolderMutation.isPending,
    isDeletingFolder: deleteFolderMutation.isPending,
    isMovingAsset: moveAssetMutation.isPending,
  };
}
