import { useQuery } from '@tanstack/react-query';
import { fetchTaskStats } from './api';

export const useTaskStats = () => {
  return useQuery({
    queryKey: ['taskStats'],
    queryFn: fetchTaskStats,
    refetchInterval: 10000,
  });
};
