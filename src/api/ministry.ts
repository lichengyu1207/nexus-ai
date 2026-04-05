import api from '../services/api';

export type Department = 'li' | 'hu' | 'li_guan' | 'bing' | 'xing' | 'gong';

export interface MinistryStatus {
  is_active: boolean;
  departments: DepartmentInfo[];
  total_agents: number;
  active_tasks: number;
}

export interface DepartmentInfo {
  code: Department;
  name: string;
  description: string;
  agent_count: number;
  active_tasks: number;
  efficiency: number;
  responsibilities: string[];
}

export interface MinistryAgent {
  id: string;
  name: string;
  department: Department;
  level: number;
  rarity: string;
  status: 'idle' | 'working' | 'training';
  skills: Array<{ name: string; level: number }>;
  current_task?: string;
  efficiency: number;
}

export interface MinistryTask {
  id: string;
  department: Department;
  task_type: string;
  description: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  assigned_agents: string[];
  priority: number;
  created_at: string;
  completed_at?: string;
  result?: Record<string, unknown>;
}

export const ministryApi = {
  async getStatus(): Promise<MinistryStatus> {
    const response = await api.get('/ministry/status');
    return response.data;
  },

  async getDepartments(): Promise<{ departments: DepartmentInfo[] }> {
    const response = await api.get('/ministry/departments');
    return response.data;
  },

  async getDepartment(deptCode: Department): Promise<DepartmentInfo> {
    const response = await api.get(`/ministry/departments/${deptCode}`);
    return response.data;
  },

  async getDepartmentAgents(deptCode: Department): Promise<{ agents: MinistryAgent[] }> {
    const response = await api.get(`/ministry/departments/${deptCode}/agents`);
    return response.data;
  },

  async getTasks(department?: Department, status?: string): Promise<{
    tasks: MinistryTask[];
    total: number;
  }> {
    const response = await api.get('/ministry/tasks', {
      params: { department, status },
    });
    return response.data;
  },

  async createTask(request: {
    department: Department;
    task_type: string;
    description: string;
    priority?: number;
    context?: Record<string, unknown>;
  }): Promise<{ success: boolean; task: MinistryTask }> {
    const response = await api.post('/ministry/tasks', { json: request });
    return response.data;
  },

  async assignAgents(taskId: string, agentIds: string[]): Promise<{ success: boolean }> {
    const response = await api.post(`/ministry/tasks/${taskId}/assign`, {
      json: { agent_ids: agentIds },
    });
    return response.data;
  },

  async getStatistics(department?: Department): Promise<{
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    avg_completion_time: number;
    by_department: Record<Department, { total: number; completed: number }>;
  }> {
    const response = await api.get('/ministry/statistics', { params: { department } });
    return response.data;
  },

  async getDepartmentReport(deptCode: Department, days: number = 7): Promise<{
    department: DepartmentInfo;
    tasks_completed: number;
    avg_efficiency: number;
    top_agents: MinistryAgent[];
    recent_tasks: MinistryTask[];
  }> {
    const response = await api.get(`/ministry/departments/${deptCode}/report`, {
      params: { days },
    });
    return response.data;
  },
};

export default ministryApi;
