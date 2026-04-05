import { create } from 'zustand';
import { 
  ReportChunk, 
  ChartData, 
  InsightData, 
  AgentContribution,
  ChartPoint,
  TypingRecordData,
  ReferenceData,
  DisclaimerData,
  CopyrightData,
  SectionTitleData,
  ParagraphData
} from './types/reportStream';
import { MockReportStreamPlayer } from './mockReportStream';

interface ReportSection {
  title: string;
  paragraphs: ParagraphData[];
}

interface ReportGeneratorState {
  title: string;
  summary: string;
  sections: ReportSection[];
  currentSectionIndex: number;
  insights: InsightData[];
  charts: Map<string, ChartData>;
  chartProgress: Map<string, number>;
  typingRecords: TypingRecordData[];
  references: ReferenceData[];
  disclaimer: DisclaimerData | null;
  copyright: CopyrightData | null;
  progress: number;
  isComplete: boolean;
  isPlaying: boolean;
  speed: number;
  currentTime: number;
  totalDuration: number;
  agentContributions: Map<string, AgentContribution>;
  activeAgent: string | null;
  streamPlayer: MockReportStreamPlayer | null;
  
  setTitle: (title: string) => void;
  setSummary: (summary: string) => void;
  addSectionTitle: (sectionTitle: SectionTitleData) => void;
  addParagraph: (paragraph: ParagraphData) => void;
  addInsight: (insight: InsightData) => void;
  addChart: (chart: ChartData) => void;
  updateChartProgress: (chartId: string, progress: number) => void;
  addChartPoint: (chartId: string, point: ChartPoint) => void;
  addTypingRecord: (record: TypingRecordData) => void;
  addReference: (reference: ReferenceData) => void;
  setDisclaimer: (disclaimer: DisclaimerData) => void;
  setCopyright: (copyright: CopyrightData) => void;
  setProgress: (progress: number) => void;
  setComplete: (isComplete: boolean) => void;
  setPlaying: (isPlaying: boolean) => void;
  setSpeed: (speed: number) => void;
  setCurrentTime: (time: number) => void;
  setActiveAgent: (agent: string | null) => void;
  processChunk: (chunk: ReportChunk) => void;
  initStreamPlayer: () => void;
  play: () => void;
  pause: () => void;
  reset: () => void;
  seekToProgress: (progress: number) => void;
}

export const useReportGeneratorStore = create<ReportGeneratorState>((set, get) => ({
  title: '',
  summary: '',
  sections: [],
  currentSectionIndex: -1,
  insights: [],
  charts: new Map(),
  chartProgress: new Map(),
  typingRecords: [],
  references: [],
  disclaimer: null,
  copyright: null,
  progress: 0,
  isComplete: false,
  isPlaying: false,
  speed: 1,
  currentTime: 0,
  totalDuration: 0,
  agentContributions: new Map(),
  activeAgent: null,
  streamPlayer: null,

  setTitle: (title) => set({ title }),
  
  setSummary: (summary) => set({ summary }),
  
  addSectionTitle: (sectionTitle) => set((state) => ({
    sections: [...state.sections, { title: sectionTitle.text, paragraphs: [] }],
    currentSectionIndex: state.sections.length,
  })),
  
  addParagraph: (paragraph) => set((state) => {
    if (state.currentSectionIndex < 0) return state;
    const newSections = [...state.sections];
    newSections[state.currentSectionIndex] = {
      ...newSections[state.currentSectionIndex],
      paragraphs: [...newSections[state.currentSectionIndex].paragraphs, paragraph],
    };
    return { sections: newSections };
  }),
  
  addInsight: (insight) => set((state) => ({
    insights: [...state.insights, insight],
  })),
  
  addChart: (chart) => set((state) => {
    const newCharts = new Map(state.charts);
    newCharts.set(chart.chartId, chart);
    const newProgress = new Map(state.chartProgress);
    newProgress.set(chart.chartId, 0);
    return { charts: newCharts, chartProgress: newProgress };
  }),
  
  updateChartProgress: (chartId, progress) => set((state) => {
    const newProgress = new Map(state.chartProgress);
    newProgress.set(chartId, progress);
    return { chartProgress: newProgress };
  }),
  
  addChartPoint: (chartId, point) => set((state) => {
    const chart = state.charts.get(chartId);
    if (!chart) return state;
    
    const newCharts = new Map(state.charts);
    const updatedChart = {
      ...chart,
      data: [...chart.data, point],
    };
    newCharts.set(chartId, updatedChart);
    
    return { charts: newCharts };
  }),
  
  addTypingRecord: (record) => set((state) => ({
    typingRecords: [...state.typingRecords, record],
  })),
  
  addReference: (reference) => set((state) => ({
    references: [...state.references, reference],
  })),
  
  setDisclaimer: (disclaimer) => set({ disclaimer }),
  
  setCopyright: (copyright) => set({ copyright }),
  
  setProgress: (progress) => set({ progress }),
  
  setComplete: (isComplete) => set({ isComplete }),
  
  setPlaying: (isPlaying) => set({ isPlaying }),
  
  setSpeed: (speed) => {
    const { streamPlayer } = get();
    streamPlayer?.setSpeed(speed);
    set({ speed });
  },
  
  setCurrentTime: (currentTime) => set({ currentTime }),
  
  setActiveAgent: (activeAgent) => set({ activeAgent }),
  
  processChunk: (chunk) => {
    const { addInsight, addChart, setTitle, setSummary, setComplete, setProgress, 
            addTypingRecord, addReference, setDisclaimer, setCopyright,
            addSectionTitle, addParagraph } = get();
    
    if (chunk.agent) {
      set((state) => {
        const newContributions = new Map(state.agentContributions);
        const existing = newContributions.get(chunk.agent!);
        
        if (existing) {
          newContributions.set(chunk.agent!, {
            ...existing,
            contributionCount: existing.contributionCount + 1,
            lastContribution: chunk.timestamp,
            dataTypes: existing.dataTypes.includes(chunk.type) 
              ? existing.dataTypes 
              : [...existing.dataTypes, chunk.type],
          });
        } else {
          newContributions.set(chunk.agent!, {
            agentId: chunk.agent!,
            agentName: chunk.agent!,
            agentIcon: '🤖',
            contributionCount: 1,
            dataTypes: [chunk.type],
            lastContribution: chunk.timestamp,
          });
        }
        
        return { 
          agentContributions: newContributions,
          activeAgent: chunk.agent!,
        };
      });
    }
    
    switch (chunk.type) {
      case 'title':
        setTitle(chunk.content as string);
        break;
      case 'summary':
        setSummary(chunk.content as string);
        break;
      case 'section-title':
        addSectionTitle(chunk.content as SectionTitleData);
        break;
      case 'paragraph':
        addParagraph(chunk.content as ParagraphData);
        break;
      case 'insight':
        addInsight({
          id: `insight-${Date.now()}`,
          text: chunk.content as string,
          agent: chunk.agent || 'unknown',
          timestamp: chunk.timestamp,
          type: 'neutral',
        });
        break;
      case 'chart':
        addChart(chunk.content as ChartData);
        break;
      case 'chart-point':
        get().addChartPoint(chunk.chartId!, chunk.content as ChartPoint);
        break;
      case 'typing-record':
        addTypingRecord(chunk.content as TypingRecordData);
        break;
      case 'reference':
        addReference(chunk.content as ReferenceData);
        break;
      case 'disclaimer':
        setDisclaimer(chunk.content as DisclaimerData);
        break;
      case 'copyright':
        setCopyright(chunk.content as CopyrightData);
        break;
      case 'complete':
        setComplete(true);
        setProgress(100);
        break;
    }
    
    const { streamPlayer } = get();
    if (streamPlayer) {
      set({
        progress: streamPlayer.getProgress(),
        currentTime: streamPlayer.getCurrentTime(),
      });
    }
  },
  
  initStreamPlayer: () => {
    const player = new MockReportStreamPlayer();
    
    player.subscribe((chunk) => {
      get().processChunk(chunk);
    });
    
    set({
      streamPlayer: player,
      totalDuration: player.getTotalDuration(),
    });
  },
  
  play: () => {
    const { streamPlayer, isPlaying } = get();
    set({ isPlaying: true });
    if (!streamPlayer) {
      get().initStreamPlayer();
      const newPlayer = get().streamPlayer!;
      newPlayer.subscribe((chunk) => {
        get().processChunk(chunk);
      });
      newPlayer.play();
    } else if (!isPlaying) {
      streamPlayer.play();
    }
  },
  
  pause: () => {
    const { streamPlayer } = get();
    streamPlayer?.pause();
    set({ isPlaying: false });
  },
  
  reset: () => {
    const { streamPlayer } = get();
    streamPlayer?.reset();
    
    set({
      title: '',
      summary: '',
      sections: [],
      currentSectionIndex: -1,
      insights: [],
      charts: new Map(),
      chartProgress: new Map(),
      typingRecords: [],
      references: [],
      disclaimer: null,
      copyright: null,
      progress: 0,
      isComplete: false,
      isPlaying: false,
      currentTime: 0,
      agentContributions: new Map(),
      activeAgent: null,
    });
  },
  
  seekToProgress: (progress) => {
    const { streamPlayer } = get();
    if (!streamPlayer) return;
    
    streamPlayer.seekToProgress(progress);
    
    const chunks = streamPlayer.getChunksUpToProgress(progress);
    
    set({
      title: '',
      summary: '',
      sections: [],
      currentSectionIndex: -1,
      insights: [],
      charts: new Map(),
      chartProgress: new Map(),
      typingRecords: [],
      references: [],
      disclaimer: null,
      copyright: null,
      agentContributions: new Map(),
      progress: progress,
    });
    
    chunks.forEach(chunk => {
      get().processChunk(chunk);
    });
    
    set({ progress });
  },
}));
