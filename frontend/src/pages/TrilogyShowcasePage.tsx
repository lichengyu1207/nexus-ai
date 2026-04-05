import React, { useState, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  LinearProgress,
  Grid,
  Paper
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  SkipNext as SkipIcon,
  Replay as ReplayIcon,
  Close as CloseIcon,
  AutoAwesome as SparkleIcon,
  Psychology as BrainIcon,
  Description as ReportIcon
} from '@mui/icons-material';

interface ConfessionAnimationProps {
  text: string;
  agentEmoji: string;
  onComplete: () => void;
}

const ConfessionAnimation: React.FC<ConfessionAnimationProps> = ({ text, agentEmoji, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [phase, setPhase] = useState<'particles' | 'beam' | 'fadeout'>('particles');

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
          p.x += Math.sin(frame * 0.05 + p.x * 0.01) * 0.5;
          p.y += Math.cos(frame * 0.05 + p.y * 0.01) * 0.5;
        } else {
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

        const gradient = ctx.createLinearGradient(centerX, centerY, targetX, targetY);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
        gradient.addColorStop(1, 'rgba(118, 75, 162, 0.8)');

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(targetX, targetY);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3 + Math.sin(frame * 0.1) * 2;
        ctx.stroke();

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
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: 'rgba(0, 0, 0, 0.8)',
        zIndex: 9999,
      }}
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

interface MemoryRippleProps {
  memoryContent: string;
  memoryId?: string;
  onComplete: () => void;
}

const MemoryRipple: React.FC<MemoryRippleProps> = ({ memoryContent, memoryId, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [showCard, setShowCard] = useState(false);

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

const TrilogyShowcasePage: React.FC = () => {
  const [step, setStep] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [hasPlayed, setHasPlayed] = useState<Set<number>>(new Set());
  const [userInput, setUserInput] = useState('');
  const [showInput, setShowInput] = useState(true);

  const steps = [
    { id: 1, title: '倾诉回响', icon: '✨', description: '文字粒子化，飞向智能体' },
    { id: 2, title: '记忆涟漪', icon: '💭', description: '涟漪动画，显示记忆卡片' },
    { id: 3, title: '慰藉成章', icon: '📖', description: '打字机效果，报告生成' },
  ];

  const startTrilogy = useCallback(() => {
    if (!userInput.trim()) {
      alert('请输入您的烦恼');
      return;
    }
    setStep(1);
    setHasPlayed(new Set());
    setShowInput(false);
  }, [userInput]);

  const handleConfessionComplete = useCallback(() => {
    setHasPlayed(prev => new Set(prev).add(1));
    if (!isPaused) {
      setStep(2);
    }
  }, [isPaused]);

  const handleMemoryComplete = useCallback(() => {
    setHasPlayed(prev => new Set(prev).add(2));
    if (!isPaused) {
      setStep(3);
    }
  }, [isPaused]);

  const handleReportComplete = useCallback(() => {
    setHasPlayed(prev => new Set(prev).add(3));
    setStep(0);
    setShowInput(true);
  }, []);

  const handleReplay = useCallback((stepNumber: number) => {
    setStep(stepNumber);
    setHasPlayed(prev => {
      const newSet = new Set(prev);
      newSet.delete(stepNumber);
      return newSet;
    });
  }, []);

  const handlePause = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  const handleSkip = useCallback(() => {
    setStep(0);
    setShowInput(true);
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          ✨ 烦恼橡皮擦三部曲演示
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          体验从倾诉到关怀的完整过程
        </Typography>
      </Box>

      {/* 步骤指示器 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mb: 4 }}>
        {steps.map((s, index) => (
          <motion.div
            key={s.id}
            style={{
              opacity: step === s.id ? 1 : 0.5,
            }}
            animate={{
              scale: step === s.id ? 1.1 : 1,
            }}
          >
            <Card
              sx={{
                minWidth: 150,
                border: step === s.id ? '2px solid' : '1px solid',
                borderColor: step === s.id ? 'primary.main' : 'divider',
                bgcolor: hasPlayed.has(s.id) ? 'success.light' : 'background.paper',
              }}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" sx={{ mb: 1 }}>
                  {hasPlayed.has(s.id) ? '✓' : s.icon}
                </Typography>
                <Typography variant="subtitle1" fontWeight="bold">
                  {s.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {s.description}
                </Typography>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </Box>

      {/* 输入区域 */}
      {showInput && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              请输入您的烦恼，开始体验三部曲
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={3}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="例如：最近工作压力很大，感觉喘不过气来..."
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              size="large"
              startIcon={<PlayIcon />}
              onClick={startTrilogy}
              disabled={!userInput.trim()}
            >
              开始体验三部曲
            </Button>
          </CardContent>
        </Card>
      )}

      {/* 控制按钮 */}
      {step > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 4 }}>
          <Button
            variant="outlined"
            startIcon={isPaused ? <PlayIcon /> : <PauseIcon />}
            onClick={handlePause}
          >
            {isPaused ? '继续' : '暂停'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<SkipIcon />}
            onClick={handleSkip}
          >
            跳过
          </Button>
          {hasPlayed.size > 0 && (
            <Button
              variant="outlined"
              startIcon={<ReplayIcon />}
              onClick={() => handleReplay(1)}
            >
              重播
            </Button>
          )}
        </Box>
      )}

      {/* 动画组件 */}
      <AnimatePresence mode="wait">
        {step === 1 && (
          <ConfessionAnimation
            key="confession"
            text={userInput}
            agentEmoji="🎵"
            onComplete={handleConfessionComplete}
          />
        )}
        {step === 2 && (
          <MemoryRipple
            key="memory"
            memoryContent="你曾说过：工作压力大，加班太多"
            memoryId="memory-001"
            onComplete={handleMemoryComplete}
          />
        )}
        {step === 3 && (
          <motion.div
            key="report"
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
            <Card sx={{ maxWidth: 600, width: '90%', maxHeight: '80vh', overflow: 'auto' }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <ReportIcon sx={{ mr: 1 }} />
                  第三幕：慰藉成章
                </Typography>
                <Alert severity="success" sx={{ mb: 2 }}>
                  报告生成完成！
                </Alert>
                <Typography variant="body1" paragraph>
                  基于您的倾诉，我们为您生成了专属的关怀报告。
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={handleReportComplete}
                >
                  完成体验
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 功能说明 */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SparkleIcon sx={{ fontSize: 40, color: 'primary.main', mr: 1 }} />
                <Typography variant="h6">第一幕：倾诉回响</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                您的文字将化作粒子，飞向智能体，象征着您的烦恼被倾听和理解。
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <BrainIcon sx={{ fontSize: 40, color: 'secondary.main', mr: 1 }} />
                <Typography variant="h6">第二幕：记忆涟漪</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                系统检索相似记忆，用涟漪动画表现回忆被唤醒，智能体提及过往经历。
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ReportIcon sx={{ fontSize: 40, color: 'success.main', mr: 1 }} />
                <Typography variant="h6">第三幕：慰藉成章</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                生成专属关怀报告，包含情绪分析、暖心建议和成长记录。
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TrilogyShowcasePage;
