import api from '@/services/api';
import showToast from '@/utils/toast';

export interface Feedback {
  id: string;
  user_id: string;
  type: string;
  title: string | null;
  content: string;
  attachments: string[];
  status: string;
  admin_reply: string | null;
  replied_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackCreateParams {
  type: string;
  title?: string;
  content: string;
  attachments?: string[];
}

export interface FeedbackListResponse {
  items: Feedback[];
  total: number;
}

export const feedbackTypes = {
  feedback: '功能反馈',
  suggestion: '建议',
  bug: '问题报告',
  complaint: '投诉',
};

export const feedbackStatus = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  processing: { label: '处理中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  rejected: { label: '已拒绝', color: 'bg-gray-100 text-gray-700' },
};

export const submitFeedback = async (data: FeedbackCreateParams): Promise<Feedback> => {
  const response = await api.post('/feedback', data);
  return response.data.data;
};

export const getMyFeedbacks = async (limit: number = 20): Promise<FeedbackListResponse> => {
  const response = await api.get(`/feedback/my?limit=${limit}`);
  return response.data;
};

export const getFeedbackDetail = async (feedbackId: string): Promise<Feedback> => {
  const response = await api.get(`/feedback/${feedbackId}`);
  return response.data;
};

export const getFeedbackTypes = async (): Promise<Record<string, string>> => {
  const response = await api.get('/feedback/types');
  return response.data.types;
};

export const uploadAttachment = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data.url || response.data.path;
};
