import { motion, AnimatePresence } from 'framer-motion';
import type { BatchAction } from '../types';

interface BatchActionModalProps {
  isOpen: boolean;
  action: BatchAction;
  count: number;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
}

const actionConfig: Record<BatchAction, { title: string; description: string; confirmText: string; danger: boolean }> = {
  retry: {
    title: '批量重试',
    description: '确认重试选中的任务吗？',
    confirmText: '确认重试',
    danger: false,
  },
  delete: {
    title: '批量删除',
    description: '确认删除选中的任务吗？此操作不可恢复。',
    confirmText: '确认删除',
    danger: true,
  },
  export: {
    title: '批量导出',
    description: '确认导出选中的任务数据吗？',
    confirmText: '确认导出',
    danger: false,
  },
};

export function BatchActionModal({
  isOpen,
  action,
  count,
  onConfirm,
  onCancel,
  isPending,
}: BatchActionModalProps) {
  const config = actionConfig[action];

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
            aria-labelledby="batch-action-title"
            aria-describedby="batch-action-description"
          >
            <h2 id="batch-action-title" className="text-lg font-semibold text-white mb-2">
              {config.title}
            </h2>

            <p id="batch-action-description" className="text-gray-400 mb-2">
              {config.description}
            </p>

            <p className="text-amber-400 font-medium mb-6">
              已选择 {count} 个任务
            </p>

            <div className="flex justify-end gap-3">
              <button
                onClick={onCancel}
                disabled={isPending}
                className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300
                  hover:bg-slate-600 disabled:opacity-50 transition-colors"
              >
                取消
              </button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onConfirm}
                disabled={isPending}
                className={`px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50
                  ${config.danger
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
                  config.confirmText
                )}
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
