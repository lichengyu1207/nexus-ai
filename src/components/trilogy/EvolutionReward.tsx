import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { ParticleManager } from './ParticleManager';
import { SoundEffects } from './SoundEffects';
import evolutionData from '../../data/evolutionMilestones.json';

interface Ability {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface EvolutionRewardProps {
  milestoneId?: string;
  onComplete?: () => void;
  autoShow?: boolean;
}

const iconEmojis: Record<string, string> = {
  'chart-bar': '📊',
  'search': '🔍',
  'shield': '🛡️',
  'heart': '❤️',
  'network': '🌐',
  'trending-up': '📈',
  'lock': '🔒',
  'star': '⭐',
  'infinity': '∞',
  'users': '👥',
  'lightbulb': '💡',
};

export const EvolutionReward: React.FC<EvolutionRewardProps> = ({
  milestoneId,
  onComplete,
  autoShow = false,
}) => {
  const [visible, setVisible] = useState(false);
  const [phase, setPhase] = useState<'chest' | 'opening' | 'abilities' | 'detail'>('chest');
  const [selectedAbility, setSelectedAbility] = useState<Ability | null>(null);
  const [abilities, setAbilities] = useState<Ability[]>([]);
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    if (autoShow) {
      showReward();
    }
  }, [autoShow]);

  const showReward = () => {
    setVisible(true);
    setPhase('chest');
    setSelectedAbility(null);
    
    const milestone = milestoneId 
      ? evolutionData.milestones.find(m => m.id === milestoneId)
      : evolutionData.milestones[evolutionData.milestones.length - 1];
    
    if (milestone) {
      setAbilities(milestone.abilities);
    }
  };

  const handleChestClick = () => {
    setPhase('opening');
    SoundEffects.playTone(523, 0.2, 'sine');
    
    setTimeout(() => {
      SoundEffects.playEvolutionComplete();
      setPhase('abilities');
      setShowConfetti(true);
      ParticleManager.createBurst('evolution', 200, 150, 50);
      
      setTimeout(() => setShowConfetti(false), 2000);
    }, 1000);
  };

  const handleAbilityClick = (ability: Ability) => {
    setSelectedAbility(ability);
    setPhase('detail');
    SoundEffects.playTone(440, 0.1, 'sine');
  };

  const handleClose = () => {
    setVisible(false);
    onComplete?.();
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={styles.overlay}
        >
          <motion.div
            initial={{ scale: 0.8, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.8, y: 50 }}
            style={styles.container}
          >
            {showConfetti && (
              <div style={styles.confetti}>
                {Array.from({ length: 50 }).map((_, i) => (
                  <motion.div
                    key={i}
                    style={{
                      ...styles.confettiPiece,
                      background: ['#D4AF37', '#FFD700', '#FFA500', '#FF6347'][i % 4],
                      left: `${Math.random() * 100}%`,
                    }}
                    initial={{ y: -20, opacity: 1 }}
                    animate={{
                      y: 400,
                      opacity: 0,
                      rotate: Math.random() * 720 - 360,
                    }}
                    transition={{
                      duration: 2 + Math.random(),
                      ease: 'easeIn',
                    }}
                  />
                ))}
              </div>
            )}

            {phase === 'chest' && (
              <motion.div
                style={styles.chestContainer}
                onClick={handleChestClick}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <motion.div
                  animate={{
                    y: [0, -10, 0],
                    rotate: [-5, 5, -5],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                  style={styles.chest}
                >
                  🎁
                </motion.div>
                <p style={styles.chestText}>点击打开进化宝箱</p>
              </motion.div>
            )}

            {phase === 'opening' && (
              <motion.div
                style={styles.openingContainer}
                initial={{ scale: 1 }}
                animate={{ scale: [1, 1.2, 0] }}
                transition={{ duration: 1 }}
              >
                <motion.div
                  animate={{ rotate: [0, 15, -15, 0] }}
                  transition={{ duration: 0.5, repeat: 2 }}
                  style={styles.chestOpening}
                >
                  🎁
                </motion.div>
              </motion.div>
            )}

            {(phase === 'abilities' || phase === 'detail') && (
              <div style={styles.abilitiesContainer}>
                <h2 style={styles.title}>🎉 进化完成！</h2>
                <p style={styles.subtitle}>解锁新能力</p>
                
                <div style={styles.abilitiesGrid}>
                  {abilities.map((ability, index) => (
                    <motion.div
                      key={ability.id}
                      style={{
                        ...styles.abilityCard,
                        borderColor: selectedAbility?.id === ability.id 
                          ? theme.colors.primary.gold 
                          : 'transparent',
                      }}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.2 }}
                      onClick={() => handleAbilityClick(ability)}
                      whileHover={{ scale: 1.05, y: -5 }}
                    >
                      <span style={styles.abilityIcon}>
                        {iconEmojis[ability.icon] || '✨'}
                      </span>
                      <span style={styles.abilityName}>{ability.name}</span>
                    </motion.div>
                  ))}
                </div>

                <AnimatePresence>
                  {selectedAbility && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      style={styles.detailPanel}
                    >
                      <h3 style={styles.detailTitle}>{selectedAbility.name}</h3>
                      <p style={styles.detailDesc}>{selectedAbility.description}</p>
                      <div style={styles.demoHint}>
                        💡 点击查看演示效果
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button
                  style={styles.closeButton}
                  onClick={handleClose}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  完成
                </motion.button>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  container: {
    width: '90%',
    maxWidth: '500px',
    padding: '32px',
    background: `linear-gradient(180deg, ${theme.colors.primary.deepBlue}, ${theme.colors.primary.deepBlueDark})`,
    borderRadius: theme.borderRadius.xl,
    border: `2px solid ${theme.colors.primary.gold}`,
    textAlign: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  confetti: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    overflow: 'hidden',
  },
  confettiPiece: {
    position: 'absolute',
    width: '10px',
    height: '10px',
    borderRadius: '2px',
    top: 0,
  },
  chestContainer: {
    cursor: 'pointer',
    padding: '40px',
  },
  chest: {
    fontSize: '120px',
    marginBottom: '20px',
  },
  chestText: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.lg,
    margin: 0,
  },
  openingContainer: {
    padding: '60px',
  },
  chestOpening: {
    fontSize: '120px',
  },
  abilitiesContainer: {
    padding: '20px',
  },
  title: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize['2xl'],
    margin: '0 0 8px 0',
    fontFamily: theme.typography.fontFamily.display,
  },
  subtitle: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.base,
    margin: '0 0 24px 0',
    opacity: 0.8,
  },
  abilitiesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
  },
  abilityCard: {
    padding: '20px 12px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.lg,
    border: '2px solid transparent',
    cursor: 'pointer',
    transition: `all ${theme.animation.duration.standard}s`,
  },
  abilityIcon: {
    display: 'block',
    fontSize: '32px',
    marginBottom: '8px',
  },
  abilityName: {
    display: 'block',
    color: '#fff',
    fontSize: theme.typography.fontSize.sm,
    fontWeight: 'bold',
  },
  detailPanel: {
    padding: '20px',
    background: 'rgba(212, 175, 55, 0.1)',
    borderRadius: theme.borderRadius.lg,
    marginBottom: '20px',
    border: `1px solid ${theme.colors.primary.gold}40`,
  },
  detailTitle: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.lg,
    margin: '0 0 8px 0',
  },
  detailDesc: {
    color: '#fff',
    fontSize: theme.typography.fontSize.base,
    margin: '0 0 12px 0',
    lineHeight: 1.6,
  },
  demoHint: {
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    opacity: 0.8,
  },
  closeButton: {
    padding: '12px 48px',
    background: `linear-gradient(135deg, ${theme.colors.primary.gold}, ${theme.colors.primary.goldDark})`,
    color: theme.colors.primary.deepBlue,
    fontSize: theme.typography.fontSize.base,
    fontWeight: 'bold',
    border: 'none',
    borderRadius: theme.borderRadius.lg,
    cursor: 'pointer',
  },
};

export default EvolutionReward;
