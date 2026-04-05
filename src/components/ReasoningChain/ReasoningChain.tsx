import React, { useCallback } from 'react';
import { DocumentDuplicateIcon } from '@heroicons/react/24/outline';
import { useReasoningChain } from './useReasoningChain';
import ReasoningItem from './ReasoningItem';
import toast from 'react-hot-toast';

interface ReasoningChainProps {
  taskId: string;
}

const ReasoningChain: React.FC<ReasoningChainProps> = ({ taskId }) => {
  const { steps, isLoading, error, submitFeedback } = useReasoningChain(taskId);

  const handleCopy = useCallback(() => {
    if (!steps.length) return;
    
    const text = steps
      .map((step) => {
        const time = new Date(step.timestamp).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        return `[${time}] ${step.step}\n${step.content}`;
      })
      .join('\n\n');
    
    navigator.clipboard.writeText(text).then(() => {
      toast.success('推理链已复制到剪贴板');
    }).catch(() => {
      toast.error('复制失败');
    });
  }, [steps]);

  const handleFeedback = useCallback(
    (index: number, type: 'helpful' | 'not_helpful') => {
    submitFeedback({ stepIndex: index, feedback: type });
  },
  [submitFeedback]
  );

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        <p className="text-gray-500 mt-2">加载中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500 mb-2">加载失败</div>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-blue-500 hover:underline"
        >
          点击重试
        </button>
      </div>
    );
  }

  if (!steps.length) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
          <DocumentDuplicateIcon className="w-8 h-8 text-gray-400" />
        </div>
        <p className="text-gray-500 dark:text-gray-400">暂无推理链数据</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
          任务执行后将在此展示推理过程
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          推理链 ({steps.length} 步)
        </h3>
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          aria-label="复制推理链"
        >
          <DocumentDuplicateIcon className="w-4 h-4" />
          复制推理链
        </button>
      </div>
      
      <div className="space-y-0">
        {steps.map((step, idx) => (
          <ReasoningItem
            key={`${step.timestamp}-${idx}`}
            step={step}
            index={idx}
            onFeedback={handleFeedback}
          />
        ))}
      </div>
    </div>
  );
};

export default ReasoningChain;
