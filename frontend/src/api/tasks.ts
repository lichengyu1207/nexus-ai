import api from './client';
import { Task, Report, PaginatedResponse } from '../types';

export const taskApi = {
  list: async (params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ tasks: Task[]; total: number }> => {
    const response = await api.get('/api/tasks', { params });
    return response.data;
  },

  get: async (taskId: string): Promise<Task> => {
    const response = await api.get(`/api/tasks/${taskId}`);
    return response.data;
  },

  create: async (data: { query: string; type?: string }): Promise<Task> => {
    const response = await api.post('/api/tasks', data);
    return response.data;
  },

  getReport: async (taskId: string): Promise<Report> => {
    const response = await api.get(`/api/tasks/${taskId}/report`);
    return response.data;
  },

  getSteps: async (taskId: string): Promise<any[]> => {
    const response = await api.get(`/api/tasks/${taskId}/steps`);
    return response.data.steps || [];
  },

  streamProgress: (taskId: string): EventSource => {
    const baseUrl = api.defaults.baseURL || 'http://localhost:8000';
    return new EventSource(`${baseUrl}/api/tasks/${taskId}/stream`);
  },
};

export default taskApi;
