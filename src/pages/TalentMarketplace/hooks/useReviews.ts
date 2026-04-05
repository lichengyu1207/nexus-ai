import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Review } from '../types';

interface UseReviewsOptions {
  talentId?: string;
  projectId?: string;
}

interface CreateReviewData {
  toTalentId: string;
  rating: number;
  comment: string;
  projectId?: string;
}

async function fetchReviews(talentId: string): Promise<Review[]> {
  const response = await fetch(`/api/talents/${talentId}/reviews`);
  if (!response.ok) throw new Error('Failed to fetch reviews');
  return response.json();
}

async function createReview(data: CreateReviewData): Promise<Review> {
  const response = await fetch('/api/reviews', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create review');
  return response.json();
}

export function useReviews(options: UseReviewsOptions = {}) {
  const queryClient = useQueryClient();
  const { talentId, projectId } = options;

  const reviewsQuery = useQuery({
    queryKey: ['reviews', talentId, projectId],
    queryFn: () => fetchReviews(talentId!),
    enabled: !!talentId,
  });

  const createReviewMutation = useMutation({
    mutationFn: createReview,
    onSuccess: (newReview) => {
      queryClient.invalidateQueries({ queryKey: ['reviews', newReview.toTalentId] });
      queryClient.invalidateQueries({ queryKey: ['talent', newReview.toTalentId] });
    },
  });

  const averageRating = reviewsQuery.data
    ? reviewsQuery.data.reduce((sum, r) => sum + r.rating, 0) / reviewsQuery.data.length
    : 0;

  const ratingDistribution = reviewsQuery.data
    ? [5, 4, 3, 2, 1].map((rating) => ({
        rating,
        count: reviewsQuery.data.filter((r) => r.rating === rating).length,
        percentage: (reviewsQuery.data.filter((r) => r.rating === rating).length / reviewsQuery.data.length) * 100,
      }))
    : [];

  return {
    reviews: reviewsQuery.data ?? [],
    isLoading: reviewsQuery.isLoading,
    error: reviewsQuery.error,
    averageRating,
    ratingDistribution,
    totalReviews: reviewsQuery.data?.length ?? 0,
    createReview: createReviewMutation.mutate,
    isCreating: createReviewMutation.isPending,
    createError: createReviewMutation.error,
  };
}
