import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ClockIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface WorkflowStep {
  step_id: string;
  step_name: string;
  step_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data: any;
  output_data: any;
  duration_ms?: number;
  metadata?: Record<string, any>;
}

interface DialogueWorkflowProps {
  steps: WorkflowStep[];
  currentStepIndex?: number;
  title?: string;
}

const stepIcons: Record<string, string> = {
  input_processing: '📝',
  agent_assignment: '🤖',
  keyword_extraction: '🔍',
  missing_info_detection: '❓',
  response_generation: '💬',
};

const DialogueWorkflow: React.FC<DialogueWorkflowProps> = ({
  steps,
  currentStepIndex = -1,
  title = '处理流程',
}) => {
  const [expandedSteps, setExpandedSteps] = React.useState<Set<string>>(new Set());

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

  const getStatusIcon = (status: string, index: number) => {
    if (index === currentStepIndex) {
      return <ArrowPathIcon className="w-5 h-5 text-blue-500 animate-spin" />;
    }
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
      case 'running':
        return <ArrowPathIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string, index: number) => {
    if (index === currentStepIndex) return 'border-blue-500 bg-blue-50';
    switch (status) {
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'failed':
        return 'border-red-500 bg-red-50';
      case 'running':
        return 'border-blue-500 bg-blue-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const renderDataPreview = (data: any, label: string) => {
    if (!data) return null;
    
    let content = '';
    if (typeof data === 'string') {
      content = data.length > 100 ? data.slice(0, 100) + '...' : data;
    } else if (Array.isArray(data)) {
      content = data.slice(0, 5).map((item, i) => 
        typeof item === 'object' ? JSON.stringify(item) : String(item)
      ).join(', ') + (data.length > 5 ? '...' : '');
    } else {
      content = JSON.stringify(data, null, 2);
      if (content.length > 200) {
        content = content.slice(0, 200) + '...';
      }
    }

    return (
      <div className="mt-2">
        <p className="text-xs text-gray-500 mb-1">{label}</p>
        <pre className="text-xs bg-gray-100 rounded p-2 overflow-x-auto whitespace-pre-wrap">
          {content}
        </pre>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <span className="text-lg">⚡</span>
          {title}
        </h3>
      </div>

      <div className="p-4">
        <div className="relative">
          {steps.map((step, index) => {
            const isExpanded = expandedSteps.has(step.step_id);
            const isLast = index === steps.length - 1;

            return (
              <div key={step.step_id} className="relative">
                {!isLast && (
                  <div
                    className={`absolute left-5 top-10 w-0.5 h-full ${
                      step.status === 'completed' ? 'bg-green-300' : 'bg-gray-200'
                    }`}
                  />
                )}

                <div
                  className={`relative mb-4 rounded-lg border-2 transition-all cursor-pointer ${getStatusColor(step.status, index)}`}
                  onClick={() => toggleStep(step.step_id)}
                >
                  <div className="p-3 flex items-center gap-3">
                    {getStatusIcon(step.status, index)}
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">
                          {stepIcons[step.step_type] || '📋'}
                        </span>
                        <span className="font-medium text-gray-900">{step.step_name}</span>
                      </div>
                      {step.duration_ms && (
                        <span className="text-xs text-gray-500 ml-7">
                          耗时 {formatDuration(step.duration_ms)}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {isExpanded ? (
                        <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-4 pb-3 border-t border-gray-200 mt-1">
                      {renderDataPreview(step.input_data, '输入')}
                      {renderDataPreview(step.output_data, '输出')}
                      {step.metadata && Object.keys(step.metadata).length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">元数据</p>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(step.metadata).map(([key, value]) => (
                              <span
                                key={key}
                                className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                              >
                                {key}: {String(value)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default DialogueWorkflow;
