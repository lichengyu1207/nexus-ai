import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      console.error('[API] 后端服务不可用，请检查后端是否启动');
      localStorage.setItem('backend_status', 'offline');
    } else {
      localStorage.setItem('backend_status', 'online');
      if (error.response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export const adminApi = {
  get: (url: string, params?: any) => api.get(url, { params }),
  post: (url: string, data?: any) => api.post(url, data),
  put: (url: string, data?: any) => api.put(url, data),
  delete: (url: string) => api.delete(url),
};

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: any) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const userApi = {
  getProfile: () => api.get('/auth/me'),
  updateProfile: (data: any) => api.put('/auth/me', data),
  getIntegralLogs: () => api.get('/user/integral/logs'),
};

export const taskApi = {
  create: (data: any) => api.post('/analyze', data),
  getList: () => api.get('/tasks'),
  getById: (id: string) => api.get(`/tasks/${id}`),
};

export const reportApi = {
  getList: () => api.get('/reports'),
  getById: (id: string) => api.get(`/reports/${id}`),
};

export const teamApi = {
  getList: () => api.get('/teams'),
  create: (data: any) => api.post('/teams', data),
  join: (inviteCode: string) => api.post(`/teams/join/${inviteCode}`),
};

export const analyticsApi = {
  trackEvent: (data: any) => api.post('/events', data),
};

export default api;
