import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  CircleIcon,
  ClockIcon,
  CogIcon,
  UserGroupIcon,
  TagIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowPathIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

interface ProcessingStep {
  step_id: string;
  step_name: string;
  step_type: string;
  status: string;
  input_data: any;
  output_data: any;
  timestamp: string;
  duration_ms: number;
  metadata: Record<string, any>;
}

interface AgentAssignment {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  confidence: number;
  reason: string;
  capabilities: string[];
}

interface KeywordMatch {
  keyword: string;
  category: string;
  value: any;
  confidence: number;
}

interface MissingInfo {
  field_name: string;
  field_label: string;
  importance: string;
  question: string;
  suggestions: string[];
}

interface DialogueProcess {
  session_id: string;
  user_input: string;
  binary_input: string;
  decoded_input: string;
  steps: ProcessingStep[];
  agent_assignments: AgentAssignment[];
  keywords_matched: KeywordMatch[];
  missing_info: MissingInfo[];
  final_response: string;
  needs_follow_up: boolean;
  follow_up_question: string | null;
  created_at: string;
}

interface ProcessVisualizationProps {
  process: DialogueProcess | null;
  isLoading: boolean;
}

const StepIcon: React.FC<{ type: string; status: string }> = ({ type, status }) => {
  const iconClass = `w-5 h-5 ${
    status === 'completed' ? 'text-green-500' : 
    status === 'processing' ? 'text-blue-500 animate-spin' : 
    status === 'failed' ? 'text-red-500' : 'text-gray-400'
  }`;

  switch (type) {
    case 'input_processing':
      return <DocumentTextIcon className={iconClass} />;
    case 'agent_routing':
      return <UserGroupIcon className={iconClass} />;
    case 'keyword_extraction':
      return <TagIcon className={iconClass} />;
    case 'missing_info_detection':
      return <ExclamationTriangleIcon className={iconClass} />;
    default:
      return <CogIcon className={iconClass} />;
  }
};

const ProcessStepCard: React.FC<{ step: ProcessingStep; isExpanded: boolean; onToggle: () => void }> = ({
  step,
  isExpanded,
  onToggle,
}) => {
  const duration = step.duration_ms > 0 ? `${step.duration_ms}ms` : '-';
  
  return (
    <div className="border rounded-lg dark:border-gray-700 overflow-hidden">
      <div
        onClick={onToggle}
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
      >
        <div className="flex items-center gap-3">
          <StepIcon type={step.step_type} status={step.status} />
          <div>
            <p className="font-medium text-gray-900 dark:text-white">{step.step_name}</p>
            <p className="text-xs text-gray-500">{step.step_type}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">{duration}</span>
          {isExpanded ? (
            <ChevronDownIcon className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>
      
      {isExpanded && (
        <div className="px-3 pb-3 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="mt-2">
            <p className="text-xs font-medium text-gray-500 mb-1">输入数据</p>
            <pre className="text-xs bg-white dark:bg-gray-900 p-2 rounded overflow-x-auto">
              {typeof step.input_data === 'string' ? step.input_data : JSON.stringify(step.input_data, null, 2)}
            </pre>
          </div>
          <div className="mt-2">
            <p className="text-xs font-medium text-gray-500 mb-1">输出数据</p>
            <pre className="text-xs bg-white dark:bg-gray-900 p-2 rounded overflow-x-auto">
              {typeof step.output_data === 'string' ? step.output_data : JSON.stringify(step.output_data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

const AgentCard: React.FC<{ agent: AgentAssignment }> = ({ agent }) => {
  const confidenceColor = agent.confidence >= 0.8 ? 'text-green-500' : 
                          agent.confidence >= 0.5 ? 'text-yellow-500' : 'text-red-500';
  
  return (
    <div className="border rounded-lg p-3 dark:border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900 dark:text-white">{agent.agent_name}</span>
        <span className={`text-sm font-semibold ${confidenceColor}`}>
          {(agent.confidence * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-2">{agent.reason}</p>
      <div className="flex flex-wrap gap-1">
        {agent.capabilities.map((cap, i) => (
          <span key={i} className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
            {cap}
          </span>
        ))}
      </div>
    </div>
  );
};

const KeywordTag: React.FC<{ keyword: KeywordMatch }> = ({ keyword }) => {
  const categoryColors: Record<string, string> = {
    location: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    budget: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    property_type: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    purpose: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    time: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
    family: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
  };
  
  const colorClass = categoryColors[keyword.category] || 'bg-gray-100 text-gray-700';
  
  return (
    <span className={`text-xs px-2 py-1 rounded ${colorClass}`}>
      {keyword.keyword}: {keyword.value}
    </span>
  );
};

const MissingInfoCard: React.FC<{ info: MissingInfo; onSelect: (suggestion: string) => void }> = ({
  info,
  onSelect,
}) => {
  const importanceColors: Record<string, string> = {
    high: 'border-red-300 bg-red-50 dark:bg-red-900/20',
    medium: 'border-yellow-300 bg-yellow-50 dark:bg-yellow-900/20',
    low: 'border-gray-300 bg-gray-50 dark:bg-gray-800',
  };
  
  return (
    <div className={`border rounded-lg p-3 ${importanceColors[info.importance]}`}>
      <div className="flex items-center gap-2 mb-2">
        <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />
        <span className="font-medium text-gray-900 dark:text-white">{info.field_label}</span>
        <span className="text-xs text-gray-500">({info.importance})</span>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{info.question}</p>
      {info.suggestions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {info.suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSelect(s)}
              className="text-xs bg-white dark:bg-gray-700 border dark:border-gray-600 px-2 py-1 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const ProcessVisualization: React.FC<ProcessVisualizationProps> = ({ process, isLoading }) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [showBinary, setShowBinary] = useState(false);

  const toggleStep = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <ArrowPathIcon className="w-8 h-8 text-blue-500 animate-spin" />
        <span className="ml-2 text-gray-500">处理中...</span>
      </div>
    );
  }

  if (!process) {
    return (
      <div className="text-center py-8 text-gray-500">
        <CogIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
        <p>发送消息后查看处理过程</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 输入/二进制展示 */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">用户输入</span>
          <button
            onClick={() => setShowBinary(!showBinary)}
            className="text-xs text-blue-600 hover:underline"
          >
            {showBinary ? '显示原文' : '显示二进制'}
          </button>
        </div>
        <p className="text-sm font-mono break-all">
          {showBinary ? process.binary_input : process.user_input}
        </p>
      </div>

      {/* 处理步骤 */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          处理步骤 ({process.steps.length})
        </h3>
        <div className="space-y-2">
          {process.steps.map((step) => (
            <ProcessStepCard
              key={step.step_id}
              step={step}
              isExpanded={expandedSteps.has(step.step_id)}
              onToggle={() => toggleStep(step.step_id)}
            />
          ))}
        </div>
      </div>

      {/* 智能体分配 */}
      {process.agent_assignments.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            智能体分配
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {process.agent_assignments.map((agent) => (
              <AgentCard key={agent.agent_id} agent={agent} />
            ))}
          </div>
        </div>
      )}

      {/* 关键词匹配 */}
      {process.keywords_matched.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            已识别信息
          </h3>
          <div className="flex flex-wrap gap-2">
            {process.keywords_matched.map((kw, i) => (
              <KeywordTag key={i} keyword={kw} />
            ))}
          </div>
        </div>
      )}

      {/* 缺失信息 */}
      {process.missing_info.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            需要补充的信息 ({process.missing_info.length})
          </h3>
          <div className="space-y-2">
            {process.missing_info.map((info, i) => (
              <MissingInfoCard 
                key={i} 
                info={info} 
                onSelect={(s) => console.log('Selected:', s)}
              />
            ))}
          </div>
        </div>
      )}

      {/* 追问 */}
      {process.needs_follow_up && process.follow_up_question && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-blue-800 dark:text-blue-200">{process.follow_up_question}</p>
        </div>
      )}
    </div>
  );
};

export default ProcessVisualization;
