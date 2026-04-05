import { motion, AnimatePresence } from 'framer-motion';
import {
  SignalIcon,
  SignalSlashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

interface RealtimeIndicatorProps {
  isConnected: boolean;
  isReconnecting?: boolean;
  error?: string | null;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: {
    icon: 'w-3 h-3',
    text: 'text-xs',
    dot: 'w-1.5 h-1.5',
  },
  md: {
    icon: 'w-4 h-4',
    text: 'text-sm',
    dot: 'w-2 h-2',
  },
  lg: {
    icon: 'w-5 h-5',
    text: 'text-base',
    dot: 'w-2.5 h-2.5',
  },
};

export function RealtimeIndicator({
  isConnected,
  isReconnecting = false,
  error,
  showLabel = true,
  size = 'md',
  className = '',
}: RealtimeIndicatorProps) {
  const classes = sizeClasses[size];

  const getStatusColor = () => {
    if (isConnected) return 'bg-green-400';
    if (isReconnecting) return 'bg-yellow-400';
    return 'bg-red-400';
  };

  const getStatusText = () => {
    if (isConnected) return '已连接';
    if (isReconnecting) return '重连中...';
    if (error) return '连接失败';
    return '未连接';
  };

  const Icon = isConnected ? SignalIcon : isReconnecting ? ArrowPathIcon : SignalSlashIcon;

  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      role="status"
      aria-live="polite"
      aria-label={`实时连接状态: ${getStatusText()}`}
    >
      <div className="relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={isConnected ? 'connected' : isReconnecting ? 'reconnecting' : 'disconnected'}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Icon
              className={`${classes.icon} ${
                isConnected
                  ? 'text-green-400'
                  : isReconnecting
                  ? 'text-yellow-400 animate-spin'
                  : 'text-red-400'
              }`}
            />
          </motion.div>
        </AnimatePresence>

        <motion.div
          className={`absolute -top-0.5 -right-0.5 ${classes.dot} rounded-full ${getStatusColor()}`}
          animate={{
            scale: isConnected ? [1, 1.2, 1] : 1,
            opacity: isConnected ? [1, 0.7, 1] : 1,
          }}
          transition={{
            duration: 2,
            repeat: isConnected ? Infinity : 0,
            ease: 'easeInOut',
          }}
        />
      </div>

      {showLabel && (
        <span
          className={`${classes.text} ${
            isConnected
              ? 'text-green-400'
              : isReconnecting
              ? 'text-yellow-400'
              : 'text-red-400'
          } font-medium`}
        >
          {getStatusText()}
        </span>
      )}

      {error && !isConnected && !isReconnecting && (
        <motion.span
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className={`${classes.text} text-red-300 ml-1`}
          title={error}
        >
          ({error.length > 20 ? `${error.slice(0, 20)}...` : error})
        </motion.span>
      )}
    </div>
  );
}

export default RealtimeIndicator;
