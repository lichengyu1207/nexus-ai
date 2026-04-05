import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface EvolutionProgressPanelProps {
  currentProgress?: number;
  experience?: number;
  level?: number;
  nextLevelExp?: number;
  isActive?: boolean;
  onEvolution?: () => void;
  compact?: boolean;
}

interface Ability {
  id: string;
  name: string;
  icon: string;
  description: string;
  unlocked: boolean;
}

const EvolutionProgressPanel: React.FC<EvolutionProgressPanelProps> = ({
  currentProgress = 0,
  experience = 0,
  level = 1,
  nextLevelExp = 1000,
  isActive = false,
  onEvolution,
  compact = false,
}) => {
  const [progress, setProgress] = useState(currentProgress);
  const [isEvolving, setIsEvolving] = useState(false);
  const [showReward, setShowReward] = useState(false);
  const [unlockedAbilities, setUnlockedAbilities] = useState<Ability[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const particlesRef = useRef<Array<{
    x: number;
    y: number;
    vx: number;
    vy: number;
    life: number;
    maxLife: number;
    color: string;
    size: number;
  }>>([]);

  const progressPercent = Math.min(100, (experience / nextLevelExp) * 100);

  useEffect(() => {
    setProgress(currentProgress);
  }, [currentProgress]);

  useEffect(() => {
    if (!isActive || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const width = compact ? 200 : 300;
    const height = compact ? 200 : 300;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      const angle = -Math.PI / 2 + (progressPercent / 100) * Math.PI;
      const arcStart = angle - Math.PI / 2;
      const arcEnd = angle + Math.PI / 2;

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, arcStart, arcEnd);
      ctx.strokeStyle = 'rgba(212, 175, 55, 0.3)';
      ctx.lineWidth = 8;
      ctx.stroke();

      const gradient = ctx.createLinearGradient(
        centerX - radius * Math.cos(angle),
        centerY - radius * Math.sin(angle),
        centerX + radius * Math.cos(angle),
        centerY + radius * Math.sin(angle)
      );
      gradient.addColorStop(0, 'rgba(212, 175, 55, 0.1)');
      gradient.addColorStop(progressPercent / 100, 'rgba(212, 175, 55, 0.8)');
      gradient.addColorStop(1, 'rgba(212, 175, 55, 0.3)');

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, arcStart, arcEnd);
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 12;
      ctx.stroke();

      particlesRef.current.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.1;
        p.life++;

        if (p.life < p.maxLife) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
          ctx.fill();
        }
      });

      particlesRef.current = particlesRef.current.filter((p) => p.life < p.maxLife);

      if (isActive) {
        if (Math.random() < 0.05) {
          const angle = Math.random() * Math.PI * 2;
          const distance = radius * 0.8 + Math.random() * radius * 0.2;
          particlesRef.current.push({
            x: centerX + Math.cos(angle) * distance,
            y: centerY + Math.sin(angle) * distance,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            life: 0,
            maxLife: 60 + Math.random() * 30,
            color: `rgba(212, 175, 55, ${0.3 + Math.random() * 0.7})`,
            size: 2 + Math.random() * 3,
          });
        }
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  };
}, [isActive, progressPercent, compact]);

  const triggerEvolution = useCallback(() => {
    setIsEvolving(true);

    setTimeout(() => {
      setShowReward(true);
      setUnlockedAbilities([
        {
          id: 'ability-1',
          name: '多轮诱导检测',
          icon: '🛡️',
          description: '识别并防御复杂的多轮对话诱导攻击',
          unlocked: true,
        },
        {
          id: 'ability-2',
          name: '情感识别',
          icon: '💭',
          description: '精准识别用户情绪，提供个性化服务',
          unlocked: true,
        },
        {
          id: 'ability-3',
          name: '风险预警',
          icon: '⚠️',
          description: '提前预警潜在风险，保护用户利益',
          unlocked: true,
        },
      ]);
      onEvolution?.();
    }, 2000);
  }, [onEvolution]);

  const getLevelName = (lvl: number) => {
    const levels = ['新手', '入门', '熟练', '精通', '专家', '大师'];
    return levels[Math.min(lvl - 1, levels.length - 1)] || '大师';
  };

  return (
    <div style={{
      padding: compact ? '16px' : '24px',
      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95))',
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: compact ? '20px' : '24px' }}>⚡</span>
          <h3 style={{
            color: '#D4AF37',
            fontSize: compact ? '14px' : '18px',
            fontWeight: 600,
            margin: 0,
          }}>
            智能体进化
          </h3>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 12px',
          background: 'rgba(212, 175, 55, 0.1)',
          borderRadius: '20px',
          border: '1px solid rgba(212, 175, 55, 0.3)',
        }}>
          <span style={{ color: '#D4AF37', fontSize: compact ? '12px' : '14px', fontWeight: 600 }}>
            Lv.{level}
          </span>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '11px' }}>
            {getLevelName(level)}
          </span>
        </div>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: compact ? '16px' : '24px',
      }}>
        <canvas
          ref={canvasRef}
          style={{
            width: compact ? 200 : 300,
            height: compact ? 200 : 300,
          }}
        />

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
        }}>
          <motion.div
            animate={{
              scale: isEvolving ? [1, 1.2, 1] : 1,
              opacity: isEvolving ? [1, 0.8, 1] : 1,
            }}
            transition={{ duration: 0.5 }}
            style={{
              textAlign: 'center',
            }}
          >
            <span style={{
              display: 'block',
              color: '#D4AF37',
              fontSize: compact ? '24px' : '36px',
              fontWeight: 'bold',
              textShadow: '0 0 20px rgba(212, 175, 55, 0.5)',
            }}>
              {Math.round(progressPercent)}%
            </span>
            <span style={{
              display: 'block',
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: compact ? '10px' : '12px',
              marginTop: '4px',
            }}>
              进化进度
            </span>
          </motion.div>
        </div>
      </div>

      <div style={{
        marginTop: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '12px' }}>
            经验值
          </span>
          <span style={{ color: '#D4AF37', fontSize: '16px', fontWeight: 600 }}>
            {experience} / {nextLevelExp}
          </span>
        </div>

        <motion.button
          onClick={triggerEvolution}
          disabled={isEvolving || progressPercent >= 100}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            padding: '8px 16px',
            background: isEvolving || progressPercent >= 100
              ? 'rgba(212, 175, 55, 0.3)'
              : 'linear-gradient(135deg, #D4AF37, #F59E0B)',
            border: 'none',
            borderRadius: '8px',
            color: isEvolving || progressPercent >= 100 ? 'rgba(255, 255, 255, 0.5)' : '#0f172a',
            fontSize: '12px',
            fontWeight: 600,
            cursor: isEvolving || progressPercent >= 100 ? 'not-allowed' : 'pointer',
            opacity: progressPercent >= 100 ? 0.5 : 1,
          }}
        >
          {isEvolving ? '进化中...' : progressPercent >= 100 ? '已满级' : '触发进化'}
        </motion.button>
      </div>

      <AnimatePresence>
        {showReward && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            style={{
              marginTop: '16px',
              padding: '16px',
              background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(245, 158, 11, 0.1))',
              borderRadius: '12px',
              border: '1px solid rgba(212, 175, 55, 0.3)',
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}>
              <span style={{ fontSize: '24px' }}>🎉</span>
              <span style={{ color: '#D4AF37', fontSize: '16px', fontWeight: 600 }}>
                进化成功！
              </span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '8px',
            }}>
              {unlockedAbilities.map((ability, index) => (
                <motion.div
                  key={ability.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  style={{
                    padding: '12px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '8px',
                    textAlign: 'center',
                  }}
                >
                  <span style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {ability.icon}
                  </span>
                  <span style={{
                    display: 'block',
                    color: '#fff',
                    fontSize: '13px',
                    fontWeight: 600,
                    marginBottom: '4px',
                  }}>
                    {ability.name}
                  </span>
                  <span style={{
                    display: 'block',
                    color: 'rgba(255, 255, 255, 0.6)',
                    fontSize: '11px',
                  }}>
                    {ability.description}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EvolutionProgressPanel;
