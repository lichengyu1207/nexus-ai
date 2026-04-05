import { useRef } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeftIcon, ChevronRightIcon, ClockIcon } from '@heroicons/react/24/outline';
import type { TaskSnapshot } from '../types';

interface TaskSnapshotListProps {
  tasks: TaskSnapshot[];
  onTaskClick?: (taskId: string) => void;
}

export function TaskSnapshotList({ tasks, onTaskClick }: TaskSnapshotListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = 320;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
    }
  };

  const formatRemaining = (estimatedEnd: string) => {
    const end = new Date(estimatedEnd);
    const now = new Date();
    const diff = end.getTime() - now.getTime();
    
    if (diff < 0) return '已超时';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) return `${hours}小时${minutes}分钟`;
    return `${minutes}分钟`;
  };

  if (tasks.length === 0) {
    return (
      <div className="bg-slate-800/30 rounded-xl border border-slate-700/50 p-6 text-center">
        <p className="text-slate-400">暂无进行中的任务</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">任务快照</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => scroll('left')}
            className="p-1.5 rounded-lg bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
          >
            <ChevronLeftIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="p-1.5 rounded-lg bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors"
          >
            <ChevronRightIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto scrollbar-hide pb-2"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {tasks.map((task, index) => (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onTaskClick?.(task.id)}
            className="
              flex-shrink-0 w-72 bg-slate-800/50 backdrop-blur-sm rounded-xl 
              border border-slate-700/50 p-4 cursor-pointer
              hover:border-amber-500/30 transition-all duration-200
            "
          >
            <div className="flex items-start justify-between mb-3">
              <h4 className="text-white font-medium truncate flex-1">{task.name}</h4>
              <span className="text-xs text-slate-400 ml-2">
                {Math.round(task.progress)}%
              </span>
            </div>

            <div className="mb-3">
              <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${task.progress}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="truncate">{task.currentAgent}</span>
              <span className="flex items-center gap-1">
                <ClockIcon className="w-3.5 h-3.5" />
                {formatRemaining(task.estimatedEnd)}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
