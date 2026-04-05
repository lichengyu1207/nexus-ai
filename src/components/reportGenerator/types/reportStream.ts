export type ReportChunkType = 
  | 'title'
  | 'summary'
  | 'section-title'
  | 'paragraph'
  | 'insight'
  | 'chart'
  | 'chart-point'
  | 'typing-record'
  | 'disclaimer'
  | 'copyright'
  | 'reference'
  | 'complete';

export interface ChartPoint {
  x: number | string;
  y: number;
  agent?: string;
}

export interface ChartData {
  chartId: string;
  chartType: 'line' | 'bar' | 'pie';
  title: string;
  data: ChartPoint[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  colors?: string[];
}

export interface InsightData {
  id: string;
  text: string;
  agent: string;
  timestamp: number;
  type: 'positive' | 'negative' | 'neutral';
}

export interface TypingRecordData {
  id: string;
  agent: string;
  content: string;
  timestamp: number;
  isVirtual: boolean;
  source?: string;
}

export interface ReferenceData {
  id: string;
  title: string;
  source: string;
  url?: string;
  publishDate?: string;
  agent?: string;
}

export interface DisclaimerData {
  title: string;
  content: string;
}

export interface CopyrightData {
  holder: string;
  year: string;
  rights: string;
  contact?: string;
}

export interface SectionTitleData {
  id: string;
  text: string;
  level: 1 | 2 | 3;
}

export interface ParagraphData {
  id: string;
  text: string;
  agent?: string;
}

export interface ReportChunk {
  type: ReportChunkType;
  content: string | ChartData | ChartPoint | TypingRecordData | ReferenceData | DisclaimerData | CopyrightData | SectionTitleData | ParagraphData;
  agent?: string;
  timestamp: number;
  chartId?: string;
}

export interface AgentContribution {
  agentId: string;
  agentName: string;
  agentIcon: string;
  contributionCount: number;
  dataTypes: string[];
  lastContribution: number;
}

export interface ReportState {
  title: string;
  summary: string;
  sections: Array<{ title: string; paragraphs: string[] }>;
  insights: InsightData[];
  charts: Map<string, ChartData>;
  typingRecords: TypingRecordData[];
  references: ReferenceData[];
  disclaimer: DisclaimerData | null;
  copyright: CopyrightData | null;
  progress: number;
  isComplete: boolean;
  startTime: number;
  agentContributions: Map<string, AgentContribution>;
}

export interface PlaybackState {
  isPlaying: boolean;
  speed: number;
  currentTime: number;
  totalDuration: number;
}

export const AGENT_CONFIG: Record<string, { name: string; icon: string; color: string }> = {
  hubu: { name: '户部', icon: '🏛️', color: '#F59E0B' },
  bingbu: { name: '兵部', icon: '⚔️', color: '#EF4444' },
  libu: { name: '吏部', icon: '📜', color: '#3B82F6' },
  gongbu: { name: '工部', icon: '🔧', color: '#10B981' },
  xingbu: { name: '刑部', icon: '⚖️', color: '#8B5CF6' },
  libu2: { name: '礼部', icon: '🎭', color: '#EC4899' },
  analyst: { name: '分析师', icon: '📊', color: '#06B6D4' },
  collector: { name: '采集器', icon: '📡', color: '#84CC16' },
};

export function getAgentInfo(agentId: string) {
  return AGENT_CONFIG[agentId] || { name: agentId, icon: '🤖', color: '#6B7280' };
}
