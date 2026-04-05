import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Recruitment, RecruitmentListResponse, RecruitmentStatus } from '../types';

const API_BASE = '/api/recruitments';

async function fetchRecruitments(params: {
  page?: number;
  limit?: number;
  status?: RecruitmentStatus;
  ownerId?: string;
}): Promise<RecruitmentListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.append('page', String(params.page));
  if (params.limit) searchParams.append('limit', String(params.limit));
  if (params.status) searchParams.append('status', params.status);
  if (params.ownerId) searchParams.append('ownerId', params.ownerId);

  const response = await fetch(`${API_BASE}?${searchParams}`);
  if (!response.ok) {
    throw new Error('Failed to fetch recruitments');
  }
  return response.json();
}

async function fetchRecruitmentById(id: string): Promise<Recruitment> {
  const response = await fetch(`${API_BASE}/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch recruitment');
  }
  return response.json();
}

async function createRecruitment(data: Partial<Recruitment>): Promise<Recruitment> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create recruitment');
  }
  return response.json();
}

async function updateRecruitment(id: string, data: Partial<Recruitment>): Promise<Recruitment> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to update recruitment');
  }
  return response.json();
}

async function deleteRecruitment(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete recruitment');
  }
}

export interface UseRecruitmentsOptions {
  status?: RecruitmentStatus;
  ownerId?: string;
  pageSize?: number;
}

export function useRecruitments(options: UseRecruitmentsOptions = {}) {
  const { status, ownerId, pageSize = 20 } = options;
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: ['recruitments', { status, ownerId }],
    queryFn: ({ pageParam = 1 }) => fetchRecruitments({ page: pageParam, limit: pageSize, status, ownerId }),
    getNextPageParam: (lastPage) => (lastPage.hasMore ? lastPage.page + 1 : undefined),
    initialPageParam: 1,
  });

  const createMutation = useMutation({
    mutationFn: createRecruitment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitments'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Recruitment> }) => updateRecruitment(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitments'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRecruitment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitments'] });
    },
  });

  const recruitments = query.data?.pages.flatMap((page) => page.recruitments) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;

  return {
    recruitments,
    total,
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    error: query.error,
    refetch: query.refetch,
    createRecruitment: createMutation.mutate,
    updateRecruitment: updateMutation.mutate,
    deleteRecruitment: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}

export function useRecruitment(id: string | null) {
  const query = useInfiniteQuery({
    queryKey: ['recruitment', id],
    queryFn: () => fetchRecruitmentById(id!),
    enabled: !!id,
  });

  return {
    recruitment: query.data?.pages[0],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
