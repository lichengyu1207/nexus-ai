import React, { memo } from 'react';
import { format } from 'date-fns';
import { HandThumbUpIcon, HandThumbDownIcon } from '@heroicons/react/24/outline';
import type { ReasoningStep } from './types';

interface ReasoningItemProps {
  step: ReasoningStep;
  index: number;
  onFeedback: (index: number, type: 'helpful' | 'not_helpful') => void;
}

const ReasoningItem: React.FC<ReasoningItemProps> = memo(({ step, index, onFeedback }) => {
  const timeFormatted = format(new Date(step.timestamp), 'HH:mm:ss');

  return (
    <div className="relative pl-6 pb-6 border-l-2 border-gray-200 dark:border-gray-700 last:border-l-0 last:pb-0">
      <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-blue-500 dark:bg-blue-400 ring-2 ring-white dark:ring-gray-900" />

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <div className="flex justify-between items-start mb-2">
          <div>
            <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">{timeFormatted}</span>
            <h4 className="font-semibold text-gray-900 dark:text-white mt-1">{step.step}</h4>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => !step.feedbackGiven && onFeedback(index, 'helpful')}
              disabled={step.feedbackGiven}
              className={`p-1.5 rounded-lg transition-colors ${
                step.feedbackGiven
                  ? 'text-green-500 cursor-default'
                  : 'text-gray-400 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20'
              }`}
              title="此步骤有用"
              aria-label="标记为有用"
            >
              <HandThumbUpIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => !step.feedbackGiven && onFeedback(index, 'not_helpful')}
              disabled={step.feedbackGiven}
              className={`p-1.5 rounded-lg transition-colors ${
                step.feedbackGiven
                  ? 'text-red-500 cursor-default'
                  : 'text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
              }`}
              title="此步骤无用"
              aria-label="标记为无用"
            >
              <HandThumbDownIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
        <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
          {step.content}
        </p>
      </div>
    </div>
  );
});

ReasoningItem.displayName = 'ReasoningItem';

export default ReasoningItem;
