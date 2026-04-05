import React from 'react';
import { Link } from 'react-router-dom';
import { Task, AgentSummary } from '@/services/api';
import {
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  MapPinIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';

interface TaskCardProps {
  task: Task;
  showActions?: boolean;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, showActions = true }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          icon: <CheckCircleIcon className="w-5 h-5" />,
          text: '已完成',
          bgColor: 'bg-green-100',
          textColor: 'text-green-700',
          borderColor: 'border-green-200',
        };
      case 'failed':
        return {
          icon: <ExclamationCircleIcon className="w-5 h-5" />,
          text: '失败',
          bgColor: 'bg-red-100',
          textColor: 'text-red-700',
          borderColor: 'border-red-200',
        };
      case 'running':
        return {
          icon: <ArrowPathIcon className="w-5 h-5 animate-spin" />,
          text: '分析中',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-700',
          borderColor: 'border-blue-200',
        };
      default:
        return {
          icon: <ClockIcon className="w-5 h-5" />,
          text: '等待中',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-700',
          borderColor: 'border-gray-200',
        };
    }
  };

  const getStyleLabel = (style: string) => {
    switch (style) {
      case 'conservative':
        return { label: '保守型', color: 'text-blue-600 bg-blue-50' };
      case 'aggressive':
        return { label: '进取型', color: 'text-orange-600 bg-orange-50' };
      default:
        return { label: '平衡型', color: 'text-green-600 bg-green-50' };
    }
  };

  const statusConfig = getStatusConfig(task.status);
  const styleConfig = getStyleLabel(task.style);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const extractLocation = (query: string) => {
    const cities = ['深圳', '北京', '上海', '广州', '杭州', '成都', '武汉', '南京'];
    for (const city of cities) {
      if (query.includes(city)) return city;
    }
    return null;
  };

  const extractBudget = (query: string) => {
    const match = query.match(/(\d+)万/);
    if (match) return `${match[1]}万`;
    const match2 = query.match(/(\d+)千万/);
    if (match2) return `${match2[1]}千万`;
    return null;
  };

  const location = extractLocation(task.query);
  const budget = extractBudget(task.query);

  return (
    <Link
      to={`/tasks/${task.id}`}
      className="block bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group"
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.textColor}`}
              >
                {statusConfig.icon}
                {statusConfig.text}
              </span>
              <span
                className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${styleConfig.color}`}
              >
                {styleConfig.label}
              </span>
            </div>

            <p className="text-gray-900 font-medium line-clamp-2 mb-3 group-hover:text-primary-600 transition-colors">
              {task.query}
            </p>

            <div className="flex items-center gap-4 text-sm text-gray-500">
              {location && (
                <div className="flex items-center gap-1">
                  <MapPinIcon className="w-4 h-4" />
                  <span>{location}</span>
                </div>
              )}
              {budget && (
                <div className="flex items-center gap-1">
                  <CurrencyDollarIcon className="w-4 h-4" />
                  <span>{budget}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <ClockIcon className="w-4 h-4" />
                <span>{formatDate(task.created_at)}</span>
              </div>
            </div>
          </div>

          {task.status === 'running' && (
            <div className="flex-shrink-0 w-20">
              <div className="text-xs text-gray-500 mb-1 text-right">{task.progress}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {task.agents && task.agents.length > 0 && task.status !== 'pending' && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">参与代理:</span>
              <div className="flex items-center gap-1">
                {task.agents.slice(0, 4).map((agent: AgentSummary, index: number) => (
                  <span
                    key={index}
                    className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium ${
                      agent.status === 'completed'
                        ? 'bg-green-100 text-green-600'
                        : agent.status === 'running'
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                    title={agent.name}
                  >
                    {agent.name.charAt(0).toUpperCase()}
                  </span>
                ))}
                {task.agents.length > 4 && (
                  <span className="text-xs text-gray-400">+{task.agents.length - 4}</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {task.status === 'completed' && showActions && (
        <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-gray-500">点击查看分析报告</span>
          <span className="text-xs text-primary-600 font-medium group-hover:underline">
            查看详情 →
          </span>
        </div>
      )}
    </Link>
  );
};

export default TaskCard;
