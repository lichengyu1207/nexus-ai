import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface TimelineEvent {
  id: string;
  agent: string;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  detail?: string;
}

interface TimelineProps {
  events: TimelineEvent[];
  title?: string;
}

const agentLabels: Record<string, string> = {
  supervisor: '主管代理',
  requirement: '需求解析',
  collector: '数据采集',
  analyst: '分析代理',
};

const agentColors: Record<string, string> = {
  supervisor: 'bg-purple-500',
  requirement: 'bg-blue-500',
  collector: 'bg-green-500',
  analyst: 'bg-orange-500',
};

const Timeline: React.FC<TimelineProps> = ({ events, title = '执行时间线' }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'running':
        return <ArrowPathIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const sortedEvents = [...events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500">共 {events.length} 个事件</p>
      </div>
      
      <div className="p-4">
        {sortedEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <ClockIcon className="w-12 h-12 mx-auto mb-2" />
            <p>暂无执行记录</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

            {/* Events */}
            <div className="space-y-4">
              {sortedEvents.map((event) => (
                <div key={event.id} className="relative pl-10">
                  {/* Agent color dot */}
                  <div
                    className={`absolute left-2 top-1 w-5 h-5 rounded-full ${
                      agentColors[event.agent] || 'bg-gray-500'
                    } flex items-center justify-center`}
                  >
                    <div className="w-2 h-2 rounded-full bg-white" />
                  </div>

                  {/* Content */}
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {agentLabels[event.agent] || event.agent}
                        </span>
                        <span className="text-xs text-gray-500">•</span>
                        <span className="text-sm text-gray-600">{event.action}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {formatTime(event.timestamp)}
                        </span>
                        {getStatusIcon(event.status)}
                      </div>
                    </div>
                    {event.detail && (
                      <p className="text-sm text-gray-500 mt-1">{event.detail}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Timeline;
