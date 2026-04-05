import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Skill, SkillListResponse } from '../types';

const API_BASE = '/api/skills';

async function fetchSkills(params: {
  page?: number;
  limit?: number;
  category?: string;
  search?: string;
}): Promise<SkillListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.append('page', String(params.page));
  if (params.limit) searchParams.append('limit', String(params.limit));
  if (params.category) searchParams.append('category', params.category);
  if (params.search) searchParams.append('search', params.search);

  const response = await fetch(`${API_BASE}?${searchParams}`);
  if (!response.ok) {
    throw new Error('Failed to fetch skills');
  }
  return response.json();
}

async function fetchSkillById(id: string): Promise<Skill> {
  const response = await fetch(`${API_BASE}/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch skill');
  }
  return response.json();
}

async function subscribeSkill(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}/subscribe`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to subscribe skill');
  }
}

export interface UseSkillsOptions {
  category?: string;
  search?: string;
  pageSize?: number;
}

export function useSkills(options: UseSkillsOptions = {}) {
  const { category, search, pageSize = 20 } = options;

  const query = useInfiniteQuery({
    queryKey: ['skills', { category, search }],
    queryFn: ({ pageParam = 1 }) => fetchSkills({ page: pageParam, limit: pageSize, category, search }),
    getNextPageParam: (lastPage) => (lastPage.hasMore ? lastPage.page + 1 : undefined),
    initialPageParam: 1,
  });

  const skills = query.data?.pages.flatMap((page) => page.skills) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;

  return {
    skills,
    total,
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    error: query.error,
    refetch: query.refetch,
  };
}

export function useSkill(id: string | null) {
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: ['skill', id],
    queryFn: () => fetchSkillById(id!),
    enabled: !!id,
  });

  const subscribeMutation = useMutation({
    mutationFn: subscribeSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skill', id] });
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  return {
    skill: query.data?.pages[0],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    subscribe: subscribeMutation.mutate,
    isSubscribing: subscribeMutation.isPending,
  };
}
