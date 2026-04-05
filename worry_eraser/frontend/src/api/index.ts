import apiClient from './client';
import { ChatRequest, ChatResponse, Report, Agent } from '../types';

export const chatApi = {
  sendMessage: async (message: string, agent: 'zhouyu' | 'luxun'): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat', {
      message,
      agent,
    } as ChatRequest);
    return response.data;
  },

  getReport: async (reportId: string): Promise<Report> => {
    const response = await apiClient.get<Report>(`/report/${reportId}`);
    return response.data;
  },

  getAgents: async (): Promise<Agent[]> => {
    const response = await apiClient.get<Agent[]>('/agents');
    return response.data;
  },

  healthCheck: async (): Promise<{ status: string; service: string; version: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
