export type AssetType = 'datasource' | 'dataset' | 'knowledgebase';

export type DataSourceType = 'mysql' | 'postgres' | 's3' | 'api';

export type ViewMode = 'list' | 'card' | 'lineage';

export interface Asset {
  id: string;
  name: string;
  type: AssetType;
  description?: string;
  createdAt: string;
  updatedAt: string;
  owner: string;
  tags: string[];
  size?: number;
  recordCount?: number;
  qualityScore?: number;
  version: number;
  parentId?: string;
}

export interface AssetConfig {
  type: DataSourceType;
  connection?: string;
  syncSchedule?: string;
}

export interface AssetDetail extends Asset {
  config: AssetConfig;
  previewData?: Record<string, unknown>[];
  lineage: {
    upstream: string[];
    downstream: string[];
  };
  versions: AssetVersion[];
  permissions: Permission[];
}

export interface AssetVersion {
  version: number;
  createdAt: string;
  createdBy: string;
  changeSummary: string;
  snapshotUrl?: string;
}

export interface Permission {
  id: string;
  principalType: 'user' | 'agent' | 'role';
  principalId: string;
  principalName: string;
  accessLevel: 'read' | 'write' | 'admin';
  grantedAt: string;
}

export interface QualityMetric {
  assetId: string;
  completeness: number;
  accuracy: number;
  timeliness: number;
  lastChecked: string;
}

export interface QualityStats {
  overallScore: number;
  byType: {
    type: AssetType;
    count: number;
    avgScore: number;
  }[];
  trend: {
    date: string;
    score: number;
  }[];
  recentIssues: {
    assetId: string;
    assetName: string;
    issue: string;
    severity: 'low' | 'medium' | 'high';
  }[];
}

export interface TreeNode {
  id: string;
  name: string;
  type: 'folder' | AssetType;
  children?: TreeNode[];
  parentId?: string;
  assetCount?: number;
}

export interface AssetListResponse {
  assets: Asset[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface AssetFilters {
  parentId?: string;
  type?: AssetType;
  search?: string;
  sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'qualityScore';
  sortOrder?: 'asc' | 'desc';
}

export interface LineageNode {
  id: string;
  name: string;
  type: AssetType;
  x?: number;
  y?: number;
}

export interface LineageEdge {
  id: string;
  source: string;
  target: string;
}

export interface LineageData {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export const ASSET_TYPE_CONFIG: Record<AssetType, {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
}> = {
  datasource: {
    label: '数据源',
    icon: 'CircleStackIcon',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
  },
  dataset: {
    label: '数据集',
    icon: 'TableCellsIcon',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
  },
  knowledgebase: {
    label: '知识库',
    icon: 'BookOpenIcon',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
  },
};

export const DATA_SOURCE_TYPE_CONFIG: Record<DataSourceType, {
  label: string;
  icon: string;
}> = {
  mysql: { label: 'MySQL', icon: 'DatabaseIcon' },
  postgres: { label: 'PostgreSQL', icon: 'DatabaseIcon' },
  s3: { label: 'Amazon S3', icon: 'CloudIcon' },
  api: { label: 'REST API', icon: 'CloudArrowDownIcon' },
};

export const ACCESS_LEVEL_CONFIG: Record<Permission['accessLevel'], {
  label: string;
  color: string;
}> = {
  read: { label: '只读', color: 'text-blue-400' },
  write: { label: '读写', color: 'text-green-400' },
  admin: { label: '管理', color: 'text-amber-400' },
};
