/**
 * 房都督AI - 智能体工作剧场类型定义
 * 
 * 本文件包含三部曲演示系统所需的所有TypeScript类型定义
 * @module trilogy/types
 */

// ==================== 粒子系统类型 ====================

export type ParticleType = 'lightBeam' | 'probe' | 'memory' | 'evolution';

export interface ParticleConfig {
  color: string;
  size: { min: number; max: number };
  speed: { min: number; max: number };
  opacity: { min: number; max: number };
  lifetime: { min: number; max: number };
}

export interface Particle {
  id: string;
  type: ParticleType;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  opacity: number;
  lifetime: number;
  age: number;
  targetX?: number;
  targetY?: number;
}

// ==================== 记忆系统类型 ====================

export type MemoryType = 'userMemory' | 'businessData' | 'externalKnowledge';

export interface Memory {
  id: string;
  date: string;
  summary: string;
  agentId: string;
  graphNodeId: string;
  importance: number;
  type: MemoryType;
  details: Record<string, unknown>;
}

export interface GraphNode {
  id: string;
  label: string;
  type: MemoryType;
  importance: number;
  summary: string;
  position: { x: number; y: number };
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  strength: number;
  label: string;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ==================== 人格系统类型 ====================

export type PersonalityType = 'zhouyu' | 'luxun';
export type SceneType = 'taskStart' | 'taskComplete' | 'difficulty' | 'evolutionComplete' | 'memoryRecall' | 'miningSuccess';

export interface PersonalityQuotes {
  intro: string;
  taskStart: string[];
  taskComplete: string[];
  difficulty: string[];
  evolutionComplete: string[];
  memoryRecall: string[];
  miningSuccess: string[];
}

export interface Personality {
  name: string;
  title: string;
  description: string;
  quotes: PersonalityQuotes;
}

export interface PersonalityData {
  zhouyu: Personality;
  luxun: Personality;
}

// ==================== 进化系统类型 ====================

export interface Ability {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  requiredProgress: number;
  abilities: Ability[];
}

export interface EvolutionData {
  milestones: Milestone[];
  progressSources: {
    memoryInjection: number;
    userInteraction: number;
    taskCompletion: number;
    miningSuccess: number;
  };
}

// ==================== 挖掘系统类型 ====================

export interface MiningResult {
  id: string;
  title: string;
  description: string;
  relatedNodes: string[];
}

// ==================== 三部曲控制器类型 ====================

export type TrilogyPhase = 'intro' | 'episode1' | 'episode2' | 'episode3' | 'complete';

export interface PhaseConfig {
  id: TrilogyPhase;
  title: string;
  description: string;
  duration?: number;
}

// ==================== 性能监控类型 ====================

export type PerformanceLevel = 'high' | 'medium' | 'low';

export interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  particleCount: number;
  memoryUsage?: number;
}

export interface PerformanceMonitorState {
  level: PerformanceLevel;
  metrics: PerformanceMetrics;
  isWebGLSupported: boolean;
  isCanvasSupported: boolean;
  shouldReduceMotion: boolean;
}

// ==================== 组件Props类型 ====================

export interface MemoryTimelineProps {
  onMemorySelect?: (memory: Memory) => void;
  isActive?: boolean;
}

export interface KnowledgeGraphProps {
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  isMining?: boolean;
  highlightedNodes?: string[];
}

export interface MemoryMiningAnimationProps {
  onStart?: () => void;
  onComplete?: (result: MiningResult) => void;
  autoStart?: boolean;
  duration?: number;
}

export interface MemoryInjectionProps {
  sourcePosition: { x: number; y: number };
  targetPosition: { x: number; y: number };
  onComplete?: () => void;
  autoStart?: boolean;
}

export interface PersonalitySelectorProps {
  onSelect?: (personality: PersonalityType) => void;
  initialPersonality?: PersonalityType;
}

export interface PersonalityBubbleProps {
  personality: PersonalityType;
  scene: SceneType;
  targetAgent?: string;
  onComplete?: () => void;
  autoShow?: boolean;
}

export interface EvolutionProgressProps {
  currentProgress?: number;
  onMilestoneReach?: (milestone: Milestone) => void;
  onEvolutionComplete?: () => void;
  showDetails?: boolean;
}

export interface EvolutionRewardProps {
  milestoneId?: string;
  onComplete?: () => void;
  autoShow?: boolean;
}

// ==================== 主题类型 ====================

export interface ThemeColors {
  primary: {
    gold: string;
    goldLight: string;
    goldDark: string;
    deepBlue: string;
    deepBlueLight: string;
    deepBlueDark: string;
  };
  agents: {
    libu: string;
    gongbu: string;
    hubu: string;
    bingbu: string;
    libu2: string;
    xingbu: string;
  };
  memory: {
    userMemory: string;
    businessData: string;
    externalKnowledge: string;
  };
  evolution: {
    stage1: string;
    stage2: string;
    stage3: string;
    complete: string;
  };
  personality: {
    zhouyu: {
      primary: string;
      secondary: string;
      glow: string;
    };
    luxun: {
      primary: string;
      secondary: string;
      glow: string;
    };
  };
}

export interface ThemeAnimation {
  duration: {
    fast: number;
    standard: number;
    slow: number;
    verySlow: number;
  };
  easing: {
    easeInOut: string;
    easeOut: string;
    easeIn: string;
    spring: string;
  };
}

export interface ThemeParticles {
  types: Record<ParticleType, ParticleConfig>;
  maxCount: number;
  performanceThreshold: number;
}

export interface Theme {
  colors: ThemeColors;
  animation: ThemeAnimation;
  particles: ThemeParticles;
  typography: {
    fontFamily: {
      primary: string;
      display: string;
    };
    fontSize: Record<string, string>;
  };
  borderRadius: Record<string, string>;
  shadows: Record<string, string | Record<string, string>>;
  zIndex: Record<string, number>;
}
