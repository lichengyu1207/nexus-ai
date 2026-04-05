import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { ParticleManager } from './ParticleManager';
import { SoundEffects } from './SoundEffects';
import memoryData from '../../data/memoryData.json';

interface Memory {
  id: string;
  date: string;
  summary: string;
  agentId: string;
  graphNodeId: string;
  importance: number;
  type: 'userMemory' | 'businessData' | 'externalKnowledge';
  details: Record<string, unknown>;
}

interface MemoryTimelineProps {
  onMemorySelect?: (memory: Memory) => void;
  isActive?: boolean;
}

const typeColors = {
  userMemory: theme.colors.memory.userMemory,
  businessData: theme.colors.memory.businessData,
  externalKnowledge: theme.colors.memory.externalKnowledge,
};

const agentNames: Record<string, string> = {
  libu: '礼部',
  gongbu: '工部',
  hubu: '户部',
  bingbu: '兵部',
  xingbu: '刑部',
  libu2: '吏部',
};

export const MemoryTimeline: React.FC<MemoryTimelineProps> = ({
  onMemorySelect,
  isActive = false,
}) => {
  const [memories] = useState<Memory[]>(memoryData.memories as Memory[]);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [isRecalling, setIsRecalling] = useState(false);
  const [visibleNodes, setVisibleNodes] = useState<number>(0);

  useEffect(() => {
    if (isActive && visibleNodes < memories.length) {
      const timer = setInterval(() => {
        setVisibleNodes(prev => Math.min(prev + 1, memories.length));
      }, 200);
      return () => clearInterval(timer);
    }
  }, [isActive, visibleNodes, memories.length]);

  const handleMemoryClick = useCallback((memory: Memory) => {
    if (isRecalling) return;
    
    setSelectedMemory(memory);
    setIsRecalling(true);
    SoundEffects.playMemoryRecall();
    
    ParticleManager.createBurst('memory', 100, 50, 20);
    
    setTimeout(() => {
      setIsRecalling(false);
      onMemorySelect?.(memory);
    }, 2000);
  }, [isRecalling, onMemorySelect]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}月${date.getDate()}日`;
  };

  return (
    <div className="memory-timeline-container" style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>记忆时间轴</h3>
        <span style={styles.subtitle}>点击节点唤醒记忆</span>
      </div>
      
      <div style={styles.timeline}>
        {memories.slice(0, visibleNodes).map((memory, index) => (
          <motion.div
            key={memory.id}
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{
              duration: theme.animation.duration.standard,
              delay: index * 0.1,
            }}
            style={{
              ...styles.node,
              borderLeftColor: typeColors[memory.type],
            }}
            onClick={() => handleMemoryClick(memory)}
          >
            <div style={styles.date}>{formatDate(memory.date)}</div>
            <div style={styles.content}>
              <div style={styles.summary}>{memory.summary}</div>
              <div style={styles.meta}>
                <span style={styles.agent}>
                  {agentNames[memory.agentId] || memory.agentId}
                </span>
                <span style={styles.importance}>
                  重要度: {Math.round(memory.importance * 100)}%
                </span>
              </div>
            </div>
            
            <AnimatePresence>
              {selectedMemory?.id === memory.id && isRecalling && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  style={styles.recallOverlay}
                >
                  <div style={styles.recallText}>记忆回放中...</div>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={styles.spinner}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
      
      <AnimatePresence>
        {selectedMemory && !isRecalling && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={styles.detailPanel}
          >
            <h4 style={styles.detailTitle}>{selectedMemory.summary}</h4>
            <div style={styles.detailContent}>
              {Object.entries(selectedMemory.details).map(([key, value]) => (
                <div key={key} style={styles.detailItem}>
                  <span style={styles.detailKey}>{key}:</span>
                  <span style={styles.detailValue}>{String(value)}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    maxWidth: '400px',
    padding: '20px',
    background: 'rgba(10, 35, 66, 0.8)',
    borderRadius: theme.borderRadius.xl,
    border: `1px solid ${theme.colors.primary.gold}40`,
  },
  header: {
    marginBottom: '20px',
    textAlign: 'center',
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
  timeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  node: {
    display: 'flex',
    alignItems: 'flex-start',
    padding: '12px 16px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.lg,
    borderLeft: `4px solid ${theme.colors.memory.userMemory}`,
    cursor: 'pointer',
    transition: `all ${theme.animation.duration.standard}s ${theme.animation.easing.easeOut}`,
    position: 'relative',
    overflow: 'hidden',
  },
  date: {
    minWidth: '60px',
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    opacity: 0.8,
  },
  content: {
    flex: 1,
  },
  summary: {
    color: '#fff',
    fontSize: theme.typography.fontSize.base,
    marginBottom: '4px',
  },
  meta: {
    display: 'flex',
    gap: '12px',
    fontSize: theme.typography.fontSize.xs,
  },
  agent: {
    color: theme.colors.primary.gold,
    opacity: 0.8,
  },
  importance: {
    color: theme.colors.primary.goldLight,
    opacity: 0.6,
  },
  recallOverlay: {
    position: 'absolute',
    inset: 0,
    background: 'rgba(212, 175, 55, 0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
  },
  recallText: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.sm,
  },
  spinner: {
    width: '20px',
    height: '20px',
    border: `2px solid ${theme.colors.primary.gold}`,
    borderTopColor: 'transparent',
    borderRadius: '50%',
  },
  detailPanel: {
    marginTop: '20px',
    padding: '16px',
    background: 'rgba(212, 175, 55, 0.1)',
    borderRadius: theme.borderRadius.lg,
    border: `1px solid ${theme.colors.primary.gold}30`,
  },
  detailTitle: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.lg,
    margin: '0 0 12px 0',
  },
  detailContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  detailItem: {
    display: 'flex',
    gap: '8px',
  },
  detailKey: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    minWidth: '80px',
  },
  detailValue: {
    color: '#fff',
    fontSize: theme.typography.fontSize.sm,
  },
};

export default MemoryTimeline;
