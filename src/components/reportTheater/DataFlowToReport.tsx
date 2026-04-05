import React, { useEffect, useRef, useCallback } from 'react';
import { agentColors, DataFlowParticle } from './types';

interface DataFlowToReportProps {
  isActive: boolean;
  progress: number;
  agents?: string[];
}

const DataFlowToReport: React.FC<DataFlowToReportProps> = ({
  isActive,
  progress,
  agents = ['li', 'hu', 'li_guan', 'bing', 'gong', 'xing'],
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<DataFlowParticle[]>([]);
  const animationRef = useRef<number>(0);

  const createParticle = useCallback((sourceAgent: string, targetX: number, targetY: number): DataFlowParticle => {
    const sourceIndex = agents.indexOf(sourceAgent);
    const angle = (sourceIndex / agents.length) * Math.PI * 2 - Math.PI / 2;
    const radius = 120;
    const sourceX = 150 + Math.cos(angle) * radius;
    const sourceY = 150 + Math.sin(angle) * radius;

    return {
      id: `particle_${Date.now()}_${Math.random()}`,
      sourceAgent,
      targetX,
      targetY,
      x: sourceX,
      y: sourceY,
      color: agentColors[sourceAgent] || '#D4AF37',
      size: 4 + Math.random() * 4,
      speed: 2 + Math.random() * 2,
      trail: [],
    };
  }, [agents]);

  const updateParticles = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const targetX = canvas.width - 80;
    const targetY = canvas.height - 80;

    particlesRef.current = particlesRef.current.filter(particle => {
      const dx = targetX - particle.x;
      const dy = targetY - particle.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < 10) {
        return false;
      }

      particle.trail.push({ x: particle.x, y: particle.y });
      if (particle.trail.length > 10) {
        particle.trail.shift();
      }

      const speed = particle.speed * (1 + progress / 100);
      particle.x += (dx / distance) * speed;
      particle.y += (dy / distance) * speed;

      return true;
    });

    if (isActive && Math.random() < 0.1 + progress / 200) {
      const randomAgent = agents[Math.floor(Math.random() * agents.length)];
      particlesRef.current.push(createParticle(randomAgent, targetX, targetY));
    }

    if (particlesRef.current.length > 50) {
      particlesRef.current = particlesRef.current.slice(-50);
    }
  }, [isActive, progress, agents, createParticle]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const agentPositions = agents.map((agent, index) => {
      const angle = (index / agents.length) * Math.PI * 2 - Math.PI / 2;
      const radius = 120;
      return {
        agent,
        x: 150 + Math.cos(angle) * radius,
        y: 150 + Math.sin(angle) * radius,
        color: agentColors[agent] || '#D4AF37',
      };
    });

    agentPositions.forEach(pos => {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 20, 0, Math.PI * 2);
      ctx.fillStyle = `${pos.color}40`;
      ctx.fill();
      ctx.strokeStyle = pos.color;
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#fff';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const agentNames: Record<string, string> = {
        li: '吏',
        hu: '户',
        li_guan: '礼',
        bing: '兵',
        gong: '工',
        xing: '刑',
      };
      ctx.fillText(agentNames[pos.agent] || pos.agent.charAt(0).toUpperCase(), pos.x, pos.y);
    });

    const targetX = canvas.width - 80;
    const targetY = canvas.height - 80;

    ctx.beginPath();
    ctx.roundRect(targetX - 30, targetY - 40, 60, 80, 8);
    ctx.fillStyle = 'rgba(212, 175, 55, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#D4AF37';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#D4AF37';
    ctx.font = '24px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('📊', targetX, targetY);

    particlesRef.current.forEach(particle => {
      particle.trail.forEach((point, index) => {
        const alpha = index / particle.trail.length * 0.5;
        ctx.beginPath();
        ctx.arc(point.x, point.y, particle.size * 0.5, 0, Math.PI * 2);
        ctx.fillStyle = `${particle.color}${Math.floor(alpha * 255).toString(16).padStart(2, '0')}`;
        ctx.fill();
      });

      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      const gradient = ctx.createRadialGradient(
        particle.x, particle.y, 0,
        particle.x, particle.y, particle.size
      );
      gradient.addColorStop(0, particle.color);
      gradient.addColorStop(1, `${particle.color}00`);
      ctx.fillStyle = gradient;
      ctx.fill();
    });

    if (progress >= 100) {
      ctx.beginPath();
      ctx.arc(targetX, targetY, 50 + Math.sin(Date.now() / 200) * 10, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(212, 175, 55, ${0.3 + Math.sin(Date.now() / 200) * 0.2})`;
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  }, [agents, progress]);

  const animate = useCallback(() => {
    updateParticles();
    draw();
    animationRef.current = requestAnimationFrame(animate);
  }, [updateParticles, draw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = 400;
    canvas.height = 300;

    if (isActive) {
      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, animate]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        maxWidth: '400px',
        maxHeight: '300px',
      }}
    />
  );
};

export default DataFlowToReport;
