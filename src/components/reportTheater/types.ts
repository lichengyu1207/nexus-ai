export interface ReportData {
  id: string;
  taskId: string;
  title: string;
  summary: string;
  createdAt: string;
  charts: ReportChart[];
  insights: ReportInsight[];
  rawData?: any;
}

export interface ReportChart {
  id: string;
  type: 'line' | 'bar' | 'pie' | 'heatmap';
  title: string;
  data: any[];
  config?: {
    colors?: string[];
    xAxisLabel?: string;
    yAxisLabel?: string;
  };
}

export interface ReportInsight {
  id: string;
  content: string;
  confidence: number;
  sourceAgent?: string;
  type?: 'positive' | 'negative' | 'neutral';
}

export interface ReportGenerationProgress {
  taskId: string;
  status: 'pending' | 'collecting' | 'analyzing' | 'rendering' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  partialData?: Partial<ReportData>;
}

export interface DataFlowParticle {
  id: string;
  sourceAgent: string;
  targetX: number;
  targetY: number;
  x: number;
  y: number;
  color: string;
  size: number;
  speed: number;
  trail: { x: number; y: number }[];
}

export const agentColors: Record<string, string> = {
  li: '#6366f1',
  hu: '#10b981',
  li_guan: '#3b82f6',
  bing: '#f59e0b',
  gong: '#ef4444',
  xing: '#8b5cf6',
};
