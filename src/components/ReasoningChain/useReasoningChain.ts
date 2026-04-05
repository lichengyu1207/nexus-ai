import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchReasoningChain, submitFeedback } from './api';
import type { FeedbackRequest, ReasoningStep } from './types';
import toast from 'react-hot-toast';

export const useReasoningChain = (taskId: string) => {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['reasoningChain', taskId],
    queryFn: () => fetchReasoningChain(taskId),
    enabled: !!taskId,
  });

  const feedbackMutation = useMutation({
    mutationFn: (feedback: FeedbackRequest) => submitFeedback(taskId, feedback),
    onSuccess: (_, variables) => {
      queryClient.setQueryData<ReasoningStep[]>(['reasoningChain', taskId], (old) => {
        if (!old) return old;
        return old.map((step, idx) =>
          idx === variables.stepIndex ? { ...step, feedbackGiven: true } : step
        );
      });
      toast.success('感谢反馈！');
    },
    onError: () => {
      toast.error('反馈失败，请重试');
    },
  });

  return {
    steps: data ?? [],
    isLoading,
    error,
    refetch,
    submitFeedback: feedbackMutation.mutate,
  };
};
