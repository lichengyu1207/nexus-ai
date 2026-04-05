import React, { useEffect, useRef, useCallback } from 'react';
import { useDemoStore } from '@/stores/demoStore';
import agentsData from '@/data/agentsData.json';

interface Particle {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  color: string;
  speed: number;
  progress: number;
  size: number;
}

const DataFlowCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const particlesRef = useRef<Particle[]>([]);
  const { agentsStatus, currentScene } = useDemoStore();
  
  const agents = agentsData.agents;
  
  const getAgentPosition = useCallback((agentId: string, canvasWidth: number, canvasHeight: number) => {
    const index = agents.findIndex(a => a.id === agentId);
    const cols = 3;
    const rows = 2;
    const cellWidth = canvasWidth / cols;
    const cellHeight = canvasHeight / rows;
    
    const col = index % cols;
    const row = Math.floor(index / cols);
    
    return {
      x: cellWidth * (col + 0.5),
      y: cellHeight * (row + 0.5),
    };
  }, [agents]);

  const createParticle = useCallback((fromAgent: string, toAgent: string, color: string, canvas: HTMLCanvasElement) => {
    const fromPos = getAgentPosition(fromAgent, canvas.width, canvas.height);
    const toPos = getAgentPosition(toAgent, canvas.width, canvas.height);
    
    return {
      x: fromPos.x,
      y: fromPos.y,
      targetX: toPos.x,
      targetY: toPos.y,
      color,
      speed: 0.02 + Math.random() * 0.01,
      progress: 0,
      size: 3 + Math.random() * 2,
    };
  }, [getAgentPosition]);

  const drawParticle = useCallback((ctx: CanvasRenderingContext2D, particle: Particle) => {
    const x = particle.x + (particle.targetX - particle.x) * particle.progress;
    const y = particle.y + (particle.targetY - particle.y) * particle.progress;
    
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, particle.size * 2);
    gradient.addColorStop(0, particle.color);
    gradient.addColorStop(0.5, particle.color + '80');
    gradient.addColorStop(1, 'transparent');
    
    ctx.beginPath();
    ctx.arc(x, y, particle.size, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(x, y, particle.size * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
  }, []);

  const drawConnectionLines = useCallback((ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i < agents.length; i++) {
      for (let j = i + 1; j < agents.length; j++) {
        const pos1 = getAgentPosition(agents[i].id, canvas.width, canvas.height);
        const pos2 = getAgentPosition(agents[j].id, canvas.width, canvas.height);
        
        ctx.beginPath();
        ctx.moveTo(pos1.x, pos1.y);
        ctx.lineTo(pos2.x, pos2.y);
        ctx.stroke();
      }
    }
  }, [agents, getAgentPosition]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || currentScene !== 'scene2') return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const resizeCanvas = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    const flowPatterns = [
      { from: 'li', to: 'li_guan' },
      { from: 'li_guan', to: 'hu' },
      { from: 'hu', to: 'bing' },
      { from: 'bing', to: 'gong' },
      { from: 'gong', to: 'xing' },
      { from: 'xing', to: 'li' },
    ];
    
    let patternIndex = 0;
    let lastSpawnTime = 0;
    const spawnInterval = 500;
    
    const animate = (timestamp: number) => {
      if (!ctx || !canvas) return;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      drawConnectionLines(ctx, canvas);
      
      if (timestamp - lastSpawnTime > spawnInterval) {
        const pattern = flowPatterns[patternIndex % flowPatterns.length];
        const fromAgent = agents.find(a => a.id === pattern.from);
        const toAgent = agents.find(a => a.id === pattern.to);
        
        if (fromAgent && toAgent) {
          const particle = createParticle(pattern.from, pattern.to, fromAgent.color, canvas);
          particlesRef.current.push(particle);
        }
        
        patternIndex++;
        lastSpawnTime = timestamp;
      }
      
      particlesRef.current = particlesRef.current.filter(particle => {
        particle.progress += particle.speed;
        
        if (particle.progress >= 1) {
          return false;
        }
        
        drawParticle(ctx, particle);
        return true;
      });
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animationRef.current = requestAnimationFrame(animate);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [currentScene, drawConnectionLines, createParticle, drawParticle, agents]);

  if (currentScene !== 'scene2') return null;

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ mixBlendMode: 'screen' }}
    />
  );
};

export default DataFlowCanvas;
