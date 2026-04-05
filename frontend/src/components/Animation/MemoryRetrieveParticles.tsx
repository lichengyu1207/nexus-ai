/**
 * 记忆检索粒子效果组件
 * Memory Retrieve Particles Component
 * 
 * 展示记忆被激活的粒子效果
 */

import React, { useRef, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ParticleConfig {
  count: number;
  speed: number;
  color: string;
  size: number;
  lifetime: number;
}

export interface RetrieveEvent {
  id: string;
  sourcePosition: { x: number; y: number };
  targetPositions: Array<{ x: number; y: number; weight: number }>;
  config?: Partial<ParticleConfig>;
}

export interface MemoryRetrieveParticlesProps {
  events: RetrieveEvent[];
  enabled?: boolean;
  performanceMode?: 'high' | 'balanced' | 'low';
  onParticleComplete?: (eventId: string) => void;
  className?: string;
}

interface Particle {
  id: string;
  eventId: string;
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  vx: number;
  vy: number;
  color: string;
  size: number;
  alpha: number;
  life: number;
  maxLife: number;
}

const defaultConfig: ParticleConfig = {
  count: 20,
  speed: 3,
  color: '#3B82F6',
  size: 4,
  lifetime: 60,
};

const performanceConfigs = {
  high: { countMultiplier: 0.3, fps: 30 },
  balanced: { countMultiplier: 0.6, fps: 45 },
  low: { countMultiplier: 1, fps: 60 },
};

const MemoryRetrieveParticles: React.FC<MemoryRetrieveParticlesProps> = memo(({
  events,
  enabled = true,
  performanceMode = 'balanced',
  onParticleComplete,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationRef = useRef<number | null>(null);
  const perfConfig = performanceConfigs[performanceMode];

  const createParticles = useCallback((event: RetrieveEvent) => {
    const config = { ...defaultConfig, ...event.config };
    const count = Math.floor(config.count * perfConfig.countMultiplier);
    const particles: Particle[] = [];

    event.targetPositions.forEach(target => {
      const particleCount = Math.floor(count * target.weight);
      
      for (let i = 0; i < particleCount; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = config.speed * (0.5 + Math.random() * 0.5);
        const dx = target.x - event.sourcePosition.x;
        const dy = target.y - event.sourcePosition.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        particles.push({
          id: `${event.id}-${target.x}-${target.y}-${i}`,
          eventId: event.id,
          x: event.sourcePosition.x,
          y: event.sourcePosition.y,
          targetX: target.x,
          targetY: target.y,
          vx: (dx / dist) * speed,
          vy: (dy / dist) * speed,
          color: config.color,
          size: config.size * (0.5 + Math.random() * 0.5),
          alpha: 1,
          life: 0,
          maxLife: config.lifetime * (0.8 + Math.random() * 0.4),
        });
      }
    });

    return particles;
  }, [perfConfig.countMultiplier]);

  useEffect(() => {
    if (!enabled) return;

    events.forEach(event => {
      const newParticles = createParticles(event);
      particlesRef.current = [...particlesRef.current, ...newParticles];
    });
  }, [events, enabled, createParticles]);

  useEffect(() => {
    if (!enabled || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let lastTime = performance.now();
    const frameInterval = 1000 / perfConfig.fps;

    const animate = (currentTime: number) => {
      const deltaTime = currentTime - lastTime;

      if (deltaTime >= frameInterval) {
        lastTime = currentTime - (deltaTime % frameInterval);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const completedEvents = new Set<string>();

        particlesRef.current = particlesRef.current.filter(particle => {
          particle.x += particle.vx;
          particle.y += particle.vy;
          particle.life++;

          const dx = particle.targetX - particle.x;
          const dy = particle.targetY - particle.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 10 || particle.life >= particle.maxLife) {
            completedEvents.add(particle.eventId);
            return false;
          }

          particle.vx += (dx / dist) * 0.1;
          particle.vy += (dy / dist) * 0.1;

          const progress = particle.life / particle.maxLife;
          particle.alpha = 1 - progress * 0.5;

          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fillStyle = particle.color;
          ctx.globalAlpha = particle.alpha;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size * 2, 0, Math.PI * 2);
          ctx.fillStyle = particle.color;
          ctx.globalAlpha = particle.alpha * 0.3;
          ctx.fill();

          return true;
        });

        ctx.globalAlpha = 1;

        completedEvents.forEach(eventId => {
          onParticleComplete?.(eventId);
        });
      }

      if (particlesRef.current.length > 0) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    if (particlesRef.current.length > 0) {
      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [enabled, perfConfig.fps, onParticleComplete]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none ${className}`}
      style={{ width: '100%', height: '100%' }}
    />
  );
});

MemoryRetrieveParticles.displayName = 'MemoryRetrieveParticles';

export const MemoryRetrieveEffect: React.FC<{
  sourcePosition: { x: number; y: number };
  targetPositions: Array<{ x: number; y: number; weight: number }>;
  onComplete?: () => void;
  color?: string;
}> = memo(({ sourcePosition, targetPositions, onComplete, color = '#3B82F6' }) => {
  const [showEffect, setShowEffect] = React.useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowEffect(false);
      onComplete?.();
    }, 2000);

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <AnimatePresence>
      {showEffect && (
        <motion.div className="absolute inset-0 pointer-events-none">
          <svg className="w-full h-full">
            <defs>
              <linearGradient id="particleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={color} stopOpacity="0" />
                <stop offset="50%" stopColor={color} stopOpacity="1" />
                <stop offset="100%" stopColor={color} stopOpacity="0" />
              </linearGradient>
            </defs>
            
            {targetPositions.map((target, index) => (
              <motion.line
                key={index}
                x1={sourcePosition.x}
                y1={sourcePosition.y}
                x2={target.x}
                y2={target.y}
                stroke="url(#particleGradient)"
                strokeWidth={2 + target.weight * 3}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: [0, 1, 0] }}
                transition={{ duration: 1.5, delay: index * 0.1 }}
              />
            ))}
            
            {targetPositions.map((target, index) => (
              <motion.circle
                key={`pulse-${index}`}
                cx={target.x}
                cy={target.y}
                r={20}
                fill="none"
                stroke={color}
                strokeWidth={2}
                initial={{ scale: 0, opacity: 1 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{ duration: 0.8, delay: 0.3 + index * 0.1 }}
              />
            ))}
          </svg>
        </motion.div>
      )}
    </AnimatePresence>
  );
});

MemoryRetrieveEffect.displayName = 'MemoryRetrieveEffect';

export default MemoryRetrieveParticles;
