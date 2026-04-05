import React, { useEffect, useRef, useCallback, useMemo } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  baseOpacity: number;
  pulsePhase: number;
}

interface MemoryParticlesProps {
  active?: boolean;
  intensity?: 'low' | 'medium' | 'high';
}

const MemoryParticles: React.FC<MemoryParticlesProps> = ({ 
  active = false, 
  intensity = 'low' 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const particlesRef = useRef<Particle[]>([]);
  const mouseRef = useRef({ x: 0, y: 0 });
  
  const config = useMemo(() => ({
    low: { count: 50, speed: 0.3, connectionDistance: 100 },
    medium: { count: 80, speed: 0.5, connectionDistance: 120 },
    high: { count: 100, speed: 0.8, connectionDistance: 150 },
  }), []);

  const createParticles = useCallback((canvas: HTMLCanvasElement) => {
    const { count } = config[intensity];
    const particles: Particle[] = [];
    
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * config[intensity].speed,
        vy: (Math.random() - 0.5) * config[intensity].speed,
        size: 1 + Math.random() * 2,
        opacity: 0.1 + Math.random() * 0.3,
        baseOpacity: 0.1 + Math.random() * 0.3,
        pulsePhase: Math.random() * Math.PI * 2,
      });
    }
    
    return particles;
  }, [intensity, config]);

  const drawParticles = useCallback((ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
    const particles = particlesRef.current;
    const { connectionDistance } = config[intensity];
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    for (let i = 0; i < particles.length; i++) {
      const p1 = particles[i];
      
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < connectionDistance) {
          const opacity = (1 - distance / connectionDistance) * 0.15;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(139, 92, 246, ${opacity})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    
    for (const particle of particles) {
      const gradient = ctx.createRadialGradient(
        particle.x, particle.y, 0,
        particle.x, particle.y, particle.size * 3
      );
      gradient.addColorStop(0, `rgba(139, 92, 246, ${particle.opacity})`);
      gradient.addColorStop(0.5, `rgba(59, 130, 246, ${particle.opacity * 0.5})`);
      gradient.addColorStop(1, 'transparent');
      
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();
    }
  }, [intensity, config]);

  const updateParticles = useCallback((canvas: HTMLCanvasElement, time: number) => {
    const particles = particlesRef.current;
    const { speed } = config[intensity];
    
    for (const particle of particles) {
      particle.x += particle.vx;
      particle.y += particle.vy;
      
      if (particle.x < 0 || particle.x > canvas.width) {
        particle.vx *= -1;
        particle.x = Math.max(0, Math.min(canvas.width, particle.x));
      }
      if (particle.y < 0 || particle.y > canvas.height) {
        particle.vy *= -1;
        particle.y = Math.max(0, Math.min(canvas.height, particle.y));
      }
      
      const dx = mouseRef.current.x - particle.x;
      const dy = mouseRef.current.y - particle.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < 150 && active) {
        particle.opacity = Math.min(1, particle.baseOpacity + (150 - distance) / 150 * 0.5);
        particle.vx += dx * 0.0001 * speed;
        particle.vy += dy * 0.0001 * speed;
      } else {
        particle.opacity = particle.baseOpacity + Math.sin(time * 0.001 + particle.pulsePhase) * 0.1;
      }
      
      const maxSpeed = speed * 1.5;
      particle.vx = Math.max(-maxSpeed, Math.min(maxSpeed, particle.vx));
      particle.vy = Math.max(-maxSpeed, Math.min(maxSpeed, particle.vy));
    }
  }, [active, intensity, config]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const resizeCanvas = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height;
        particlesRef.current = createParticles(canvas);
      }
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    };
    
    canvas.addEventListener('mousemove', handleMouseMove);
    
    const animate = (time: number) => {
      if (!ctx || !canvas) return;
      
      updateParticles(canvas, time);
      drawParticles(ctx, canvas);
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animationRef.current = requestAnimationFrame(animate);
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('resize', resizeCanvas);
      canvas.removeEventListener('mousemove', handleMouseMove);
    };
  }, [createParticles, drawParticles, updateParticles]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-auto"
      style={{ opacity: active ? 1 : 0.5 }}
    />
  );
};

export default MemoryParticles;
