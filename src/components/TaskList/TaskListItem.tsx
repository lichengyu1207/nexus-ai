import React, { memo } from 'react';
import TaskStatusCard from '../TaskStatusCard/TaskStatusCard';
import type { Task } from './types';

interface TaskListItemProps {
  task: Task;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
  onViewReport?: (id: string) => void;
  onRetry?: (id: string) => void;
}

const TaskListItem: React.FC<TaskListItemProps> = memo(({
  task,
  isSelected,
  onToggleSelect,
  onViewReport,
  onRetry,
}) => {
  const canSelect = task.status === 'completed' || task.status === 'failed';

  return (
    <div className="relative group flex items-start gap-3">
      <div className="flex-shrink-0 pt-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => canSelect && onToggleSelect(task.id)}
          disabled={!canSelect}
          className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label={`选择任务 ${task.name}`}
        />
      </div>
      <div className="flex-1 min-w-0">
        <TaskStatusCard
          task={task}
          onViewReport={onViewReport ? () => onViewReport(task.id) : undefined}
          onRetry={onRetry ? () => onRetry(task.id) : undefined}
        />
      </div>
    </div>
  );
});

TaskListItem.displayName = 'TaskListItem';

export default TaskListItem;
