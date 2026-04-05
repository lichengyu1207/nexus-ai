import React, { useState, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';

export interface SearchFilters {
  q: string;
  status: string;
  start_date: string;
  end_date: string;
}

interface ReportSearchBarProps {
  onSearch: (filters: SearchFilters) => void;
  isLoading?: boolean;
}

const ReportSearchBar: React.FC<ReportSearchBarProps> = ({ onSearch, isLoading = false }) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    q: '',
    status: '',
    start_date: '',
    end_date: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(filters);
  };

  const handleClear = useCallback(() => {
    const clearedFilters = {
      q: '',
      status: '',
      start_date: '',
      end_date: '',
    };
    setFilters(clearedFilters);
    onSearch(clearedFilters);
  }, [onSearch]);

  const hasActiveFilters = filters.q || filters.status || filters.start_date || filters.end_date;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <form onSubmit={handleSubmit}>
        <div className="flex items-center gap-3">
          {/* Search Input */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              name="q"
              value={filters.q}
              onChange={handleInputChange}
              placeholder="搜索报告内容或摘要..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-primary-50 border-primary-300 text-primary-700'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
          >
            <FunnelIcon className="w-5 h-5" />
            <span className="hidden sm:inline">筛选</span>
            {hasActiveFilters && (
              <span className="w-5 h-5 bg-primary-600 text-white text-xs rounded-full flex items-center justify-center">
                !
              </span>
            )}
          </button>

          {/* Search Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <MagnifyingGlassIcon className="w-5 h-5" />
            )}
            <span className="hidden sm:inline">搜索</span>
          </button>

          {/* Clear Button */}
          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleClear}
              className="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  状态
                </label>
                <select
                  name="status"
                  value={filters.status}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">全部状态</option>
                  <option value="completed">已完成</option>
                  <option value="generating">生成中</option>
                  <option value="pending">等待中</option>
                  <option value="failed">失败</option>
                  <option value="archived">已归档</option>
                </select>
              </div>

              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  开始日期
                </label>
                <div className="relative">
                  <CalendarIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="date"
                    name="start_date"
                    value={filters.start_date}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* End Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  结束日期
                </label>
                <div className="relative">
                  <CalendarIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="date"
                    name="end_date"
                    value={filters.end_date}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Active Filters Display */}
            {hasActiveFilters && (
              <div className="mt-4 flex flex-wrap gap-2">
                {filters.status && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                    状态: {filters.status === 'completed' ? '已完成' : 
                           filters.status === 'generating' ? '生成中' :
                           filters.status === 'pending' ? '等待中' :
                           filters.status === 'failed' ? '失败' : '已归档'}
                    <button
                      type="button"
                      onClick={() => setFilters(prev => ({ ...prev, status: '' }))}
                      className="hover:text-primary-900"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </span>
                )}
                {filters.start_date && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                    从: {filters.start_date}
                    <button
                      type="button"
                      onClick={() => setFilters(prev => ({ ...prev, start_date: '' }))}
                      className="hover:text-primary-900"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </span>
                )}
                {filters.end_date && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                    到: {filters.end_date}
                    <button
                      type="button"
                      onClick={() => setFilters(prev => ({ ...prev, end_date: '' }))}
                      className="hover:text-primary-900"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </form>
    </div>
  );
};

export default ReportSearchBar;
