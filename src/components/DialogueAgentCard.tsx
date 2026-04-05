import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ClockIcon,
  SparklesIcon,
  ChartBarIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  UserGroupIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

interface DialogueAgentCardProps {
  agentId: string;
  agentName: string;
  agentType: string;
  confidence: number;
  reason: string;
  capabilities: string[];
  status: 'pending' | 'running' | 'completed' | 'failed';
  isActive?: boolean;
  matchedKeywords?: string[];
}

const agentIcons: Record<string, React.FC<{ className?: string }>> = {
  analysis: ChartBarIcon,
  location: MapPinIcon,
  finance: CurrencyDollarIcon,
  policy: DocumentTextIcon,
  community: UserGroupIcon,
  general: LightBulbIcon,
};

const agentColors: Record<string, { bg: string; text: string; border: string }> = {
  analysis: { bg: 'bg-purple-100', text: 'text-purple-600', border: 'border-purple-200' },
  location: { bg: 'bg-blue-100', text: 'text-blue-600', border: 'border-blue-200' },
  finance: { bg: 'bg-green-100', text: 'text-green-600', border: 'border-green-200' },
  policy: { bg: 'bg-orange-100', text: 'text-orange-600', border: 'border-orange-200' },
  community: { bg: 'bg-pink-100', text: 'text-pink-600', border: 'border-pink-200' },
  general: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-200' },
};

const DialogueAgentCard: React.FC<DialogueAgentCardProps> = ({
  agentId,
  agentName,
  agentType,
  confidence,
  reason,
  capabilities,
  status,
  isActive = false,
  matchedKeywords = [],
}) => {
  const Icon = agentIcons[agentType] || LightBulbIcon;
  const colors = agentColors[agentType] || agentColors.general;

  const getStatusConfig = () => {
    switch (status) {
      case 'completed':
        return {
          icon: <CheckCircleIcon className="w-4 h-4" />,
          text: '已完成',
          bgColor: 'bg-green-100',
          textColor: 'text-green-700',
        };
      case 'failed':
        return {
          icon: <ExclamationCircleIcon className="w-4 h-4" />,
          text: '失败',
          bgColor: 'bg-red-100',
          textColor: 'text-red-700',
        };
      case 'running':
        return {
          icon: <ArrowPathIcon className="w-4 h-4 animate-spin" />,
          text: '处理中',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-700',
        };
      default:
        return {
          icon: <ClockIcon className="w-4 h-4" />,
          text: '等待中',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-600',
        };
    }
  };

  const statusConfig = getStatusConfig();
  const confidencePercent = Math.round(confidence * 100);

  return (
    <div
      className={`bg-white rounded-xl border-2 overflow-hidden transition-all hover:shadow-md ${
        isActive ? 'border-primary-500 ring-2 ring-primary-200 animate-pulse' : colors.border
      }`}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colors.bg} ${colors.text}`}>
            <Icon className="w-6 h-6" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                {agentName}
                {isActive && (
                  <span className="flex items-center gap-1 text-xs text-primary-600">
                    <SparklesIcon className="w-3 h-3" />
                    当前处理
                  </span>
                )}
              </h3>
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${statusConfig.bgColor} ${statusConfig.textColor}`}>
                {statusConfig.icon}
                <span className="text-xs font-medium">{statusConfig.text}</span>
              </div>
            </div>
            
            <p className="text-sm text-gray-500 mt-0.5">{reason}</p>
          </div>
        </div>

        <div className="mt-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-gray-500">匹配置信度</span>
            <span className={`font-medium ${confidencePercent >= 70 ? 'text-green-600' : confidencePercent >= 40 ? 'text-yellow-600' : 'text-gray-500'}`}>
              {confidencePercent}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${
                confidencePercent >= 70 ? 'bg-green-500' : confidencePercent >= 40 ? 'bg-yellow-500' : 'bg-gray-400'
              }`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        {capabilities.length > 0 && (
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-1">能力范围</p>
            <div className="flex flex-wrap gap-1">
              {capabilities.map((cap, idx) => (
                <span
                  key={idx}
                  className={`px-2 py-0.5 text-xs rounded-full ${colors.bg} ${colors.text}`}
                >
                  {cap}
                </span>
              ))}
            </div>
          </div>
        )}

        {matchedKeywords.length > 0 && (
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-1">匹配关键词</p>
            <div className="flex flex-wrap gap-1">
              {matchedKeywords.map((kw, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                >
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DialogueAgentCard;
