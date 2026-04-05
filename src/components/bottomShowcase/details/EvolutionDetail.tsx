import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { mockShowcaseData } from '../showcaseData';

const EvolutionDetail: React.FC = () => {
  const [adaptationScore, setAdaptationScore] = useState(0);
  const evolutionData = mockShowcaseData.evolution;

  useEffect(() => {
    const targetScore = evolutionData.adaptationScore;
    const duration = 2000;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setAdaptationScore(targetScore * easeOut);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }, [evolutionData.adaptationScore]);

  return (
    <div style={styles.container}>
      <div style={styles.personalitiesContainer}>
        <motion.div
          style={styles.personalityCard}
          animate={evolutionData.currentPersonality === 'zhouyu' ? { scale: 1.05 } : { scale: 0.95 }}
        >
          <div style={{
            ...styles.avatar,
            background: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
            opacity: evolutionData.currentPersonality === 'zhouyu' ? 1 : 0.5,
          }}>
            瑜
          </div>
          <span style={styles.personalityName}>周瑜</span>
          <span style={styles.personalityTrait}>豪迈果敢</span>
        </motion.div>

        <div style={styles.progressContainer}>
          <div style={styles.progressLabel}>人格适应度</div>
          <div style={styles.progressBar}>
            <motion.div
              style={styles.progressFill}
              animate={{ width: `${adaptationScore}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
          <div style={styles.progressValue}>{adaptationScore.toFixed(1)}%</div>
        </div>

        <motion.div
          style={styles.personalityCard}
          animate={evolutionData.currentPersonality === 'luxun' ? { scale: 1.05 } : { scale: 0.95 }}
        >
          <div style={{
            ...styles.avatar,
            background: 'linear-gradient(135deg, #3B82F6, #60A5FA)',
            opacity: evolutionData.currentPersonality === 'luxun' ? 1 : 0.5,
          }}>
            逊
          </div>
          <span style={styles.personalityName}>陆逊</span>
          <span style={styles.personalityTrait}>沉稳细致</span>
        </motion.div>
      </div>

      <div style={styles.levelSection}>
        <div style={styles.levelBadge}>
          <span style={styles.levelIcon}>⚡</span>
          <span style={styles.levelText}>进化等级 Lv.{evolutionData.level}</span>
        </div>
      </div>

      <div style={styles.abilitiesSection}>
        <h4 style={styles.sectionTitle}>已解锁能力</h4>
        <div style={styles.abilitiesGrid}>
          {evolutionData.unlockedAbilities.map((ability, index) => (
            <motion.div
              key={ability}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              style={styles.abilityCard}
            >
              <span style={styles.abilityIcon}>✓</span>
              <span style={styles.abilityName}>{ability}</span>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.button
        style={styles.chatButton}
        whileHover={{ scale: 1.02 }}
      >
        与我对话 →
      </motion.button>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  personalitiesContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '24px',
  },
  personalityCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    padding: '16px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  avatar: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '28px',
    color: '#fff',
    fontFamily: 'serif',
  },
  personalityName: {
    fontSize: '16px',
    color: '#fff',
    fontWeight: 'bold',
  },
  personalityTrait: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  progressContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    flex: 1,
    maxWidth: '200px',
  },
  progressLabel: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  progressBar: {
    width: '100%',
    height: '8px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #10B981, #34D399)',
    borderRadius: '4px',
  },
  progressValue: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#10B981',
  },
  levelSection: {
    display: 'flex',
    justifyContent: 'center',
  },
  levelBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 20px',
    background: 'rgba(16, 185, 129, 0.2)',
    borderRadius: '20px',
    border: '1px solid rgba(16, 185, 129, 0.4)',
  },
  levelIcon: {
    fontSize: '16px',
  },
  levelText: {
    fontSize: '14px',
    color: '#10B981',
    fontWeight: 'bold',
  },
  abilitiesSection: {
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    padding: '16px',
  },
  sectionTitle: {
    color: '#10B981',
    fontSize: '14px',
    margin: '0 0 12px 0',
  },
  abilitiesGrid: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
  },
  abilityCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 16px',
    background: 'rgba(16, 185, 129, 0.1)',
    borderRadius: '8px',
    border: '1px solid rgba(16, 185, 129, 0.3)',
  },
  abilityIcon: {
    color: '#10B981',
    fontSize: '12px',
  },
  abilityName: {
    color: '#fff',
    fontSize: '13px',
  },
  chatButton: {
    padding: '14px 32px',
    background: 'linear-gradient(135deg, #10B981, #059669)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    alignSelf: 'center',
  },
};

export default EvolutionDetail;
