import React, { useState } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { MemoryFilters, MemoryType } from '../types';

interface MemoryFilterSidebarProps {
  filters: MemoryFilters;
  onFilterChange: (filters: MemoryFilters) => void;
  totalCount: number;
  dateRange: { earliest: string; latest: string } | null;
}

const typeOptions: { value: MemoryType; label: string; icon: string }[] = [
  { value: 'episodic', label: '情景记忆', icon: '📅' },
  { value: 'semantic', label: '语义记忆', icon: '🧠' },
  { value: 'procedural', label: '程序性记忆', icon: '⚙️' },
];

const quickFilters = [
  { id: 'recent', label: '最近使用', icon: '🕐' },
  { id: 'frequent', label: '高频引用', icon: '🔥' },
  { id: 'starred', label: '我的收藏', icon: '⭐' },
];

export const MemoryFilterSidebar: React.FC<MemoryFilterSidebarProps> = ({
  filters,
  onFilterChange,
  totalCount,
  dateRange,
}) => {
  const [localFilters, setLocalFilters] = useState<MemoryFilters>(filters);
  const [selectedQuickFilter, setSelectedQuickFilter] = useState<string | null>(null);

  const handleApply = () => {
    onFilterChange(localFilters);
  };

  const handleReset = () => {
    const resetFilters: MemoryFilters = {};
    setLocalFilters(resetFilters);
    setSelectedQuickFilter(null);
    onFilterChange(resetFilters);
  };

  const handleTypeToggle = (type: MemoryType) => {
    const currentTypes = localFilters.type || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter((t) => t !== type)
      : [...currentTypes, type];
    setLocalFilters({ ...localFilters, type: newTypes.length > 0 ? newTypes : undefined });
  };

  const handleImportanceChange = (value: number) => {
    setLocalFilters({
      ...localFilters,
      importanceMin: value > 0 ? value : undefined,
    });
  };

  const handleQuickFilter = (id: string) => {
    setSelectedQuickFilter(id === selectedQuickFilter ? null : id);
    switch (id) {
      case 'recent':
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        setLocalFilters({
          ...localFilters,
          dateRange: {
            start: weekAgo.toISOString(),
            end: new Date().toISOString(),
          },
        });
        break;
      case 'frequent':
        setLocalFilters({ ...localFilters, importanceMin: 4 });
        break;
      case 'starred':
        setLocalFilters({ ...localFilters, importanceMin: 5 });
        break;
    }
  };

  return (
    <div className="w-[300px] h-full bg-bg-primary/50 backdrop-blur-md border-r border-border-light flex flex-col">
      <div className="p-4 border-b border-border-light">
        <h2 className="text-lg font-semibold text-text-primary mb-1">记忆系统</h2>
        <p className="text-xs text-text-secondary">海马体 · 长期知识存储</p>
      </div>

      <div className="p-4 border-b border-border-light">
        <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
          快速访问
        </h3>
        <div className="flex flex-wrap gap-2">
          {quickFilters.map((filter) => (
            <motion.button
              key={filter.id}
              onClick={() => handleQuickFilter(filter.id)}
              className={clsx(
                'px-3 py-1.5 text-xs rounded-full transition-all',
                selectedQuickFilter === filter.id
                  ? 'bg-primary/20 text-primary border border-primary/50'
                  : 'bg-bg-secondary/60 text-text-secondary border border-border-light hover:border-primary/30'
              )}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className="mr-1">{filter.icon}</span>
              {filter.label}
            </motion.button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
        <div>
          <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
            记忆类型
          </h3>
          <div className="space-y-2">
            {typeOptions.map((option) => (
              <label
                key={option.value}
                className={clsx(
                  'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all',
                  localFilters.type?.includes(option.value)
                    ? 'bg-primary/10 border border-primary/30'
                    : 'hover:bg-bg-secondary/50 border border-transparent'
                )}
              >
                <input
                  type="checkbox"
                  checked={localFilters.type?.includes(option.value) || false}
                  onChange={() => handleTypeToggle(option.value)}
                  className="sr-only"
                />
                <span className="text-lg">{option.icon}</span>
                <span className="text-sm text-text-primary">{option.label}</span>
                <div
                  className={clsx(
                    'ml-auto w-4 h-4 rounded border-2 flex items-center justify-center',
                    localFilters.type?.includes(option.value)
                      ? 'bg-primary border-primary'
                      : 'border-border-light'
                  )}
                >
                  {localFilters.type?.includes(option.value) && (
                    <svg className="w-3 h-3 text-bg-primary" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </label>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
            最低重要度
          </h3>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleImportanceChange(star)}
                className={clsx(
                  'text-xl transition-transform hover:scale-110',
                  (localFilters.importanceMin || 0) >= star
                    ? 'text-primary'
                    : 'text-text-secondary/30'
                )}
              >
                ★
              </button>
            ))}
          </div>
          <p className="text-xs text-text-secondary mt-2">
            {localFilters.importanceMin
              ? `显示 ${localFilters.importanceMin} 星及以上`
              : '显示全部'}
          </p>
        </div>

        <div>
          <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
            时间范围
          </h3>
          <div className="space-y-2">
            <select
              className="w-full px-3 py-2 bg-bg-secondary/60 border border-border-light rounded-lg text-sm text-text-primary focus:outline-none focus:border-primary/50"
              onChange={(e) => {
                const value = e.target.value;
                if (value === 'custom') return;
                const now = new Date();
                let start: Date;
                switch (value) {
                  case '7d':
                    start = new Date(now.setDate(now.getDate() - 7));
                    break;
                  case '30d':
                    start = new Date(now.setDate(now.getDate() - 30));
                    break;
                  case '90d':
                    start = new Date(now.setDate(now.getDate() - 90));
                    break;
                  default:
                    setLocalFilters({ ...localFilters, dateRange: undefined });
                    return;
                }
                setLocalFilters({
                  ...localFilters,
                  dateRange: { start: start.toISOString(), end: new Date().toISOString() },
                });
              }}
            >
              <option value="all">全部时间</option>
              <option value="7d">最近 7 天</option>
              <option value="30d">最近 30 天</option>
              <option value="90d">最近 90 天</option>
            </select>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-border-light">
        <div className="flex gap-2 mb-4">
          <button
            onClick={handleReset}
            className="flex-1 py-2 text-sm text-text-secondary hover:text-text-primary border border-border-light rounded-lg hover:border-primary/30 transition-colors"
          >
            重置
          </button>
          <button
            onClick={handleApply}
            className="flex-1 py-2 text-sm bg-primary text-bg-primary rounded-lg hover:bg-primary-dark transition-colors"
          >
            应用筛选
          </button>
        </div>
        <div className="text-xs text-text-secondary text-center">
          共 {totalCount.toLocaleString()} 条记忆
          {dateRange && (
            <span className="block mt-1">
              覆盖 {new Date(dateRange.earliest).toLocaleDateString()} 至{' '}
              {new Date(dateRange.latest).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemoryFilterSidebar;
