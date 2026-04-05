import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, SparklesIcon, ArrowRightIcon } from '@heroicons/react/24/outline';
import Mascot, { MascotEmotion } from './Mascot';

export type ReminderType = 'idle' | 'daily-greeting' | 'new-feature' | 'help-offer';

interface ReminderConfig {
  type: ReminderType;
  message: string;
  emotion?: 'default' | 'thinking' | 'happy' | 'confused' | 'surprised' | 'comforting';
  pose?: 'standing' | 'sitting' | 'waving' | 'pointing';
  actionLabel?: string;
  actionUrl?: string;
  cooldownHours: number;
}

const reminderConfigs: Record<ReminderType, ReminderConfig> = {
  'idle': {
    type: 'idle',
    message: '需要帮助吗？点击我问问小智～',
    emotion: 'default',
    pose: 'standing',
    actionLabel: '开始对话',
    cooldownHours: 2,
  },
  'daily-greeting': {
    type: 'daily-greeting',
    message: '早上好！今天想分析哪里的房产？',
    emotion: 'happy',
    pose: 'waving',
    actionLabel: '开始分析',
    actionUrl: '/dashboard',
    cooldownHours: 24,
  },
  'new-feature': {
    type: 'new-feature',
    message: '有新功能上线啦，快来看看～',
    emotion: 'happy',
    pose: 'waving',
    actionLabel: '查看详情',
    cooldownHours: 24,
  },
  'help-offer': {
    type: 'help-offer',
    message: '看起来你遇到了一些问题，需要帮助吗？',
    emotion: 'thinking',
    pose: 'pointing',
    actionLabel: '查看帮助',
    actionUrl: '/help',
    cooldownHours: 4,
  },
};

const STORAGE_PREFIX = 'mascot_reminder_';

const getStorageKey = (type: ReminderType) => `${STORAGE_PREFIX}${type}`;

const getLastShownTime = (type: ReminderType): number => {
  try {
    const stored = localStorage.getItem(getStorageKey(type));
    return stored ? parseInt(stored, 10) : 0;
  } catch {
    return 0;
  }
};

const setLastShownTime = (type: ReminderType) => {
  try {
    localStorage.setItem(getStorageKey(type), Date.now().toString());
  } catch {
    // Ignore storage errors
  }
};

const shouldShowReminder = (type: ReminderType, cooldownHours: number): boolean => {
  if (cooldownHours <= 0) return true;
  const lastShown = getLastShownTime(type);
  const cooldownMs = cooldownHours * 60 * 60 * 1000;
  return Date.now() - lastShown > cooldownMs;
};

interface ActiveReminderProps {
  type: ReminderType;
  customMessage?: string;
  customAction?: {
    label: string;
    onClick: () => void;
  };
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  onDismiss?: () => void;
  onAction?: () => void;
  showCloseButton?: boolean;
}

export const ActiveReminder: React.FC<ActiveReminderProps> = ({
  type,
  customMessage,
  customAction,
  position = 'bottom-right',
  onDismiss,
  onAction,
  showCloseButton = true,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const config = reminderConfigs[type];

  useEffect(() => {
    if (shouldShowReminder(type, config.cooldownHours)) {
      const timer = setTimeout(() => {
        setIsVisible(true);
        setLastShownTime(type);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [type, config.cooldownHours]);

  const handleDismiss = useCallback(() => {
    setIsVisible(false);
    onDismiss?.();
  }, [onDismiss]);

  const handleAction = useCallback(() => {
    setIsVisible(false);
    onAction?.();
    if (customAction) {
      customAction.onClick();
    } else if (config.actionUrl) {
      window.location.href = config.actionUrl;
    }
  }, [onAction, customAction, config.actionUrl]);

  const getPositionStyles = (): React.CSSProperties => {
    const offset = '24px';
    switch (position) {
      case 'bottom-left':
        return { bottom: offset, left: offset };
      case 'top-right':
        return { top: '80px', right: offset };
      case 'top-left':
        return { top: '80px', left: offset };
      default:
        return { bottom: offset, right: offset };
    }
  };

  const message = customMessage || config.message;
  const actionLabel = customAction?.label || config.actionLabel;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed z-[9998] pointer-events-auto"
          style={getPositionStyles()}
          initial={{ opacity: 0, y: 20, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.9 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        >
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-4 max-w-xs">
            <div className="flex items-start gap-3">
              <motion.div
                animate={{ y: [0, -4, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                className="flex-shrink-0"
              >
                <Mascot
                  emotion={config.emotion}
                  pose={config.pose}
                  size="lg"
                  animate
                  onClick={handleAction}
                />
              </motion.div>

              <div className="flex-1 min-w-0">
                <div className="bg-gray-50 dark:bg-gray-700 rounded-xl px-3 py-2 relative">
                  <div className="absolute left-0 top-1/2 -translate-x-2 -translate-y-1/2 w-0 h-0 border-t-6 border-b-6 border-r-8 border-transparent border-r-gray-50 dark:border-r-gray-700" />
                  <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">
                    {message}
                  </p>
                </div>

                {actionLabel && (
                  <motion.button
                    onClick={handleAction}
                    className="mt-2 text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 flex items-center gap-1"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    {actionLabel}
                    <ArrowRightIcon className="w-3 h-3" />
                  </motion.button>
                )}
              </div>

              {showCloseButton && (
                <button
                  onClick={handleDismiss}
                  className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  aria-label="关闭提醒"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

interface IdleReminderProps {
  idleTimeout?: number;
  enabled?: boolean;
}

export const IdleReminder: React.FC<IdleReminderProps> = ({
  idleTimeout = 30000,
  enabled = true,
}) => {
  const [showReminder, setShowReminder] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const resetTimer = useCallback(() => {
    setShowReminder(false);
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => {
      if (shouldShowReminder('idle', 2)) {
        setShowReminder(true);
        setLastShownTime('idle');
      }
    }, idleTimeout);
  }, [idleTimeout]);

  useEffect(() => {
    if (!enabled) return;

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach((event) => {
      document.addEventListener(event, resetTimer, { passive: true });
    });

    resetTimer();

    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, resetTimer);
      });
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [enabled, resetTimer]);

  if (!showReminder) return null;

  return (
    <ActiveReminder
      type="idle"
      position="bottom-right"
      onDismiss={() => setShowReminder(false)}
      customAction={{
        label: '开始对话',
        onClick: () => {
          window.location.href = '/help';
        },
      }}
    />
  );
};

interface DailyGreetingProps {
  enabled?: boolean;
}

export const DailyGreeting: React.FC<DailyGreetingProps> = ({ enabled = true }) => {
  const [showGreeting, setShowGreeting] = useState(false);
  const [greetingMessage, setGreetingMessage] = useState('');

  useEffect(() => {
    if (!enabled) return;

    const today = new Date().toDateString();
    const lastGreetingDate = localStorage.getItem('mascot_greeting_date');

    if (lastGreetingDate !== today) {
      const hour = new Date().getHours();
      let message = '你好！';

      if (hour >= 5 && hour < 12) {
        message = '早上好！今天想分析哪里的房产？';
      } else if (hour >= 12 && hour < 18) {
        message = '下午好！有什么可以帮你的吗？';
      } else {
        message = '晚上好！今天还有其他需要分析的吗？';
      }

      setGreetingMessage(message);
      setShowGreeting(true);
      localStorage.setItem('mascot_greeting_date', today);
    }
  }, [enabled]);

  if (!showGreeting) return null;

  return (
    <ActiveReminder
      type="daily-greeting"
      customMessage={greetingMessage}
      position="bottom-right"
      onDismiss={() => setShowGreeting(false)}
    />
  );
};

interface NewFeatureReminderProps {
  featureId: string;
  message: string;
  actionUrl?: string;
  enabled?: boolean;
}

export const NewFeatureReminder: React.FC<NewFeatureReminderProps> = ({
  featureId,
  message,
  actionUrl,
  enabled = true,
}) => {
  const [showReminder, setShowReminder] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    const dismissedFeatures = JSON.parse(
      localStorage.getItem('mascot_dismissed_features') || '[]'
    );

    if (!dismissedFeatures.includes(featureId)) {
      setShowReminder(true);
    }
  }, [enabled, featureId]);

  const handleDismiss = () => {
    const dismissedFeatures = JSON.parse(
      localStorage.getItem('mascot_dismissed_features') || '[]'
    );
    dismissedFeatures.push(featureId);
    localStorage.setItem('mascot_dismissed_features', JSON.stringify(dismissedFeatures));
    setShowReminder(false);
  };

  if (!showReminder) return null;

  return (
    <ActiveReminder
      type="new-feature"
      customMessage={message}
      position="bottom-right"
      onDismiss={handleDismiss}
      customAction={actionUrl ? {
        label: '查看详情',
        onClick: () => {
          window.location.href = actionUrl;
        },
      } : undefined}
    />
  );
};

interface ActiveReminderManagerProps {
  enableIdleReminder?: boolean;
  enableDailyGreeting?: boolean;
  idleTimeout?: number;
  children?: React.ReactNode;
}

export const ActiveReminderManager: React.FC<ActiveReminderManagerProps> = ({
  enableIdleReminder = true,
  enableDailyGreeting = true,
  idleTimeout = 30000,
  children,
}) => {
  return (
    <>
      {children}
      <IdleReminder enabled={enableIdleReminder} idleTimeout={idleTimeout} />
      <DailyGreeting enabled={enableDailyGreeting} />
    </>
  );
};

export default ActiveReminder;
