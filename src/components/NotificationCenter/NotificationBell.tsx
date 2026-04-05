import { motion, AnimatePresence } from 'framer-motion';
import { BellIcon } from '@heroicons/react/24/outline';

export interface NotificationBellProps {
  onClick: () => void;
  unreadCount: number;
  isShaking?: boolean;
}

export function NotificationBell({
  onClick,
  unreadCount,
  isShaking = false,
}: NotificationBellProps) {
  const displayCount = unreadCount > 99 ? '99+' : unreadCount;

  return (
    <motion.button
      onClick={onClick}
      className="relative p-2 rounded-lg hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500/50"
      aria-label={`通知，未读数量 ${unreadCount}`}
      animate={isShaking ? { rotate: [0, -15, 15, -10, 10, -5, 5, 0] } : {}}
      transition={isShaking ? { duration: 0.5 } : {}}
    >
      <BellIcon className="w-6 h-6 text-amber-400" />

      <AnimatePresence>
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full px-1"
          >
            {displayCount}
          </motion.span>
        )}
      </AnimatePresence>

      {unreadCount > 0 && (
        <motion.span
          className="absolute -top-1 -right-1 w-[18px] h-[18px] rounded-full bg-red-500"
          initial={{ scale: 1, opacity: 0.5 }}
          animate={{ scale: 1.5, opacity: 0 }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}
    </motion.button>
  );
}
