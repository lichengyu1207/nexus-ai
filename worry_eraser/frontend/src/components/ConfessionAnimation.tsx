import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ConfessionAnimationProps {
  text: string;
  agentEmoji: string;
  onComplete: () => void;
}

const ConfessionAnimation: React.FC<ConfessionAnimationProps> = ({
  text,
  agentEmoji,
  onComplete,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [phase, setPhase] = useState<'particles' | 'beam' | 'fadeout'>('particles');
  const [displayText, setDisplayText] = useState('');

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    interface Particle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      life: number;
      maxLife: number;
      char: string;
      size: number;
    }

    const particles: Particle[] = [];
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const targetX = canvas.width * 0.7;
    const targetY = canvas.height * 0.3;

    const chars = text.split('');
    const charsPerRow = Math.ceil(Math.sqrt(chars.length));
    const spacing = 30;

    chars.forEach((char, index) => {
      const row = Math.floor(index / charsPerRow);
      const col = index % charsPerRow;
      const startX = centerX - (charsPerRow * spacing) / 2 + col * spacing;
      const startY = centerY + row * spacing;

      particles.push({
        x: startX,
        y: startY,
        vx: 0,
        vy: 0,
        life: 0,
        maxLife: 120,
        char,
        size: 16,
      });
    });

    let animationId: number;
    let frame = 0;

    const animate = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      particles.forEach(p => {
        p.life++;

        if (frame < 60) {
          // Phase 1: Particles float
          p.x += Math.sin(frame * 0.05 + p.x * 0.01) * 0.5;
          p.y += Math.cos(frame * 0.05 + p.y * 0.01) * 0.5;
        } else {
          // Phase 2: Fly to target
          const dx = targetX - p.x;
          const dy = targetY - p.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const speed = Math.min(distance * 0.05, 8);

          p.vx = (dx / distance) * speed;
          p.vy = (dy / distance) * speed;
          p.x += p.vx;
          p.y += p.vy;
        }

        const alpha = Math.max(0, 1 - p.life / p.maxLife);
        ctx.font = `${p.size}px Arial`;
        ctx.fillStyle = `rgba(102, 126, 234, ${alpha})`;
        ctx.textAlign = 'center';
        ctx.fillText(p.char, p.x, p.y);
      });

      frame++;

      if (frame < 150) {
        animationId = requestAnimationFrame(animate);
      } else {
        setPhase('beam');
      }
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [text]);

  useEffect(() => {
    if (phase === 'beam') {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const targetX = canvas.width * 0.7;
      const targetY = canvas.height * 0.3;

      let frame = 0;
      let animationId: number;

      const animateBeam = () => {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw beam
        const gradient = ctx.createLinearGradient(centerX, centerY, targetX, targetY);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
        gradient.addColorStop(1, 'rgba(118, 75, 162, 0.8)');

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(targetX, targetY);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3 + Math.sin(frame * 0.1) * 2;
        ctx.stroke();

        // Draw particles along beam
        for (let i = 0; i < 5; i++) {
          const t = (frame * 0.02 + i * 0.2) % 1;
          const x = centerX + (targetX - centerX) * t;
          const y = centerY + (targetY - centerY) * t;

          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(102, 126, 234, ${1 - t})`;
          ctx.fill();
        }

        frame++;
        if (frame < 60) {
          animationId = requestAnimationFrame(animateBeam);
        } else {
          setPhase('fadeout');
        }
      };

      animateBeam();

      return () => {
        cancelAnimationFrame(animationId);
      };
    }
  }, [phase]);

  useEffect(() => {
    if (phase === 'fadeout') {
      const timer = setTimeout(() => {
        onComplete();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [phase, onComplete]);

  return (
    <motion.div
      className="animation-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <canvas ref={canvasRef} />
      
      <motion.div
        style={{
          position: 'absolute',
          top: '30%',
          right: '10%',
          fontSize: '48px',
        }}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 1, duration: 0.5 }}
      >
        {agentEmoji}
      </motion.div>
      
      <motion.div
        style={{
          position: 'absolute',
          bottom: '10%',
          left: '50%',
          transform: 'translateX(-50%)',
          color: 'white',
          fontSize: '14px',
          opacity: 0.7,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.7 }}
        transition={{ delay: 0.5 }}
      >
        第一幕：倾诉回响
      </motion.div>
    </motion.div>
  );
};

export default ConfessionAnimation;
