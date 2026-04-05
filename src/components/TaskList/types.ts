export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Task {
  id: string;
  name: string;
  status: TaskStatus;
  progress: number;
  startTime: string;
  estimatedEndTime?: string;
  resultSummary?: string;
  errorMessage?: string;
  inputParams?: Record<string, unknown>;
  agentsUsed?: string[];
  fullProcessLog?: string[];
}

export interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  limit: number;
}

export interface TaskStats {
  total: number;
  completed: number;
  processing: number;
  failed: number;
}
