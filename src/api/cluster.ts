import api from '../services/api';

export interface AgentNode {
  id: string;
  name: string;
  type: 'red' | 'blue' | 'supervisor' | 'collector' | 'analyst' | 'memory' | 'defense' | 'social';
  status: 'healthy' | 'degraded' | 'down' | 'starting';
  cpu: number;
  memory: number;
  connections: number;
  lastHeartbeat: string;
  address: string;
  version: string;
  uptime?: number;
  tasksCompleted?: number;
}

export interface SwarmLink {
  source: string;
  target: string;
  type: 'gossip' | 'consensus' | 'data' | 'control';
  latency: number;
  throughput: number;
  status: 'active' | 'idle' | 'error';
}

export interface LivenessRecord {
  id: string;
  userId?: string;
  method: 'face' | 'voice' | 'behavior' | 'multi';
  result: 'success' | 'failed' | 'spoof_attempt';
  confidence: number;
  timestamp: string;
  ip: string;
  userAgent: string;
  reason?: string;
  duration?: number;
}

export interface ClusterStats {
  totalNodes: number;
  healthyNodes: number;
  degradedNodes: number;
  downNodes: number;
  avgCpu: number;
  avgMemory: number;
  totalMessagesPerSec: number;
  livenessSuccessRate: number;
  uptime: number;
}

export interface NodeMetrics {
  nodeId: string;
  timestamps: string[];
  cpu: number[];
  memory: number[];
  connections: number[];
  throughput: number[];
}

export const clusterApi = {
  async getNodes(): Promise<AgentNode[]> {
    const response = await api.get('/cluster/nodes');
    return response.data;
  },

  async getNode(nodeId: string): Promise<AgentNode> {
    const response = await api.get(`/cluster/nodes/${nodeId}`);
    return response.data;
  },

  async getSwarmLinks(): Promise<SwarmLink[]> {
    const response = await api.get('/cluster/links');
    return response.data;
  },

  async getLivenessRecords(params?: {
    limit?: number;
    result?: string;
    method?: string;
  }): Promise<{ records: LivenessRecord[]; total: number }> {
    const response = await api.get('/cluster/liveness', { params });
    return response.data;
  },

  async getClusterStats(): Promise<ClusterStats> {
    const response = await api.get('/cluster/stats');
    return response.data;
  },

  async getNodeMetrics(nodeId: string, params?: {
    duration?: number;
    interval?: number;
  }): Promise<NodeMetrics> {
    const response = await api.get(`/cluster/nodes/${nodeId}/metrics`, { params });
    return response.data;
  },

  async restartNode(nodeId: string): Promise<{ message: string }> {
    const response = await api.post(`/cluster/nodes/${nodeId}/restart`);
    return response.data;
  },

  async getSwarmTopology(): Promise<{
    nodes: Array<{ id: string; name: string; type: string; x: number; y: number }>;
    links: SwarmLink[];
  }> {
    const response = await api.get('/cluster/topology');
    return response.data;
  },

  async getLivenessStats(): Promise<{
    totalAttempts: number;
    successRate: number;
    spoofAttempts: number;
    byMethod: Record<string, { total: number; success: number }>;
  }> {
    const response = await api.get('/cluster/liveness/stats');
    return response.data;
  },

  async getHealthHistory(params?: {
    duration?: number;
    interval?: number;
  }): Promise<{
    timestamps: string[];
    healthyCount: number[];
    degradedCount: number[];
    downCount: number[];
  }> {
    const response = await api.get('/cluster/health/history', { params });
    return response.data;
  },
};

export default clusterApi;
