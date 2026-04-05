/**
 * 全局数据流动画组件
 * Data Flow Animation Component
 * 
 * 在后台运行时展示数据流粒子效果
 */

import React, { useRef, useEffect, useCallback, memo } from 'react';

export interface DataFlowConfig {
  particleCount: number;
  baseSpeed: number;
  color: string;
  qpsThreshold: number;
}

export interface DataFlowAnimationProps {
  qps?: number;
  enabled?: boolean;
  config?: Partial<DataFlowConfig>;
  className?: string;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  color: string;
  life: number;
  maxLife: number;
}

interface FlowPath {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  controlX: number;
  controlY: number;
}

const defaultConfig: DataFlowConfig = {
  particleCount: 50,
  baseSpeed: 2,
  color: '#3B82F6',
  qpsThreshold: 100,
};

const DataFlowAnimation: React.FC<DataFlowAnimationProps> = memo(({
  qps = 0,
  enabled = true,
  config: userConfig,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationRef = useRef<number | null>(null);
  const config = { ...defaultConfig, ...userConfig };

  const createParticle = useCallback((width: number, height: number): Particle => {
    const paths: FlowPath[] = [
      { startX: 0, startY: height * 0.3, endX: width, endY: height * 0.3, controlX: width * 0.5, controlY: height * 0.1 },
      { startX: 0, startY: height * 0.7, endX: width, endY: height * 0.7, controlX: width * 0.5, controlY: height * 0.9 },
      { startX: width * 0.3, startY: 0, endX: width * 0.3, endY: height, controlX: width * 0.1, controlY: height * 0.5 },
      { startX: width * 0.7, startY: 0, endX: width * 0.7, endY: height, controlX: width * 0.9, controlY: height * 0.5 },
    ];

    const path = paths[Math.floor(Math.random() * paths.length)];
    const t = Math.random();
    
    const x = Math.pow(1 - t, 2) * path.startX + 2 * (1 - t) * t * path.controlX + Math.pow(t, 2) * path.endX;
    const y = Math.pow(1 - t, 2) * path.startY + 2 * (1 - t) * t * path.controlY + Math.pow(t, 2) * path.endY;

    const speedMultiplier = qps > config.qpsThreshold ? 1 + (qps - config.qpsThreshold) / config.qpsThreshold : 1;
    const speed = config.baseSpeed * speedMultiplier * (0.5 + Math.random() * 0.5);

    return {
      x,
      y,
      vx: (Math.random() - 0.5) * speed,
      vy: (Math.random() - 0.5) * speed,
      size: 2 + Math.random() * 3,
      alpha: 0.3 + Math.random() * 0.4,
      color: config.color,
      life: 0,
      maxLife: 100 + Math.random() * 100,
    };
  }, [qps, config]);

  useEffect(() => {
    if (!enabled || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const targetCount = Math.floor(config.particleCount * (qps > config.qpsThreshold ? 1.5 : 1));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      while (particlesRef.current.length < targetCount) {
        particlesRef.current.push(createParticle(canvas.offsetWidth, canvas.offsetHeight));
      }

      const intensityMultiplier = qps > config.qpsThreshold ? 1.5 : 1;

      particlesRef.current = particlesRef.current.filter(particle => {
        particle.x += particle.vx * intensityMultiplier;
        particle.y += particle.vy * intensityMultiplier;
        particle.life++;

        if (
          particle.x < 0 ||
          particle.x > canvas.offsetWidth ||
          particle.y < 0 ||
          particle.y > canvas.offsetHeight ||
          particle.life >= particle.maxLife
        ) {
          return false;
        }

        const fadeIn = Math.min(particle.life / 20, 1);
        const fadeOut = Math.max(1 - (particle.life - particle.maxLife + 20) / 20, 0);
        const alpha = particle.alpha * fadeIn * fadeOut * intensityMultiplier;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = alpha;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size * 2, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = alpha * 0.3;
        ctx.fill();

        return true;
      });

      ctx.globalAlpha = 1;

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [enabled, qps, config, createParticle]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none ${className}`}
      style={{ width: '100%', height: '100%' }}
    />
  );
});

DataFlowAnimation.displayName = 'DataFlowAnimation';

export const DataFlowIndicator: React.FC<{
  qps: number;
  threshold?: number;
}> = memo(({ qps, threshold = 100 }) => {
  const status = qps > threshold * 1.5 ? 'critical' : qps > threshold ? 'warning' : 'normal';
  const statusConfig = {
    normal: { color: '#22C55E', label: '正常', icon: '✓' },
    warning: { color: '#EAB308', label: '较高', icon: '⚠' },
    critical: { color: '#EF4444', label: '过载', icon: '❗' },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-white/80 backdrop-blur-sm rounded-full shadow-sm">
      <span style={{ color: config.color }}>{config.icon}</span>
      <span className="text-xs text-gray-600">
        QPS: <span className="font-medium" style={{ color: config.color }}>{qps}</span>
      </span>
      <span className="text-xs text-gray-400">|</span>
      <span className="text-xs" style={{ color: config.color }}>
        {config.label}
      </span>
    </div>
  );
});

DataFlowIndicator.displayName = 'DataFlowIndicator';

export default DataFlowAnimation;
