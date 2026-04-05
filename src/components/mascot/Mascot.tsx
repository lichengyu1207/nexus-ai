import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence, useDragControls, PanInfo } from 'framer-motion';
import quotesData from '@/data/mascot-quotes.json';

export type MascotEmotion = 'default' | 'thinking' | 'happy' | 'confused' | 'surprised' | 'comforting';
export type MascotPose = 'standing' | 'sitting' | 'waving' | 'pointing';
export type MascotSize = 'sm' | 'md' | 'lg' | 'xl';

interface MascotProps {
  emotion?: MascotEmotion;
  pose?: MascotPose;
  size?: MascotSize;
  className?: string;
  onClick?: () => void;
  animate?: boolean;
  alt?: string;
}

const emotionImages: Record<MascotEmotion, string> = {
  default: '/images/mascot/expressions/default.svg',
  thinking: '/images/mascot/expressions/thinking.svg',
  happy: '/images/mascot/expressions/happy.svg',
  confused: '/images/mascot/expressions/confused.svg',
  surprised: '/images/mascot/expressions/surprised.svg',
  comforting: '/images/mascot/expressions/reassuring.svg',
};

const poseImages: Record<MascotPose, string> = {
  standing: '/images/mascot/poses/standing.svg',
  sitting: '/images/mascot/poses/sitting.svg',
  waving: '/images/mascot/poses/waving.svg',
  pointing: '/images/mascot/poses/pointing.svg',
};

const sizeMap: Record<MascotSize, number> = {
  sm: 16,
  md: 32,
  lg: 64,
  xl: 128,
};

const emotions: MascotEmotion[] = ['default', 'thinking', 'happy', 'confused', 'surprised', 'comforting'];
const poses: MascotPose[] = ['standing', 'sitting', 'waving', 'pointing'];

const breatheAnimation = {
  scale: [1, 1.03, 1],
  transition: {
    duration: 3,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

const floatAnimation = {
  y: [0, -6, 0],
  transition: {
    duration: 2.5,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

const danceAnimation = {
  rotate: [0, -15, 15, -10, 10, 0],
  scale: [1, 1.1, 1.1, 1.1, 1.1, 1],
  transition: {
    duration: 0.8,
    ease: 'easeInOut',
  },
};

const Mascot: React.FC<MascotProps> = ({
  emotion = 'default',
  pose,
  size = 'md',
  className = '',
  onClick,
  animate = true,
  alt = '房小智',
}) => {
  const [imageError, setImageError] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  const imageSrc = pose ? poseImages[pose] : emotionImages[emotion];
  const pixelSize = sizeMap[size];

  useEffect(() => {
    setImageError(false);
  }, [emotion, pose]);

  const handleClick = () => {
    if (onClick) {
      setIsClicked(true);
      setTimeout(() => setIsClicked(false), 600);
      onClick();
    }
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const getAnimationVariants = () => {
    if (!animate) return {};

    if (isClicked) {
      return {
        scale: [1, 0.9, 1.1, 1],
        transition: { duration: 0.4 },
      };
    }

    if (pose === 'waving') {
      return floatAnimation;
    }

    if (emotion === 'thinking') {
      return breatheAnimation;
    }

    if (emotion === 'happy') {
      return {
        ...breatheAnimation,
        scale: [1, 1.05, 1],
      };
    }

    return breatheAnimation;
  };

  if (imageError) {
    return (
      <motion.div
        className={`mascot-fallback ${className}`}
        style={{
          width: pixelSize,
          height: pixelSize,
          backgroundColor: '#E5E7EB',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: pixelSize * 0.5,
          cursor: onClick ? 'pointer' : 'default',
        }}
        onClick={handleClick}
        whileHover={onClick ? { scale: 1.05 } : {}}
        whileTap={onClick ? { scale: 0.95 } : {}}
      >
        🏠
      </motion.div>
    );
  }

  return (
    <motion.div
      className={`mascot ${className}`}
      style={{
        width: pixelSize,
        height: pixelSize,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: onClick ? 'pointer' : 'default',
        userSelect: 'none',
      }}
      onClick={handleClick}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ 
        opacity: 1, 
        scale: 1,
        ...getAnimationVariants(),
      }}
      exit={{ opacity: 0, scale: 0.8 }}
      whileHover={onClick ? { scale: 1.08 } : {}}
      whileTap={onClick ? { scale: 0.92 } : {}}
      transition={{ 
        opacity: { duration: 0.3 },
        scale: { duration: 0.3 },
      }}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <img
        src={imageSrc}
        alt={alt}
        onError={handleImageError}
        draggable={false}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          pointerEvents: 'none',
        }}
      />
    </motion.div>
  );
};

export default Mascot;

const getRandomItem = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

const getRandomQuote = (emotion: MascotEmotion, isEasterEgg: boolean = false): string => {
  if (isEasterEgg) {
    return getRandomItem(quotesData.easterEgg);
  }
  const emotionQuotes = quotesData[emotion as keyof typeof quotesData] as string[];
  const randomQuotes = quotesData.random;
  const allQuotes = [...emotionQuotes, ...randomQuotes];
  return getRandomItem(allQuotes);
};

const POSITION_STORAGE_KEY = 'mascot_position';
const EASTER_EGG_THRESHOLD = 3;
const CLICK_TIMEOUT = 1000;

interface InteractiveMascotProps {
  size?: MascotSize;
  initialPosition?: { x: number; y: number };
  onQuoteShow?: (quote: string) => void;
  onEasterEggTrigger?: () => void;
  draggable?: boolean;
  showQuoteBubble?: boolean;
  className?: string;
}

export const InteractiveMascot: React.FC<InteractiveMascotProps> = ({
  size = 'lg',
  initialPosition,
  onQuoteShow,
  onEasterEggTrigger,
  draggable = true,
  showQuoteBubble = true,
  className = '',
}) => {
  const [emotion, setEmotion] = useState<MascotEmotion>('default');
  const [pose, setPose] = useState<MascotPose | undefined>(undefined);
  const [quote, setQuote] = useState<string | null>(null);
  const [isDancing, setIsDancing] = useState(false);
  const [isEasterEggActive, setIsEasterEggActive] = useState(false);
  const [position, setPosition] = useState<{ x: number; y: number }>(() => {
    if (initialPosition) return initialPosition;
    try {
      const saved = localStorage.getItem(POSITION_STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {
      // ignore
    }
    return { x: 20, y: 20 };
  });

  const clickCountRef = useRef(0);
  const clickTimerRef = useRef<NodeJS.Timeout | null>(null);
  const dragControls = useDragControls();
  const constraintsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(position));
    } catch {
      // ignore
    }
  }, [position]);

  const triggerEasterEgg = useCallback(() => {
    setIsEasterEggActive(true);
    setIsDancing(true);
    setEmotion('happy');
    setPose('waving');
    
    const easterQuote = getRandomQuote('happy', true);
    setQuote(easterQuote);
    onQuoteShow?.(easterQuote);
    onEasterEggTrigger?.();

    setTimeout(() => {
      setIsDancing(false);
      setIsEasterEggActive(false);
    }, 3000);
  }, [onQuoteShow, onEasterEggTrigger]);

  const handleClick = useCallback(() => {
    clickCountRef.current += 1;

    if (clickTimerRef.current) {
      clearTimeout(clickTimerRef.current);
    }

    clickTimerRef.current = setTimeout(() => {
      if (clickCountRef.current >= EASTER_EGG_THRESHOLD && !isEasterEggActive) {
        triggerEasterEgg();
      } else if (clickCountRef.current < EASTER_EGG_THRESHOLD) {
        const newEmotion = getRandomItem(emotions);
        const newPose = Math.random() > 0.5 ? getRandomItem(poses) : undefined;
        
        setEmotion(newEmotion);
        setPose(newPose);
        
        const newQuote = getRandomQuote(newEmotion, false);
        setQuote(newQuote);
        onQuoteShow?.(newQuote);
      }
      
      clickCountRef.current = 0;
    }, CLICK_TIMEOUT);
  }, [isEasterEggActive, triggerEasterEgg, onQuoteShow]);

  const handleDragEnd = useCallback((_: unknown, info: PanInfo) => {
    const newX = position.x + info.offset.x;
    const newY = position.y + info.offset.y;
    
    const maxX = window.innerWidth - 150;
    const maxY = window.innerHeight - 150;
    
    setPosition({
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY)),
    });
  }, [position]);

  const handleDismissQuote = useCallback(() => {
    setQuote(null);
  }, []);

  return (
    <div 
      ref={constraintsRef}
      className={`interactive-mascot-container ${className}`}
      style={{
        position: 'fixed',
        zIndex: 9999,
        pointerEvents: 'none',
      }}
    >
      <motion.div
        drag={draggable}
        dragControls={dragControls}
        dragMomentum={false}
        dragElastic={0}
        onDragEnd={handleDragEnd}
        style={{
          position: 'fixed',
          left: position.x,
          top: position.y,
          pointerEvents: 'auto',
          cursor: draggable ? 'grab' : 'pointer',
        }}
        whileDrag={{ cursor: 'grabbing', scale: 1.05 }}
        animate={isDancing ? danceAnimation : {}}
      >
        <div className="relative">
          <Mascot
            emotion={emotion}
            pose={pose}
            size={size}
            onClick={handleClick}
            animate={!isDancing}
          />

          <AnimatePresence>
            {quote && showQuoteBubble && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: 10 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className="absolute left-full ml-3 top-1/2 -translate-y-1/2"
              >
                <div className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-3 max-w-xs">
                  <div className="absolute left-0 top-1/2 -translate-x-2 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-r-8 border-transparent border-r-white dark:border-r-gray-800" />
                  
                  <p className="text-sm text-gray-700 dark:text-gray-200 pr-6">
                    {quote}
                  </p>
                  
                  <button
                    onClick={handleDismissQuote}
                    className="absolute top-1 right-1 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                    aria-label="关闭"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {isEasterEggActive && (
              <motion.div
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0 }}
                className="absolute -top-4 -right-4"
              >
                <motion.div
                  animate={{
                    rotate: [0, 360],
                    scale: [1, 1.2, 1],
                  }}
                  transition={{
                    rotate: { duration: 2, repeat: Infinity, ease: 'linear' },
                    scale: { duration: 0.5, repeat: Infinity },
                  }}
                  className="text-2xl"
                >
                  ✨
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

interface MascotWithAnimationProps extends MascotProps {
  animationType?: 'breathe' | 'float' | 'nod' | 'none';
}

export const MascotWithAnimation: React.FC<MascotWithAnimationProps> = ({
  animationType = 'breathe',
  ...props
}) => {
  const animations = {
    breathe: breatheAnimation,
    float: floatAnimation,
    nod: {
      rotate: [0, 8, -4, 0],
      transition: {
        duration: 0.6,
        ease: 'easeInOut',
      },
    },
    none: {},
  };

  return (
    <motion.div
      animate={animations[animationType]}
      style={{ display: 'inline-flex' }}
    >
      <Mascot {...props} animate={animationType !== 'none'} />
    </motion.div>
  );
};

interface MascotEmptyStateProps {
  title: string;
  description?: string;
  emotion?: MascotEmotion;
  action?: React.ReactNode;
}

export const MascotEmptyState: React.FC<MascotEmptyStateProps> = ({
  title,
  description,
  emotion = 'confused',
  action,
}) => {
  return (
    <motion.div
      className="mascot-empty-state"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Mascot emotion={emotion} size="xl" animate />
      <motion.div
        style={{
          fontSize: '18px',
          fontWeight: 600,
          color: 'var(--color-neutral-700, #374151)',
          marginTop: '16px',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        {title}
      </motion.div>
      {description && (
        <motion.div
          style={{
            fontSize: '14px',
            color: 'var(--color-neutral-500, #64748B)',
            maxWidth: '280px',
            marginTop: '8px',
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {description}
        </motion.div>
      )}
      {action && (
        <motion.div
          style={{ marginTop: '16px' }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          {action}
        </motion.div>
      )}
    </motion.div>
  );
};

interface MascotLoadingProps {
  message?: string;
  size?: MascotSize;
}

export const MascotLoading: React.FC<MascotLoadingProps> = ({
  message = '正在处理...',
  size = 'lg',
}) => {
  return (
    <motion.div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <Mascot emotion="thinking" size={size} animate />
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary-600, #1D4ED8)',
            }}
            animate={{
              scale: [0.6, 1, 0.6],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.4,
              repeat: Infinity,
              delay: i * 0.16,
            }}
          />
        ))}
      </div>
      <span style={{ color: 'var(--color-neutral-600, #4B5563)' }}>
        {message}
      </span>
    </motion.div>
  );
};

interface MascotSuccessProps {
  message?: string;
  size?: MascotSize;
  onComplete?: () => void;
  duration?: number;
}

export const MascotSuccess: React.FC<MascotSuccessProps> = ({
  message = '操作成功！',
  size = 'md',
  onComplete,
  duration = 2000,
}) => {
  useEffect(() => {
    if (onComplete) {
      const timer = setTimeout(onComplete, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onComplete]);

  return (
    <motion.div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '16px',
        backgroundColor: '#ECFDF5',
        borderRadius: '8px',
        border: '1px solid #A7F3D0',
      }}
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: -10 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
    >
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, -5, 5, 0],
        }}
        transition={{ duration: 0.5 }}
      >
        <Mascot emotion="happy" size={size} animate={false} />
      </motion.div>
      <span style={{ color: '#065F46', fontWeight: 500 }}>{message}</span>
    </motion.div>
  );
};

interface MascotErrorProps {
  message?: string;
  suggestion?: string;
  onRetry?: () => void;
  size?: MascotSize;
}

export const MascotError: React.FC<MascotErrorProps> = ({
  message = '出错了',
  suggestion,
  onRetry,
  size = 'lg',
}) => {
  return (
    <motion.div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        padding: '24px',
        backgroundColor: '#FEF2F2',
        borderRadius: '12px',
        border: '1px solid #FECACA',
        textAlign: 'center',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Mascot emotion="comforting" size={size} animate />
      <div style={{ color: '#991B1B', fontWeight: 500 }}>{message}</div>
      {suggestion && (
        <div style={{ color: '#6B7280', fontSize: '14px' }}>{suggestion}</div>
      )}
      {onRetry && (
        <motion.button
          onClick={onRetry}
          style={{
            marginTop: '8px',
            padding: '8px 16px',
            backgroundColor: '#1D4ED8',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
          whileHover={{ backgroundColor: '#1E40AF' }}
          whileTap={{ scale: 0.95 }}
        >
          重试
        </motion.button>
      )}
    </motion.div>
  );
};

interface MascotWelcomeProps {
  username?: string;
  onStart?: () => void;
}

export const MascotWelcome: React.FC<MascotWelcomeProps> = ({
  username,
  onStart,
}) => {
  return (
    <motion.div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px',
        padding: '48px 24px',
        textAlign: 'center',
      }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <motion.div
        animate={floatAnimation}
      >
        <Mascot pose="waving" size="xl" animate={false} />
      </motion.div>
      <motion.div
        style={{ fontSize: '24px', fontWeight: 600, color: '#111827' }}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        你好{username ? `，${username}` : ''}！
      </motion.div>
      <motion.div
        style={{ fontSize: '16px', color: '#6B7280', maxWidth: '320px' }}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        我是房小智，你的智能房产助手。让我来帮你进行房产分析吧！
      </motion.div>
      {onStart && (
        <motion.button
          onClick={onStart}
          style={{
            marginTop: '16px',
            padding: '12px 32px',
            backgroundColor: '#1D4ED8',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 500,
            fontSize: '16px',
          }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          whileHover={{ backgroundColor: '#1E40AF', scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          开始使用
        </motion.button>
      )}
    </motion.div>
  );
};

interface MascotHelperProps {
  tip: string;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  onDismiss?: () => void;
  emotion?: MascotEmotion;
}

export const MascotHelper: React.FC<MascotHelperProps> = ({
  tip,
  position = 'bottom-right',
  onDismiss,
  emotion = 'default',
}) => {
  const [dismissed, setDismissed] = useState(false);

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  const positionStyles: Record<string, React.CSSProperties> = {
    'bottom-right': { bottom: '24px', right: '24px' },
    'bottom-left': { bottom: '24px', left: '24px' },
    'top-right': { top: '24px', right: '24px' },
    'top-left': { top: '24px', left: '24px' },
  };

  return (
    <AnimatePresence>
      {!dismissed && (
        <motion.div
          style={{
            position: 'fixed',
            ...positionStyles[position],
            display: 'flex',
            alignItems: 'flex-end',
            gap: '12px',
            zIndex: 100,
          }}
          initial={{ opacity: 0, y: 20, x: position.includes('right') ? 20 : -20 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, y: 20, x: position.includes('right') ? 20 : -20 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        >
          <motion.div
            style={{
              backgroundColor: 'white',
              padding: '12px 16px',
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              maxWidth: '280px',
              position: 'relative',
            }}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <motion.button
              onClick={handleDismiss}
              style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#9CA3AF',
                fontSize: '16px',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              whileHover={{ color: '#6B7280', scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              ×
            </motion.button>
            <p style={{ margin: 0, fontSize: '14px', color: '#374151', paddingRight: '16px' }}>
              {tip}
            </p>
          </motion.div>
          <Mascot emotion={emotion} size="md" animate onClick={handleDismiss} />
        </motion.div>
      )}
    </AnimatePresence>
  );
};
