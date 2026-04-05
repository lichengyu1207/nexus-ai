import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { TaskFilters as TaskFiltersType, TaskStatus } from '../types';

interface TaskFiltersProps {
  filters: TaskFiltersType;
  onFilterChange: (filters: Partial<TaskFiltersType>) => void;
  onReset: () => void;
}

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
];

const dateRangePresets = [
  { label: '最近7天', days: 7 },
  { label: '最近30天', days: 30 },
  { label: '最近90天', days: 90 },
];

export function TaskFilters({ filters, onFilterChange, onReset }: TaskFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [localFilters, setLocalFilters] = useState<TaskFiltersType>(filters);
  const [customDateStart, setCustomDateStart] = useState('');
  const [customDateEnd, setCustomDateEnd] = useState('');

  const handleStatusChange = (status: TaskStatus, checked: boolean) => {
    const newStatus = checked
      ? [...localFilters.status, status]
      : localFilters.status.filter((s) => s !== status);
    setLocalFilters({ ...localFilters, status: newStatus });
  };

  const handleDatePreset = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    setLocalFilters({
      ...localFilters,
      dateRange: {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0],
      },
    });
    setCustomDateStart(start.toISOString().split('T')[0]);
    setCustomDateEnd(end.toISOString().split('T')[0]);
  };

  const handleCustomDateChange = () => {
    if (customDateStart && customDateEnd) {
      setLocalFilters({
        ...localFilters,
        dateRange: { start: customDateStart, end: customDateEnd },
      });
    }
  };

  const handleApply = () => {
    onFilterChange(localFilters);
  };

  const handleReset = () => {
    setLocalFilters({ status: [] });
    setCustomDateStart('');
    setCustomDateEnd('');
    onReset();
  };

  return (
    <motion.div
      initial={false}
      animate={{ width: isExpanded ? 300 : 48 }}
      className="bg-slate-900/50 backdrop-blur-md border-r border-slate-700/50 overflow-hidden"
    >
      {isExpanded ? (
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">筛选器</h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="p-1 rounded text-gray-400 hover:text-white hover:bg-slate-700"
              aria-label="折叠筛选器"
            >
              ◀
            </button>
          </div>

          <div className="space-y-6">
            <fieldset>
              <legend className="text-sm font-medium text-gray-400 mb-2">状态</legend>
              <div className="space-y-2">
                {statusOptions.map((option) => (
                  <label
                    key={option.value}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={localFilters.status.includes(option.value)}
                      onChange={(e) => handleStatusChange(option.value, e.target.checked)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-amber-500
                        focus:ring-amber-500 focus:ring-offset-0"
                    />
                    <span className="text-gray-300 text-sm">{option.label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="text-sm font-medium text-gray-400 mb-2">时间范围</legend>
              <div className="flex flex-wrap gap-2 mb-2">
                {dateRangePresets.map((preset) => (
                  <button
                    key={preset.days}
                    onClick={() => handleDatePreset(preset.days)}
                    className="px-2 py-1 text-xs rounded bg-slate-800 text-gray-300
                      hover:bg-slate-700 hover:text-white transition-colors"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              <div className="space-y-2">
                <input
                  type="date"
                  value={customDateStart}
                  onChange={(e) => setCustomDateStart(e.target.value)}
                  onBlur={handleCustomDateChange}
                  className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700
                    text-gray-300 text-sm focus:outline-none focus:border-amber-500"
                  placeholder="开始日期"
                />
                <input
                  type="date"
                  value={customDateEnd}
                  onChange={(e) => setCustomDateEnd(e.target.value)}
                  onBlur={handleCustomDateChange}
                  className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700
                    text-gray-300 text-sm focus:outline-none focus:border-amber-500"
                  placeholder="结束日期"
                />
              </div>
            </fieldset>

            <fieldset>
              <legend className="text-sm font-medium text-gray-400 mb-2">搜索</legend>
              <input
                type="text"
                value={localFilters.searchText || ''}
                onChange={(e) =>
                  setLocalFilters({ ...localFilters, searchText: e.target.value || undefined })
                }
                placeholder="任务名称或ID"
                className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700
                  text-gray-300 text-sm focus:outline-none focus:border-amber-500"
              />
            </fieldset>

            <div className="pt-4 space-y-2">
              <button
                onClick={handleApply}
                className="w-full py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                  hover:bg-amber-400 transition-colors"
              >
                应用筛选
              </button>
              <button
                onClick={handleReset}
                className="w-full py-2 rounded-lg bg-slate-700 text-gray-300
                  hover:bg-slate-600 transition-colors"
              >
                重置
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full h-full flex items-center justify-center text-gray-400
            hover:text-white hover:bg-slate-800/50 transition-colors"
          aria-label="展开筛选器"
        >
          ▶
        </button>
      )}
    </motion.div>
  );
}
