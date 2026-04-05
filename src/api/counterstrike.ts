import api from '../services/api';

export interface CounterstrikeStatus {
  status: string;
  components: Record<string, unknown>;
}

export interface CounterstrikeStats {
  total_threats: number;
  blocked_threats: number;
  active_honeypots: number;
  active_pursuits: number;
}

export interface TrafficData {
  source_ip: string;
  destination_ip?: string;
  port?: number;
  method?: string;
  path?: string;
  payload?: string;
  headers?: Record<string, unknown>;
  user_agent?: string;
  status_code?: number;
}

export interface Threat {
  id: string;
  timestamp: string;
  source_ip: string;
  threat_type: string;
  severity: number;
  status: string;
  description: string;
}

export interface Honeypot {
  id: string;
  honeypot_type: string;
  status: string;
  attacker_profile: Record<string, unknown>;
  created_at: string;
  triggered_count: number;
}

export interface HoneypotCreate {
  honeypot_type: string;
  attacker_profile?: Record<string, unknown>;
  custom_config?: Record<string, unknown>;
}

export interface CounterStrikeAction {
  id: string;
  action_type: string;
  target_identity: string;
  target_ip: string;
  status: string;
  severity: number;
  created_at: string;
  duration_hours: number;
}

export interface CounterStrikeCreate {
  action_type: string;
  target_identity: string;
  target_ip: string;
  parameters?: Record<string, unknown>;
  severity?: number;
  duration_hours?: number;
}

export interface ApprovalRequest {
  request_id: string;
  approver: string;
  notes?: string;
}

export interface RejectionRequest {
  request_id: string;
  rejecter: string;
  reason: string;
}

export interface Pursuit {
  id: string;
  target_identity: string;
  target_ips: string[];
  formation: string;
  status: string;
  priority: number;
  started_at: string;
}

export interface PursuitCreate {
  target_identity: string;
  target_ips: string[];
  formation?: string;
  priority?: number;
}

export interface Tactic {
  id: string;
  name: string;
  category: string;
  description: string;
  conditions: Record<string, unknown>;
  parameters: Record<string, unknown>;
  required_agents: Record<string, unknown>;
  tags: string[];
}

export interface TacticCreate {
  name: string;
  category: string;
  description: string;
  conditions: Record<string, unknown>;
  parameters: Record<string, unknown>;
  required_agents: Record<string, unknown>;
  tags: string[];
}

export interface AttackerIdentity {
  id: string;
  identity_type: string;
  value: string;
  confidence: number;
  first_seen: string;
  last_seen: string;
  attack_count: number;
}

export interface AttackChain {
  id: string;
  attacker_id: string;
  status: string;
  events: any[];
  created_at: string;
}

export const counterstrikeApi = {
  async getStatus(): Promise<CounterstrikeStatus> {
    const response = await api.get('/counterstrike/status');
    return response.data;
  },

  async getStats(): Promise<CounterstrikeStats> {
    const response = await api.get('/counterstrike/stats');
    return response.data;
  },

  async processTraffic(traffic: TrafficData): Promise<{ status: string; result: any }> {
    const response = await api.post('/counterstrike/traffic/process', traffic);
    return response.data;
  },

  async getActiveThreats(): Promise<any[]> {
    const response = await api.get('/counterstrike/threats/active');
    return response.data;
  },

  async getRecentAssessments(limit: number = 20): Promise<any[]> {
    const response = await api.get('/counterstrike/assessments/recent', { params: { limit } });
    return response.data;
  },

  async getAllAttackers(): Promise<AttackerIdentity[]> {
    const response = await api.get('/counterstrike/recon/attackers');
    return response.data;
  },

  async getReconReports(limit: number = 20): Promise<any[]> {
    const response = await api.get('/counterstrike/recon/reports', { params: { limit } });
    return response.data;
  },

  async getAttackChains(status?: string): Promise<AttackChain[]> {
    const params = status ? { status } : {};
    const response = await api.get('/counterstrike/trace/chains', { params });
    return response.data;
  },

  async getAttackChain(chainId: string): Promise<AttackChain> {
    const response = await api.get(`/counterstrike/trace/chains/${chainId}`);
    return response.data;
  },

  async getChainTimeline(chainId: string): Promise<any[]> {
    const response = await api.get(`/counterstrike/trace/chains/${chainId}/timeline`);
    return response.data;
  },

  async getChainGraph(chainId: string): Promise<any> {
    const response = await api.get(`/counterstrike/trace/chains/${chainId}/graph`);
    return response.data;
  },

  async createHoneypot(config: HoneypotCreate): Promise<any> {
    const response = await api.post('/counterstrike/honeypot/create', config);
    return response.data;
  },

  async listHoneypots(): Promise<Honeypot[]> {
    const response = await api.get('/counterstrike/honeypot/list');
    return response.data;
  },

  async getHoneypot(honeypotId: string): Promise<Honeypot> {
    const response = await api.get(`/counterstrike/honeypot/${honeypotId}`);
    return response.data;
  },

  async shutdownHoneypot(honeypotId: string): Promise<{ status: string; honeypot_id: string }> {
    const response = await api.delete(`/counterstrike/honeypot/${honeypotId}`);
    return response.data;
  },

  async getCapturedCredentials(): Promise<any[]> {
    const response = await api.get('/counterstrike/honeypot/credentials');
    return response.data;
  },

  async getAllIdentities(): Promise<AttackerIdentity[]> {
    const response = await api.get('/counterstrike/attribution/identities');
    return response.data;
  },

  async getIdentity(identityId: string): Promise<AttackerIdentity> {
    const response = await api.get(`/counterstrike/attribution/identities/${identityId}`);
    return response.data;
  },

  async getBlacklist(): Promise<any[]> {
    const response = await api.get('/counterstrike/attribution/blacklist');
    return response.data;
  },

  async getWatchlist(): Promise<any[]> {
    const response = await api.get('/counterstrike/attribution/watchlist');
    return response.data;
  },

  async createCounterStrike(action: CounterStrikeCreate): Promise<any> {
    const response = await api.post('/counterstrike/counter-strike/create', action);
    return response.data;
  },

  async approveCounterStrike(actionId: string, request: ApprovalRequest): Promise<{ status: string; action_id: string }> {
    const response = await api.post(`/counterstrike/counter-strike/${actionId}/approve`, request);
    return response.data;
  },

  async getActiveCounterStrikes(): Promise<CounterStrikeAction[]> {
    const response = await api.get('/counterstrike/counter-strike/active');
    return response.data;
  },

  async getCounterStrikeHistory(limit: number = 50): Promise<CounterStrikeAction[]> {
    const response = await api.get('/counterstrike/counter-strike/history', { params: { limit } });
    return response.data;
  },

  async createPursuit(pursuit: PursuitCreate): Promise<any> {
    const response = await api.post('/counterstrike/pursuit/create', pursuit);
    return response.data;
  },

  async getActivePursuits(): Promise<Pursuit[]> {
    const response = await api.get('/counterstrike/pursuit/active');
    return response.data;
  },

  async completePursuit(strategyId: string, success: boolean = true): Promise<{ status: string; strategy_id: string; success: boolean }> {
    const response = await api.post(`/counterstrike/pursuit/${strategyId}/complete?success=${success}`);
    return response.data;
  },

  async getAllTactics(): Promise<Tactic[]> {
    const response = await api.get('/counterstrike/tactics');
    return response.data;
  },

  async createTactic(tactic: TacticCreate): Promise<any> {
    const response = await api.post('/counterstrike/tactics/create', tactic);
    return response.data;
  },

  async recommendTactics(attackType: string, threatLevel: number = 2, confidence: number = 0.5): Promise<any[]> {
    const response = await api.get('/counterstrike/tactics/recommend', {
      params: { attack_type: attackType, threat_level: threatLevel, confidence },
    });
    return response.data;
  },

  async queryMemory(memoryType?: string, attackerId?: string, limit: number = 20): Promise<any> {
    const params: any = { limit };
    if (memoryType) params.memory_type = memoryType;
    if (attackerId) params.attacker_id = attackerId;
    const response = await api.get('/counterstrike/memory/query', { params });
    return response.data;
  },

  async getReviewReports(limit: number = 20): Promise<any[]> {
    const response = await api.get('/counterstrike/review/reports', { params: { limit } });
    return response.data;
  },

  async getConsoleDashboard(): Promise<any> {
    const response = await api.get('/counterstrike/console/dashboard');
    return response.data;
  },

  async getPendingApprovals(): Promise<any[]> {
    const response = await api.get('/counterstrike/console/approvals/pending');
    return response.data;
  },

  async consoleApprove(request: ApprovalRequest): Promise<{ status: string }> {
    const response = await api.post('/counterstrike/console/approve', request);
    return response.data;
  },

  async consoleReject(request: RejectionRequest): Promise<{ status: string }> {
    const response = await api.post('/counterstrike/console/reject', request);
    return response.data;
  },

  async setOperationMode(mode: string, operator: string): Promise<{ status: string; mode: string }> {
    const response = await api.post(`/counterstrike/console/mode?mode=${mode}&operator=${operator}`);
    return response.data;
  },

  async getBoundaryRules(): Promise<any[]> {
    const response = await api.get('/counterstrike/boundary/rules');
    return response.data;
  },

  async getBoundaryViolations(limit: number = 50): Promise<any[]> {
    const response = await api.get('/counterstrike/boundary/violations', { params: { limit } });
    return response.data;
  },

  async getPheromoneState(): Promise<any> {
    const response = await api.get('/counterstrike/pheromone/state');
    return response.data;
  },

  async getCoordinationStats(): Promise<any> {
    const response = await api.get('/counterstrike/coordination/stats');
    return response.data;
  },
};

export default counterstrikeApi;
