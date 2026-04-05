import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { ParticleManager } from './ParticleManager';
import { SoundEffects } from './SoundEffects';

interface MemoryInjectionProps {
  sourcePosition: { x: number; y: number };
  targetPosition: { x: number; y: number };
  onComplete?: () => void;
  autoStart?: boolean;
}

export const MemoryInjection: React.FC<MemoryInjectionProps> = ({
  sourcePosition,
  targetPosition,
  onComplete,
  autoStart = false,
}) => {
  const [isInjecting, setIsInjecting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [particles, setParticles] = useState<Array<{ x: number; y: number; opacity: number }>>([]);

  useEffect(() => {
    if (autoStart) {
    startInjection();
  }
  }, [autoStart]);
  const startInjection = () => {
    setIsInjecting(true);
    setProgress(0);
    SoundEffects.playTone(800, 0.1, 'sine');
    
    const particleCount = 30;
    const newParticles = [];
    
    for (let i = 0; i < particleCount; i++) {
      newParticles.push({
        x: sourcePosition.x,
        y: sourcePosition.y,
        opacity: 1,
      });
    }
    setParticles(newParticles);
    
    const duration = 2000;
    const startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const currentProgress = Math.min((elapsed / duration) * 100, 100);
      
      setProgress(currentProgress);
      
      setParticles(prev => 
        prev.map(p => {
          const t = currentProgress / 100;
          return {
            x: sourcePosition.x + (targetPosition.x - sourcePosition.x) * t,
            y: sourcePosition.y + (targetPosition.y - sourcePosition.y) * t,
            opacity: 1 - t,
          };
        })
      );
      
      if (currentProgress >= 100) {
        setIsInjecting(false);
        SoundEffects.playTone(1200, 0.2, 'sine');
        onComplete?.();
        return;
      }
      
      requestAnimationFrame(animate);
    };
    
    animate();
  };
  
  return (
    <div style={styles.container}>
      <AnimatePresence>
        {isInjecting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.injectionOverlay}
          >
            <svg
              width="100%"
              height="100%"
              viewBox="0 0 100 100"
              style={styles.svg}
            >
              <defs>
                <linearGradient id="beamGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={theme.colors.primary.gold} />
                  <stop offset="100%" stopColor={theme.colors.primary.goldLight} />
                </linearGradient>
              </defs>
              
              <motion.line
                x1={sourcePosition.x}
                y1={sourcePosition.y}
                x2={targetPosition.x}
                y2={targetPosition.y}
                stroke="url(#beamGradient)"
                strokeWidth={3}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: progress / 100 }}
              />
              
              {particles.map((p, i) => (
                <motion.circle
                  key={i}
                  cx={p.x}
                  cy={p.y}
                  r={3}
                  fill={theme.colors.primary.gold}
                  opacity={p.opacity}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: i * 0.02 }}
                />
              ))}
            </svg>
            
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={styles.progressText}
            >
              注入中... {Math.round(progress)}%
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'relative',
    width: '100%',
    height: '100%',
  },
  injectionOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  svg: {
    overflow: 'visible',
  },
  progressText: {
    position: 'absolute',
    bottom: '-30px',
    left: '50%',
    transform: 'translateX(-50%)',
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.sm,
    whiteSpace: 'nowrap',
  },
};

