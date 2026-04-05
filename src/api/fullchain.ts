import api from '../services/api';

export interface FullchainStatus {
  is_active: boolean;
  total_chains: number;
  active_chains: number;
  total_steps: number;
  avg_completion_time: number;
}

export interface Chain {
  id: string;
  name: string;
  description: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused';
  steps: ChainStep[];
  current_step: number;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ChainStep {
  id: string;
  chain_id: string;
  name: string;
  order: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  agent_id?: string;
  started_at?: string;
  completed_at?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface ChainTemplate {
  id: string;
  name: string;
  description: string;
  steps: Array<{
    name: string;
    agent_type: string;
    config: Record<string, unknown>;
  }>;
  created_at: string;
}

export const fullchainApi = {
  async getStatus(): Promise<FullchainStatus> {
    const response = await api.get('/fullchain/status');
    return response.data;
  },

  async getChains(status?: string): Promise<{ chains: Chain[]; total: number }> {
    const response = await api.get('/fullchain/chains', { params: { status } });
    return response.data;
  },

  async getChain(chainId: string): Promise<Chain> {
    const response = await api.get(`/fullchain/chains/${chainId}`);
    return response.data;
  },

  async createChain(request: {
    name: string;
    description?: string;
    steps: Array<{
      name: string;
      agent_type: string;
      config?: Record<string, unknown>;
    }>;
  }): Promise<{ success: boolean; chain: Chain }> {
    const response = await api.post('/fullchain/chains', { json: request });
    return response.data;
  },

  async startChain(chainId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/fullchain/chains/${chainId}/start`);
    return response.data;
  },

  async pauseChain(chainId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/fullchain/chains/${chainId}/pause`);
    return response.data;
  },

  async resumeChain(chainId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/fullchain/chains/${chainId}/resume`);
    return response.data;
  },

  async cancelChain(chainId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/fullchain/chains/${chainId}/cancel`);
    return response.data;
  },

  async getTemplates(): Promise<{ templates: ChainTemplate[] }> {
    const response = await api.get('/fullchain/templates');
    return response.data;
  },

  async createTemplate(request: {
    name: string;
    description?: string;
    steps: Array<{
      name: string;
      agent_type: string;
      config: Record<string, unknown>;
    }>;
  }): Promise<{ success: boolean; template: ChainTemplate }> {
    const response = await api.post('/fullchain/templates', { json: request });
    return response.data;
  },

  async getStatistics(): Promise<{
    total_chains: number;
    completed_chains: number;
    failed_chains: number;
    avg_steps_per_chain: number;
    avg_completion_time: number;
  }> {
    const response = await api.get('/fullchain/statistics');
    return response.data;
  },
};

export default fullchainApi;
