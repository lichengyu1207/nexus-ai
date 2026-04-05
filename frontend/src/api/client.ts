import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { useUserStore } from '../stores/userStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useUserStore.getState().token || localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        useUserStore.getState().logout();
        localStorage.removeItem('token');
        window.location.href = '/login';
      } else if (status === 403) {
        console.error('Permission denied');
      } else if (status === 500) {
        console.error('Server error');
      }
      
      return Promise.reject(data || error.message);
    }
    
    if (error.request) {
      console.error('Network error');
      return Promise.reject({ detail: '网络连接失败，请检查网络' });
    }
    
    return Promise.reject(error);
  }
);

export default api;
