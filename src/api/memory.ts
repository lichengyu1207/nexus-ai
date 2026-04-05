import api from '../services/api';

export interface Memory {
  id: string;
  type: 'event' | 'fact' | 'procedure' | 'insight';
  input: string;
  output: string;
  importance: number;
  createdAt: string;
  lastAccessed?: string;
  accessCount: number;
  relatedMemories?: string[];
  agents?: string[];
  tags?: string[];
  metadata?: Record<string, unknown>;
  source?: 'user' | 'agent' | 'system';
}

export interface MemoryGraphNode {
  id: string;
  label: string;
  type: Memory['type'];
  importance: number;
  group?: string;
  accessCount?: number;
  createdAt?: string;
}

export interface MemoryGraphEdge {
  from: string;
  to: string;
  strength: number;
  type?: 'related' | 'derived' | 'contradicts';
}

export interface MemoryGraph {
  nodes: MemoryGraphNode[];
  edges: MemoryGraphEdge[];
  stats?: {
    totalNodes: number;
    totalEdges: number;
    avgImportance: number;
  };
}

export interface MemoryStats {
  total: number;
  byType: Record<Memory['type'], number>;
  avgImportance: number;
  recentCount: number;
  topAgents: Array<{ agent: string; count: number }>;
}

export interface CreateMemoryRequest {
  type: Memory['type'];
  input: string;
  output: string;
  importance?: number;
  relatedMemories?: string[];
  agents?: string[];
  tags?: string[];
  metadata?: Record<string, unknown>;
  source?: Memory['source'];
}

export interface MemoryListResponse {
  memories: Memory[];
  total: number;
  page: number;
  pageSize: number;
}

export interface MemorySearchParams {
  query?: string;
  type?: Memory['type'];
  minImportance?: number;
  agents?: string[];
  tags?: string[];
  startDate?: string;
  endDate?: string;
  page?: number;
  pageSize?: number;
}

export interface MiningResult {
  newMemories: Memory[];
  newConnections: Array<{
    from: string;
    to: string;
    strength: number;
  }>;
  insights: string[];
  progress: number;
}

export const memoryApi = {
  async getMemories(params?: MemorySearchParams): Promise<MemoryListResponse> {
    const response = await api.get('/memories', { params });
    return response.data;
  },

  async getMemory(id: string): Promise<Memory> {
    const response = await api.get(`/memories/${id}`);
    return response.data;
  },

  async createMemory(data: CreateMemoryRequest): Promise<Memory> {
    const response = await api.post('/memories', data);
    return response.data;
  },

  async updateMemory(id: string, data: Partial<CreateMemoryRequest>): Promise<Memory> {
    const response = await api.put(`/memories/${id}`, data);
    return response.data;
  },

  async deleteMemory(id: string): Promise<void> {
    await api.delete(`/memories/${id}`);
  },

  async updateImportance(id: string, importance: number): Promise<Memory> {
    const response = await api.patch(`/memories/${id}/importance`, { importance });
    return response.data;
  },

  async getMemoryGraph(params?: {
    minImportance?: number;
    maxNodes?: number;
    agentFilter?: string[];
  }): Promise<MemoryGraph> {
    const response = await api.get('/memories/graph', { params });
    return response.data;
  },

  async getMemoryStats(): Promise<MemoryStats> {
    const response = await api.get('/memories/stats');
    return response.data;
  },

  async searchMemories(query: string, limit?: number): Promise<Memory[]> {
    const response = await api.get('/memories/search', {
      params: { query, limit },
    });
    return response.data;
  },

  async getRelatedMemories(id: string, limit?: number): Promise<Memory[]> {
    const response = await api.get(`/memories/${id}/related`, {
      params: { limit },
    });
    return response.data;
  },

  async startMining(params?: {
    depth?: number;
    focusArea?: string;
  }): Promise<{ taskId: string; message: string }> {
    const response = await api.post('/memories/mine', params);
    return response.data;
  },

  async getMiningStatus(taskId: string): Promise<MiningResult> {
    const response = await api.get(`/memories/mine/${taskId}`);
    return response.data;
  },

  async getMemoryTimeline(params?: {
    startDate?: string;
    endDate?: string;
    groupBy?: 'day' | 'week' | 'month';
  }): Promise<Array<{
    date: string;
    count: number;
    avgImportance: number;
    types: Record<Memory['type'], number>;
  }>> {
    const response = await api.get('/memories/timeline', { params });
    return response.data;
  },

  async exportMemories(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await api.get('/memories/export', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  async importMemories(file: File): Promise<{
    imported: number;
    skipped: number;
    errors: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/memories/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export default memoryApi;
