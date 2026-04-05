import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, ArrowPathIcon, ArrowRightIcon } from '@heroicons/react/24/outline';
import Mascot, { MascotEmotion, MascotPose, MascotSize } from './Mascot';

export type MascotToastType = 
  | 'success' 
  | 'report-complete' 
  | 'feedback-sent' 
  | 'task-deleted' 
  | 'network-error'
  | 'server-error'
  | 'auth-error'
  | 'not-found'
  | 'custom';

interface MascotToastConfig {
  emotion: MascotEmotion;
  pose?: MascotPose;
  message: string;
  duration: number;
  bgColor?: string;
  borderColor?: string;
}

const defaultConfigs: Record<MascotToastType, MascotToastConfig> = {
  'success': {
    emotion: 'happy',
    message: '操作成功！',
    duration: 3000,
  },
  'report-complete': {
    emotion: 'happy',
    pose: 'waving',
    message: '分析完成！这是为你生成的报告',
    duration: 4000,
  },
  'feedback-sent': {
    emotion: 'happy',
    pose: 'waving',
    message: '感谢你的反馈，我们会尽快处理',
    duration: 3000,
  },
  'task-deleted': {
    emotion: 'default',
    message: '任务已删除',
    duration: 2500,
  },
  'network-error': {
    emotion: 'confused',
    message: '网络开小差了，请检查连接后重试',
    duration: 5000,
    bgColor: 'bg-orange-50 dark:bg-orange-900/20',
    borderColor: 'border-orange-200 dark:border-orange-800',
  },
  'server-error': {
    emotion: 'comforting',
    message: '服务器遇到点问题，我们已收到通知，请稍后再试',
    duration: 5000,
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-200 dark:border-red-800',
  },
  'auth-error': {
    emotion: 'default',
    pose: 'pointing',
    message: '需要登录才能继续操作哦',
    duration: 4000,
    bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
  },
  'not-found': {
    emotion: 'confused',
    message: '页面迷路了，回首页看看吧',
    duration: 5000,
    bgColor: 'bg-gray-50 dark:bg-gray-800',
    borderColor: 'border-gray-200 dark:border-gray-700',
  },
  'custom': {
    emotion: 'happy',
    message: '',
    duration: 3000,
  },
};

interface MascotToastItem {
  id: string;
  type: MascotToastType;
  message?: string;
  emotion?: MascotEmotion;
  pose?: MascotPose;
  size?: MascotSize;
  duration?: number;
  showClose?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface MascotToastContextValue {
  showToast: (toast: Omit<MascotToastItem, 'id'>) => void;
  showSuccess: (message?: string) => void;
  showReportComplete: () => void;
  showFeedbackSent: () => void;
  showTaskDeleted: () => void;
  showNetworkError: (onRetry?: () => void) => void;
  showServerError: () => void;
  showAuthError: (onLogin?: () => void) => void;
  showNotFound: (onGoHome?: () => void) => void;
  dismissToast: (id: string) => void;
  dismissAll: () => void;
}

const MascotToastContext = createContext<MascotToastContextValue | null>(null);

export const useMascotToast = () => {
  const context = useContext(MascotToastContext);
  if (!context) {
    throw new Error('useMascotToast must be used within a MascotToastProvider');
  }
  return context;
};

interface MascotToastProviderProps {
  children: ReactNode;
  position?: 'top-center' | 'top-right' | 'bottom-right' | 'bottom-center';
}

export const MascotToastProvider: React.FC<MascotToastProviderProps> = ({
  children,
  position = 'top-center',
}) => {
  const [toasts, setToasts] = useState<MascotToastItem[]>([]);

  const showToast = useCallback((toast: Omit<MascotToastItem, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: MascotToastItem = { ...toast, id };
    
    setToasts((prev) => [...prev, newToast]);

    const duration = toast.duration ?? defaultConfigs[toast.type].duration;
    if (duration > 0) {
      setTimeout(() => {
        dismissToast(id);
      }, duration);
    }

    return id;
  }, []);

  const showSuccess = useCallback((message?: string) => {
    showToast({ type: 'success', message });
  }, [showToast]);

  const showReportComplete = useCallback(() => {
    showToast({ type: 'report-complete' });
  }, [showToast]);

  const showFeedbackSent = useCallback(() => {
    showToast({ type: 'feedback-sent' });
  }, [showToast]);

  const showTaskDeleted = useCallback(() => {
    showToast({ type: 'task-deleted' });
  }, [showToast]);

  const showNetworkError = useCallback((onRetry?: () => void) => {
    showToast({
      type: 'network-error',
      action: onRetry ? {
        label: '重试',
        onClick: onRetry,
      } : undefined,
    });
  }, [showToast]);

  const showServerError = useCallback(() => {
    showToast({ type: 'server-error' });
  }, [showToast]);

  const showAuthError = useCallback((onLogin?: () => void) => {
    showToast({
      type: 'auth-error',
      action: onLogin ? {
        label: '去登录',
        onClick: onLogin,
      } : undefined,
    });
  }, [showToast]);

  const showNotFound = useCallback((onGoHome?: () => void) => {
    showToast({
      type: 'not-found',
      action: onGoHome ? {
        label: '回首页',
        onClick: onGoHome,
      } : undefined,
    });
  }, [showToast]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setToasts([]);
  }, []);

  const getPositionStyles = (): React.CSSProperties => {
    switch (position) {
      case 'top-center':
        return { top: '24px', left: '50%', transform: 'translateX(-50%)' };
      case 'top-right':
        return { top: '24px', right: '24px' };
      case 'bottom-right':
        return { bottom: '24px', right: '24px' };
      case 'bottom-center':
        return { bottom: '24px', left: '50%', transform: 'translateX(-50%)' };
      default:
        return { top: '24px', left: '50%', transform: 'translateX(-50%)' };
    }
  };

  return (
    <MascotToastContext.Provider
      value={{
        showToast,
        showSuccess,
        showReportComplete,
        showFeedbackSent,
        showTaskDeleted,
        showNetworkError,
        showServerError,
        showAuthError,
        showNotFound,
        dismissToast,
        dismissAll,
      }}
    >
      {children}
      <div
        className="fixed z-[9999] flex flex-col gap-3 pointer-events-none"
        style={getPositionStyles()}
      >
        <AnimatePresence>
          {toasts.map((toast) => {
            const config = defaultConfigs[toast.type];
            const emotion = toast.emotion ?? config.emotion;
            const pose = toast.pose ?? config.pose;
            const message = toast.message ?? config.message;
            const size = toast.size ?? 'md';

            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, y: -20, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.9 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className="pointer-events-auto"
              >
                <div className={`${config.bgColor || 'bg-white dark:bg-gray-800'} rounded-2xl shadow-xl border ${config.borderColor || 'border-gray-100 dark:border-gray-700'} p-4 max-w-sm`}>
                  <div className="flex items-start gap-3">
                    <motion.div
                      animate={{ y: [0, -4, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                    >
                      <Mascot
                        emotion={emotion}
                        pose={pose}
                        size={size}
                        animate
                      />
                    </motion.div>

                    <div className="flex-1 min-w-0">
                      <motion.div
                        className="bg-white/80 dark:bg-gray-700/80 rounded-xl px-3 py-2 relative"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.1 }}
                      >
                        <div className="absolute left-0 top-1/2 -translate-x-2 -translate-y-1/2 w-0 h-0 border-t-6 border-b-6 border-r-8 border-transparent border-r-white/80 dark:border-r-gray-700/80" />
                        <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">
                          {message}
                        </p>
                      </motion.div>

                      {toast.action && (
                        <motion.button
                          onClick={toast.action.onClick}
                          className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.2 }}
                        >
                          {toast.action.label}
                          {toast.type === 'network-error' && <ArrowPathIcon className="w-3 h-3" />}
                          {(toast.type === 'auth-error' || toast.type === 'not-found') && <ArrowRightIcon className="w-3 h-3" />}
                        </motion.button>
                      )}
                    </div>

                    {toast.showClose !== false && (
                      <button
                        onClick={() => dismissToast(toast.id)}
                        className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </MascotToastContext.Provider>
  );
};

export default MascotToastProvider;

export const mascotToast = {
  success: (message?: string) => {
    console.log('MascotToast: success -', message);
  },
  reportComplete: () => {
    console.log('MascotToast: report complete');
  },
  feedbackSent: () => {
    console.log('MascotToast: feedback sent');
  },
  taskDeleted: () => {
    console.log('MascotToast: task deleted');
  },
  networkError: (onRetry?: () => void) => {
    console.log('MascotToast: network error');
  },
  serverError: () => {
    console.log('MascotToast: server error');
  },
  authError: (onLogin?: () => void) => {
    console.log('MascotToast: auth error');
  },
  notFound: (onGoHome?: () => void) => {
    console.log('MascotToast: not found');
  },
};
