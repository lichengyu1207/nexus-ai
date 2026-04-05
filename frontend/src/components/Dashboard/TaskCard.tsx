import React from 'react';
import { Link } from 'react-router-dom';

interface TaskCardProps {
  task: {
    id: string;
    type: 'analysis' | 'consult' | 'auto' | 'batch';
    description: string;
    progress: number;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    assignedAgents: Array<{
      id: string;
      name: string;
      avatar: string;
    }>;
    startTime: string;
    estimatedEndTime?: string;
    result?: string;
  };
}

const taskTypeConfig = {
  analysis: {
    label: '房产分析',
    icon: '🏠',
    color: 'bg-blue-500',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
  },
  consult: {
    label: '智能咨询',
    icon: '💬',
    color: 'bg-green-500',
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
  },
  auto: {
    label: '自主任务',
    icon: '🤖',
    color: 'bg-purple-500',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
  },
  batch: {
    label: '批量分析',
    icon: '📊',
    color: 'bg-orange-500',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-700',
  },
};

const statusConfig = {
  pending: {
    label: '等待中',
    color: 'bg-fluent-gold-500',
    textColor: 'text-fluent-gold-700',
  },
  processing: {
    label: '进行中',
    color: 'bg-blue-500',
    textColor: 'text-blue-700',
  },
  completed: {
    label: '已完成',
    color: 'bg-fluent-jade-500',
    textColor: 'text-fluent-jade-700',
  },
  failed: {
    label: '失败',
    color: 'bg-red-500',
    textColor: 'text-red-700',
  },
};

const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
  const typeConfig = taskTypeConfig[task.type];
  const statusConf = statusConfig[task.status];

  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return date.toLocaleDateString('zh-CN');
  };

  const getProgressColor = () => {
    if (task.status === 'completed') return 'bg-fluent-jade-500';
    if (task.status === 'failed') return 'bg-red-500';
    if (task.progress < 30) return 'bg-fluent-gold-500';
    if (task.progress < 70) return 'bg-blue-500';
    return 'bg-fluent-jade-500';
  };

  return (
    <div className="acrylic rounded-xl shadow-fluent-md p-4 border border-white/30 hover:shadow-fluent-lg transition-all duration-300">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${typeConfig.bgColor} flex items-center justify-center text-xl`}>
            {typeConfig.icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full ${typeConfig.bgColor} ${typeConfig.textColor}`}>
                {typeConfig.label}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${statusConf.color} text-white`}>
                {statusConf.label}
              </span>
            </div>
            <p className="text-sm text-fluent-deepOcean-400 mt-1">
              {formatTime(task.startTime)}
            </p>
          </div>
        </div>
      </div>

      <p className="text-fluent-deepOcean-500 font-medium mb-3 line-clamp-2">
        {task.description}
      </p>

      {task.status === 'processing' && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-fluent-deepOcean-300">进度</span>
            <span className="text-fluent-deepOcean-500 font-medium">{task.progress}%</span>
          </div>
          <div className="w-full bg-fluent-deepOcean-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${getProgressColor()}`}
              style={{ width: `${task.progress}%` }}
            ></div>
          </div>
          {task.estimatedEndTime && (
            <p className="text-xs text-fluent-deepOcean-300 mt-1">
              预计剩余时间：{task.estimatedEndTime}
            </p>
          )}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          <span className="text-xs text-fluent-deepOcean-300">参与智能体：</span>
          <div className="flex -space-x-2">
            {task.assignedAgents.slice(0, 4).map((agent, index) => (
              <div
                key={agent.id}
                className="w-6 h-6 rounded-full bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 flex items-center justify-center text-xs text-white border-2 border-white"
                title={agent.name}
                style={{ zIndex: 4 - index }}
              >
                {agent.name.charAt(0)}
              </div>
            ))}
            {task.assignedAgents.length > 4 && (
              <div className="w-6 h-6 rounded-full bg-fluent-deepOcean-200 flex items-center justify-center text-xs text-fluent-deepOcean-500 border-2 border-white">
                +{task.assignedAgents.length - 4}
              </div>
            )}
          </div>
        </div>

        {task.status === 'completed' && (
          <Link
            to={`/virtual-office/${task.id}`}
            className="text-xs text-fluent-gold-500 hover:text-fluent-gold-600 font-medium transition-colors"
          >
            查看报告 →
          </Link>
        )}

        {task.status === 'processing' && (
          <Link
            to={`/dashboard/tasks/${task.id}`}
            className="text-xs text-blue-500 hover:text-blue-600 font-medium transition-colors"
          >
            查看详情 →
          </Link>
        )}

        {task.status === 'failed' && (
          <button className="text-xs text-red-500 hover:text-red-600 font-medium transition-colors">
            重试
          </button>
        )}
      </div>
    </div>
  );
};

export default TaskCard;
