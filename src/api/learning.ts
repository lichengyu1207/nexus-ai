import api from '../services/api';

export interface LearningStatus {
  engine_running: boolean;
  agents: AgentLearningStatus[];
  pending_jobs: number;
  total_jobs: number;
}

export interface AgentLearningStatus {
  agent_id: string;
  health_score: number;
  success_rate: number;
  avg_response_time: number;
  satisfaction_rate: number;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  avg_reward: number;
  learning_progress: Record<string, unknown>;
  recommendations: string[];
  anomalies: any[];
}

export interface AgentLearningDetail {
  agent_id: string;
  trainer: Record<string, unknown>;
  active_model: string | null;
  model_versions: number;
  experience_buffer: Record<string, unknown>;
  reflection: Record<string, unknown>;
  performance_analysis: Record<string, unknown>;
}

export interface TrainingJob {
  job_id: string;
  agent_id: string;
  status: string;
  progress: number;
  created_at: string;
  completed_at?: string;
}

export interface ReflectionResult {
  success: boolean;
  reflection_id: string;
  analysis: string;
  suggestions: string[];
  training_samples_count: number;
}

export interface ModelVersion {
  version: string;
  agent_id: string;
  created_at: string;
  metrics: Record<string, number>;
  is_active: boolean;
  is_champion: boolean;
}

export interface ABTestResult {
  success: boolean;
  experiment: Record<string, unknown>;
}

export interface RecordTaskRequest {
  agent_id: string;
  task_id: string;
  task_type: string;
  success: boolean;
  duration: number;
  reward?: number;
  user_feedback?: string;
  error?: string;
}

export const learningApi = {
  async getStatus(): Promise<LearningStatus> {
    const response = await api.get('/learning/status');
    return response.data;
  },

  async getAgentStatus(agentId: string): Promise<AgentLearningDetail> {
    const response = await api.get(`/learning/agent/${agentId}`);
    return response.data;
  },

  async startEngine(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/learning/engine/start');
    return response.data;
  },

  async stopEngine(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/learning/engine/stop');
    return response.data;
  },

  async triggerTraining(agentId: string): Promise<{ success: boolean; job_id: string; agent_id: string }> {
    const response = await api.post(`/learning/train/${agentId}`);
    return response.data;
  },

  async getTrainingJobs(limit: number = 20): Promise<{ jobs: TrainingJob[]; total: number }> {
    const response = await api.get('/learning/jobs', { params: { limit } });
    return response.data;
  },

  async getTrainingJobStatus(jobId: string): Promise<Record<string, unknown>> {
    const response = await api.get(`/learning/jobs/${jobId}`);
    return response.data;
  },

  async getReflections(agentId: string, limit: number = 10): Promise<{
    agent_id: string;
    reflections: any[];
    summary: Record<string, unknown>;
  }> {
    const response = await api.get(`/learning/reflections/${agentId}`, { params: { limit } });
    return response.data;
  },

  async triggerReflection(request: {
    agent_id: string;
    trigger?: string;
    context?: Record<string, unknown>;
  }): Promise<ReflectionResult> {
    const response = await api.post('/learning/reflect', request);
    return response.data;
  },

  async getModelVersions(agentId: string, limit: number = 10): Promise<{
    agent_id: string;
    versions: ModelVersion[];
  }> {
    const response = await api.get(`/learning/models/${agentId}`, { params: { limit } });
    return response.data;
  },

  async rollbackModel(agentId: string): Promise<{
    success: boolean;
    version?: string;
    message: string;
  }> {
    const response = await api.post(`/learning/rollback/${agentId}`);
    return response.data;
  },

  async createABTest(request: {
    agent_id: string;
    version_a: string;
    version_b: string;
    traffic_split?: number;
  }): Promise<ABTestResult> {
    const response = await api.post('/learning/ab-test', request);
    return response.data;
  },

  async getABTestStats(experimentId: string): Promise<Record<string, unknown>> {
    const response = await api.get(`/learning/ab-test/${experimentId}`);
    return response.data;
  },

  async endABTest(experimentId: string, winner?: string): Promise<Record<string, unknown>> {
    const params = winner ? { winner } : {};
    const response = await api.post(`/learning/ab-test/${experimentId}/end`, null, { params });
    return response.data;
  },

  async recordTask(request: RecordTaskRequest): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/learning/record-task', request);
    return response.data;
  },

  async getAgentMetrics(
    agentId: string,
    metricType: string = 'avg_reward',
    granularity: string = 'hour',
    hours: number = 24
  ): Promise<{
    agent_id: string;
    metric_type: string;
    granularity: string;
    series: any[];
  }> {
    const response = await api.get(`/learning/metrics/${agentId}`, {
      params: { metric_type: metricType, granularity, hours },
    });
    return response.data;
  },

  async getDashboard(agentIds: string = '', hours: number = 24): Promise<Record<string, unknown>> {
    const response = await api.get('/learning/dashboard', {
      params: { agent_ids: agentIds, hours },
    });
    return response.data;
  },

  async exportReport(
    agentIds: string = '',
    hours: number = 24,
    format: string = 'json'
  ): Promise<any> {
    const response = await api.get('/learning/report', {
      params: { agent_ids: agentIds, hours, format },
    });
    return response.data;
  },

  async compareAgents(agentIds: string, hours: number = 24): Promise<Record<string, unknown>> {
    const response = await api.get('/learning/compare', {
      params: { agent_ids: agentIds, hours },
    });
    return response.data;
  },

  async getExperienceBufferStats(): Promise<Record<string, unknown>> {
    const response = await api.get('/learning/experience-buffer');
    return response.data;
  },

  async registerAgent(agentId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/learning/register-agent/${agentId}`);
    return response.data;
  },
};

export default learningApi;
