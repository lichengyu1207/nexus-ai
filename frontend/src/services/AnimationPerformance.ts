/**
 * 动画性能优化模块
 * Animation Performance Module
 * 
 * 监控和优化动画性能
 */

import { create } from 'zustand';

export type PerformanceMode = 'high' | 'balanced' | 'low';

export interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  memoryUsage: number;
  animationCount: number;
  particleCount: number;
}

export interface PerformanceConfig {
  mode: PerformanceMode;
  maxFPS: number;
  particleMultiplier: number;
  animationQuality: 'full' | 'reduced' | 'minimal';
  enableParticles: boolean;
  enableTransitions: boolean;
  enableBlur: boolean;
  enableShadows: boolean;
}

const modeConfigs: Record<PerformanceMode, PerformanceConfig> = {
  high: {
    mode: 'high',
    maxFPS: 30,
    particleMultiplier: 0.3,
    animationQuality: 'minimal',
    enableParticles: false,
    enableTransitions: true,
    enableBlur: false,
    enableShadows: false,
  },
  balanced: {
    mode: 'balanced',
    maxFPS: 45,
    particleMultiplier: 0.6,
    animationQuality: 'reduced',
    enableParticles: true,
    enableTransitions: true,
    enableBlur: false,
    enableShadows: true,
  },
  low: {
    mode: 'low',
    maxFPS: 60,
    particleMultiplier: 1,
    animationQuality: 'full',
    enableParticles: true,
    enableTransitions: true,
    enableBlur: true,
    enableShadows: true,
  },
};

export interface PerformanceState {
  metrics: PerformanceMetrics;
  config: PerformanceConfig;
  isMobile: boolean;
  autoAdjustEnabled: boolean;
  
  updateMetrics: (metrics: Partial<PerformanceMetrics>) => void;
  setMode: (mode: PerformanceMode) => void;
  setAutoAdjust: (enabled: boolean) => void;
  adjustForPerformance: () => void;
}

const isMobileDevice = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

export const usePerformanceStore = create<PerformanceState>((set, get) => ({
  metrics: {
    fps: 60,
    frameTime: 16.67,
    memoryUsage: 0,
    animationCount: 0,
    particleCount: 0,
  },
  config: isMobileDevice() ? modeConfigs.high : modeConfigs.balanced,
  isMobile: isMobileDevice(),
  autoAdjustEnabled: true,

  updateMetrics: (newMetrics) =>
    set((state) => ({
      metrics: { ...state.metrics, ...newMetrics },
    })),

  setMode: (mode) =>
    set({ config: modeConfigs[mode] }),

  setAutoAdjust: (enabled) =>
    set({ autoAdjustEnabled: enabled }),

  adjustForPerformance: () => {
    const { metrics, autoAdjustEnabled } = get();
    
    if (!autoAdjustEnabled) return;

    if (metrics.fps < 30) {
      set({ config: modeConfigs.high });
    } else if (metrics.fps < 45) {
      set({ config: modeConfigs.balanced });
    } else {
      set({ config: modeConfigs.low });
    }
  },
}));

export class AnimationPerformanceMonitor {
  private frameCount = 0;
  private lastTime = performance.now();
  private fpsHistory: number[] = [];
  private readonly historySize = 60;
  private animationFrameId: number | null = null;
  private isRunning = false;

  start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.lastTime = performance.now();
    this.measure();
  }

  stop(): void {
    this.isRunning = false;
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  private measure = (): void => {
    if (!this.isRunning) return;

    const now = performance.now();
    const delta = now - this.lastTime;
    
    this.frameCount++;

    if (delta >= 1000) {
      const fps = Math.round((this.frameCount * 1000) / delta);
      
      this.fpsHistory.push(fps);
      if (this.fpsHistory.length > this.historySize) {
        this.fpsHistory.shift();
      }

      const avgFps = this.getAverageFPS();
      const frameTime = 1000 / avgFps;

      usePerformanceStore.getState().updateMetrics({
        fps: avgFps,
        frameTime,
      });

      usePerformanceStore.getState().adjustForPerformance();

      this.frameCount = 0;
      this.lastTime = now;
    }

    this.animationFrameId = requestAnimationFrame(this.measure);
  };

  getAverageFPS(): number {
    if (this.fpsHistory.length === 0) return 60;
    return Math.round(
      this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length
    );
  }

  getCurrentFPS(): number {
    return this.fpsHistory[this.fpsHistory.length - 1] || 60;
  }

  getFPSHistory(): number[] {
    return [...this.fpsHistory];
  }
}

let monitorInstance: AnimationPerformanceMonitor | null = null;

export const getPerformanceMonitor = (): AnimationPerformanceMonitor => {
  if (!monitorInstance) {
    monitorInstance = new AnimationPerformanceMonitor();
  }
  return monitorInstance;
};

export const usePerformanceConfig = (): PerformanceConfig => {
  return usePerformanceStore((state) => state.config);
};

export const usePerformanceMetrics = (): PerformanceMetrics => {
  return usePerformanceStore((state) => state.metrics);
};

export const useShouldReduceMotion = (): boolean => {
  const config = usePerformanceStore((state) => state.config);
  const isMobile = usePerformanceStore((state) => state.isMobile);
  
  return isMobile || config.mode === 'high' || 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

export const useParticleMultiplier = (): number => {
  return usePerformanceStore((state) => state.config.particleMultiplier);
};

export const reportAnimationStart = (): void => {
  const state = usePerformanceStore.getState();
  state.updateMetrics({
    animationCount: state.metrics.animationCount + 1,
  });
};

export const reportAnimationEnd = (): void => {
  const state = usePerformanceStore.getState();
  state.updateMetrics({
    animationCount: Math.max(0, state.metrics.animationCount - 1),
  });
};

export const reportParticleCount = (count: number): void => {
  usePerformanceStore.getState().updateMetrics({
    particleCount: count,
  });
};

export default AnimationPerformanceMonitor;
