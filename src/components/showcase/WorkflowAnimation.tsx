import React, { useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface WorkflowStep {
  id: number;
  name: string;
  nameEn: string;
  duration: number;
}

const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 1, name: '需求唤醒', nameEn: 'Awakening', duration: 12000 },
  { id: 2, name: '集群协作', nameEn: 'Collaboration', duration: 12000 },
  { id: 3, name: '记忆挖掘', nameEn: 'Memory Mining', duration: 12000 },
  { id: 4, name: '人格进化', nameEn: 'Evolution', duration: 12000 },
  { id: 5, name: '报告生成', nameEn: 'Report', duration: 12000 },
];

const AGENTS = [
  { id: 'li', name: '礼部', color: '#FFD700' },
  { id: 'hu', name: '户部', color: '#4CAF50' },
  { id: 'bing', name: '兵部', color: '#F44336' },
  { id: 'xing', name: '刑部', color: '#9C27B0' },
  { id: 'li2', name: '吏部', color: '#2196F3' },
  { id: 'gong', name: '工部', color: '#FF9800' },
];

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  alpha: number;
  life: number;
}

interface DataFlow {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  progress: number;
  color: string;
}

interface WorkflowAnimationProps {
  currentStep: number;
  isPlaying: boolean;
  onStepComplete?: (step: number) => void;
}

export interface WorkflowAnimationRef {
  play: () => void;
  pause: () => void;
  reset: () => void;
  seek: (step: number) => void;
}

const WorkflowAnimation = forwardRef<WorkflowAnimationRef, WorkflowAnimationProps>(
  ({ currentStep, isPlaying, onStepComplete }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>(0);
    const particlesRef = useRef<Particle[]>([]);
    const dataFlowsRef = useRef<DataFlow[]>([]);
    const timeRef = useRef<number>(0);
    const stepStartTimeRef = useRef<number>(0);

    const initParticles = useCallback((width: number, height: number) => {
      const particles: Particle[] = [];
      const count = Math.min(150, Math.floor((width * height) / 8000));
      
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: Math.random() * 2 + 1,
          color: `hsl(${220 + Math.random() * 60}, 70%, 60%)`,
          alpha: Math.random() * 0.5 + 0.2,
          life: Math.random() * 1000,
        });
      }
      
      particlesRef.current = particles;
    }, []);

    const createDataFlow = useCallback((startX: number, startY: number, endX: number, endY: number, color: string) => {
      dataFlowsRef.current.push({
        startX,
        startY,
        endX,
        endY,
        progress: 0,
        color,
      });
    }, []);

    const drawStep1 = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, progress: number) => {
      const centerX = width / 2;
      const centerY = height / 2;
      
      ctx.save();
      
      const inputWidth = 300;
      const inputHeight = 50;
      const inputX = centerX - inputWidth / 2;
      const inputY = height * 0.3;
      
      ctx.strokeStyle = `rgba(100, 200, 255, ${0.3 + progress * 0.7})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.roundRect(inputX, inputY, inputWidth, inputHeight, 8);
      ctx.stroke();
      
      const cursorX = inputX + 20 + progress * 200;
      ctx.fillStyle = `rgba(100, 200, 255, ${Math.sin(timeRef.current * 0.01) * 0.5 + 0.5})`;
      ctx.fillRect(cursorX, inputY + 10, 2, 30);
      
      if (progress > 0.5) {
        const beamProgress = (progress - 0.5) * 2;
        const gradient = ctx.createLinearGradient(centerX, inputY + inputHeight, centerX, centerY);
        gradient.addColorStop(0, 'rgba(100, 200, 255, 0.8)');
        gradient.addColorStop(1, 'rgba(255, 215, 0, 0.8)');
        
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX, inputY + inputHeight);
        ctx.lineTo(centerX, inputY + inputHeight + (centerY - inputY - inputHeight) * beamProgress);
        ctx.stroke();
        
        for (let i = 0; i < 5; i++) {
          const px = centerX + (Math.random() - 0.5) * 20;
          const py = inputY + inputHeight + (centerY - inputY - inputHeight) * beamProgress * Math.random();
          ctx.fillStyle = `rgba(255, 255, 255, ${Math.random() * 0.5})`;
          ctx.beginPath();
          ctx.arc(px, py, Math.random() * 3 + 1, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      
      ctx.restore();
    }, []);

    const drawStep2 = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, progress: number) => {
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.25;
      
      AGENTS.forEach((agent, index) => {
        const angle = (index / AGENTS.length) * Math.PI * 2 - Math.PI / 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        const agentProgress = Math.max(0, Math.min(1, progress * AGENTS.length - index));
        
        ctx.save();
        
        ctx.globalAlpha = agentProgress;
        ctx.fillStyle = agent.color;
        ctx.shadowColor = agent.color;
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(x, y, 25, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(agent.name, x, y);
        
        ctx.restore();
        
        if (agentProgress > 0.5 && index > 0) {
          const prevAngle = ((index - 1) / AGENTS.length) * Math.PI * 2 - Math.PI / 2;
          const prevX = centerX + Math.cos(prevAngle) * radius;
          const prevY = centerY + Math.sin(prevAngle) * radius;
          
          createDataFlow(prevX, prevY, x, y, agent.color);
        }
      });
      
      if (progress > 0.8) {
        const coreProgress = (progress - 0.8) * 5;
        ctx.save();
        ctx.globalAlpha = coreProgress;
        ctx.fillStyle = '#fff';
        ctx.shadowColor = '#FFD700';
        ctx.shadowBlur = 30;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 15 + Math.sin(timeRef.current * 0.05) * 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }, [createDataFlow]);

    const drawStep3 = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, progress: number) => {
      const centerX = width / 2;
      const centerY = height / 2;
      const nodeCount = 12;
      const radius = Math.min(width, height) * 0.3;
      
      const nodes: { x: number; y: number; active: boolean }[] = [];
      
      for (let i = 0; i < nodeCount; i++) {
        const angle = (i / nodeCount) * Math.PI * 2;
        const r = radius * (0.6 + Math.random() * 0.4);
        nodes.push({
          x: centerX + Math.cos(angle) * r,
          y: centerY + Math.sin(angle) * r,
          active: i < nodeCount * progress,
        });
      }
      
      nodes.forEach((node, i) => {
        if (node.active) {
          nodes.forEach((other, j) => {
            if (i < j && other.active) {
              const dist = Math.sqrt((node.x - other.x) ** 2 + (node.y - other.y) ** 2);
              if (dist < radius * 0.8) {
                ctx.strokeStyle = `rgba(100, 200, 255, ${0.3 * (1 - dist / (radius * 0.8))})`;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(node.x, node.y);
                ctx.lineTo(other.x, other.y);
                ctx.stroke();
              }
            }
          });
        }
      });
      
      nodes.forEach((node) => {
        if (node.active) {
          ctx.fillStyle = '#4FC3F7';
          ctx.shadowColor = '#4FC3F7';
          ctx.shadowBlur = 15;
          ctx.beginPath();
          ctx.arc(node.x, node.y, 8, 0, Math.PI * 2);
          ctx.fill();
        }
      });
      
      if (progress > 0.5) {
        const newNodes = Math.floor((progress - 0.5) * 10);
        for (let i = 0; i < newNodes; i++) {
          const angle = Math.random() * Math.PI * 2;
          const r = radius * (0.3 + Math.random() * 0.3);
          const x = centerX + Math.cos(angle) * r;
          const y = centerY + Math.sin(angle) * r;
          
          ctx.fillStyle = '#FFD700';
          ctx.shadowColor = '#FFD700';
          ctx.shadowBlur = 20;
          ctx.beginPath();
          ctx.arc(x, y, 5, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }, []);

    const drawStep4 = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, progress: number) => {
      const centerX = width / 2;
      const centerY = height / 2;
      
      const avatars = [
        { name: '周瑜', color: '#FFD700', x: centerX - 80 },
        { name: '陆逊', color: '#2196F3', x: centerX + 80 },
      ];
      
      avatars.forEach((avatar, index) => {
        const avatarProgress = Math.max(0, Math.min(1, progress * 2 - index));
        
        ctx.save();
        ctx.globalAlpha = avatarProgress;
        
        ctx.fillStyle = avatar.color;
        ctx.shadowColor = avatar.color;
        ctx.shadowBlur = 30;
        ctx.beginPath();
        ctx.arc(avatar.x, centerY, 40, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 16px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(avatar.name, avatar.x, centerY);
        
        ctx.restore();
      });
      
      if (progress > 0.5) {
        const switchProgress = (progress - 0.5) * 2;
        const pulseRadius = 60 + Math.sin(switchProgress * Math.PI * 4) * 10;
        
        ctx.strokeStyle = `rgba(255, 215, 0, ${1 - switchProgress})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
        ctx.stroke();
      }
      
      const barWidth = 200;
      const barHeight = 10;
      const barX = centerX - barWidth / 2;
      const barY = centerY + 80;
      
      ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.fillRect(barX, barY, barWidth, barHeight);
      
      ctx.fillStyle = '#4CAF50';
      ctx.fillRect(barX, barY, barWidth * progress, barHeight);
    }, []);

    const drawStep5 = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number, progress: number) => {
      const centerX = width / 2;
      const centerY = height / 2;
      const docWidth = 200;
      const docHeight = 280;
      const docX = centerX - docWidth / 2;
      const docY = centerY - docHeight / 2;
      
      ctx.save();
      ctx.globalAlpha = Math.min(1, progress * 2);
      
      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
      ctx.shadowBlur = 20;
      ctx.shadowOffsetY = 10;
      ctx.beginPath();
      ctx.roundRect(docX, docY, docWidth, docHeight, 8);
      ctx.fill();
      
      ctx.restore();
      
      if (progress > 0.2) {
        const textProgress = (progress - 0.2) / 0.3;
        ctx.fillStyle = '#333';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('分析报告', docX + 20, docY + 30);
        
        for (let i = 0; i < 5; i++) {
          if (textProgress > i / 5) {
            ctx.fillStyle = '#666';
            ctx.fillRect(docX + 20, docY + 50 + i * 20, 160 * Math.min(1, textProgress * 5 - i), 8);
          }
        }
      }
      
      if (progress > 0.5) {
        const chartProgress = (progress - 0.5) * 2;
        const chartX = docX + 30;
        const chartY = docY + 160;
        const chartWidth = 140;
        const chartHeight = 80;
        
        ctx.strokeStyle = '#ddd';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(chartX, chartY);
        ctx.lineTo(chartX, chartY + chartHeight);
        ctx.lineTo(chartX + chartWidth, chartY + chartHeight);
        ctx.stroke();
        
        ctx.strokeStyle = '#4CAF50';
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i <= 4; i++) {
          const x = chartX + (chartWidth / 4) * i;
          const y = chartY + chartHeight - (chartHeight * 0.3 + Math.random() * chartHeight * 0.5) * Math.min(1, chartProgress * 2);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      
      if (progress > 0.8) {
        const completeProgress = (progress - 0.8) * 5;
        
        ctx.save();
        ctx.globalAlpha = completeProgress;
        ctx.fillStyle = '#4CAF50';
        ctx.font = 'bold 16px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('✓ 分析完成', centerX, docY + docHeight + 30);
        ctx.restore();
      }
    }, []);

    const animate = useCallback(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      const width = canvas.width;
      const height = canvas.height;
      
      ctx.fillStyle = 'rgba(10, 15, 30, 0.1)';
      ctx.fillRect(0, 0, width, height);
      
      if (isPlaying) {
        timeRef.current += 16;
      }
      
      particlesRef.current.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.life -= 1;
        
        if (particle.x < 0 || particle.x > width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > height) particle.vy *= -1;
        
        if (particle.life <= 0) {
          particle.x = Math.random() * width;
          particle.y = Math.random() * height;
          particle.life = Math.random() * 1000;
        }
        
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.alpha;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
      });
      
      ctx.globalAlpha = 1;
      
      const stepProgress = Math.min(1, (timeRef.current - stepStartTimeRef.current) / WORKFLOW_STEPS[currentStep - 1]?.duration || 12000);
      
      switch (currentStep) {
        case 1:
          drawStep1(ctx, width, height, stepProgress);
          break;
        case 2:
          drawStep2(ctx, width, height, stepProgress);
          break;
        case 3:
          drawStep3(ctx, width, height, stepProgress);
          break;
        case 4:
          drawStep4(ctx, width, height, stepProgress);
          break;
        case 5:
          drawStep5(ctx, width, height, stepProgress);
          break;
      }
      
      dataFlowsRef.current = dataFlowsRef.current.filter((flow) => {
        flow.progress += 0.02;
        
        const x = flow.startX + (flow.endX - flow.startX) * flow.progress;
        const y = flow.startY + (flow.endY - flow.startY) * flow.progress;
        
        ctx.fillStyle = flow.color;
        ctx.shadowColor = flow.color;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        
        return flow.progress < 1;
      });
      
      if (isPlaying && stepProgress >= 1 && onStepComplete) {
        onStepComplete(currentStep);
      }
      
      animationRef.current = requestAnimationFrame(animate);
    }, [currentStep, isPlaying, onStepComplete, drawStep1, drawStep2, drawStep3, drawStep4, drawStep5]);

    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const handleResize = () => {
        canvas.width = canvas.offsetWidth * window.devicePixelRatio;
        canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        }
        initParticles(canvas.offsetWidth, canvas.offsetHeight);
      };
      
      handleResize();
      window.addEventListener('resize', handleResize);
      
      return () => {
        window.removeEventListener('resize', handleResize);
        cancelAnimationFrame(animationRef.current);
      };
    }, [initParticles]);

    useEffect(() => {
      stepStartTimeRef.current = timeRef.current;
    }, [currentStep]);

    useEffect(() => {
      if (isPlaying) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        cancelAnimationFrame(animationRef.current);
      }
      
      return () => {
        cancelAnimationFrame(animationRef.current);
      };
    }, [isPlaying, animate]);

    useImperativeHandle(ref, () => ({
      play: () => {},
      pause: () => {},
      reset: () => {
        timeRef.current = 0;
        stepStartTimeRef.current = 0;
        dataFlowsRef.current = [];
      },
      seek: (step: number) => {
        stepStartTimeRef.current = timeRef.current;
      },
    }));

    return (
      <div className="relative w-full h-full">
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full"
          style={{ background: 'linear-gradient(135deg, #0a0f1e 0%, #1a1a2e 50%, #0f0f23 100%)' }}
        />
        
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
          {WORKFLOW_STEPS.map((step) => (
            <div
              key={step.id}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                currentStep === step.id
                  ? 'bg-yellow-400 scale-125'
                  : currentStep > step.id
                  ? 'bg-green-400'
                  : 'bg-gray-600'
              }`}
            />
          ))}
        </div>
      </div>
    );
  }
);

WorkflowAnimation.displayName = 'WorkflowAnimation';

export default WorkflowAnimation;
