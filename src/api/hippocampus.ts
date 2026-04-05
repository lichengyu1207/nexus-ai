import api from '../services/api';

export interface HippocampusMemory {
  id: string;
  user_id: string;
  type: 'episodic' | 'semantic' | 'procedural';
  content: string;
  summary: string;
  importance: number;
  timestamp: string;
  source: string;
  agents: string[];
  entities: string[];
  context: Record<string, unknown>;
  access_count: number;
  last_access: string | null;
  created_at: string;
}

export interface SearchResult {
  memory: HippocampusMemory;
  score: number;
  match_type: string;
}

export interface MemoryStats {
  total_memories: number;
  by_type: Record<string, number>;
  average_importance: number;
  health_score: number;
  type_distribution: Record<string, number>;
}

export interface RelatedMemory {
  memory: HippocampusMemory;
  relation_type: string;
  strength: number;
}

export interface CreateMemoryRequest {
  content: string;
  source?: string;
  memory_type?: 'episodic' | 'semantic' | 'procedural';
  agents?: string[];
  context?: Record<string, unknown>;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  min_importance?: number;
  memory_type?: string;
}

export const hippocampusApi = {
  async createMemory(request: CreateMemoryRequest): Promise<HippocampusMemory> {
    const response = await api.post('/hippocampus/memories', request);
    return response.data;
  },

  async getMemories(params?: {
    limit?: number;
    offset?: number;
    memory_type?: string;
    days?: number;
  }): Promise<HippocampusMemory[]> {
    const response = await api.get('/hippocampus/memories', { params });
    return response.data;
  },

  async getMemory(memoryId: string): Promise<HippocampusMemory> {
    const response = await api.get(`/hippocampus/memories/${memoryId}`);
    return response.data;
  },

  async deleteMemory(memoryId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/hippocampus/memories/${memoryId}`);
    return response.data;
  },

  async searchMemories(request: SearchRequest): Promise<SearchResult[]> {
    const response = await api.post('/hippocampus/search', request);
    return response.data;
  },

  async searchByEntity(entity: string, limit?: number): Promise<HippocampusMemory[]> {
    const response = await api.get(`/hippocampus/search/entity/${encodeURIComponent(entity)}`, {
      params: { limit },
    });
    return response.data;
  },

  async getRecentMemories(days?: number, limit?: number): Promise<HippocampusMemory[]> {
    const response = await api.get('/hippocampus/recent', {
      params: { days, limit },
    });
    return response.data;
  },

  async getImportantMemories(minImportance?: number, limit?: number): Promise<HippocampusMemory[]> {
    const response = await api.get('/hippocampus/important', {
      params: { min_importance: minImportance, limit },
    });
    return response.data;
  },

  async getMemoryContext(query?: string, maxMemories?: number): Promise<{
    context: string;
    query: string;
  }> {
    const response = await api.get('/hippocampus/context', {
      params: { query, max_memories: maxMemories },
    });
    return response.data;
  },

  async getStats(): Promise<MemoryStats> {
    const response = await api.get('/hippocampus/stats');
    return response.data;
  },

  async consolidate(): Promise<{
    success: boolean;
    consolidated_count: number;
    message: string;
  }> {
    const response = await api.post('/hippocampus/consolidate');
    return response.data;
  },

  async getRelatedMemories(memoryId: string, limit?: number): Promise<RelatedMemory[]> {
    const response = await api.get(`/hippocampus/memories/${memoryId}/related`, {
      params: { limit },
    });
    return response.data;
  },

  async getMemoryTimeline(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: 'day' | 'week' | 'month';
  }): Promise<Array<{
    date: string;
    count: number;
    avg_importance: number;
    types: Record<string, number>;
  }>> {
    const response = await api.get('/hippocampus/timeline', { params });
    return response.data;
  },
};

export default hippocampusApi;
