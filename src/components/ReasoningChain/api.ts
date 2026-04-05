import axios from 'axios';
import type { ReasoningStep, FeedbackRequest, FeedbackResponse } from './types';

const apiClient = axios.create({ baseURL: '/api' });

export const fetchReasoningChain = async (taskId: string): Promise<ReasoningStep[]> => {
  const { data } = await apiClient.get(`/tasks/${taskId}/reasoning`);
  return data;
};

export const submitFeedback = async (
  taskId: string,
  feedback: FeedbackRequest
): Promise<FeedbackResponse> => {
  const { data } = await apiClient.post(`/tasks/${taskId}/reasoning/feedback`, feedback);
  return data;
};
