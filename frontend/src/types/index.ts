export interface User {
  id: string;
  email: string;
  username: string;
  role: 'user' | 'admin' | 'super_admin';
  integral: number;
  membership_level: string;
  membership_expires: string | null;
  source?: string;
  source_name?: string;
  bonus_label?: string;
  created_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  query: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface Report {
  id: string;
  task_id: string;
  content: string;
  summary?: string;
  confidence?: number;
  data_sources?: string[];
  created_at: string;
}

export interface IntegralLog {
  id: string;
  user_id: string;
  change: number;
  balance_after: number;
  reason: string;
  admin_note?: string;
  created_at: string;
}

export interface Feedback {
  id: string;
  user_id: string;
  type: string;
  title: string;
  content: string;
  status: 'pending' | 'processing' | 'resolved' | 'rejected';
  admin_reply?: string;
  created_at: string;
  replied_at?: string;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  content: string;
  read: boolean;
  created_at: string;
}

export interface Plan {
  id: string;
  name: string;
  price: number;
  integral: number;
  description: string;
  popular?: boolean;
}

export interface RechargeOrder {
  id: string;
  user_id: string;
  amount: number;
  integral: number;
  status: 'pending' | 'approved' | 'rejected';
  wechat_transaction_id: string;
  notes?: string;
  created_at: string;
  processed_at?: string;
}

export interface AgentStep {
  id: string;
  task_id: string;
  agent_name: string;
  step_name: string;
  step_detail?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
}

export interface CompareAnalysis {
  id: string;
  user_id: string;
  locations: string[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: any;
  created_at: string;
}

export interface Article {
  id: string;
  title: string;
  slug: string;
  content: string;
  summary?: string;
  cover_image?: string;
  author: string;
  tags: string[];
  view_count: number;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  detail?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
