import api from '../services/api';

export interface EcosystemStatus {
  is_active: boolean;
  total_agents: number;
  attack_agents: number;
  defense_agents: number;
  memory_agents: number;
  generation: number;
  avg_fitness: number;
  ecosystem_health: number;
}

export interface LivingAgent {
  agent_id: string;
  agent_type: 'attack' | 'defense' | 'memory';
  species: string;
  status: 'alive' | 'dead' | 'dormant';
  generation: number;
  age: number;
  fitness: number;
  energy: number;
  parent_ids: string[];
  mutations: string[];
  created_at: string;
}

export interface AgentStatistics {
  agent_id: string;
  total_actions: number;
  successful_actions: number;
  failed_actions: number;
  avg_response_time: number;
  fitness_history: Array<{ timestamp: string; fitness: number }>;
}

export interface SpawnAgentRequest {
  agent_type: 'attack' | 'defense' | 'memory';
  species?: string;
  parent_ids?: string[];
}

export interface ReproduceRequest {
  agent_id: string;
  agent_type: 'attack' | 'defense' | 'memory';
  partner_id?: string;
}

export interface AttackRequest {
  agent_id: string;
  target: Record<string, any>;
  strategy?: string;
}

export interface DefenseRequest {
  agent_id: string;
  threat: Record<string, any>;
  strategy?: string;
}

export interface MemoryStoreRequest {
  agent_id: string;
  key: string;
  value: Record<string, any>;
  memory_type?: 'episodic' | 'semantic' | 'procedural';
  importance?: number;
  tags?: string[];
  ttl?: number;
}

export interface MemoryRetrieveRequest {
  query: string;
  top_k?: number;
}

export interface EvolutionHistory {
  generation: number;
  timestamp: string;
  population_size: number;
  avg_fitness: number;
  best_agent_id: string;
  best_fitness: number;
}

export interface EmergencePattern {
  pattern_id: string;
  pattern_type: string;
  description: string;
  participating_agents: string[];
  first_observed: string;
  occurrence_count: number;
}

export const ecosystemApi = {
  async getStatus(): Promise<EcosystemStatus> {
    const response = await api.get('/ecosystem/status');
    return response.data;
  },

  async getAgents(agentType?: string, status?: string, limit: number = 50): Promise<{ agents: LivingAgent[]; total: number }> {
    const params: any = { limit };
    if (agentType) params.agent_type = agentType;
    if (status) params.status = status;
    const response = await api.get('/ecosystem/agents', { params });
    return response.data;
  },

  async getAgent(agentId: string): Promise<LivingAgent> {
    const response = await api.get(`/ecosystem/agents/${agentId}`);
    return response.data;
  },

  async spawnAgent(request: SpawnAgentRequest): Promise<{ agent_id: string; type: string; status: string }> {
    const response = await api.post('/ecosystem/agents/spawn', request);
    return response.data;
  },

  async stopAgent(agentId: string): Promise<{ agent_id: string; status: string }> {
    const response = await api.post(`/ecosystem/agents/${agentId}/stop`);
    return response.data;
  },

  async addAgentEnergy(agentId: string, amount: number): Promise<{ agent_id: string; energy_added: number }> {
    const response = await api.post(`/ecosystem/agents/${agentId}/energy?amount=${amount}`);
    return response.data;
  },

  async executeAttack(request: AttackRequest): Promise<{ agent_id: string; result: any }> {
    const response = await api.post('/ecosystem/attack/execute', request);
    return response.data;
  },

  async getAttackStrategies(agentId?: string): Promise<{ agent_id?: string; strategies?: any; strategies_by_agent?: Record<string, string[]> }> {
    const params = agentId ? { agent_id: agentId } : {};
    const response = await api.get('/ecosystem/attack/strategies', { params });
    return response.data;
  },

  async executeDefense(request: DefenseRequest): Promise<{ agent_id: string; result: any }> {
    const response = await api.post('/ecosystem/defense/execute', request);
    return response.data;
  },

  async getDefenseStrategies(agentId?: string): Promise<{ agent_id?: string; strategies?: any; strategies_by_agent?: Record<string, string[]> }> {
    const params = agentId ? { agent_id: agentId } : {};
    const response = await api.get('/ecosystem/defense/strategies', { params });
    return response.data;
  },

  async storeMemory(request: MemoryStoreRequest): Promise<{ memory_id: string; agent_id: string; status: string }> {
    const response = await api.post('/ecosystem/memory/store', request);
    return response.data;
  },

  async retrieveMemory(request: MemoryRetrieveRequest, agentId?: string): Promise<{ query: string; results: any[]; count: number }> {
    const params: any = { agent_id: agentId };
    const response = await api.post('/ecosystem/memory/retrieve', request, { params });
    return response.data;
  },

  async reproduceAsexual(request: ReproduceRequest): Promise<{ parent_id: string; offspring_id: string; status: string }> {
    const response = await api.post('/ecosystem/reproduction/asexual', request);
    return response.data;
  },

  async reproduceSexual(request: ReproduceRequest): Promise<{ parent_ids: string[]; offspring_id: string; status: string }> {
    const response = await api.post('/ecosystem/reproduction/sexual', request);
    return response.data;
  },

  async getEvolutionHistory(limit: number = 100): Promise<{ history: EvolutionHistory[]; generation: number }> {
    const response = await api.get('/ecosystem/evolution/history', { params: { limit } });
    return response.data;
  },

  async getEmergencePatterns(): Promise<{ patterns: EmergencePattern[]; count: number }> {
    const response = await api.get('/ecosystem/emergence/patterns');
    return response.data;
  },

  async triggerSelection(): Promise<{ status: string; generation: number }> {
    const response = await api.post('/ecosystem/selection/trigger');
    return response.data;
  },

  async triggerMutation(): Promise<{ status: string; generation: number }> {
    const response = await api.post('/ecosystem/mutation/trigger');
    return response.data;
  },

  async getMetricsHistory(limit: number = 100): Promise<{ metrics: any[] }> {
    const response = await api.get('/ecosystem/metrics/history', { params: { limit } });
    return response.data;
  },
};

export default ecosystemApi;
