import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  ClockIcon,
  ArrowPathIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import type { TimeRange } from '../types';

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
  refreshInterval?: number;
  onRefresh?: () => void;
}

const QUICK_RANGES = [
  { label: '1小时', value: 3600000 },
  { label: '6小时', value: 21600000 },
  { label: '24小时', value: 86400000 },
  { label: '7天', value: 604800000 },
  { label: '30天', value: 2592000000 },
];

const REFRESH_INTERVALS = [
  { label: '关闭', value: 0 },
  { label: '10秒', value: 10000 },
  { label: '30秒', value: 30000 },
  { label: '1分钟', value: 60000 },
  { label: '5分钟', value: 300000 },
];

export function TimeRangeSelector({
  value,
  onChange,
  refreshInterval = 0,
  onRefresh,
}: TimeRangeSelectorProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  const handleQuickRange = useCallback((duration: number) => {
    const now = Date.now();
    onChange({ from: now - duration, to: now });
    setShowCustom(false);
  }, [onChange]);

  const handleCustomApply = useCallback(() => {
    if (customFrom && customTo) {
      onChange({
        from: new Date(customFrom).getTime(),
        to: new Date(customTo).getTime(),
      });
      setShowCustom(false);
    }
  }, [customFrom, customTo, onChange]);

  const activeRange = QUICK_RANGES.find(
    (r) => value.to - value.from === r.value
  );

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
        {QUICK_RANGES.map((range) => (
          <button
            key={range.value}
            onClick={() => handleQuickRange(range.value)}
            className={`
              px-3 py-1.5 text-sm rounded-md transition-colors
              ${activeRange?.value === range.value
                ? 'bg-amber-500 text-slate-900'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }
            `}
          >
            {range.label}
          </button>
        ))}
        <button
          onClick={() => setShowCustom(!showCustom)}
          className={`
            px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1
            ${!activeRange && (customFrom || customTo)
              ? 'bg-amber-500 text-slate-900'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }
          `}
        >
          <CalendarIcon className="w-4 h-4" />
          自定义
        </button>
      </div>

      {showCustom && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-full left-0 mt-2 bg-slate-800 border border-slate-700/50 rounded-lg p-4 shadow-xl z-10"
        >
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">开始时间</label>
              <input
                type="datetime-local"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
                className="px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">结束时间</label>
              <input
                type="datetime-local"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
                className="px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white text-sm focus:outline-none focus:border-amber-500/50"
              />
            </div>
            <button
              onClick={handleCustomApply}
              className="px-4 py-2 bg-amber-500 text-slate-900 rounded-lg text-sm font-medium hover:bg-amber-400 transition-colors mt-4"
            >
              应用
            </button>
          </div>
        </motion.div>
      )}

      <div className="flex items-center gap-2">
        <select
          value={refreshInterval}
          onChange={() => {}}
          className="px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-amber-500/50"
        >
          {REFRESH_INTERVALS.map((interval) => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>

        <button
          onClick={onRefresh}
          className="p-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 transition-colors"
          title="刷新"
        >
          <ArrowPathIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default TimeRangeSelector;
