/**
 * 房都督AI - 智能体工作剧场组件库
 * 
 * 本模块包含三部曲演示系统的所有组件和工具
 * 
 * @example
 * ```tsx
 * import { TrilogyController, MemoryTimeline, KnowledgeGraph } from '@/components/trilogy';
 * 
 * function DemoPage() {
 *   return <TrilogyController />;
 * }
 * ```
 * 
 * @module trilogy
 */

// 核心配置
export { default as theme, theme } from './theme';
export type { Theme, ThemeColors, ThemeAnimation, ThemeParticles } from './types';

// 粒子系统
export { default as ParticleManager, ParticleManager } from './ParticleManager';
export type { Particle, ParticleConfig, ParticleType } from './types';

// 音效系统
export { default as SoundEffects, SoundEffects } from './SoundEffects';

// 性能监控
export { 
  default as PerformanceMonitor, 
  PerformanceMonitor,
  usePerformanceMonitor,
  useAdaptiveParticles,
  useProgressiveEnhancement,
} from './PerformanceMonitor';
export type { 
  PerformanceLevel, 
  PerformanceMetrics, 
  PerformanceMonitorState,
} from './types';

// 第二弹组件 - 海马体记忆
export { default as MemoryTimeline, MemoryTimeline } from './MemoryTimeline';
export { default as KnowledgeGraph, KnowledgeGraph } from './KnowledgeGraph';
export { default as MemoryMiningAnimation, MemoryMiningAnimation } from './MemoryMiningAnimation';
export { default as MemoryInjection, MemoryInjection } from './MemoryInjection';
export type { 
  Memory, 
  MemoryType,
  GraphNode, 
  GraphEdge, 
  KnowledgeGraphData,
  MiningResult,
  MemoryTimelineProps,
  KnowledgeGraphProps,
  MemoryMiningAnimationProps,
  MemoryInjectionProps,
} from './types';

// 第三弹组件 - 人格化交互与进化
export { default as PersonalitySelector, PersonalitySelector } from './PersonalitySelector';
export { default as PersonalityBubble, PersonalityBubble } from './PersonalityBubble';
export { default as EvolutionProgress, EvolutionProgress } from './EvolutionProgress';
export { default as EvolutionReward, EvolutionReward } from './EvolutionReward';
export type {
  PersonalityType,
  SceneType,
  Personality,
  PersonalityQuotes,
  PersonalityData,
  Ability,
  Milestone,
  EvolutionData,
  PersonalitySelectorProps,
  PersonalityBubbleProps,
  EvolutionProgressProps,
  EvolutionRewardProps,
} from './types';

// 控制器
export { default as TrilogyController, TrilogyController } from './TrilogyController';
export type { TrilogyPhase, PhaseConfig } from './types';
