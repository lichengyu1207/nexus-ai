import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface MemoryRippleProps {
  memoryContent: string;
  memoryId?: string;
  onComplete: () => void;
}

const MemoryRipple: React.FC<MemoryRippleProps> = ({
  memoryContent,
  memoryId,
  onComplete,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showCard, setShowCard] = useState(false);
  const [ripples, setRipples] = useState<number[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = 400;
    canvas.height = 400;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    let animationId: number;
    let frame = 0;
    const maxRadius = 180;
    const rippleCount = 3;
    const rippleDelay = 20;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < rippleCount; i++) {
        const rippleFrame = frame - i * rippleDelay;
        if (rippleFrame > 0) {
          const radius = rippleFrame * 2;
          const alpha = Math.max(0, 1 - radius / maxRadius);

          if (alpha > 0) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(102, 126, 234, ${alpha * 0.6})`;
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.beginPath();
            ctx.arc(centerX, centerY, radius * 0.8, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(118, 75, 162, ${alpha * 0.4})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      frame++;

      if (frame < 120) {
        animationId = requestAnimationFrame(animate);
      } else {
        setShowCard(true);
      }
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, []);

  useEffect(() => {
    if (showCard) {
      const timer = setTimeout(() => {
        onComplete();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [showCard, onComplete]);

  return (
    <motion.div
      className="memory-ripple-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
      }}
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        style={{
          position: 'relative',
          padding: '40px',
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '20px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        }}
      >
        <canvas
          ref={canvasRef}
          style={{
            display: 'block',
            margin: '0 auto',
          }}
        />

        <motion.div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '48px',
          }}
          animate={{
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          💭
        </motion.div>

        <AnimatePresence>
          {showCard && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              style={{
                marginTop: '20px',
                padding: '16px',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                backdropFilter: 'blur(10px)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '8px',
                }}
              >
                <span style={{ fontSize: '20px', marginRight: '8px' }}>📖</span>
                <span
                  style={{
                    fontSize: '14px',
                    fontWeight: 'bold',
                    color: '#667eea',
                  }}
                >
                  记忆唤醒
                </span>
              </div>
              <p
                style={{
                  fontSize: '14px',
                  color: '#666',
                  lineHeight: '1.6',
                  margin: 0,
                }}
              >
                {memoryContent}
              </p>
              {memoryId && (
                <div
                  style={{
                    marginTop: '8px',
                    fontSize: '12px',
                    color: '#999',
                  }}
                >
                  ID: {memoryId}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div
          style={{
            position: 'absolute',
            bottom: '-40px',
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
          第二幕：记忆涟漪
        </motion.div>
      </motion.div>
    </motion.div>
  );
};

export default MemoryRipple;
