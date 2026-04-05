import api from '../services/api';

export interface BusinessAgent {
  agent_id: string;
  name: string;
  role: string;
  species: string;
  energy: number;
  age: number;
  generation: number;
  status: 'idle' | 'working' | 'resting' | 'training';
  is_alive: boolean;
  is_available: boolean;
  stats: Record<string, number>;
}

export interface BusinessTask {
  id: string;
  task_type: string;
  title: string;
  description: string;
  complexity: number;
  status: 'pending' | 'bidding' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  assigned_agent?: string;
  priority: number;
  created_at: string;
}

export const businessAgentsApi = {
  async getAgents(): Promise<{ agents: BusinessAgent[]; total: number }> {
    const response = await api.get('/business-agents');
    return response.data;
  },

  async getAgent(agentId: string): Promise<BusinessAgent> {
    const response = await api.get(`/business-agents/${agentId}`);
    return response.data;
  },

  async createTask(request: {
    task_type: string;
    title: string;
    description: string;
    complexity?: number;
    priority?: number;
  }): Promise<{ success: boolean; task: BusinessTask }> {
    const response = await api.post('/business-agents/tasks', { json: request });
    return response.data;
  },

  async getTasks(status?: string): Promise<{ tasks: BusinessTask[]; total: number }> {
    const response = await api.get('/business-agents/tasks', { params: { status } });
    return response.data;
  },

  async submitFeedback(request: {
    user_id: string;
    agent_id: string;
    task_id: string;
    feedback_type: string;
    rating?: number;
  }): Promise<{ success: boolean }> {
    const response = await api.post('/business-agents/feedback', { json: request });
    return response.data;
  },

  async getStatistics(): Promise<{
    total_agents: number;
    active_agents: number;
    total_tasks: number;
    completed_tasks: number;
  }> {
    const response = await api.get('/business-agents/statistics');
    return response.data;
  },
};

export default businessAgentsApi;
