import { motion } from 'framer-motion';
import type { QueueTask, QueueTaskStatus } from '../types';

interface TaskQueueListProps {
  tasks: QueueTask[];
}

const statusConfig: Record<QueueTaskStatus, { label: string; color: string; bgColor: string }> = {
  pending: { label: '排队中', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' },
  processing: { label: '进行中', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
};

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

export function TaskQueueList({ tasks }: TaskQueueListProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        队列为空
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.slice(0, 10).map((task, index) => {
        const config = statusConfig[task.status];
        return (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-3 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <p className="text-white text-sm font-medium truncate flex-1">
                {task.name}
              </p>
              <span className={`px-2 py-0.5 rounded text-xs ${config.bgColor} ${config.color}`}>
                {config.label}
              </span>
            </div>

            {task.progress !== undefined && task.status === 'processing' && (
              <div className="mb-2">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>进度</span>
                  <span>{task.progress}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${task.progress}%` }}
                    className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
                  />
                </div>
              </div>
            )}

            {task.startTime && (
              <p className="text-xs text-gray-500">
                开始时间: {formatTime(task.startTime)}
              </p>
            )}
          </motion.div>
        );
      })}

      {tasks.length > 10 && (
        <p className="text-center text-xs text-gray-500 py-2">
          还有 {tasks.length - 10} 个任务...
        </p>
      )}
    </div>
  );
}
