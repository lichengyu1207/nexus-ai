import React, { useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AgentContribution, AGENT_CONFIG, getAgentInfo } from './types/reportStream';

interface AgentContributorProps {
  contributions: Map<string, AgentContribution>;
  onAgentClick?: (agentId: string) => void;
  activeAgent?: string;
  showParticles?: boolean;
}

const AgentContributor: React.FC<AgentContributorProps> = ({
  contributions,
  onAgentClick,
  activeAgent,
  showParticles = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Array<{
    x: number;
    y: number;
    targetX: number;
    targetY: number;
    color: string;
    alpha: number;
    speed: number;
    agentId: string;
  }>>([]);
  const animationRef = useRef<number | null>(null);
  const lastContributionRef = useRef<Map<string, number>>(new Map());

  const sortedContributions = useMemo(() => {
    return Array.from(contributions.values())
      .sort((a, b) => b.contributionCount - a.contributionCount);
  }, [contributions]);

  const totalContributions = useMemo(() => {
    return sortedContributions.reduce((sum, c) => sum + c.contributionCount, 0);
  }, [sortedContributions]);

  useEffect(() => {
    if (!showParticles || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    contributions.forEach((contribution, agentId) => {
      const lastCount = lastContributionRef.current.get(agentId) || 0;
      if (contribution.contributionCount > lastCount) {
        const agentInfo = getAgentInfo(agentId);
        const agentIndex = sortedContributions.findIndex(c => c.agentId === agentId);
        const startY = 40 + agentIndex * 80;
        
        for (let i = 0; i < 3; i++) {
          particlesRef.current.push({
            x: 20,
            y: startY + Math.random() * 40,
            targetX: rect.width - 20,
            targetY: rect.height / 2 + (Math.random() - 0.5) * 100,
            color: agentInfo.color,
            alpha: 1,
            speed: 2 + Math.random() * 2,
            agentId,
          });
        }
        lastContributionRef.current.set(agentId, contribution.contributionCount);
      }
    });

    const animate = () => {
      ctx.clearRect(0, 0, rect.width, rect.height);

      particlesRef.current = particlesRef.current.filter(particle => {
        const dx = particle.targetX - particle.x;
        const dy = particle.targetY - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 5) {
          return false;
        }

        particle.x += (dx / distance) * particle.speed;
        particle.y += (dy / distance) * particle.speed;
        particle.alpha = Math.max(0.2, 1 - (distance / 300));

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.alpha;
        ctx.fill();
        ctx.globalAlpha = 1;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.alpha * 0.3;
        ctx.fill();
        ctx.globalAlpha = 1;

        return true;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [contributions, sortedContributions, showParticles]);

  return (
    <div style={{
      position: 'relative',
      padding: '16px',
      background: 'rgba(255, 255, 255, 0.02)',
      borderRadius: '12px',
      border: '1px solid rgba(255, 255, 255, 0.05)',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <h4 style={{
          color: 'rgba(255, 255, 255, 0.9)',
          margin: 0,
          fontSize: '14px',
          fontWeight: 600,
        }}>
          智能体贡献
        </h4>
        <span style={{
          fontSize: '12px',
          color: 'rgba(255, 255, 255, 0.5)',
        }}>
          共 {totalContributions} 项数据
        </span>
      </div>

      <div style={{ position: 'relative' }}>
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            zIndex: 10,
          }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <AnimatePresence mode="popLayout">
            {sortedContributions.map((contribution, index) => {
              const agentInfo = getAgentInfo(contribution.agentId);
              const percentage = totalContributions > 0 
                ? (contribution.contributionCount / totalContributions) * 100 
                : 0;
              const isActive = activeAgent === contribution.agentId;

              return (
                <motion.div
                  key={contribution.agentId}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={() => onAgentClick?.(contribution.agentId)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    background: isActive 
                      ? `${agentInfo.color}15`
                      : 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    border: isActive 
                      ? `1px solid ${agentInfo.color}40`
                      : '1px solid transparent',
                    transition: 'all 0.2s ease',
                  }}
                  whileHover={{ 
                    background: `${agentInfo.color}10`,
                    borderColor: `${agentInfo.color}30`,
                  }}
                >
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '8px',
                    background: `${agentInfo.color}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '18px',
                    flexShrink: 0,
                  }}>
                    {agentInfo.icon}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '4px',
                    }}>
                      <span style={{
                        color: '#fff',
                        fontSize: '13px',
                        fontWeight: 500,
                      }}>
                        {agentInfo.name}
                      </span>
                      <span style={{
                        color: agentInfo.color,
                        fontSize: '12px',
                        fontWeight: 600,
                      }}>
                        {contribution.contributionCount}
                      </span>
                    </div>

                    <div style={{
                      height: '4px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '2px',
                      overflow: 'hidden',
                    }}>
                      <motion.div
                        style={{
                          height: '100%',
                          background: agentInfo.color,
                          borderRadius: '2px',
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                      />
                    </div>

                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '4px',
                      marginTop: '6px',
                    }}>
                      {contribution.dataTypes.slice(0, 3).map((type, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '10px',
                            padding: '2px 6px',
                            background: 'rgba(255, 255, 255, 0.05)',
                            borderRadius: '4px',
                            color: 'rgba(255, 255, 255, 0.6)',
                          }}
                        >
                          {type}
                        </span>
                      ))}
                      {contribution.dataTypes.length > 3 && (
                        <span style={{
                          fontSize: '10px',
                          padding: '2px 6px',
                          background: 'rgba(255, 255, 255, 0.05)',
                          borderRadius: '4px',
                          color: 'rgba(255, 255, 255, 0.4)',
                        }}>
                          +{contribution.dataTypes.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      {sortedContributions.length === 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '32px',
          color: 'rgba(255, 255, 255, 0.4)',
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🤖</div>
          <span style={{ fontSize: '14px' }}>等待智能体贡献数据...</span>
        </div>
      )}
    </div>
  );
};

export default AgentContributor;
