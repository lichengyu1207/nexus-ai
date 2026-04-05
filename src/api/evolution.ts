import api from '../services/api';

export interface EvolutionReport {
  total_agents: number;
  healthy_agents: number;
  warning_agents: number;
  critical_agents: number;
  recent_improvements: number;
  avg_success_rate: number;
  avg_response_time: number;
}

export interface RegisteredAgent {
  agent_id: string;
  agent_name: string;
  department: string;
  status: 'healthy' | 'warning' | 'critical' | 'inactive';
  success_rate: number;
  avg_response_time: number;
  version: string;
  last_updated: string;
  total_improvements: number;
}

export interface AgentPerformance {
  agent_id: string;
  agent_name: string;
  department: string;
  current_version: string;
  performance_metrics: {
    success_rate: number;
    avg_response_time: number;
    user_feedback_avg: number;
    total_decisions: number;
    recent_trend: string;
  };
  version_history: Array<{
    version: string;
    created_at: string;
    success_rate: number;
    improvement: number;
  }>;
  recent_trajectories: Array<{
    id: string;
    timestamp: string;
    decision_type: string;
    success: boolean;
    response_time: number;
  }>;
}

export interface DiagnosisResult {
  agent_id: string;
  agent_name: string;
  diagnosis_type: 'performance' | 'behavior' | 'comprehensive';
  status: 'healthy' | 'warning' | 'critical';
  issues: Array<{
    type: string;
    severity: 'low' | 'medium' | 'high';
    description: string;
    recommendation: string;
  }>;
  suggestions: Array<{
    id: string;
    type: string;
    description: string;
    potential_impact: number;
    status: 'pending' | 'approved' | 'rejected' | 'applied';
    created_at: string;
  }>;
}

export interface EvolutionSuggestion {
  id: string;
  agent_id: string;
  agent_name: string;
  type: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'applied';
  potential_impact: number;
  created_at: string;
  reviewed_at?: string;
  reviewer?: string;
}

export interface RecordTrajectoryRequest {
  agent_id: string;
  input_context: Record<string, unknown>;
  decision: Record<string, unknown>;
  execution_time: number;
  success: boolean;
  user_feedback?: number;
  error_message?: string;
}

export interface SetBaselineRequest {
  agent_id: string;
  success_rate?: number;
  avg_time?: number;
  feedback?: number;
}

export const evolutionApi = {
  async getReport(): Promise<EvolutionReport> {
    const response = await api.get('/api/evolution/report');
    return response.data;
  },

  async getRegisteredAgents(): Promise<{ agents: RegisteredAgent[]; total: number }> {
    const response = await api.get('/api/evolution/agents');
    return response.data;
  },

  async getAgentPerformance(agentId: string): Promise<AgentPerformance> {
    const response = await api.get(`/api/evolution/agents/${agentId}/performance`);
    return response.data;
  },

  async runDiagnosis(agentId: string, diagnosisType: 'performance' | 'behavior' | 'comprehensive'): Promise<DiagnosisResult> {
    const response = await api.post('/api/evolution/diagnose', {
      json: { agent_id: agentId, diagnosis_type: diagnosisType },
    });
    return response.data;
  },

  async getSuggestions(): Promise<{ suggestions: EvolutionSuggestion[]; total: number }> {
    const response = await api.get('/api/evolution/suggestions');
    return response.data;
  },

  async getSuggestionsByAgent(agentId: string): Promise<EvolutionSuggestion[]> {
    const response = await api.get(`/api/evolution/suggestions/${agentId}`);
    return response.data;
  },

  async approveSuggestion(suggestionId: string, reason?: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/evolution/suggestions/approve', {
      json: { suggestion_id: suggestionId, reason },
    });
    return response.data;
  },

  async rejectSuggestion(suggestionId: string, reason: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/evolution/suggestions/reject', {
      json: { suggestion_id: suggestionId, reason },
    });
    return response.data;
  },

  async applySuggestion(suggestionId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/evolution/suggestions/apply', {
      json: { suggestion_id: suggestionId },
    });
    return response.data;
  },

  async recordTrajectory(request: RecordTrajectoryRequest): Promise<{ success: boolean; trajectory_id: string }> {
    const response = await api.post('/api/evolution/trajectory', request);
    return response.data;
  },

  async setBaseline(request: SetBaselineRequest): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/evolution/baseline', request);
    return response.data;
  },

  async createVersion(request: {
    agent_id: string;
    version_number: string;
    strategy_hash: string;
    parameters_hash: string;
    performance_metrics: Record<string, unknown>;
  }): Promise<{ success: boolean; version_id: string; message: string }> {
    const response = await api.post('/api/evolution/version', request);
    return response.data;
  },
};

export default evolutionApi;
