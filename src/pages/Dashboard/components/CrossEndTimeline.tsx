import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { CrossEndEvent } from '../types';

interface CrossEndTimelineProps {
  events: CrossEndEvent[];
  className?: string;
}

const eventVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0 },
};

const endColors: Record<string, string> = {
  bing: 'bg-blue-500',
  hu: 'bg-green-500',
  li: 'bg-purple-500',
  xing: 'bg-red-500',
  gong: 'bg-yellow-500',
  default: 'bg-gray-500',
};

const endLabels: Record<string, string> = {
  bing: '兵部',
  hu: '户部',
  li: '礼部',
  xing: '刑部',
  gong: '工部',
};

export const CrossEndTimeline: React.FC<CrossEndTimelineProps> = ({ events, className }) => {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (events.length === 0) {
    return (
      <div className={clsx('bg-bg-secondary/50 rounded-xl p-6 text-center', className)}>
        <p className="text-text-secondary">暂无协同动态</p>
      </div>
    );
  }

  return (
    <div className={clsx('bg-bg-secondary/50 rounded-xl p-4', className)}>
      <h3 className="text-lg font-semibold text-text-primary mb-4">五端协同动态</h3>
      <div className="relative">
        <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border-light" />
        <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
          {events.map((event, index) => (
            <motion.div
              key={event.id}
              variants={eventVariants}
              initial="hidden"
              animate="visible"
              transition={{ delay: index * 0.05 }}
              className="relative pl-8 group"
            >
              <div
                className={clsx(
                  'absolute left-2 top-1.5 w-3 h-3 rounded-full',
                  endColors[event.fromEnd] || endColors.default
                )}
              />

              <div className="bg-bg-tertiary/50 rounded-lg p-3 hover:bg-bg-tertiary/80 transition-colors cursor-pointer">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'text-xs px-1.5 py-0.5 rounded',
                      endColors[event.fromEnd] || endColors.default,
                      'text-white'
                    )}>
                      {endLabels[event.fromEnd] || event.fromEnd}
                    </span>
                    <svg className="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5-5m-5 5l5-5m0 0-5-5" />
                    </svg>
                    <span className={clsx(
                      'text-xs px-1.5 py-0.5 rounded',
                      endColors[event.toEnd] || endColors.default,
                      'text-white'
                    )}>
                      {endLabels[event.toEnd] || event.toEnd}
                    </span>
                  </div>
                  <span className="text-xs text-text-secondary">
                    {formatTime(event.timestamp)}
                  </span>
                </div>
                <p className="text-sm text-text-primary">{event.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CrossEndTimeline;
