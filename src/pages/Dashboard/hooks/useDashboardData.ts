import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { DashboardData } from '../types';

export const useDashboardData = () => {
  return useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data } = await axios.get('/api/dashboard');
      return data;
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  });
};

export const useHealthData = () => {
  const { data, isLoading, error } = useDashboardData();
  return {
    health: data?.health ?? 0,
    isLoading,
    error,
  };
};

export const useRecentTasks = () => {
  const { data, isLoading, error } = useDashboardData();
  return {
    tasks: data?.recentTasks ?? [],
    isLoading,
    error,
  };
};

export const useCrossEndEvents = () => {
  const { data, isLoading, error } = useDashboardData();
  return {
    events: data?.crossEndEvents ?? [],
    isLoading,
    error,
  };
};

export const useAgentTopology = () => {
  const { data, isLoading, error } = useDashboardData();
  return {
    topology: data?.agentTopology ?? { nodes: [], links: [] },
    isLoading,
    error,
  };
};
