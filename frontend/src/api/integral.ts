import api from './client';
import { IntegralLog, PaginatedResponse } from '../types';

export const integralApi = {
  getBalance: async (): Promise<{ balance: number }> => {
    const response = await api.get('/api/integral/balance');
    return response.data;
  },

  getLogs: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<{ logs: IntegralLog[]; total: number }> => {
    const response = await api.get('/api/integral/logs', { params });
    return response.data;
  },

  consume: async (amount: number, reason: string): Promise<{ balance: number }> => {
    const response = await api.post('/api/integral/consume', { amount, reason });
    return response.data;
  },
};

export default integralApi;
