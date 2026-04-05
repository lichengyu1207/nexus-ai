export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type TaskPriority = 'low' | 'medium' | 'high';

export type TaskSortField = 'createdAt' | 'progress' | 'priority';
export type TaskSortOrder = 'asc' | 'desc';

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
  tags?: string[];
  priority?: TaskPriority;
}

export interface TaskFilters {
  status: TaskStatus[];
  dateRange?: { start: string; end: string };
  agentIds?: string[];
  tags?: string[];
  searchText?: string;
  progressMin?: number;
  progressMax?: number;
}

export interface TaskSort {
  field: TaskSortField;
  order: TaskSortOrder;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  nextPage?: number;
}

export interface BatchActionPayload {
  taskIds: string[];
}

export interface NewTaskPayload {
  name: string;
  agentId: string;
  inputParams?: Record<string, unknown>;
  scheduledTime?: string;
}

export type ViewMode = 'card' | 'table';

export type BatchAction = 'retry' | 'delete' | 'export';

export interface TaskDetail {
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
  tags?: string[];
  priority?: TaskPriority;
  workflowSteps?: WorkflowStep[];
  intermediateResults?: IntermediateResult[];
  finalReport?: FinalReport;
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: TaskStatus;
  startTime?: string;
  endTime?: string;
  agentId?: string;
}

export interface IntermediateResult {
  id: string;
  name: string;
  type: string;
  value: unknown;
  timestamp: string;
}

export interface FinalReport {
  id: string;
  title: string;
  summary: string;
  downloadUrl: string;
  generatedAt: string;
}
