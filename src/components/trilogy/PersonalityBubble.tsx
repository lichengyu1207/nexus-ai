import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { theme } from './theme';
import { SoundEffects } from './SoundEffects';
import personalityData from '../../data/personalityLines.json';

type PersonalityType = 'zhouyu' | 'luxun';
type SceneType = 'taskStart' | 'taskComplete' | 'difficulty' | 'evolutionComplete' | 'memoryRecall' | 'miningSuccess';

interface PersonalityBubbleProps {
  personality: PersonalityType;
  scene: SceneType;
  targetAgent?: string;
  onComplete?: () => void;
  autoShow?: boolean;
}

const personalities = personalityData as Record<PersonalityType, {
  name: string;
  quotes: Record<string, string[]>;
}>;

export const PersonalityBubble: React.FC<PersonalityBubbleProps> = ({
  personality,
  scene,
  targetAgent,
  onComplete,
  autoShow = false,
}) => {
  const [visible, setVisible] = useState(false);
  const [displayText, setDisplayText] = useState('');
  const [fullText, setFullText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const getRandomQuote = useCallback(() => {
    const quotes = personalities[personality].quotes[scene];
    return quotes[Math.floor(Math.random() * quotes.length)];
  }, [personality, scene]);

  const showBubble = useCallback(() => {
    const quote = getRandomQuote();
    setFullText(quote);
    setDisplayText('');
    setVisible(true);
    setIsTyping(true);

    if (personality === 'zhouyu') {
      SoundEffects.playZhouyuSpeak();
    } else {
      SoundEffects.playLuxunSpeak();
    }

    let index = 0;
    const typeInterval = setInterval(() => {
      if (index < quote.length) {
        setDisplayText(quote.slice(0, index + 1));
        index++;
        
        if (index % 3 === 0) {
          SoundEffects.playTone(personality === 'zhouyu' ? 392 : 349, 0.03, 'sine');
        }
      } else {
        clearInterval(typeInterval);
        setIsTyping(false);
        
        setTimeout(() => {
          setVisible(false);
          onComplete?.();
        }, 3000);
      }
    }, 60);

    return () => clearInterval(typeInterval);
  }, [getRandomQuote, personality, onComplete]);

  useEffect(() => {
    if (autoShow) {
      showBubble();
    }
  }, [autoShow, showBubble]);

  const colors = theme.colors.personality[personality];

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.9 }}
          style={{
            ...styles.bubble,
            borderColor: colors.primary,
            boxShadow: `0 4px 20px ${colors.glow}`,
          }}
        >
          <div style={{
            ...styles.avatar,
            background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`,
          }}>
            {personality === 'zhouyu' ? '瑜' : '逊'}
          </div>
          
          <div style={styles.content}>
            <div style={{ ...styles.name, color: colors.primary }}>
              {personalities[personality].name}
            </div>
            <div style={styles.text}>
              {displayText}
              {isTyping && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  style={styles.cursor}
                >
                  |
                </motion.span>
              )}
            </div>
          </div>
          
          {targetAgent && (
            <div style={styles.targetAgent}>
              → {targetAgent}
            </div>
          )}
          
          <div style={{
            ...styles.pointer,
            borderTopColor: colors.primary,
          }} />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const styles: Record<string, React.CSSProperties> = {
  bubble: {
    position: 'relative',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '16px',
    background: 'rgba(10, 35, 66, 0.95)',
    borderRadius: theme.borderRadius.lg,
    borderWidth: '2px',
    borderStyle: 'solid',
    maxWidth: '300px',
  },
  avatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontSize: '18px',
    fontWeight: 'bold',
    fontFamily: theme.typography.fontFamily.display,
    flexShrink: 0,
  },
  content: {
    flex: 1,
  },
  name: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  text: {
    color: '#fff',
    fontSize: theme.typography.fontSize.base,
    lineHeight: 1.5,
  },
  cursor: {
    color: theme.colors.primary.gold,
    marginLeft: '2px',
  },
  targetAgent: {
    position: 'absolute',
    bottom: '-20px',
    right: '10px',
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.primary.goldLight,
    opacity: 0.7,
  },
  pointer: {
    position: 'absolute',
    bottom: '-10px',
    left: '30px',
    width: 0,
    height: 0,
    borderLeft: '10px solid transparent',
    borderRight: '10px solid transparent',
    borderTop: '10px solid',
  },
};

export default PersonalityBubble;
