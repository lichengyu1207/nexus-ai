export type MemoryType = 'episodic' | 'semantic' | 'procedural';

export interface Memory {
  id: string;
  title?: string;
  content: string;
  type: MemoryType;
  importance: number;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  version: number;
  versions?: MemoryVersion[];
  associations: {
    memories: string[];
    tasks: string[];
    agents: string[];
  };
}

export interface MemoryVersion {
  version: number;
  content: string;
  updatedAt: string;
  updatedBy: string;
  changeSummary?: string;
}

export interface MemoryFilters {
  searchText?: string;
  type?: MemoryType[];
  importanceMin?: number;
  dateRange?: { start: string; end: string };
  agentIds?: string[];
  tags?: string[];
}

export interface GraphNode {
  id: string;
  name: string;
  type: MemoryType;
  importance: number;
  size: number;
  color: string;
}

export interface GraphLink {
  source: string;
  target: string;
  value: number;
}

export interface PaginatedMemories {
  items: Memory[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export type ViewMode = 'card' | 'graph';
export type SortBy = 'time' | 'importance';
