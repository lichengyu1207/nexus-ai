import { useState, useEffect, useCallback, useRef } from 'react';
import { theme } from './theme';

type PerformanceLevel = 'high' | 'medium' | 'low';

interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  particleCount: number;
  memoryUsage?: number;
}

interface PerformanceMonitor {
  level: PerformanceLevel;
  metrics: PerformanceMetrics;
  isWebGLSupported: boolean;
  isCanvasSupported: boolean;
  shouldReduceMotion: boolean;
}

const PERFORMANCE_THRESHOLDS = {
  high: { minFps: 55, maxFrameTime: 18 },
  medium: { minFps: 30, maxFrameTime: 33 },
  low: { minFps: 0, maxFrameTime: Infinity },
};

class PerformanceMonitorClass {
  private level: PerformanceLevel = 'high';
  private metrics: PerformanceMetrics = {
    fps: 60,
    frameTime: 16.67,
    particleCount: 0,
  };
  private frameCount = 0;
  private lastTime = performance.now();
  private callbacks: Set<(monitor: PerformanceMonitor) => void> = new Set();
  private animationId: number | null = null;
  private warningCount = 0;

  isWebGLSupported(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!(
        canvas.getContext('webgl') || 
        canvas.getContext('experimental-webgl')
      );
    } catch {
      return false;
    }
  }

  isCanvasSupported(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!canvas.getContext('2d');
    } catch {
      return false;
    }
  }

  shouldReduceMotion(): boolean {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  start(): void {
    if (this.animationId) return;
    
    this.lastTime = performance.now();
    this.frameCount = 0;
    this.measure();
  }

  stop(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  private measure = (): void => {
    const now = performance.now();
    this.frameCount++;

    const elapsed = now - this.lastTime;
    
    if (elapsed >= 1000) {
      this.metrics.fps = Math.round((this.frameCount * 1000) / elapsed);
      this.metrics.frameTime = elapsed / this.frameCount;
      
      this.frameCount = 0;
      this.lastTime = now;
      
      this.evaluatePerformance();
      this.notifyCallbacks();
    }

    this.animationId = requestAnimationFrame(this.measure);
  };

  private evaluatePerformance(): void {
    const { fps, frameTime } = this.metrics;
    
    if (fps >= PERFORMANCE_THRESHOLDS.high.minFps && 
        frameTime <= PERFORMANCE_THRESHOLDS.high.maxFrameTime) {
      if (this.level !== 'high') {
        this.level = 'high';
        console.log('[性能] 高性能模式');
      }
    } else if (fps >= PERFORMANCE_THRESHOLDS.medium.minFps && 
               frameTime <= PERFORMANCE_THRESHOLDS.medium.maxFrameTime) {
      if (this.level !== 'medium') {
        this.level = 'medium';
        this.warningCount++;
        console.warn('[性能] 中等性能模式 - 降低粒子数量');
      }
    } else {
      if (this.level !== 'low') {
        this.level = 'low';
        this.warningCount++;
        console.warn('[性能] 低性能模式 - 禁用复杂动画');
      }
    }

    if (this.metrics.frameTime > theme.particles.performanceThreshold) {
      console.warn(
        `[性能警告] 帧时间过长: ${this.metrics.frameTime.toFixed(2)}ms，` +
        `建议: 减少粒子数量、关闭阴影效果`
      );
    }
  }

  setParticleCount(count: number): void {
    this.metrics.particleCount = count;
  }

  subscribe(callback: (monitor: PerformanceMonitor) => void): () => void {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }

  private notifyCallbacks(): void {
    const monitor: PerformanceMonitor = {
      level: this.level,
      metrics: { ...this.metrics },
      isWebGLSupported: this.isWebGLSupported(),
      isCanvasSupported: this.isCanvasSupported(),
      shouldReduceMotion: this.shouldReduceMotion(),
    };
    
    this.callbacks.forEach(cb => cb(monitor));
  }

  getLevel(): PerformanceLevel {
    return this.level;
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  getMonitor(): PerformanceMonitor {
    return {
      level: this.level,
      metrics: { ...this.metrics },
      isWebGLSupported: this.isWebGLSupported(),
      isCanvasSupported: this.isCanvasSupported(),
      shouldReduceMotion: this.shouldReduceMotion(),
    };
  }
}

export const performanceMonitor = new PerformanceMonitorClass();

export const usePerformanceMonitor = (): PerformanceMonitor => {
  const [monitor, setMonitor] = useState<PerformanceMonitor>(() => 
    performanceMonitor.getMonitor()
  );

  useEffect(() => {
    performanceMonitor.start();
    const unsubscribe = performanceMonitor.subscribe(setMonitor);
    
    return () => {
      unsubscribe();
      performanceMonitor.stop();
    };
  }, []);

  return monitor;
};

export const useAdaptiveParticles = (
  baseCount: number
): { particleCount: number; isEnabled: boolean } => {
  const monitor = usePerformanceMonitor();
  
  const getAdaptiveCount = useCallback((): number => {
    if (monitor.shouldReduceMotion) return 0;
    
    switch (monitor.level) {
      case 'high':
        return baseCount;
      case 'medium':
        return Math.floor(baseCount * 0.6);
      case 'low':
        return Math.floor(baseCount * 0.3);
      default:
        return baseCount;
    }
  }, [baseCount, monitor.level, monitor.shouldReduceMotion]);

  return {
    particleCount: getAdaptiveCount(),
    isEnabled: !monitor.shouldReduceMotion && monitor.level !== 'low',
  };
};

export const useProgressiveEnhancement = (): {
  canUseParticles: boolean;
  canUseWebGL: boolean;
  canUseCanvas: boolean;
  shouldReduceMotion: boolean;
  performanceLevel: PerformanceLevel;
} => {
  const monitor = usePerformanceMonitor();

  return {
    canUseParticles: monitor.isCanvasSupported && !monitor.shouldReduceMotion,
    canUseWebGL: monitor.isWebGLSupported && !monitor.shouldReduceMotion,
    canUseCanvas: monitor.isCanvasSupported,
    shouldReduceMotion: monitor.shouldReduceMotion,
    performanceLevel: monitor.level,
  };
};

export default performanceMonitor;
