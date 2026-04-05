// 房产类型定义
export interface Property {
  id: string;
  address: string;
  type: 'apartment' | 'house' | 'commercial' | 'other';
  area: number;
  age: number;
  description?: string;
  price?: number;
  marketValue?: number;
  createdAt: string;
  updatedAt: string;
}

// 用户类型定义
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin' | 'analyst';
  createdAt: string;
  updatedAt: string;
}

// 报告类型定义
export interface Report {
  id: string;
  propertyId: string;
  propertyAddress: string;
  title: string;
  content: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
  generatedAt?: string;
}

// 分析任务类型定义
export interface AnalysisTask {
  id: string;
  propertyId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  steps: AnalysisStep[];
  createdAt: string;
  updatedAt: string;
}

// 分析步骤类型定义
export interface AnalysisStep {
  id: string;
  taskId: string;
  name: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  result?: string;
  error?: string;
  startedAt?: string;
  completedAt?: string;
}

// API响应类型定义
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 分页类型定义
export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

// 分页响应类型定义
export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}
