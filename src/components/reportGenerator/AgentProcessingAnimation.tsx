import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AGENT_CONFIG, getAgentInfo } from './types/reportStream';

interface AgentProcessingAnimationProps {
  isActive: boolean;
  currentAgent?: string | null;
  onComplete?: () => void;
  duration?: number;
}

const AGENT_NODES = Object.entries(AGENT_CONFIG).map(([id, config]) => ({
  id,
  ...config,
}));

const AgentProcessingAnimation: React.FC<AgentProcessingAnimationProps> = ({
  isActive,
  currentAgent,
  onComplete,
  duration = 3000,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const [processingStage, setProcessingStage] = useState(0);
  const particlesRef = useRef<Array<{
    x: number;
    y: number;
    vx: number;
    vy: number;
    color: string;
    size: number;
    alpha: number;
    life: number;
  }>>([]);

  useEffect(() => {
    if (!isActive || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const radius = Math.min(rect.width, rect.height) * 0.35;

    const stageTimer = setInterval(() => {
      setProcessingStage(prev => (prev + 1) % 4);
    }, duration / 4);

    const completeTimer = setTimeout(() => {
      onComplete?.();
    }, duration);

    const animate = () => {
      ctx.clearRect(0, 0, rect.width, rect.height);

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius * 0.6, 0, Math.PI * 2);
      ctx.stroke();

      AGENT_NODES.forEach((node, index) => {
        const angle = (index / AGENT_NODES.length) * Math.PI * 2 - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        const isActiveNode = currentAgent === node.id;
        const pulseScale = isActiveNode ? 1 + Math.sin(Date.now() / 200) * 0.2 : 1;
        
        ctx.beginPath();
        ctx.arc(x, y, 20 * pulseScale, 0, Math.PI * 2);
        ctx.fillStyle = isActiveNode 
          ? node.color 
          : `${node.color}40`;
        ctx.fill();

        if (isActiveNode) {
          ctx.beginPath();
          ctx.arc(x, y, 30, 0, Math.PI * 2);
          ctx.strokeStyle = node.color;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        ctx.font = '16px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.icon, x, y);

        ctx.font = '10px sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.fillText(node.name, x, y + 32);
      });

      if (currentAgent) {
        const activeIndex = AGENT_NODES.findIndex(n => n.id === currentAgent);
        if (activeIndex >= 0) {
          const angle = (activeIndex / AGENT_NODES.length) * Math.PI * 2 - Math.PI / 2;
          const x = centerX + Math.cos(angle) * radius;
          const y = centerY + Math.sin(angle) * radius;

          for (let i = 0; i < 2; i++) {
            particlesRef.current.push({
              x: x,
              y: y,
              vx: (centerX - x) / 50 + (Math.random() - 0.5) * 2,
              vy: (centerY - y) / 50 + (Math.random() - 0.5) * 2,
              color: getAgentInfo(currentAgent).color,
              size: 3 + Math.random() * 3,
              alpha: 1,
              life: 60,
            });
          }
        }
      }

      particlesRef.current = particlesRef.current.filter(particle => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.alpha = Math.max(0, particle.alpha - 0.02);
        particle.life--;

        if (particle.alpha > 0 && particle.life > 0) {
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
          ctx.fillStyle = particle.color;
          ctx.globalAlpha = particle.alpha;
          ctx.fill();
          ctx.globalAlpha = 1;
          return true;
        }
        return false;
      });

      const time = Date.now() / 1000;
      const innerRadius = radius * 0.3;
      const points = 6;
      
      ctx.beginPath();
      for (let i = 0; i <= points; i++) {
        const angle = (i / points) * Math.PI * 2 + time;
        const r = innerRadius * (0.8 + Math.sin(time * 2 + i) * 0.2);
        const x = centerX + Math.cos(angle) * r;
        const y = centerY + Math.sin(angle) * r;
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.closePath();
      ctx.strokeStyle = 'rgba(212, 175, 55, 0.5)';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.font = '24px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('📊', centerX, centerY);

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      clearInterval(stageTimer);
      clearTimeout(completeTimer);
    };
  }, [isActive, currentAgent, duration, onComplete]);

  const stageLabels = ['数据采集', '智能分析', '内容生成', '报告整合'];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        padding: '20px',
      }}
    >
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: '400px',
        aspectRatio: '1',
      }}>
        <canvas
          ref={canvasRef}
          style={{
            width: '100%',
            height: '100%',
          }}
        />
      </div>

      <motion.div
        style={{
          marginTop: '24px',
          textAlign: 'center',
        }}
      >
        <motion.div
          key={processingStage}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            fontSize: '16px',
            color: '#D4AF37',
            fontWeight: 600,
            marginBottom: '8px',
          }}
        >
          {stageLabels[processingStage]}
        </motion.div>
        
        <div style={{
          display: 'flex',
          gap: '8px',
          justifyContent: 'center',
        }}>
          {stageLabels.map((_, index) => (
            <motion.div
              key={index}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: index === processingStage 
                  ? '#D4AF37' 
                  : 'rgba(255, 255, 255, 0.2)',
              }}
              animate={index === processingStage ? { scale: [1, 1.3, 1] } : {}}
              transition={{ duration: 0.5, repeat: Infinity }}
            />
          ))}
        </div>

        {currentAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              marginTop: '16px',
              padding: '8px 16px',
              background: `${getAgentInfo(currentAgent).color}20`,
              borderRadius: '20px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>{getAgentInfo(currentAgent).icon}</span>
            <span style={{ 
              color: getAgentInfo(currentAgent).color,
              fontSize: '14px',
            }}>
              {getAgentInfo(currentAgent).name} 正在处理...
            </span>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default AgentProcessingAnimation;
