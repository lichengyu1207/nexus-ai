import { useInfiniteQuery } from '@tanstack/react-query';
import type { Talent, TalentFilters, TalentListResponse } from '../types';

const API_BASE = '/api/talents';

async function fetchTalents(params: {
  page?: number;
  limit?: number;
} & TalentFilters): Promise<TalentListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.append('page', String(params.page));
  if (params.limit) searchParams.append('limit', String(params.limit));
  if (params.skills?.length) searchParams.append('skills', params.skills.join(','));
  if (params.domain) searchParams.append('domain', params.domain);
  if (params.priceMin) searchParams.append('priceMin', String(params.priceMin));
  if (params.priceMax) searchParams.append('priceMax', String(params.priceMax));
  if (params.ratingMin) searchParams.append('ratingMin', String(params.ratingMin));
  if (params.verified !== undefined) searchParams.append('verified', String(params.verified));
  if (params.availability) searchParams.append('availability', params.availability);
  if (params.location) searchParams.append('location', params.location);
  if (params.search) searchParams.append('search', params.search);

  const response = await fetch(`${API_BASE}?${searchParams}`);
  if (!response.ok) {
    throw new Error('Failed to fetch talents');
  }
  return response.json();
}

async function fetchTalentById(id: string): Promise<Talent> {
  const response = await fetch(`${API_BASE}/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch talent');
  }
  return response.json();
}

export interface UseTalentsOptions {
  filters?: TalentFilters;
  pageSize?: number;
}

export function useTalents(options: UseTalentsOptions = {}) {
  const { filters = {}, pageSize = 20 } = options;

  const query = useInfiniteQuery({
    queryKey: ['talents', filters],
    queryFn: ({ pageParam = 1 }) => fetchTalents({ page: pageParam, limit: pageSize, ...filters }),
    getNextPageParam: (lastPage) => (lastPage.hasMore ? lastPage.page + 1 : undefined),
    initialPageParam: 1,
  });

  const talents = query.data?.pages.flatMap((page) => page.talents) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;

  return {
    talents,
    total,
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    error: query.error,
    refetch: query.refetch,
  };
}

export function useTalent(id: string | null) {
  const query = useInfiniteQuery({
    queryKey: ['talent', id],
    queryFn: () => fetchTalentById(id!),
    enabled: !!id,
  });

  return {
    talent: query.data?.pages[0],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
