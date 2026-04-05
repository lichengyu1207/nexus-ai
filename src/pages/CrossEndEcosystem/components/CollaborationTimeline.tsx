import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCollaborationEvents, useProcessEvent } from '../hooks/useCollaborationEvents';
import { EventDetailModal } from './EventDetailModal';
import type { EndName, CollaborationEvent } from '../types';

interface CollaborationTimelineProps {
  endId: EndName;
}

type EventFilter = 'all' | 'request' | 'response' | 'task_assignment';

const filterOptions: { value: EventFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'request', label: '请求' },
  { value: 'response', label: '响应' },
  { value: 'task_assignment', label: '任务分配' },
];

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

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  return date.toLocaleDateString('zh-CN');
}

export function CollaborationTimeline({ endId }: CollaborationTimelineProps) {
  const [filter, setFilter] = useState<EventFilter>('all');
  const [selectedEvent, setSelectedEvent] = useState<CollaborationEvent | null>(null);
  
  const { data: events, isLoading, error } = useCollaborationEvents({ endId, filter });
  const processEvent = useProcessEvent();

  const filteredEvents = useMemo(() => {
    if (!events) return [];
    return events;
  }, [events]);

  const handleProcessEvent = async (eventId: string) => {
    try {
      await processEvent.mutateAsync({ eventId, endId });
    } catch (e) {
      console.error('Failed to process event:', e);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4">
            <div className="w-3 h-3 rounded-full bg-slate-700 animate-pulse" />
            <div className="flex-1 h-20 rounded-lg bg-slate-800/50 animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-500/10 text-red-400 text-center">
        加载协同事件失败
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">协同事件时间线</h3>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as EventFilter)}
          className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-gray-300
            focus:outline-none focus:border-amber-500 text-sm"
        >
          {filterOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="relative">
        <div className="absolute left-1.5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-amber-500 to-amber-500/20" />
        
        <AnimatePresence mode="popLayout">
          {filteredEvents.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="pl-8 text-gray-500 text-center py-8"
            >
              暂无协同事件
            </motion.div>
          ) : (
            filteredEvents.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
                className="relative flex gap-4 mb-4 pl-8"
              >
                <div className="absolute left-0 top-2 w-3 h-3 rounded-full bg-amber-500 ring-4 ring-slate-900" />
                
                <motion.div
                  whileHover={{ y: -2 }}
                  className="flex-1 p-4 rounded-xl bg-slate-800/60 backdrop-blur-sm border border-slate-700/50
                    hover:border-amber-500/30 transition-all cursor-pointer"
                  onClick={() => setSelectedEvent(event)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${statusColors[event.status]}`} />
                      <span className="text-xs text-gray-500">
                        {statusLabels[event.status]}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </div>
                  
                  <h4 className="text-white font-medium mb-1">{event.title}</h4>
                  <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                    {event.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-gray-300">
                        {endDisplayNames[event.fromEnd]}
                      </span>
                      <span className="text-gray-500">→</span>
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-gray-300">
                        {endDisplayNames[event.toEnd]}
                      </span>
                    </div>
                    
                    {event.actionable && event.status === 'pending' && (
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleProcessEvent(event.id);
                        }}
                        disabled={processEvent.isPending}
                        className="px-3 py-1 rounded-lg bg-amber-500 text-slate-900 text-sm font-medium
                          hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {processEvent.isPending ? '处理中...' : '处理'}
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      <EventDetailModal
        event={selectedEvent}
        isOpen={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        onProcess={handleProcessEvent}
      />
    </div>
  );
}
