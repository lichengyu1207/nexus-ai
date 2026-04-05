import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { consultApi } from '../../api/consult';

interface PersonalitySelectorProps {
  onSelect?: (agent: 'zhouyu' | 'luxun', sessionId: string) => void;
  recentSessions?: Array<{ agent: 'zhouyu' | 'luxun'; title: string; id: string }>;
  compact?: boolean;
}

const PERSONALITIES = {
  zhouyu: {
    id: 'zhouyu',
    name: '周瑜都督',
    subtitle: '豪迈果敢 · 战略眼光',
    description: '善于宏观把控，以战略眼光分析房产投资价值，决策果断有力',
    avatar: '瑜',
    color: '#D4AF37',
    gradient: 'linear-gradient(135deg, #D4AF37, #F59E0B)',
    traits: ['宏观分析', '战略决策', '果断执行'],
    icon: '🎯',
  },
  luxun: {
    id: 'luxun',
    name: '陆逊都督',
    subtitle: '沉稳细致 · 数据验证',
    description: '精于数据验证，以严谨态度确保分析准确性，注重细节把控',
    avatar: '逊',
    color: '#3B82F6',
    gradient: 'linear-gradient(135deg, #3B82F6, #60A5FA)',
    traits: ['数据验证', '细节把控', '严谨分析'],
    icon: '📊',
  },
};

const PersonalitySelector: React.FC<PersonalitySelectorProps> = ({
  onSelect,
  recentSessions = [],
  compact = false,
}) => {
  const [selected, setSelected] = useState<'zhouyu' | 'luxun' | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredPersonality, setHoveredPersonality] = useState<'zhouyu' | 'luxun' | null>(null);

  const handleSelect = useCallback(async (agent: 'zhouyu' | 'luxun') => {
    if (isCreating) return;

    setSelected(agent);
    setIsCreating(true);
    setError(null);

    try {
      const session = await consultApi.createSession(`${PERSONALITIES[agent].name}咨询会话`);
      onSelect?.(agent, session.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建会话失败');
      setSelected(null);
    } finally {
      setIsCreating(false);
    }
  }, [isCreating, onSelect]);

  useEffect(() => {
    const randomSelect = Math.random() > 0.5 ? 'zhouyu' : 'luxun';
    setHoveredPersonality(randomSelect);
  }, []);

  return (
    <div style={{
      padding: compact ? '16px' : '24px',
      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95))',
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
    }}>
      <div style={{
        textAlign: 'center',
        marginBottom: compact ? '16px' : '24px',
      }}>
        <motion.div
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          style={{ fontSize: '32px', marginBottom: '8px' }}
        >
          👥
        </motion.div>
        <h3 style={{
          color: '#fff',
          fontSize: compact ? '16px' : '20px',
          fontWeight: 600,
          margin: 0,
          marginBottom: '4px',
        }}>
          选择您的专属都督
        </h3>
        <p style={{
          color: 'rgba(255, 255, 255, 0.5)',
          fontSize: '13px',
          margin: 0,
        }}>
          不同人格，不同风格的分析体验
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: compact ? '1fr 1fr' : '1fr 1fr',
        gap: compact ? '12px' : '16px',
        marginBottom: compact ? '16px' : '24px',
      }}>
        {(Object.keys(PERSONALITIES) as Array<'zhouyu' | 'luxun'>).map((key) => {
          const personality = PERSONALITIES[key];
          const isSelected = selected === key;
          const isHovered = hoveredPersonality === key;

          return (
            <motion.div
              key={key}
              onClick={() => handleSelect(key)}
              onMouseEnter={() => setHoveredPersonality(key)}
              onMouseLeave={() => setHoveredPersonality(null)}
              whileHover={{ scale: 1.02, y: -4 }}
              whileTap={{ scale: 0.98 }}
              style={{
                position: 'relative',
                padding: compact ? '16px' : '24px',
                background: isSelected
                  ? `${personality.color}15`
                  : isHovered
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'rgba(255, 255, 255, 0.02)',
                borderRadius: '16px',
                border: `2px solid ${isSelected ? personality.color : 'rgba(255, 255, 255, 0.1)'}`,
                cursor: isCreating ? 'wait' : 'pointer',
                overflow: 'hidden',
              }}
            >
              {isSelected && (
                <motion.div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: `linear-gradient(135deg, ${personality.color}10, transparent)`,
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
              )}

              {isHovered && !isSelected && (
                <motion.div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: `radial-gradient(circle at center, ${personality.color}10, transparent)`,
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
              )}

              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '12px',
                }}>
                  <motion.div
                    style={{
                      width: compact ? '48px' : '64px',
                      height: compact ? '48px' : '64px',
                      borderRadius: '50%',
                      background: personality.gradient,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: compact ? '24px' : '32px',
                      color: '#fff',
                      fontFamily: 'serif',
                      fontWeight: 'bold',
                      boxShadow: isSelected
                        ? `0 0 20px ${personality.color}60`
                        : 'none',
                    }}
                    animate={isSelected ? {
                      boxShadow: [
                        `0 0 20px ${personality.color}60`,
                        `0 0 40px ${personality.color}80`,
                        `0 0 20px ${personality.color}60`,
                      ],
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    {isCreating && isSelected ? (
                      <motion.span
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      >
                        ⏳
                      </motion.span>
                    ) : (
                      personality.avatar
                    )}
                  </motion.div>

                  <div>
                    <h4 style={{
                      color: personality.color,
                      fontSize: compact ? '14px' : '18px',
                      fontWeight: 600,
                      margin: 0,
                    }}>
                      {personality.name}
                    </h4>
                    <p style={{
                      color: 'rgba(255, 255, 255, 0.5)',
                      fontSize: '11px',
                      margin: 0,
                    }}>
                      {personality.subtitle}
                    </p>
                  </div>
                </div>

                <p style={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '12px',
                  lineHeight: 1.6,
                  margin: 0,
                  marginBottom: '12px',
                }}>
                  {personality.description}
                </p>

                <div style={{
                  display: 'flex',
                  gap: '6px',
                  flexWrap: 'wrap',
                }}>
                  {personality.traits.map((trait) => (
                    <span
                      key={trait}
                      style={{
                        padding: '4px 8px',
                        background: `${personality.color}20`,
                        borderRadius: '4px',
                        color: personality.color,
                        fontSize: '10px',
                      }}
                    >
                      {trait}
                    </span>
                  ))}
                </div>
              </div>

              {isSelected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    width: '24px',
                    height: '24px',
                    background: personality.color,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontSize: '14px',
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
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              padding: '12px',
              background: 'rgba(239, 68, 68, 0.1)',
              borderRadius: '8px',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              marginBottom: '16px',
            }}
          >
            <span style={{ color: '#ef4444', fontSize: '13px' }}>⚠️ {error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {recentSessions.length > 0 && (
        <div style={{
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
        }}>
          <span style={{
            color: 'rgba(255, 255, 255, 0.5)',
            fontSize: '11px',
            marginBottom: '8px',
            display: 'block',
          }}>
            最近会话
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {recentSessions.slice(0, 3).map((session) => {
              const personality = PERSONALITIES[session.agent];
              return (
                <motion.div
                  key={session.id}
                  whileHover={{ background: 'rgba(255, 255, 255, 0.05)' }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: personality.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    color: '#fff',
                  }}>
                    {personality.avatar}
                  </div>
                  <span style={{
                    flex: 1,
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '12px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {session.title}
                  </span>
                  <span style={{
                    color: personality.color,
                    fontSize: '10px',
                  }}>
                    继续 →
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalitySelector;
