import { create } from 'zustand';

type SceneType = 'idle' | 'scene1' | 'scene2' | 'scene3' | 'complete';
type AgentStatus = 'idle' | 'working' | 'done';

interface AgentState {
  status: AgentStatus;
  message: string;
  progress: number;
}

interface ReportSection {
  type: string;
  title?: string;
  content?: string;
  chartType?: string;
  visible: boolean;
}

interface DemoState {
  currentScene: SceneType;
  userInput: string;
  agentsStatus: Record<string, AgentState>;
  reportData: ReportSection[];
  isPlaying: boolean;
  startTime: number | null;
  lightBeams: LightBeam[];
  dataFlows: DataFlow[];
  
  startDemo: (input?: string) => void;
  resetDemo: () => void;
  setScene: (scene: SceneType) => void;
  setAgentStatus: (agentId: string, status: AgentStatus, message?: string) => void;
  addReportSection: (section: ReportSection) => void;
  addLightBeam: (beam: LightBeam) => void;
  removeLightBeam: (id: string) => void;
  addDataFlow: (flow: DataFlow) => void;
  removeDataFlow: (id: string) => void;
}

interface LightBeam {
  id: string;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  color: string;
  progress: number;
}

interface DataFlow {
  id: string;
  fromAgent: string;
  toAgent: string;
  color: string;
  progress: number;
}

const initialAgentsStatus: Record<string, AgentState> = {
  li: { status: 'idle', message: '', progress: 0 },
  hu: { status: 'idle', message: '', progress: 0 },
  li_guan: { status: 'idle', message: '', progress: 0 },
  bing: { status: 'idle', message: '', progress: 0 },
  gong: { status: 'idle', message: '', progress: 0 },
  xing: { status: 'idle', message: '', progress: 0 },
};

export const useDemoStore = create<DemoState>((set, get) => ({
  currentScene: 'idle',
  userInput: '帮我分析深圳南山区学区房',
  agentsStatus: initialAgentsStatus,
  reportData: [],
  isPlaying: false,
  startTime: null,
  lightBeams: [],
  dataFlows: [],

  startDemo: (input) => {
    set({
      currentScene: 'scene1',
      userInput: input || get().userInput,
      isPlaying: true,
      startTime: Date.now(),
      agentsStatus: initialAgentsStatus,
      reportData: [],
      lightBeams: [],
      dataFlows: [],
    });
  },

  resetDemo: () => {
    set({
      currentScene: 'idle',
      isPlaying: false,
      startTime: null,
      agentsStatus: initialAgentsStatus,
      reportData: [],
      lightBeams: [],
      dataFlows: [],
    });
  },

  setScene: (scene) => {
    set({ currentScene: scene });
  },

  setAgentStatus: (agentId, status, message = '') => {
    set((state) => ({
      agentsStatus: {
        ...state.agentsStatus,
        [agentId]: {
          status,
          message,
          progress: status === 'done' ? 100 : status === 'working' ? 50 : 0,
        },
      },
    }));
  },

  addReportSection: (section) => {
    set((state) => ({
      reportData: [...state.reportData, { ...section, visible: true }],
    }));
  },

  addLightBeam: (beam) => {
    set((state) => ({
      lightBeams: [...state.lightBeams, beam],
    }));
  },

  removeLightBeam: (id) => {
    set((state) => ({
      lightBeams: state.lightBeams.filter((b) => b.id !== id),
    }));
  },

  addDataFlow: (flow) => {
    set((state) => ({
      dataFlows: [...state.dataFlows, flow],
    }));
  },

  removeDataFlow: (id) => {
    set((state) => ({
      dataFlows: state.dataFlows.filter((f) => f.id !== id),
    }));
  },
}));
