import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { taskApi, Task } from '@/services/api';
import TaskCard from '@/components/TaskCard';
import ExportButton from '@/components/ExportButton';
import { EmptyStateWithMascot, useMascotToast } from '@/components/mascot';
import { BatchTaskInput, BatchProgress, BatchResultView } from '@/components/batch';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  TrashIcon,
  ArrowPathIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';

const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [styleFilter, setStyleFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  const [showBatchInput, setShowBatchInput] = useState(false);
  const [batchParentTaskId, setBatchParentTaskId] = useState<string | null>(null);
  const [showBatchProgress, setShowBatchProgress] = useState(false);
  const [showBatchResult, setShowBatchResult] = useState(false);
  const [batchTaskIds, setBatchTaskIds] = useState<string[]>([]);
  
  const navigate = useNavigate();
  const { showTaskDeleted } = useMascotToast();
  const limit = 12;

  const loadTasks = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await taskApi.list({
        limit,
        offset: page * limit,
        status: statusFilter || undefined,
      });
      
      let filteredTasks = response.tasks;
      
      if (searchQuery) {
        filteredTasks = filteredTasks.filter(task =>
          task.query.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      
      if (styleFilter) {
        filteredTasks = filteredTasks.filter(task => task.style === styleFilter);
      }
      
      setTasks(filteredTasks);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setIsLoading(false);
    }
  }, [page, statusFilter, searchQuery, styleFilter]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleDelete = async (taskId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (deleteConfirm === taskId) {
      setIsDeleting(true);
      try {
        await taskApi.delete(taskId);
        setTasks(tasks.filter(t => t.id !== taskId));
        setTotal(prev => prev - 1);
        setDeleteConfirm(null);
        showTaskDeleted();
      } catch (error) {
        console.error('Failed to delete task:', error);
      } finally {
        setIsDeleting(false);
      }
    } else {
      setDeleteConfirm(taskId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    loadTasks();
  };

  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('');
    setStyleFilter('');
    setPage(0);
  };

  const hasActiveFilters = searchQuery || statusFilter || styleFilter;

  const totalPages = Math.ceil(total / limit);

  const getStatusCount = (status: string) => {
    return tasks.filter(t => t.status === status).length;
  };

  const handleBatchTaskSubmit = async (taskIds: string[], parentId: string) => {
    setBatchParentTaskId(parentId);
    setBatchTaskIds(taskIds);
    setShowBatchInput(false);
    setShowBatchProgress(true);
    loadTasks();
  };

  const handleBatchProgressComplete = () => {
    setShowBatchProgress(false);
    setShowBatchResult(true);
    loadTasks();
  };

  const handleBatchCancel = async () => {
    if (batchParentTaskId) {
      try {
        await fetch(`/api/tasks/batch/${batchParentTaskId}/cancel`, { method: 'POST' });
      } catch (error) {
        console.error('Cancel failed:', error);
      }
    }
    setShowBatchProgress(false);
    setBatchParentTaskId(null);
  };

  return (
    <div className="space-y-6">
      {showBatchInput && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">批量任务输入</h2>
              <button
                onClick={() => setShowBatchInput(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <BatchTaskInput
              onSubmit={handleBatchTaskSubmit}
              onCancel={() => setShowBatchInput(false)}
            />
          </div>
        </div>
      )}

      {showBatchProgress && batchParentTaskId && (
        <BatchProgress
          parentTaskId={batchParentTaskId}
          onComplete={handleBatchProgressComplete}
          onCancel={handleBatchCancel}
        />
      )}

      {showBatchResult && batchParentTaskId && (
        <BatchResultView
          parentTaskId={batchParentTaskId}
          tasks={batchTaskIds.map((id) => ({
            id,
            type: 'property_analysis',
            typeLabel: '房产分析',
            status: 'completed',
            params: {},
            result: {},
            duration: 0,
            createdAt: new Date().toISOString(),
          }))}
          onTaskClick={(taskId) => navigate(`/tasks/${taskId}`)}
          onExport={(format) => console.log('Export as:', format)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">任务列表</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">共 {total} 个分析任务</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowBatchInput(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors dark:bg-gray-700 dark:text-gray-300"
          >
            <DocumentDuplicateIcon className="w-5 h-5" />
            智能批量输入
          </button>
          <ExportButton type="tasks" filters={{ status: statusFilter }} />
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors"
          >
            <span>+ 创建新任务</span>
          </Link>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <p className="text-sm text-gray-500">全部</p>
          <p className="text-2xl font-bold text-gray-900">{total}</p>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <p className="text-sm text-gray-500">进行中</p>
          <p className="text-2xl font-bold text-blue-600">{getStatusCount('running')}</p>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <p className="text-sm text-gray-500">已完成</p>
          <p className="text-2xl font-bold text-green-600">{getStatusCount('completed')}</p>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <p className="text-sm text-gray-500">失败</p>
          <p className="text-2xl font-bold text-red-600">{getStatusCount('failed')}</p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Search Bar */}
        <div className="p-4 border-b border-gray-100">
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索任务..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition-colors ${
                showFilters || hasActiveFilters
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="w-5 h-5" />
              <span className="hidden sm:inline">筛选</span>
              {hasActiveFilters && (
                <span className="w-5 h-5 bg-primary-600 text-white text-xs rounded-full flex items-center justify-center">
                  {[searchQuery, statusFilter, styleFilter].filter(Boolean).length}
                </span>
              )}
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              搜索
            </button>
          </form>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="p-4 bg-gray-50 border-b border-gray-100">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(0);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">全部状态</option>
                  <option value="pending">等待中</option>
                  <option value="running">进行中</option>
                  <option value="completed">已完成</option>
                  <option value="failed">失败</option>
                </select>
              </div>

              {/* Style Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">分析风格</label>
                <select
                  value={styleFilter}
                  onChange={(e) => {
                    setStyleFilter(e.target.value);
                    setPage(0);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">全部风格</option>
                  <option value="conservative">保守型</option>
                  <option value="balanced">平衡型</option>
                  <option value="aggressive">进取型</option>
                </select>
              </div>

              {/* Clear Filters */}
              <div className="flex items-end">
                <button
                  onClick={clearFilters}
                  disabled={!hasActiveFilters}
                  className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <XMarkIcon className="w-5 h-5" />
                  清除筛选
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quick Status Filters */}
        <div className="p-4 flex flex-wrap gap-2">
          {['', 'pending', 'running', 'completed', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => {
                setStatusFilter(status);
                setPage(0);
              }}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                statusFilter === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {status === '' ? '全部' : status === 'pending' ? '等待中' : status === 'running' ? '进行中' : status === 'completed' ? '已完成' : '失败'}
            </button>
          ))}
        </div>
      </div>

      {/* Task Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <ArrowPathIcon className="w-8 h-8 text-primary-600 animate-spin mb-3" />
          <p className="text-gray-500">加载中...</p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <EmptyStateWithMascot
            type={hasActiveFilters ? 'no-results' : 'no-tasks'}
            message={hasActiveFilters ? '没有找到匹配的任务，换个关键词试试？' : '点击"新建任务"开始你的房产分析吧！'}
            actionText={hasActiveFilters ? '清除筛选' : '创建任务'}
            onAction={hasActiveFilters ? clearFilters : () => window.location.href = '/dashboard'}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map((task) => (
            <div key={task.id} className="relative group">
              <TaskCard task={task} showActions={false} />
              
              {/* Delete Button */}
              <button
                onClick={(e) => handleDelete(task.id, e)}
                disabled={isDeleting}
                className={`absolute top-3 right-3 p-2 rounded-lg transition-all ${
                  deleteConfirm === task.id
                    ? 'bg-red-100 text-red-600 hover:bg-red-200'
                    : 'bg-white/80 text-gray-400 hover:text-red-600 hover:bg-white opacity-0 group-hover:opacity-100'
                }`}
                title={deleteConfirm === task.id ? '再次点击确认删除' : '删除任务'}
              >
                {deleteConfirm === task.id ? (
                  <ExclamationTriangleIcon className="w-5 h-5" />
                ) : (
                  <TrashIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="flex items-center gap-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeftIcon className="w-5 h-5" />
            上一页
          </button>
          
          <div className="flex items-center gap-2">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i;
              } else if (page < 2) {
                pageNum = i;
              } else if (page > totalPages - 3) {
                pageNum = totalPages - 5 + i;
              } else {
                pageNum = page - 2 + i;
              }
              
              return (
                <button
                  key={i}
                  onClick={() => setPage(pageNum)}
                  className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                    page === pageNum
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {pageNum + 1}
                </button>
              );
            })}
          </div>
          
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="flex items-center gap-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            下一页
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
};

export default TasksPage;
