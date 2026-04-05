import { motion } from 'framer-motion';

interface FloatingButtonProps {
  onClick: () => void;
  hasUnread: boolean;
  unreadCount?: number;
}

export function FloatingButton({ onClick, hasUnread, unreadCount = 0 }: FloatingButtonProps) {
  return (
    <motion.button
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="fixed bottom-6 right-6 w-14 h-14 rounded-full
        bg-gradient-to-br from-amber-400 to-amber-600
        shadow-lg shadow-amber-500/30
        flex items-center justify-center
        cursor-pointer z-50
        hover:shadow-xl hover:shadow-amber-500/40
        transition-shadow duration-300"
      aria-label="打开智能体活动面板"
    >
      <span className="text-2xl">🤖</span>

      {hasUnread && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-1 -right-1 min-w-[20px] h-5 px-1.5
            bg-red-500 rounded-full flex items-center justify-center"
        >
          {unreadCount > 0 && (
            <span className="text-white text-xs font-bold">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </motion.div>
      )}

      <motion.div
        animate={{
          boxShadow: [
            '0 0 0 0 rgba(245, 158, 11, 0.4)',
            '0 0 0 8px rgba(245, 158, 11, 0)',
          ],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeOut',
        }}
        className="absolute inset-0 rounded-full pointer-events-none"
      />
    </motion.button>
  );
}
