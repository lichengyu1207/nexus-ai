import React from 'react';
import {
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  CogIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface AgentCardProps {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: string | null;
  completedAt: string | null;
  steps?: {
    name: string;
    status: string;
    detail?: string;
  }[];
  isHighlighted?: boolean;
  highlightSection?: string | null;
  onHighlightClick?: () => void;
}

const agentConfig: Record<string, { icon: React.FC<{ className?: string }>; color: string; label: string }> = {
  supervisor: { icon: CogIcon, color: 'purple', label: '主管代理' },
  requirement: { icon: DocumentTextIcon, color: 'blue', label: '需求解析' },
  collector: { icon: MagnifyingGlassIcon, color: 'green', label: '数据采集' },
  analyst: { icon: ChartBarIcon, color: 'orange', label: '分析代理' },
};

const AgentCard: React.FC<AgentCardProps> = ({ 
  name, 
  status, 
  startedAt, 
  completedAt, 
  steps,
  isHighlighted = false,
  highlightSection = null,
  onHighlightClick,
}) => {
  const config = agentConfig[name] || { icon: CogIcon, color: 'gray', label: name };
  const Icon = config.icon;

  const getStatusConfig = () => {
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
          text: '运行中',
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

  const statusConfig = getStatusConfig();

  const calculateDuration = () => {
    if (!startedAt) return null;
    const start = new Date(startedAt).getTime();
    const end = completedAt ? new Date(completedAt).getTime() : Date.now();
    const duration = Math.round((end - start) / 1000);
    
    if (duration < 60) return `${duration}秒`;
    if (duration < 3600) return `${Math.round(duration / 60)}分钟`;
    return `${Math.round(duration / 3600)}小时`;
  };

  const colorClasses = {
    purple: 'bg-purple-100 text-purple-600',
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    gray: 'bg-gray-100 text-gray-600',
  };

  const borderClass = isHighlighted 
    ? 'border-primary-500 ring-2 ring-primary-200' 
    : statusConfig.borderColor;

  return (
    <div 
      className={`bg-white rounded-xl border-2 ${borderClass} overflow-hidden transition-all hover:shadow-md ${isHighlighted ? 'animate-pulse' : ''} ${onHighlightClick ? 'cursor-pointer' : ''}`}
      onClick={onHighlightClick}
    >
      {/* Header */}
      <div className="p-4 flex items-center gap-3">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[config.color as keyof typeof colorClasses]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            {config.label}
            {isHighlighted && (
              <span className="flex items-center gap-1 text-xs text-primary-600">
                <SparklesIcon className="w-3 h-3" />
                生成报告中
              </span>
            )}
          </h3>
          <p className="text-sm text-gray-500">{name}</p>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full ${statusConfig.bgColor} ${statusConfig.textColor}`}>
          {statusConfig.icon}
          <span className="text-sm font-medium">{statusConfig.text}</span>
        </div>
      </div>

      {/* Highlight Section Indicator */}
      {isHighlighted && highlightSection && (
        <div className="px-4 py-2 bg-primary-50 border-t border-primary-100">
          <p className="text-sm text-primary-700">
            正在生成: <span className="font-medium">{highlightSection}</span>
          </p>
        </div>
      )}

      {/* Duration */}
      {startedAt && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 flex items-center justify-between text-sm">
          <span className="text-gray-500">耗时</span>
          <span className="font-medium text-gray-900">{calculateDuration()}</span>
        </div>
      )}

      {/* Steps */}
      {steps && steps.length > 0 && (
        <div className="border-t border-gray-100">
          <div className="p-3">
            <p className="text-xs font-medium text-gray-500 mb-2">执行步骤</p>
            <div className="space-y-2">
              {steps.map((step, index) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                    step.status === 'completed' ? 'bg-green-100' :
                    step.status === 'running' ? 'bg-blue-100' :
                    step.status === 'failed' ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    {step.status === 'completed' && <CheckCircleIcon className="w-3 h-3 text-green-600" />}
                    {step.status === 'running' && <ArrowPathIcon className="w-3 h-3 text-blue-600 animate-spin" />}
                    {step.status === 'failed' && <ExclamationCircleIcon className="w-3 h-3 text-red-600" />}
                    {step.status === 'pending' && <ClockIcon className="w-3 h-3 text-gray-400" />}
                  </div>
                  <span className="text-gray-700">{step.name}</span>
                  {step.detail && (
                    <span className="text-gray-400 text-xs truncate flex-1">{step.detail}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentCard;
