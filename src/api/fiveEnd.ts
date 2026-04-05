import api from '../services/api';

export type EndType = 'government' | 'enterprise' | 'education' | 'standard' | 'public';

export interface FiveEndStatus {
  status: string;
  timestamp: number;
  initialized: boolean;
}

export interface ClusterStatus {
  cluster_id: string;
  agents: {
    [key: string]: number;
  };
  energy: number;
  status: string;
}

export interface EventCreateRequest {
  event_type: string;
  source_end: string;
  source_agent: string;
  target_end?: string;
  target_agent?: string;
  broadcast?: boolean;
  payload?: Record<string, unknown>;
  priority?: number;
}

export interface BlackboardWriteRequest {
  key: string;
  value: unknown;
  source_end: string;
  source_agent: string;
  knowledge_type?: string;
  region?: string;
  ttl?: number;
  tags?: string[];
}

export interface ProposalCreateRequest {
  proposal_type: string;
  title: string;
  description: string;
  content?: Record<string, unknown>;
  proposer_end: string;
  proposer_agent: string;
  voting_duration?: number;
  required_quorum?: number;
}

export interface VoteRequest {
  proposal_id: string;
  voter_end: string;
  voter_agent: string;
  choice: string;
  reason?: string;
}

export interface DisclaimerConsentRequest {
  user_id: string;
  disclaimer_type: string;
  ip_address?: string;
  device_fingerprint?: string;
  user_agent?: string;
  session_id?: string;
}

export interface BanCreateRequest {
  ban_type: string;
  target_value: string;
  reason: string;
  risk_score?: number;
  duration_seconds?: number;
  is_permanent?: boolean;
  source_end?: string;
  source_agent?: string;
}

export interface AppealCreateRequest {
  ban_id: string;
  user_id: string;
  contact_info: string;
  appeal_reason: string;
  evidence?: string[];
}

export interface AppealResolveRequest {
  appeal_id: string;
  action: string;
  reviewer_id: string;
  notes?: string;
}

export const fiveEndApi = {
  async getStatus(): Promise<FiveEndStatus> {
    const response = await api.get('/five-end/status');
    return response.data;
  },

  async getGovernmentClusterStatus(): Promise<ClusterStatus> {
    const response = await api.get('/five-end/government/cluster/status');
    return response.data;
  },

  async getEnterpriseClusterStatus(): Promise<ClusterStatus> {
    const response = await api.get('/five-end/enterprise/cluster/status');
    return response.data;
  },

  async getEducationClusterStatus(): Promise<ClusterStatus> {
    const response = await api.get('/five-end/education/cluster/status');
    return response.data;
  },

  async getStandardClusterStatus(): Promise<ClusterStatus> {
    const response = await api.get('/five-end/standard/cluster/status');
    return response.data;
  },

  async getPublicClusterStatus(): Promise<ClusterStatus> {
    const response = await api.get('/five-end/public/cluster/status');
    return response.data;
  },

  async getAllClustersStatus(): Promise<Record<EndType, ClusterStatus>> {
    const [government, enterprise, education, standard, public_] = await Promise.all([
      this.getGovernmentClusterStatus(),
      this.getEnterpriseClusterStatus(),
      this.getEducationClusterStatus(),
      this.getStandardClusterStatus(),
      this.getPublicClusterStatus(),
    ]);
    return { government, enterprise, education, standard, public: public_ };
  },
};

export default fiveEndApi;
