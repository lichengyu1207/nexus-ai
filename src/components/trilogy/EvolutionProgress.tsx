import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { ParticleManager } from './ParticleManager';
import { SoundEffects } from './SoundEffects';
import evolutionData from '../../data/evolutionMilestones.json';

interface Milestone {
  id: string;
  name: string;
  description: string;
  requiredProgress: number;
  abilities: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
  }>;
}

interface EvolutionProgressProps {
  currentProgress?: number;
  onMilestoneReach?: (milestone: Milestone) => void;
  onEvolutionComplete?: () => void;
  showDetails?: boolean;
}

export const EvolutionProgress: React.FC<EvolutionProgressProps> = ({
  currentProgress = 0,
  onMilestoneReach,
  onEvolutionComplete,
  showDetails = true,
}) => {
  const [progress, setProgress] = useState(currentProgress);
  const [currentMilestone, setCurrentMilestone] = useState<Milestone | null>(null);
  const [showEvolutionAnimation, setShowEvolutionAnimation] = useState(false);
  const [unlockedAbilities, setUnlockedAbilities] = useState<string[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  const milestones: Milestone[] = evolutionData.milestones;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 80;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 8;
      ctx.stroke();

      const progressAngle = (progress / 100) * Math.PI * 2 - Math.PI / 2;
      
      const gradient = ctx.createLinearGradient(
        centerX - radius, centerY,
        centerX + radius, centerY
      );
      gradient.addColorStop(0, theme.colors.evolution.stage1);
      gradient.addColorStop(0.5, theme.colors.evolution.stage2);
      gradient.addColorStop(1, theme.colors.evolution.stage3);

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, -Math.PI / 2, progressAngle);
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 8;
      ctx.lineCap = 'round';
      ctx.stroke();

      milestones.forEach((milestone, index) => {
        const angle = (milestone.requiredProgress / 100) * Math.PI * 2 - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        const isUnlocked = progress >= milestone.requiredProgress;

        ctx.beginPath();
        ctx.arc(x, y, isUnlocked ? 10 : 6, 0, Math.PI * 2);
        ctx.fillStyle = isUnlocked 
          ? theme.colors.evolution.complete 
          : 'rgba(255, 255, 255, 0.3)';
        ctx.fill();

        if (isUnlocked) {
          ctx.shadowColor = theme.colors.evolution.complete;
          ctx.shadowBlur = 10;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      ctx.fillStyle = '#fff';
      ctx.font = 'bold 32px "Microsoft YaHei", sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${Math.round(progress)}%`, centerX, centerY - 10);

      ctx.font = '12px "Microsoft YaHei", sans-serif';
      ctx.fillStyle = theme.colors.primary.goldLight;
      ctx.fillText('进化进度', centerX, centerY + 20);

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [progress, milestones]);

  useEffect(() => {
    setProgress(currentProgress);
  }, [currentProgress]);

  useEffect(() => {
    const reachedMilestone = milestones.find(
      m => progress >= m.requiredProgress && !unlockedAbilities.includes(m.id)
    );

    if (reachedMilestone) {
      setCurrentMilestone(reachedMilestone);
      setUnlockedAbilities(prev => [...prev, reachedMilestone.id]);
      
      SoundEffects.playEvolutionComplete();
      ParticleManager.createBurst('evolution', 100, 100, 30);
      
      onMilestoneReach?.(reachedMilestone);

      if (reachedMilestone.requiredProgress === 100) {
        setShowEvolutionAnimation(true);
        onEvolutionComplete?.();
      }
    }
  }, [progress, milestones, unlockedAbilities, onMilestoneReach, onEvolutionComplete]);

  const addProgress = useCallback((amount: number) => {
    setProgress(prev => Math.min(100, prev + amount));
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.progressSection}>
        <canvas
          ref={canvasRef}
          width={200}
          height={200}
          style={styles.canvas}
        />
        
        <div style={styles.milestoneLabels}>
          {milestones.map((milestone, index) => (
            <motion.div
              key={milestone.id}
              style={{
                ...styles.milestoneLabel,
                opacity: progress >= milestone.requiredProgress ? 1 : 0.5,
              }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: progress >= milestone.requiredProgress ? 1 : 0.5, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <span style={styles.milestoneName}>{milestone.name}</span>
              <span style={styles.milestoneProgress}>{milestone.requiredProgress}%</span>
            </motion.div>
          ))}
        </div>
      </div>

      <AnimatePresence>
        {currentMilestone && showDetails && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.9 }}
            style={styles.milestonePanel}
          >
            <div style={styles.milestoneHeader}>
              <span style={styles.milestoneIcon}>🎉</span>
              <span style={styles.milestoneTitle}>里程碑达成！</span>
            </div>
            <h4 style={styles.milestoneNameLarge}>{currentMilestone.name}</h4>
            <p style={styles.milestoneDesc}>{currentMilestone.description}</p>
            
            <div style={styles.abilitiesGrid}>
              {currentMilestone.abilities.map(ability => (
                <motion.div
                  key={ability.id}
                  style={styles.abilityCard}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <span style={styles.abilityIcon}>{ability.icon}</span>
                  <span style={styles.abilityName}>{ability.name}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showEvolutionAnimation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={styles.evolutionOverlay}
          >
            <motion.div
              animate={{
                scale: [1, 1.5, 1],
                rotate: [0, 360],
              }}
              transition={{ duration: 2 }}
              style={styles.evolutionBadge}
            >
              <span style={styles.evolutionBadgeText}>进化完成</span>
            </motion.div>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
              style={styles.evolutionMessage}
            >
              智能体集群已完成终极进化！
            </motion.p>
          </motion.div>
        )}
      </AnimatePresence>

      {showDetails && (
        <div style={styles.controls}>
          <span style={styles.controlLabel}>模拟进度增加：</span>
          <div style={styles.buttonGroup}>
            {[5, 10, 25].map(amount => (
              <motion.button
                key={amount}
                style={styles.progressButton}
                onClick={() => addProgress(amount)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                +{amount}%
              </motion.button>
            ))}
          </div>
        </div>
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
  progressSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
    marginBottom: '20px',
  },
  canvas: {
    display: 'block',
  },
  milestoneLabels: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  milestoneLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.md,
  },
  milestoneName: {
    color: '#fff',
    fontSize: theme.typography.fontSize.sm,
  },
  milestoneProgress: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.xs,
  },
  milestonePanel: {
    padding: '20px',
    background: `linear-gradient(135deg, ${theme.colors.evolution.complete}20, ${theme.colors.evolution.stage2}10)`,
    borderRadius: theme.borderRadius.lg,
    border: `1px solid ${theme.colors.evolution.complete}40`,
    marginBottom: '20px',
  },
  milestoneHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px',
  },
  milestoneIcon: {
    fontSize: '24px',
  },
  milestoneTitle: {
    color: theme.colors.evolution.complete,
    fontSize: theme.typography.fontSize.lg,
    fontWeight: 'bold',
  },
  milestoneNameLarge: {
    color: '#fff',
    fontSize: theme.typography.fontSize.xl,
    margin: '0 0 8px 0',
  },
  milestoneDesc: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    margin: '0 0 16px 0',
  },
  abilitiesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '12px',
  },
  abilityCard: {
    padding: '12px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.md,
    textAlign: 'center',
  },
  abilityIcon: {
    display: 'block',
    fontSize: '24px',
    marginBottom: '8px',
  },
  abilityName: {
    display: 'block',
    color: '#fff',
    fontSize: theme.typography.fontSize.xs,
  },
  evolutionOverlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  evolutionBadge: {
    width: '150px',
    height: '150px',
    background: `linear-gradient(135deg, ${theme.colors.evolution.complete}, ${theme.colors.evolution.stage2})`,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: `0 0 60px ${theme.colors.evolution.complete}`,
  },
  evolutionBadgeText: {
    color: theme.colors.primary.deepBlue,
    fontSize: theme.typography.fontSize.lg,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  evolutionMessage: {
    marginTop: '24px',
    color: '#fff',
    fontSize: theme.typography.fontSize.xl,
    textAlign: 'center',
  },
  controls: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    justifyContent: 'center',
  },
  controlLabel: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
  },
  buttonGroup: {
    display: 'flex',
    gap: '8px',
  },
  progressButton: {
    padding: '8px 16px',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldDark})`,
    color: theme.colors.primary.deepBlue,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: 'bold',
    border: 'none',
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
  },
};

export default EvolutionProgress;
