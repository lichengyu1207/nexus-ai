import axios from 'axios';
import type { Task, TasksResponse, TaskStats, TaskStatus } from './types';

const apiClient = axios.create({ baseURL: '/api' });

export const fetchTasks = async (params: {
  status?: TaskStatus | '';
  sort?: 'asc' | 'desc';
  page: number;
  limit: number;
}): Promise<TasksResponse> => {
  const { data } = await apiClient.get('/tasks', { params });
  return data;
};

export const deleteTasks = async (taskIds: string[]): Promise<{ success: boolean }> => {
  const { data } = await apiClient.delete('/tasks', { data: { taskIds } });
  return data;
};

export const fetchTaskStats = async (): Promise<TaskStats> => {
  const { data } = await apiClient.get('/tasks/stats');
  return data;
};
