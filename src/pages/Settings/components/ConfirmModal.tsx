import { motion, AnimatePresence } from 'framer-motion';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
  isDanger?: boolean;
  confirmText?: string;
  cancelText?: string;
}

export function ConfirmModal({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  isPending,
  isDanger = false,
  confirmText = '确认',
  cancelText = '取消',
}: ConfirmModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onCancel}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
              w-full max-w-md p-6 rounded-xl bg-slate-800 border border-slate-700 shadow-2xl"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-modal-title"
            aria-describedby="confirm-modal-description"
          >
            <h2
              id="confirm-modal-title"
              className="text-lg font-semibold text-white mb-2"
            >
              {title}
            </h2>

            <p
              id="confirm-modal-description"
              className="text-gray-400 mb-6"
            >
              {message}
            </p>

            <div className="flex justify-end gap-3">
              <button
                onClick={onCancel}
                disabled={isPending}
                className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300
                  hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {cancelText}
              </button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onConfirm}
                disabled={isPending}
                className={`px-4 py-2 rounded-lg font-medium transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed ${
                    isDanger
                      ? 'bg-red-500 text-white hover:bg-red-400'
                      : 'bg-amber-500 text-slate-900 hover:bg-amber-400'
                  }`}
              >
                {isPending ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    处理中...
                  </span>
                ) : (
                  confirmText
                )}
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
