export interface TaskMetric {
  valuation: number;
  riskScore: number;
  confidence: number;
  suggestion: string;
  profitExpectation: number;
}

export interface RadarData {
  valuation: number;
  riskScore: number;
  profitExpectation: number;
  stability: number;
}

export interface CompareTask {
  id: string;
  name: string;
  completedAt: string;
  metrics: TaskMetric;
  radarData: RadarData;
}

export interface CompareResponse {
  tasks: CompareTask[];
}

export interface AvailableTask {
  id: string;
  name: string;
  completedAt: string;
}

export interface DifferenceAnalysis {
  metric: string;
  maxValue: number;
  minValue: number;
  maxTask: string;
  minTask: string;
  diffPercent: number;
  isSignificant: boolean;
}
