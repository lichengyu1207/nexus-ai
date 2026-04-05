import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Mascot, { MascotEmotion, MascotSize } from './Mascot';

export type LoadingPhase = 'initial' | 'processing' | 'extended' | 'completed';

interface LoadingMessage {
  text: string;
  duration: number;
}

interface LoadingWithMascotProps {
  phase?: LoadingPhase;
  progress?: number;
  messages?: LoadingMessage[];
  extendedThreshold?: number;
  size?: MascotSize;
  onComplete?: () => void;
  showProgress?: boolean;
  className?: string;
}

const defaultMessages: Record<LoadingPhase, LoadingMessage[]> = {
  initial: [
    { text: '正在召唤智能体团队...', duration: 2000 },
    { text: '准备分析环境...', duration: 1500 },
  ],
  processing: [
    { text: '数据采集中，请稍候...', duration: 2500 },
    { text: '市场分析师正在努力工作...', duration: 3000 },
    { text: '正在整合多源数据...', duration: 2500 },
    { text: 'AI模型推理中...', duration: 2000 },
    { text: '生成分析报告中...', duration: 2500 },
  ],
  extended: [
    { text: '数据量有点大，再等一下下～', duration: 3000 },
    { text: '正在处理复杂数据...', duration: 2500 },
    { text: '马上就好，请耐心等待...', duration: 2000 },
  ],
  completed: [
    { text: '完成啦！点击查看报告', duration: 0 },
  ],
};

const LoadingWithMascot: React.FC<LoadingWithMascotProps> = ({
  phase = 'initial',
  progress = 0,
  messages,
  extendedThreshold = 10,
  size = 'xl',
  onComplete,
  showProgress = true,
  className = '',
}) => {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentPhase, setCurrentPhase] = useState<LoadingPhase>(phase);

  const currentMessages = messages || defaultMessages[currentPhase];

  useEffect(() => {
    setCurrentPhase(phase);
    setCurrentMessageIndex(0);
  }, [phase]);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (elapsedTime >= extendedThreshold && currentPhase === 'processing') {
      setCurrentPhase('extended');
      setCurrentMessageIndex(0);
    }
  }, [elapsedTime, extendedThreshold, currentPhase]);

  useEffect(() => {
    if (currentMessages.length <= 1) return;

    const currentMsg = currentMessages[currentMessageIndex];
    if (currentMsg.duration === 0) return;

    const timer = setTimeout(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % currentMessages.length);
    }, currentMsg.duration);

    return () => clearTimeout(timer);
  }, [currentMessageIndex, currentMessages]);

  const getEmotion = (): MascotEmotion => {
    switch (currentPhase) {
      case 'initial':
        return 'thinking';
      case 'processing':
        return 'thinking';
      case 'extended':
        return 'comforting';
      case 'completed':
        return 'happy';
      default:
        return 'thinking';
    }
  };

  const getAnimationType = () => {
    switch (currentPhase) {
      case 'initial':
      case 'processing':
        return 'pulse';
      case 'extended':
        return 'float';
      case 'completed':
        return 'bounce';
      default:
        return 'pulse';
    }
  };

  const handleMascotClick = () => {
    if (currentPhase === 'completed' && onComplete) {
      onComplete();
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      className={`flex flex-col items-center justify-center py-8 px-4 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-start gap-4 max-w-md">
        <motion.div
          animate={getAnimationType() === 'float' ? { y: [0, -8, 0] } : { scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Mascot
            emotion={getEmotion()}
            size={size}
            animate
            onClick={currentPhase === 'completed' ? handleMascotClick : undefined}
          />
        </motion.div>

        <div className="flex-1 pt-2">
          <motion.div
            key={`${currentPhase}-${currentMessageIndex}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm relative"
          >
            <div className="absolute left-0 top-1/2 -translate-x-2 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-r-8 border-transparent border-r-white" />
            <div className="absolute left-0 top-1/2 -translate-x-2.5 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-r-8 border-transparent border-r-gray-200" />
            
            <p className="text-sm text-gray-700 leading-relaxed">
              {currentMessages[currentMessageIndex]?.text}
            </p>

            {showProgress && currentPhase !== 'completed' && (
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>处理进度</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-primary-600 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}

            {currentPhase !== 'completed' && (
              <div className="mt-2 text-xs text-gray-400 flex items-center gap-1">
                <motion.div
                  className="w-2 h-2 bg-primary-500 rounded-full"
                  animate={{ scale: [1, 1.2, 1], opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
                <span>已用时 {formatTime(elapsedTime)}</span>
              </div>
            )}
          </motion.div>

          {currentPhase === 'completed' && onComplete && (
            <motion.button
              onClick={onComplete}
              className="mt-3 w-full py-2 px-4 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              查看报告
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default LoadingWithMascot;

interface TaskLoadingWithMascotProps {
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  taskName?: string;
  onComplete?: () => void;
  size?: MascotSize;
}

export const TaskLoadingWithMascot: React.FC<TaskLoadingWithMascotProps> = ({
  status,
  progress = 0,
  taskName,
  onComplete,
  size = 'xl',
}) => {
  const [phase, setPhase] = useState<LoadingPhase>('initial');
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    setElapsedTime(0);
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (status === 'completed') {
      setPhase('completed');
    } else if (status === 'running') {
      if (elapsedTime >= 10) {
        setPhase('extended');
      } else {
        setPhase('processing');
      }
    } else {
      setPhase('initial');
    }
  }, [status, elapsedTime]);

  const messages: LoadingMessage[] = status === 'completed'
    ? [{ text: '完成啦！点击查看报告', duration: 0 }]
    : status === 'running'
      ? elapsedTime >= 10
        ? [
            { text: '数据量有点大，再等一下下～', duration: 3000 },
            { text: '正在处理复杂数据...', duration: 2500 },
            { text: '马上就好，请耐心等待...', duration: 2000 },
          ]
        : [
            { text: '正在召唤智能体团队...', duration: 2000 },
            { text: '数据采集中，请稍候...', duration: 2500 },
            { text: '市场分析师正在努力工作...', duration: 3000 },
            { text: '正在整合多源数据...', duration: 2500 },
            { text: 'AI模型推理中...', duration: 2000 },
          ]
      : [
          { text: '准备开始分析...', duration: 1500 },
          { text: '初始化智能体...', duration: 2000 },
        ];

  return (
    <div className="w-full">
      {taskName && (
        <div className="text-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">{taskName}</h3>
        </div>
      )}
      <LoadingWithMascot
        phase={phase}
        progress={progress}
        messages={messages}
        size={size}
        onComplete={onComplete}
        showProgress={status === 'running'}
      />
    </div>
  );
};

interface CompactLoadingWithMascotProps {
  message?: string;
  emotion?: MascotEmotion;
  size?: MascotSize;
  showDots?: boolean;
}

export const CompactLoadingWithMascot: React.FC<CompactLoadingWithMascotProps> = ({
  message = '处理中...',
  emotion = 'thinking',
  size = 'md',
  showDots = true,
}) => {
  return (
    <motion.div
      className="flex items-center gap-3 py-3 px-4 bg-gray-50 rounded-xl"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <Mascot emotion={emotion} size={size} animate />
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">{message}</span>
        {showDots && (
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-1.5 h-1.5 bg-primary-500 rounded-full"
                animate={{ scale: [0.6, 1, 0.6], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.16 }}
              />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

interface InlineLoadingWithMascotProps {
  message?: string;
  size?: MascotSize;
}

export const InlineLoadingWithMascot: React.FC<InlineLoadingWithMascotProps> = ({
  message = '加载中...',
  size = 'sm',
}) => {
  return (
    <motion.div
      className="flex items-center justify-center gap-2 py-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <Mascot emotion="thinking" size={size} animate />
      <span className="text-sm text-gray-500">{message}</span>
    </motion.div>
  );
};
