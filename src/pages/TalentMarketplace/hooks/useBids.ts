import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Bid, BidStatus } from '../types';

const API_BASE = '/api/bids';

async function fetchBids(params: {
  page?: number;
  limit?: number;
  recruitmentId?: string;
  talentId?: string;
  status?: BidStatus;
}): Promise<{ bids: Bid[]; total: number; page: number; limit: number; hasMore: boolean }> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.append('page', String(params.page));
  if (params.limit) searchParams.append('limit', String(params.limit));
  if (params.recruitmentId) searchParams.append('recruitmentId', params.recruitmentId);
  if (params.talentId) searchParams.append('talentId', params.talentId);
  if (params.status) searchParams.append('status', params.status);

  const response = await fetch(`${API_BASE}?${searchParams}`);
  if (!response.ok) {
    throw new Error('Failed to fetch bids');
  }
  return response.json();
}

async function createBid(data: Partial<Bid>): Promise<Bid> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create bid');
  }
  return response.json();
}

async function updateBidStatus(id: string, status: BidStatus): Promise<Bid> {
  const response = await fetch(`${API_BASE}/${id}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) {
    throw new Error('Failed to update bid status');
  }
  return response.json();
}

export interface UseBidsOptions {
  recruitmentId?: string;
  talentId?: string;
  status?: BidStatus;
  pageSize?: number;
}

export function useBids(options: UseBidsOptions = {}) {
  const { recruitmentId, talentId, status, pageSize = 20 } = options;
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: ['bids', { recruitmentId, talentId, status }],
    queryFn: ({ pageParam = 1 }) => fetchBids({ page: pageParam, limit: pageSize, recruitmentId, talentId, status }),
    getNextPageParam: (lastPage) => (lastPage.hasMore ? lastPage.page + 1 : undefined),
    initialPageParam: 1,
  });

  const createMutation = useMutation({
    mutationFn: createBid,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bids'] });
      queryClient.invalidateQueries({ queryKey: ['recruitment'] });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: BidStatus }) => updateBidStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bids'] });
      queryClient.invalidateQueries({ queryKey: ['recruitments'] });
    },
  });

  const bids = query.data?.pages.flatMap((page) => page.bids) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;

  return {
    bids,
    total,
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    error: query.error,
    refetch: query.refetch,
    createBid: createMutation.mutate,
    updateBidStatus: updateStatusMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdatingStatus: updateStatusMutation.isPending,
  };
}
