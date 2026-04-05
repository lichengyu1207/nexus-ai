import React from 'react';
import { motion } from 'framer-motion';
import { ShowcaseItem } from './showcaseData';

interface ProcessCardProps {
  item: ShowcaseItem;
  index: number;
  isActive: boolean;
  isHovered: boolean;
  onClick: () => void;
  onHover: () => void;
  onLeave: () => void;
}

const ProcessCard: React.FC<ProcessCardProps> = ({
  item,
  index,
  isActive,
  isHovered,
  onClick,
  onHover,
  onLeave,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      whileHover={{ scale: 1.02, y: -5 }}
      whileTap={{ scale: 0.98 }}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      onClick={onClick}
      style={{
        ...styles.card,
        borderColor: isActive ? item.color : 'rgba(255, 255, 255, 0.1)',
        background: isActive 
          ? `linear-gradient(135deg, ${item.color}15, ${item.color}08)`
          : 'rgba(255, 255, 255, 0.03)',
        boxShadow: isHovered 
          ? `0 10px 40px ${item.color}30, 0 0 20px ${item.color}20`
          : '0 4px 20px rgba(0, 0, 0, 0.2)',
      }}
    >
      {isActive && (
        <motion.div
          style={{ ...styles.activeGlow, background: item.gradient }}
          animate={{
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      )}

      <div style={styles.iconContainer}>
        <motion.span
          style={styles.icon}
          animate={isHovered ? { scale: [1, 1.2, 1], rotate: [0, 5, -5, 0] } : {}}
          transition={{ duration: 0.5 }}
        >
          {item.icon}
        </motion.span>
        <motion.div
          style={{ ...styles.iconRing, borderColor: item.color }}
          animate={isHovered ? { scale: [1, 1.1, 1], opacity: [0.3, 0.6, 0.3] } : { opacity: 0.3 }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      </div>

      <div style={styles.content}>
        <h3 style={{ ...styles.title, color: isActive ? item.color : '#fff' }}>
          {item.title}
        </h3>
        <p style={styles.description}>{item.description}</p>

        {item.stats && (
          <div style={styles.statsContainer}>
            {item.stats.map((stat, i) => (
              <div key={i} style={styles.statItem}>
                <span style={styles.statValue}>{stat.value}</span>
                <span style={styles.statLabel}>{stat.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <motion.div
        style={styles.playButton}
        animate={isHovered ? { opacity: 1, scale: 1 } : { opacity: 0.5, scale: 0.9 }}
      >
        <span style={styles.playIcon}>▶</span>
      </motion.div>

      {isActive && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          style={{ ...styles.activeIndicator, background: item.color }}
        >
          ✓
        </motion.div>
      )}
    </motion.div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: {
    position: 'relative',
    padding: '24px',
    borderRadius: '16px',
    border: '1px solid',
    cursor: 'pointer',
    overflow: 'hidden',
    transition: 'all 0.3s ease',
    minHeight: '180px',
    display: 'flex',
    flexDirection: 'column',
  },
  activeGlow: {
    position: 'absolute',
    inset: 0,
    opacity: 0.3,
    filter: 'blur(20px)',
    pointerEvents: 'none',
  },
  iconContainer: {
    position: 'relative',
    width: '60px',
    height: '60px',
    marginBottom: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: '32px',
    zIndex: 1,
  },
  iconRing: {
    position: 'absolute',
    inset: 0,
    borderRadius: '50%',
    border: '2px solid',
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: '18px',
    fontWeight: 'bold',
    margin: '0 0 8px 0',
    fontFamily: 'sans-serif',
  },
  description: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: 0,
    lineHeight: 1.5,
  },
  statsContainer: {
    display: 'flex',
    gap: '16px',
    marginTop: '16px',
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  statValue: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#D4AF37',
  },
  statLabel: {
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  playButton: {
    position: 'absolute',
    bottom: '16px',
    right: '16px',
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    background: 'rgba(212, 175, 55, 0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  playIcon: {
    fontSize: '12px',
    color: '#D4AF37',
    marginLeft: '2px',
  },
  activeIndicator: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontSize: '12px',
  },
};

export default ProcessCard;
