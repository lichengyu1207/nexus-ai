import api from '../services/api';

export interface DataEngineStatus {
  is_active: boolean;
  total_pipelines: number;
  active_pipelines: number;
  total_datasets: number;
  storage_used: number;
}

export interface DataPipeline {
  id: string;
  name: string;
  source_type: string;
  target_type: string;
  status: 'idle' | 'running' | 'paused' | 'error';
  schedule?: string;
  last_run?: string;
  next_run?: string;
  records_processed: number;
}

export interface Dataset {
  id: string;
  name: string;
  type: string;
  size: number;
  records: number;
  created_at: string;
  updated_at: string;
}

export const dataEngineApi = {
  async getStatus(): Promise<DataEngineStatus> {
    const response = await api.get('/data-engine/status');
    return response.data;
  },

  async getPipelines(): Promise<{ pipelines: DataPipeline[]; total: number }> {
    const response = await api.get('/data-engine/pipelines');
    return response.data;
  },

  async createPipeline(request: {
    name: string;
    source_type: string;
    source_config: Record<string, unknown>;
    target_type: string;
    target_config: Record<string, unknown>;
    schedule?: string;
  }): Promise<{ success: boolean; pipeline: DataPipeline }> {
    const response = await api.post('/data-engine/pipelines', { json: request });
    return response.data;
  },

  async runPipeline(pipelineId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/data-engine/pipelines/${pipelineId}/run`);
    return response.data;
  },

  async getDatasets(): Promise<{ datasets: Dataset[]; total: number }> {
    const response = await api.get('/data-engine/datasets');
    return response.data;
  },

  async getDataset(datasetId: string): Promise<Dataset> {
    const response = await api.get(`/data-engine/datasets/${datasetId}`);
    return response.data;
  },

  async deleteDataset(datasetId: string): Promise<{ success: boolean }> {
    const response = await api.delete(`/data-engine/datasets/${datasetId}`);
    return response.data;
  },
};

export default dataEngineApi;
