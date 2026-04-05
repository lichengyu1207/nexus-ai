import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { ParticleManager } from './ParticleManager';
import { SoundEffects } from './SoundEffects';

interface MiningResult {
  id: string;
  title: string;
  description: string;
  relatedNodes: string[];
}

interface MemoryMiningAnimationProps {
  onStart?: () => void;
  onComplete?: (result: MiningResult) => void;
  autoStart?: boolean;
  duration?: number;
}

const sampleResults: MiningResult[] = [
  {
    id: 'result_1',
    title: '学区房需求与地铁规划高度相关',
    description: '通过分析用户历史查询，发现学区房偏好与地铁规划信息有85%的关联度',
    relatedNodes: ['node_education', 'node_metro'],
  },
  {
    id: 'result_2',
    title: '深圳投资热点区域预测',
    description: '基于市场数据和用户偏好，预测南山科技园周边为下一投资热点',
    relatedNodes: ['node_shenzhen', 'node_market'],
  },
  {
    id: 'result_3',
    title: '信用评分与购房能力关联',
    description: '发现信用评级优秀的用户更倾向于选择学区房',
    relatedNodes: ['node_credit', 'node_education'],
  },
];

export const MemoryMiningAnimation: React.FC<MemoryMiningAnimationProps> = ({
  onStart,
  onComplete,
  autoStart = false,
  duration = 10000,
}) => {
  const [isMining, setIsMining] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<'idle' | 'scanning' | 'analyzing' | 'discovering'>('idle');
  const [discoveredConnections, setDiscoveredConnections] = useState<string[]>([]);
  const [finalResult, setFinalResult] = useState<MiningResult | null>(null);
  const [showResult, setShowResult] = useState(false);

  const startMining = useCallback(() => {
    setIsMining(true);
    setProgress(0);
    setPhase('scanning');
    setDiscoveredConnections([]);
    setFinalResult(null);
    setShowResult(false);
    onStart?.();
    SoundEffects.playTone(440, 0.2, 'sine');
  }, [onStart]);

  useEffect(() => {
    if (autoStart && !isMining) {
      startMining();
    }
  }, [autoStart, isMining, startMining]);

  useEffect(() => {
    if (!isMining) return;

    const interval = setInterval(() => {
      setProgress(prev => {
        const next = prev + (100 / (duration / 100));
        
        if (next >= 25 && next < 50) {
          setPhase('analyzing');
        } else if (next >= 50 && next < 75) {
          setPhase('discovering');
          if (Math.random() > 0.7) {
            const connectionId = `conn_${Date.now()}`;
            setDiscoveredConnections(prev => [...prev, connectionId]);
            SoundEffects.playMiningSuccess();
            ParticleManager.createBurst('probe', 300, 200, 8);
          }
        } else if (next >= 100) {
          clearInterval(interval);
          setIsMining(false);
          setPhase('idle');
          
          const result = sampleResults[Math.floor(Math.random() * sampleResults.length)];
          setFinalResult(result);
          setShowResult(true);
          SoundEffects.playEvolutionComplete();
          onComplete?.(result);
          
          return 100;
        }
        
        return next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isMining, duration, onComplete]);

  const phaseLabels = {
    idle: '准备就绪',
    scanning: '正在扫描记忆网络...',
    analyzing: '分析关联模式...',
    discovering: '发现新关联！',
  };

  const phaseIcons = {
    idle: '🔍',
    scanning: '📡',
    analyzing: '🧠',
    discovering: '💡',
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>记忆挖掘系统</h3>
        <span style={styles.subtitle}>从记忆网络中发现隐藏洞察</span>
      </div>

      <div style={styles.visualization}>
        <svg width="100%" height="200" viewBox="0 0 400 200">
          <defs>
            <radialGradient id="nodeGradient">
              <stop offset="0%" stopColor={theme.colors.primary.gold} />
              <stop offset="100%" stopColor={theme.colors.primary.goldDark} />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          
          {[1, 2, 3, 4, 5, 6].map((_, i) => (
            <motion.circle
              key={`node-${i}`}
              cx={50 + (i % 3) * 150}
              cy={50 + Math.floor(i / 3) * 100}
              r={isMining ? 15 : 12}
              fill="url(#nodeGradient)"
              filter={isMining ? 'url(#glow)' : undefined}
              animate={isMining ? {
                scale: [1, 1.2, 1],
                opacity: [0.7, 1, 0.7],
              } : {}}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
          
          {isMining && (
            <motion.circle
              cx={200}
              cy={100}
              r={5}
              fill={theme.colors.memory.userMemory}
              animate={{
                cx: [50, 200, 350, 200, 50],
                cy: [50, 150, 50, 150, 50],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
              }}
            />
          )}
          
          {discoveredConnections.map((conn, i) => (
            <motion.line
              key={conn}
              x1={50 + (i % 3) * 150}
              y1={50 + Math.floor(i / 3) * 100}
              x2={200 + (i % 2) * 150}
              y2={100 + (i % 2) * 50}
              stroke={theme.colors.primary.gold}
              strokeWidth={2}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 0.8 }}
              transition={{ duration: 0.5 }}
            />
          ))}
        </svg>
      </div>

      <div style={styles.progressSection}>
        <div style={styles.phaseIndicator}>
          <span style={styles.phaseIcon}>{phaseIcons[phase]}</span>
          <span style={styles.phaseLabel}>{phaseLabels[phase]}</span>
        </div>
        
        <div style={styles.progressBar}>
          <motion.div
            style={styles.progressFill}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
        
        <div style={styles.progressText}>{Math.round(progress)}%</div>
      </div>

      <div style={styles.stats}>
        <div style={styles.statItem}>
          <span style={styles.statValue}>{discoveredConnections.length}</span>
          <span style={styles.statLabel}>发现关联</span>
        </div>
        <div style={styles.statItem}>
          <span style={styles.statValue}>{Math.floor(progress / 10)}</span>
          <span style={styles.statLabel}>分析节点</span>
        </div>
      </div>

      <AnimatePresence>
        {showResult && finalResult && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.9 }}
            style={styles.resultPanel}
          >
            <div style={styles.resultHeader}>
              <span style={styles.resultIcon}>💡</span>
              <span style={styles.resultTitle}>发现新洞察！</span>
            </div>
            <h4 style={styles.resultName}>{finalResult.title}</h4>
            <p style={styles.resultDescription}>{finalResult.description}</p>
            <div style={styles.resultNodes}>
              {finalResult.relatedNodes.map(node => (
                <span key={node} style={styles.resultNode}>{node}</span>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!isMining && !showResult && (
        <motion.button
          style={styles.startButton}
          onClick={startMining}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          开始挖掘
        </motion.button>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    padding: '24px',
    background: 'rgba(10, 35, 66, 0.9)',
    borderRadius: theme.borderRadius.xl,
    border: `1px solid ${theme.colors.primary.gold}40`,
  },
  header: {
    textAlign: 'center',
    marginBottom: '20px',
  },
  title: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.xl,
    margin: 0,
    fontFamily: theme.typography.fontFamily.display,
  },
  subtitle: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    opacity: 0.7,
  },
  visualization: {
    marginBottom: '20px',
  },
  progressSection: {
    marginBottom: '16px',
  },
  phaseIndicator: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  phaseIcon: {
    fontSize: '20px',
  },
  phaseLabel: {
    color: '#fff',
    fontSize: theme.typography.fontSize.sm,
  },
  progressBar: {
    width: '100%',
    height: '8px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: theme.borderRadius.full,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: `linear-gradient(90deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldLight})`,
    borderRadius: theme.borderRadius.full,
  },
  progressText: {
    textAlign: 'center',
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.sm,
    marginTop: '4px',
  },
  stats: {
    display: 'flex',
    justifyContent: 'center',
    gap: '40px',
    marginBottom: '20px',
  },
  statItem: {
    textAlign: 'center',
  },
  statValue: {
    display: 'block',
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize['2xl'],
    fontWeight: 'bold',
  },
  statLabel: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.xs,
    opacity: 0.7,
  },
  resultPanel: {
    padding: '16px',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}20, ${theme.colors.primary.goldLight}10)`,
    borderRadius: theme.borderRadius.lg,
    border: `1px solid ${theme.colors.primary.gold}60`,
    marginBottom: '16px',
  },
  resultHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  resultIcon: {
    fontSize: '24px',
  },
  resultTitle: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.lg,
    fontWeight: 'bold',
  },
  resultName: {
    color: '#fff',
    fontSize: theme.typography.fontSize.base,
    margin: '0 0 8px 0',
  },
  resultDescription: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    margin: 0,
    lineHeight: 1.6,
  },
  resultNodes: {
    display: 'flex',
    gap: '8px',
    marginTop: '12px',
  },
  resultNode: {
    padding: '4px 8px',
    background: 'rgba(212, 175, 55, 0.2)',
    borderRadius: theme.borderRadius.sm,
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.xs,
  },
  startButton: {
    width: '100%',
    padding: '12px 24px',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldDark})`,
    color: theme.colors.primary.deepBlue,
    fontSize: theme.typography.fontSize.base,
    fontWeight: 'bold',
    border: 'none',
    borderRadius: theme.borderRadius.lg,
    cursor: 'pointer',
    transition: `all ${theme.animation.duration.standard}s`,
  },
};

export default MemoryMiningAnimation;
