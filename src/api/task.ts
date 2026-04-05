import api from '../services/api';

export interface Task {
  id: string;
  title: string;
  description: string;
  budget?: number;
  style: 'balanced' | 'aggressive' | 'conservative';
  createdAt: string;
  completedAt?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  workflow: WorkflowStep[];
  agents: AgentStatus[];
  realtimeMessages: RealtimeMessage[];
  result?: TaskResult;
}

export interface WorkflowStep {
  name: string;
  status: 'waiting' | 'processing' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  progress?: number;
}

export interface AgentStatus {
  id: string;
  name: string;
  icon?: string;
  color?: string;
  status: 'waiting' | 'working' | 'done';
  progress?: number;
  lastActive?: string;
  currentTask?: string;
}

export interface RealtimeMessage {
  id: string;
  agentId: string;
  agentName?: string;
  content: string;
  timestamp: string;
  type: 'log' | 'warning' | 'success' | 'info' | 'error';
  metadata?: Record<string, unknown>;
}

export interface TaskResult {
  summary: string;
  findings: string[];
  charts: ChartData[];
  recommendations: string[];
  riskLevel: 'low' | 'medium' | 'high';
  confidence: number;
}

export interface ChartData {
  chartId: string;
  chartType: 'line' | 'bar' | 'pie' | 'radar';
  title: string;
  data: ChartPoint[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  colors?: string[];
}

export interface ChartPoint {
  x: string | number;
  y: number;
  label?: string;
  agent?: string;
}

export interface CreateTaskRequest {
  title?: string;
  description: string;
  budget?: number;
  style?: 'balanced' | 'aggressive' | 'conservative';
  location?: {
    city?: string;
    district?: string;
    address?: string;
  };
  propertyType?: 'residential' | 'commercial' | 'land';
  requirements?: string[];
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  pageSize: number;
}

export const taskApi = {
  async getTasks(params?: {
    status?: string;
    page?: number;
    pageSize?: number;
  }): Promise<TaskListResponse> {
    const response = await api.get('/tasks', { params });
    return response.data;
  },

  async getTask(taskId: string): Promise<Task> {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  async createTask(data: CreateTaskRequest): Promise<Task> {
    const response = await api.post('/tasks', data);
    return response.data;
  },

  async updateTask(taskId: string, data: Partial<CreateTaskRequest>): Promise<Task> {
    const response = await api.put(`/tasks/${taskId}`, data);
    return response.data;
  },

  async deleteTask(taskId: string): Promise<void> {
    await api.delete(`/tasks/${taskId}`);
  },

  async getTaskStatus(taskId: string): Promise<{
    status: Task['status'];
    progress: number;
    agents: AgentStatus[];
    currentStep?: string;
  }> {
    const response = await api.get(`/tasks/${taskId}/status`);
    return response.data;
  },

  async getTaskMessages(taskId: string, params?: {
    limit?: number;
    before?: string;
  }): Promise<{ messages: RealtimeMessage[]; hasMore: boolean }> {
    const response = await api.get(`/tasks/${taskId}/messages`, { params });
    return response.data;
  },

  async getTaskResult(taskId: string): Promise<TaskResult> {
    const response = await api.get(`/tasks/${taskId}/result`);
    return response.data;
  },

  async cancelTask(taskId: string): Promise<Task> {
    const response = await api.post(`/tasks/${taskId}/cancel`);
    return response.data;
  },

  async retryTask(taskId: string): Promise<Task> {
    const response = await api.post(`/tasks/${taskId}/retry`);
    return response.data;
  },

  async getPopularTasks(limit: number = 5): Promise<Array<{
    id: string;
    title: string;
    description: string;
    count: number;
  }>> {
    const response = await api.get('/tasks/popular', { params: { limit } });
    return response.data;
  },

  async getTaskStats(): Promise<{
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  }> {
    const response = await api.get('/tasks/stats');
    return response.data;
  },
};

export default taskApi;
