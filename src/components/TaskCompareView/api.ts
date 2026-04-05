import axios from 'axios';
import { CompareResponse } from './types';

export const fetchCompareData = async (taskIds: string[]): Promise<CompareResponse> => {
  const params = { taskIds: taskIds.join(',') };
  const { data } = await axios.get('/api/tasks/compare', { params });
  return data;
};

export const fetchAvailableTasks = async (): Promise<{ id: string; name: string; completedAt: string }[]> => {
  const { data } = await axios.get('/api/tasks', { params: { status: 'completed' } });
  return data.tasks || data;
};
