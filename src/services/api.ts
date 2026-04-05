import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = '/api';

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{ field: string; message: string; value?: string }>;
  request_id?: string;
}

export class AppApiError extends Error {
  public code: string;
  public requestId?: string;
  public details?: Array<{ field: string; message: string; value?: string }>;
  public status: number;

  constructor(message: string, status: number, code: string = 'UNKNOWN_ERROR', requestId?: string, details?: Array<{ field: string; message: string; value?: string }>) {
    super(message);
    this.name = 'AppApiError';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
    this.details = details;
  }
}

const ERROR_MESSAGES: Record<string, string> = {
  AUTH_FAILED: '认证失败，请检查用户名或密码',
  AUTH_TOKEN_EXPIRED: '登录已过期，请重新登录',
  AUTH_INVALID_TOKEN: '无效的认证信息',
  NOT_FOUND: '请求的资源不存在',
  TASK_NOT_FOUND: '任务不存在或已被删除',
  REPORT_NOT_FOUND: '报告不存在或已被删除',
  USER_NOT_FOUND: '用户不存在',
  TEAM_NOT_FOUND: '团队不存在或已被删除',
  BAD_REQUEST: '请求参数错误',
  VALIDATION_ERROR: '数据验证失败',
  UNAUTHORIZED: '未授权访问，请先登录',
  FORBIDDEN: '没有权限执行此操作',
  CONFLICT: '资源冲突',
  DUPLICATE_ENTRY: '该数据已存在',
  RATE_LIMIT_EXCEEDED: '请求过于频繁，请稍后再试',
  SERVICE_UNAVAILABLE: '服务暂时不可用',
  INTERNAL_ERROR: '服务器内部错误，请稍后重试',
  AI_SERVICE_ERROR: 'AI服务暂时不可用，请稍后重试',
  FILE_UPLOAD_ERROR: '文件上传失败',
  EXPORT_ERROR: '数据导出失败',
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept-Encoding': 'gzip, deflate, br',
  },
  timeout: 30000,
  decompress: true,
});

// API缓存系统
const cache: Record<string, { data: any; timestamp: number }> = {};
const CACHE_DURATION = 5 * 60 * 1000; // 5分钟缓存

const getCacheKey = (config: InternalAxiosRequestConfig) => {
  if (config.method === 'get') {
    const url = config.url || '';
    const params = config.params ? JSON.stringify(config.params) : '';
    return `${url}?${params}`;
  }
  return null;
};

let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (error: Error) => void }> = [];

const processQueue = (error: Error | null, token: string | null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    const requestId = Math.random().toString(36).substring(2, 10);
    config.headers['X-Request-ID'] = requestId;
    
    // 检查缓存
    const cacheKey = getCacheKey(config);
    if (cacheKey) {
      const cachedItem = cache[cacheKey];
      if (cachedItem && Date.now() - cachedItem.timestamp < CACHE_DURATION) {
        return Promise.resolve({ 
          data: cachedItem.data, 
          status: 200, 
          statusText: 'OK', 
          headers: {}, 
          config 
        });
      }
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response: AxiosResponse) => {
    // 缓存GET请求的响应
    const cacheKey = getCacheKey(response.config);
    if (cacheKey) {
      cache[cacheKey] = {
        data: response.data,
        timestamp: Date.now()
      };
    }
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status || 0;
    const data = error.response?.data;
    
    if (status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        const response = await axios.post('/api/auth/refresh', {}, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        const newToken = response.data.access_token;
        localStorage.setItem('token', newToken);
        
        processQueue(null, newToken);
        
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(new Error('Token refresh failed'), null);
        
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    if (status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    if (status === 403) {
      const currentPath = window.location.pathname;
      if (currentPath.startsWith('/admin')) {
        console.warn('[API] Access denied to admin resource');
      }
    }
    
    const errorCode = data?.code || `HTTP_${status}`;
    const errorMessage = data?.message || ERROR_MESSAGES[errorCode] || getErrorMessage(status, error.message);
    
    const apiError = new AppApiError(
      errorMessage,
      status,
      errorCode,
      data?.request_id,
      data?.details
    );
    
    console.error('[API Error]', {
      status,
      code: apiError.code,
      message: apiError.message,
      requestId: apiError.requestId,
      details: apiError.details,
    });
    
    return Promise.reject(apiError);
  }
);

const getErrorMessage = (status: number, defaultMessage: string): string => {
  const messages: Record<number, string> = {
    400: '请求参数错误',
    401: '请先登录',
    403: '没有权限访问',
    404: '资源不存在',
    409: '资源冲突',
    422: '数据验证失败',
    429: '请求过于频繁，请稍后再试',
    500: '服务器内部错误',
    502: '网关错误',
    503: '服务暂时不可用',
    504: '网关超时',
  };
  
  return messages[status] || defaultMessage || '网络请求失败';
};

export const handleApiError = (error: unknown, fallbackMessage: string = '操作失败'): string => {
  if (error instanceof AppApiError) {
    if (error.details && error.details.length > 0) {
      return error.details.map((e: { field: string; message: string }) => `${e.field}: ${e.message}`).join(', ');
    }
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message || fallbackMessage;
  }
  
  return fallbackMessage;
};

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_admin?: boolean;
  permissions?: Record<string, boolean>;
  created_at: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  source?: string;
  referred_by?: string;
  referred_by_other?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

export interface Task {
  id: string;
  user_id: string;
  query: string;
  status: string;
  progress: number;
  style: string;
  created_at: string | null;
  completed_at: string | null;
  agents: AgentSummary[];
}

export interface AgentSummary {
  name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  limit: number;
  offset: number;
}

export interface TaskStep {
  id: string;
  task_id: string;
  agent_name: string;
  step_name: string;
  step_order: number;
  status: string;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface TaskMessage {
  id: string;
  task_id: string;
  sender: string;
  recipient: string | null;
  type: string;
  content: Record<string, unknown>;
  in_reply_to: string | null;
  timestamp: string;
}

export interface UserStats {
  total_tasks: number;
  completed_tasks: number;
  running_tasks: number;
  failed_tasks: number;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  updateMe: async (data: { full_name?: string; password?: string }): Promise<User> => {
    const response = await api.put<User>('/auth/me', data);
    return response.data;
  },

  changePassword: async (data: { old_password: string; new_password: string }): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>('/auth/me/password', data);
    return response.data;
  },

  getStats: async (): Promise<UserStats> => {
    const response = await api.get<UserStats>('/auth/me/stats');
    return response.data;
  },
};

export const userApi = {
  getProfile: async (): Promise<User & { username: string; avatar_url: string | null; theme: string; language: string; notification_preferences: Record<string, boolean> }> => {
    const response = await api.get('/users/me');
    return response.data;
  },
  
  updateProfile: async (data: { full_name?: string; username?: string }): Promise<User> => {
    const response = await api.put('/users/me', data);
    return response.data;
  },
  
  uploadAvatar: async (file: File): Promise<{ avatar_url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/users/me/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  changePassword: async (data: { current_password: string; new_password: string }): Promise<{ message: string }> => {
    const response = await api.put('/users/me/password', data);
    return response.data;
  },
  
  getPreferences: async (): Promise<{ theme: string; language: string; notification_preferences: Record<string, boolean> }> => {
    const response = await api.get('/users/me/preferences');
    return response.data;
  },
  
  updatePreferences: async (data: { theme?: string; language?: string; notification_preferences?: Record<string, boolean> }): Promise<{ message: string }> => {
    const response = await api.put('/users/me/preferences', data);
    return response.data;
  },
};

export const taskApi = {
  create: async (data: { query: string; style?: string }): Promise<Task> => {
    const response = await api.post<Task>('/tasks', data);
    return response.data;
  },

  createBatch: async (data: { queries: string[]; style?: string }): Promise<{
    tasks: Task[];
    total: number;
    success_count: number;
    failed_count: number;
    integral_consumed: number;
  }> => {
    const response = await api.post('/tasks/batch', data);
    return response.data;
  },

  list: async (params?: { limit?: number; offset?: number; status?: string }): Promise<TaskListResponse> => {
    const response = await api.get<TaskListResponse>('/tasks', { params });
    return response.data;
  },

  get: async (taskId: string): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  getMessages: async (taskId: string): Promise<{ task_id: string; messages: TaskMessage[]; total: number }> => {
    const response = await api.get<{ task_id: string; messages: TaskMessage[]; total: number }>(`/tasks/${taskId}/messages`);
    return response.data;
  },

  getSteps: async (taskId: string): Promise<TaskStep[]> => {
    const response = await api.get<TaskStep[]>(`/tasks/${taskId}/steps`);
    return response.data;
  },

  delete: async (taskId: string): Promise<void> => {
    await api.delete(`/tasks/${taskId}`);
  },

  getReport: async (taskId: string): Promise<{ task_id: string; report: Record<string, unknown> }> => {
    const response = await api.get<{ task_id: string; report: Record<string, unknown> }>(`/tasks/${taskId}/report`);
    return response.data;
  },
};

export const sseApi = {
  connect: (taskId: string): EventSource => {
    return new EventSource(`${API_BASE_URL}/sse/tasks/${taskId}/stream`);
  },
};

export const batchApi = {
  batch: async (requests: Array<{
    url: string;
    method: 'get' | 'post' | 'put' | 'delete';
    data?: any;
    params?: any;
  }>): Promise<Array<{
    status: number;
    data: any;
    error?: string;
  }>> => {
    const response = await api.post('/batch', {
      requests,
    });
    return response.data;
  },
};

export interface Team {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  invite_code: string;
  created_at: string | null;
  user_role?: string;
  member_count?: number;
  shared_tasks?: { task_id: string }[];
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: string;
  email: string;
  full_name: string | null;
  joined_at: string | null;
}

export interface TeamTask {
  id: string;
  user_id: string;
  query: string;
  status: string;
  progress: number;
  style: string;
  team_id: string | null;
  owner_email: string;
  owner_name: string | null;
  created_at: string | null;
}

export const teamApi = {
  create: async (data: { name: string; description?: string }): Promise<Team> => {
    const response = await api.post<Team>('/teams', data);
    return response.data;
  },

  list: async (): Promise<Team[]> => {
    const response = await api.get<Team[]>('/teams');
    return response.data;
  },

  get: async (teamId: string): Promise<Team> => {
    const response = await api.get<Team>(`/teams/${teamId}`);
    return response.data;
  },

  update: async (teamId: string, data: { name?: string; description?: string }): Promise<Team> => {
    const response = await api.put<Team>(`/teams/${teamId}`, data);
    return response.data;
  },

  delete: async (teamId: string): Promise<void> => {
    await api.delete(`/teams/${teamId}`);
  },

  getMembers: async (teamId: string): Promise<TeamMember[]> => {
    const response = await api.get<TeamMember[]>(`/teams/${teamId}/members`);
    return response.data;
  },

  join: async (inviteCode: string): Promise<{ message: string; team_id: string; team_name: string }> => {
    const response = await api.post<{ message: string; team_id: string; team_name: string }>(`/teams/join/${inviteCode}`);
    return response.data;
  },

  leave: async (teamId: string, userId: string): Promise<void> => {
    await api.delete(`/teams/${teamId}/members/${userId}`);
  },

  getTasks: async (teamId: string, limit?: number, offset?: number): Promise<TeamTask[]> => {
    const response = await api.get<TeamTask[]>(`/teams/${teamId}/tasks`, { params: { limit, offset } });
    return response.data;
  },

  shareTask: async (teamId: string, taskId: string): Promise<void> => {
    await api.post(`/teams/${teamId}/tasks/${taskId}`);
  },
};

export interface DistrictInfo {
  id: string;
  city: string;
  district: string | null;
  introduction: string | null;
  transportation: string | null;
  education: string | null;
  commercial: string | null;
  future_plan: string | null;
  pros: string[] | null;
  cons: string[] | null;
}

export interface DistrictInfoListResponse {
  city: string;
  districts: DistrictInfo[];
  total: number;
}

export const districtInfoApi = {
  getList: async (city: string, district?: string): Promise<DistrictInfoListResponse> => {
    const params: Record<string, string> = { city };
    if (district) params.district = district;
    const response = await api.get<DistrictInfoListResponse>('/district-info', { params });
    return response.data;
  },
  
  getDetail: async (city: string, district: string): Promise<DistrictInfo> => {
    const response = await api.get<DistrictInfo>('/district-info/detail', {
      params: { city, district }
    });
    return response.data;
  },
  
  getCities: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/district-info/cities');
    return response.data;
  },
};

export interface ParsedQuery {
  raw_query: string;
  city: string | null;
  district: string | null;
  community: string | null;
  room_count: number | null;
  hall_count: number | null;
  area_min: number | null;
  area_max: number | null;
  area_avg?: number | null;
  area_estimated?: boolean;
  price_min: number | null;
  price_max: number | null;
  price_avg?: number | null;
  price_estimated?: boolean;
  orientation: string | null;
  floor_type: string | null;
  decoration: string | null;
  is_school_district: boolean | null;
  is_near_subway: boolean | null;
  special_requirements: string[];
  missing_fields: string[];
  confidence: number;
  inferences: Array<{
    field: string;
    inferred_value: Record<string, unknown>;
    confidence: number;
    reasoning: string;
  }>;
  recommendations: Record<string, Array<{ value: unknown; label: string }>>;
}

export interface EstimateResult {
  area_estimate: {
    min: number;
    max: number;
    avg: number;
    common_areas: number[];
  } | null;
  price_estimate: {
    min: number;
    max: number;
    avg: number;
    unit_price: { avg: number; min: number; max: number };
  } | null;
  confidence: number;
}

export const parseApi = {
  parseQuery: async (query: string, enableInference: boolean = true): Promise<ParsedQuery> => {
    const response = await api.post<ParsedQuery>('/parse/query', {
      query,
      enable_inference: enableInference
    });
    return response.data;
  },
  
  estimate: async (data: {
    city?: string;
    district?: string;
    room_count?: number;
    hall_count?: number;
    area_min?: number;
    area_max?: number;
    special_requirements?: string[];
  }): Promise<EstimateResult> => {
    const response = await api.post<EstimateResult>('/parse/estimate', data);
    return response.data;
  },
  
  getCityRecommendations: async (): Promise<{ cities: Array<{ value: string; label: string; has_data: boolean }> }> => {
    const response = await api.get('/parse/recommendations/cities');
    return response.data;
  },
  
  getDistrictRecommendations: async (city: string): Promise<{ districts: Array<{ value: string; label: string; avg_price: number }> }> => {
    const response = await api.get(`/parse/recommendations/districts/${encodeURIComponent(city)}`);
    return response.data;
  },
  
  getAreaRecommendations: async (roomCount?: number): Promise<{ areas: Array<{ value: number; label: string; rooms: number }> }> => {
    const params = roomCount ? { room_count: roomCount } : {};
    const response = await api.get('/parse/recommendations/areas', { params });
    return response.data;
  },
  
  getPriceRecommendations: async (city?: string): Promise<{ prices: Array<{ value: number; label: string; tier: string }> }> => {
    const params = city ? { city } : {};
    const response = await api.get('/parse/recommendations/prices', { params });
    return response.data;
  },
};

export interface AmbiguityCheck {
  has_ambiguity: boolean;
  ambiguous_fields: Array<{
    field: string;
    value: string;
    message: string;
    candidate_count: number;
  }>;
}

export interface DisambiguationCandidate {
  value: string;
  label: string;
  description?: string;
  city?: string;
  district?: string;
  community?: string;
  avg_price?: number;
  confidence: number;
}

export interface DisambiguationResult {
  field: string;
  original_value: string;
  message: string;
  candidates: DisambiguationCandidate[];
  requires_selection: boolean;
}

export const disambiguateApi = {
  checkAmbiguity: async (data: {
    query: string;
    city?: string;
    district?: string;
    community?: string;
  }): Promise<AmbiguityCheck> => {
    const response = await api.post<AmbiguityCheck>('/disambiguate/check', data);
    return response.data;
  },
  
  resolve: async (data: {
    query: string;
    ambiguous_field: string;
    current_value: string;
    context?: Record<string, unknown>;
  }): Promise<DisambiguationResult> => {
    const response = await api.post<DisambiguationResult>('/disambiguate/resolve', data);
    return response.data;
  },
  
  getDistrictCandidates: async (districtName: string): Promise<{
    district_name: string;
    candidates: Array<{
      city: string;
      district: string;
      description?: string;
      avg_price?: number;
      label: string;
    }>;
    total: number;
  }> => {
    const response = await api.get(`/disambiguate/districts/${encodeURIComponent(districtName)}`);
    return response.data;
  },
  
  getSupportedCities: async (): Promise<{
    cities: Array<{
      city: string;
      district_count: number;
      avg_price: number;
    }>;
    total: number;
  }> => {
    const response = await api.get('/disambiguate/cities');
    return response.data;
  },
};

export interface Comment {
  id: string;
  report_id: string;
  user_id: string;
  content: string;
  parent_id: string | null;
  mentions: string[] | null;
  email: string;
  full_name: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CommentListResponse {
  comments: Comment[];
  total: number;
}

export const commentApi = {
  create: async (reportId: string, data: { content: string; parent_id?: string }): Promise<Comment> => {
    const response = await api.post<Comment>(`/reports/${reportId}/comments`, data);
    return response.data;
  },

  list: async (reportId: string, limit?: number, offset?: number): Promise<CommentListResponse> => {
    const response = await api.get<CommentListResponse>(`/reports/${reportId}/comments`, {
      params: { limit, offset }
    });
    return response.data;
  },

  getReplies: async (commentId: string): Promise<Comment[]> => {
    const response = await api.get<Comment[]>(`/comments/${commentId}/replies`);
    return response.data;
  },

  update: async (commentId: string, content: string): Promise<Comment> => {
    const response = await api.put<Comment>(`/comments/${commentId}`, { content });
    return response.data;
  },

  delete: async (commentId: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/comments/${commentId}`);
    return response.data;
  },

  getMentions: async (limit?: number): Promise<{ mentions: Comment[]; total: number }> => {
    const response = await api.get('/comments/mentions', { params: { limit } });
    return response.data;
  },
};

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string | null;
  content: string;
  link: string | null;
  action_text: string | null;
  related_id: string | null;
  related_type: string | null;
  is_read: boolean;
  created_at: string | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  unread_count: number;
  total: number;
}

export const notificationApi = {
  list: async (params?: { is_read?: boolean; limit?: number; offset?: number }): Promise<NotificationListResponse> => {
    const response = await api.get<NotificationListResponse>('/notifications', { params });
    return response.data;
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get<{ unread_count: number }>('/notifications/unread-count');
    return response.data;
  },

  markAsRead: async (notificationId: string): Promise<{ message: string }> => {
    const response = await api.put<{ message: string }>(`/notifications/${notificationId}/read`);
    return response.data;
  },

  markAllAsRead: async (): Promise<{ message: string; count: number }> => {
    const response = await api.put<{ message: string; count: number }>('/notifications/read-all');
    return response.data;
  },

  delete: async (notificationId: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/notifications/${notificationId}`);
    return response.data;
  },
};

export const integralApi = {
  getIntegral: async (): Promise<{
    integral: number;
    membership_level: string;
    membership_expires: string | null;
    is_member: boolean;
    recent_logs: Array<{
      id: string;
      user_id: string;
      change: number;
      balance_after: number;
      reason: string;
      admin_note: string | null;
      admin_id: string | null;
      created_at: string;
    }>;
    source: string | null;
    source_name: string | null;
    bonus_label: string | null;
    initial_integral: number | null;
  }> => {
    const response = await api.get('/user/integral');
    return response.data;
  },

  getLogs: async (limit: number = 20, offset: number = 0): Promise<{
    logs: Array<{
      id: string;
      user_id: string;
      change: number;
      balance_after: number;
      reason: string;
      admin_note: string | null;
      admin_id: string | null;
      created_at: string;
    }>;
    total: number;
    limit: number;
    offset: number;
  }> => {
    const response = await api.get('/user/integral/logs', { params: { limit, offset } });
    return response.data;
  },

  getPackages: async (): Promise<{
    integral_packages: Array<{
      id: string;
      name: string;
      integral: number;
      price: number;
      unit_price: number;
      description: string;
      is_popular: boolean;
    }>;
    membership_plans: Array<{
      id: string;
      name: string;
      price: number;
      duration_months: number;
      description: string;
      features: string[];
    }>;
    contact: {
      wechat: string;
      note: string;
    };
  }> => {
    const response = await api.get('/user/integral/packages');
    return response.data;
  },
};

export default api;
