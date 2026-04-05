export interface Message {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  timestamp: Date;
  agent?: 'zhouyu' | 'luxun';
  memoryId?: string;
}

export interface Agent {
  name: string;
  title: string;
  personality: string;
  avatar: string;
}

export interface Report {
  report_id: string;
  title: string;
  summary: string;
  emotion_trend: string;
  suggestions: string[];
  chart_data: {
    labels: string[];
    values: number[];
  };
  generated_at: string;
}

export interface ChatRequest {
  message: string;
  agent: 'zhouyu' | 'luxun';
}

export interface ChatResponse {
  reply: string;
  report_id: string;
}

export interface Memory {
  id: string;
  user_message: string;
  agent_reply: string;
  agent: string;
  emotion_tag?: string;
  created_at: number;
}
