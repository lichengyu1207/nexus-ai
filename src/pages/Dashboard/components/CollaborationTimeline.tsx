import { motion } from 'framer-motion';
import type { CollaborationEvent } from '../types';
import { END_LABELS } from '../types';

interface CollaborationTimelineProps {
  events: CollaborationEvent[];
  onEventClick?: (event: CollaborationEvent) => void;
}

export function CollaborationTimeline({ events, onEventClick }: CollaborationTimelineProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  if (events.length === 0) {
    return (
      <div className="bg-slate-800/30 rounded-xl border border-slate-700/50 p-6 text-center">
        <p className="text-slate-400">暂无协同事件</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/30 rounded-xl border border-slate-700/50 p-4">
      <h3 className="text-lg font-semibold text-white mb-4">五端协同动态</h3>
      
      <div className="relative">
        <div className="absolute left-3 top-0 bottom-0 w-px bg-gradient-to-b from-amber-500/50 via-amber-500/30 to-transparent" />
        
        <div className="space-y-4">
          {events.slice(0, 5).map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => onEventClick?.(event)}
              className={`
                relative pl-8 cursor-pointer group
                ${event.actionable ? 'hover:bg-slate-700/30' : ''}
              `}
            >
              <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full bg-slate-800 border-2 border-amber-500 flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-amber-500" />
              </div>
              
              <div className="pb-4 border-b border-slate-700/30 last:border-0 last:pb-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded">
                    {END_LABELS[event.fromEnd] || event.fromEnd}
                  </span>
                  <span className="text-slate-500">→</span>
                  <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded">
                    {END_LABELS[event.toEnd] || event.toEnd}
                  </span>
                  <span className="text-xs text-slate-500 ml-auto">
                    {formatTime(event.timestamp)}
                  </span>
                </div>
                
                <p className="text-sm text-slate-300 group-hover:text-white transition-colors">
                  {event.description}
                </p>
                
                {event.actionable && (
                  <span className="text-xs text-amber-400 mt-1 inline-block">
                    可操作
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
