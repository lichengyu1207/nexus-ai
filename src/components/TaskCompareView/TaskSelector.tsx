import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { AvailableTask } from './types';

interface TaskSelectorProps {
  tasks: AvailableTask[];
  onCompare: (selectedIds: string[]) => void;
  onCancel?: () => void;
  maxSelection?: number;
  minSelection?: number;
}

export const TaskSelector: React.FC<TaskSelectorProps> = ({
  tasks,
  onCompare,
  onCancel,
  maxSelection = 5,
  minSelection = 2,
}) => {
  const [selected, setSelected] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTasks = useMemo(() => {
    if (!searchTerm) return tasks;
    return tasks.filter(
      (task) =>
        task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.id.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [tasks, searchTerm]);

  const toggleTask = (id: string) => {
    if (selected.includes(id)) {
      setSelected(selected.filter((s) => s !== id));
    } else {
      if (selected.length >= maxSelection) {
        return;
      }
      setSelected([...selected, id]);
    }
  };

  const handleCompare = () => {
    if (selected.length < minSelection) {
      return;
    }
    onCompare(selected);
  };

  const canCompare = selected.length >= minSelection && selected.length <= maxSelection;

  return (
    <div className="bg-bg-secondary rounded-xl p-6 shadow-lg border border-border-light">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">选择对比任务</h3>
        <span className="text-sm text-text-secondary">
          已选择 {selected.length}/{maxSelection} 个（最少 {minSelection} 个）
        </span>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="搜索任务名称或ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 bg-bg-tertiary border border-border-light rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-80 overflow-y-auto pr-2">
        {filteredTasks.map((task) => {
          const isSelected = selected.includes(task.id);
          const isDisabled = !isSelected && selected.length >= maxSelection;

          return (
            <motion.label
              key={task.id}
              whileHover={{ scale: isDisabled ? 1 : 1.01 }}
              whileTap={{ scale: isDisabled ? 1 : 0.99 }}
              className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all ${
                isSelected
                  ? 'bg-primary/20 border border-primary'
                  : isDisabled
                  ? 'bg-bg-tertiary/50 opacity-50 cursor-not-allowed'
                  : 'bg-bg-tertiary hover:bg-bg-tertiary/80 border border-transparent'
              }`}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => !isDisabled && toggleTask(task.id)}
                disabled={isDisabled}
                className="w-4 h-4 text-primary rounded border-border-light focus:ring-primary/50"
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-text-primary truncate">{task.name}</div>
                <div className="text-xs text-text-secondary">
                  {new Date(task.completedAt).toLocaleDateString('zh-CN')}
                </div>
              </div>
            </motion.label>
          );
        })}
      </div>

      {filteredTasks.length === 0 && (
        <div className="text-center py-8 text-text-secondary">没有找到匹配的任务</div>
      )}

      <div className="flex justify-end mt-6 space-x-3">
        {onCancel && (
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-border-light rounded-lg text-text-secondary hover:bg-bg-tertiary transition"
          >
            取消
          </button>
        )}
        <button
          onClick={handleCompare}
          disabled={!canCompare}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            canCompare
              ? 'bg-primary text-gray-900 hover:bg-primary-dark'
              : 'bg-bg-tertiary text-text-disabled cursor-not-allowed'
          }`}
        >
          开始对比
        </button>
      </div>
    </div>
  );
};

export default TaskSelector;
