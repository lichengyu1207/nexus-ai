import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { SoundEffects } from './SoundEffects';
import personalityData from '../../data/personalityLines.json';

type PersonalityType = 'zhouyu' | 'luxun';

interface Personality {
  name: string;
  title: string;
  description: string;
  quotes: {
    intro: string;
    taskStart: string[];
    taskComplete: string[];
    difficulty: string[];
    evolutionComplete: string[];
    memoryRecall: string[];
    miningSuccess: string[];
  };
}

interface PersonalitySelectorProps {
  onSelect?: (personality: PersonalityType) => void;
  initialPersonality?: PersonalityType;
}

const personalities: Record<PersonalityType, Personality> = personalityData as Record<PersonalityType, Personality>;

export const PersonalitySelector: React.FC<PersonalitySelectorProps> = ({
  onSelect,
  initialPersonality,
}) => {
  const [selected, setSelected] = useState<PersonalityType | null>(initialPersonality || null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [showIntro, setShowIntro] = useState(false);
  const [introText, setIntroText] = useState('');

  useEffect(() => {
    if (!initialPersonality) {
      setIsAnimating(true);
      
      let count = 0;
      const interval = setInterval(() => {
        setSelected(count % 2 === 0 ? 'zhouyu' : 'luxun');
        count++;
        
        if (count >= 6) {
          clearInterval(interval);
          const finalSelection = Math.random() > 0.5 ? 'zhouyu' : 'luxun';
          setSelected(finalSelection);
          setIsAnimating(false);
          playIntroAnimation(finalSelection);
        }
      }, 100);
    }
  }, [initialPersonality]);

  const playIntroAnimation = useCallback((personality: PersonalityType) => {
    const data = personalities[personality];
    setShowIntro(true);
    setIntroText('');
    
    const text = data.quotes.intro;
    let index = 0;
    
    const typeInterval = setInterval(() => {
      if (index < text.length) {
        setIntroText(text.slice(0, index + 1));
        index++;
        
        if (index % 2 === 0) {
          SoundEffects.playTone(personality === 'zhouyu' ? 392 : 349, 0.05, 'sine');
        }
      } else {
        clearInterval(typeInterval);
        setTimeout(() => setShowIntro(false), 2000);
      }
    }, 80);
  }, []);

  const handleSelect = useCallback((personality: PersonalityType) => {
    if (isAnimating) return;
    
    setSelected(personality);
    SoundEffects.playTone(personality === 'zhouyu' ? 523 : 440, 0.15, 'sine');
    
    if (personality === 'zhouyu') {
      SoundEffects.playZhouyuSpeak();
    } else {
      SoundEffects.playLuxunSpeak();
    }
    
    playIntroAnimation(personality);
    onSelect?.(personality);
  }, [isAnimating, onSelect, playIntroAnimation]);

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>选择您的都督</h3>
      <p style={styles.subtitle}>不同都督将带来不同的交互风格</p>
      
      <div style={styles.selectorContainer}>
        {(Object.keys(personalities) as PersonalityType[]).map((key) => {
          const p = personalities[key];
          const isSelected = selected === key;
          const colors = theme.colors.personality[key];
          
          return (
            <motion.div
              key={key}
              style={{
                ...styles.personalityCard,
                borderColor: isSelected ? colors.primary : 'transparent',
                boxShadow: isSelected ? `0 0 30px ${colors.glow}` : 'none',
              }}
              onClick={() => handleSelect(key)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              animate={isAnimating && isSelected ? {
                opacity: [0.3, 1, 0.3],
              } : {}}
              transition={{
                duration: 0.1,
                repeat: isAnimating ? Infinity : 0,
              }}
            >
              <div style={{
                ...styles.avatar,
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`,
              }}>
                <span style={styles.avatarText}>
                  {key === 'zhouyu' ? '瑜' : '逊'}
                </span>
                
                {isSelected && (
                  <motion.div
                    style={{
                      ...styles.glowRing,
                      borderColor: colors.primary,
                    }}
                    animate={{
                      rotate: 360,
                      scale: [1, 1.1, 1],
                    }}
                    transition={{
                      rotate: { duration: 3, repeat: Infinity, ease: 'linear' },
                      scale: { duration: 1.5, repeat: Infinity },
                    }}
                  />
                )}
              </div>
              
              <div style={styles.info}>
                <h4 style={{ ...styles.name, color: colors.primary }}>{p.name}</h4>
                <span style={styles.title}>{p.title}</span>
                <p style={styles.description}>{p.description}</p>
              </div>
              
              {isSelected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  style={{
                    ...styles.checkMark,
                    background: colors.primary,
                  }}
                >
                  ✓
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
      
      <AnimatePresence>
        {showIntro && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={styles.introBubble}
          >
            <span style={styles.introText}>{introText}</span>
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            >
              |
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>
      
      {selected && !showIntro && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={styles.currentStatus}
        >
          <span style={styles.statusText}>
            当前都督：<strong style={{ color: theme.colors.personality[selected].primary }}>
              {personalities[selected].name}
            </strong>
          </span>
        </motion.div>
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
  title: {
    textAlign: 'center',
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.xl,
    margin: '0 0 4px 0',
    fontFamily: theme.typography.fontFamily.display,
  },
  subtitle: {
    textAlign: 'center',
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.sm,
    margin: '0 0 24px 0',
    opacity: 0.7,
  },
  selectorContainer: {
    display: 'flex',
    gap: '20px',
    justifyContent: 'center',
  },
  personalityCard: {
    flex: 1,
    maxWidth: '200px',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: theme.borderRadius.xl,
    border: '2px solid transparent',
    cursor: 'pointer',
    transition: `all ${theme.animation.duration.standard}s`,
    position: 'relative',
    overflow: 'hidden',
  },
  avatar: {
    width: '80px',
    height: '80px',
    margin: '0 auto 16px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  avatarText: {
    fontSize: '36px',
    color: '#fff',
    fontWeight: 'bold',
    fontFamily: theme.typography.fontFamily.display,
  },
  glowRing: {
    position: 'absolute',
    inset: '-4px',
    borderRadius: '50%',
    border: '2px solid',
  },
  info: {
    textAlign: 'center',
  },
  name: {
    fontSize: theme.typography.fontSize.lg,
    margin: '0 0 4px 0',
  },
  title: {
    display: 'block',
    color: theme.colors.primary.goldLight,
    fontSize: theme.typography.fontSize.xs,
    marginBottom: '8px',
  },
  description: {
    color: '#fff',
    fontSize: theme.typography.fontSize.xs,
    margin: 0,
    lineHeight: 1.5,
    opacity: 0.8,
  },
  checkMark: {
    position: 'absolute',
    top: '10px',
    right: '10px',
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: theme.colors.primary.deepBlue,
    fontSize: '14px',
    fontWeight: 'bold',
  },
  introBubble: {
    marginTop: '20px',
    padding: '16px 24px',
    background: 'rgba(212, 175, 55, 0.1)',
    borderRadius: theme.borderRadius.lg,
    border: `1px solid ${theme.colors.primary.gold}40`,
    textAlign: 'center',
  },
  introText: {
    color: theme.colors.primary.gold,
    fontSize: theme.typography.fontSize.base,
    fontFamily: theme.typography.fontFamily.display,
  },
  currentStatus: {
    marginTop: '16px',
    textAlign: 'center',
  },
  statusText: {
    color: '#fff',
    fontSize: theme.typography.fontSize.sm,
  },
};

export default PersonalitySelector;
