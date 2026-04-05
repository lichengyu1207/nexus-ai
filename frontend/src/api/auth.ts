import api from './client';
import { User, ApiResponse } from '../types';

export const authApi = {
  login: async (email: string, password: string): Promise<{ user: User; token: string }> => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  register: async (data: {
    email: string;
    password: string;
    username?: string;
    source?: string;
    ref?: string;
  }): Promise<{ user: User; token: string }> => {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  updateProfile: async (data: { username?: string }): Promise<User> => {
    const response = await api.put('/api/auth/profile', data);
    return response.data;
  },

  changePassword: async (data: {
    current_password: string;
    new_password: string;
  }): Promise<ApiResponse<null>> => {
    const response = await api.put('/api/auth/password', data);
    return response.data;
  },

  forgotPassword: async (email: string): Promise<ApiResponse<null>> => {
    const response = await api.post('/api/auth/forgot-password', { email });
    return response.data;
  },

  resetPassword: async (token: string, password: string): Promise<ApiResponse<null>> => {
    const response = await api.post('/api/auth/reset-password', { token, password });
    return response.data;
  },
};

export default authApi;
