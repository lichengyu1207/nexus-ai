import api from '../services/api';

export interface TrainingStatus {
  is_training: boolean;
  total_episodes: number;
  current_episode: number;
  best_attacker_win_rate: number;
  best_defender_win_rate: number;
  population_size: number;
  champion_id: string | null;
  last_update: string;
}

export interface EnvironmentInfo {
  state_dim: number;
  attacker_action_dim: number;
  defender_action_dim: number;
  attack_types: string[];
  defense_actions: string[];
}

export interface AgentStatus {
  agent_id: string;
  role: 'attacker' | 'defender';
  win_rate: number;
  total_games: number;
  avg_reward: number;
  created_at: string;
}

export interface PopulationStatus {
  attacker_population: AgentStatus[];
  defender_population: AgentStatus[];
  population_size: number;
}

export interface TrainRequest {
  num_episodes: number;
  update_interval?: number;
}

export interface TrainResult {
  success: boolean;
  episodes_completed: number;
  results: EpisodeResult[];
  total_episodes: number;
}

export interface EpisodeResult {
  episode: number;
  attacker_reward: number;
  defender_reward: number;
  winner: string;
  duration: number;
}

export interface EvaluateRequest {
  num_games: number;
}

export interface EvaluateResult {
  total_games: number;
  attacker_wins: number;
  defender_wins: number;
  attacker_win_rate: number;
  defender_win_rate: number;
  avg_attacker_reward: number;
  avg_defender_reward: number;
}

export interface TrainingHistory {
  history: TrainingHistoryItem[];
  total: number;
}

export interface TrainingHistoryItem {
  episode: number;
  timestamp: string;
  attacker_reward: number;
  defender_reward: number;
  winner: string;
  duration: number;
}

export interface TrainingStatistics {
  statistics: StatisticItem[];
  days: number;
}

export interface StatisticItem {
  stat_date: string;
  population_size: number;
  total_episodes: number;
  best_attacker_id: string;
  best_attacker_win_rate: number;
  best_defender_id: string;
  best_defender_win_rate: number;
  avg_attacker_reward: number;
  avg_defender_reward: number;
}

export interface SaveModelRequest {
  path: string;
}

export const trainingApi = {
  async getStatus(): Promise<TrainingStatus> {
    const response = await api.get('/selfplay/status');
    return response.data;
  },

  async getEnvironmentInfo(): Promise<EnvironmentInfo> {
    const response = await api.get('/selfplay/environment/info');
    return response.data;
  },

  async train(request: TrainRequest): Promise<TrainResult> {
    const response = await api.post('/selfplay/train', request);
    return response.data;
  },

  async evaluate(request: EvaluateRequest): Promise<EvaluateResult> {
    const response = await api.post('/selfplay/evaluate', request);
    return response.data;
  },

  async getPopulation(): Promise<PopulationStatus> {
    const response = await api.get('/selfplay/population');
    return response.data;
  },

  async getAttackerStatus(agentId: string): Promise<AgentStatus> {
    const response = await api.get(`/selfplay/population/attacker/${agentId}`);
    return response.data;
  },

  async getDefenderStatus(agentId: string): Promise<AgentStatus> {
    const response = await api.get(`/selfplay/population/defender/${agentId}`);
    return response.data;
  },

  async saveChampion(request: SaveModelRequest): Promise<{ success: boolean; path: string; champion_id: string | null }> {
    const response = await api.post('/selfplay/save-champion', request);
    return response.data;
  },

  async getHistory(limit: number = 100): Promise<TrainingHistory> {
    const response = await api.get('/selfplay/history', { params: { limit } });
    return response.data;
  },

  async getStatistics(days: number = 7): Promise<TrainingStatistics> {
    const response = await api.get('/selfplay/statistics', { params: { days } });
    return response.data;
  },
};

export default trainingApi;
