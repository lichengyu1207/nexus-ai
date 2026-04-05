import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { CollaborationEvent } from '../types';

interface EventDetailModalProps {
  event: CollaborationEvent | null;
  isOpen: boolean;
  onClose: () => void;
  onProcess: (eventId: string) => void;
}

const endDisplayNames: Record<string, string> = {
  university: '院校端',
  enterprise: '企业端',
  government: '政府端',
  association: '协会端',
  public: '公众端',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500',
  processing: 'bg-blue-500',
  completed: 'bg-green-500',
};

const statusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
};

function formatFullTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function EventDetailModal({ event, isOpen, onClose, onProcess }: EventDetailModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const processButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        closeButtonRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!event) return null;

  const timeline = [
    { label: '创建时间', time: event.timestamp, status: 'completed' },
    ...(event.status !== 'pending'
      ? [{ label: '开始处理', time: event.timestamp, status: event.status }]
      : []),
    ...(event.status === 'completed'
      ? [{ label: '完成时间', time: event.timestamp, status: 'completed' }]
      : []),
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
            aria-hidden="true"
          />
          
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
              w-full max-w-lg p-6 rounded-2xl bg-slate-800 border border-slate-700 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="event-modal-title"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2
                  id="event-modal-title"
                  className="text-xl font-semibold text-white"
                >
                  事件详情
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`w-2 h-2 rounded-full ${statusColors[event.status]}`} />
                  <span className="text-sm text-gray-400">
                    {statusLabels[event.status]}
                  </span>
                </div>
              </div>
              <button
                ref={closeButtonRef}
                onClick={onClose}
                className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-slate-700
                  transition-colors"
                aria-label="关闭"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/50">
                <h3 className="text-white font-medium mb-2">{event.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  {event.description}
                </p>
              </div>

              <div className="flex items-center gap-4 p-3 rounded-lg bg-slate-900/30">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded text-xs bg-slate-700 text-gray-300">
                    {endDisplayNames[event.fromEnd]}
                  </span>
                  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                  <span className="px-2 py-1 rounded text-xs bg-slate-700 text-gray-300">
                    {endDisplayNames[event.toEnd]}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-400">时间线</h4>
                <div className="relative pl-4">
                  <div className="absolute left-1.5 top-0 bottom-0 w-0.5 bg-slate-700" />
                  {timeline.map((item, index) => (
                    <div key={index} className="relative flex items-start gap-3 mb-3">
                      <div className="absolute left-[-10px] w-3 h-3 rounded-full bg-amber-500 ring-2 ring-slate-800" />
                      <div>
                        <p className="text-white text-sm">{item.label}</p>
                        <p className="text-gray-500 text-xs">
                          {formatFullTimestamp(item.time)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {event.relatedTaskId && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <p className="text-sm text-gray-400 mb-1">关联任务</p>
                  <a
                    href={`/tasks/${event.relatedTaskId}`}
                    className="text-amber-400 hover:text-amber-300 text-sm underline"
                  >
                    查看任务详情 →
                  </a>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-700">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300 hover:bg-slate-600
                  transition-colors"
              >
                关闭
              </button>
              {event.actionable && event.status === 'pending' && (
                <button
                  ref={processButtonRef}
                  onClick={() => {
                    onProcess(event.id);
                    onClose();
                  }}
                  className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                    hover:bg-amber-400 transition-colors"
                >
                  处理事件
                </button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
