/**
 * 动画动效模块索引
 * Animation Module Index
 * 
 * 导出所有动画相关组件和服务
 */

// 智能体动画组件
export { default as AgentAnimation } from './AgentAnimation';
export type { AgentStatus, AgentDepartment, AgentAnimationProps } from './AgentAnimation';

// 智能体点击交互组件
export { default as AgentClickable } from './AgentClickable';
export type { AgentClickableProps, AgentInfo, AgentTask } from './AgentClickable';

// 智能体工作流动画组件
export { default as AgentWorkflowAnimation } from './AgentWorkflowAnimation';
export type { AgentWorkflowAnimationProps, WorkflowData, WorkflowStep } from './AgentWorkflowAnimation';

// 记忆网络图组件
export { default as MemoryGraph } from './MemoryGraph';
export type { 
  MemoryGraphProps, 
  MemoryGraphData, 
  MemoryNode, 
  MemoryEdge, 
  MemoryType 
} from './MemoryGraph';

// 记忆检索粒子效果组件
export { default as MemoryRetrieveParticles, MemoryRetrieveEffect } from './MemoryRetrieveParticles';
export type { 
  MemoryRetrieveParticlesProps, 
  ParticleConfig, 
  RetrieveEvent 
} from './MemoryRetrieveParticles';

// 记忆气泡组件
export { default as MemoryBubble } from './MemoryBubble';
export type { MemoryBubbleProps, MemoryBubbleData } from './MemoryBubble';

// 平台启动动画组件
export { default as SplashAnimation } from './SplashAnimation';
export type { SplashAnimationProps } from './SplashAnimation';

// 数据流动画组件
export { default as DataFlowAnimation, DataFlowIndicator } from './DataFlowAnimation';
export type { 
  DataFlowAnimationProps, 
  DataFlowConfig 
} from './DataFlowAnimation';

// 页面过渡动画组件
export { 
  default as PageTransition,
  PageTransitionWrapper,
  SlideTransition,
  FadeTransition,
  ScaleTransition,
  ModalTransition,
  ListTransition,
} from './PageTransition';
export type { 
  PageTransitionProps, 
  TransitionType 
} from './PageTransition';

// 悬停提示组件
export { default as HoverTip, QuickTip, RichTip } from './HoverTip';
export type { HoverTipProps, TipPosition } from './HoverTip';

// 点击反馈组件
export { 
  default as ClickFeedback,
  ClickableButton,
  ClickableCard,
  ClickableIcon,
} from './ClickFeedback';
export type { 
  ClickFeedbackProps, 
  FeedbackType 
} from './ClickFeedback';

// 彩蛋触发器组件
export { default as EasterEggTrigger, useEasterEggTrigger } from './EasterEggTrigger';
export type { EasterEgg, EasterEggTriggerProps } from './EasterEggTrigger';

// 组件集合
export const AnimationComponents = {
  AgentAnimation: './AgentAnimation',
  AgentClickable: './AgentClickable',
  AgentWorkflowAnimation: './AgentWorkflowAnimation',
  MemoryGraph: './MemoryGraph',
  MemoryRetrieveParticles: './MemoryRetrieveParticles',
  MemoryBubble: './MemoryBubble',
  SplashAnimation: './SplashAnimation',
  DataFlowAnimation: './DataFlowAnimation',
  PageTransition: './PageTransition',
  HoverTip: './HoverTip',
  ClickFeedback: './ClickFeedback',
  EasterEggTrigger: './EasterEggTrigger',
};

// 组件数量统计
export const COMPONENT_COUNT = Object.keys(AnimationComponents).length;
