export interface VoiceSettings {
  enabled: boolean;
  volume: number;
  rate: number;
  pitch: number;
  voiceURI: string;
  events: VoiceEvents;
  customSounds: CustomSounds;
  agentVoices: Record<string, string>;
}

export interface VoiceEvents {
  taskCompleted: boolean;
  taskFailed: boolean;
  taskProgress: boolean;
  newNotification: boolean;
  agentStatusChange: boolean;
  collaborationEvent: boolean;
}

export interface CustomSounds {
  taskCompleted?: string;
  taskFailed?: string;
  taskProgress?: string;
  newNotification?: string;
  agentStatusChange?: string;
  collaborationEvent?: string;
}

export interface VoiceCommand {
  phrase: string | RegExp;
  action: () => void;
  description: string;
}

export interface SpeechQueueItem {
  text: string;
  options?: SpeechOptions;
  id: string;
}

export interface SpeechOptions {
  voiceURI?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

export interface VoiceRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

export type VoiceEventType = keyof VoiceEvents;

export const DEFAULT_VOICE_SETTINGS: VoiceSettings = {
  enabled: true,
  volume: 0.8,
  rate: 1.0,
  pitch: 1.0,
  voiceURI: '',
  events: {
    taskCompleted: true,
    taskFailed: true,
    taskProgress: false,
    newNotification: true,
    agentStatusChange: false,
    collaborationEvent: false,
  },
  customSounds: {},
  agentVoices: {},
};

export const EVENT_LABELS: Record<VoiceEventType, string> = {
  taskCompleted: '任务完成',
  taskFailed: '任务失败',
  taskProgress: '任务进度更新',
  newNotification: '新通知',
  agentStatusChange: '智能体状态变更',
  collaborationEvent: '协同事件',
};

export const RATE_OPTIONS = [
  { value: 0.5, label: '慢速' },
  { value: 1.0, label: '正常' },
  { value: 1.5, label: '快速' },
  { value: 2.0, label: '极快' },
];

export const VOICE_COMMANDS: VoiceCommand[] = [
  { phrase: '新建任务', action: () => {}, description: '创建新任务' },
  { phrase: '任务列表', action: () => {}, description: '查看任务列表' },
  { phrase: '智能体状态', action: () => {}, description: '查看智能体状态' },
  { phrase: '打开设置', action: () => {}, description: '打开设置页面' },
  { phrase: '静音', action: () => {}, description: '关闭语音播报' },
  { phrase: '取消静音', action: () => {}, description: '开启语音播报' },
];
